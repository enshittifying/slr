#!/usr/bin/env python3
"""
Diagnose OpenAI API Issues
Comprehensive diagnostic tool
"""

import json
from pathlib import Path
import openai
import os
import base64

def diagnose_api():
    """Comprehensive API diagnostic"""
    
    print("=" * 70)
    print("OPENAI API DIAGNOSTIC TOOL")
    print("=" * 70)
    
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
        print("❌ No API key found!")
        return
    
    # Analyze key
    print("\n1. API KEY ANALYSIS")
    print("-" * 40)
    print(f"Key prefix: {api_key[:15]}...")
    print(f"Key suffix: ...{api_key[-4:]}")
    print(f"Total length: {len(api_key)} characters")
    
    if api_key.startswith("sk-proj-"):
        print("Type: PROJECT KEY 🏢")
        print("\n⚠️  PROJECT KEY DETECTED!")
        print("Project keys have separate quotas from the organization.")
        print("Even if the org has credits, the PROJECT might not.")
        
        # Extract project info from key if possible
        try:
            key_parts = api_key.split("-")
            if len(key_parts) >= 3:
                print(f"Project identifier: {key_parts[2][:10]}...")
        except:
            pass
            
    elif api_key.startswith("sk-"):
        print("Type: USER KEY 👤")
        print("This is a personal API key.")
    else:
        print("Type: UNKNOWN ❓")
        print("This doesn't look like a standard OpenAI key.")
    
    # Test authentication
    print("\n2. AUTHENTICATION TEST")
    print("-" * 40)
    
    client = openai.OpenAI(api_key=api_key)
    
    try:
        # Just list one model to verify auth
        models = list(client.models.list())
        print("✅ Authentication successful!")
        print(f"   Can access {len(models)} models")
        
        # Show available GPT models
        gpt_models = [m.id for m in models if 'gpt' in m.id.lower()]
        print(f"\n   Available GPT models ({len(gpt_models)}):")
        for model in sorted(gpt_models)[:10]:
            print(f"   • {model}")
            
    except openai.AuthenticationError as e:
        print("❌ Authentication failed!")
        print(f"   Error: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return
    
    # Test actual API calls
    print("\n3. API CALL TESTS")
    print("-" * 40)
    
    # Test with the cheapest possible call
    test_configs = [
        {"model": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo (cheapest)"},
        {"model": "gpt-5-mini", "name": "GPT-5 Mini"},
        {"model": "gpt-5", "name": "GPT-5 (most capable)"},
    ]
    
    for config in test_configs:
        print(f"\nTesting {config['name']}...")
        try:
            response = client.chat.completions.create(
                model=config['model'],
                messages=[{"role": "user", "content": "1"}],
                max_tokens=1,
                temperature=0
            )
            print(f"  ✅ SUCCESS! Model {config['model']} is working!")
            print(f"     You should use: model='{config['model']}'")
            return True
            
        except openai.RateLimitError as e:
            error_details = e.response.json() if hasattr(e, 'response') else {}
            error_type = error_details.get('error', {}).get('type', '')
            
            if error_type == 'insufficient_quota':
                print(f"  ❌ INSUFFICIENT QUOTA")
                
        except openai.NotFoundError:
            print(f"  ❌ Model not available")
            
        except Exception as e:
            print(f"  ❌ Error: {type(e).__name__}")
    
    # Diagnosis
    print("\n" + "=" * 70)
    print("DIAGNOSIS SUMMARY")
    print("=" * 70)
    
    print("\n🔍 FINDINGS:")
    print("• Your API key is valid and authenticated ✅")
    print("• You can see available models ✅")
    print("• But you cannot make completion requests ❌")
    
    if api_key.startswith("sk-proj-"):
        print("\n🎯 ROOT CAUSE: PROJECT KEY WITH NO CREDITS")
        print("\nThis is a PROJECT-scoped API key that doesn't have credits.")
        print("Project keys have their own quotas separate from the organization.")
        
        print("\n💡 SOLUTIONS (in order of preference):")
        print("\n1. ALLOCATE CREDITS TO THE PROJECT:")
        print("   • Log into platform.openai.com")
        print("   • Go to your project settings")
        print("   • Allocate credits/budget to this specific project")
        
        print("\n2. USE A DIFFERENT API KEY:")
        print("   • Create a personal API key (not project-scoped)")
        print("   • Go to platform.openai.com/api-keys")
        print("   • Create a new SECRET KEY (not project key)")
        print("   • Update config/api_keys.json with the new key")
        
        print("\n3. USE ORGANIZATION DEFAULT KEY:")
        print("   • If your org has a default key with credits")
        print("   • Use that instead of the project key")
    else:
        print("\n🎯 ROOT CAUSE: NO CREDITS ON ACCOUNT")
        print("\nThe account associated with this API key has no credits.")
        
        print("\n💡 SOLUTIONS:")
        print("1. Add credits at platform.openai.com/account/billing")
        print("2. Use a different API key with active credits")
    
    print("\n📝 FOR NOW:")
    print("You can use the fallback parser without GPT:")
    print("python enhanced_sourcepull_workflow.py document.docx --no-gpt")
    
    return False

if __name__ == "__main__":
    diagnose_api()