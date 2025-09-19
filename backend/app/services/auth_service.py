# backend/app/services/auth_service.py
"""
Authentication service handling OAuth flows and user management.
"""
import httpx
import secrets
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.user import User, BrightspaceToken
from app.utils.exceptions import AuthenticationError
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Handle authentication flows and user management."""
    
    def __init__(self):
        self.client_id = settings.BRIGHTSPACE_OAUTH_CLIENT_ID
        self.client_secret = settings.BRIGHTSPACE_OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.BRIGHTSPACE_OAUTH_REDIRECT_URI
        self.scope = settings.BRIGHTSPACE_OAUTH_SCOPE
        
        # Brightspace OAuth URLs (these might need adjustment for uOttawa)
        self.auth_url = f"{settings.BRIGHTSPACE_API_URL.replace('/api', '')}/oauth2/auth"
        self.token_url = f"{settings.BRIGHTSPACE_API_URL}/oauth2/token"
    
    def generate_auth_url(self) -> Tuple[str, str]:
        """
        Generate OAuth authorization URL and state parameter.
        
        Returns:
            Tuple of (auth_url, state)
        """
        # Generate secure random state
        state = secrets.token_urlsafe(32)
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": state,
            "access_type": "offline",  # Request refresh token
        }
        
        auth_url = f"{self.auth_url}?{urlencode(params)}"
        return auth_url, state
    
    async def exchange_code_for_tokens(self, code: str, state: str) -> Dict[str, any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from callback
            state: State parameter for validation
            
        Returns:
            Token response data
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Token exchange failed: {e.response.status_code} - {e.response.text}")
            raise AuthenticationError(f"Failed to exchange code for tokens: {e.response.text}")
        except Exception as e:
            logger.error(f"Token exchange error: {str(e)}")
            raise AuthenticationError(f"Token exchange error: {str(e)}")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response
        """
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Token refresh failed: {e.response.status_code} - {e.response.text}")
            raise AuthenticationError(f"Failed to refresh token: {e.response.text}")
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise AuthenticationError(f"Token refresh error: {str(e)}")
    
    async def get_user_info_from_brightspace(self, access_token: str) -> Dict[str, any]:
        """
        Get user information from Brightspace using access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User information from Brightspace
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Get user info from Brightspace whoami endpoint
        user_info_url = f"{settings.BRIGHTSPACE_API_URL}/lp/{settings.BRIGHTSPACE_API_VERSION}/users/whoami"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(user_info_url, headers=headers)
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Get user info failed: {e.response.status_code} - {e.response.text}")
            raise AuthenticationError(f"Failed to get user info: {e.response.text}")
        except Exception as e:
            logger.error(f"Get user info error: {str(e)}")
            raise AuthenticationError(f"Get user info error: {str(e)}")
    
    async def create_or_update_user(
        self, 
        db: AsyncSession, 
        brightspace_user_info: Dict[str, any],
        token_data: Dict[str, any]
    ) -> User:
        """
        Create new user or update existing user with Brightspace info.
        
        Args:
            db: Database session
            brightspace_user_info: User info from Brightspace
            token_data: OAuth token data
            
        Returns:
            User object
        """
        brightspace_user_id = str(brightspace_user_info.get("Identifier"))
        email = brightspace_user_info.get("EmailAddress")
        full_name = f"{brightspace_user_info.get('FirstName', '')} {brightspace_user_info.get('LastName', '')}".strip()
        
        # Check if user already exists
        stmt = select(User).where(User.brightspace_user_id == brightspace_user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.email = email or user.email
            user.full_name = full_name or user.full_name
            user.last_login_at = datetime.now()
            logger.info(f"Updated existing user: {user.email}")
        else:
            # Create new user
            user = User(
                email=email,
                full_name=full_name,
                brightspace_user_id=brightspace_user_id,
                is_verified=True,  # Verified through Brightspace OAuth
                last_login_at=datetime.now()
            )
            db.add(user)
            logger.info(f"Created new user: {user.email}")
        
        # Save or update OAuth tokens
        await self._save_brightspace_tokens(db, user.id, token_data)
        
        await db.commit()
        await db.refresh(user)
        return user
    
    async def _save_brightspace_tokens(
        self, 
        db: AsyncSession, 
        user_id: str, 
        token_data: Dict[str, any]
    ):
        """Save or update Brightspace OAuth tokens for user."""
        
        # Check if token record exists
        stmt = select(BrightspaceToken).where(BrightspaceToken.user_id == user_id)
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()
        
        # Calculate expiration time
        expires_in = token_data.get("expires_in")
        expires_at = None
        if expires_in:
            expires_at = datetime.now() + timedelta(seconds=int(expires_in))
        
        if token_record:
            # Update existing tokens
            token_record.access_token = token_data["access_token"]
            token_record.refresh_token = token_data.get("refresh_token")
            token_record.token_type = token_data.get("token_type", "Bearer")
            token_record.scope = token_data.get("scope")
            token_record.expires_at = expires_at
            token_record.updated_at = datetime.now()
        else:
            # Create new token record
            token_record = BrightspaceToken(
                user_id=user_id,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                token_type=token_data.get("token_type", "Bearer"),
                scope=token_data.get("scope"),
                expires_at=expires_at
            )
            db.add(token_record)
    
    async def get_valid_brightspace_token(self, db: AsyncSession, user_id: str) -> Optional[str]:
        """
        Get a valid Brightspace access token for user, refreshing if needed.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            Valid access token or None
        """
        stmt = select(BrightspaceToken).where(BrightspaceToken.user_id == user_id)
        result = await db.execute(stmt)
        token_record = result.scalar_one_or_none()
        
        if not token_record:
            return None
        
        # Check if token is expired
        if token_record.is_expired() and token_record.refresh_token:
            try:
                # Refresh the token
                new_token_data = await self.refresh_access_token(token_record.refresh_token)
                await self._save_brightspace_tokens(db, user_id, new_token_data)
                await db.commit()
                return new_token_data["access_token"]
                
            except AuthenticationError:
                logger.warning(f"Failed to refresh token for user {user_id}")
                return None
        
        elif not token_record.is_expired():
            return token_record.access_token
        
        return None
    
    def create_jwt_token(self, user: User) -> str:
        """
        Create JWT token for user session.
        
        Args:
            user: User object
            
        Returns:
            JWT token string
        """
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        
        to_encode = {
            "sub": user.id,
            "email": user.email,
            "brightspace_user_id": user.brightspace_user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, any]]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None
    
    async def get_user_by_id(self, db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

# Singleton instance
auth_service = AuthService()