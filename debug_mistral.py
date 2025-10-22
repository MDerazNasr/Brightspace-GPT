#!/usr/bin/env python3
"""
Debug script for Mistral API issues
Run this to diagnose what's wrong with your Mistral integration
"""
import sys
import os
from pathlib import Path

print("🔍 Mistral API Debugging Tool")
print("=" * 60)

# Step 1: Check if API key is set
print("\n1️⃣ Checking API Key...")
api_key = os.getenv('MISTRAL_API_KEY')

if not api_key:
    print("❌ MISTRAL_API_KEY is not set in environment!")
    print("\n🔧 Solutions:")
    print("   Option A - Load from .env file:")
    print("   ```python")
    print("   from dotenv import load_dotenv")
    print("   load_dotenv()")
    print("   ```")
    print("\n   Option B - Set manually:")
    print("   ```bash")
    print("   export MISTRAL_API_KEY='your_key_here'")
    print("   ```")
    
    # Try loading from .env
    print("\n   Attempting to load from .env...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('MISTRAL_API_KEY')
        if api_key:
            print(f"   ✅ Found in .env file!")
        else:
            print("   ❌ Not found in .env file either")
            sys.exit(1)
    except ImportError:
        print("   ❌ python-dotenv not installed")
        print("   Install: pip install python-dotenv")
        sys.exit(1)
else:
    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")

# Step 2: Check API key format
print("\n2️⃣ Validating API Key Format...")
if len(api_key) < 20:
    print("⚠️  API key seems too short")
elif api_key.startswith('your_') or api_key.startswith('xxx'):
    print("❌ You're using a placeholder key! Replace with real key.")
    print("   Get one at: https://console.mistral.ai/")
    sys.exit(1)
else:
    print(f"✅ API key format looks valid (length: {len(api_key)})")

# Step 3: Check if mistralai package is installed
print("\n3️⃣ Checking Mistral Package...")
try:
    from mistralai import Mistral
    print("✅ mistralai package installed")
    
    # Check version
    try:
        import mistralai
        version = getattr(mistralai, '__version__', 'unknown')
        print(f"   Version: {version}")
    except:
        print("   Version: unknown")
        
except ImportError as e:
    print("❌ mistralai package not installed!")
    print("   Install: pip install mistralai")
    sys.exit(1)

# Step 4: Test actual API connection
print("\n4️⃣ Testing API Connection...")
try:
    client = Mistral(api_key=api_key)
    print("✅ Client initialized")
    
    print("   Sending test request...")
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "user", "content": "Say 'hello' if you can hear me"}
        ],
        max_tokens=10
    )
    
    message = response.choices[0].message.content
    print(f"✅ API Connection Successful!")
    print(f"   Response: {message}")
    
except Exception as e:
    print(f"❌ API Connection Failed!")
    print(f"   Error Type: {type(e).__name__}")
    print(f"   Error Message: {str(e)}")
    
    # Provide specific solutions
    error_msg = str(e).lower()
    
    if 'unauthorized' in error_msg or 'invalid' in error_msg or '401' in error_msg:
        print("\n🔧 Solution:")
        print("   Your API key is invalid. Please:")
        print("   1. Go to https://console.mistral.ai/")
        print("   2. Generate a new API key")
        print("   3. Update your .env file:")
        print("      MISTRAL_API_KEY='your_new_key_here'")
        print("   4. Restart your backend server")
        
    elif 'rate limit' in error_msg or '429' in error_msg:
        print("\n🔧 Solution:")
        print("   You've hit rate limits. Either:")
        print("   1. Wait a few minutes and try again")
        print("   2. Upgrade your Mistral plan")
        
    elif 'network' in error_msg or 'connection' in error_msg:
        print("\n🔧 Solution:")
        print("   Network connectivity issue. Check:")
        print("   1. Your internet connection")
        print("   2. Firewall settings")
        print("   3. Proxy configuration")
        
    elif 'timeout' in error_msg:
        print("\n🔧 Solution:")
        print("   Request timeout. Try:")
        print("   1. Check your internet speed")
        print("   2. Increase timeout in client configuration")
        
    else:
        print("\n🔧 General Solutions:")
        print("   1. Verify API key at console.mistral.ai")
        print("   2. Check you have API credits")
        print("   3. Try regenerating your API key")
        print("   4. Check Mistral status page")
    
    print(f"\n📋 Full Error Details:")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Test with backend imports
print("\n5️⃣ Testing Backend Integration...")
try:
    # Add backend to path
    backend_path = Path(__file__).parent.parent / "backend"
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
        print(f"✅ Backend path added: {backend_path}")
    
    from app.services.mistral_service import get_mistral_service
    print("✅ Mistral service imported successfully")
    
    service = get_mistral_service()
    print(f"✅ Service initialized (model: {service.model})")
    
except Exception as e:
    print(f"⚠️  Backend integration test failed: {e}")
    print("   This is okay if running standalone")

# Summary
print("\n" + "=" * 60)
print("📊 Diagnostic Summary")
print("=" * 60)
print("✅ All checks passed!")
print("\n🎯 Next Steps:")
print("   1. Your Mistral integration should work now")
print("   2. Restart your backend server")
print("   3. Try your query again in the extension")
print("   4. If still fails, check backend logs for errors")

print("\n💡 Debugging Tips:")
print("   • Check backend console for detailed error messages")
print("   • Look for actual Python exceptions (not just the user-facing message)")
print("   • Verify the query and context are being passed correctly")
print("   • Try a simple query first: 'What courses do I have?'")

print("\n📝 If problem persists, check:")
print("   • Backend logs: Look for actual exception traces")
print("   • Network tab: Check if API request is being made")
print("   • Mistral console: Check for API usage and errors")