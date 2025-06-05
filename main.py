from fastapi import FastAPI, Query, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes import book_pdf, Audio, blog, user_book, auth, portfolio, clean_file, investment
import requests
import uvicorn

 
app = FastAPI()


app.include_router(book_pdf.router)
app.include_router(Audio.router)
app.include_router(blog.router)
app.include_router(user_book.router)
app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(clean_file.router)
app.include_router(investment.router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
