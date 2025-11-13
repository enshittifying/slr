# SLR Citation Processor Desktop Application - Complete Implementation Plan

## Executive Summary

This document provides a comprehensive implementation plan for building a cross-platform desktop application (Windows & Mac) that automates the Stanford Law Review's citation processing pipeline. The application will integrate the existing Python-based `r2_pipeline` and `sp_machine` code into a PyQt6 GUI application that interfaces with Google Cloud services via a service account.

---

## 1. Project Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SLR Citation Processor (Desktop Application)                   │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Presentation Layer (PyQt6)                               │  │
│  │  - Main Window (article selection, progress)              │  │
│  │  - SP Manager Window (source downloading)                 │  │
│  │  - R1 Manager Window (PDF preparation)                    │  │
│  │  - R2 Manager Window (validation & review)                │  │
│  │  - Settings/Configuration                                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           ↕                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Business Logic Layer (Python)                            │  │
│  │  - Pipeline Orchestrator                                  │  │
│  │  - sp_machine (Source Pull)                               │  │
│  │  - R1 Machine (PDF Prep & Redboxing)                      │  │
│  │  - R2 Pipeline (LLM Validation)                           │  │
│  │  - Queue Manager (Background processing)                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           ↕                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Data Access Layer                                        │  │
│  │  - Google Sheets Client (read assignments/update status)  │  │
│  │  - Google Drive Client (upload/download PDFs)             │  │
│  │  - LLM API Client (OpenAI/Anthropic)                      │  │
│  │  - Local Cache Manager (SQLite)                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           ↕                                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Service Account Authentication                           │  │
│  │  - Encrypted credentials.json                             │  │
│  │  - Google OAuth 2.0 client                                │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           ↕ (HTTPS/API calls)
┌─────────────────────────────────────────────────────────────────┐
│  External Services                                              │
│  - Google Sheets API (Master Control Sheet)                    │
│  - Google Drive API (R1/R2 PDF storage)                        │
│  - OpenAI API (GPT-4o-mini for validation)                     │
│  - Legal Database APIs (HeinOnline, Westlaw, etc.)             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

**SP (Source Pull) Flow:**
1. User selects article from Master Sheet
2. App downloads source list for that article
3. For each source: query legal databases → download PDF → upload to Drive → update Sheet
4. Local cache stores progress (resume capability)

**R1 (Preparation) Flow:**
1. App downloads raw PDFs from Drive
2. Clean PDFs (remove cover pages)
3. Perform OCR and metadata extraction
4. Draw redboxes around citation elements (PyMuPDF)
5. Upload prepared R1 PDFs to Drive → update Sheet

**R2 (Validation) Flow:**
1. App downloads R1 PDFs and article Word doc
2. Extract footnotes from Word doc
3. For each citation: call LLM to validate format and support
4. Generate annotated R2 PDFs with comments
5. Create Word doc with tracked changes
6. Upload results to Drive → update Sheet → generate review queue HTML

---

## 2. Technology Stack

### 2.1 Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| GUI Framework | PyQt6 | 6.6+ | Cross-platform native UI |
| Language | Python | 3.11+ | All business logic |
| PDF Processing | PyMuPDF (fitz) | 1.23+ | PDF manipulation, OCR, annotations |
| Word Processing | python-docx | 1.1+ | Footnote extraction, tracked changes |
| HTTP Client | requests | 2.31+ | API calls |
| Google APIs | google-auth, google-api-python-client | Latest | Sheets/Drive integration |
| LLM Interface | openai, anthropic | Latest | Citation validation |
| Local Database | SQLite3 | Built-in | Progress cache, offline mode |
| Packaging | PyInstaller | 6.0+ | .exe (Windows) / .app (Mac) bundles |
| Cryptography | cryptography | 41+ | Encrypt service account credentials |

### 2.2 Additional Dependencies

```
# requirements.txt
PyQt6==6.6.1
PyQt6-WebEngine==6.6.0
PyMuPDF==1.23.8
python-docx==1.1.0
requests==2.31.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
google-api-python-client==2.111.0
openai==1.6.1
anthropic==0.8.1
pandas==2.1.4
openpyxl==3.1.2
cryptography==41.0.7
tqdm==4.66.1
beautifulsoup4==4.12.2
lxml==5.0.0
Pillow==10.1.0
PyInstaller==6.3.0
```

---

## 3. Project Directory Structure

