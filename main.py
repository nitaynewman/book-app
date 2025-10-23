from fastapi import FastAPI, Query, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import book_pdf, Audio, blog, user_book, auth, portfolio, clean_file, Investment, nn_data, questions, locations, pizza, tictactoe
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import requests
import uvicorn, sys, asyncio


if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = FastAPI(title="Portfolio API", version="1.0.0")


app.include_router(book_pdf.router)
app.include_router(Audio.router)
app.include_router(blog.router)
app.include_router(user_book.router)
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(clean_file.router)
app.include_router(Investment.router)
app.include_router(nn_data.router)
app.include_router(questions.router)
app.include_router(locations.router)
app.include_router(pizza.router)
app.include_router(tictactoe.router)



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
