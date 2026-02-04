from fastapi import FastAPI, UploadFile, File, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
import os
import shutil
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import uvicorn
from pathlib import Path
import subprocess
import asyncio
import sys
import logging
import json
import threading
import time
import psutil
import requests
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the app directory to Python path
current_file = Path(__file__).resolve()
app_dir = current_file.parent
project_root = app_dir.parent

sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(project_root))

# Import configuration FIRST
try:
    from app.config import config
    logger.info("✓ Configuration loaded")
except ImportError as e:
    logger.error(f"Failed to import config: {e}")
    sys.exit(1)

# Import custom modules
try:
    from app.utils import VectorStore, format_context
    from app.ai.llm import OllamaClient
    logger.info("✓ Imported modules")
except ImportError as e:
    logger.error(f"Import failed: {e}")
    sys.exit(1)

# Initialize components
try:
    vector_store = VectorStore()
    llm_client = OllamaClient()
    
    # Try to load vector store immediately
    vector_store.load()
    
    if vector_store.loaded:
        logger.info(f"✓ Vector store loaded with {len(vector_store.chunks)} chunks")
    else:
        logger.info("✓ Vector store initialized (not loaded yet - run ingestion first)")
    
    logger.info(f"✓ Components initialized with model: {config.chat_model}")
    
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    vector_store = None
    llm_client = None

# Global variables for task tracking
progress_data = {}
task_lock = threading.Lock()

# Initialize FastAPI
app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description="University of Embu Library Support AI"
)

# Add middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
pdfs_dir = config.pdfs_dir
data_dir = config.data_dir
templates_dir = config.templates_dir

# Templates
if not templates_dir.exists():
    os.makedirs(templates_dir, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

def format_file_size(bytes):
    if bytes == 0: return "0 Bytes"
    size_names = ["Bytes", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes >= 1024 and i < len(size_names) - 1:
        bytes /= 1024.0
        i += 1
    return f"{bytes:.2f} {size_names[i]}"

# ==================== TASK MANAGEMENT ====================

def update_task_progress(task_id: str, progress: int, message: str, status: str = "running"):
    """Update task progress in a thread-safe way"""
    with task_lock:
        if task_id not in progress_data:
            progress_data[task_id] = {
                "task_id": task_id,
                "progress": 0,
                "message": "",
                "status": "pending",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "logs": []
            }
        
        progress_data[task_id]["progress"] = progress
        progress_data[task_id]["message"] = message
        progress_data[task_id]["status"] = status
        
        if status in ["completed", "failed", "cancelled"]:
            progress_data[task_id]["end_time"] = datetime.now(timezone.utc).isoformat()
            progress_data[task_id]["duration"] = (
                datetime.now(timezone.utc) - 
                datetime.fromisoformat(progress_data[task_id]["start_time"].replace('Z', '+00:00'))
            ).total_seconds()
        
        # Keep log of last 100 messages
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        progress_data[task_id]["logs"].append(log_entry)
        if len(progress_data[task_id]["logs"]) > 100:
            progress_data[task_id]["logs"] = progress_data[task_id]["logs"][-100:]

def reindex_task(task_id: str):
    """Background task for reindexing documents"""
    try:
        update_task_progress(task_id, 0, "Starting reindexing process...")
        
        # Check if there are PDFs to process
        pdf_files = list(pdfs_dir.glob("*.pdf"))
        if not pdf_files:
            update_task_progress(task_id, 100, "No PDF files found to process", "completed")
            return
        
        total_files = len(pdf_files)
        
        # Simulate processing (in production, replace with actual ingestion)
        for i, pdf_file in enumerate(pdf_files):
            progress = int((i / total_files) * 100)
            update_task_progress(task_id, progress, f"Processing {pdf_file.name} ({i+1}/{total_files})")
            
            # Simulate processing time
            time.sleep(2)  # Simulate processing time
            
            # TODO: Add actual PDF processing here
            
        update_task_progress(task_id, 100, f"Successfully reindexed {total_files} files", "completed")
        
        # Reload vector store
        if vector_store:
            vector_store.load()
        
    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        update_task_progress(task_id, 0, f"Reindexing failed: {str(e)}", "failed")

def install_model_task(task_id: str, model_name: str):
    """Background task for installing models"""
    try:
        update_task_progress(task_id, 0, f"Starting installation of {model_name}")
        
        # Check if Ollama is available
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                update_task_progress(task_id, 0, "Ollama is not running or not accessible", "failed")
                return
        except:
            update_task_progress(task_id, 0, "Ollama is not running or not accessible", "failed")
            return
        
        # Run ollama pull command
        process = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Stream output and update progress
        line_count = 0
        max_lines = 50  # Estimated max lines for a pull operation
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
                
            if line:
                line_count += 1
                progress = min(95, int((line_count / max_lines) * 100))
                
                # Parse progress from ollama output
                line_lower = line.lower()
                if "pulling" in line_lower or "downloading" in line_lower:
                    update_task_progress(task_id, progress, f"Downloading {model_name}: {line.strip()}")
                elif "verifying" in line_lower:
                    update_task_progress(task_id, progress, f"Verifying {model_name}: {line.strip()}")
                elif "success" in line_lower or "complete" in line_lower or "pulled" in line_lower:
                    update_task_progress(task_id, 95, f"Finalizing {model_name}: {line.strip()}")
                else:
                    update_task_progress(task_id, progress, f"Installing {model_name}: {line.strip()}")
        
        process.wait()
        
        if process.returncode == 0:
            update_task_progress(task_id, 100, f"Successfully installed {model_name}", "completed")
        else:
            update_task_progress(task_id, 0, f"Failed to install {model_name} (exit code: {process.returncode})", "failed")
            
    except Exception as e:
        logger.error(f"Model installation failed: {e}")
        update_task_progress(task_id, 0, f"Installation failed: {str(e)}", "failed")

# ==================== ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": config.app_name,
        "app_version": config.app_version,
        "current_model": config.chat_model
    })

