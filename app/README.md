# SLR Citation Processor - Desktop Application

A cross-platform desktop application for automating Stanford Law Review's citation processing pipeline.

## Overview

The SLR Citation Processor integrates the proven SLRinator backend with a modern PyQt6 GUI to provide a complete desktop solution for citation processing across three stages:

- **SP (Source Pull)**: Automated retrieval of source PDFs from legal databases
- **R1 (Preparation)**: PDF cleaning and citation element redboxing
- **R2 (Validation)**: LLM-powered citation format and support checking

## Features

### Complete Pipeline Integration
- **SP Machine**: Leverages SLRinator's multi-source retrieval system (CourtListener, GovInfo, HeinOnline, etc.)
- **R1 Machine**: Automated PDF cleaning and intelligent redboxing using PyMuPDF
- **R2 Pipeline**: GPT-4/Claude-powered citation validation with Bluebook compliance checking

### Modern Desktop Interface
- Cross-platform PyQt6 GUI (macOS & Windows)
- Tabbed interface for SP/R1/R2 workflows
- Real-time progress tracking and logging
- Background processing with worker threads

### Google Cloud Integration
- Google Sheets for master control and status tracking
- Google Drive for organized PDF storage
- Service account authentication with encrypted credentials

### Enterprise Features
- Comprehensive logging and audit trails
- Local caching for resume capability
- Configurable LLM providers (OpenAI/Anthropic)
- Error handling with automatic retries

## Architecture

```
┌─────────────────────────────────────────────────────┐
│           PyQt6 Desktop Application                 │
│  ┌───────────────────────────────────────────────┐  │
│  │  GUI Layer (app/gui/)                         │  │
│  │  - Main Window with Tabs                      │  │
│  │  - SP/R1/R2 Manager Widgets                   │  │
│  │  - Settings Dialog                             │  │
│  │  - Progress Tracking                           │  │
│  └────────────────┬──────────────────────────────┘  │
│                   │                                  │
│  ┌────────────────▼──────────────────────────────┐  │
│  │  Core Pipeline (app/core/)                    │  │
│  │  - Pipeline Orchestrator                      │  │
│  │  - SP Machine (wraps SLRinator)               │  │
│  │  - R1 Machine (PDF + Redboxing)               │  │
│  │  - R2 Pipeline (LLM Validation)               │  │
│  └────────────────┬──────────────────────────────┘  │
│                   │                                  │
│  ┌────────────────▼──────────────────────────────┐  │
│  │  Data Layer (app/data/)                       │  │
│  │  - Google Sheets Client                       │  │
│  │  - Google Drive Client                        │  │
│  │  - LLM Client (OpenAI/Anthropic)              │  │
│  └────────────────┬──────────────────────────────┘  │
│                   │                                  │
│  ┌────────────────▼──────────────────────────────┐  │
│  │  SLRinator Backend                            │  │
│  │  - Source Retrieval                           │  │
│  │  - Citation Parsing                           │  │
│  │  - PDF Redboxing                              │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- macOS 12+ or Windows 10+
- Google Cloud service account with Sheets & Drive access
- OpenAI or Anthropic API key

### From Source

```bash
# Clone repository
git clone https://github.com/enshittifying/slr.git
cd slr

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r app/requirements.txt

