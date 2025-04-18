from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import audio, books
import uvicorn

app = FastAPI()

app.include_router(audio.router)
app.include_router(books.router)

@app.get("/")
def hello():
    return {"hello": True}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