@app.get("/files", response_class=HTMLResponse)
async def manage_files(request: Request):
    files = []
    if pdfs_dir.exists():
        for f in os.listdir(pdfs_dir):
            if f.endswith(".pdf"):
                file_path = pdfs_dir / f
                files.append({
                    "name": f,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)),
                    "formatted_size": format_file_size(os.path.getsize(file_path))
                })
    files.sort(key=lambda x: x["modified"], reverse=True)
    
    vector_status = "Ready" if vector_store and vector_store.loaded else "Not processed"
    total_size = format_file_size(sum(f["size"] for f in files) if files else 0)

    return templates.TemplateResponse("files.html", {
        "request": request,
        "files": files,
        "total_files": len(files),
        "total_size": total_size,
        "vector_status": vector_status,
        "current_model": config.chat_model,
        "embedding_model": config.embedding_model
    })

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    files_count = len([f for f in os.listdir(pdfs_dir) if f.endswith(".pdf")]) if pdfs_dir.exists() else 0
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "total_files": files_count,
        "current_model": config.chat_model
    })

@app.post("/chat")
async def chat_api(request_data: dict):
    user_message = request_data.get("message") or request_data.get("query") or ""
    if not user_message:
        return {"response": "Please enter a question."}
    
    try:
        # Check if vector store is loaded
        if not vector_store:
            return {
                "response": "Vector store not initialized. Please restart the application.",
                "context_used": False,
                "model_used": config.chat_model
            }
        
        # Load vector store if not already loaded
        if not vector_store.loaded:
            vector_store.load()
        
        if not vector_store.loaded:
            return {
                "response": "No documents have been processed yet. Please upload and process PDF files first.",
                "context_used": False,
                "model_used": config.chat_model
            }
        
        # Check if Ollama is connected
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                return {
                    "response": "Ollama is not connected. Please ensure Ollama is running.",
                    "context_used": False,
                    "model_used": config.chat_model
                }
        except:
            return {
                "response": "Ollama is not connected. Please ensure Ollama is running.",
                "context_used": False,
                "model_used": config.chat_model
            }
        
        # 1. Search
        search_results = vector_store.search(user_message, k=config.search_default_k)
        logger.info(f"Chat search for '{user_message}' found {len(search_results)} results")
        
        if not search_results:
            return {
                "response": "I cannot find relevant information in the library documents.",
                "context_used": False,
                "model_used": config.chat_model
            }
        
        # 2. Format context
        context = format_context(search_results, max_length=config.max_context_length)
        logger.info(f"Chat formatted context length: {len(context)}")
        
        if not context or len(context.strip()) < 50:
            logger.warning(f"Context too short: {len(context)} chars")
            return {
                "response": "I found some information but it doesn't seem relevant to your question.",
                "context_used": False,
                "model_used": config.chat_model
            }
        
        # 3. Generate response
        response = llm_client.generate_response(prompt=user_message, context=context)
        
        return {
            "response": response,
            "context_used": len(context) > 0,
            "model_used": config.chat_model
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"response": f"System error: {str(e)}", "error": str(e)}

