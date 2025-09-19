# backend/app/models/user.py
"""
User and authentication models.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """User model for storing user information."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic user info
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    brightspace_user_id = Column(String(50), unique=True, index=True, nullable=True)
    student_number = Column(String(20), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Preferences
    preferences = Column(JSON, default=dict)  # Store user preferences as JSON
    timezone = Column(String(50), default="America/Toronto")
    language = Column(String(10), default="en")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(email='{self.email}', brightspace_id='{self.brightspace_user_id}')>"

class BrightspaceToken(Base):
    """Store OAuth tokens for Brightspace access."""
    
    __tablename__ = "brightspace_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)  # Foreign key to User.id
    
    # OAuth tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(20), default="Bearer")
    
    # Token metadata
    scope = Column(String(500), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self.expires_at:
            return False
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at
    
    def __repr__(self):
        return f"<BrightspaceToken(user_id='{self.user_id}', expires_at='{self.expires_at}')>"

class ChatSession(Base):
    """Store chat sessions and conversation history."""
    
    __tablename__ = "chat_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)  # Foreign key to User.id
    
    # Session metadata
    title = Column(String(255), nullable=True)  # Auto-generated or user-set
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChatSession(id='{self.id}', user_id='{self.user_id}', title='{self.title}')>"

class ChatMessage(Base):
    """Store individual chat messages."""
    
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, index=True)  # Foreign key to ChatSession.id
    
    # Message content
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Metadata
    brightspace_context = Column(JSON, nullable=True)  # Course/assignment context
    token_count = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<ChatMessage(role='{self.role}', session_id='{self.session_id}')>"

class UserCourseCache(Base):
    """Cache course data to reduce API calls."""
    
    __tablename__ = "user_course_cache"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)
    course_id = Column(String, nullable=False, index=True)
    
    # Cached data
    course_data = Column(JSON, nullable=False)  # Full course info
    assignments_data = Column(JSON, nullable=True)  # Assignments
    grades_data = Column(JSON, nullable=True)  # Grades
    content_data = Column(JSON, nullable=True)  # Course content
    
    # Cache metadata
    last_synced_at = Column(DateTime(timezone=True), server_default=func.now())
    sync_version = Column(Integer, default=1)  # Increment when data structure changes
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def is_stale(self, max_age_hours: int = 6) -> bool:
        """Check if cached data is stale."""
        if not self.last_synced_at:
            return True
        
        age = datetime.now(self.last_synced_at.tzinfo) - self.last_synced_at
        return age.total_seconds() > (max_age_hours * 3600)
    
    def __repr__(self):
        return f"<UserCourseCache(user_id='{self.user_id}', course_id='{self.course_id}')>"