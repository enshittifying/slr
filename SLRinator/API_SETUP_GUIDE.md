# SLRinator API Configuration Guide

## Overview
The SLRinator system uses multiple APIs to retrieve legal documents and parse citations. This guide provides comprehensive instructions for setting up and configuring all required APIs.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Required APIs](#required-apis)
3. [Optional APIs](#optional-apis)
4. [Configuration Methods](#configuration-methods)
5. [Testing Your Configuration](#testing-your-configuration)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### 1. Install Required Packages
```bash
# Using pip with virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Or using pipx for system-wide installation
pipx install PyMuPDF python-docx beautifulsoup4 pandas PyYAML aiohttp openai requests
```

### 2. Configure API Keys
```bash
# Copy template configuration
cp config/api_keys_template.json config/api_keys.json

# Edit configuration file
nano config/api_keys.json  # or use your preferred editor
```

### 3. Run Health Check
```bash
python system_health_check.py
```

## Required APIs

### OpenAI GPT-5 API
**Purpose**: Parse complex legal citations from footnotes

**How to Get API Key**:
1. Go to [https://platform.openai.com/signup](https://platform.openai.com/signup)
2. Create an account or sign in
3. Navigate to [API Keys](https://platform.openai.com/api-keys)
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

**Configuration**:
```json
{
  "openai": {
    "api_key": "sk-YOUR-API-KEY-HERE"
  }
}
```

**Alternative**: Set environment variable
```bash
export OPENAI_API_KEY="sk-YOUR-API-KEY-HERE"
```

**Cost**: Pay-per-use (typically $0.01-0.03 per 1K tokens)

## Optional APIs (Recommended)

### CourtListener API
**Purpose**: Retrieve federal and state court cases

**How to Get API Token**:
1. Go to [https://www.courtlistener.com/sign-up/](https://www.courtlistener.com/sign-up/)
2. Create a free account
3. Navigate to [API Token](https://www.courtlistener.com/api/rest-info/)
4. Copy your token

**Configuration**:
```json
{
  "courtlistener": {
    "token": "YOUR-TOKEN-HERE"
  }
}
```

**Cost**: FREE (with rate limits)

### GovInfo API
**Purpose**: Retrieve federal statutes, regulations, and government documents

**How to Get API Key**:
1. Go to [https://api.govinfo.gov/](https://api.govinfo.gov/)
2. Click "Get API Key"
3. Fill out the form with your email
4. Check email for API key

**Configuration**:
```json
{
  "govinfo": {
    "api_key": "YOUR-API-KEY-HERE"
  }
}
```

**Cost**: FREE

## Configuration Methods

### Method 1: Configuration File (Recommended)
Edit `config/api_keys.json`:

```json
{
  "openai": {
    "api_key": "sk-...",
    "model": "gpt-4-turbo-preview",
    "max_retries": 3
  },
  "courtlistener": {
    "token": "...",
    "base_url": "https://www.courtlistener.com/api/rest/v3/"
  },
  "govinfo": {
    "api_key": "...",
    "base_url": "https://api.govinfo.gov/"
  },
  "rate_limits": {
    "default": 1.0,
    "courtlistener": 10.0,
    "govinfo": 5.0
  }
}
```

### Method 2: Environment Variables
Set environment variables in your shell:

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="sk-..."
export COURTLISTENER_TOKEN="..."
export GOVINFO_API_KEY="..."
```

### Method 3: .env File
Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-...
COURTLISTENER_TOKEN=...
GOVINFO_API_KEY=...
```

## Testing Your Configuration

### 1. Run Health Check
```bash
python system_health_check.py
```

Expected output:
```
✅ OpenAI API: PASS - Configured
✅ CourtListener API: PASS - Configured  
✅ GovInfo API: PASS - Configured
```

### 2. Test Individual APIs

#### Test OpenAI
```python
python -c "
from src.core.enhanced_gpt_parser import EnhancedGPTParser
parser = EnhancedGPTParser()
print('OpenAI API:', 'Connected' if parser.api_available else 'Not configured')
"
```

#### Test CourtListener
```bash
curl -H "Authorization: Token YOUR-TOKEN" \
  https://www.courtlistener.com/api/rest/v3/search/
```

#### Test GovInfo
```bash
curl "https://api.govinfo.gov/collections?api_key=YOUR-KEY"
```

## API Usage Monitoring

The system automatically logs all API usage to `output/logs/api_usage/`:
- Daily log files with timestamps
- Masked API keys for security
- Request/response tracking
- Error logging
- Cost estimation (for paid APIs)

View API usage:
```bash
tail -f output/logs/api_usage/api_usage_$(date +%Y%m%d).log
```

## Rate Limiting

The system implements automatic rate limiting to prevent API throttling:

| API | Default Rate | Burst Size | Notes |
|-----|-------------|------------|-------|
| OpenAI | 1 req/sec | 10 | Adjustable based on tier |
| CourtListener | 10 req/sec | 50 | Free tier limits |
| GovInfo | 5 req/sec | 20 | Government API |

Configure custom rate limits in `config/api_keys.json`:
```json
{
  "rate_limits": {
    "openai": 2.0,
    "courtlistener": 15.0,
    "govinfo": 10.0
  }
}
```

## Security Best Practices

1. **Never commit API keys**:
   - Add `config/api_keys.json` to `.gitignore`
   - Use environment variables in production
   
2. **Rotate keys regularly**:
   - OpenAI: Regenerate monthly
   - CourtListener: Change every 90 days
   
3. **Monitor usage**:
   - Check daily logs for unusual activity
   - Set up billing alerts for paid APIs
   
4. **Use minimal permissions**:
   - Only grant necessary API scopes
   - Use read-only tokens when possible

## Troubleshooting

### Common Issues

#### OpenAI API Error: "Invalid API Key"
- Verify key starts with `sk-`
- Check for extra spaces or quotes
- Ensure key hasn't been revoked

#### CourtListener: "Rate limit exceeded"
- Default free tier: 5000 requests/day
- Implement caching for repeated queries
- Consider upgrading to paid tier

#### GovInfo: "Service unavailable"
- Government APIs have maintenance windows
- Usually 2-4 AM EST on Sundays
- Implement retry logic with backoff

### Debug Mode
Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Test Connection Script
```bash
python -c "
import json
from pathlib import Path

config_file = Path('config/api_keys.json')
if config_file.exists():
    with open(config_file) as f:
        config = json.load(f)
    
    print('API Configuration Status:')
    print('OpenAI:', '✅' if config.get('openai', {}).get('api_key') else '❌')
    print('CourtListener:', '✅' if config.get('courtlistener', {}).get('token') else '❌')
    print('GovInfo:', '✅' if config.get('govinfo', {}).get('api_key') else '❌')
else:
    print('❌ Configuration file not found')
"
```

## Support

For API-specific support:
- **OpenAI**: [help.openai.com](https://help.openai.com)
- **CourtListener**: [courtlistener.com/help](https://www.courtlistener.com/help/)
- **GovInfo**: [api.govinfo.gov/docs](https://api.govinfo.gov/docs/)

For SLRinator issues:
- Check `output/logs/` for detailed error messages
- Run `python system_health_check.py` for diagnostics
- Review action logs in `output/logs/actions/`