# --- STREAMING INGESTION ENDPOINT ---
@app.get("/ingest/stream")
async def stream_ingestion():
    """Run ingestion script and stream logs to client"""
    
    async def log_generator():
        ingest_script = project_root / "ingest.py"
        
        if not ingest_script.exists():
            yield "❌ Error: ingest.py not found\n"
            return
        
        # Run python script unbuffered
        process = subprocess.Popen(
            ["python3", "-u", str(ingest_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        yield "🚀 Starting ingestion process...\n"
        
        # Stream output line by line
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                yield line

        # Final status
        if process.returncode == 0:
            yield "\n✅ Ingestion Completed Successfully!\n"
            # Reload vector store in memory so the new data is available immediately
            if vector_store:
                vector_store.load()
                yield f"✅ Vector store reloaded with {len(vector_store.chunks) if vector_store.loaded else 0} chunks\n"
        else:
            yield f"\n❌ Process failed with exit code {process.returncode}\n"

    return StreamingResponse(log_generator(), media_type="text/plain")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded = []
    for file in files:
        if file.filename.lower().endswith('.pdf'):
            path = pdfs_dir / file.filename
            with open(path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            uploaded.append({"name": file.filename})
    return {"status": "success", "uploaded": uploaded}

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    path = pdfs_dir / filename
    if path.exists():
        os.remove(path)
        return {"status": "deleted"}
    raise HTTPException(404, "File not found")

@app.delete("/clear-all-files")
async def clear_all_files():
    try:
        # Clear PDFs
        if pdfs_dir.exists():
            for f in os.listdir(pdfs_dir):
                os.remove(pdfs_dir / f)
        # Clear Data
        if config.vector_store_path.exists():
            shutil.rmtree(config.vector_store_path)
            os.makedirs(config.vector_store_path, exist_ok=True)
        # Reset memory
        if vector_store:
            vector_store.loaded = False
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/config")
async def get_configuration():
    """Get current configuration and available models"""
    try:
        # Try to get models from Ollama
        chat_models = []
        embedding_models = []
        
        try:
            response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                ollama_models = response.json().get("models", [])
                
                # Common embedding model patterns
                embedding_patterns = [
                    "embed", "bge", "nomic", "mxbai", "e5", "minilm", "multilingual",
                    "instructor", "text-embedding", "sentence", "all-mpnet"
                ]
                
                for model in ollama_models:
                    model_name = model.get("name", "")
                    
                    # Check if it's an embedding model
                    is_embedding = any(pattern in model_name.lower() for pattern in embedding_patterns)
                    
                    if is_embedding:
                        embedding_models.append(model_name)
                    else:
                        chat_models.append(model_name)
        except Exception as e:
            logger.warning(f"Could not fetch Ollama models: {e}")
            # Fallback to default models
            chat_models = ["llama2:7b", "mistral:7b", "qwen:0.5b"]
            embedding_models = ["nomic-embed-text:latest", "all-minilm:latest"]
        
        return {
            "current": {
                "chat_model": config.chat_model,
                "embedding_model": config.embedding_model,
                "ollama_base_url": config.ollama_base_url
            },
            "available_models": {
                "chat_models": chat_models,
                "embedding_models": embedding_models
            },
            "system": {
                "pdfs_dir": str(pdfs_dir),
                "vector_store_path": str(config.vector_store_path),
                "max_context_length": config.max_context_length,
                "search_default_k": config.search_default_k
            }
        }
    except Exception as e:
        logger.error(f"Error getting config: {e}")
        raise HTTPException(500, f"Failed to get configuration: {str(e)}")

@app.put("/config/model")
async def update_model(data: dict):
    """Update model configuration"""
    try:
        success = True
        changes = {}
        
        if "chat_model" in data:
            changes["chat_model"] = data["chat_model"]
            success &= config.update_config("ollama", "chat_model", data["chat_model"])
            if llm_client:
                llm_client.model = data["chat_model"]
        
        if "embedding_model" in data:
            changes["embedding_model"] = data["embedding_model"]
            success &= config.update_config("ollama", "embedding_model", data["embedding_model"])
            if vector_store:
                vector_store.embedding_model = data["embedding_model"]
        
        if success:
            return {
                "success": True,
                "message": "Models updated successfully. Changes will take effect immediately.",
                "updated": changes
            }
        else:
            return {
                "success": False,
                "error": "Failed to update configuration file"
            }
            
    except Exception as e:
        logger.error(f"Error updating model: {e}")
        raise HTTPException(500, f"Failed to update model: {str(e)}")

@app.get("/test-chat")
async def test_chat():
    """Test endpoint to debug chat functionality"""
    test_query = "What is MyLOFT?"
    
    try:
        # Ensure vector store is loaded
        if not vector_store:
            return {"error": "Vector store not initialized"}
        
        # Load the vector store
        vector_store.load()
        
        if not vector_store.loaded:
            return {
                "error": "Vector store not loaded", 
                "vector_store_path": str(config.vector_store_path),
                "exists": config.vector_store_path.exists()
            }
        
        # 1. Search
        search_results = vector_store.search(test_query, k=5)
        
        # Debug: Log what we found
        logger.info(f"Test chat search for '{test_query}' found {len(search_results)} results")
        
        # 2. Format context
        context = format_context(search_results)
        logger.info(f"Test chat formatted context length: {len(context)}")
        
        # 3. Generate response
        response = llm_client.generate_response(prompt=test_query, context=context)
        
        return {
            "query": test_query,
            "search_results_count": len(search_results),
            "context_length": len(context),
            "response": response,
            "search_results_preview": [
                {
                    "score": r["score"],
                    "preview": r["content"][:100]
                }
                for r in search_results[:3]
            ],
            "vector_store_loaded": vector_store.loaded,
            "chunks_count": len(vector_store.chunks) if vector_store.loaded else 0
        }
    except Exception as e:
        logger.error(f"Test chat error: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}

@app.get("/reload-vector-store")
async def reload_vector_store():
    """Manually reload the vector store (useful after ingestion)"""
    try:
        if not vector_store:
            return {"success": False, "error": "Vector store not initialized"}
        
        vector_store.load()
        
        return {
            "success": True,
            "loaded": vector_store.loaded,
            "chunks_count": len(vector_store.chunks) if vector_store.loaded else 0,
            "vector_store_path": str(config.vector_store_path),
            "path_exists": config.vector_store_path.exists(),
            "index_exists": (config.vector_store_path / "vector_index.bin").exists(),
            "metadata_exists": (config.vector_store_path / "metadata.pkl").exists()
        }
    except Exception as e:
        logger.error(f"Failed to reload vector store: {e}")
        return {"success": False, "error": str(e)}

@app.get("/system/info")
def system_info():
    """Get system information including RAM"""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "memory": {
            "total_gb": round(mem.total / 1024**3, 1),
            "available_gb": round(mem.available / 1024**3, 1),
            "used_gb": round(mem.used / 1024**3, 1),
            "percent": mem.percent
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 1),
            "free_gb": round(disk.free / 1024**3, 1),
            "used_gb": round(disk.used / 1024**3, 1),
            "percent": disk.percent
        },
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.5),
            "cores": psutil.cpu_count(),
            "cores_logical": psutil.cpu_count(logical=True)
        }
    }

@app.get("/system/status")
async def system_status():
    """Get detailed system status"""
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    cpu_percent = psutil.cpu_percent(interval=0.5)
    
    # Process info
    process = psutil.Process()
    process_mem = process.memory_info()
    
    # Get number of active tasks
    with task_lock:
        active_tasks = sum(1 for task in progress_data.values() if task["status"] == "running")
    
    # Check Ollama status
    ollama_connected = False
    ollama_models = []
    try:
        response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            ollama_connected = True
            ollama_models = response.json().get("models", [])
    except:
        ollama_connected = False
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "cores": psutil.cpu_count(),
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        },
        "memory": {
            "total_gb": round(mem.total / 1024**3, 2),
            "available_gb": round(mem.available / 1024**3, 2),
            "used_gb": round(mem.used / 1024**3, 2),
            "percent": mem.percent,
            "swap_total_gb": round(psutil.swap_memory().total / 1024**3, 2),
            "swap_used_gb": round(psutil.swap_memory().used / 1024**3, 2)
        },
        "disk": {
            "total_gb": round(disk.total / 1024**3, 2),
            "used_gb": round(disk.used / 1024**3, 2),
            "free_gb": round(disk.free / 1024**3, 2),
            "percent": disk.percent
        },
        "process": {
            "memory_mb": round(process_mem.rss / 1024**2, 2),
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads()
        },
        "system": {
            "active_tasks": active_tasks,
            "total_tasks": len(progress_data),
            "ollama_connected": ollama_connected,
            "ollama_models_count": len(ollama_models),
            "vector_store_ready": vector_store.loaded if vector_store else False,
            "vector_store_chunks": len(vector_store.chunks) if vector_store and vector_store.loaded else 0,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

@app.get("/health")
async def health_check():
    """System health check"""
    ollama_ok = False
    ollama_models = []
    try:
        response = requests.get(f"{config.ollama_base_url}/api/tags", timeout=2)
        if response.status_code == 200:
            ollama_ok = True
            ollama_models = response.json().get("models", [])
    except Exception as e:
        logger.warning(f"Ollama connection failed: {e}")
    
    # Get memory info
    mem = psutil.virtual_memory()
    
    # Check vector store
    vector_store_ready = False
    vector_store_chunks = 0
    if vector_store:
        vector_store_ready = vector_store.loaded
        if vector_store.loaded:
            vector_store_chunks = len(vector_store.chunks)
    
    return {
        "status": "healthy" if ollama_ok and vector_store else "degraded",
        "vector_store_ready": vector_store_ready,
        "vector_store_chunks": vector_store_chunks,
        "ollama_connected": ollama_ok,
        "ollama_models_count": len(ollama_models),
        "current_model": config.chat_model,
        "embedding_model": config.embedding_model,
        "memory_usage": f"{mem.percent}% ({round(mem.available / 1024**3, 1)}GB available)",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.post("/install-model")
async def install_model(request: Request, background_tasks: BackgroundTasks):
    """Install a model via Ollama"""
    try:
        data = await request.json()
        model = data.get("model")
        
        if not model:
            raise HTTPException(status_code=400, detail="Model name required")
        
        # Generate task ID
        task_id = f"install_{model.replace(':', '_')}_{int(time.time())}"
        
        # Start installation in background
        background_tasks.add_task(install_model_task, task_id, model)
        
        return {
            "task_id": task_id,
            "message": f"Started installation of {model}",
            "status": "started",
            "monitor_url": f"/tasks/progress/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting model installation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start installation: {str(e)}")

# Add this endpoint to handle HEAD requests
@app.head("/install-model")
async def install_model_head():
    """Handle HEAD requests for install-model endpoint"""
    return JSONResponse(content={}, headers={"Allow": "POST, HEAD"})

@app.post("/tasks/start/{task_type}")
async def start_task(task_type: str, request: Request, background_tasks: BackgroundTasks):
    """Start a long-running task"""
    try:
        data = await request.json() if await request.body() else {}
        
        # Generate task ID
        timestamp = int(time.time())
        task_id = f"{task_type}_{timestamp}"
        
        if task_type == "reindex":
            # Start reindexing task
            background_tasks.add_task(reindex_task, task_id)
            
            return {
                "task_id": task_id,
                "message": "Started reindexing documents",
                "status": "started",
                "monitor_url": f"/tasks/progress/{task_id}"
            }
            
        elif task_type == "install_model":
            # This is handled by the /install-model endpoint
            raise HTTPException(400, "Use /install-model endpoint for model installation")
            
        else:
            raise HTTPException(400, f"Unknown task type: {task_type}")
            
    except Exception as e:
        logger.error(f"Error starting task: {e}")
        raise HTTPException(500, f"Failed to start task: {str(e)}")

@app.get("/tasks/progress/{task_id}")
async def get_task_progress(task_id: str):
    """Get progress of a long-running task"""
    with task_lock:
        if task_id in progress_data:
            task_info = progress_data[task_id].copy()
            
            # Calculate estimated time remaining if still running
            if task_info["status"] == "running":
                start_time = datetime.fromisoformat(task_info["start_time"].replace('Z', '+00:00'))
                elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                if task_info["progress"] > 0:
                    estimated_total = elapsed / (task_info["progress"] / 100)
                    remaining = estimated_total - elapsed
                    task_info["estimated_remaining_seconds"] = max(0, int(remaining))
                    task_info["elapsed_seconds"] = int(elapsed)
            
            return task_info
        else:
            raise HTTPException(404, f"Task {task_id} not found")

@app.get("/tasks/active")
async def get_active_tasks():
    """Get list of active tasks"""
    with task_lock:
        active_tasks = [
            {
                "task_id": task_id,
                "type": task_id.split('_')[0],
                "progress": info["progress"],
                "message": info["message"],
                "status": info["status"],
                "start_time": info["start_time"]
            }
            for task_id, info in progress_data.items()
            if info["status"] == "running"
        ]
        
        completed_tasks = [
            {
                "task_id": task_id,
                "type": task_id.split('_')[0],
                "progress": info["progress"],
                "status": info["status"],
                "start_time": info["start_time"],
                "end_time": info.get("end_time"),
                "duration": info.get("duration")
            }
            for task_id, info in progress_data.items()
            if info["status"] in ["completed", "failed", "cancelled"]
        ][-10:]  # Last 10 completed tasks
        
        return {
            "active": active_tasks,
            "recent": completed_tasks,
            "total_tasks": len(progress_data)
        }

@app.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """Cancel a running task"""
    with task_lock:
        if task_id in progress_data:
            if progress_data[task_id]["status"] == "running":
                progress_data[task_id]["status"] = "cancelled"
                progress_data[task_id]["message"] = "Task cancelled by user"
                progress_data[task_id]["end_time"] = datetime.now(timezone.utc).isoformat()
                return {"status": "cancelled", "task_id": task_id}
            else:
                return {"status": "not_running", "task_id": task_id}
        else:
            raise HTTPException(404, f"Task {task_id} not found")

@app.get("/api/files")
async def api_files():
    """API endpoint to get file list"""
    files = []
    if pdfs_dir.exists():
        for f in os.listdir(pdfs_dir):
            if f.endswith(".pdf"):
                file_path = pdfs_dir / f
                files.append({
                    "name": f,
                    "size": os.path.getsize(file_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                    "formatted_size": format_file_size(os.path.getsize(file_path))
                })
    files.sort(key=lambda x: x["modified"], reverse=True)
    return {"files": files, "count": len(files)}

# Add a simple test endpoint
@app.get("/test")
async def test_endpoint():
    return {"status": "ok", "message": "Server is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
