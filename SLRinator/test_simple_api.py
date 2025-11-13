#!/usr/bin/env python3
"""
Test with the simplest possible API call
"""

import json
from pathlib import Path
import openai
import os

def test_simple():
    """Test with OpenAI Python client directly"""
    
    print("=" * 60)
    print("Testing with OpenAI Python Client")
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
    
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print(f"Key format check:")
    print(f"  - Starts with 'sk-': {api_key.startswith('sk-')}")
    print(f"  - Length: {len(api_key)}")
    
    # Initialize client
    print("\nInitializing OpenAI client...")
    client = openai.OpenAI(api_key=api_key)
    
    # Test 1: List models to verify auth
    print("\n1. Testing authentication by listing models...")
    try:
        models = client.models.list()
        model_ids = [m.id for m in models.data if 'gpt' in m.id][:5]
        print(f"✅ Auth successful! Found {len(model_ids)} GPT models")
        print(f"   Models: {model_ids}")
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return False
    
    # Test 2: Try different model variations
    print("\n2. Testing different models...")
    
    models_to_try = [
        "gpt-3.5-turbo",  # Most common, should work
        "gpt-4",          # Standard GPT-4
        "gpt-4-turbo",    # Turbo variant
        "gpt-4o",         # Optimized variant
        "gpt-5",          # GPT-5 if available
        "gpt-5-mini",     # GPT-5 mini variant
    ]
    
    for model_name in models_to_try:
        print(f"\nTrying {model_name}...")
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": "Say 'yes'"}
                ],
                max_tokens=5,
                temperature=0
            )
            
            result = response.choices[0].message.content
            print(f"  ✅ SUCCESS with {model_name}!")
            print(f"     Response: {result}")
            print(f"     Model used: {response.model}")
            
            # If this worked, update our config
            print(f"\n  📝 Recommendation: Use model='{model_name}' in your code")
            return True
            
        except openai.RateLimitError as e:
            error_msg = str(e)
            if "insufficient_quota" in error_msg:
                print(f"  ❌ Quota error: Account has no credits")
            else:
                print(f"  ❌ Rate limit: {error_msg[:100]}")
                
        except openai.NotFoundError as e:
            print(f"  ❌ Model not found or no access")
            
        except Exception as e:
            print(f"  ❌ Other error: {type(e).__name__}: {str(e)[:100]}")
    
    # Test 3: Check if it's an org/project issue
    print("\n3. Checking API key details...")
    
    # Try to decode the key structure
    if api_key.startswith("sk-proj-"):
        print("  This is a PROJECT API key")
        print("  Project keys have specific quota/model access")
    elif api_key.startswith("sk-"):
        print("  This is a USER API key")
    
    # Test with minimal parameters
    print("\n4. Testing with absolute minimum parameters...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "1"}],
            max_tokens=1
        )
        print(f"  ✅ Minimal call worked!")
        return True
    except Exception as e:
        print(f"  ❌ Even minimal call failed: {e}")
    
    return False

if __name__ == "__main__":
    success = test_simple()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Found a working model configuration!")
    else:
        print("❌ No models are accessible with this API key")
        print("\nPossible issues:")
        print("1. This might be a PROJECT key with no credits allocated")
        print("2. The organization might have billing issues")
        print("3. The key might be restricted to specific models")
        print("\nTry:")
        print("1. Creating a new API key at platform.openai.com")
        print("2. Checking project settings if using a project key")
        print("3. Using a personal API key instead of project key")