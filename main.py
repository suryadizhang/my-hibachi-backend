from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import router
import logging

app = FastAPI()
app.include_router(router, prefix="/api/booking")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Change to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booking")

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle uncaught exceptions and return a generic error response."""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})