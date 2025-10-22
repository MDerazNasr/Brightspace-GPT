# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat, health
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verify API key is loaded
api_key = os.getenv('MISTRAL_API_KEY')
if api_key:
    logger.info(f"✅ MISTRAL_API_KEY loaded: {api_key[:10]}...{api_key[-4:]}")
else:
    logger.error("❌ MISTRAL_API_KEY not found in environment!")
    logger.error("   Make sure backend/.env exists and contains MISTRAL_API_KEY")

# Test Mistral import
try:
    from mistralai import Mistral
    logger.info("✅ Mistral package imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import Mistral: {e}")
    logger.error("   Run: pip install mistralai")
    
# Create FastAPI app
app = FastAPI(
    title="Brightspace GPT API",
    description="AI-powered assistant for University of Ottawa Brightspace",
    version="1.0.0"
)

# Configure CORS to allow Chrome extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # Allow all Chrome extensions
        "http://localhost:*",    # Allow local development
        "http://127.0.0.1:*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": "Brightspace GPT API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)