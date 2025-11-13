# SLRinator System Documentation

## Complete Architecture and Workflow Guide

### Version: 2.0
### Last Updated: August 9, 2025

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Workflow Pipeline](#workflow-pipeline)
5. [API Integrations](#api-integrations)
6. [Logging System](#logging-system)
7. [Error Handling](#error-handling)
8. [Usage Guide](#usage-guide)
9. [Troubleshooting](#troubleshooting)
10. [Development Guide](#development-guide)

---

## System Overview

### Purpose
SLRinator is an automated legal citation extraction and source retrieval system designed specifically for Stanford Law Review. It processes legal documents, extracts citations from footnotes, and automatically retrieves source materials from various legal databases.

### Key Features
- **Intelligent Citation Parsing**: Uses GPT-5 with fallback regex patterns
- **Multi-Source Retrieval**: Integrates with 10+ legal databases
- **Professional Redboxing**: Automated highlighting of key citation elements
- **Comprehensive Logging**: Full audit trail of all operations
- **Error Recovery**: Automatic retry with exponential backoff
- **Batch Processing**: Handle multiple documents efficiently

### System Requirements
- Python 3.8+
- 4GB RAM minimum
- Internet connection for API access
- Word document processing capability

---

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                          │
│                    Word Documents (.docx)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    EXTRACTION LAYER                          │
│              FootnoteExtractor Component                     │
│         Extracts footnotes with numbering                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     PARSING LAYER                            │
│    ┌──────────────────────────────────────────────┐         │
│    │  Enhanced GPT Parser (Primary)               │         │
│    │  - GPT-5                                    │         │
│    │  - Structured JSON output                    │         │
│    └──────────────────┬───────────────────────────┘         │
│                       │                                      │
│                       ▼ (Fallback)                          │
│    ┌──────────────────────────────────────────────┐         │
│    │  Regex Citation Parser                       │         │
│    │  - Pattern matching                          │         │
│    │  - Basic extraction                          │         │
│    └──────────────────────────────────────────────┘         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    RETRIEVAL LAYER                           │
│    ┌─────────────────────────────────────────────┐          │
│    │        Unified Retriever System             │          │
│    ├─────────────────────────────────────────────┤          │
│    │  • Supreme Court API                        │          │
│    │  • CourtListener API                        │          │
│    │  • GovInfo API                              │          │
│    │  • Justia                                   │          │
│    │  • Case.law (Harvard)                       │          │
│    │  • Google Scholar                           │          │
│    │  • SSRN                                     │          │
│    │  • CrossRef                                 │          │
│    │  • Westlaw Edge (Optional)                  │          │
│    │  • LexisNexis (Optional)                    │          │
│    └─────────────────────────────────────────────┘          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   PROCESSING LAYER                           │
│    ┌─────────────────────────────────────────────┐          │
│    │         PDF Redboxer Component              │          │
│    │  - Text search and highlighting             │          │
│    │  - Priority-based coloring                  │          │
│    │  - Metadata page generation                 │          │
│    └─────────────────────────────────────────────┘          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                     OUTPUT LAYER                             │
│  • PDF files with redboxing                                  │
│  • JSON reports with statistics                              │
│  • CSV spreadsheets for Google Sheets                        │
│  • Action logs for audit trail                               │
│  • API usage logs for monitoring                             │
└──────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
SLRinator/
├── src/
│   ├── core/                      # Core system components
│   │   ├── enhanced_gpt_parser.py # GPT-5 citation parser
│   │   ├── fallback_citation_parser.py # Regex fallback
│   │   ├── pdf_retriever.py       # PDF retrieval logic
│   │   ├── sourcepull_system.py   # Main orchestrator
│   │   └── retrieval_framework.py # Retrieval framework
│   │
│   ├── utils/                     # Utility modules
│   │   ├── action_logger.py       # Action logging system
│   │   ├── api_logger.py          # API usage tracking
│   │   ├── retry_handler.py       # Retry with backoff
│   │   ├── cache_manager.py       # Response caching
│   │   ├── connection_pool.py     # Connection pooling
│   │   └── error_handler.py       # Error management
│   │
│   ├── stage1/                    # Stage 1 processing
│   │   ├── enhanced_source_retriever.py
│   │   ├── pdf_processor.py
│   │   ├── pdf_redboxer.py
│   │   └── spreadsheet_manager.py
│   │
│   ├── processors/                # Document processors
│   │   ├── footnote_extractor.py
│   │   └── redboxer.py
│   │
│   └── retrievers/                # API retrievers
│       ├── courtlistener.py
│       └── unified_retriever.py
│
├── config/                        # Configuration files
│   ├── api_keys.json             # API credentials
│   └── sourcepull_config.yaml    # System config
│
├── output/                        # Output directory
│   ├── data/                     # Retrieved documents
│   ├── logs/                     # System logs
│   └── reports/                  # Generated reports
│
├── tests/                         # Test suite
├── examples/                      # Example scripts
└── readme/                        # Documentation
```

---

## Core Components

### 1. Footnote Extractor
**File**: `src/processors/footnote_extractor.py`

**Purpose**: Extract footnotes from Word documents

**Features**:
- Handles complex document structures
- Preserves footnote numbering
- Supports range filtering
- Maintains original formatting

**Usage**:
```python
from src.processors.footnote_extractor import FootnoteExtractor

extractor = FootnoteExtractor()
footnotes = extractor.extract_from_docx("document.docx")
```

### 2. Enhanced GPT Parser
**File**: `src/core/enhanced_gpt_parser.py`

**Purpose**: Parse citations using GPT-5

**Features**:
- Structured JSON output
- Multiple citation types
- Confidence scoring
- Automatic retry on failure
- Fallback to regex parser

**Citation Types Supported**:
- Court cases
- Federal/state statutes
- Regulations
- Constitutional provisions
- Law review articles
- Books and treatises
- Congressional materials
- Web sources

### 3. Unified Retriever
**File**: `src/retrievers/unified_retriever.py`

**Purpose**: Coordinate retrieval from multiple sources

**Strategy**:
1. Check cache first
2. Try official sources (Supreme Court, GovInfo)
3. Fall back to free databases
4. Use premium APIs if configured
5. Log all attempts

### 4. PDF Redboxer
**File**: `src/stage1/pdf_redboxer.py`

**Purpose**: Highlight citation elements in PDFs

**Features**:
- Text search and highlighting
- Color-coded priorities
- Multiple instance detection
- Metadata page generation
- Verification instructions

### 5. Action Logger
**File**: `src/utils/action_logger.py`

**Purpose**: Comprehensive operation logging

**Tracks**:
- All API calls
- File operations
- Citation parsing
- PDF retrieval
- Errors and recovery
- Workflow progress

---

## Workflow Pipeline

### Stage 1: Document Input
```python
# Load document
document_path = "article.docx"
footnote_range = "1-50"  # Optional
```

### Stage 2: Footnote Extraction
```python
# Extract footnotes
footnotes = extractor.extract_from_docx(
    document_path,
    range_filter=footnote_range
)
```

### Stage 3: Citation Parsing
```python
# Parse with GPT-5
parsed_citations = gpt_parser.parse_multiple_footnotes(footnotes)

# Fallback if GPT fails
if not parsed_citations:
    parsed_citations = fallback_parser.parse_all(footnotes)
```

### Stage 4: Source Retrieval
```python
# Retrieve PDFs
for citation in parsed_citations:
    pdf_path = retriever.retrieve(citation)
    if pdf_path:
        successful_retrievals.append(pdf_path)
```

### Stage 5: Redboxing
```python
# Apply redboxing
for pdf_path in successful_retrievals:
    redboxed_path = redboxer.process(
        pdf_path,
        citation_elements
    )
```

### Stage 6: Report Generation
```python
# Generate reports
report = {
    "total_footnotes": len(footnotes),
    "citations_found": len(parsed_citations),
    "pdfs_retrieved": len(successful_retrievals),
    "success_rate": success_rate
}
```

---

## API Integrations

### Configured APIs

| API | Purpose | Authentication | Rate Limit |
|-----|---------|---------------|------------|
| OpenAI GPT-5 | Citation parsing | API Key | 1 req/sec |
| CourtListener | Federal/state cases | Token | 10 req/sec |
| GovInfo | Statutes/regulations | API Key | 5 req/sec |
| Supreme Court | SCOTUS opinions | None | 2 req/sec |
| Justia | Legal resources | None | 1 req/sec |
| Case.law | Historical cases | Optional | 5 req/sec |
| Google Scholar | Academic papers | None | 0.5 req/sec |
| SSRN | Law review articles | None | 2 req/sec |
| CrossRef | DOI resolution | None | 5 req/sec |

### API Configuration
```json
{
  "openai": {
    "api_key": "sk-...",
    "model": "gpt-5"
  },
  "courtlistener": {
    "token": "..."
  },
  "govinfo": {
    "api_key": "..."
  }
}
```

---

## Logging System

### Log Types

1. **Action Logs** (`output/logs/actions/`)
   - Every system operation
   - Timestamped entries
   - Session tracking
   - JSON format

2. **API Usage Logs** (`output/logs/api_usage/`)
   - All API calls
   - Response codes
   - Error messages
   - Usage statistics

3. **Workflow Logs** (`output/logs/`)
   - High-level workflow progress
   - Success/failure tracking
   - Performance metrics

### Log Analysis
```python
# Generate summary report
from src.utils.action_logger import get_action_logger

logger = get_action_logger()
summary = logger.generate_summary_report()
print(f"Success Rate: {summary['success_rate']}%")
print(f"Total API Calls: {len(summary['api_calls'])}")
```

---

## Error Handling

### Retry Strategy
```python
from src.utils.retry_handler import RetryHandler

handler = RetryHandler(
    max_retries=3,
    base_delay=2.0,
    exponential_base=2.0,
    jitter=True
)
```

### Error Recovery Flow
1. **Initial Attempt**: Try operation
2. **Error Detection**: Catch exception
3. **Retry Decision**: Check if retryable
4. **Backoff Calculation**: Calculate delay
5. **Retry Attempt**: Try again
6. **Fallback**: Use alternative method
7. **Logging**: Record all attempts

### Common Error Scenarios

| Error | Cause | Solution |
|-------|-------|----------|
| API Rate Limit | Too many requests | Exponential backoff |
| Network Timeout | Connection issues | Retry with longer timeout |
| Parse Failure | Complex citation | Fallback to regex |
| PDF Not Found | Source unavailable | Try alternative sources |
| Invalid API Key | Configuration error | Check credentials |

---

## Usage Guide

### Basic Usage
```bash
# Process entire document
python enhanced_sourcepull_workflow.py document.docx

# Process specific footnotes
python enhanced_sourcepull_workflow.py document.docx --footnotes 1-50

# Skip GPT parsing
python enhanced_sourcepull_workflow.py document.docx --no-gpt
```

### Advanced Options
```bash
# Custom output directory
python enhanced_sourcepull_workflow.py document.docx --output ~/Desktop/Output

# Verbose logging
python enhanced_sourcepull_workflow.py document.docx --verbose

# Dry run (no API calls)
python enhanced_sourcepull_workflow.py document.docx --dry-run
```

### Python API
```python
from src.core.sourcepull_system import SourcepullSystem

system = SourcepullSystem()
results = system.process_document(
    "document.docx",
    footnote_range="1-100",
    use_gpt=True,
    output_dir="output"
)
```

---

## Troubleshooting

### Health Check
```bash
# Run comprehensive health check
python system_health_check.py
```

### Common Issues

#### 1. GPT Parsing Failures
**Symptoms**: All footnotes fall back to regex
**Solution**:
- Check OpenAI API key
- Verify API credits
- Review rate limits

#### 2. Low Retrieval Rate
**Symptoms**: Many PDFs not found
**Solution**:
- Configure additional APIs
- Check network connection
- Review citation formats

#### 3. Redboxing Errors
**Symptoms**: Elements not highlighted
**Solution**:
- Verify PyMuPDF installation
- Check PDF text layer
- Review element patterns

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable verbose output
system = SourcepullSystem(debug=True)
```

### Log Analysis
```bash
# View recent errors
grep ERROR output/logs/*.log | tail -20

# Check API failures
grep "API_CALL.*FAILED" output/logs/actions/*.json

# Monitor real-time
tail -f output/logs/enhanced_sourcepull_*.log
```

---

## Development Guide

### Adding New Retriever
```python
# src/retrievers/new_source.py
class NewSourceRetriever:
    def retrieve(self, citation):
        # Implementation
        pass
```

### Custom Citation Type
```python
# Add to enhanced_gpt_parser.py
CITATION_TYPES = {
    "new_type": {
        "pattern": r"...",
        "fields": ["field1", "field2"]
    }
}
```

### Testing
```bash
# Run unit tests
pytest tests/

# Integration test
python tests/test_integration.py

# Stress test
python tests/stress_test.py --citations 1000
```

### Contributing
1. Fork repository
2. Create feature branch
3. Add tests
4. Update documentation
5. Submit pull request

---

## Performance Optimization

### Caching Strategy
- Cache API responses for 24 hours
- Store successful retrievals
- Reuse parsed citations

### Parallel Processing
- Concurrent API calls
- Batch footnote parsing
- Async PDF downloads

### Resource Management
- Connection pooling
- Memory-efficient PDF processing
- Streaming large files

---

## Security Considerations

### API Key Management
- Never commit keys to repository
- Use environment variables in production
- Rotate keys regularly
- Monitor usage for anomalies

### Data Privacy
- Log masking for sensitive data
- Secure file storage
- Encrypted API communications
- User data isolation

---

## Maintenance

### Daily Tasks
- Review error logs
- Check API usage
- Monitor success rates

### Weekly Tasks
- Clear old cache files
- Archive completed jobs
- Update API rate limits

### Monthly Tasks
- Rotate API keys
- Review performance metrics
- Update dependencies

---

## Support and Resources

### Documentation
- API Setup Guide: `API_SETUP_GUIDE.md`
- Workflow Guide: `WORKFLOW.md`
- System Health: `system_health_check.py`

### Logs and Debugging
- Action Logs: `output/logs/actions/`
- API Logs: `output/logs/api_usage/`
- Health Reports: `output/logs/health_check_*.json`

### Contact
- GitHub Issues: Report bugs and request features
- Documentation: Check readme/ directory
- Logs: Review output/logs/ for diagnostics

---

## Version History

### v2.0 (Current)
- Enhanced GPT-5 integration
- Retry logic with exponential backoff
- Comprehensive action logging
- System health monitoring
- Multi-source retrieval

### v1.0
- Basic footnote extraction
- Simple citation parsing
- Manual source retrieval

---

## License

Stanford Law Review - Internal Use Only

---

*Last updated: August 9, 2025*