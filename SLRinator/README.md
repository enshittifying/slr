# Stanford Law Review Editorial Automation System (SLRinator)

## Overview

The SLRinator is a comprehensive automation system for Stanford Law Review editorial processes, implementing sourcepull, redboxing, citechecking, and Bluebook compliance verification.

## Features

### Sourcepull (SP)
- **Systematic Source Retrieval**: Hierarchical retrieval system with multiple fallback strategies
- **Smart Classification**: Automatic citation type detection (cases, statutes, articles, books)
- **PDF Redboxing**: Intelligent highlighting of citation elements in retrieved PDFs
- **Google Sheets Integration**: Direct integration with SLR sourcepull spreadsheets
- **Multi-Database Support**: CourtListener, GovInfo, HeinOnline, Westlaw, Lexis
- **Reasoning Documentation**: Tracks and documents why each source was retrieved from specific locations

### R1 Cite Checking (NEW!)
- **Citation Format Validation**: Validates against 354 Bluebook + Redbook rules
- **Quote Accuracy Verification**: Character-by-character quote checking
- **Proposition Support Analysis**: Verifies source supports legal claims (optional)
- **Hybrid Validation**: Deterministic checks + AI-powered analysis
- **Comprehensive Reporting**: JSON and HTML reports with human review queue
- **Cost-Effective**: ~$0.002 per citation using GPT-4o-mini

See [R1_CITE_CHECKING_README.md](R1_CITE_CHECKING_README.md) for details.

## Installation

### Quick Setup (R1 Cite Checking)

```bash
cd SLRinator
python setup_r1.py
```

This installs all dependencies and configures the R1 cite checking system.

See [QUICKSTART.md](QUICKSTART.md) for detailed instructions.

### Manual Installation

```bash
# Clone the repository
git clone [repository-url]
cd SLRinator

# Install dependencies
pip install -r requirements_r1.txt

# Set up API keys
cp config/api_keys.example.json config/api_keys.json
# Edit config/api_keys.json with your actual API keys
```

## Project Structure

```
SLRinator/
├── src/                    # Core source code
│   ├── core/              # Core framework and classification
│   ├── retrievers/        # Source retrieval implementations
│   ├── processors/        # Document processing (extraction, redboxing)
│   ├── integration/       # External service integrations
│   ├── r1_validation/     # R1 cite checking validation (NEW)
│   └── utils/             # Utility functions
├── config/                # Configuration files
│   ├── rules/             # Bluebook.json (354 rules)
│   └── validation_settings.py  # R1 validation config
├── prompts/r1/            # R1 validation prompts
├── output/                # All generated output
│   ├── data/             # Retrieved and processed documents
│   ├── r1_validation/    # R1 validation reports
│   ├── logs/             # Application logs
│   └── reports/          # Generated reports
├── examples/             # Example usage scripts
│   └── r1_basic_example.py  # R1 validation examples
├── tests/                # Test suite
│   └── test_r1_validation.py  # R1 validation tests
├── r1_workflow.py        # Complete R1 workflow (NEW)
├── setup_r1.py           # R1 setup script (NEW)
├── setup_vector_store.py # Vector store setup (NEW)
├── QUICKSTART.md         # Quick start guide (NEW)
└── R1_CITE_CHECKING_README.md  # R1 documentation (NEW)
```

## Quick Start

### R1 Workflow (Sourcepull + Cite Checking)

```bash
# Process entire document with validation
python r1_workflow.py article.docx

# Process specific footnotes
python r1_workflow.py article.docx --footnotes 1-50
```

See [QUICKSTART.md](QUICKSTART.md) for more options.

### Basic Retrieval (Sourcepull Only)

```python
from src.retrievers.unified_retriever import SourceRetriever
from src.core.retrieval_framework import SourceClassifier

# Initialize retriever
retriever = SourceRetriever()

# Classify and retrieve a source
citation = "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014)"
source_type, components = SourceClassifier.classify(citation)
pdf_path = retriever.retrieve_source(1, citation)
```

### Redboxing PDFs

```python
from src.processors.redboxer import SmartRedboxer

redboxer = SmartRedboxer()
redboxer.redbox_citation(
    input_path="output/data/Sourcepull/Retrieved/input.pdf",
    output_path="output/data/Sourcepull/Redboxed/output.pdf",
    citation_type="case",
    citation_data={
        'party1': 'Alice Corp.',
        'party2': 'CLS Bank',
        'volume': '573',
        'reporter': 'U.S.',
        'page': '208',
        'year': '2014'
    }
)
```

### Processing Article Footnotes

```python
from src.processors.footnote_extractor import extract_footnotes_from_docx

# Extract footnotes from a Word document
footnotes = extract_footnotes_from_docx("article.docx")

# Process each footnote for retrieval
for fn_num, fn_text in footnotes.items():
    pdf_path = retriever.retrieve_source(fn_num, fn_text)
    # PDFs are saved to output/data/Sourcepull/Retrieved/
```

## Configuration

### API Keys

Create `config/api_keys.json`:

```json
{
    "courtlistener": {
        "token": "your-token-here"
    },
    "govinfo": {
        "api_key": "your-key-here"
    }
}
```

### Settings

Edit `config/settings.json` to configure:
- Retrieval hierarchy preferences
- Cache settings
- Output directories
- Logging levels

## Retrieval Hierarchy

The system follows Stanford Law Review's retrieval hierarchy:

1. **Format-Preserving Sources** (Highest Priority)
   - CourtListener (federal cases)
   - GovInfo.gov (federal documents)
   - State court websites
   - Publisher websites

2. **Database Sources** (Medium Priority)
   - HeinOnline
   - Westlaw
   - Lexis Advance
   - Google Scholar

3. **Fallback Sources** (Lowest Priority)
   - Justia
   - Generic search engines

## Testing

```bash
# Run all tests
python -m pytest tests/

# Run specific test module
python -m pytest tests/test_retrieval.py

# Run with coverage
python -m pytest --cov=src tests/
```

## Examples

See the `examples/` directory for complete working examples:

- `sherkow_gugliuzza.py` - Process Sherkow & Gugliuzza article
- `basic_retrieval.py` - Simple retrieval examples

## Documentation

Additional documentation can be found in the `readme/` directory:
- [Enhancement Ideas](readme/ENHANCEMENTS.md) - Future improvements and features
- [Cleanup Plan](readme/cleanup_plan.md) - Project organization details

## Contributing

Please ensure all tests pass before submitting pull requests:

```bash
python -m pytest tests/
python -m flake8 src/
```


## License

Stanford Law Review - Editorial Use Only

## Support

For issues or questions, please contact the Stanford Law Review editorial team.