```
slr-citation-processor/
├── app/
│   ├── __init__.py
│   ├── main.py                      # Application entry point
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main application window
│   │   ├── sp_manager.py            # Source Pull tab
│   │   ├── r1_manager.py            # R1 Preparation tab
│   │   ├── r2_manager.py            # R2 Validation tab
│   │   ├── settings_dialog.py       # Settings/config
│   │   ├── progress_widget.py       # Reusable progress display
│   │   └── styles.qss               # Qt stylesheet
│   ├── core/
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Main pipeline coordinator
│   │   ├── sp_machine.py            # Source Pull engine (refactored)
│   │   ├── r1_machine.py            # R1 preparation engine (NEW)
│   │   ├── r2_pipeline.py           # R2 validation engine (refactored)
│   │   ├── citation_parser.py       # Citation parsing logic
│   │   └── queue_manager.py         # Background task queue
│   ├── data/
│   │   ├── __init__.py
│   │   ├── sheets_client.py         # Google Sheets API wrapper
│   │   ├── drive_client.py          # Google Drive API wrapper
│   │   ├── llm_client.py            # OpenAI/Anthropic wrapper
│   │   ├── cache_manager.py         # SQLite local cache
│   │   └── models.py                # Data models (Article, Source, etc.)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── auth.py                  # Service account authentication
│   │   ├── config.py                # App configuration management
│   │   ├── pdf_utils.py             # PDF manipulation helpers
│   │   ├── word_utils.py            # Word document helpers
│   │   └── crypto.py                # Credential encryption/decryption
│   └── resources/
│       ├── icons/                   # Application icons
│       ├── credentials.enc          # Encrypted service account key
│       ├── config.json              # Default configuration
│       └── prompts/                 # LLM prompts
│           ├── citation_format.txt
│           └── support_check.txt
├── tests/
│   ├── __init__.py
│   ├── test_sp_machine.py
│   ├── test_r1_machine.py
│   ├── test_r2_pipeline.py
│   └── test_integration.py
├── build/
│   ├── build_mac.sh                 # Mac build script
│   ├── build_windows.bat            # Windows build script
│   └── slr.spec                     # PyInstaller spec file
├── docs/
│   ├── user_guide.md
│   ├── developer_guide.md
│   └── api_reference.md
├── reference_files/                 # Copy from main repo
│   ├── Bluebook.json
│   ├── r1_handbook_summary.md
│   └── redbook_processed/
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 4. Detailed Component Specifications

### 4.1 GUI Layer (PyQt6)

#### 4.1.1 Main Window (`gui/main_window.py`)

**Responsibilities:**
- Application entry point
- Menu bar (File, Edit, View, Help)
- Tab widget containing SP/R1/R2 managers
- Status bar with connection status
- System tray integration

**Key Features:**
```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SLR Citation Processor")
        self.setMinimumSize(1200, 800)

        # Menu bar
        self.create_menu_bar()

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.addTab(SPManagerWidget(), "Source Pull")
        self.tabs.addTab(R1ManagerWidget(), "R1 Preparation")
        self.tabs.addTab(R2ManagerWidget(), "R2 Validation")

        # Status bar
        self.status_label = QLabel("Ready")
        self.statusBar().addPermanentWidget(self.status_label)

        # Connect to Google Sheets on startup
        self.check_connection()

    def create_menu_bar(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")
        file_menu.addAction("Refresh Articles", self.refresh_articles)
        file_menu.addAction("Settings", self.open_settings)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # Help menu
        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("User Guide", self.open_user_guide)
        help_menu.addAction("About", self.show_about)
```

**Threading Model:**
- UI runs on main thread
- All processing (SP/R1/R2) runs on QThread workers
- Signals/slots for progress updates

#### 4.1.2 SP Manager (`gui/sp_manager.py`)

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  Article Selection                              │
│  [Dropdown: 78.6 Sanders Article]  [Refresh]    │
├─────────────────────────────────────────────────┤
│  Sources (23 total, 18 completed, 5 pending)    │
│  ┌─────────────────────────────────────────┐    │
│  │ ☑ SP-001  Case A v. B       [Downloaded]│    │
│  │ ☑ SP-002  Statute Title     [Downloaded]│    │
│  │ ☐ SP-003  Law Review Art.   [Pending]   │    │
│  │ ...                                      │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  [Start Source Pull]  [Pause]  [View Logs]     │
│                                                 │
│  Progress: ████████░░░░░░░░░░░  18/23           │
└─────────────────────────────────────────────────┘
```

**Implementation:**
```python
class SPManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_articles()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Article selection
        article_layout = QHBoxLayout()
        self.article_combo = QComboBox()
        self.refresh_btn = QPushButton("Refresh")
        article_layout.addWidget(QLabel("Article:"))
        article_layout.addWidget(self.article_combo)
        article_layout.addWidget(self.refresh_btn)

        # Sources list
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(4)
        self.sources_table.setHorizontalHeaderLabels(
            ["ID", "Citation", "Status", "Actions"]
        )

        # Controls
        controls_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Source Pull")
        self.pause_btn = QPushButton("Pause")
        self.logs_btn = QPushButton("View Logs")

        # Progress bar
        self.progress_bar = QProgressBar()

        layout.addLayout(article_layout)
        layout.addWidget(self.sources_table)
        layout.addLayout(controls_layout)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # Connect signals
        self.start_btn.clicked.connect(self.start_processing)
        self.article_combo.currentIndexChanged.connect(self.load_sources)

    def start_processing(self):
        """Start SP processing in background thread"""
        self.worker = SPWorkerThread(self.current_article_id)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.source_completed.connect(self.mark_source_complete)
        self.worker.finished.connect(self.processing_finished)
        self.worker.start()
```

#### 4.1.3 R1 Manager (`gui/r1_manager.py`)

**Features:**
- Similar layout to SP Manager
- Shows R1 PDFs ready for preparation
- Preview pane for PDF viewer
- Manual override for redbox coordinates

**Key Functionality:**
```python
class R1ManagerWidget(QWidget):
    def preview_pdf(self, source_id):
        """Show PDF preview with existing redboxes"""
        pdf_path = self.cache.get_pdf_path(source_id)
        self.pdf_viewer.load_pdf(pdf_path)

        # Overlay existing redboxes
        redboxes = self.r1_machine.get_redboxes(source_id)
        self.pdf_viewer.draw_boxes(redboxes)

    def manual_redbox(self):
        """Allow user to manually draw/adjust redboxes"""
        self.pdf_viewer.enable_drawing_mode()
```

#### 4.1.4 R2 Manager (`gui/r2_manager.py`)

**Features:**
- Shows validation results
- Human review queue
- Side-by-side comparison (original vs. suggested changes)
- Export R2 package

**Key Functionality:**
```python
class R2ManagerWidget(QWidget):
    def show_review_queue(self):
        """Display citations requiring human review"""
        issues = self.r2_pipeline.get_review_queue()
        for issue in issues:
            item = QListWidgetItem(f"{issue.footnote_num}: {issue.issue_type}")
            item.setData(Qt.UserRole, issue)
            self.review_list.addItem(item)

    def approve_change(self, citation_id):
        """User approves LLM suggestion"""
        self.r2_pipeline.approve_change(citation_id)
        self.update_review_queue()

    def reject_change(self, citation_id):
        """User rejects LLM suggestion"""
        self.r2_pipeline.reject_change(citation_id)
```

#### 4.1.5 Settings Dialog (`gui/settings_dialog.py`)

**Configuration Options:**
```python
class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        # Google Sheets ID
        self.sheet_id_input = QLineEdit()
        layout.addRow("Master Sheet ID:", self.sheet_id_input)

        # Google Drive folder
        self.drive_folder_input = QLineEdit()
        layout.addRow("Drive Folder ID:", self.drive_folder_input)

        # LLM Provider
        self.llm_provider = QComboBox()
        self.llm_provider.addItems(["OpenAI", "Anthropic"])
        layout.addRow("LLM Provider:", self.llm_provider)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.api_key_input)

        # Service Account
        self.sa_btn = QPushButton("Update Service Account")
        self.sa_btn.clicked.connect(self.update_service_account)
        layout.addRow("Service Account:", self.sa_btn)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.save_settings)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)
        self.setLayout(layout)
```

---

### 4.2 Business Logic Layer

#### 4.2.1 Pipeline Orchestrator (`core/orchestrator.py`)

**Responsibilities:**
- Coordinates SP → R1 → R2 flow
- Manages state transitions
- Handles errors and retries

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class PipelineStage(Enum):
    NOT_STARTED = "not_started"
    SP_IN_PROGRESS = "sp_in_progress"
    SP_COMPLETE = "sp_complete"
    R1_IN_PROGRESS = "r1_in_progress"
    R1_COMPLETE = "r1_complete"
    R2_IN_PROGRESS = "r2_in_progress"
    R2_COMPLETE = "r2_complete"
    ERROR = "error"

@dataclass
class ArticleState:
    article_id: str
    volume_issue: str
    stage: PipelineStage
    sources_total: int
    sources_completed: int
    last_updated: str
    error_message: Optional[str] = None

class PipelineOrchestrator:
    def __init__(self, sheets_client, drive_client, cache_manager):
        self.sheets = sheets_client
        self.drive = drive_client
        self.cache = cache_manager

        self.sp_machine = None  # Initialized when needed
        self.r1_machine = None
        self.r2_pipeline = None

    def get_article_state(self, article_id: str) -> ArticleState:
        """Get current state of article from cache and Sheet"""
        cached = self.cache.get_article_state(article_id)
        if cached:
            return cached

        # Fetch from Sheet
        sheet_data = self.sheets.get_article_row(article_id)
        state = ArticleState(
            article_id=article_id,
            volume_issue=sheet_data['volume_issue'],
            stage=PipelineStage(sheet_data['stage']),
            sources_total=sheet_data['sources_total'],
            sources_completed=sheet_data['sources_completed'],
            last_updated=sheet_data['last_updated']
        )
        self.cache.save_article_state(state)
        return state

    def run_sp(self, article_id: str, progress_callback=None):
        """Run Source Pull for an article"""
        from .sp_machine import SPMachine

        self.sp_machine = SPMachine(
            sheets_client=self.sheets,
            drive_client=self.drive,
            cache_manager=self.cache
        )

        try:
            self.update_stage(article_id, PipelineStage.SP_IN_PROGRESS)
            self.sp_machine.process_article(article_id, progress_callback)
            self.update_stage(article_id, PipelineStage.SP_COMPLETE)
        except Exception as e:
            self.update_stage(article_id, PipelineStage.ERROR, str(e))
            raise

    def run_r1(self, article_id: str, progress_callback=None):
        """Run R1 Preparation for an article"""
        from .r1_machine import R1Machine

        state = self.get_article_state(article_id)
        if state.stage != PipelineStage.SP_COMPLETE:
            raise ValueError("Cannot run R1: SP not complete")

        self.r1_machine = R1Machine(
            sheets_client=self.sheets,
            drive_client=self.drive,
            cache_manager=self.cache
        )

        try:
            self.update_stage(article_id, PipelineStage.R1_IN_PROGRESS)
            self.r1_machine.process_article(article_id, progress_callback)
            self.update_stage(article_id, PipelineStage.R1_COMPLETE)
        except Exception as e:
            self.update_stage(article_id, PipelineStage.ERROR, str(e))
            raise

    def run_r2(self, article_id: str, progress_callback=None):
        """Run R2 Validation for an article"""
        from .r2_pipeline import R2Pipeline

        state = self.get_article_state(article_id)
        if state.stage != PipelineStage.R1_COMPLETE:
            raise ValueError("Cannot run R2: R1 not complete")

        self.r2_pipeline = R2Pipeline(
            sheets_client=self.sheets,
            drive_client=self.drive,
            llm_client=self.llm_client,
            cache_manager=self.cache
        )

        try:
            self.update_stage(article_id, PipelineStage.R2_IN_PROGRESS)
            self.r2_pipeline.process_article(article_id, progress_callback)
            self.update_stage(article_id, PipelineStage.R2_COMPLETE)
        except Exception as e:
            self.update_stage(article_id, PipelineStage.ERROR, str(e))
            raise

    def update_stage(self, article_id: str, stage: PipelineStage, error_msg: str = None):
        """Update article stage in both cache and Sheet"""
        state = self.get_article_state(article_id)
        state.stage = stage
        state.error_message = error_msg
        state.last_updated = datetime.now().isoformat()

        self.cache.save_article_state(state)
        self.sheets.update_article_stage(article_id, stage.value, error_msg)
```

#### 4.2.2 SP Machine (`core/sp_machine.py`)

**Refactored from existing `/sp_machine/main.py`**

Key changes:
- Add progress callbacks
- Integrate with cache manager
- Better error handling

```python
class SPMachine:
    def __init__(self, sheets_client, drive_client, cache_manager):
        self.sheets = sheets_client
        self.drive = drive_client
        self.cache = cache_manager

        # Initialize pullers for different source types
        from .pullers import (
            HeinOnlinePuller,
            WestlawPuller,
            WebsitePuller,
            GoogleBooksPuller
        )
        self.pullers = {
            'case': HeinOnlinePuller(),
            'statute': WebsitePuller(),
            'article': GoogleBooksPuller(),
            'book': GoogleBooksPuller(),
            'website': WebsitePuller()
        }

    def process_article(self, article_id: str, progress_callback=None):
        """Process all sources for an article"""
        sources = self.sheets.get_sources_for_article(article_id)

        for i, source in enumerate(sources):
            if self.cache.is_source_complete(source['source_id']):
                if progress_callback:
                    progress_callback(i, len(sources), f"Skipping {source['source_id']} (cached)")
                continue

            try:
                if progress_callback:
                    progress_callback(i, len(sources), f"Pulling {source['citation']}")

                # Parse citation to determine source type
                parsed = self.parse_citation(source['citation'])

                # Get appropriate puller
                puller = self.pullers.get(parsed['type'])
                if not puller:
                    raise ValueError(f"No puller for type: {parsed['type']}")

                # Pull the source
                pdf_path = puller.pull(parsed)

                # Upload to Drive
                drive_file_id = self.drive.upload_source_pdf(
                    pdf_path,
                    source['source_id'],
                    article_id
                )

                # Update Sheet
                self.sheets.update_source_status(
                    source['source_id'],
                    status='downloaded',
                    drive_link=f"https://drive.google.com/file/d/{drive_file_id}"
                )

                # Mark in cache
                self.cache.mark_source_complete(source['source_id'], pdf_path)

            except Exception as e:
                logging.error(f"Failed to pull {source['source_id']}: {e}")
                self.sheets.update_source_status(
                    source['source_id'],
                    status='error',
                    error_message=str(e)
                )

    def parse_citation(self, citation: str) -> dict:
        """Parse citation to determine source type and metadata"""
        from .citation_parser import CitationParser
        parser = CitationParser()
        return parser.parse(citation)
```

#### 4.2.3 R1 Machine (`core/r1_machine.py`)

**NEW - Implements R1 Handbook Summary process**

```python
import fitz  # PyMuPDF
from pathlib import Path

class R1Machine:
    def __init__(self, sheets_client, drive_client, cache_manager):
        self.sheets = sheets_client
        self.drive = drive_client
        self.cache = cache_manager

    def process_article(self, article_id: str, progress_callback=None):
        """Prepare all sources for R1 review"""
        sources = self.sheets.get_sources_for_article(article_id)

        for i, source in enumerate(sources):
            if self.cache.is_r1_complete(source['source_id']):
                if progress_callback:
                    progress_callback(i, len(sources), f"Skipping {source['source_id']} (R1 done)")
                continue

            try:
                if progress_callback:
                    progress_callback(i, len(sources), f"Preparing {source['citation']}")

                # Download raw PDF from Drive
                raw_pdf_path = self.drive.download_source_pdf(source['drive_link'])

                # Step 1: Clean PDF (remove cover pages, etc.)
                cleaned_path = self.clean_pdf(raw_pdf_path, source['type'])

                # Step 2: Perform metadata redboxing
                redboxed_path = self.redbox_citation_metadata(
                    cleaned_path,
                    source['citation'],
                    source['type']
                )

                # Step 3: Upload R1 PDF to Drive
                r1_drive_id = self.drive.upload_r1_pdf(
                    redboxed_path,
                    source['source_id'],
                    article_id
                )

                # Update Sheet
                self.sheets.update_r1_status(
                    source['source_id'],
                    status='r1_complete',
                    r1_drive_link=f"https://drive.google.com/file/d/{r1_drive_id}"
                )

                # Mark in cache
                self.cache.mark_r1_complete(source['source_id'], redboxed_path)

            except Exception as e:
                logging.error(f"R1 failed for {source['source_id']}: {e}")
                self.sheets.update_r1_status(source['source_id'], status='error', error_message=str(e))

    def clean_pdf(self, pdf_path: str, source_type: str) -> str:
        """Remove extraneous pages from PDF"""
        doc = fitz.open(pdf_path)

        # HeinOnline PDFs have cover page - remove first page
        if 'hein' in pdf_path.lower():
            doc.delete_page(0)

        # Westlaw PDFs have header - remove first 2 pages
        if 'westlaw' in pdf_path.lower():
            doc.delete_page(0)
            doc.delete_page(0)

        output_path = pdf_path.replace('.pdf', '_cleaned.pdf')
        doc.save(output_path)
        doc.close()
        return output_path

    def redbox_citation_metadata(self, pdf_path: str, citation: str, source_type: str) -> str:
        """Draw red boxes around citation elements"""
        doc = fitz.open(pdf_path)

        # Parse citation to get elements to find
        from .citation_parser import CitationParser
        parser = CitationParser()
        parsed = parser.parse(citation)

        # Use OCR/text search to find elements
        elements_to_box = []

        if source_type == 'case':
            elements_to_box = [
                parsed.get('case_name'),
                parsed.get('reporter'),
                parsed.get('volume'),
                parsed.get('page'),
                parsed.get('year')
            ]
        elif source_type == 'article':
            elements_to_box = [
                parsed.get('author'),
                parsed.get('title'),
                parsed.get('journal'),
                parsed.get('volume'),
                parsed.get('page'),
                parsed.get('year')
            ]

        # Search each page for these elements
        for page_num in range(len(doc)):
            page = doc[page_num]

            for element in elements_to_box:
                if not element:
                    continue

                # Search for text
                text_instances = page.search_for(element)

                for inst in text_instances:
                    # Draw red rectangle
                    annot = page.add_rect_annot(inst)
                    annot.set_colors(stroke=(1, 0, 0))  # Red
                    annot.set_border(width=2)
                    annot.update()

        output_path = pdf_path.replace('.pdf', '_r1.pdf')
        doc.save(output_path)
        doc.close()
        return output_path
```

#### 4.2.4 R2 Pipeline (`core/r2_pipeline.py`)

**Refactored from existing `/r2_pipeline/main.py`**

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ValidationResult:
    footnote_num: int
    citation_text: str
    format_issues: List[str]
    support_issues: List[str]
    quote_issues: List[str]
    suggested_changes: str
    requires_review: bool

class R2Pipeline:
    def __init__(self, sheets_client, drive_client, llm_client, cache_manager):
        self.sheets = sheets_client
        self.drive = drive_client
        self.llm = llm_client
        self.cache = cache_manager

    def process_article(self, article_id: str, progress_callback=None):
        """Run R2 validation for an article"""

        # Step 1: Download article Word doc
        article_doc_path = self.drive.download_article_doc(article_id)

        # Step 2: Extract footnotes
        from .word_utils import extract_footnotes
        footnotes = extract_footnotes(article_doc_path)

        # Step 3: For each footnote, validate each citation
        all_results = []

        for i, footnote in enumerate(footnotes):
            if progress_callback:
                progress_callback(i, len(footnotes), f"Validating footnote {footnote.number}")

            # Parse citations from footnote text
            from .citation_parser import CitationParser
            parser = CitationParser()
            citations = parser.parse_footnote(footnote.text)

            for citation in citations:
                result = self.validate_citation(citation, footnote)
                all_results.append(result)

        # Step 4: Generate outputs
        self.generate_r2_pdfs(all_results, article_id)
        self.generate_word_changes(all_results, article_doc_path, article_id)
        self.generate_review_queue_html(all_results, article_id)

        # Step 5: Upload to Drive and update Sheet
        self.upload_results(article_id)

    def validate_citation(self, citation: dict, footnote) -> ValidationResult:
        """Validate a single citation using LLM"""

        # Get R1 PDF for this source
        source_id = citation['source_id']
        r1_pdf_path = self.cache.get_r1_pdf(source_id)

        # Extract text from R1 PDF
        from .pdf_utils import extract_text
        source_text = extract_text(r1_pdf_path)

        # Load prompts
        format_prompt = self.load_prompt('citation_format.txt')
        support_prompt = self.load_prompt('support_check.txt')

        # Call LLM for format checking
        format_response = self.llm.check_format(
            citation_text=citation['text'],
            format_rules=self.load_bluebook_rules(),
            prompt_template=format_prompt
        )

        # Call LLM for support checking
        support_response = self.llm.check_support(
            proposition=footnote.proposition,
            source_text=source_text,
            citation_text=citation['text'],
            prompt_template=support_prompt
        )

        # Quote verification (deterministic)
        quote_issues = []
        if citation.get('quote'):
            if citation['quote'] not in source_text:
                quote_issues.append("Quote not found verbatim in source")

        # Combine results
        result = ValidationResult(
            footnote_num=footnote.number,
            citation_text=citation['text'],
            format_issues=format_response.get('issues', []),
            support_issues=support_response.get('issues', []),
            quote_issues=quote_issues,
            suggested_changes=format_response.get('suggestion', ''),
            requires_review=(
                len(format_response.get('issues', [])) > 0 or
                len(support_response.get('issues', [])) > 0 or
                len(quote_issues) > 0
            )
        )

        return result

    def generate_r2_pdfs(self, results: List[ValidationResult], article_id: str):
        """Generate annotated R2 PDFs with validation comments"""
        # For each source, add annotations
        sources_processed = set()

        for result in results:
            source_id = self.get_source_id_for_citation(result.citation_text)
            if source_id in sources_processed:
                continue

            r1_pdf_path = self.cache.get_r1_pdf(source_id)
            doc = fitz.open(r1_pdf_path)

            # Find relevant results for this source
            source_results = [r for r in results if self.get_source_id_for_citation(r.citation_text) == source_id]

            # Add comment annotations
            for res in source_results:
                if res.requires_review:
                    page = doc[0]  # Add to first page for now

                    comment_text = f"Footnote {res.footnote_num}:\n"
                    if res.format_issues:
                        comment_text += "Format: " + "; ".join(res.format_issues) + "\n"
                    if res.support_issues:
                        comment_text += "Support: " + "; ".join(res.support_issues) + "\n"

                    annot = page.add_text_annot((50, 50 + len(source_results) * 20), comment_text)
                    annot.update()

            r2_pdf_path = r1_pdf_path.replace('_r1.pdf', '_r2.pdf')
            doc.save(r2_pdf_path)
            doc.close()

            self.cache.save_r2_pdf(source_id, r2_pdf_path)
            sources_processed.add(source_id)

    def generate_word_changes(self, results: List[ValidationResult], article_doc_path: str, article_id: str):
        """Generate Word doc with tracked changes"""
        from docx import Document

        doc = Document(article_doc_path)

        # For each result with suggested changes
        for result in results:
            if not result.suggested_changes:
                continue

            # Find footnote in document
            # This is simplified - actual implementation needs to search footnotes
            for para in doc.paragraphs:
                if f"[{result.footnote_num}]" in para.text:
                    # Add tracked change
                    # (python-docx has limited tracked changes support - may need manual approach)
                    pass

        output_path = article_doc_path.replace('.docx', '_R2_changes.docx')
        doc.save(output_path)
        self.cache.save_r2_word_doc(article_id, output_path)

    def generate_review_queue_html(self, results: List[ValidationResult], article_id: str):
        """Generate HTML report of items requiring review"""
        review_items = [r for r in results if r.requires_review]

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>R2 Review Queue - {article_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .issue {{ border: 1px solid #ccc; padding: 15px; margin: 10px 0; }}
                .format {{ color: #d9534f; }}
                .support {{ color: #f0ad4e; }}
                .quote {{ color: #5bc0de; }}
            </style>
        </head>
        <body>
            <h1>R2 Review Queue for {article_id}</h1>
            <p>{len(review_items)} citations require human review.</p>
        """

        for item in review_items:
            html += f"""
            <div class="issue">
                <h3>Footnote {item.footnote_num}</h3>
                <p><strong>Citation:</strong> {item.citation_text}</p>
            """
            if item.format_issues:
                html += f"<p class='format'><strong>Format Issues:</strong> {'; '.join(item.format_issues)}</p>"
            if item.support_issues:
                html += f"<p class='support'><strong>Support Issues:</strong> {'; '.join(item.support_issues)}</p>"
            if item.quote_issues:
                html += f"<p class='quote'><strong>Quote Issues:</strong> {'; '.join(item.quote_issues)}</p>"
            if item.suggested_changes:
                html += f"<p><strong>Suggested:</strong> {item.suggested_changes}</p>"
            html += "</div>"

        html += "</body></html>"

        output_path = self.cache.get_cache_dir() / f"{article_id}_review_queue.html"
        output_path.write_text(html)
        self.cache.save_review_queue(article_id, str(output_path))
```

---

### 4.3 Data Access Layer

#### 4.3.1 Google Sheets Client (`data/sheets_client.py`)

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

class SheetsClient:
    def __init__(self, credentials_path: str, spreadsheet_id: str):
        self.spreadsheet_id = spreadsheet_id

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )

        self.service = build('sheets', 'v4', credentials=credentials)

    def get_all_articles(self) -> List[dict]:
        """Get all articles from Master Sheet"""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='Articles!A2:Z'
        ).execute()

        rows = result.get('values', [])
        articles = []
        for row in rows:
            articles.append({
                'article_id': row[0],
                'volume_issue': row[1],
                'author': row[2],
                'title': row[3],
                'stage': row[4],
                'sources_total': int(row[5]) if len(row) > 5 else 0,
                'sources_completed': int(row[6]) if len(row) > 6 else 0
            })
        return articles

    def get_sources_for_article(self, article_id: str) -> List[dict]:
        """Get all sources for a specific article"""
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='Sources!A2:Z'
        ).execute()

        rows = result.get('values', [])
        sources = []
        for row in rows:
            if row[1] == article_id:  # article_id column
                sources.append({
                    'source_id': row[0],
                    'article_id': row[1],
                    'citation': row[2],
                    'type': row[3],
                    'status': row[4] if len(row) > 4 else 'pending',
                    'drive_link': row[5] if len(row) > 5 else None
                })
        return sources

    def update_source_status(self, source_id: str, status: str, drive_link: str = None, error_message: str = None):
        """Update source status in Sheet"""
        # Find row for this source_id
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheet_id,
            range='Sources!A2:A'
        ).execute()

        rows = result.get('values', [])
        row_num = None
        for i, row in enumerate(rows):
            if row[0] == source_id:
                row_num = i + 2  # +2 because of header row and 0-indexing
                break

        if not row_num:
            raise ValueError(f"Source {source_id} not found")

        # Update status column (E)
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f'Sources!E{row_num}',
            valueInputOption='RAW',
            body={'values': [[status]]}
        ).execute()

        # Update drive_link if provided
        if drive_link:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Sources!F{row_num}',
                valueInputOption='RAW',
                body={'values': [[drive_link]]}
            ).execute()

        # Update error_message if provided
        if error_message:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f'Sources!G{row_num}',
                valueInputOption='RAW',
                body={'values': [[error_message]]}
            ).execute()

    def update_article_stage(self, article_id: str, stage: str, error_message: str = None):
        """Update article stage"""
        # Similar to update_source_status but for Articles sheet
        pass
