"""
uOttawa Brightspace LLM Assistant - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from app.core.config import settings
from app.core.database import init_db
from app.api import auth, chat, courses, users, health

# Create FastAPI app
app = FastAPI(
    title="uOttawa Brightspace Assistant",
    description="AI-powered assistant for uOttawa Brightspace courses",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "assistant.uottawa.ca"]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(courses.router, prefix="/api/courses", tags=["Courses"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(health.router, prefix="/api/health", tags=["Health"])

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    pass

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "uOttawa Brightspace LLM Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
