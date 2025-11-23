# R1 Cite Checking System

**Complete implementation of R1 cite checking for Stanford Law Review**

This system integrates comprehensive citation validation into the R1 (sourcepull) workflow, combining source retrieval with Bluebook/Redbook compliance checking, quote verification, and optional proposition support analysis.

## Overview

The R1 system performs:
1. **Sourcepull** (existing): Retrieve format-preserving PDFs from legal databases
2. **Citation Validation** (NEW): Validate citations against 354 Bluebook + Redbook rules
3. **Quote Verification** (NEW): Character-by-character quote accuracy checking
4. **Support Checking** (NEW, optional): Verify source supports proposition

## Quick Start

```bash
# Basic usage: process document with full validation
python r1_workflow.py article.docx

# Process specific footnotes only
python r1_workflow.py article.docx --footnotes 1-50

# Disable validation (sourcepull only)
python r1_workflow.py article.docx --no-validation --no-quotes

# Enable proposition support checking (requires main text analysis)
python r1_workflow.py article.docx --enable-support
```

## Architecture

```
SLRinator/
├── src/
│   └── r1_validation/              # NEW: R1 validation module
│       ├── __init__.py
│       ├── citation_validator.py   # Citation format validation
│       ├── quote_verifier.py       # Quote accuracy checking
│       ├── support_checker.py      # Proposition support analysis
│       ├── rule_retrieval.py       # Bluebook/Redbook rule retrieval
│       ├── llm_interface.py        # OpenAI API interface
│       └── validation_reporter.py  # Report generation
├── config/
│   ├── validation_settings.py      # NEW: R1 validation config
│   └── rules/
│       └── Bluebook.json          # 354 rules (115 Redbook + 239 Bluebook)
├── prompts/r1/                     # NEW: R1 validation prompts
│   ├── citation_format.txt
│   └── support_check.txt
├── r1_workflow.py                  # NEW: Complete R1 workflow
└── tests/
    └── test_r1_validation.py       # NEW: Test suite
```

## Features

### 1. Citation Format Validation

**Deterministic Checks:**
- Curly quotes (Redbook 24.4)
- Non-breaking spaces (Redbook 24.8)
- Parenthetical capitalization (Bluebook 10.2.1)

**AI-Powered Checks:**
- All 354 Bluebook + Redbook rules
- Context-aware validation
- Evidence-backed error reporting

**Example:**
```python
from src.r1_validation import LLMInterface, CitationValidator, Citation

llm = LLMInterface()
validator = CitationValidator(llm)

citation = Citation(
    full_text='Alice Corp. v. CLS Bank Int\'l, 573 U.S. 208 (2014)',
    citation_type='case',
    footnote_num=1,
    citation_num=1
)

result = validator.validate_citation(citation)

if not result['validation']['is_correct']:
    for error in result['validation']['errors']:
        print(f"Error: {error['description']}")
        print(f"Rule: {error['rb_rule'] or error['bluebook_rule']}")
        print(f"Fix: {error['correct']}")
```

### 2. Quote Verification

**Checks:**
- Character-by-character accuracy
- Bracket usage (alterations, [sic], etc.)
- Ellipsis formatting
- Nested quote conventions

**Example:**
```python
from src.r1_validation import QuoteVerifier

verifier = QuoteVerifier()

result = verifier.verify_quote(
    quoted_text='"patents are important"',
    source_text='In our view, patents are important to innovation.'
)

if result['accurate']:
    print(f"Quote verified with {result['confidence']:.0%} confidence")
else:
    for issue in result['issues']:
        print(f"{issue['severity']}: {issue['description']}")
```

### 3. Support Checking (Optional)

**Analysis:**
- Direct vs. partial vs. no support
- Element-by-element breakdown
- Missing context identification

**Example:**
```python
from src.r1_validation import LLMInterface, SupportChecker

llm = LLMInterface()
checker = SupportChecker(llm)

result = checker.check_support(
    proposition="The court held that software patents are valid",
    source_text="We hold that abstract software ideas are not patentable",
    citation_text="Alice Corp. v. CLS Bank, 573 U.S. 208"
)

print(f"Support level: {result['analysis']['support_level']}")
print(f"Reasoning: {result['analysis']['reasoning']}")
```

## Configuration

### API Keys

Edit `SLRinator/config/api_keys.json`:

```json
{
  "openai": {
    "api_key": "sk-...",
    "assistant_id": "asst_..."  // Optional: for vector search
  }
}
```

### Validation Settings

Edit `SLRinator/config/validation_settings.py`:

```python
# Enable/disable features
ENABLE_CITATION_VALIDATION = True
ENABLE_QUOTE_VERIFICATION = True
ENABLE_SUPPORT_CHECKING = False

# Validation mode
VALIDATION_MODE = "strict"  # or "lenient"

# AI Configuration
GPT_MODEL = "gpt-4o-mini"  # Cost-effective
USE_VECTOR_SEARCH = True   # Use Assistants API with File Search
```

## Workflow Details

### R1 Workflow Pipeline

