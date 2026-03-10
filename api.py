"""
Real Project API - FastAPI Application
Main entry point for all English learning practice APIs.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file in the same directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# Import routers
from listening.router import router as listening_router
from reading.router import router as reading_router
from speaking.router import router as speaking_router
from writing.router import router as writing_router
from pratik.router import router as practice_router
from textbook.router import router as textbook_router

# Create FastAPI application
app = FastAPI(
    title="English Learning Practice API",
    description="""
## English Learning Practice API

A comprehensive API for generating educational English learning content.

### Features:

- **Listening Practice**: Generate realistic conversations between two characters
  for listening comprehension exercises. Adjustable difficulty levels and 
  conversation lengths to suit different learner needs.

- **Reading Practice**: Generate educational reading texts with customizable
  difficulty, length, content type, and required vocabulary words. Perfect for
  reading comprehension and vocabulary building exercises.

- **Writing Practice**: Generate writing tasks and analyze user responses with
  detailed feedback on grammar, vocabulary, style, and structure. Includes
  error detection with corrections and scoring.

- **Practice (Conversation)**: Interactive conversation practice with AI tutors.
  Create scenarios with different roles (friend, teacher, recruiter) and topics.
  Get real-time feedback on grammar and vocabulary as you practice.

### Authentication:
Currently, this API requires a `TOGETHER_API_KEY` environment variable to be set
for accessing the AI model that generates content.
""",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(listening_router, prefix="/api/v1")
app.include_router(reading_router, prefix="/api/v1")
app.include_router(speaking_router, prefix="/api/v1")
app.include_router(writing_router, prefix="/api/v1")
app.include_router(practice_router, prefix="/api/v1")
app.include_router(textbook_router, prefix="/api/v1")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": "English Learning Practice API",
        "version": "1.0.0",
        "description": "API for generating educational English learning content",
        "endpoints": {
            "listening": "/api/v1/listening",
            "reading": "/api/v1/reading",
            "speaking": "/api/v1/speaking",
            "writing": "/api/v1/writing",
            "practice": "/api/v1/practice",
            "documentation": "/docs",
            "openapi": "/openapi.json"
        }
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    together_api_configured = bool(os.getenv("TOGETHER_API_KEY"))
    
    return {
        "status": "healthy",
        "services": {
            "together_api": "configured" if together_api_configured else "not_configured"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
