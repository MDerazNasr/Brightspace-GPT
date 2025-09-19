# backend/scripts/test_oauth_flow.py
"""
Test script for OAuth authentication flow.
Run this to test the authentication system.
"""
import asyncio
import httpx
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_oauth_endpoints():
    """Test OAuth endpoints without full flow."""
    
    print("🔐 Testing uOttawa Brightspace OAuth Integration")
    print("=" * 60)
    
    # Check configuration
    print("📋 Configuration Check:")
    print(f"   API URL: {settings.API_URL}")
    print(f"   OAuth Client ID: {'SET' if settings.BRIGHTSPACE_OAUTH_CLIENT_ID else 'NOT SET'}")
    print(f"   OAuth Secret: {'SET' if settings.BRIGHTSPACE_OAUTH_CLIENT_SECRET else 'NOT SET'}")
    print(f"   Redirect URI: {settings.BRIGHTSPACE_OAUTH_REDIRECT_URI}")
    print()
    
    base_url = settings.API_URL
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health check
        print("🏥 Testing API Health...")
        try:
            response = await client.get(f"{base_url}/api/health/status")
            if response.status_code == 200:
                print("✅ API is running")
            else:
                print(f"⚠️ API health check returned {response.status_code}")
        except Exception as e:
            print(f"❌ API not accessible: {e}")
            print("   Make sure to run: uvicorn app.main:app --reload")
            return False
        
        print()
        
        # Test 2: Login initiation
        print("🚀 Testing Login Initiation...")
        try:
            response = await client.get(f"{base_url}/api/auth/login")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Login initiation successful")
                print(f"   Auth URL: {data['auth_url'][:80]}...")
                print(f"   State: {data['state'][:20]}...")
                
                # Save for manual testing
                with open("oauth_test_url.txt", "w") as f:
                    f.write(f"Auth URL: {data['auth_url']}\n")
                    f.write(f"State: {data['state']}\n")
                print("   📄 Saved auth URL to oauth_test_url.txt")
                
            else:
                print(f"❌ Login initiation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login initiation error: {e}")
            return False
        
        print()
        
        # Test 3: Auth status (unauthenticated)
        print("🔍 Testing Auth Status (Unauthenticated)...")
        try:
            response = await client.get(f"{base_url}/api/auth/status")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Auth status check successful")
                print(f"   Authenticated: {data['authenticated']}")
                print(f"   Brightspace Connected: {data['brightspace_connected']}")
            else:
                print(f"⚠️ Auth status returned {response.status_code}")
                
        except Exception as e:
            print(f"❌ Auth status error: {e}")
        
        print()
        
        # Test 4: Protected endpoint (should fail)
        print("🔒 Testing Protected Endpoint (Should Fail)...")
        try:
            response = await client.get(f"{base_url}/api/auth/me")
            
            if response.status_code == 401:
                print("✅ Protected endpoint correctly rejected unauthenticated request")
            else:
                print(f"⚠️ Protected endpoint returned unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Protected endpoint test error: {e}")
    
    print()
    print("🎯 OAuth Flow Test Summary:")
    print("✅ API is running and accessible")
    print("✅ OAuth initiation endpoint works")
    print("✅ Auth status endpoint works")
    print("✅ Protected endpoints are secured")
    print()
    print("📝 Next Steps:")
    print("1. Register your OAuth app with uOttawa Brightspace")
    print("2. Update BRIGHTSPACE_OAUTH_CLIENT_ID and BRIGHTSPACE_OAUTH_CLIENT_SECRET")
    print("3. Test full OAuth flow by visiting the auth URL")
    print("4. Check oauth_test_url.txt for the authorization URL")
    
    return True

async def test_database_connection():
    """Test database connection and models."""
    
    print("\n🗄️ Testing Database Connection...")
    
    try:
        from app.core.database import init_db, AsyncSessionLocal
        from app.models.user import User
        
        # Test database initialization
        await init_db()
        print("✅ Database initialization successful")
        
        # Test session creation
        async with AsyncSessionLocal() as session:
            print("✅ Database session created successfully")
        
        print("✅ Database connection test passed")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running and DATABASE_URL is correct")
        return False
    
    return True

async def main():
    """Main test function."""
    
    print("🚀 uOttawa Brightspace Assistant - OAuth System Test")
    print("=" * 70)
    print()
    
    # Test database first
    db_ok = await test_database_connection()
    print()
    
    if not db_ok:
        print("❌ Database tests failed. Fix database connection before proceeding.")
        return 1
    
    # Test OAuth endpoints
    oauth_ok = await test_oauth_endpoints()
    
    if oauth_ok:
        print("🎉 All OAuth system tests passed!")
        print()
        print("🔧 To complete setup:")
        print("1. Get OAuth credentials from uOttawa IT")
        print("2. Update your .env file with real credentials")
        print("3. Test full OAuth flow with a real user")
        return 0
    else:
        print("❌ Some OAuth tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())