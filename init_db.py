#!/usr/bin/env python3
"""
Initialize the database
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, User, create_tables
from app.auth import get_password_hash

def init_database():
    """Initialize database with admin user"""
    create_tables()
    
    db = SessionLocal()
    
    # Check if admin user exists
    admin = db.query(User).filter(User.username == "admin").first()
    
    if not admin:
        # Create admin user
        admin = User(
            username="admin",
            email="admin@library.local",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("✅ Database already initialized")
    
    db.close()

if __name__ == "__main__":
    print("🚀 Initializing Database...")
    init_database()
    print("✅ Database initialization complete!")
