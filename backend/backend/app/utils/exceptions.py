"""
Custom exceptions for the uOttawa Brightspace Assistant.
"""

class AssistantError(Exception):
    """Base exception for the assistant application."""
    pass

class BrightspaceError(AssistantError):
    """Exception raised for Brightspace API errors."""
    pass

class AuthenticationError(AssistantError):
    """Exception raised for authentication failures."""
    pass

class LLMError(AssistantError):
    """Exception raised for LLM service errors."""
    pass

class VectorDBError(AssistantError):
    """Exception raised for vector database errors."""
    pass

class RateLimitError(AssistantError):
    """Exception raised when rate limits are exceeded."""
    pass

class DataSyncError(AssistantError):
    """Exception raised during data synchronization."""
    pass
