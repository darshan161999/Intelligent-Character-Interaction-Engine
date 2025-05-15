"""
Main application module for Hero Agent Backend
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from dotenv import load_dotenv

# Import API router
from app.api import api_router
    
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hero Agent Backend",
    description="Backend service for Hero Agent interactive game with AI-powered character interactions",
    version="0.1.0",
    # Enable debug mode to show detailed error messages
    debug=True
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler to return detailed error messages"""
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Validation exception handler to return detailed error messages"""
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )

# Include API router
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    """
    Root endpoint to check if API is running
    """
    return {"message": "Hero Agent Backend API is running"}

@app.get("/health")
async def health():
    """
    Health check endpoint
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"  # Default to True for development
    
    uvicorn.run("main:app", host=host, port=port, reload=debug) 