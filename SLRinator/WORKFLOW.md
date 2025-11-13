# SLRinator Workflow Guide

## Quick Start

The SLRinator provides a complete workflow for Stanford Law Review sourcepull automation:

1. **Extract footnotes** from Word documents
2. **Parse citations** using GPT-5 (optional)
3. **Retrieve sources** automatically
4. **Generate reports** and spreadsheets

## Basic Usage

```bash
# Process entire document
python slrinator_workflow.py article.docx

# Process specific footnotes
python slrinator_workflow.py article.docx --footnotes 1-50

# Process without GPT (faster, less accurate)
python slrinator_workflow.py article.docx --no-gpt
```

## Setup

### 1. Configure API Keys

Edit `config/api_keys.json`:

```json
{
    "openai": {
        "api_key": "sk-...",  // For GPT-5 citation parsing
    },
    "courtlistener": {
        "token": "...",  // For federal/state cases
    },
    "govinfo": {
        "api_key": "..."  // For statutes/regulations
    }
}
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Workflow Steps

### Step 1: Footnote Extraction
- Reads Word document (.docx)
- Extracts all footnotes with numbering
- Filters by range if specified

### Step 2: Citation Parsing
- **With GPT-5**: Intelligent parsing of complex citations
  - Identifies citation types (case, statute, article, etc.)
  - Extracts structured data (parties, volumes, pages, etc.)
  - Handles signals (See, See also, Cf.)
  - Recognizes short forms (Id., supra)
  
- **Without GPT**: Basic regex parsing
  - Finds obvious patterns (U.S.C., v., etc.)
  - Less accurate but faster

### Step 3: Source Retrieval
- Attempts retrieval in priority order:
  1. Official sources (Supreme Court, GovInfo)
  2. Free databases (CourtListener, Justia)
  3. Premium databases (if configured)
- Names files systematically: `SP-001-PartyName.pdf`
- Logs all API usage for security

### Step 4: Report Generation
- Creates JSON report with statistics
- Generates CSV for Google Sheets import
- Lists sources requiring manual retrieval

## Output Structure

```
output/data/Sourcepull/
├── SP-001-Alice_v_CLS.pdf       # Retrieved PDFs
├── SP-002-35USC101.pdf
├── sourcepull_report.json       # Detailed report
├── sourcepull_spreadsheet.csv   # For Google Sheets
├── parsed_citations.json        # GPT parsing results
└── manual_retrieval_required.txt
```

## File Naming Convention

Files are named: `SP-XXX-ShortName.pdf`

- `SP` = Sourcepull prefix
- `XXX` = Three-digit source number
- `ShortName` = Abbreviated name from citation

Examples:
- `SP-001-Alice_v_CLS.pdf` (case)
- `SP-002-35USC101.pdf` (statute)
- `SP-003-Lemley.pdf` (article)

## CSV Format

The generated CSV includes:
- Source ID
- Footnote number
- Short name
- Full citation
- Type (case/statute/article/etc.)
- Status (✓ or ✗)
- File name (if retrieved)
- Date retrieved

## API Usage Logging

All API calls are logged to `output/logs/api_usage/`:
- Immutable append-only format
- Masked API keys for security
- Checksums for integrity
- Daily log rotation

## Troubleshooting

### No citations found
- Check footnote extraction worked
- Try with GPT-5 enabled for better parsing

### Low retrieval rate
- Verify API keys are configured
- Check API rate limits
- Some sources require manual retrieval

### GPT parsing fails
- Check OpenAI API key
- Verify API credits available
- Fall back to `--no-gpt` mode

## Advanced Options

```bash
# Custom output directory
python slrinator_workflow.py article.docx --output ~/Desktop/Sourcepull

# Custom config file
python slrinator_workflow.py article.docx --config my_keys.json

# Process multiple ranges
python slrinator_workflow.py article.docx --footnotes "1-50,100-150"
```

## Example Session

```bash
$ python slrinator_workflow.py SherkGugliuzza.docx --footnotes 1-50

======================================================================
                    SLRINATOR WORKFLOW
               Stanford Law Review Sourcepull
======================================================================

2025-08-08 23:49:05 - Starting SLRinator workflow...
2025-08-08 23:49:05 - Step 1: Extracting footnotes from document...
  Extracted 50 footnotes
2025-08-08 23:49:06 - Step 2: Parsing citations with GPT-5...
  Found 73 citations across 50 footnotes
2025-08-08 23:49:07 - Step 3: Running sourcepull...
  Processing SP-001: Alice Corp. v. CLS Bank...
    ✓ Retrieved and saved as: SP-001-Alice_v_CLS.pdf
  Processing SP-002: 35 U.S.C. § 101...
    ✗ Manual retrieval required
...
2025-08-08 23:49:45 - Step 4: Generating report...
✅ Workflow complete!

======================================================================
SUMMARY
======================================================================
Total Footnotes: 50
Total Citations: 73
Sources Retrieved: 28/73
Success Rate: 38.4%

Output Directory: output/data/Sourcepull
Report: output/data/Sourcepull/sourcepull_report.json
Spreadsheet: output/data/Sourcepull/sourcepull_spreadsheet.csv
```