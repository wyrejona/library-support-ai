from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import os
import shutil
from datetime import datetime
from typing import List, Optional
import uvicorn
import requests

# Import our custom modules
from app.utils import VectorStore
from app.ai.llm import OllamaClient

# Initialize components
vector_store = VectorStore()
llm_client = OllamaClient()

app = FastAPI(title="Library Support AI")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary project directories
os.makedirs("pdfs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Library Support AI</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f0f2f5;
                height: 100vh;
                display: flex;
                flex-direction: column;
            }
            .container {
                max-width: 1000px;
                margin: 20px auto;
                background: white;
                flex: 1;
                display: flex;
                flex-direction: column;
                border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            header {
                padding: 20px;
                background: #1a73e8;
                color: white;
                text-align: center;
            }
            .main-layout {
                display: grid;
                grid-template-columns: 300px 1fr;
                flex: 1;
                overflow: hidden;
            }
            .sidebar {
                border-right: 1px solid #ddd;
                padding: 20px;
                background: #fafafa;
                overflow-y: auto;
            }
            .chat-area {
                display: flex;
                flex-direction: column;
                padding: 20px;
                background: white;
                height: 100%;
            }
            #chatMessages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                margin-bottom: 10px;
                border: 1px solid #eee;
                border-radius: 8px;
                display: flex;
                flex-direction: column;
                background: #fff;
            }
            .message {
                margin-bottom: 15px;
                padding: 12px 16px;
                border-radius: 12px;
                line-height: 1.5;
                max-width: 85%;
                word-wrap: break-word;
                white-space: pre-wrap; /* Ensures formatting and spacing stay intact */
                height: auto;
                display: block;
            }
            .bot-message { background: #f1f3f4; align-self: flex-start; color: #333; }
            .user-message { background: #d2e3fc; align-self: flex-end; margin-left: auto; color: #1a73e8; }
            
            .input-group { display: flex; gap: 10px; padding-top: 10px; }
            textarea {
                flex: 1;
                padding: 12px;
                border: 1px solid #ccc;
                border-radius: 8px;
                resize: none;
                font-family: inherit;
            }
            .btn {
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
                transition: 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .btn-primary { background: #1a73e8; color: white; }
            .btn-secondary { background: #5f6368; color: white; width: 100%; margin-top: 10px; }
            .btn-danger { background: #d93025; color: white; padding: 5px 8px; font-size: 0.8em; }
            
            .status { font-size: 0.8em; margin-top: 10px; color: #666; }
            .file-item { 
                font-size: 0.85em; 
                margin-bottom: 8px; 
                padding: 8px; 
                background: #fff; 
                border: 1px solid #ddd;
                border-radius: 6px; 
                display: flex; 
                justify-content: space-between; 
                align-items: center;
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <header>
                <h1><i class="fas fa-university"></i> Library Support AI</h1>
            </header>
            <div class="main-layout">
                <div class="sidebar">
                    <h3><i class="fas fa-file-pdf"></i> Documents</h3>
                    <input type="file" id="fileInput" multiple accept=".pdf" style="display:none" onchange="uploadFiles(this.files)">
                    <button class="btn btn-secondary" onclick="document.getElementById('fileInput').click()">
                        <i class="fas fa-upload" style="margin-right:8px"></i> Upload PDFs
                    </button>
                    <button class="btn btn-secondary" style="background:#34a853" onclick="processPDFs()">
                        <i class="fas fa-brain" style="margin-right:8px"></i> Process Docs
                    </button>
                    <div id="fileList" style="margin-top:20px"></div>
                    <div id="statusBox" class="status"></div>
                </div>
                <div class="chat-area">
                    <div id="chatMessages">
                        <div class="message bot-message">Welcome, I am your Library AI buddy. Ask me anything about your uploaded documents!</div>
                    </div>
                    <div class="input-group">
                        <textarea id="userInput" placeholder="Ask about library resources..." rows="2"></textarea>
                        <button class="btn btn-primary" onclick="sendMessage()"><i class="fas fa-paper-plane"></i></button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function uploadFiles(files) {
                const formData = new FormData();
                for (let f of files) formData.append('files', f);
                document.getElementById('statusBox').innerText = "Uploading...";
                const resp = await fetch('/upload', { method: 'POST', body: formData });
                if (resp.ok) {
                    document.getElementById('statusBox').innerText = "Upload complete.";
                    loadFiles();
                }
            }

            async function loadFiles() {
                const resp = await fetch('/files');
                const data = await resp.json();
                const list = document.getElementById('fileList');
                list.innerHTML = data.files.map(f => `
                    <div class="file-item">
                        <span title="${f.name}">${f.name.length > 20 ? f.name.substring(0,20)+'...' : f.name}</span>
                        <button class="btn btn-danger" onclick="deleteFile('${f.name}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `).join('');
            }

            async function deleteFile(filename) {
                if(!confirm(`Delete ${filename}?`)) return;
                const resp = await fetch(`/files/${filename}`, { method: 'DELETE' });
                if (resp.ok) {
                    loadFiles();
                    document.getElementById('statusBox').innerText = "File deleted.";
                }
            }

            async function processPDFs() {
                document.getElementById('statusBox').innerText = "Indexing (this takes a moment)...";
                const resp = await fetch('/ingest', { method: 'POST' });
                const data = await resp.json();
                document.getElementById('statusBox').innerText = data.success ? "Ready for chat!" : "Error indexing.";
            }

            async function sendMessage() {
                const input = document.getElementById('userInput');
                const msg = input.value.trim();
                if (!msg) return;

                addMessage("You: " + msg, 'user');
                input.value = '';

                try {
                    const resp = await fetch('/chat', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({ message: msg })
                    });
                    const data = await resp.json();
                    addMessage("AI Assistant: " + data.response, 'bot');
                } catch (e) {
                    addMessage("AI Assistant: Error connecting to server.", 'bot');
                }
            }

            function addMessage(text, type) {
                const div = document.createElement('div');
                div.className = `message ${type}-message`;
                div.innerText = text;
                const container = document.getElementById('chatMessages');
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }
            
            loadFiles();
        </script>
    </body>
    </html>
    """

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    saved_count = 0
    for file in files:
        if file.filename.lower().endswith('.pdf'):
            filepath = os.path.join("pdfs", file.filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_count += 1
    return {"count": saved_count}

@app.get("/files")
async def list_files():
    files = [{"name": f} for f in os.listdir("pdfs") if f.endswith(".pdf")]
    return {"files": files}

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    filepath = os.path.join("pdfs", filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return {"message": "Deleted"}
    raise HTTPException(status_code=404, detail="File not found")

@app.post("/ingest")
async def ingest_pdfs():
    try:
        import subprocess
        result = subprocess.run(["python3", "ingest.py"], capture_output=True, text=True)
        return {"success": result.returncode == 0, "output": result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/chat")
@app.post("/ask")
async def chat(request_data: dict):
    # Support both "message" (internal UI) and "query" (WordPress plugin)
    user_message = request_data.get("message") or request_data.get("query") or ""
    
    if not user_message:
        return {"response": "I didn't receive a question.", "answer": "I didn't receive a question."}

    # RAG Retrieval
    search_results = vector_store.search(user_message, k=3)
    
    from app.utils import format_context
    context = format_context(search_results)
    
    # Call Ollama
    response = llm_client.generate_response(prompt=user_message, context=context)
    
    # Return keys compatible with all frontends
    return {
        "response": response,
        "answer": response,
        "sources": [{"file": r['source'], "page": r.get('page')} for r in search_results]
    }

@app.get("/health")
async def health_check():
    ollama_ok = False
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        ollama_ok = r.status_code == 200
    except:
        pass
    
    return {
        "ollama": "up" if ollama_ok else "down",
        "index_ready": os.path.exists("data/metadata.pkl"),
        "pdf_count": len(os.listdir("pdfs"))
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)