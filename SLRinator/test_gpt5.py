#!/usr/bin/env python3
"""
Test GPT-5 Model
"""

import json
import os
from pathlib import Path
import requests

def test_gpt5():
    """Test GPT-5 model specifically"""
    
    print("=" * 60)
    print("Testing GPT-5 Model")
    print("=" * 60)
    
    # Load API key
    config_file = Path("config/api_keys.json")
    api_key = None
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        api_key = config.get("openai", {}).get("api_key")
    
    if not api_key:
        print("❌ No API key found!")
        return False
    
    masked_key = api_key[:7] + "..." + api_key[-4:]
    print(f"Using API Key: {masked_key}")
    
    # Test GPT-5
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-5",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Reply with 'GPT-5 is working' and nothing else."}
        ],
        "max_completion_tokens": 10
    }
    
    print("\nSending request to GPT-5...")
    print(f"Model: {data['model']}")
    print(f"Prompt: {data['messages'][1]['content']}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"\nStatus code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Success!")
            print(f"Response: {content}")
            print(f"Model used: {result.get('model', 'unknown')}")
            print(f"Tokens used: {result.get('usage', {}).get('total_tokens', 'unknown')}")
            return True
        else:
            error = response.json()
            print(f"❌ Error: {error.get('error', {}).get('message', 'Unknown error')}")
            print(f"Error type: {error.get('error', {}).get('type', 'unknown')}")
            
            # If quota error, check organization/billing
            if error.get('error', {}).get('type') == 'insufficient_quota':
                print("\n⚠️  Quota Issue Detected")
                print("This could mean:")
                print("1. The API key has no credits")
                print("2. The organization has billing issues")
                print("3. The key is from a free tier that expired")
                
                # Try to get more info
                print("\nChecking account info...")
                models_url = "https://api.openai.com/v1/models/gpt-5"
                models_response = requests.get(models_url, headers={"Authorization": f"Bearer {api_key}"})
                if models_response.status_code == 200:
                    print("✅ Can access GPT-5 model info")
                    model_info = models_response.json()
                    print(f"Model ID: {model_info.get('id')}")
                    print(f"Owned by: {model_info.get('owned_by')}")
                else:
                    print(f"❌ Cannot access model info: {models_response.status_code}")
                    
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_gpt5()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ GPT-5 is working correctly!")
    else:
        print("❌ GPT-5 is not accessible")
        print("\nNext steps:")
        print("1. Check with the API key owner about billing/credits")
        print("2. Verify the organization has an active subscription")
        print("3. Try using --no-gpt flag to use fallback parser")