```

#### 4.3.2 Google Drive Client (`data/drive_client.py`)

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

class DriveClient:
    def __init__(self, credentials_path: str, root_folder_id: str):
        self.root_folder_id = root_folder_id

        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )

        self.service = build('drive', 'v3', credentials=credentials)

    def upload_source_pdf(self, local_path: str, source_id: str, article_id: str) -> str:
        """Upload source PDF to Drive, returns file ID"""

        # Find or create article folder
        article_folder_id = self.get_or_create_folder(article_id, self.root_folder_id)

        # Find or create SP subfolder
        sp_folder_id = self.get_or_create_folder('SP', article_folder_id)

        # Upload file
        file_metadata = {
            'name': f'{source_id}.pdf',
            'parents': [sp_folder_id]
        }
        media = MediaFileUpload(local_path, mimetype='application/pdf')

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')

    def upload_r1_pdf(self, local_path: str, source_id: str, article_id: str) -> str:
        """Upload R1 PDF to Drive"""
        article_folder_id = self.get_or_create_folder(article_id, self.root_folder_id)
        r1_folder_id = self.get_or_create_folder('R1', article_folder_id)

        file_metadata = {
            'name': f'{source_id}_R1.pdf',
            'parents': [r1_folder_id]
        }
        media = MediaFileUpload(local_path, mimetype='application/pdf')

        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file.get('id')

    def download_source_pdf(self, drive_link: str) -> str:
        """Download PDF from Drive link"""
        # Extract file ID from link
        file_id = drive_link.split('/')[-1]

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        # Save to temp file
        import tempfile
        temp_path = tempfile.mktemp(suffix='.pdf')
        with open(temp_path, 'wb') as f:
            f.write(fh.getvalue())

        return temp_path

    def get_or_create_folder(self, folder_name: str, parent_id: str) -> str:
        """Get folder ID or create if doesn't exist"""
        # Search for existing folder
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields='files(id, name)').execute()
        files = results.get('files', [])

        if files:
            return files[0]['id']

        # Create folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }

        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
```

