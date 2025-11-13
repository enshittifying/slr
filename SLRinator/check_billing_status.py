#!/usr/bin/env python3
"""
Check OpenAI Billing Status and Guide Through Solutions
"""

import json
from pathlib import Path
import webbrowser
import time
import os

def check_billing():
    """Guide user through checking billing status"""
    
    print("=" * 70)
    print("OPENAI BILLING STATUS CHECK")
    print("=" * 70)
    
    # Load current key info
    config_file = Path("config/api_keys.json")
    api_key = None
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        api_key = config.get("openai", {}).get("api_key")
    
    if api_key:
        print(f"Current API Key: {api_key[:15]}...{api_key[-4:]}")
        if api_key.startswith("sk-proj-"):
            print("Key Type: PROJECT KEY (needs credits allocated)")
        else:
            print("Key Type: PERSONAL KEY (uses account credits)")
    
    print("\n" + "=" * 70)
    print("STEP 1: CHECK YOUR ACCOUNT BILLING")
    print("=" * 70)
    
    print("\nI'm going to open your OpenAI billing page.")
    print("Look for the following information:")
    print("\n📊 CREDIT BALANCE:")
    print("   • Should show available credits (e.g., '$10.00' or '$0.00')")
    print("   • If $0.00, you need to add credits")
    
    print("\n💳 PAYMENT METHOD:")
    print("   • Should show a credit card ending in ****1234")
    print("   • If 'No payment method', you need to add one")
    
    print("\n📈 USAGE THIS MONTH:")
    print("   • Shows how much you've spent")
    print("   • If $0.00 and you have credits, the issue is project allocation")
    
    print("\n" + "-" * 50)
    input("Press Enter to open billing page...")
    
    # Open billing page
    billing_url = "https://platform.openai.com/account/billing"
    print(f"\nOpening: {billing_url}")
    webbrowser.open(billing_url)
    
    print("\n⏳ Take a moment to check your billing page...")
    print("Look for the information mentioned above.")
    
    # Wait for user to check
    print("\n" + "=" * 70)
    print("WHAT DID YOU FIND?")
    print("=" * 70)
    
    print("\nBased on what you see on the billing page, select:")
    print("1. I have credits available (> $0.00)")
    print("2. I have $0.00 credits but a payment method is set up")
    print("3. I have no payment method set up")
    print("4. I can't access the billing page / getting errors")
    print("0. Exit")
    
    try:
        choice = input("\nWhat describes your situation? (0-4): ").strip()
        
        if choice == "1":
            handle_has_credits()
        elif choice == "2":
            handle_no_credits_but_payment()
        elif choice == "3":
            handle_no_payment_method()
        elif choice == "4":
            handle_billing_access_issues()
        else:
            print("Exiting...")
            
    except KeyboardInterrupt:
        print("\n\nExiting...")

def handle_has_credits():
    """User has credits but project key isn't working"""
    print("\n" + "=" * 70)
    print("✅ YOU HAVE CREDITS - PROJECT ALLOCATION ISSUE")
    print("=" * 70)
    
    print("\nSince you have credits but the project key isn't working,")
    print("the issue is that credits aren't allocated to your project.")
    
    print("\n📋 SOLUTION STEPS:")
    
    print("\n1️⃣ OPEN PROJECTS PAGE:")
    print("   I'll open your projects page")
    
    input("Press Enter to open projects page...")
    projects_url = "https://platform.openai.com/organization/projects"
    webbrowser.open(projects_url)
    
    print("\n2️⃣ FIND YOUR PROJECT:")
    print("   Look for a project containing 'XmtqnxV' in its name/ID")
    
    print("\n3️⃣ ALLOCATE CREDITS:")
    print("   • Click on your project")
    print("   • Look for 'Settings', 'Billing', or 'Usage Limits'")
    print("   • Set a monthly budget (e.g., $20)")
    print("   • Or allocate credits from your account")
    
    print("\n4️⃣ TEST THE FIX:")
    input("After setting project budget, press Enter to test...")
    
    print("\nTesting your API key...")
    os.system("python test_gpt5.py")
    
    print("\n💡 ALTERNATIVE SOLUTION:")
    print("If you can't set project budgets, create a personal key:")
    print("• The project system might be controlled by your organization admin")
    print("• Personal keys use your account credits directly")
    
    create_personal_key_option()

def handle_no_credits_but_payment():
    """User has payment method but no credits"""
    print("\n" + "=" * 70)
    print("💳 PAYMENT METHOD SET - NEED TO ADD CREDITS")
    print("=" * 70)
    
    print("\nYou have a payment method but no credits.")
    
    print("\n📋 SOLUTION:")
    print("1. On the billing page you just opened")
    print("2. Look for 'Add credits' or 'Purchase credits'")
    print("3. Buy $5-20 worth for testing")
    print("4. Credits should be available immediately")
    
    print("\n💡 CREDIT RECOMMENDATIONS:")
    print("• $5: Good for basic testing (50-100 API calls)")
    print("• $20: Good for regular use (200-500 API calls)")
    
    input("After adding credits, press Enter to test...")
    
    print("\nTesting your API key...")
    os.system("python test_gpt5.py")

def handle_no_payment_method():
    """User needs to set up payment"""
    print("\n" + "=" * 70)
    print("💳 NEED TO SET UP PAYMENT METHOD")
    print("=" * 70)
    
    print("\nYou need to add a payment method first.")
    
    print("\n📋 SOLUTION:")
    print("1. On the billing page (should be open)")
    print("2. Click 'Add payment method'")
    print("3. Enter your credit card details")
    print("4. Add some credits ($5-20)")
    
    print("\n⚠️  IMPORTANT:")
    print("OpenAI requires a payment method even for testing")
    print("You can set low usage limits to control spending")
    
    input("After setting up payment and credits, press Enter to test...")
    
    print("\nTesting your API key...")
    os.system("python test_gpt5.py")

def handle_billing_access_issues():
    """User can't access billing page"""
    print("\n" + "=" * 70)
    print("🔒 BILLING ACCESS ISSUES")
    print("=" * 70)
    
    print("\nIf you can't access the billing page, this might mean:")
    print("• You're not the account owner")
    print("• The organization has restricted billing access")
    print("• You need admin permissions")
    
    print("\n📋 SOLUTIONS:")
    print("1. Contact your organization administrator")
    print("2. Or create your own OpenAI account")
    print("3. Or ask someone with billing access to allocate credits")
    
    create_personal_key_option()

def create_personal_key_option():
    """Offer to help create personal key"""
    print("\n" + "=" * 70)
    print("🔑 CREATE PERSONAL API KEY OPTION")
    print("=" * 70)
    
    print("\nWould you like to create a personal API key instead?")
    print("This bypasses project allocation issues.")
    
    choice = input("Create personal key? (y/n): ").lower().strip()
    
    if choice == 'y':
        print("\nOpening API keys page...")
        webbrowser.open("https://platform.openai.com/api-keys")
        
        print("\n📋 STEPS TO CREATE PERSONAL KEY:")
        print("1. Click '+ Create new secret key'")
        print("2. Choose 'Secret key' (NOT 'Project key')")
        print("3. Name it 'SLRinator-Personal'")
        print("4. Copy the key (starts with 'sk-' not 'sk-proj-')")
        
        input("After creating the key, press Enter...")
        
        print("\n🔧 UPDATE YOUR CONFIGURATION:")
        print("Run this command and paste your new key:")
        print("python check_openai_access.py --update-key")
    
    else:
        print("\nOK, work on the project allocation then!")

if __name__ == "__main__":
    check_billing()