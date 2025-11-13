#!/usr/bin/env python3
"""
Test GPT API Configuration
Verifies that the OpenAI API is properly configured and working
"""

import json
import os
from pathlib import Path
import openai

def test_gpt_api():
    """Test the GPT API configuration"""
    
    print("=" * 60)
    print("GPT API Configuration Test")
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
        print("   Configure in config/api_keys.json or set OPENAI_API_KEY env var")
        return False
    
    # Mask key for display
    masked_key = api_key[:7] + "..." + api_key[-4:]
    print(f"✅ API Key found: {masked_key}")
    
    # Test API connection
    print("\nTesting API connection...")
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # List available models
        print("\nAvailable models:")
        models = client.models.list()
        gpt_models = [m.id for m in models if 'gpt' in m.id.lower()]
        
        for model in sorted(gpt_models)[:10]:  # Show first 10 GPT models
            print(f"  • {model}")
        
        # Test with a simple prompt using gpt-4o
        print("\nTesting GPT-4o model...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a test assistant."},
                {"role": "user", "content": "Reply with 'API working' and nothing else."}
            ],
            max_tokens=10,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip()
        print(f"Response: {result}")
        
        if "API working" in result:
            print("\n✅ GPT API is working correctly!")
            print("   Model: gpt-4o")
            return True
        else:
            print("\n⚠️ Unexpected response from API")
            return False
            
    except openai.RateLimitError as e:
        print(f"\n❌ Rate limit error: {e}")
        print("   Your API key has exceeded its quota.")
        print("   Please check your OpenAI account billing.")
        return False
        
    except openai.NotFoundError as e:
        print(f"\n❌ Model not found: {e}")
        print("   The specified model doesn't exist or you don't have access.")
        
        # Try alternative models
        print("\nTrying alternative models...")
        for model in ["gpt-4", "gpt-3.5-turbo"]:
            try:
                print(f"  Testing {model}...")
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": "Say 'test'"}
                    ],
                    max_tokens=5
                )
                print(f"  ✅ {model} works!")
                return True
            except Exception as e:
                print(f"  ❌ {model} failed: {str(e)[:50]}")
        
        return False
        
    except Exception as e:
        print(f"\n❌ API Error: {e}")
        return False

if __name__ == "__main__":
    success = test_gpt_api()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ GPT API is properly configured and working!")
        print("\nYou can now use GPT parsing in the SLRinator.")
    else:
        print("❌ GPT API is not working properly.")
        print("\nTroubleshooting:")
        print("1. Check your OpenAI API key is valid")
        print("2. Verify you have sufficient credits")
        print("3. Ensure you have access to GPT-4o or GPT-4")
        print("\nYou can still use the fallback parser with --no-gpt")
    print("=" * 60)