#### 4.3.3 LLM Client (`data/llm_client.py`)

```python
from abc import ABC, abstractmethod
import openai
import anthropic

class LLMClient(ABC):
    @abstractmethod
    def check_format(self, citation_text: str, format_rules: dict, prompt_template: str) -> dict:
        pass

    @abstractmethod
    def check_support(self, proposition: str, source_text: str, citation_text: str, prompt_template: str) -> dict:
        pass

class OpenAIClient(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def check_format(self, citation_text: str, format_rules: dict, prompt_template: str) -> dict:
        prompt = prompt_template.format(
            citation=citation_text,
            bluebook_rules=str(format_rules)
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Bluebook citation expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        # Parse response - expecting JSON with 'issues' and 'suggestion' fields
        import json
        result = json.loads(response.choices[0].message.content)
        return result

    def check_support(self, proposition: str, source_text: str, citation_text: str, prompt_template: str) -> dict:
        prompt = prompt_template.format(
            proposition=proposition,
            source_text=source_text,
            citation=citation_text
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a legal research expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )

        import json
        result = json.loads(response.choices[0].message.content)
        return result

class AnthropicClient(LLMClient):
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def check_format(self, citation_text: str, format_rules: dict, prompt_template: str) -> dict:
        prompt = prompt_template.format(
            citation=citation_text,
            bluebook_rules=str(format_rules)
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        result = json.loads(response.content[0].text)
        return result

    def check_support(self, proposition: str, source_text: str, citation_text: str, prompt_template: str) -> dict:
        # Similar to check_format
        pass
```

