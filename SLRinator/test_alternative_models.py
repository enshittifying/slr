#!/usr/bin/env python3
"""
Test alternative GPT models to find one that works
"""

import json
from pathlib import Path
import openai

def test_models():
    """Test different OpenAI models"""
    
    # Load API key
    config_file = Path("config/api_keys.json")
    with open(config_file) as f:
        config = json.load(f)
    api_key = config['openai']['api_key']
    
    client = openai.OpenAI(api_key=api_key)
    
    # Test models in order of preference
    models_to_test = [
        "gpt-4o",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-3.5-turbo"
    ]
    
    test_content = "See Smith v. Jones, 123 U.S. 456 (1995)."
    
    print("=" * 60)
    print("TESTING ALTERNATIVE MODELS")
    print("=" * 60)
    
    working_model = None
    
    for model in models_to_test:
        print(f"\nTesting {model}...")
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": f"Extract legal citations from: {test_content}"}
                ],
                max_tokens=100 if "gpt-5" not in model else None,
                max_completion_tokens=100 if "gpt-5" in model else None
            )
            
            content = response.choices[0].message.content
            
            if content and content.strip():
                print(f"  ✅ SUCCESS: '{content.strip()}'")
                print(f"  Model: {response.model}")
                print(f"  Tokens: {response.usage.total_tokens}")
                working_model = model
                break
            else:
                print(f"  ❌ Empty response")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    if working_model:
        print(f"\n🎯 WORKING MODEL: {working_model}")
        return working_model
    else:
        print(f"\n❌ No working models found")
        return None

if __name__ == "__main__":
    test_models()