from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os

# Create app first
app = FastAPI(title="Library AI Assistant")

# CORS middleware - use hardcoded values for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hardcoded for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import database after app creation
from app.database import create_tables

# Create database tables
create_tables()

# Import routers after app creation to avoid circular imports
try:
    from app.routes import auth, chat, upload
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(upload.router)
    print("✅ Routers loaded successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not load some routers: {e}")

# Create directories
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("pdfs", exist_ok=True)
os.makedirs("app/data", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Library AI Assistant</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: white;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(255,255,255,0.9);
                padding: 30px;
                border-radius: 10px;
                color: #333;
            }
            h1 { color: #333; }
            .menu {
                display: flex;
                gap: 10px;
                margin: 20px 0;
            }
            .btn {
                padding: 10px 20px;
                background: #4361ee;
                color: white;
                text-decoration: none;
                border-radius: 5px;
            }
            .btn:hover { background: #3a56d4; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📚 Library AI Assistant</h1>
            <p>Upload PDF documents and chat with an AI assistant that answers questions based on your documents.</p>
            
            <div class="menu">
                <a href="/login" class="btn">Login</a>
                <a href="/dashboard" class="btn">Dashboard</a>
                <a href="/chat" class="btn">Chat</a>
                <a href="/health" class="btn">Health Check</a>
            </div>
            
            <h3>Quick Start:</h3>
            <ol>
                <li>Login with: admin / admin123</li>
                <li>Upload PDF files in Dashboard</li>
                <li>Use the Chat interface to ask questions</li>
            </ol>
        </div>
    </body>
    </html>
    """)

@app.get("/login")
async def login_page():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .login-box {
                background: white;
                padding: 40px;
                border-radius: 10px;
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
                width: 300px;
            }
            input, button {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                box-sizing: border-box;
            }
            button {
                background: #4361ee;
                color: white;
                border: none;
                cursor: pointer;
                border-radius: 5px;
            }
            button:hover { background: #3a56d4; }
            .error { color: red; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h2>Login</h2>
            <form id="loginForm">
                <input type="text" id="username" placeholder="Username" required>
                <input type="password" id="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <div id="message" class="error"></div>
            <p>Default: admin / admin123</p>
        </div>
        
        <script>
            document.getElementById('loginForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData();
                formData.append('username', document.getElementById('username').value);
                formData.append('password', document.getElementById('password').value);
                
                try {
                    const response = await fetch('/api/auth/login', {
                        method: 'POST',
                        body: formData,
                        credentials: 'include'
                    });
                    
                    if (response.ok) {
                        window.location.href = '/dashboard';
                    } else {
                        document.getElementById('message').textContent = 'Login failed';
                    }
                } catch (error) {
                    document.getElementById('message').textContent = 'Error: ' + error;
                }
            });
        </script>
    </body>
    </html>
    """)

@app.get("/dashboard")
async def dashboard():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .card { 
                border: 1px solid #ddd; 
                padding: 20px; 
                margin: 10px 0; 
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            button, .btn { 
                background: #4361ee; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                border-radius: 5px;
                margin: 5px;
            }
            button:hover, .btn:hover { background: #3a56d4; }
            input[type="file"] { margin: 10px 0; }
        </style>
    </head>
    <body>
        <h1>Dashboard</h1>
        
        <div class="card">
            <h3>📄 Upload PDF</h3>
            <input type="file" id="pdfFile" accept=".pdf">
            <button onclick="uploadPDF()">Upload PDF</button>
            <div id="uploadStatus"></div>
        </div>
        
        <div class="card">
            <h3>💬 Chat with Documents</h3>
            <a href="/chat" class="btn">Go to Chat Interface</a>
        </div>
        
        <div class="card">
            <h3>🔄 Create Search Index</h3>
            <button onclick="createIndex()">Create/Update Index</button>
            <div id="indexStatus"></div>
        </div>
        
        <div class="card">
            <h3>📊 Your Files</h3>
            <button onclick="listFiles()">Refresh File List</button>
            <div id="fileList"></div>
        </div>
        
        <script>
            async function uploadPDF() {
                const fileInput = document.getElementById('pdfFile');
                if (!fileInput.files[0]) {
                    alert('Please select a PDF file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    document.getElementById('uploadStatus').innerHTML = 'Uploading...';
                    const response = await fetch('/api/upload/pdf', {
                        method: 'POST',
                        body: formData,
                        credentials: 'include'
                    });
                    
                    if (response.ok) {
                        document.getElementById('uploadStatus').innerHTML = '✅ File uploaded successfully!';
                        fileInput.value = '';
                    } else {
                        document.getElementById('uploadStatus').innerHTML = '❌ Upload failed';
                    }
                } catch (error) {
                    document.getElementById('uploadStatus').innerHTML = 'Error: ' + error;
                }
            }
            
            async function createIndex() {
                try {
                    document.getElementById('indexStatus').innerHTML = 'Creating index...';
                    const response = await fetch('/ingest', {
                        method: 'POST',
                        credentials: 'include'
                    });
                    
                    const result = await response.json();
                    if (result.success) {
                        document.getElementById('indexStatus').innerHTML = '✅ Index created successfully!';
                    } else {
                        document.getElementById('indexStatus').innerHTML = '❌ Error: ' + result.error;
                    }
                } catch (error) {
                    document.getElementById('indexStatus').innerHTML = 'Error: ' + error;
                }
            }
            
            async function listFiles() {
                try {
                    const response = await fetch('/api/upload/files', {
                        credentials: 'include'
                    });
                    
                    const files = await response.json();
                    const fileList = document.getElementById('fileList');
                    
                    if (files.length === 0) {
                        fileList.innerHTML = '<p>No files uploaded yet</p>';
                        return;
                    }
                    
                    let html = '<ul>';
                    files.forEach(file => {
                        html += `<li>${file.original_filename} (${formatFileSize(file.file_size)})</li>`;
                    });
                    html += '</ul>';
                    fileList.innerHTML = html;
                    
                } catch (error) {
                    document.getElementById('fileList').innerHTML = 'Error loading files';
                }
            }
            
            function formatFileSize(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
        </script>
    </body>
    </html>
    """)

@app.get("/chat")
async def chat_page():
    return HTMLResponse("""
    <!DOCTYPE html>
<html>
<head>
    <title>Chat Interface</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .chat-container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 2px solid #4361ee; }
        .chat-messages { height: 400px; overflow-y: auto; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 20px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user-message { background: #e3f2fd; text-align: right; }
        .bot-message { background: #f5f5f5; }
        .chat-input { display: flex; gap: 10px; }
        .chat-input textarea { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; resize: vertical; }
        .chat-input button { padding: 10px 20px; background: #4361ee; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .chat-input button:hover { background: #3a56d4; }
        .source { font-size: 12px; color: #666; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>💬 Chat with Your Documents</h1>
            <a href="/dashboard" style="color: #4361ee;">← Back to Dashboard</a>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="message bot-message">
                👋 Hello! I'm your document assistant. Ask me questions about your uploaded PDF files.
            </div>
        </div>
        
        <div class="chat-input">
            <textarea id="messageInput" placeholder="Ask a question about your documents..." rows="3"></textarea>
            <button onclick="sendMessage()">Send</button>
        </div>
        
        <div style="margin-top: 20px;">
            <button onclick="clearChat()" style="background: #666;">Clear Chat</button>
            <button onclick="toggleContext()" style="background: #7209b7;">Toggle Context: <span id="contextStatus">On</span></button>
        </div>
    </div>

    <script>
        let useContext = true;
        let chatHistory = [];
        
        function toggleContext() {
            useContext = !useContext;
            document.getElementById('contextStatus').textContent = useContext ? 'On' : 'Off';
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        history: chatHistory,
                        use_context: useContext
                    }),
                    credentials: 'include'
                });
                
                const data = await response.json();
                
                // Add bot response to chat
                addMessage(data.response, 'bot', data.sources);
                
                // Update chat history
                chatHistory.push({ role: 'user', content: message });
                chatHistory.push({ role: 'assistant', content: data.response });
                
                // Keep only last 10 messages
                if (chatHistory.length > 10) {
                    chatHistory = chatHistory.slice(-10);
                }
                
            } catch (error) {
                addMessage('Error: Could not get response', 'bot');
            }
        }
        
        function addMessage(content, sender, sources = []) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = content.replace(/\\n/g, '<br>');
            
            if (sources && sources.length > 0) {
                const sourceDiv = document.createElement('div');
                sourceDiv.className = 'source';
                sourceDiv.innerHTML = '<strong>Sources:</strong> ' + 
                    sources.map(s => `${s.source}${s.page ? ' (Page ' + s.page + ')' : ''}`).join(', ');
                messageDiv.appendChild(sourceDiv);
            }
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function clearChat() {
            document.getElementById('chatMessages').innerHTML = 
                '<div class="message bot-message">👋 Chat cleared. Ask me questions about your documents.</div>';
            chatHistory = [];
        }
        
        // Allow Enter to send (Shift+Enter for new line)
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    </script>
</body>
</html>
    """)

@app.get("/health")
async def health_check():
    import sys
    
    # Check Ollama
    ollama_status = "unknown"
    try:
        import ollama
        ollama_status = "available"
    except ImportError:
        ollama_status = "not installed"
    
    # Check database
    db_exists = os.path.exists("app/data/library.db")
    
    return JSONResponse({
        "status": "ok",
        "service": "Library AI Assistant",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "ollama": ollama_status,
        "database": "exists" if db_exists else "missing",
        "pdfs_directory": os.path.exists("pdfs"),
        "data_directory": os.path.exists("app/data")
    })

# Add ingest endpoint
@app.post("/ingest")
async def trigger_ingestion():
    try:
        import subprocess
        result = subprocess.run(["python", "ingest_local.py"], capture_output=True, text=True)
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting Library AI Assistant...")
    print("📚 Open browser to: http://localhost:8000")
    print("🔑 Default login: admin / admin123")
    print("\n📂 Directory structure:")
    print(f"   PDFs folder: {os.path.abspath('pdfs')}")
    print(f"   Database: {os.path.abspath('app/data/library.db')}")
    print("\nPress Ctrl+C to stop\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
