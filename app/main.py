from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import os
import shutil
from datetime import datetime
from typing import List
import uvicorn

# Try to import our modules with error handling
try:
    from app.utils import VectorStore
    vector_store = VectorStore()
except ImportError as e:
    print(f"⚠️  Warning: Could not import VectorStore: {e}")
    vector_store = None

try:
    from app.ai.llm import OllamaClient
    llm_client = OllamaClient()
except ImportError as e:
    print(f"⚠️  Warning: Could not import OllamaClient: {e}")
    llm_client = None

app = FastAPI(title="PDF Chat Assistant")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("pdfs", exist_ok=True)
os.makedirs("data", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PDF Chat Assistant</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 2px solid #f0f0f0;
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
            }
            .subtitle {
                color: #666;
                font-size: 1.1em;
            }
            .main-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }
            .card {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .card h2 {
                color: #333;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .card h2 i { color: #4361ee; }
            .upload-area {
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 40px 20px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                background: white;
            }
            .upload-area:hover {
                border-color: #4361ee;
                background: #f8faff;
            }
            .upload-area i {
                font-size: 48px;
                color: #4361ee;
                margin-bottom: 15px;
            }
            .upload-area p {
                color: #666;
                margin-bottom: 15px;
            }
            .btn {
                background: #4361ee;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                cursor: pointer;
                font-size: 16px;
                transition: background 0.3s;
                display: inline-flex;
                align-items: center;
                gap: 8px;
            }
            .btn:hover { background: #3a56d4; }
            .btn-secondary {
                background: #7209b7;
            }
            .btn-secondary:hover { background: #5a08a0; }
            input[type="file"] { display: none; }
            .file-list {
                max-height: 200px;
                overflow-y: auto;
                margin-top: 15px;
            }
            .file-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                background: white;
                border-radius: 6px;
                margin-bottom: 5px;
                border: 1px solid #eee;
            }
            .chat-container {
                display: flex;
                flex-direction: column;
                height: 500px;
            }
            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 15px;
                background: white;
                border-radius: 8px;
                border: 1px solid #eee;
                margin-bottom: 15px;
            }
            .message {
                margin-bottom: 15px;
                padding: 12px 15px;
                border-radius: 8px;
                max-width: 80%;
            }
            .user-message {
                background: #e3f2fd;
                margin-left: auto;
            }
            .bot-message {
                background: #f5f5f5;
            }
            .chat-input {
                display: flex;
                gap: 10px;
            }
            .chat-input textarea {
                flex: 1;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                resize: none;
                font-family: inherit;
                font-size: 16px;
            }
            .chat-input button {
                padding: 12px 24px;
                white-space: nowrap;
            }
            .status {
                padding: 10px;
                border-radius: 6px;
                margin: 10px 0;
                display: none;
            }
            .status.success { background: #d4edda; color: #155724; }
            .status.error { background: #f8d7da; color: #721c24; }
            .status.info { background: #d1ecf1; color: #0c5460; }
            @media (max-width: 768px) {
                .main-content { grid-template-columns: 1fr; }
                .container { padding: 15px; }
            }
        </style>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    </head>
    <body>
        <div class="container">
            <header>
                <h1><i class="fas fa-robot"></i> PDF Chat Assistant</h1>
                <p class="subtitle">Upload PDFs and chat with an AI that reads your documents</p>
            </header>
            
            <div class="main-content">
                <!-- Left Column: Upload & Files -->
                <div>
                    <div class="card">
                        <h2><i class="fas fa-upload"></i> Upload PDF</h2>
                        <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                            <i class="fas fa-cloud-upload-alt"></i>
                            <p>Click to browse or drag & drop PDF files</p>
                            <button class="btn"><i class="fas fa-folder-open"></i> Browse Files</button>
                        </div>
                        <input type="file" id="fileInput" accept=".pdf" multiple onchange="handleFiles(this.files)">
                        
                        <div id="uploadStatus" class="status"></div>
                        
                        <div id="fileList" class="file-list"></div>
                    </div>
                    
                    <div class="card">
                        <h2><i class="fas fa-cogs"></i> Actions</h2>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            <button class="btn" onclick="processPDFs()">
                                <i class="fas fa-brain"></i> Process PDFs
                            </button>
                            <button class="btn btn-secondary" onclick="clearFiles()">
                                <i class="fas fa-trash"></i> Clear All
                            </button>
                            <button class="btn" onclick="checkHealth()">
                                <i class="fas fa-heartbeat"></i> Check Health
                            </button>
                        </div>
                        <div id="actionStatus" class="status"></div>
                    </div>
                    
                    <div class="card">
                        <h2><i class="fas fa-info-circle"></i> How It Works</h2>
                        <ol style="margin-left: 20px; color: #555;">
                            <li>Upload PDF files using the upload area</li>
                            <li>Click "Process PDFs" to make them searchable</li>
                            <li>Ask questions in the chat on the right</li>
                            <li>The AI will answer based on your documents</li>
                        </ol>
                    </div>
                </div>
                
                <!-- Right Column: Chat -->
                <div>
                    <div class="card">
                        <h2><i class="fas fa-comments"></i> Chat with Documents</h2>
                        <div class="chat-container">
                            <div class="chat-messages" id="chatMessages">
                                <div class="message bot-message">
                                    <strong>AI Assistant:</strong> Hello! Upload PDF files and click "Process PDFs" to start chatting about your documents.
                                </div>
                            </div>
                            
                            <div class="chat-input">
                                <textarea id="messageInput" placeholder="Ask a question about your documents..." rows="3"></textarea>
                                <button class="btn" onclick="sendMessage()">
                                    <i class="fas fa-paper-plane"></i> Send
                                </button>
                            </div>
                        </div>
                        
                        <div style="margin-top: 15px; display: flex; gap: 10px;">
                            <button class="btn" onclick="clearChat()">
                                <i class="fas fa-broom"></i> Clear Chat
                            </button>
                            <div style="flex: 1;"></div>
                            <label style="display: flex; align-items: center; gap: 5px; color: #555;">
                                <input type="checkbox" id="useContext" checked> Use document context
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let uploadedFiles = [];
            let chatHistory = [];
            
            function showStatus(elementId, message, type = 'info') {
                const element = document.getElementById(elementId);
                element.textContent = message;
                element.className = `status ${type}`;
                element.style.display = 'block';
                setTimeout(() => element.style.display = 'none', 5000);
            }
            
            function handleFiles(files) {
                if (files.length === 0) return;
                
                const formData = new FormData();
                for (let i = 0; i < files.length; i++) {
                    if (files[i].type === 'application/pdf' || files[i].name.toLowerCase().endsWith('.pdf')) {
                        formData.append('files', files[i]);
                        uploadedFiles.push(files[i].name);
                    }
                }
                
                if (formData.has('files')) {
                    uploadFiles(formData);
                } else {
                    showStatus('uploadStatus', 'Please select PDF files only', 'error');
                }
            }
            
            async function uploadFiles(formData) {
                try {
                    showStatus('uploadStatus', 'Uploading files...', 'info');
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        showStatus('uploadStatus', `Uploaded ${result.count} file(s) successfully!`, 'success');
                        updateFileList();
                        document.getElementById('fileInput').value = '';
                    } else {
                        showStatus('uploadStatus', 'Upload failed', 'error');
                    }
                } catch (error) {
                    showStatus('uploadStatus', 'Error: ' + error, 'error');
                }
            }
            
            function updateFileList() {
                const fileList = document.getElementById('fileList');
                if (uploadedFiles.length === 0) {
                    fileList.innerHTML = '<p style="color: #666; text-align: center;">No files uploaded yet</p>';
                    return;
                }
                
                let html = '<h3>Uploaded Files:</h3>';
                uploadedFiles.forEach((file, index) => {
                    html += `
                        <div class="file-item">
                            <span><i class="fas fa-file-pdf"></i> ${file}</span>
                            <button onclick="removeFile(${index})" style="background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer;">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `;
                });
                fileList.innerHTML = html;
            }
            
            function removeFile(index) {
                uploadedFiles.splice(index, 1);
                updateFileList();
            }
            
            async function processPDFs() {
                try {
                    showStatus('actionStatus', 'Processing PDFs and creating search index...', 'info');
                    const response = await fetch('/ingest', { method: 'POST' });
                    const result = await response.json();
                    
                    if (result.success) {
                        showStatus('actionStatus', '✅ PDFs processed successfully! You can now chat about your documents.', 'success');
                        addChatMessage('AI Assistant: Your documents have been processed and are ready for questions!', 'bot');
                    } else {
                        showStatus('actionStatus', 'Error: ' + (result.error || 'Unknown error'), 'error');
                    }
                } catch (error) {
                    showStatus('actionStatus', 'Error: ' + error, 'error');
                }
            }
            
            async function clearFiles() {
                if (confirm('Are you sure you want to remove all uploaded files?')) {
                    try {
                        const response = await fetch('/clear', { method: 'POST' });
                        if (response.ok) {
                            uploadedFiles = [];
                            updateFileList();
                            showStatus('actionStatus', 'All files cleared', 'success');
                        }
                    } catch (error) {
                        showStatus('actionStatus', 'Error clearing files', 'error');
                    }
                }
            }
            
            async function checkHealth() {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    
                    let statusMessage = `System Status:<br>`;
                    statusMessage += `• Ollama: ${data.ollama_available ? '✅ Available' : '❌ Not Available'}<br>`;
                    statusMessage += `• PDFs: ${data.pdf_count} file(s)<br>`;
                    statusMessage += `• Index: ${data.index_exists ? '✅ Ready' : '❌ Not Ready'}<br>`;
                    statusMessage += `• Model: ${data.ollama_model || 'Not loaded'}`;
                    
                    showStatus('actionStatus', statusMessage, 'info');
                } catch (error) {
                    showStatus('actionStatus', 'Health check failed', 'error');
                }
            }
            
            async function sendMessage() {
                const input = document.getElementById('messageInput');
                const message = input.value.trim();
                if (!message) return;
                
                // Add user message to chat
                addChatMessage(`You: ${message}`, 'user');
                input.value = '';
                
                // Get context setting
                const useContext = document.getElementById('useContext').checked;
                
                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            message: message,
                            use_context: useContext
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Add bot response to chat
                    let botMessage = `AI Assistant: ${data.response}`;
                    if (data.sources && data.sources.length > 0) {
                        botMessage += `<br><small style="color: #666;">Sources: ${data.sources.map(s => s.source).join(', ')}</small>`;
                    }
                    addChatMessage(botMessage, 'bot');
                    
                } catch (error) {
                    addChatMessage(`AI Assistant: Error - Could not get response. Make sure Ollama is running.`, 'bot');
                }
            }
            
            function addChatMessage(content, sender) {
                const messagesDiv = document.getElementById('chatMessages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                messageDiv.innerHTML = content;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function clearChat() {
                document.getElementById('chatMessages').innerHTML = `
                    <div class="message bot-message">
                        <strong>AI Assistant:</strong> Chat cleared. Upload PDFs and click "Process PDFs" to start chatting about your documents.
                    </div>
                `;
                chatHistory = [];
            }
            
            // Allow Enter to send (Shift+Enter for new line)
            document.getElementById('messageInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });
            
            // Drag and drop support
            const uploadArea = document.querySelector('.upload-area');
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '#4361ee';
                uploadArea.style.background = '#f8faff';
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.style.borderColor = '#ccc';
                uploadArea.style.background = 'white';
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.style.borderColor = '#ccc';
                uploadArea.style.background = 'white';
                handleFiles(e.dataTransfer.files);
            });
            
            // Initialize
            updateFileList();
            checkHealth();
        </script>
    </body>
    </html>
    """

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload PDF files"""
    saved_files = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue
            
        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join("pdfs", filename)
        
        # Save file
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        saved_files.append(filename)
    
    return {
        "message": "Files uploaded successfully",
        "count": len(saved_files),
        "files": saved_files
    }

@app.get("/files")
async def list_files():
    """List uploaded PDF files"""
    if not os.path.exists("pdfs"):
        return {"files": []}
    
    files = []
    for filename in os.listdir("pdfs"):
        if filename.lower().endswith('.pdf'):
            filepath = os.path.join("pdfs", filename)
            size = os.path.getsize(filepath)
            files.append({
                "name": filename,
                "size": size,
                "uploaded": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
            })
    
    return {"files": files}

@app.post("/clear")
async def clear_all_files():
    """Remove all uploaded files"""
    if os.path.exists("pdfs"):
        for filename in os.listdir("pdfs"):
            filepath = os.path.join("pdfs", filename)
            if os.path.isfile(filepath):
                os.remove(filepath)
    
    # Also clear vector index
    index_files = ["data/library_index.faiss", "data/metadata.pkl"]
    for file in index_files:
        if os.path.exists(file):
            os.remove(file)
    
    return {"message": "All files cleared"}

@app.post("/ingest")
async def ingest_pdfs():
    """Process PDFs and create search index"""
    try:
        # Import here to avoid circular imports
        from ingest import main as ingest_main
        
        # Run ingestion
        import subprocess
        result = subprocess.run(["python", "ingest.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "PDFs processed successfully",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "error": result.stderr or "Ingestion failed",
                "output": result.stdout
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/chat")
async def chat(message: dict):
    """Chat with the AI about documents"""
    try:
        user_message = message.get("message", "")
        use_context = message.get("use_context", True)
        
        context = ""
        sources = []
        
        if use_context:
            # Search for relevant context
            search_results = vector_store.search(user_message, k=5)
            if search_results:
                from app.utils import format_context
                context = format_context(search_results)
                sources = [{
                    'source': result['source'],
                    'page': result.get('page')
                } for result in search_results]
        
        # Get response from LLM
        response = llm_client.generate_response(
            prompt=user_message,
            context=context
        )
        
        return {
            "response": response,
            "sources": sources
        }
        
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "sources": []
        }

@app.get("/health")
async def health_check():
    """Check system health"""
    import sys
    
    # Check Ollama
    ollama_available = False
    ollama_model = None
    try:
        import ollama
        models = ollama.list()
        ollama_available = bool(models.get('models'))
        if ollama_available and models['models']:
            ollama_model = models['models'][0]['model']
    except:
        ollama_available = False
    
    # Check PDFs
    pdf_count = 0
    if os.path.exists("pdfs"):
        pdf_count = len([f for f in os.listdir("pdfs") if f.lower().endswith('.pdf')])
    
    # Check index
    index_exists = os.path.exists("data/metadata.pkl")
    
    return {
        "status": "ok",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "ollama_available": ollama_available,
        "ollama_model": ollama_model,
        "pdf_count": pdf_count,
        "index_exists": index_exists
    }

if __name__ == "__main__":
    print("🚀 Starting PDF Chat Assistant...")
    print("📚 Open browser to: http://localhost:8000")
    print("\nRequirements:")
    print("• Make sure Ollama is running: ollama serve")
    print("• Upload PDFs using the web interface")
    print("• Click 'Process PDFs' to make them searchable")
    print("• Then chat with your documents!")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
