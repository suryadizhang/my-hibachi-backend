from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

app = FastAPI()
app.include_router(router, prefix="/api/booking")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Change to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)