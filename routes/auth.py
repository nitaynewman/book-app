from fastapi import APIRouter
from fastapi.responses import JSONResponse
from functions.email import send_email 
import os, requests
from dotenv import load_dotenv


load_dotenv()

AUDIO_WEB = os.getenv("AUDIO_WEB")
BACKEND_URL = os.getenv("BACKEND_URL")
MY_EMAIL = os.getenv("MY_EMAIL")
PASSWORD = os.getenv("PASSWORD")
router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

@router.post("/signin/")
async def signin(username, email):
    title = "AudioBook user request"
    msg = f"{username} wants permission\n{email}\nurl: {BACKEND_URL}/auth/add_user?username={username}&email={email}"
    data = {msg=msg, title=title, src_email=MY_EMAIL, dest_email=MY_EMAIL}
    response = await requests.post()
    return 'success'

@router.get('/add_user')
async def add_user(username, email):
    with open('users.txt', 'a') as f:
        f.write(f'\n{username}')

    title = "AudioBook"
    msg = f"Hello {username}. \nWe added your user {username} \nyou now can enter the website at: {AUDIO_WEB}"
    await send_email(msg=msg, title=title, src_email=MY_EMAIL, src_password=PASSWORD, dest_email=email)
    return 'success'

@router.get("/login/")
def login(username: str):
    try:
        with open('users.txt', 'r') as f:
            names = {line.strip() for line in f.readlines()} 
            print(username, names)

            if username in names:
                return JSONResponse(content={"message": "Login successful"}, status_code=200)
            else:
                return JSONResponse(content={"error": "Invalid username or you are not signed up!"}, status_code=401)

    except FileNotFoundError:
        print("Error: The file 'users.txt' not found")
        return JSONResponse(content={"error": "Server error: user file not found"}, status_code=501)

