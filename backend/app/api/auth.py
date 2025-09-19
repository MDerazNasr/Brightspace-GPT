# backend/app/api/auth.py
"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.services.auth_service import auth_service
from app.schemas.auth import LoginResponse, UserResponse
from app.utils.exceptions import AuthenticationError

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory store for OAuth states (use Redis in production)
oauth_states = {}

@router.get("/login")
async def initiate_login():
    """
    Initiate OAuth login flow with Brightspace.
    
    Returns:
        Authorization URL and state for frontend to redirect user
    """
    try:
        auth_url, state = auth_service.generate_auth_url()
        
        # Store state for validation (use Redis in production)
        oauth_states[state] = {"created_at": "now"}  # Add timestamp in real implementation
        
        return {
            "auth_url": auth_url,
            "state": state,
            "message": "Redirect user to auth_url to complete login"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate auth URL: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate login")

@router.get("/brightspace/callback")
async def brightspace_callback(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle OAuth callback from Brightspace.
    
    This endpoint receives the authorization code and exchanges it for tokens.
    """
    # Get parameters from callback
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")
    
    # Handle OAuth errors
    if error:
        logger.error(f"OAuth error: {error}")
        # Redirect to frontend with error
        frontend_url = f"{settings.APP_URL}/login?error={error}"
        return RedirectResponse(url=frontend_url)
    
    # Validate required parameters
    if not code or not state:
        logger.error("Missing code or state in OAuth callback")
        frontend_url = f"{settings.APP_URL}/login?error=missing_parameters"
        return RedirectResponse(url=frontend_url)
    
    # Validate state (prevent CSRF attacks)
    if state not in oauth_states:
        logger.error(f"Invalid OAuth state: {state}")
        frontend_url = f"{settings.APP_URL}/login?error=invalid_state"
        return RedirectResponse(url=frontend_url)
    
    try:
        # Exchange code for tokens
        token_data = await auth_service.exchange_code_for_tokens(code, state)
        
        # Get user info from Brightspace
        brightspace_user_info = await auth_service.get_user_info_from_brightspace(
            token_data["access_token"]
        )
        
        # Create or update user in our database
        user = await auth_service.create_or_update_user(db, brightspace_user_info, token_data)
        
        # Create JWT token for our app
        jwt_token = auth_service.create_jwt_token(user)
        
        # Clean up OAuth state
        oauth_states.pop(state, None)
        
        # Redirect to frontend with success
        frontend_url = f"{settings.APP_URL}/dashboard?token={jwt_token}"
        return RedirectResponse(url=frontend_url)
        
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        frontend_url = f"{settings.APP_URL}/login?error=auth_failed"
        return RedirectResponse(url=frontend_url)
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        frontend_url = f"{settings.APP_URL}/login?error=server_error"
        return RedirectResponse(url=frontend_url)

@router.post("/token/refresh")
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh JWT token using existing session.
    """
    # Get current user from JWT
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    payload = auth_service.verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get user from database
    user = await auth_service.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new JWT token
    new_jwt_token = auth_service.create_jwt_token(user)
    
    return LoginResponse(
        access_token=new_jwt_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            brightspace_user_id=user.brightspace_user_id,
            is_verified=user.is_verified,
            preferences=user.preferences,
            created_at=user.created_at
        )
    )

@router.get("/me")
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Get current user information.
    """
    # Get current user from JWT
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = auth_header.split(" ")[1]
    payload = auth_service.verify_jwt_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get user from database
    user = await auth_service.get_user_by_id(db, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        brightspace_user_id=user.brightspace_user_id,
        is_verified=user.is_verified,
        preferences=user.preferences,
        created_at=user.created_at
    )

@router.post("/logout")
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Logout user (invalidate tokens).
    """
    # In a production app, you might want to:
    # 1. Revoke the Brightspace OAuth token
    # 2. Add JWT to a blacklist
    # 3. Clear any cached data
    
    return {"message": "Logged out successfully"}

@router.get("/status")
async def auth_status(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Check authentication status and Brightspace connection.
    """
    # Get current user from JWT
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"authenticated": False, "brightspace_connected": False}
    
    token = auth_header.split(" ")[1]
    payload = auth_service.verify_jwt_token(token)
    
    if not payload:
        return {"authenticated": False, "brightspace_connected": False}
    
    # Check if user has valid Brightspace token
    brightspace_token = await auth_service.get_valid_brightspace_token(db, payload["sub"])
    
    return {
        "authenticated": True,
        "brightspace_connected": brightspace_token is not None,
        "user_id": payload["sub"]
    }