#### 4.3.4 Cache Manager (`data/cache_manager.py`)

```python
import sqlite3
from pathlib import Path
import json

class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.cache_dir / 'cache.db'
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Articles cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                article_id TEXT PRIMARY KEY,
                volume_issue TEXT,
                stage TEXT,
                sources_total INTEGER,
                sources_completed INTEGER,
                last_updated TEXT,
                error_message TEXT
            )
        ''')

        # Sources cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                article_id TEXT,
                sp_complete BOOLEAN,
                r1_complete BOOLEAN,
                r2_complete BOOLEAN,
                sp_pdf_path TEXT,
                r1_pdf_path TEXT,
                r2_pdf_path TEXT,
                last_updated TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def get_article_state(self, article_id: str):
        """Get cached article state"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM articles WHERE article_id = ?', (article_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        from core.orchestrator import ArticleState, PipelineStage
        return ArticleState(
            article_id=row[0],
            volume_issue=row[1],
            stage=PipelineStage(row[2]),
            sources_total=row[3],
            sources_completed=row[4],
            last_updated=row[5],
            error_message=row[6]
        )

    def save_article_state(self, state):
        """Save article state to cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO articles VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            state.article_id,
            state.volume_issue,
            state.stage.value,
            state.sources_total,
            state.sources_completed,
            state.last_updated,
            state.error_message
        ))

        conn.commit()
        conn.close()

    def is_source_complete(self, source_id: str) -> bool:
        """Check if SP is complete for a source"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT sp_complete FROM sources WHERE source_id = ?', (source_id,))
        row = cursor.fetchone()
        conn.close()

        return row[0] if row else False

    def mark_source_complete(self, source_id: str, pdf_path: str):
        """Mark source as SP complete"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO sources (source_id, sp_complete, sp_pdf_path, last_updated)
            VALUES (?, ?, ?, datetime('now'))
        ''', (source_id, True, pdf_path))

        conn.commit()
        conn.close()

    # Similar methods for R1 and R2
```

