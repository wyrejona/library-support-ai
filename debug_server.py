#!/usr/bin/env python3
"""
Debug server for University of Embu Library AI
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os

app = FastAPI()

# Create directories
os.makedirs("pdfs", exist_ok=True)
os.makedirs("data", exist_ok=True)

@app.get("/")
async def home():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Library AI - Debug</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background: #d4edda; color: #155724; }
            .error { background: #f8d7da; color: #721c24; }
        </style>
    </head>
    <body>
        <h1>University of Embu Library AI - Debug Mode</h1>
        <div class="status success">Server is running!</div>
        <h3>Test Endpoints:</h3>
        <ul>
            <li><a href="/health">/health</a> - Health check</li>
            <li><a href="/files">/files</a> - List PDFs</li>
            <li><a href="/test">/test</a> - Simple test</li>
        </ul>
        <h3>Server Info:</h3>
        <p>Current directory: <code>""" + os.getcwd() + """</code></p>
        <p>PDFs directory: <code>""" + str(os.path.exists("pdfs")) + """</code></p>
        <p>Data directory: <code>""" + str(os.path.exists("data")) + """</code></p>
    </body>
    </html>
    """)

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "directories": {
            "pdfs": os.path.exists("pdfs"),
            "data": os.path.exists("data")
        },
        "pdf_count": len([f for f in os.listdir("pdfs") if f.endswith(".pdf")]) if os.path.exists("pdfs") else 0
    }

@app.get("/files")
async def list_files():
    try:
        if not os.path.exists("pdfs"):
            return {"files": [], "message": "pdfs directory doesn't exist"}
        
        files = []
        for f in os.listdir("pdfs"):
            if f.lower().endswith(".pdf"):
                files.append({"name": f})
        
        return {"files": files, "count": len(files)}
    except Exception as e:
        return {"error": str(e), "files": []}

@app.get("/test")
async def test():
    return {"message": "Test endpoint works", "timestamp": "now"}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Debug Server on http://0.0.0.0:8000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
