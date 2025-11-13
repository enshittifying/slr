#!/usr/bin/env python3
"""
Debug API Call to OpenAI
Test with detailed debugging
"""

import json
import os
from pathlib import Path
import openai
import requests

def test_direct_api_call():
    """Test API with direct requests to debug"""
    
    print("=" * 60)
    print("Direct API Call Debug Test")
    print("=" * 60)
    
    # Load API key
    config_file = Path("config/api_keys.json")
    api_key = None
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        api_key = config.get("openai", {}).get("api_key")
    
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ No OpenAI API key found!")
        return
    
    # Mask key for display
    masked_key = api_key[:7] + "..." + api_key[-4:]
    print(f"API Key: {masked_key}")
    print(f"Key length: {len(api_key)} characters")
    print(f"Key starts with 'sk-': {api_key.startswith('sk-')}")
    
    # Test 1: Try with requests library directly
    print("\n1. Testing with requests library...")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Try different models
    models_to_test = ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
    
    for model in models_to_test:
        print(f"\nTrying model: {model}")
        data = {
            "model": model,
            "messages": [
                {"role": "user", "content": "Say 'test'"}
            ],
            "max_tokens": 5,
            "temperature": 0
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"  Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Success! Response: {result['choices'][0]['message']['content']}")
                print(f"  Model used: {result['model']}")
                return True
            else:
                error = response.json()
                print(f"  ❌ Error: {error.get('error', {}).get('message', 'Unknown error')}")
                if 'type' in error.get('error', {}):
                    print(f"  Error type: {error['error']['type']}")
                    
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    # Test 2: Check API key validity
    print("\n2. Checking API key validity...")
    test_url = "https://api.openai.com/v1/models"
    try:
        response = requests.get(test_url, headers={"Authorization": f"Bearer {api_key}"})
        print(f"Models endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ API key is valid and can access models")
            models = response.json()
            gpt_models = [m['id'] for m in models['data'] if 'gpt' in m['id'].lower()]
            print(f"Found {len(gpt_models)} GPT models available")
            if gpt_models:
                print("Sample models:", gpt_models[:5])
        elif response.status_code == 401:
            print("❌ API key is invalid (401 Unauthorized)")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Error checking models: {e}")
    
    return False

if __name__ == "__main__":
    success = test_direct_api_call()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ API call successful!")
    else:
        print("❌ All API calls failed")
        print("\nPossible issues:")
        print("1. API key might be invalid or expired")
        print("2. Model names might be incorrect")
        print("3. Account might not have access to these models")
        print("4. There might be a network/firewall issue")