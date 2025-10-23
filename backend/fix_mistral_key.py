#!/usr/bin/env python3
"""
Mistral API Key Diagnostic and Fix Script
Run this in your backend/ directory to diagnose the 401 error
"""
import os
import sys
from pathlib import Path

print("🔍 Mistral API Key Diagnostic Tool")
print("=" * 60)

# Step 1: Check .env file location
print("\n1️⃣ Checking for .env file...")
env_paths = [
    Path(".env"),
    Path("backend/.env"),
    Path("../.env"),
]

env_file = None
for path in env_paths:
    if path.exists():
        env_file = path
        print(f"✅ Found .env at: {path.absolute()}")
        break

if not env_file:
    print("❌ No .env file found!")
    print("\n🔧 Solution:")
    print("   Create a .env file in your backend/ directory:")
    print("   ```")
    print("   cd backend")
    print("   touch .env")
    print("   ```")
    sys.exit(1)

# Step 2: Read and check API key
print(f"\n2️⃣ Reading {env_file}...")
with open(env_file, 'r') as f:
    content = f.read()

# Find MISTRAL_API_KEY line
import re
mistral_key_match = re.search(r'MISTRAL_API_KEY\s*=\s*["\']?([^"\'\n]+)["\']?', content)

if not mistral_key_match:
    print("❌ MISTRAL_API_KEY not found in .env!")
    print("\n🔧 Solution:")
    print("   Add this line to your .env file:")
    print("   ```")
    print("   MISTRAL_API_KEY=your_actual_api_key_here")
    print("   ```")
    print("\n   Get your API key from: https://console.mistral.ai/")
    sys.exit(1)

api_key = mistral_key_match.group(1).strip()
print(f"✅ Found MISTRAL_API_KEY in .env")

# Step 3: Validate key format
print(f"\n3️⃣ Validating API key...")
print(f"   Length: {len(api_key)} characters")
print(f"   Starts with: {api_key[:10]}...")
print(f"   Ends with: ...{api_key[-4:]}")

issues = []

if len(api_key) < 20:
    issues.append("Key is too short (< 20 chars)")
elif len(api_key) > 500:
    issues.append("Key is suspiciously long (> 500 chars)")

if api_key.startswith('your_') or api_key.startswith('xxx') or api_key == 'your_actual_api_key_here':
    issues.append("You're still using a placeholder key!")

if ' ' in api_key:
    issues.append("Key contains spaces (likely a copy-paste error)")

if api_key.startswith('"') or api_key.endswith('"'):
    issues.append("Key has quotes around it (remove them)")

if '\n' in api_key or '\r' in api_key:
    issues.append("Key contains newline characters")

if issues:
    print("\n❌ Issues found:")
    for issue in issues:
        print(f"   • {issue}")
    print("\n🔧 Solution:")
    print("   1. Go to: https://console.mistral.ai/")
    print("   2. Create a new API key")
    print("   3. Replace the key in your .env file (no quotes, no spaces)")
    print("   4. Restart your backend server")
    sys.exit(1)

print("✅ Key format looks valid")

# Step 4: Test the API key
print(f"\n4️⃣ Testing API connection...")

try:
    from mistralai import Mistral
    
    client = Mistral(api_key=api_key)
    print("   Sending test request to Mistral API...")
    
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": "Say 'OK' if you hear me"}],
        max_tokens=5
    )
    
    message = response.choices[0].message.content
    print(f"✅ API Test Successful!")
    print(f"   Response: {message}")
    
except Exception as e:
    error_msg = str(e).lower()
    
    print(f"❌ API Test Failed!")
    print(f"   Error: {e}")
    
    if '401' in error_msg or 'unauthorized' in error_msg:
        print("\n🔧 Solution:")
        print("   Your API key is INVALID or EXPIRED!")
        print("   1. Go to https://console.mistral.ai/")
        print("   2. Check if your key is still active")
        print("   3. If expired/deleted, create a NEW key")
        print("   4. Update your .env file with the new key:")
        print(f"      MISTRAL_API_KEY=<your_new_key_here>")
        print("   5. Restart your backend: uvicorn app.main:app --reload")
        
    elif '429' in error_msg or 'rate limit' in error_msg:
        print("\n🔧 Solution:")
        print("   Rate limit exceeded. Wait a few minutes or upgrade your plan.")
        
    elif 'network' in error_msg or 'connection' in error_msg:
        print("\n🔧 Solution:")
        print("   Network error. Check your internet connection.")
        
    sys.exit(1)

# Step 5: Final recommendations
print("\n" + "=" * 60)
print("📊 Diagnostic Complete!")
print("=" * 60)
print("✅ Your Mistral API key is working correctly")
print("\n📝 If you're still getting 401 errors:")
print("   1. Make sure you restarted your backend server")
print("   2. Check if the .env file is in the right location")
print("   3. Verify no other .env files are overriding this one")
print("   4. Check if your API key has usage limits or expiry")
print("\n💡 To restart backend:")
print("   cd backend")
print("   uvicorn app.main:app --reload --port 8001")