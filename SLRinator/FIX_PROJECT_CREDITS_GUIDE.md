# How to Fix OpenAI Project Credits Issue

## Quick Diagnosis
Your current API key: `sk-proj-XmtqnxV...1kcA` is a **PROJECT key** that has no credits allocated.

## Step-by-Step Solution

### Option 1: Check and Allocate Project Credits

1. **Log into OpenAI Platform**
   - Go to: https://platform.openai.com
   - Sign in with your account

2. **Navigate to Projects**
   - Look for "Projects" in the left sidebar
   - Or go directly to: https://platform.openai.com/organization/projects
   - Find your project (starts with `XmtqnxV...`)

3. **Check Project Settings**
   - Click on your project
   - Look for "Settings" or "Billing" or "Usage limits"
   - Check if there's a "Monthly budget" or "Credits" section

4. **Allocate Credits to Project**
   - If you see a budget/credits option:
     - Set a monthly budget (e.g., $10-20 for testing)
     - Or allocate credits from organization pool
   - Save the settings

5. **Verify It Works**
   ```bash
   python test_gpt5.py
   ```

### Option 2: Create a New Personal API Key (Easier!)

1. **Go to API Keys Page**
   - Direct link: https://platform.openai.com/api-keys
   
2. **Create New Secret Key**
   - Click "+ Create new secret key"
   - **IMPORTANT**: Choose "Secret key" NOT "Project key"
   - Name it something like "SLRinator-Personal"
   
3. **Copy the New Key**
   - It will start with `sk-` (not `sk-proj-`)
   - Copy it immediately (you won't see it again)

4. **Update Your Configuration**
   ```bash
   # Edit the config file
   nano config/api_keys.json
   ```
   
   Replace the old key:
   ```json
   {
     "openai": {
       "api_key": "sk-YOUR-NEW-PERSONAL-KEY-HERE"
     }
   }
   ```

5. **Test It**
   ```bash
   python test_gpt5.py
   ```

### Option 3: Check Organization Credits

1. **Check Organization Billing**
   - Go to: https://platform.openai.com/organization/billing
   - Or click your organization name → Billing

2. **Look for These Sections**:
   - **Credit balance**: Should show available credits
   - **Payment methods**: Should have a valid card
   - **Usage this month**: Shows current spending
   - **Limits**: Check if there are spending limits

3. **If Organization Has Credits But Project Doesn't**:
   - Look for "Project budgets" or "Project allocation"
   - Some organizations require admins to allocate credits per project
   - Contact your organization admin if you can't allocate

### How to Know Which Option to Use

Run this command to check your current status:
```bash
python -c "
import json
from pathlib import Path

config_file = Path('config/api_keys.json')
if config_file.exists():
    with open(config_file) as f:
        config = json.load(f)
    key = config.get('openai', {}).get('api_key', '')
    
    if key.startswith('sk-proj-'):
        print('🏢 You have a PROJECT key')
        print('→ Try Option 1 (allocate credits) or Option 2 (new personal key)')
    elif key.startswith('sk-'):
        print('👤 You have a PERSONAL key')
        print('→ Check Option 3 (organization billing)')
    else:
        print('❓ Unknown key type')
"
```

### Quick Test After Fixing

Once you've either:
- Allocated credits to the project, OR
- Created a new personal key

Test with:
```bash
# Quick test
python test_gpt5.py

# Full test with document
python enhanced_sourcepull_workflow.py "output/data/SherkowGugliuzza_PostSP_PostEEFormatting[70].docx" --footnotes 1-5
```

## Troubleshooting

### "I can't find project settings"
- Projects might be under "Organization" → "Projects"
- Or look for "All projects" in the sidebar
- URL pattern: `platform.openai.com/organization/org-XXX/projects/proj-XXX`

### "I don't see billing/budget options"
- You might not be a project admin
- Contact your organization administrator
- Or just create a personal key (Option 2)

### "New personal key also doesn't work"
- Check organization billing: https://platform.openai.com/organization/billing
- Make sure there's a payment method
- Check if there are organization-wide spending limits

### "I'm not sure if I have admin access"
- Try Option 2 (personal key) first - it's simpler
- If that doesn't work, contact your OpenAI organization admin

## Current Workaround

While you're fixing the API key issue, the system works fine without GPT:
```bash
python enhanced_sourcepull_workflow.py document.docx --no-gpt
```

The fallback parser still finds citations and retrieves PDFs successfully.