---

### 4.4 Security & Authentication

#### 4.4.1 Service Account Setup (`utils/auth.py`)

```python
from google.oauth2 import service_account
from pathlib import Path
import json
from .crypto import decrypt_credentials

class ServiceAccountAuth:
    def __init__(self, encrypted_creds_path: str, encryption_key: str):
        self.encrypted_creds_path = Path(encrypted_creds_path)
        self.encryption_key = encryption_key

        self.credentials = None

    def get_credentials(self, scopes: list):
        """Get service account credentials"""
        if self.credentials:
            return self.credentials

        # Decrypt credentials
        encrypted_data = self.encrypted_creds_path.read_bytes()
        decrypted_json = decrypt_credentials(encrypted_data, self.encryption_key)

        creds_dict = json.loads(decrypted_json)

        self.credentials = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=scopes
        )

        return self.credentials
```

#### 4.4.2 Credential Encryption (`utils/crypto.py`)

```python
from cryptography.fernet import Fernet
import base64

def generate_key() -> bytes:
    """Generate encryption key - run once during setup"""
    return Fernet.generate_key()

def encrypt_credentials(credentials_json: str, key: bytes) -> bytes:
    """Encrypt service account JSON"""
    f = Fernet(key)
    return f.encrypt(credentials_json.encode())

def decrypt_credentials(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt service account JSON"""
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()

# Usage during app setup:
# 1. User provides service account JSON file
# 2. App generates encryption key
# 3. App encrypts JSON and saves to resources/credentials.enc
# 4. App stores encryption key in system keyring (not in code!)
```

**Note:** The encryption key should NOT be hardcoded. Use system keyring:

```python
import keyring

# Store key
keyring.set_password("slr-citation-processor", "encryption_key", key.decode())

# Retrieve key
key = keyring.get_password("slr-citation-processor", "encryption_key").encode()
```

---

## 5. Implementation Phases

### Phase 1: Foundation (Week 1-2)

