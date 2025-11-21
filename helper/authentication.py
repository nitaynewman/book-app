# auth/api_key_auth.py (COMPLETE UPDATE)
from fastapi import Header, HTTPException, status
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Store your API keys and their permissions
API_KEYS = {
    # Auth keys
    os.getenv("API_KEY_AUTH", "your-auth-key"): ["auth", 'book', 'audio', 'blog', 'user_book'],
    os.getenv("API_KEY_ADMIN", "your-admin-key"): ["admin"],
    
    # Feature-specific keys
    os.getenv("API_KEY_BOOK", "your-book-key"): ["book"],
    os.getenv("API_KEY_AUDIO", "your-audio-key"): ["audio"],
    os.getenv("API_KEY_BLOG", "your-blog-key"): ["blog"],
    os.getenv("API_KEY_USER_BOOK", "your-user-book-key"): ["user_book"],
    
    # General key with multiple permissions (for frontend)
    os.getenv("API_KEY_GENERAL", "your-general-key"): ["auth", "book", "audio", "blog", "user_book"],
    
    # Master key with all permissions
    os.getenv("API_KEY_ALL", "your-master-key"): ["auth", "admin", "book", "audio", "blog", "user_book"],
}


def verify_api_key(api_key: str, required_permission: str) -> bool:
    """Verify if the API key exists and has the required permission"""
    if api_key not in API_KEYS:
        return False
    
    permissions = API_KEYS[api_key]
    return required_permission in permissions


class APIKeyChecker:
    def __init__(self, permission: str):
        self.permission = permission
    
    async def __call__(self, x_api_key: str = Header(None)):
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key missing. Please provide X-API-Key header."
            )
        
        if not verify_api_key(x_api_key, self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid API Key or insufficient permissions for '{self.permission}'"
            )
        
        return x_api_key