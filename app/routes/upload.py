from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from app.database import get_db, UploadedFile, User
from app.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/upload", tags=["upload"])

ALLOWED_EXTENSIONS = {'.pdf'}

def allowed_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)

@router.post("/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Ensure uploads directory exists
    os.makedirs(settings.pdfs_dir, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.pdfs_dir, unique_filename)
    
    try:
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create database record
        db_file = UploadedFile(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            user_id=token.id
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {
            "message": "File uploaded successfully",
            "filename": unique_filename,
            "original_filename": file.filename,
            "file_size": file_size,
            "uploaded_at": db_file.uploaded_at
        }
    
    except Exception as e:
        # Clean up file if error occurred
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/files")
async def get_uploaded_files(
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    files = db.query(UploadedFile).filter(UploadedFile.user_id == token.id).all()
    return [
        {
            "id": file.id,
            "original_filename": file.original_filename,
            "filename": file.filename,
            "file_size": file.file_size,
            "uploaded_at": file.uploaded_at,
            "processed": file.processed,
            "error": file.error
        }
        for file in files
    ]

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    token: str = Depends(get_current_user)
):
    file = db.query(UploadedFile).filter(
        UploadedFile.id == file_id,
        UploadedFile.user_id == token.id
    ).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        # Delete file from disk
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
        
        # Delete from database
        db.delete(file)
        db.commit()
        
        return {"message": "File deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