**Goals:**
- Set up project structure
- Implement data layer
- Basic GUI skeleton

**Tasks:**
1. Create project directory structure
2. Set up virtual environment and install dependencies
3. Implement `SheetsClient` and test with real Master Sheet
4. Implement `DriveClient` and test upload/download
5. Create basic `MainWindow` with tabs (no functionality yet)
6. Implement `CacheManager` with SQLite
7. Set up service account and encryption

**Deliverables:**
- App launches and shows empty UI
- Can connect to Google Sheets and read articles
- Can upload/download test PDFs to/from Drive

### Phase 2: SP Machine Integration (Week 3-4)

**Goals:**
- Integrate existing sp_machine code
- Build SP Manager UI
- Implement background processing

**Tasks:**
1. Refactor `sp_machine/main.py` into `core/sp_machine.py`
2. Implement `SPManagerWidget` with article selection and progress display
3. Create `SPWorkerThread` for background processing
4. Implement source pullers (HeinOnline, Westlaw, website)
5. Test end-to-end SP flow for one article
6. Add error handling and retry logic

**Deliverables:**
- User can select article and start SP processing
- PDFs are downloaded and uploaded to Drive
- Progress is shown in real-time
- Sheet is updated with status

### Phase 3: R1 Machine (Week 5-6)

**Goals:**
- Build R1 preparation engine
- Implement PDF cleaning and redboxing
- Build R1 Manager UI

**Tasks:**
1. Implement `R1Machine.clean_pdf()` for different source types
2. Implement `R1Machine.redbox_citation_metadata()` with PyMuPDF
3. Create `R1ManagerWidget` with PDF preview
4. Test redboxing accuracy on various source types
5. Implement manual override for redbox adjustment

**Deliverables:**
- R1 machine cleans and redboxes PDFs automatically
- User can preview and adjust redboxes in UI
- R1 PDFs uploaded to Drive

### Phase 4: R2 Pipeline Integration (Week 7-8)

**Goals:**
- Integrate existing r2_pipeline code
- Implement LLM validation
- Build R2 Manager UI with review queue

**Tasks:**
1. Refactor `r2_pipeline/main.py` into `core/r2_pipeline.py`
2. Implement `LLMClient` (OpenAI and Anthropic)
3. Implement footnote extraction from Word docs
4. Implement citation format validation
5. Implement support checking
6. Create `R2ManagerWidget` with review queue
7. Generate R2 PDFs, Word doc, and HTML report

**Deliverables:**
- R2 validation runs end-to-end
- Review queue shows issues requiring human attention
- User can approve/reject LLM suggestions
- Final R2 package uploaded to Drive

### Phase 5: Orchestration & Polish (Week 9-10)

**Goals:**
- Implement full pipeline orchestration
- Add settings and configuration
- Polish UI/UX

**Tasks:**
1. Implement `PipelineOrchestrator` for SP→R1→R2 flow
2. Implement `SettingsDialog` for configuration
3. Add menu bar actions (refresh, help, about)
4. Implement system tray integration
5. Add logging and error reporting
6. Create user documentation
7. UI polish (icons, styling, animations)

**Deliverables:**
- User can run entire pipeline with one click
- Settings are persistent across sessions
- Professional, polished UI
- Complete user guide

### Phase 6: Testing & Packaging (Week 11-12)

**Goals:**
- Comprehensive testing
- Build installers for Mac and Windows
- Deployment

**Tasks:**
1. Write unit tests for all core modules
2. Integration testing with real data
3. User acceptance testing
4. Set up PyInstaller build scripts
5. Test builds on Mac and Windows
6. Create installer packages
7. Set up auto-update mechanism (check GitHub releases)

**Deliverables:**
- Test coverage > 80%
- Mac .app bundle (notarized)
- Windows .exe installer
- Deployment to GitHub releases

---

## 6. Service Account Setup & Security

### 6.1 Google Cloud Project Setup

**Step-by-step:**

1. **Create Google Cloud Project**
   - Go to console.cloud.google.com
   - Create new project: "SLR Citation Processor"

2. **Enable APIs**
   - Google Sheets API
   - Google Drive API

3. **Create Service Account**
   - IAM & Admin → Service Accounts → Create
   - Name: "slr-desktop-app"
   - Description: "Service account for desktop citation processor"

4. **Create Key**
   - Click on service account → Keys → Add Key → JSON
   - Download `credentials.json`

5. **Grant Permissions**
   - Share Master Sheet with service account email (editor access)
   - Share Drive folder with service account email (editor access)

6. **Domain Restrictions** (if possible)
   - In service account settings, restrict to `stanford.edu` domain

### 6.2 Embedding Credentials in App

**Security Model:**

```python
# During first run / setup:
def setup_service_account():
    # User provides credentials.json
    creds_path = QFileDialog.getOpenFileName(None, "Select Service Account JSON")

    # Generate encryption key
    from utils.crypto import generate_key, encrypt_credentials
    key = generate_key()

    # Encrypt credentials
    with open(creds_path, 'r') as f:
        creds_json = f.read()

    encrypted = encrypt_credentials(creds_json, key)

    # Save encrypted credentials to app resources
    encrypted_path = Path('app/resources/credentials.enc')
    encrypted_path.write_bytes(encrypted)

    # Save key to system keyring (NOT in code!)
    import keyring
    keyring.set_password("slr-citation-processor", "encryption_key", key.decode())

    print("Service account configured successfully!")
```

**Important:**
- Credentials are encrypted at rest
- Encryption key stored in OS keyring (macOS Keychain, Windows Credential Manager)
- Key is NEVER in source code or version control
- Service account has minimal permissions (specific Sheet + Drive folder only)

---

## 7. Building & Packaging

### 7.1 PyInstaller Configuration

**`build/slr.spec`:**

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../app/resources', 'resources'),
        ('../reference_files', 'reference_files'),
    ],
    hiddenimports=[
        'PyQt6',
        'fitz',
        'google.auth',
        'googleapiclient',
        'openai',
        'anthropic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SLR Citation Processor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../app/resources/icons/app.icns',  # Mac
)

# For Mac
app = BUNDLE(
    exe,
    name='SLR Citation Processor.app',
    icon='../app/resources/icons/app.icns',
    bundle_identifier='edu.stanford.law.citation-processor',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
    },
)
```

### 7.2 Build Scripts

**`build/build_mac.sh`:**

```bash
#!/bin/bash

# Clean previous builds
rm -rf dist/ build/

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run PyInstaller
pyinstaller build/slr.spec

# Sign the app (requires Apple Developer ID)
codesign --force --deep --sign "Developer ID Application: Your Name" \
    "dist/SLR Citation Processor.app"