```
1. Extract Footnotes
   └─> Parse Word document
   └─> Extract footnote text with numbering

2. Parse Citations
   └─> Use GPT-5 for intelligent parsing
   └─> Identify citation type, components
   └─> Handle signals, short forms

3. Pre-Retrieval Validation
   └─> Check citation format
   └─> Flag formatting errors
   └─> Generate corrections

4. Source Retrieval
   └─> Attempt retrieval from databases
   └─> Save to SP-XXX-ShortName.pdf
   └─> Log retrieval status

5. Post-Retrieval Validation
   └─> Verify quotes (if present)
   └─> Check support (if enabled)
   └─> Redbox validation elements

6. Generate Reports
   └─> JSON report with full results
   └─> HTML report for human review
   └─> Human review queue for issues
```

### Validation Checkpoints

**Checkpoint 1: Pre-Retrieval (Citation Format)**
- Runs BEFORE source retrieval
- Fast deterministic + AI checks
- Flags obvious errors early
- Continues to retrieval even with errors

**Checkpoint 2: Post-Retrieval (Quotes & Support)**
- Runs AFTER successful retrieval
- Requires PDF text extraction
- Verifies quotes against source
- Checks proposition support (optional)

## Output

### JSON Report

```json
{
  "report_metadata": {
    "generated_at": "2025-01-15T10:30:00",
    "document_path": "article.docx",
    "validation_enabled": true
  },
  "validation_summary": {
    "total_citations": 73,
    "citations_validated": 73,
    "citations_correct": 45,
    "citations_with_errors": 28,
    "accuracy_rate": "61.6%",
    "quotes_checked": 12,
    "quotes_accurate": 10,
    "quote_accuracy_rate": "83.3%"
  },
  "citations": [
    {
      "citation_num": 1,
      "footnote_num": 1,
      "text": "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014)",
      "type": "case",
      "retrieval_status": "success",
      "pdf_path": "SP-001-Alice_v_CLS.pdf",
      "validation_result": {
        "success": true,
        "validation": {
          "is_correct": true,
          "errors": [],
          "gpt_cost": 0.0023
        }
      },
      "needs_human_review": false
    }
  ],
  "human_review_queue": [],
  "cost_analysis": {
    "total_tokens": 12543,
    "total_cost": "$0.1542",
    "avg_cost_per_citation": "$0.0021"
  }
}
```

### HTML Report

Visual report with:
- Summary statistics
- Color-coded validation results
- Human review queue with priority
- Cost breakdown

## Cost Analysis

**Typical Costs (GPT-4o-mini):**
- Citation validation: $0.001-0.003 per citation
- Quote verification: Free (deterministic)
- Support checking: $0.002-0.005 per check
- **Average R1 cost: ~$0.15 for 73 citations**

**Cost Optimization:**
- Uses GPT-4o-mini (3x cheaper than GPT-4o)
- Deterministic checks first (free)
- Batch processing where possible
- Optional support checking

## Testing

```bash
# Run test suite
cd SLRinator
python tests/test_r1_validation.py

# Run specific test
python -m unittest tests.test_r1_validation.TestCitationValidator.test_curly_quotes_detection
```

## Troubleshooting

### "Bluebook.json not found"
```bash
# Copy Bluebook.json to config
cp reference_files/Bluebook.json SLRinator/config/rules/
```

### "OpenAI API key not configured"
Edit `SLRinator/config/api_keys.json` with your API key

### "No assistant available"
Vector search is optional. The system will fall back to direct GPT calls.

### Low validation accuracy
- Check that Bluebook.json has all 354 rules
- Verify prompt templates are in prompts/r1/
- Try increasing confidence thresholds in settings

## Rule Coverage

**Redbook Rules: 115**
- Citation formatting (1.1-1.19)
- Typefaces (2.1-2.3)
- Subdivisions (3.1-3.7)
- Short citations (4.1-4.4)
- Quotations (5.1-5.5)
- Abbreviations (6.1-6.8)
- Italicization (7.1)
- Capitalization (8.1-8.4)
- Titles of judges (9.1-9.3)
- Cases (10.1-10.18)
- Constitutions (11.1)
- Statutes (12.1-12.8)
- Administrative materials (14.1-14.3)
- Books & reports (15.1-15.6)
- Periodicals (16.1-16.6)
- Unpublished sources (17.1-17.2)
- Internet sources (18.1-18.9)
- International materials (21.1-21.2)
- Style & grammar (22.1-22.11)

**Bluebook Rules: 239**
- Complete 21st edition coverage
- Tables 1, 6, 13 included
- All citation types

## Redbook Priority

The system enforces **Redbook-first priority**:
1. Search Redbook rules first
2. Use Bluebook only if Redbook doesn't address issue
3. Cite Redbook rule numbers in errors when available
4. AI prompt emphasizes Redbook precedence

## Future Enhancements

- [ ] Auto-correction of common errors
- [ ] Machine learning for pattern recognition
- [ ] Real-time validation in Word plugin
- [ ] Integration with citation management tools
- [ ] Batch processing optimization
- [ ] Custom rule additions

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test suite for examples
3. See R1_CITE_CHECKING_INTEGRATION_PLAN.md for design details
4. Contact SLR editorial team

## License

Stanford Law Review - Editorial Use Only

## Credits

- Adapted from R2 pipeline validation system
- Implements Volume 78 Member Editor Handbook requirements
- Full Redbook and Bluebook (21st edition) compliance
