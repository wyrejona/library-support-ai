from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import shutil
from datetime import datetime
from typing import List
import uvicorn
from pathlib import Path
import sys

# Add the app directory to Python path
current_file = Path(__file__).resolve()
app_dir = current_file.parent
project_root = app_dir.parent

sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(project_root))

# Import our custom modules
try:
    # First try: if running from project root
    from app.utils import VectorStore
    from app.ai.llm import OllamaClient
except ImportError:
    try:
        # Second try: if running from app directory
        from utils import VectorStore
        from ai.llm import OllamaClient
    except ImportError:
        # Third try: relative import
        from .utils import VectorStore
        from .ai.llm import OllamaClient

# Initialize components
vector_store = VectorStore()
# Configured for your verified qwen:0.5b model on OptiPlex 3040
llm_client = OllamaClient(model="qwen:0.5b")

app = FastAPI(title="Library Support AI")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the current directory
current_dir = Path(__file__).parent

# Create necessary project directories
pdfs_dir = current_dir.parent / "pdfs"
data_dir = current_dir.parent / "data"
os.makedirs(pdfs_dir, exist_ok=True)
os.makedirs(data_dir, exist_ok=True)

# Configure templates - they are in app/templates
templates = Jinja2Templates(directory=str(current_dir / "templates"))

def format_file_size(bytes):
    """Format file size in human readable format"""
    if bytes == 0:
        return "0 Bytes"
    size_names = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes >= 1024 and i < len(size_names) - 1:
        bytes /= 1024.0
        i += 1
    return f"{bytes:.2f} {size_names[i]}"

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Library Support AI</title>
        <style>
            :root {
                --primary: #1a73e8;
                --primary-dark: #0d47a1;
                --secondary: #5f6368;
                --success: #34a853;
                --danger: #d93025;
                --warning: #f9ab00;
                --light: #f8f9fa;
                --dark: #202124;
                --gray: #dadce0;
                --gray-light: #f1f3f4;
                --shadow: 0 4px 12px rgba(0,0,0,0.1);
                --radius: 12px;
                --radius-sm: 8px;
                --transition: all 0.3s ease;
            }

            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                min-height: 100vh;
                color: var(--dark);
                line-height: 1.6;
            }

            .container {
                max-width: 1400px;
                margin: 0 auto;
                padding: 20px;
                height: 100vh;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }

            header {
                background: white;
                border-radius: var(--radius);
                padding: 20px 30px;
                box-shadow: var(--shadow);
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 15px;
            }

            .logo {
                display: flex;
                align-items: center;
                gap: 15px;
            }

            .logo i {
                font-size: 2.5rem;
                color: var(--primary);
                background: linear-gradient(135deg, var(--primary), var(--primary-dark));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }

            .logo h1 {
                font-size: 1.8rem;
                font-weight: 700;
                color: var(--dark);
            }

            .nav-links {
                display: flex;
                gap: 15px;
            }

            .nav-link {
                padding: 10px 20px;
                text-decoration: none;
                color: var(--dark);
                border-radius: var(--radius-sm);
                transition: var(--transition);
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
            }

            .nav-link:hover {
                background: var(--gray-light);
                color: var(--primary);
            }

            .nav-link.active {
                background: var(--primary);
                color: white;
            }

            .status-indicator {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 8px 16px;
                background: var(--gray-light);
                border-radius: 20px;
                font-size: 0.9rem;
            }

            .status-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: var(--success);
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .welcome-message {
                background: white;
                border-radius: var(--radius);
                padding: 40px;
                text-align: center;
                box-shadow: var(--shadow);
                margin-top: 20px;
            }

            .welcome-message h2 {
                margin-bottom: 20px;
                color: var(--primary);
            }

            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 30px;
            }

            .feature {
                padding: 25px;
                background: var(--gray-light);
                border-radius: var(--radius);
                text-align: center;
                transition: var(--transition);
            }

            .feature:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }

            .feature i {
                font-size: 2.5rem;
                color: var(--primary);
                margin-bottom: 15px;
            }

            .quick-actions {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 30px;
            }

            .btn {
                padding: 12px 24px;
                border: none;
                border-radius: var(--radius-sm);
                font-weight: 600;
                font-size: 0.95rem;
                cursor: pointer;
                transition: var(--transition);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                text-decoration: none;
            }

            .btn i {
                font-size: 1.1rem;
            }

            .btn-primary {
                background: linear-gradient(135deg, var(--primary), var(--primary-dark));
                color: white;
            }

            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(26, 115, 232, 0.2);
            }

            .btn-success {
                background: linear-gradient(135deg, var(--success), #2e7d32);
                color: white;
            }

            .btn-success:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 12px rgba(52, 168, 83, 0.2);
            }

            @media (max-width: 768px) {
                .container {
                    padding: 10px;
                    height: auto;
                    min-height: 100vh;
                }
                
                header {
                    flex-direction: column;
                    text-align: center;
                    gap: 15px;
                }
                
                .nav-links {
                    flex-wrap: wrap;
                    justify-content: center;
                }
                
                .features {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 480px) {
                .btn {
                    padding: 10px 16px;
                    font-size: 0.9rem;
                }
                
                .nav-link {
                    padding: 8px 12px;
                    font-size: 0.9rem;
                }
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <header>
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    <h1>Library Support AI</h1>
                </div>
                
                <div class="nav-links">
                    <a href="/" class="nav-link active">
                        <i class="fas fa-home"></i> Home
                    </a>
                    <a href="/files" class="nav-link">
                        <i class="fas fa-folder"></i> Manage Files
                    </a>
                    <a href="/chat" class="nav-link">
                        <i class="fas fa-comments"></i> Chat
                    </a>
                </div>
                
                <div class="status-indicator">
                    <div class="status-dot"></div>
                    <span>System Ready</span>
                </div>
            </header>

            <div class="welcome-message">
                <h2>Welcome to Library Support AI</h2>
                <p>Your intelligent assistant for managing and querying library documents. Upload PDFs, ask questions, and get instant answers from your documents.</p>
                
                <div class="features">
                    <div class="feature">
                        <i class="fas fa-file-upload"></i>
                        <h3>Upload PDFs</h3>
                        <p>Easily upload multiple PDF documents</p>
                    </div>
                    <div class="feature">
                        <i class="fas fa-robot"></i>
                        <h3>AI-Powered Chat</h3>
                        <p>Ask questions about your documents</p>
                    </div>
                    <div class="feature">
                        <i class="fas fa-search"></i>
                        <h3>Smart Search</h3>
                        <p>Find information quickly and accurately</p>
                    </div>
                    <div class="feature">
                        <i class="fas fa-download"></i>
                        <h3>Easy Download</h3>
                        <p>Preview and download your files</p>
                    </div>
                </div>
                
                <div class="quick-actions">
                    <a href="/files" class="btn btn-primary">
                        <i class="fas fa-upload"></i> Upload Files
                    </a>
                    <a href="/chat" class="btn btn-success">
                        <i class="fas fa-comment"></i> Start Chatting
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# File Management Page - GET request returns HTML
@app.get("/files", response_class=HTMLResponse)
async def manage_files(request: Request):
    # Get list of files
    files = []
    for f in os.listdir(pdfs_dir):
        if f.endswith(".pdf"):
            file_path = pdfs_dir / f
            files.append({
                "name": f,
                "size": os.path.getsize(file_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)),
                "formatted_size": format_file_size(os.path.getsize(file_path))
            })
    
    # Sort files by modification time (newest first)
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    # Get vector store status
    vector_status = "Not processed"
    if os.path.exists(data_dir / "chroma.sqlite3"):
        vector_status = "Ready"
    
    total_size = sum(f["size"] for f in files)
    
    return templates.TemplateResponse("files.html", {
        "request": request,
        "files": files,
        "total_files": len(files),
        "total_size": total_size,
        "format_file_size": format_file_size,
        "vector_status": vector_status
    })

# Chat Page - GET request returns HTML (SEPARATE FROM POST!)
@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    # Get list of files
    files = []
    for f in os.listdir(pdfs_dir):
        if f.endswith(".pdf"):
            file_path = pdfs_dir / f
            files.append({
                "name": f,
                "size": os.path.getsize(file_path),
                "formatted_size": format_file_size(os.path.getsize(file_path))
            })
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "files": files,
        "total_files": len(files)
    })