# Create DMG
hdiutil create -volname "SLR Citation Processor" \
    -srcfolder "dist/SLR Citation Processor.app" \
    -ov -format UDZO \
    "dist/SLR-Citation-Processor-Mac.dmg"

echo "Build complete: dist/SLR-Citation-Processor-Mac.dmg"
```

**`build/build_windows.bat`:**

```batch
@echo off

REM Clean previous builds
rmdir /s /q dist build

REM Activate virtual environment
call venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Run PyInstaller
pyinstaller build\slr.spec

REM Create installer with Inno Setup (optional)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer.iss

echo Build complete: dist\SLR-Citation-Processor-Setup.exe
```

### 7.3 Distribution

**GitHub Releases:**

1. Tag version: `git tag v1.0.0`
2. Push tag: `git push origin v1.0.0`
3. Create GitHub release with:
   - `SLR-Citation-Processor-Mac.dmg`
   - `SLR-Citation-Processor-Windows.exe`
   - Release notes

**Auto-update mechanism:**

```python
def check_for_updates():
    import requests

    current_version = "1.0.0"

    response = requests.get(
        "https://api.github.com/repos/enshittifying/slr/releases/latest"
    )

    latest = response.json()
    latest_version = latest['tag_name'].lstrip('v')

    if latest_version > current_version:
        # Prompt user to download update
        msg = QMessageBox()
        msg.setText(f"Version {latest_version} is available!")
        msg.setInformativeText("Would you like to download it?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        if msg.exec() == QMessageBox.Yes:
            import webbrowser
            webbrowser.open(latest['html_url'])
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test Coverage:**
- All `core/` modules (SP, R1, R2)
- All `data/` clients (Sheets, Drive, LLM)
- Citation parser
- PDF utilities

**Example Test:**

```python
# tests/test_sp_machine.py
import unittest
from unittest.mock import Mock, patch
from app.core.sp_machine import SPMachine

class TestSPMachine(unittest.TestCase):
    def setUp(self):
        self.sheets_client = Mock()
        self.drive_client = Mock()
        self.cache_manager = Mock()

        self.sp_machine = SPMachine(
            self.sheets_client,
            self.drive_client,
            self.cache_manager
        )

    def test_process_article_success(self):
        # Mock sources
        self.sheets_client.get_sources_for_article.return_value = [
            {
                'source_id': 'SP-001',
                'citation': 'Case A v. B, 123 U.S. 456 (2020)',
                'type': 'case'
            }
        ]

        # Mock puller
        with patch('app.core.sp_machine.HeinOnlinePuller') as MockPuller:
            mock_puller = MockPuller.return_value
            mock_puller.pull.return_value = '/tmp/test.pdf'

            # Run
            self.sp_machine.process_article('article-001')

            # Assert
            self.drive_client.upload_source_pdf.assert_called_once()
            self.sheets_client.update_source_status.assert_called_once_with(
                'SP-001',
                status='downloaded',
                drive_link=unittest.mock.ANY
            )
```

### 8.2 Integration Tests

**Test with real Google APIs (sandbox environment):**

```python
# tests/test_integration.py
import unittest
from app.data.sheets_client import SheetsClient
from app.data.drive_client import DriveClient

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Use test service account and test sheet
        cls.sheets = SheetsClient('test_credentials.json', 'TEST_SHEET_ID')
        cls.drive = DriveClient('test_credentials.json', 'TEST_FOLDER_ID')

    def test_end_to_end_sp(self):
        # Create test article in test sheet
        # Run SP machine
        # Verify PDF uploaded to Drive
        # Verify Sheet updated
        pass
```

### 8.3 User Acceptance Testing

**Test Cases:**

1. **First-time setup**
   - User installs app
   - User configures service account
   - User enters API keys
   - App connects to Google Sheets

2. **SP Processing**
   - User selects article
   - User starts SP
   - All sources downloaded
   - User can pause/resume

3. **R1 Processing**
   - User reviews R1 PDFs
   - User manually adjusts redboxes
   - R1 PDFs uploaded

4. **R2 Processing**
   - User runs R2 validation
   - User reviews issues
   - User approves/rejects changes
   - Final package generated

5. **Error Handling**
   - Network disconnection during processing
   - Invalid API credentials
   - Missing source (not found in databases)
   - LLM rate limit exceeded

---

## 9. Deployment Checklist

**Before Release:**

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] User acceptance testing complete
- [ ] Code reviewed
- [ ] User documentation complete
- [ ] Mac build tested on macOS 12, 13, 14
- [ ] Windows build tested on Windows 10, 11
- [ ] Service account permissions verified
- [ ] Encryption key generation tested
- [ ] Auto-update mechanism tested
- [ ] License file included
- [ ] GitHub repository public
- [ ] Release notes written

**Release Process:**

1. Bump version in `app/__init__.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Build Mac and Windows installers
5. Create GitHub release
6. Upload installers
7. Announce to users

---

## 10. Future Enhancements

**Potential features for v2.0:**

1. **Multi-user collaboration**
   - Multiple editors can work on same article
   - Real-time progress sync

2. **Advanced redboxing**
   - Machine learning model for automatic redbox detection
   - Higher accuracy for complex layouts

3. **Bluebook updates**
   - Auto-update Bluebook.json from online source
   - Version tracking

4. **Analytics dashboard**
   - Citation statistics
   - Common errors
   - Processing time metrics

5. **Batch processing**
   - Process multiple articles in parallel
   - Scheduled processing

6. **Mobile companion app**
   - iOS/Android app to view progress
   - Push notifications

7. **Integration with Zotero**
   - Import citations from Zotero library

---

## 11. Conclusion

This implementation plan provides a complete roadmap for building the SLR Citation Processor desktop application. The phased approach allows for iterative development and testing, while the detailed specifications ensure consistency and maintainability.

**Key Success Factors:**

1. **Reuse existing code** - Leverage r2_pipeline and sp_machine
2. **Robust error handling** - Network issues, API limits, edge cases
3. **User-centric design** - Clean UI, clear feedback, helpful errors
4. **Security first** - Encrypted credentials, minimal permissions
5. **Cross-platform compatibility** - Test thoroughly on both platforms
6. **Comprehensive testing** - Unit, integration, and user acceptance

**Estimated Timeline:**
- 12 weeks for full implementation
- 2-week buffer for bug fixes
- Total: ~14 weeks to production-ready v1.0

**Team Requirements:**
- 1 Python developer (full-time)
- 1 UI/UX designer (part-time, weeks 1-6)
- 1 QA tester (part-time, weeks 9-12)
- 1 technical writer (part-time, weeks 10-12)

---

**Document Version:** 1.0
**Last Updated:** 2024-11-13
**Author:** SLR Development Team
