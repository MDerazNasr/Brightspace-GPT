# backend/app/core/database.py
"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import Base
import logging

logger = logging.getLogger(__name__)

# Convert sync PostgreSQL URL to async if needed
async_database_url = settings.DATABASE_URL
if async_database_url.startswith("postgresql://"):
    async_database_url = async_database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine
engine = create_async_engine(
    async_database_url,
    echo=settings.LOG_SQL_QUERIES,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def init_db():
    """Initialize database tables."""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models.user import User, BrightspaceToken, ChatSession, ChatMessage, UserCourseCache
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# backend/scripts/init_database.py
"""
Script to initialize the database.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import init_db
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Initialize the database."""
    logger.info("🗄️  Initializing uOttawa Brightspace Assistant Database")
    logger.info("=" * 60)
    
    logger.info(f"Database URL: {settings.DATABASE_URL}")
    
    try:
        await init_db()
        logger.info("✅ Database initialization completed successfully!")
        
        logger.info("\n📋 Created tables:")
        logger.info("   - users (user accounts)")
        logger.info("   - brightspace_tokens (OAuth tokens)")
        logger.info("   - chat_sessions (conversation sessions)")
        logger.info("   - chat_messages (individual messages)")
        logger.info("   - user_course_cache (cached course data)")
        
        logger.info("\n🚀 Next steps:")
        logger.info("   1. Start the backend server: uvicorn app.main:app --reload")
        logger.info("   2. Register OAuth app with Brightspace")
        logger.info("   3. Test user authentication flow")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)