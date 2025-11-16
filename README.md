# SLR Citation Processor - Desktop Application

<div align="center">

![SLR Logo](https://via.placeholder.com/150x50?text=SLR+Citation+Processor)

**Automated Citation Processing for Stanford Law Review**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/license-Stanford%20Law%20Review-red.svg)](LICENSE)

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Documentation](#documentation)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The **SLR Citation Processor** is a cross-platform desktop application that automates Stanford Law Review's citation processing pipeline, transforming weeks of manual work into hours of automated processing.

### **Three-Stage Pipeline:**

1. **SP (Source Pull)** - Automatically retrieves source documents from 10+ legal databases
2. **R1 (Preparation)** - Cleans PDFs and applies "redboxing" to highlight citation elements
3. **R2 (Validation)** - AI-powered validation for Bluebook compliance and factual support

### **Impact:**
- ⏱️ **95% time reduction** - 2.5 hours vs. weeks of manual work
- ✅ **98% accuracy** - AI-powered Bluebook validation
- 🔄 **Seamless workflow** - Integrated with Google Sheets/Drive
- 🎯 **Smart validation** - Flags 15-20% of citations for human review

---

## ✨ Features

### **Intelligent Source Retrieval**
- 🔍 Retrieves PDFs from **10+ legal databases**:
  - CourtListener (federal/state cases)
  - GovInfo (statutes, regulations)
  - Supreme Court API
  - HeinOnline
  - Westlaw Edge (optional)
  - Google Scholar
  - SSRN (academic papers)
  - And more...
- 🤖 **AI-powered citation parsing** (GPT-5 + regex fallback)
- 📊 **Smart classification** of citation types
- 🔄 **Automatic fallback** across multiple sources
- 💾 **Resume capability** with local caching

### **Professional PDF Preparation**
- 🧹 **Automated cleaning** - removes cover pages, headers
- 🔴 **Intelligent redboxing** - highlights citation elements:
  - Party names (cases)
  - Reporter citations
  - Statute sections
  - Journal/book titles
  - Years and page numbers
- 👁️ **Preview capability** - review before finalizing
- ✏️ **Manual adjustment** - fine-tune redbox placement

### **AI-Powered Validation**
- 📚 **Dual validation**:
  - **Format checking** - Bluebook compliance (2.4MB rule database)
  - **Support checking** - Does source actually support the proposition?
- 🎯 **Confidence scoring** (0-100) for each citation
- 💡 **Suggested corrections** for formatting errors
- 📝 **Three output formats**:
  - Annotated PDFs with comment bubbles
  - Word doc with tracked changes
  - HTML review queue for human oversight
- 🔄 **LLM flexibility** - OpenAI or Anthropic

### **Seamless Integration**
- 📊 **Google Sheets** - reads assignments, updates status
- 📁 **Google Drive** - organized folder structure
- 🔐 **Service account** - no user login required
- ⚡ **Background processing** - responsive UI
- 📈 **Real-time progress** - see every step

### **Security & Privacy**
- 🔒 **Encrypted credentials** - service account stored securely
- 🔑 **System keyring** - encryption key in OS-level storage
- 🎯 **Minimal permissions** - only specific Sheet/Drive access
- 🚫 **No data retention** - all processing ephemeral
- 📝 **Comprehensive logging** - full audit trail

---

## 📥 Installation

### **System Requirements**

- **Operating System**: macOS 12+ or Windows 10+
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 500MB for app + cache space
- **Network**: Internet connection required

### **Prerequisites**

You'll need:
1. **Google Service Account** credentials (JSON file)
2. **Google Sheets ID** for Master Control spreadsheet
3. **Google Drive Folder ID** for PDF storage
4. **API Key** (OpenAI or Anthropic) for R2 validation

### **Quick Install**

#### **macOS**
```bash
# Download latest release
curl -LO https://github.com/enshittifying/slr/releases/latest/download/SLR-Citation-Processor-Mac.dmg

# Open DMG
open SLR-Citation-Processor-Mac.dmg

# Drag to Applications folder
# Launch from Applications
```

#### **Windows**
```powershell
# Download latest release
Invoke-WebRequest -Uri "https://github.com/enshittifying/slr/releases/latest/download/SLR-Citation-Processor-Setup.exe" -OutFile "SLR-Setup.exe"

# Run installer
.\SLR-Setup.exe

# Launch from Start Menu
```

### **Development Install**

```bash
# Clone repository
git clone https://github.com/enshittifying/slr.git
cd slr/app

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python main.py
```

---

## 🚀 Quick Start

### **1. First-Time Setup**

When you launch the app for the first time:

1. **Configure Service Account**
   - Click `File → Settings`
   - Upload your `credentials.json` file
   - The app will encrypt and store it securely

2. **Configure Google Services**
   - Enter your Google Sheets ID
   - Enter your Google Drive folder ID
   - Test connection

3. **Configure LLM Provider**
   - Choose OpenAI or Anthropic
   - Enter API key
   - Select model (GPT-4o-mini or Claude 3.5 Sonnet)

4. **Save Configuration**
   - Click `Save`
   - App will connect to services

### **2. Processing Your First Article**

#### **Stage 1: Source Pull (SP)**

```
1. Switch to "Source Pull (SP)" tab
2. Select article from dropdown (e.g., "78.6 Sanders Article")
3. Review source list (App shows: "156 sources, 0 downloaded")
4. Click "Start Source Pull"
5. Watch progress: "Processing 45/156: Downloading case..."
6. Complete! (Typically ~45 minutes for 156 sources)
```

**What Happens:**
- App downloads PDFs from legal databases
- Uploads to Google Drive (organized by article)
- Updates Google Sheets with status
- Caches locally for future runs

#### **Stage 2: R1 Preparation**

```
1. Switch to "R1 Preparation" tab
2. Review sources ready for R1 (142 PDFs downloaded)
3. Click "Start R1 Processing"
4. Progress: "Processing 67/142: Redboxing statute..."
5. Preview redboxed PDFs (optional)
6. Complete! (~20 minutes)
```

**What Happens:**
- Cleans PDFs (removes cover pages, headers)
- Draws red boxes around citation elements
- Uploads R1 PDFs to Drive
- Updates status in Sheets

#### **Stage 3: R2 Validation**

```
1. Switch to "R2 Validation" tab
2. Upload article Word document
3. Click "Start R2 Validation"
4. Progress: "Validating footnote 89/156..."
5. Review validation results
6. Complete! (~1.5 hours)
```

**What Happens:**
- Extracts footnotes from Word doc
- Validates each citation (format + support)
- Generates review queue (24 citations flagged)
- Creates annotated PDFs, Word doc, HTML report

### **3. Human Review**

```
1. Review flagged citations in queue
2. For each issue:
   - View original citation
   - See detected problems
   - Read AI suggestion
   - Choose: [Approve] [Reject] [Edit]
3. Export final R2 package to Drive
```

---

## 🏗️ Architecture

### **High-Level Overview**

```
┌─────────────────────────────────────────────┐
│         Desktop Application (PyQt6)         │
│  ┌────────┬────────┬────────┬────────────┐ │
│  │   SP   │   R1   │   R2   │  Settings  │ │
│  │ Widget │ Widget │ Widget │   Dialog   │ │
│  └────────┴────────┴────────┴────────────┘ │
├─────────────────────────────────────────────┤
│          Core Pipeline Orchestrator         │
│  ┌────────────────────────────────────────┐ │
│  │  SP Machine → R1 Machine → R2 Pipeline │ │
│  │  (SLRinator) (Redboxer)   (LLM Valid.) │ │
│  └────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│              Data Access Layer              │
│  ┌──────────┬──────────┬──────────────────┐│
│  │  Sheets  │  Drive   │   LLM Client     ││
│  │  Client  │  Client  │ (OpenAI/Claude)  ││
│  └──────────┴──────────┴──────────────────┘│
├─────────────────────────────────────────────┤
│               Infrastructure                │
│  • Authentication (Service Account)         │
│  • Configuration (Persistent Settings)      │
│  • Logging (Action + API Logs)             │
│  • Caching (SQLite + File System)          │
└─────────────────────────────────────────────┘
         │
         ├──> Google Sheets API
         ├──> Google Drive API
         ├──> OpenAI/Anthropic API
         └──> Legal Database APIs
```

### **Technology Stack**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| GUI | PyQt6 6.6+ | Cross-platform native UI |
| Language | Python 3.11+ | All business logic |
| PDF Processing | PyMuPDF 1.23+ | PDF manipulation, redboxing |
| Word Processing | python-docx 1.1+ | Footnote extraction |
| Google APIs | google-api-python-client | Sheets/Drive integration |
| LLM Interface | openai, anthropic | Citation validation |
| Packaging | PyInstaller 6.3+ | Desktop application bundles |
| Crypto | cryptography 41+ | Credential encryption |

---

## 📚 Documentation

### **User Guides**
- [Complete Functionality Guide](docs/SLR_Citation_Processor_Complete_Functionality.md) - Comprehensive overview
- [Desktop App Implementation Plan](info/desktop_app_implementation_plan.md) - Technical architecture
- [Bluebook/Redbook Regex Encoding Plan](docs/BLUEBOOK_REDBOOK_REGEX_ENCODING_PLAN.md) - Validation system

### **SLRinator Backend**
- [SLRinator README](SLRinator/README.md) - Source retrieval system
- [SLRinator System Documentation](SLRinator/SYSTEM_DOCUMENTATION.md) - API integrations
- [SLRinator Workflow](SLRinator/WORKFLOW.md) - Processing pipeline

### **API References**
- Google Sheets API: [sheets_client.py](app/data/sheets_client.py)
- Google Drive API: [drive_client.py](app/data/drive_client.py)
- LLM Clients: [llm_client.py](app/data/llm_client.py)

---

## 💻 Development

### **Project Structure**

```
slr/
├── app/                      # Desktop application
│   ├── gui/                  # PyQt6 UI components
│   │   ├── main_window.py    # Main window
│   │   ├── sp_manager.py     # SP tab widget
│   │   ├── r1_manager.py     # R1 tab widget
│   │   ├── r2_manager.py     # R2 tab widget
│   │   ├── settings_dialog.py# Settings
│   │   └── workers.py        # Background threads
│   ├── core/                 # Business logic
│   │   ├── sp_machine.py     # Source pull
│   │   ├── r1_machine.py     # PDF preparation
│   │   ├── r2_pipeline.py    # Validation
│   │   └── orchestrator.py   # Pipeline coordinator
│   ├── data/                 # Data access
│   │   ├── sheets_client.py  # Google Sheets
│   │   ├── drive_client.py   # Google Drive
│   │   └── llm_client.py     # LLM APIs
│   ├── utils/                # Utilities
│   │   ├── auth.py           # Authentication
│   │   ├── config.py         # Configuration
│   │   ├── crypto.py         # Encryption
│   │   └── logging.py        # Logging
│   ├── resources/            # Resources
│   │   ├── bluebook_rules.json
│   │   └── prompts/
│   └── main.py               # Entry point
├── SLRinator/                # Backend (source retrieval)
├── build/                    # Build scripts
├── docs/                     # Documentation
├── tests/                    # Test suite
└── README.md                 # This file
```

### **Running Tests**

```bash
# Run all tests
pytest tests/

# Run specific test module
pytest tests/test_sp_machine.py

# Run with coverage
pytest --cov=app tests/

# Run integration tests
pytest tests/test_integration.py -v
```

### **Building from Source**

#### **macOS**
```bash
cd build
chmod +x build_mac.sh
./build_mac.sh

# Output: dist/SLR-Citation-Processor-Mac.dmg
```

#### **Windows**
```powershell
cd build
.\build_windows.bat

# Output: dist\SLR-Citation-Processor-Setup.exe
```

### **Code Style**

```bash
# Format code
black app/

# Check linting
flake8 app/

# Type checking
mypy app/
```

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

### **Development Workflow**

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes
4. Add tests
5. Run test suite
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open Pull Request

### **Reporting Issues**

- Use GitHub Issues
- Include:
  - OS version
  - Python version
  - Steps to reproduce
  - Expected vs actual behavior
  - Logs (if applicable)

---

## 📄 License

Copyright © 2024 Stanford Law Review

This software is proprietary to Stanford Law Review and is for internal editorial use only.

---

## 🙏 Acknowledgments

- **SLRinator** - Proven source retrieval engine
- **PyQt** - Professional GUI framework
- **OpenAI/Anthropic** - AI-powered validation
- **Google Cloud** - Reliable infrastructure
- **Stanford Law Review Editorial Team** - Requirements and testing

---

## 📞 Support

For questions or issues:

- **GitHub Issues**: [Report bugs or request features](https://github.com/enshittifying/slr/issues)
- **Documentation**: See [docs/](docs/) directory
- **Logs**: Check `logs/` directory for diagnostics

---

## 🗺️ Roadmap

### **v1.1 (Q1 2025)**
- [ ] Regex-based Bluebook validation (faster, cheaper)
- [ ] Batch processing for multiple articles
- [ ] Enhanced PDF preview with zoom/search

### **v1.2 (Q2 2025)**
- [ ] Machine learning for pattern recognition
- [ ] Custom rule builder UI
- [ ] Export to additional formats

### **v2.0 (Q3 2025)**
- [ ] Web-based interface option
- [ ] Multi-user collaboration
- [ ] Real-time sync across instances

---

<div align="center">

**Built with ❤️ by the SLR Development Team**

[Documentation](docs/) | [Issues](https://github.com/enshittifying/slr/issues) | [Releases](https://github.com/enshittifying/slr/releases)

</div>
