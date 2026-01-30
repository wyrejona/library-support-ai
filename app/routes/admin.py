from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from app.database import get_db, User, UploadedFile, QueryLog
from app.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])

class StatsResponse(BaseModel):
    total_users: int
    total_files: int
    total_queries: int
    storage_used: int  # in bytes

@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    # Only admins can access this
    if not token.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    total_users = db.query(User).count()
    total_files = db.query(UploadedFile).count()
    total_queries = db.query(QueryLog).count()
    
    # Calculate total storage used
    files = db.query(UploadedFile).all()
    storage_used = sum(file.file_size for file in files if file.file_size)
    
    return StatsResponse(
        total_users=total_users,
        total_files=total_files,
        total_queries=total_queries,
        storage_used=storage_used
    )

@router.get("/users")
async def get_all_users(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    if not token.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "uploads_count": len(user.uploads),
            "queries_count": len(user.queries)
        }
        for user in users
    ]
