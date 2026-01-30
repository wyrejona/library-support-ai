from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db, QueryLog, User
from app.auth import get_current_user
from app.utils import VectorStore, format_context
from app.ai.llm import ollama_client

router = APIRouter(prefix="/api/chat", tags=["chat"])

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = None
    use_context: bool = True

class ChatResponse(BaseModel):
    response: str
    sources: List[dict] = []
    query_id: int

# Initialize vector store
vector_store = VectorStore()

@router.post("")
async def chat_endpoint(
    request: ChatRequest,
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    try:
        context = ""
        sources = []
        
        if request.use_context:
            # Search for relevant context in vector store
            search_results = vector_store.search(request.message, k=5)
            if search_results:
                context = format_context(search_results)
                sources = [{
                    'content': result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                    'source': result['source'],
                    'page': result.get('page')
                } for result in search_results]
        
        # Convert history to list of dicts
        history_list = []
        if request.history:
            for msg in request.history:
                history_list.append({"role": msg.role, "content": msg.content})
        
        # Generate response using Ollama
        response = ollama_client.generate_response(
            prompt=request.message,
            context=context,
            history=history_list
        )
        
        # Log the query
        query_log = QueryLog(
            user_id=token.id,
            query=request.message,
            response=response,
            sources=json.dumps(sources) if sources else None
        )
        
        db.add(query_log)
        db.commit()
        db.refresh(query_log)
        
        # Cleanup old logs
        from app.database import cleanup_old_logs
        cleanup_old_logs(db)
        
        return {
            "response": response,
            "sources": sources,
            "query_id": query_log.id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    queries = db.query(QueryLog).filter(
        QueryLog.user_id == token.id
    ).order_by(QueryLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": q.id,
            "query": q.query,
            "response": q.response,
            "sources": json.loads(q.sources) if q.sources else [],
            "created_at": q.created_at
        }
        for q in queries
    ]