# Chat API - POST request returns JSON (SEPARATE FROM GET!)
@app.post("/chat")
async def chat_api(request_data: dict):
    user_message = request_data.get("message") or request_data.get("query") or ""
    if not user_message:
        return {"response": "Please enter a question."}
    
    try:
        # Search for relevant context
        search_results = vector_store.search(user_message, k=2)
        from utils import format_context
        context = format_context(search_results)
        
        # Generate response using LLM
        response = llm_client.generate_response(prompt=user_message, context=context)
        
        return {
            "response": response,
            "answer": response,
            "context_used": len(context) > 0
        }
    except Exception as e:
        return {
            "response": f"I apologize, but I encountered an error: {str(e)}",
            "error": str(e)
        }

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded_files = []
    
    for file in files:
        if file.filename.lower().endswith('.pdf'):
            file_path = pdfs_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            file_size = os.path.getsize(file_path)
            uploaded_files.append({
                "name": file.filename,
                "size": file_size,
                "uploaded_at": datetime.now().isoformat()
            })
    return {"status": "success", "uploaded": uploaded_files}

@app.get("/api/files")
async def list_files_api():
    files = []
    for f in os.listdir(pdfs_dir):
        if f.endswith(".pdf"):
            file_path = pdfs_dir / f
            files.append({
                "name": f,
                "size": os.path.getsize(file_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    return {"files": files}

@app.get("/download/{filename}")
async def download_file(filename: str):
    filepath = pdfs_dir / filename
    if os.path.exists(filepath):
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type='application/pdf',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    raise HTTPException(status_code=404, detail="File not found")

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    path = pdfs_dir / filename
    if os.path.exists(path):
        os.remove(path)
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="File not found")

@app.delete("/clear-all-files")
async def clear_all_files():
    try:
        # Remove all PDF files
        for filename in os.listdir(pdfs_dir):
            if filename.endswith(".pdf"):
                os.remove(pdfs_dir / filename)
        
        # Optionally clear vector store data
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
            os.makedirs(data_dir, exist_ok=True)
        
        return {"status": "success", "message": "All files cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingest")
async def ingest_pdfs():
    import subprocess
    try:
        # Run ingest.py from the parent directory
        ingest_script = project_root / "ingest.py"
        result = subprocess.run(["python3", str(ingest_script)], capture_output=True, text=True)
        if result.returncode == 0:
            return {"success": True, "message": "PDFs processed successfully"}
        else:
            return {"success": False, "error": result.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
