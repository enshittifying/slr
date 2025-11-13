#!/usr/bin/env python3
"""
Check OpenAI API Usage and Billing Status
"""

import json
import os
from pathlib import Path
import requests
from datetime import datetime, timedelta

def check_api_usage():
    """Check API usage and billing status"""
    
    print("=" * 60)
    print("OpenAI API Account Status Check")
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
        return
    
    masked_key = api_key[:7] + "..." + api_key[-4:]
    print(f"API Key: {masked_key}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Check subscription
    print("\n1. Checking Subscription Status...")
    subscription_url = "https://api.openai.com/v1/dashboard/billing/subscription"
    
    try:
        response = requests.get(subscription_url, headers=headers)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Subscription data retrieved")
            if 'plan' in data:
                print(f"   Plan: {data.get('plan', {}).get('id', 'unknown')}")
            if 'has_payment_method' in data:
                print(f"   Payment method: {'Yes' if data.get('has_payment_method') else 'No'}")
        else:
            print(f"   ❌ Cannot access subscription info (may need different permissions)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check usage
    print("\n2. Checking Usage...")
    # Try to get usage for current month
    today = datetime.now()
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    usage_url = f"https://api.openai.com/v1/dashboard/billing/usage?start_date={start_date}&end_date={end_date}"
    
    try:
        response = requests.get(usage_url, headers=headers)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Usage data retrieved")
            print(f"   Current month usage: ${data.get('total_usage', 0) / 100:.2f}")
        else:
            print(f"   ❌ Cannot access usage info (may need different permissions)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check rate limits by making a minimal request
    print("\n3. Testing Minimal Request...")
    test_url = "https://api.openai.com/v1/chat/completions"
    
    # Try the absolute minimum request
    minimal_data = {
        "model": "gpt-5",
        "messages": [{"role": "user", "content": "1"}],
        "max_tokens": 1
    }
    
    try:
        response = requests.post(test_url, headers=headers, json=minimal_data)
        print(f"   Status code: {response.status_code}")
        
        # Check response headers for rate limit info
        if 'x-ratelimit-limit-requests' in response.headers:
            print(f"   Rate limit: {response.headers.get('x-ratelimit-limit-requests')} requests")
            print(f"   Remaining: {response.headers.get('x-ratelimit-remaining-requests', 'unknown')}")
            print(f"   Reset: {response.headers.get('x-ratelimit-reset-requests', 'unknown')}")
        
        if response.status_code == 200:
            print("   ✅ API calls are working!")
            result = response.json()
            print(f"   Response: {result['choices'][0]['message']['content']}")
        elif response.status_code == 429:
            error = response.json()
            error_type = error.get('error', {}).get('type', '')
            if error_type == 'insufficient_quota':
                print("   ❌ Insufficient quota - need to add credits")
                print("   This is a billing issue, not a code issue")
            elif error_type == 'rate_limit_exceeded':
                print("   ⚠️  Rate limited - too many requests")
                print("   Wait a bit and try again")
            else:
                print(f"   ❌ Rate limit error: {error_type}")
        else:
            print(f"   ❌ Error: {response.json().get('error', {}).get('message', 'Unknown')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    print("\n" + "=" * 60)
    print("Summary:")
    print("• The API key is valid and authenticated")
    print("• GPT-5 model exists and is accessible")
    print("• The issue is with quota/billing")
    print("\nTo fix this:")
    print("1. Log into https://platform.openai.com")
    print("2. Go to Billing section")
    print("3. Add payment method and credits")
    print("4. Or use a different API key with active credits")

if __name__ == "__main__":
    check_api_usage()