# Run application
python app/main.py
```

### From Binary

Download the latest release for your platform:
- **macOS**: `SLR-Citation-Processor-Mac.dmg`
- **Windows**: `SLR-Citation-Processor-Setup.exe`

## Configuration

### First-Time Setup

1. **Launch Application**
   ```bash
   python app/main.py
   ```

2. **Configure Settings** (File → Settings)
   - **Google Sheets ID**: From your master control spreadsheet URL
   - **Google Drive Folder ID**: Root folder for PDF storage
   - **Service Account**: Browse to your `credentials.json` file
   - **LLM Provider**: Choose OpenAI or Anthropic
   - **API Key**: Your LLM API key

3. **Test Connection**
   - Click "Refresh" in any tab to verify Google Sheets connection

### Service Account Setup

1. Create Google Cloud project
2. Enable Sheets & Drive APIs
3. Create service account and download JSON key
4. Share master spreadsheet and Drive folder with service account email
5. Import credentials via Settings → Service Account → Browse

The app will encrypt and store credentials securely using system keyring.

## Usage

### Source Pull (SP Tab)

1. Select article from dropdown
2. Review sources list (footnote numbers, citations, status)
3. Click "Start Source Pull"
4. Monitor progress in real-time
5. Review completed sources in Google Drive

**What it does:**
- Downloads PDFs from legal databases (CourtListener, GovInfo, etc.)
- Uploads to organized Drive folders
- Updates status in Google Sheets
- Caches locally for resume capability

### R1 Preparation (R1 Tab)

1. Select article (must have SP complete)
2. Review sources ready for R1
3. Click "Start R1 Preparation"
4. Monitor redboxing progress
5. Review prepared PDFs in Drive (R1 folder)

**What it does:**
- Downloads raw PDFs from Drive
- Cleans PDFs (removes cover pages, headers)
- Applies intelligent redboxing to highlight citation elements
- Uploads R1 PDFs to Drive
- Updates R1 status in Sheets

### R2 Validation (R2 Tab)

1. Select article (must have R1 complete)
2. Browse to article Word document (.docx)
3. Click "Start R2 Validation"
4. Monitor LLM validation progress
5. Click "View Review Queue" to see issues

**What it does:**
- Extracts footnotes from Word document
- Downloads R1 PDFs for each source
- Uses LLM to check citation format (Bluebook compliance)
- Uses LLM to verify source supports proposition
- Generates review queue HTML report
- Creates Word doc with tracked changes
- Uploads R2 package to Drive

## Project Structure

```
app/
├── main.py                 # Application entry point
├── gui/                    # PyQt6 UI components
│   ├── main_window.py     # Main application window
│   ├── sp_manager.py      # Source Pull tab
│   ├── r1_manager.py      # R1 Preparation tab
│   ├── r2_manager.py      # R2 Validation tab
│   ├── settings_dialog.py # Configuration dialog
│   ├── progress_widget.py # Progress tracking widget
│   ├── workers.py         # Background worker threads
│   └── styles.qss         # Qt stylesheet
├── core/                   # Business logic
│   ├── orchestrator.py    # Pipeline coordinator
│   ├── sp_machine.py      # SP wrapper
│   ├── r1_machine.py      # R1 processing
│   └── r2_pipeline.py     # R2 validation
├── data/                   # Data access layer
│   ├── sheets_client.py   # Google Sheets API
│   ├── drive_client.py    # Google Drive API
│   └── llm_client.py      # LLM API (OpenAI/Anthropic)
├── utils/                  # Utilities
│   ├── auth.py            # Service account auth
│   ├── crypto.py          # Credential encryption
│   ├── config.py          # Configuration management
│   └── logging.py         # Logging setup
└── resources/              # Static resources
    ├── bluebook_rules.json # Bluebook citation rules
    ├── prompts/            # LLM prompts
    └── config/             # Default configuration
```

## Building from Source

### macOS

```bash
cd build
chmod +x build_mac.sh
./build_mac.sh
```

Output: `dist/SLR Citation Processor.app`

### Windows

```cmd
cd build
build_windows.bat
```

Output: `dist\SLR Citation Processor\SLR Citation Processor.exe`

## Troubleshooting

### "Service account not configured"
- Go to File → Settings
- Browse to your `credentials.json` file
- Ensure service account has access to Sheets & Drive

### "Failed to load articles"
- Verify Google Sheets ID in settings
- Check service account has Editor access to spreadsheet
- Test connection with "Refresh" button

### "LLM validation failed"
- Verify API key in settings
- Check API credits/quota
- Review logs in View → View Logs

### Performance Issues
- Reduce "Max Concurrent Downloads" in settings
- Clear cache directory (View → View Cache)
- Check network connection

## Logging

Logs are stored in:
- **Location**: `logs/` directory
- **Format**: Timestamped files with session IDs
- **Access**: View → View Logs

Action logs track all operations for audit purposes.

## Caching

Local caching speeds up processing and enables resume capability:
- **SP cache**: `cache/sp/` - Downloaded source PDFs
- **R1 cache**: `cache/r1/` - Prepared R1 PDFs
- **R2 cache**: `cache/r2/` - Validation results

Clear cache via View → View Cache.

## Security

- **Credentials**: Encrypted using Fernet symmetric encryption
- **Key Storage**: System keyring (macOS Keychain / Windows Credential Manager)
- **API Keys**: Stored in encrypted configuration file
- **Permissions**: Service account has minimal required permissions

## Dependencies

See `app/requirements.txt` for complete list:
- PyQt6 6.6+ (GUI framework)
- PyMuPDF 1.23+ (PDF processing)
- google-api-python-client (Google APIs)
- openai / anthropic (LLM clients)
- cryptography (Credential encryption)
- python-docx (Word document processing)

## Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
flake8 app/
black app/
```

### Contributing
1. Fork repository
2. Create feature branch
3. Add tests
4. Submit pull request

## License

Stanford Law Review - Internal Use Only

## Support

For issues or questions:
- GitHub Issues: https://github.com/enshittifying/slr/issues
- Documentation: See `info/` directory
- Logs: Check `logs/` directory for debugging

## Credits

- **SLRinator**: Backend citation processing engine
- **PyQt6**: Cross-platform GUI framework
- **OpenAI/Anthropic**: LLM providers for validation
- Built with assistance from Claude AI

---

**Version**: 1.0.0
**Last Updated**: November 2024
**Maintained by**: Stanford Law Review Editorial Team
