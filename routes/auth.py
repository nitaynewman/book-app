from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from functions.email import send_email 
import os
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor
from helper.authentication import APIKeyChecker
from helper.supabase import supabase_service

load_dotenv()

AUDIO_WEB = os.getenv("AUDIO_WEB")
BACKEND_URL = os.getenv("BACKEND_URL")
MY_EMAIL = os.getenv("MY_EMAIL")

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

# Thread pool for sync operations
executor = ThreadPoolExecutor(max_workers=3)

# Create API key checkers for different permissions
auth_checker = APIKeyChecker("auth")
admin_checker = APIKeyChecker("admin")


@router.post("/signin/")
async def signin(
    username: str, 
    email: str,
    api_key: str = Depends(auth_checker)
):
    """
    User requests access - sends email to admin for approval
    Protected with API key
    """
    try:
        title = "AudioBook user request"
        msg = f"{username} wants permission\n{email}\nurl: {BACKEND_URL}/auth/add_user?username={username}&email={email}"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            send_email,
            'nitay',
            MY_EMAIL,
            title,
            msg
        )
        
        return JSONResponse(
            content={"success": True, "message": "Sign-in request sent successfully"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@router.get('/add_user')
async def add_user(
    username: str, 
    email: str,
    api_key: str = Depends(admin_checker)
):
    """
    Admin endpoint to add user and send confirmation email
    Protected with admin API key
    """
    try:
        # Create user in supabase
        supabase_service.add_user(username=username, email=email)
        
        # Send confirmation email
        title = "AudioBook"
        msg = f"Hello {username}.\nWe added your user {username}\nyou now can enter the website at: {AUDIO_WEB}"
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            send_email,
            MY_EMAIL,
            email,
            title,
            msg
        )
        
        return JSONResponse(
            content={"success": True, "message": f"User {username} added successfully"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@router.get("/login/")
def login(
    username: str,
    api_key: str = Depends(auth_checker)
):
    """
    User login endpoint - checks if username exists
    Protected with API key
    """
    try:
        # Check if user exists in Supabase
        user_exists = supabase_service.check_user(username=username)
        
        if user_exists:
            return JSONResponse(
                content={"success": True, "message": "Login successful"},
                status_code=200
            )
        else:
            return JSONResponse(
                content={"success": False, "error": "Invalid username or you are not signed up!"},
                status_code=401
            )
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


# Optional: Health check endpoint (no API key required)
@router.get("/health")
def health_check():
    """Public health check endpoint"""
    return {"status": "ok", "service": "auth"}