from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
import shutil
from datetime import datetime
from typing import List
import uvicorn
from pathlib import Path

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
project_root = current_dir.parent

# Create necessary project directories
pdfs_dir = project_root / "pdfs"
data_dir = project_root / "data"
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

# Dummy implementations for testing
class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
    def search(self, query: str, k: int = 3):
        return []
    def load(self):
        return False

class OllamaClient:
    def __init__(self, model="qwen:0.5b"):
        self.model = model
    def generate_response(self, prompt, context):
        return f"AI Response: I received your query: '{prompt}'. The full AI functionality is being set up."

# Initialize components
vector_store = VectorStore()
llm_client = OllamaClient(model="qwen:0.5b")

@app.get("/")
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Library Support AI</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            a { display: inline-block; margin: 10px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
    <h1>Library Support AI</h1>
    <p>Server is working!</p>
    <a href="/chat">Go to Chat</a>
    <a href="/files">Manage Files</a>
    <a href="/api/files">API: List Files</a>
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

# Chat Page - GET request returns HTML
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

# Chat API - POST request returns JSON
@app.post("/chat")
async def chat_api(request_data: dict):
    user_message = request_data.get("message", "")
    return {
        "response": f"I received: '{user_message}'. Full AI features coming soon!",
        "answer": f"Test response to: {user_message}"
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
    print(f"Starting server on http://0.0.0.0:8000")
    print(f"PDFs directory: {pdfs_dir}")
    print(f"Templates directory: {current_dir / 'templates'}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
