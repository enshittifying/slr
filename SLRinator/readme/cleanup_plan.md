# SLRinator Cleanup Plan

## Current Structure Analysis

### Root Directory Files (Need Organization)
- Multiple demo/test files (demo_*.py, integration_test.py)
- Multiple retrieval implementations (redundant)
- Setup files mixed with implementation files

### Identified Issues

#### 1. Redundant Retrieval Files
- `courtlistener_retriever.py` - CourtListener API integration
- `pull_footnotes_1_50.py` - Older retrieval implementation
- `retrieve_actual_pdfs.py` - Manual URL-based retrieval
- `source_retriever_unified.py` - New unified retriever
- Multiple files doing similar things

#### 2. Demo/Test Files in Root
- `demo_sherkow_gugliuzza.py`
- `demo_working_system.py`
- `integration_test.py`
- `run_sherkow_gugliuzza.py`
- Should be in tests/ or examples/

#### 3. Temporary/Obsolete Files
- `create_redboxed_pdfs.py` - Superseded by pdf_redboxer.py
- `apply_redboxing.py` - Redundant with stage1/pdf_redboxer.py
- Multiple setup files doing similar things

## Proposed Clean Structure

```
SLRinator/
├── README.md                        # Main documentation
├── requirements.txt                 # Python dependencies
├── setup.py                        # Package setup
├── .gitignore                      # Git ignore file
│
├── src/                            # Core source code
│   ├── __init__.py
│   ├── core/                      # Core functionality
│   │   ├── __init__.py
│   │   ├── retrieval_framework.py # Systematic retrieval framework
│   │   ├── classifier.py          # Citation classifier
│   │   └── models.py              # Data models
│   │
│   ├── retrievers/                # Source retrievers
│   │   ├── __init__.py
│   │   ├── unified_retriever.py   # Main retriever
│   │   ├── courtlistener.py       # CourtListener integration
│   │   ├── govinfo.py            # GovInfo integration
│   │   └── strategies.py         # Retrieval strategies
│   │
│   ├── processors/                # Document processors
│   │   ├── __init__.py
│   │   ├── footnote_extractor.py  # Extract footnotes
│   │   ├── redboxer.py           # PDF redboxing
│   │   └── validator.py          # Citation validation
│   │
│   ├── integration/               # External integrations
│   │   ├── __init__.py
│   │   ├── google_sheets.py      # Sheets integration
│   │   └── google_drive.py       # Drive integration
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── pdf_utils.py
│       └── logging_config.py
│
├── data/                          # Data directory
│   ├── Sourcepull/               # Retrieved sources
│   │   ├── Retrieved/
│   │   └── Redboxed/
│   └── cache/                    # Temporary cache
│
├── config/                        # Configuration
│   ├── api_keys.example.json
│   └── settings.json
│
├── examples/                      # Example scripts
│   ├── sherkow_gugliuzza.py
│   └── basic_retrieval.py
│
├── tests/                         # Test files
│   ├── test_retrieval.py
│   ├── test_classifier.py
│   └── test_redboxing.py
│
├── docs/                          # Documentation
│   ├── member_handbook_notes.md
│   ├── api_documentation.md
│   └── setup_guide.md
│
└── logs/                          # Log files
    └── .gitkeep
```

## Files to Move/Rename

### Move to src/core/
- `systematic_retrieval_framework.py` → `src/core/retrieval_framework.py`

### Move to src/retrievers/
- `source_retriever_unified.py` → `src/retrievers/unified_retriever.py`
- `courtlistener_retriever.py` → `src/retrievers/courtlistener.py`

### Move to src/processors/
- `footnote_processor.py` → `src/processors/footnote_extractor.py`
- `src/stage1/pdf_redboxer.py` → `src/processors/redboxer.py`

### Move to src/integration/
- `sheets_integration.py` → `src/integration/google_sheets.py`

### Move to examples/
- `demo_sherkow_gugliuzza.py` → `examples/sherkow_gugliuzza.py`
- `run_sherkow_gugliuzza.py` → (merge with above)

### Move to tests/
- `integration_test.py` → `tests/test_integration.py`
- `demo_working_system.py` → `tests/test_system.py`

## Files to Delete (Redundant/Obsolete)

1. `create_redboxed_pdfs.py` - Superseded by pdf_redboxer
2. `apply_redboxing.py` - Redundant
3. `pull_footnotes_1_50.py` - Superseded by unified retriever
4. `retrieve_actual_pdfs.py` - Superseded by unified retriever
5. `setup_api_keys.py` - Move functionality to config management
6. `main.py` - Old implementation
7. `SHERKOW_GUGLIUZZA_COMPLETE.md` - Move content to docs

## New Files to Create

1. `.gitignore` - Ignore logs, cache, __pycache__, .DS_Store
2. `src/core/models.py` - Clean data models
3. `src/utils/logging_config.py` - Centralized logging
4. `docs/setup_guide.md` - Installation instructions
5. `docs/api_documentation.md` - API reference

## Benefits of Cleanup

1. **Clear separation of concerns** - Core, retrievers, processors
2. **No redundant code** - Single implementation for each feature
3. **Proper test structure** - Tests separate from implementation
4. **Better maintainability** - Organized module structure
5. **Professional package structure** - Ready for distribution