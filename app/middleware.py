from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.auth import get_current_user
from app.database import get_db
import re

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        path = request.url.path
        
        # Public paths that don't require authentication
        public_paths = [
            "/",
            "/login",
            "/static/",
            "/api/auth/login",
            "/api/auth/register",
            "/health"
        ]
        
        # Check if path is public
        is_public = any(path.startswith(public_path) for public_path in public_paths)
        
        if not is_public:
            # Check for Authorization header or session cookie
            auth_header = request.headers.get("authorization")
            session_cookie = request.cookies.get("session_token")
            
            if not auth_header and not session_cookie:
                if path.startswith("/api/"):
                    raise HTTPException(status_code=401, detail="Not authenticated")
                else:
                    # Redirect to login for web pages
                    response = RedirectResponse(url="/login")
                    await response(scope, receive, send)
                    return
            
            # Validate token
            token = session_cookie or auth_header.replace("Bearer ", "")
            db = next(get_db())
            try:
                user = get_current_user(token, db)
                # Attach user to request state
                scope["user"] = user
            except:
                if path.startswith("/api/"):
                    raise HTTPException(status_code=401, detail="Invalid token")
                else:
                    response = RedirectResponse(url="/login")
                    await response(scope, receive, send)
                    return
        
        await self.app(scope, receive, send)
