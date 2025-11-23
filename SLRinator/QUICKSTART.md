# R1 Cite Checking Quick Start Guide

Get started with the R1 cite checking system in 5 minutes.

## Prerequisites

- Python 3.8+
- OpenAI API key
- Word document with footnotes

## Installation

### Step 1: Run Setup Script

```bash
cd SLRinator
python setup_r1.py
```

This will:
- ✓ Check Python version
- ✓ Install all dependencies
- ✓ Create config directories
- ✓ Set up output directories
- ✓ Verify installation

### Step 2: Configure API Key

Edit `config/api_keys.json`:

```json
{
  "openai": {
    "api_key": "sk-your-key-here"
  }
}
```

### Step 3 (Optional): Set Up Vector Store

For faster and more accurate validation using OpenAI Assistants API:

```bash
python setup_vector_store.py
```

This creates a vector store with all 354 Bluebook + Redbook rules.

## Basic Usage

### Process a Document

```bash
# Full R1 workflow (sourcepull + validation)
python r1_workflow.py path/to/article.docx

# Process specific footnotes
python r1_workflow.py path/to/article.docx --footnotes 1-50

# Process multiple ranges
python r1_workflow.py path/to/article.docx --footnotes "1-50,100-150"
```

### Options

```bash
# Disable citation validation (sourcepull only)
python r1_workflow.py article.docx --no-validation

# Disable quote checking
python r1_workflow.py article.docx --no-quotes

# Enable proposition support checking (requires main text analysis)
python r1_workflow.py article.docx --enable-support

# Custom output directory
python r1_workflow.py article.docx --output ~/Desktop/R1_Output
```

## Programmatic Usage

### Example 1: Validate a Single Citation

```python
from src.r1_validation import LLMInterface, CitationValidator, Citation

# Initialize
llm = LLMInterface()
validator = CitationValidator(llm)

# Create citation
citation = Citation(
    full_text='Alice Corp. v. CLS Bank Int\'l, 573 U.S. 208 (2014)',
    citation_type='case',
    footnote_num=1,
    citation_num=1
)

# Validate
result = validator.validate_citation(citation)

# Check results
if result['validation']['is_correct']:
    print("✓ Citation is correct")
else:
    print("✗ Errors found:")
    for error in result['validation']['errors']:
        print(f"  - {error['description']}")
```

### Example 2: Verify a Quote

```python
from src.r1_validation import QuoteVerifier

verifier = QuoteVerifier()

result = verifier.verify_quote(
    quoted_text='"patents are important"',
    source_text='In our view, patents are important to innovation.'
)

if result['accurate']:
    print(f"✓ Quote verified ({result['confidence']:.0%} confidence)")
else:
    print(f"✗ Issues: {result['issues']}")
```

### Example 3: Run Examples

```bash
python examples/r1_basic_example.py
```

## Output

### JSON Report

Location: `output/r1_validation/r1_validation_report_TIMESTAMP.json`

Contains:
- Validation summary statistics
- Detailed results for each citation
- Quote verification results
- Cost analysis
- Human review queue

### HTML Report

Location: `output/r1_validation/r1_validation_report_TIMESTAMP.html`

Visual report with:
- Color-coded results
- Summary statistics
- Human review queue
- Filterable tables

### Retrieved PDFs

Location: `output/data/Sourcepull/Retrieved/`

Format: `SP-001-ShortName.pdf`

## Understanding Results

### Citation Validation

**Correct citation:**
```json
{
  "is_correct": true,
  "errors": [],
  "confidence": 1.0
}
```

**Citation with errors:**
```json
{
  "is_correct": false,
  "errors": [
    {
      "error_type": "curly_quotes_error",
      "description": "Use curly quotes instead of straight quotes",
      "rb_rule": "24.4",
      "current": "\"text\"",
      "correct": ""text""
    }
  ]
}
```

### Quote Verification

**Accurate quote:**
```json
{
  "accurate": true,
  "confidence": 1.0,
  "issues": []
}
```

**Inaccurate quote:**
```json
{
  "accurate": false,
  "confidence": 0.7,
  "issues": [
    {
      "issue_type": "mismatch",
      "severity": "major",
      "description": "Character mismatch at position 15"
    }
  ],
  "suggested_action": "review_major_issues"
}
```

## Common Issues

### "Bluebook.json not found"

**Fix:**
```bash
# Copy from reference_files
cp ../reference_files/Bluebook.json config/rules/
```

### "OpenAI API key not configured"

**Fix:**
```bash
# Edit config/api_keys.json
nano config/api_keys.json

# Add your key:
{
  "openai": {
    "api_key": "sk-your-key-here"
  }
}
```

### "Module not found" errors

**Fix:**
```bash
# Reinstall dependencies
pip install -r requirements_r1.txt
```

### API rate limiting

**Fix:**
- The system includes automatic rate limiting and retries
- If issues persist, add delays between citations
- Consider using vector store for more efficient validation

## Cost Management

**Typical costs:**
- Citation validation: $0.001-0.003 per citation
- Quote verification: FREE (deterministic)
- Support checking: $0.002-0.005 per check

**For 73 citations (typical article):**
- Validation only: ~$0.15
- With support checking: ~$0.35

**Cost reduction tips:**
1. Use `--no-validation` for sourcepull-only runs
2. Process specific footnotes with `--footnotes`
3. Set up vector store for better caching
4. Use `DETERMINISTIC_CHECKS_ONLY=True` in config

## Next Steps

### 1. Run Tests

```bash
python tests/test_r1_validation.py
```

### 2. Review Documentation

- `R1_CITE_CHECKING_README.md` - Full documentation
- `R1_CITE_CHECKING_INTEGRATION_PLAN.md` - Design details
- `WORKFLOW.md` - Workflow guide

### 3. Customize Configuration

Edit `config/validation_settings.py`:

```python
# Enable/disable features
ENABLE_CITATION_VALIDATION = True
ENABLE_QUOTE_VERIFICATION = True
ENABLE_SUPPORT_CHECKING = False  # Optional

# Validation mode
VALIDATION_MODE = "strict"  # or "lenient"

# Confidence thresholds
CONFIDENCE_THRESHOLD = 0.85
AUTO_APPROVE_HIGH_CONFIDENCE = True
```

### 4. Integrate with Existing Workflow

The R1 system integrates seamlessly with existing SLRinator workflows.

## Support

**Having issues?**

1. Check this quickstart guide
2. Review `R1_CITE_CHECKING_README.md`
3. Run `python setup_r1.py` again
4. Check test suite: `python tests/test_r1_validation.py`
5. Review examples: `python examples/r1_basic_example.py`

**Need help?**
Contact the Stanford Law Review editorial team.

## Summary

```bash
# 1. Setup
python setup_r1.py

# 2. Configure API key
nano config/api_keys.json

# 3. (Optional) Setup vector store
python setup_vector_store.py

# 4. Run R1 workflow
python r1_workflow.py your_article.docx --footnotes 1-50

# 5. Review reports
open output/r1_validation/r1_validation_report_*.html
```

That's it! You're now running production-ready R1 cite checking with full Bluebook/Redbook compliance.
