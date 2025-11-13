#!/usr/bin/env python3
"""
Verify API Key Type and Status
"""

import json
from pathlib import Path
import requests
import os

def verify_key():
    """Verify what type of key this really is"""
    
    print("=" * 70)
    print("API KEY VERIFICATION")
    print("=" * 70)
    
    # Load key
    config_file = Path("config/api_keys.json")
    api_key = None
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        api_key = config.get("openai", {}).get("api_key")
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    print(f"\nYour API Key: {api_key[:20]}...{api_key[-4:]}")
    print(f"Length: {len(api_key)} characters")
    
    # Check prefix
    if api_key.startswith("sk-proj-"):
        print("\n🔍 Key prefix indicates: PROJECT KEY")
        print("   Even if created as 'personal', this has 'sk-proj-' prefix")
        print("   This means it's tied to a specific project")
    elif api_key.startswith("sk-"):
        print("\n🔍 Key prefix indicates: STANDARD SECRET KEY")
        print("   This is a regular API key")
    else:
        print("\n❓ Unusual key format")
    
    # Test the key thoroughly
    print("\n" + "-" * 70)
    print("TESTING KEY CAPABILITIES")
    print("-" * 70)
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test 1: Check if we can list models (basic auth)
    print("\n1. Testing Authentication...")
    models_url = "https://api.openai.com/v1/models"
    response = requests.get(models_url, headers=headers)
    
    if response.status_code == 200:
        print("   ✅ Authentication successful")
        models = response.json()
        gpt_models = [m['id'] for m in models['data'] if 'gpt' in m['id'].lower()]
        print(f"   Can see {len(gpt_models)} GPT models")
    else:
        print(f"   ❌ Authentication failed: {response.status_code}")
        return
    
    # Test 2: Check organization info
    print("\n2. Checking Organization Access...")
    org_url = "https://api.openai.com/v1/organization"
    response = requests.get(org_url, headers=headers)
    
    if response.status_code == 200:
        org_data = response.json()
        print(f"   Organization: {org_data.get('name', 'Unknown')}")
        print(f"   Org ID: {org_data.get('id', 'Unknown')}")
    
    # Test 3: Try the absolute cheapest call possible
    print("\n3. Testing Completion Capability...")
    
    test_models = ["gpt-3.5-turbo", "gpt-5-mini", "gpt-5"]
    
    for model in test_models:
        url = "https://api.openai.com/v1/chat/completions"
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "1"}],
            "max_tokens": 1
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            print(f"   ✅ {model}: WORKS!")
            return True
        elif response.status_code == 429:
            error_data = response.json()
            error_type = error_data.get('error', {}).get('type', '')
            if error_type == 'insufficient_quota':
                print(f"   ❌ {model}: Insufficient quota")
            else:
                print(f"   ❌ {model}: Rate limited")
        elif response.status_code == 404:
            print(f"   ⚠️  {model}: Model not found")
        else:
            print(f"   ❌ {model}: Error {response.status_code}")
    
    # Analysis
    print("\n" + "=" * 70)
    print("DIAGNOSIS")
    print("=" * 70)
    
    if api_key.startswith("sk-proj-"):
        print("\n🎯 This IS a project key (sk-proj- prefix)")
        print("\nEven if you selected 'personal' when creating it,")
        print("the 'sk-proj-' prefix means it's project-scoped.")
        print("\nProject keys need separate credit allocation.")
        
        print("\n💡 SOLUTION:")
        print("You need to create a TRUE personal key:")
        print("1. Go to: https://platform.openai.com/api-keys")
        print("2. Create new SECRET KEY")
        print("3. Make sure the new key starts with 'sk-' (not 'sk-proj-')")
        print("\nOR")
        print("1. Go to: https://platform.openai.com/account/billing")
        print("2. Check if you have credits in your account")
        print("3. If yes, your project needs credits allocated to it")
    else:
        print("\n🎯 This is a standard secret key")
        print("But it still has no available credits.")
        print("\n💡 SOLUTION:")
        print("1. Go to: https://platform.openai.com/account/billing")
        print("2. Add payment method")
        print("3. Purchase credits ($5-20 for testing)")
    
    return False

if __name__ == "__main__":
    verify_key()