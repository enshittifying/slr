#!/usr/bin/env python3
"""
Check OpenAI Account Access and Credits
Helps determine what you can do to fix the issue
"""

import json
from pathlib import Path
import webbrowser
import os

def check_access():
    """Interactive guide to fix OpenAI access"""
    
    print("=" * 70)
    print("OPENAI ACCESS CHECKER & FIX GUIDE")
    print("=" * 70)
    
    # Load current key
    config_file = Path("config/api_keys.json")
    current_key = None
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        current_key = config.get("openai", {}).get("api_key")
    
    if not current_key:
        current_key = os.getenv("OPENAI_API_KEY")
    
    if not current_key:
        print("\n❌ No API key found!")
        print("\nYou need to get an API key first:")
        print("1. Go to: https://platform.openai.com/api-keys")
        print("2. Create a new secret key")
        print("3. Add it to config/api_keys.json")
        return
    
    # Analyze current key
    print(f"\n📍 Current API Key: {current_key[:15]}...{current_key[-4:]}")
    
    if current_key.startswith("sk-proj-"):
        print("🏢 Type: PROJECT KEY")
        print("\n⚠️  This is why you're getting quota errors!")
        print("Project keys need credits allocated separately from the organization.")
        
        print("\n" + "=" * 70)
        print("RECOMMENDED SOLUTIONS")
        print("=" * 70)
        
        print("\n🥇 EASIEST FIX: Create a Personal Key")
        print("-" * 40)
        print("1. Open this link in your browser:")
        print("   https://platform.openai.com/api-keys")
        print("\n2. Click '+ Create new secret key'")
        print("\n3. IMPORTANT: Choose 'Secret key' (NOT 'Project key')")
        print("\n4. Name it: 'SLRinator-Personal'")
        print("\n5. Copy the new key (starts with 'sk-' not 'sk-proj-')")
        print("\n6. Come back here and run:")
        print("   python check_openai_access.py --update-key")
        
        print("\n" + "=" * 70)
        print("\n🥈 ALTERNATIVE: Fix Project Credits")
        print("-" * 40)
        print("1. Open this link:")
        print("   https://platform.openai.com/organization/projects")
        print("\n2. Find your project (contains 'XmtqnxV')")
        print("\n3. Look for Settings → Billing or Usage Limits")
        print("\n4. Allocate monthly budget (e.g., $20)")
        
    elif current_key.startswith("sk-"):
        print("👤 Type: PERSONAL KEY")
        print("\nThis is the right type of key, but it might not have credits.")
        
        print("\n" + "=" * 70)
        print("CHECK YOUR BILLING")
        print("=" * 70)
        
        print("\n1. Open this link:")
        print("   https://platform.openai.com/organization/billing")
        print("\n2. Check:")
        print("   • Credit balance (should be > $0)")
        print("   • Payment method (should have valid card)")
        print("\n3. If no credits, add them:")
        print("   • Click 'Add payment method'")
        print("   • Add credit card")
        print("   • Purchase credits ($5-20 for testing)")
    
    # Offer to open links
    print("\n" + "=" * 70)
    print("QUICK ACTIONS")
    print("=" * 70)
    
    print("\nWould you like to:")
    print("1. Open API Keys page in browser")
    print("2. Open Billing page in browser")
    print("3. Open Projects page in browser")
    print("4. Update API key in config")
    print("5. Test current configuration")
    print("0. Exit")
    
    try:
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == "1":
            print("Opening API Keys page...")
            webbrowser.open("https://platform.openai.com/api-keys")
            print("\n✅ Create a new SECRET KEY (not project key)")
            print("Then run: python check_openai_access.py --update-key")
            
        elif choice == "2":
            print("Opening Billing page...")
            webbrowser.open("https://platform.openai.com/organization/billing")
            print("\n✅ Check your credit balance and add funds if needed")
            
        elif choice == "3":
            print("Opening Projects page...")
            webbrowser.open("https://platform.openai.com/organization/projects")
            print("\n✅ Find your project and check its settings/billing")
            
        elif choice == "4":
            update_api_key()
            
        elif choice == "5":
            print("\nTesting current configuration...")
            os.system("python test_gpt5.py")
            
    except KeyboardInterrupt:
        print("\n\nExiting...")

def update_api_key():
    """Update API key in config"""
    print("\n" + "=" * 70)
    print("UPDATE API KEY")
    print("=" * 70)
    
    print("\nPaste your new API key (or press Enter to cancel):")
    new_key = input("New key: ").strip()
    
    if not new_key:
        print("Cancelled.")
        return
    
    if not new_key.startswith("sk-"):
        print("❌ Invalid key format (should start with 'sk-')")
        return
    
    # Check key type
    if new_key.startswith("sk-proj-"):
        print("\n⚠️  WARNING: This is another PROJECT key!")
        print("Project keys often have the same quota issues.")
        print("Are you sure you want to use this? (y/n): ", end="")
        if input().lower() != 'y':
            print("Cancelled.")
            return
    
    # Update config
    config_file = Path("config/api_keys.json")
    config = {}
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
    
    if "openai" not in config:
        config["openai"] = {}
    
    config["openai"]["api_key"] = new_key
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✅ Updated API key in {config_file}")
    print(f"   Key type: {'PROJECT' if new_key.startswith('sk-proj-') else 'PERSONAL'}")
    print(f"   Key preview: {new_key[:15]}...{new_key[-4:]}")
    
    print("\nTesting new key...")
    os.system("python test_gpt5.py")

if __name__ == "__main__":
    import sys
    
    if "--update-key" in sys.argv:
        update_api_key()
    else:
        check_access()