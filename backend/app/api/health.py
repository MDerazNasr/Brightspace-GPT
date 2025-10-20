# backend/app/api/health.py

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("")
async def health_check():
    """
    Health check endpoint for the extension to test connectivity
    """
    return {
        "status": "healthy",
        "service": "Brightspace GPT API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }