#!/usr/bin/env python3
"""
Database initialization script for uOttawa Brightspace Assistant.
Run this to create all database tables.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path so we can import our modules
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import init_db
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Initialize the database."""
    logger.info("🗄️  Initializing uOttawa Brightspace Assistant Database")
    logger.info("=" * 60)
    
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    print()
    
    try:
        # Initialize database tables
        await init_db()
        
        logger.info("✅ Database initialization completed successfully!")
        logger.info("")
        logger.info("📋 Created tables:")
        logger.info("   - users (user accounts and profiles)")
        logger.info("   - brightspace_tokens (OAuth access tokens)")
        logger.info("   - chat_sessions (conversation sessions)")
        logger.info("   - chat_messages (individual chat messages)")
        logger.info("   - user_course_cache (cached course data)")
        logger.info("")
        logger.info("🚀 Next steps:")
        logger.info("   1. Start the backend server:")
        logger.info("      cd backend && uvicorn app.main:app --reload")
        logger.info("   2. Test the OAuth system:")
        logger.info("      python scripts/test_oauth_flow.py")
        logger.info("   3. Register OAuth app with uOttawa Brightspace")
        logger.info("   4. Update .env with OAuth credentials")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        logger.error("")
        logger.error("🔍 Troubleshooting:")
        logger.error("   - Make sure PostgreSQL is running")
        logger.error("   - Check DATABASE_URL in your .env file")
        logger.error("   - Ensure database exists: createdb uottawa_assistant")
        logger.error(f"   - Current DATABASE_URL: {settings.DATABASE_URL}")
        
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
