# R2 Pipeline Project Status

**Last Updated:** 2025-10-29
**Status:** Operational with Vector Store Integration

## Overview

Automated legal citation checking pipeline (R2 - "Second Round") that validates citations from Word documents against PDF source materials using GPT-4o-mini and OpenAI's Bluebook vector store.

---

## Features Implemented

### ✅ Core Functionality
- **Word Document Processing**: Extracts footnotes with full formatting preservation (italic, bold, small caps)
- **PDF Analysis**: Extracts "redboxed" (annotated) text from R1 PDF source files
- **Citation Parsing**: Breaks down footnotes into individual citations
- **Proposition Extraction**: Extracts main text propositions associated with each footnote
- **Format Validation**: Checks citations against Bluebook rules using OpenAI Assistant with File Search
- **Support Verification**: Verifies if source material supports the proposition
- **R2 PDF Generation**: Creates annotated PDFs with clickable note icons (non-intrusive)
- **Excel Integration**: Updates master spreadsheet with results
- **Word Document Editing**: Applies corrections with track changes

### ✅ Vector Store Integration (NEW!)
- **Bluebook Assistant**: OpenAI Assistant with uploaded Bluebook.json (272KB) via File Search
- **Rule-Based Validation**: GPT searches Bluebook during validation for exact rule numbers
- **Per-Error Confidence**: Each violation includes individual confidence score (0.0-1.0)
- **Cached**: Assistant ID and vector store ID cached at `config/vector_store_cache.json`
- **Markdown Aware**: GPT understands markdown formatting notation (`*italic*`, `**bold**`, `[SC]small caps[/SC]`)

### ✅ Formatting Preservation
- **Markdown Notation**:
  - `*text*` = italic
  - `**text**` = bold
  - `[SC]text[/SC]` = small caps
- **Special Characters**: Preserves § (section symbol) and \xa0 (non-breaking space)
- **Whitepages Rule 10**: Case names NOT italicized per Whitepages style
- **Signals**: Latin terms like *see*, *supra*, *infra*, *id.* properly italicized

---

## Architecture

```
r2_pipeline/
├── main.py                          # Main orchestrator
├── config/
│   ├── settings.py                  # Configuration (API keys, paths)
│   └── vector_store_cache.json      # Cached assistant/vector store IDs
├── src/
│   ├── llm_interface.py             # GPT-4o-mini + Assistant with File Search
│   ├── vector_store_manager.py      # Manages Bluebook vector store
│   ├── markdown_utils.py            # Markdown formatting utilities
│   ├── pdf_processor.py             # PDF text & annotation extraction
│   ├── citation_parser.py           # Parse citations from footnotes
│   ├── citation_validator.py        # Bluebook format validation
│   ├── support_checker.py           # Proposition support verification
│   ├── quote_verifier.py            # Quote accuracy checking
│   ├── r2_generator.py              # Generate annotated R2 PDFs
│   ├── spreadsheet_updater.py       # Excel integration
│   └── word_editor.py               # Word document editing
├── prompts/
│   ├── citation_format.txt          # Citation validation prompt (markdown-aware)
│   └── support_check.txt            # Support verification prompt
├── scripts/
│   ├── setup_vector_store.py       # One-time Bluebook upload
│   └── test_vector_store.py        # Test vector store integration
└── data/
    ├── input/                       # (not used - files specified in settings)
    └── output/
        ├── r2_pdfs/                 # Generated R2 PDFs with note icons
        ├── logs/                    # Pipeline logs & CSV reports
        ├── reports/                 # HTML review queue
        └── Bersh_R2_Edited.docx     # Edited Word document

```

---

## Configuration

### Required Files
- **Word Document**: `/Users/ben/app/slrapp/78 SLR V2 R2 F/References/Bersh_PreR2.docx`
- **R1 PDFs**: `/Users/ben/app/slrapp/78 SLR V2 R2 F/78 SLR V2 R1/`
- **Spreadsheet**: `/Users/ben/app/slrapp/78 SLR V2 R2 F/References/V78.4 Bersh Master Sheet.xlsx`
- **Bluebook**: `/Users/ben/app/slrapp/Bluebook.json`
- **API Key**: `/Users/ben/app/slrapp/openaikey.txt`

### Environment
- **Python**: 3.x
- **Key Libraries**: python-docx, lxml, PyMuPDF (fitz), openai, openpyxl, tqdm, colorama
- **OpenAI Model**: gpt-4o-mini (cost-effective)
- **Assistant ID**: `asst_hcNme6KtVQ3TGpz0gZhYf465`
- **Vector Store ID**: `vs_690256ac5cd881918e52e5834e40f358`

---

## Usage

### Running the Pipeline
```bash
# Process specific footnotes
python3 main.py --footnotes 78 79 80

# Process all footnotes
python3 main.py
```

### First-Time Setup
```bash
# Upload Bluebook to OpenAI (one-time only)
python3 scripts/setup_vector_store.py
```

### Testing
```bash
# Test vector store integration
python3 scripts/test_vector_store.py
```

---

## Output Files

### Generated Files
1. **R2 PDFs** (`data/output/r2_pdfs/`):
   - Annotated with clickable note icon in top-right corner
   - Contains validation summary (format, support, quotes)

2. **CSV Report** (`data/output/logs/footnote_citations_formatted.csv`):
   - Columns: FN #, Cite #, Proposition Text, Footnote Text
   - Full formatting preserved with markdown notation

3. **JSON Log** (`data/output/logs/full_pipeline_log.json`):
   - Complete processing details
   - All validation results with confidence scores

4. **HTML Review Queue** (`data/output/reports/human_review_queue.html`):
   - Items flagged for human review
   - Shows support analysis and format issues

5. **Edited Word Document** (`data/output/Bersh_R2_Edited.docx`):
   - Track changes enabled
   - Corrected citations applied

---

## Key Fixes & Issues

### ✅ Fixed
1. **Word Footnote Extraction**: Used XML parsing with lxml (python-docx doesn't expose footnotes)
2. **PDF Redbox Extraction**: Extract ALL redboxed regions, increased tolerance to 20px
3. **Proposition Extraction**: Fixed off-by-one error - text between FN(N) and FN(N+1)
4. **MuPDF Errors**: Suppressed display errors with `fitz.TOOLS.mupdf_display_errors(False)`
5. **PDF Annotation**: Changed from large yellow box to small clickable note icon
6. **Vector Store Integration**: Implemented OpenAI Assistant API with File Search
7. **Markdown Awareness**: Updated prompt to teach GPT about markdown notation

### ⚠️ Known Issues
1. **Word Document Update Warnings**: Track changes text matching sometimes fails
2. **Spreadsheet Row Matching**: Can't find specific citation rows (warnings logged)
3. **Markdown Spacing (Ongoing)**: Some instances of `*supra *note` instead of `*supra* note`
   - Root cause: Word document has inconsistent formatting runs
   - Normalize function exists but may need refinement

---

## Citation Validation Output Format

```json
{
  "is_correct": false,
  "overall_confidence": 0.9,
  "errors": [
    {
      "error_type": "comma_missing",
      "description": "A comma is missing before 'at' in a supra citation.",
      "bluebook_rule": "4.2",
      "confidence": 0.9,
      "current": "Crusey, supra note 21 at 483",
      "correct": "Crusey, supra note 21, at 483"
    }
  ],
  "corrected_version": "Crusey, *supra* note 21, at 483...",
  "notes": "Additional observations"
}
```

---

## Cost & Performance

### Recent Run (Footnotes 78-80, 6 citations)
- **Total API Calls**: 12 (6 format validations + 6 support checks)
- **Total Tokens**: ~13,000
- **Estimated Cost**: $0.0026
- **Processing Time**: ~2 minutes
- **Success Rate**: 100%
- **Human Review Items**: 2

### Pricing (GPT-4o-mini)
- Input: $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- Assistant calls: Slightly higher due to vector search overhead

---

## Next Steps / Improvements

### Potential Enhancements
1. **Markdown Normalization**: Improve handling of inconsistent Word formatting runs
2. **Spreadsheet Matching**: Fix row matching logic for better Excel updates
3. **Quote Verification**: Currently basic - could be enhanced
4. **Parallel Processing**: Enable for faster processing of many citations
5. **Custom Bluebook Rules**: Add ability to override or extend rules
6. **Batch Processing**: Process multiple footnote ranges in one run

### User-Requested Features
- ✅ Vector store integration with Bluebook.json
- ✅ Per-error confidence scores
- ✅ Explicit Bluebook rule references
- ✅ Non-intrusive PDF annotations
- ✅ Markdown formatting preservation

---

## Development Notes

### Critical Implementation Details

1. **Footnote Extraction** (`main.py:72-144`):
   ```python
   # Access footnotes through XML (python-docx limitation workaround)
   for rel in doc_part.rels.values():
       if "footnotes" in rel.target_ref:
           footnotes_part = rel.target_part
           footnotes_xml = footnotes_part.blob
           root = etree.fromstring(footnotes_xml)
   ```

2. **Proposition Extraction** (`main.py:296-422`):
   ```python
   # CRITICAL: Text for FN N is between FN N and FN N+1 (not N-1 and N)
   next_fn_num = footnote_num + 1
   proposition = combined_text[current_fn_pos:next_fn_pos]
   ```

3. **Vector Store Integration** (`src/llm_interface.py:136-261`):
   ```python
   # Create thread, add message, run assistant, wait for completion
   thread = self.client.beta.threads.create()
   run = self.client.beta.threads.runs.create(
       thread_id=thread.id,
       assistant_id=self.assistant_id
   )
   ```

4. **Markdown Normalization** (`src/markdown_utils.py`):
   ```python
   # Move trailing spaces outside formatting markers
   text = re.sub(r'\*([^\*]+?)\s+\*', r'*\1* ', text)
   ```

---

## Contact & Support

**Pipeline Author**: Claude (Anthropic)
**Project**: SLR V78 R2 Automation
**Date Range**: August-October 2025

For issues or questions:
- Check `data/output/logs/pipeline.log` for detailed execution logs
- Review `data/output/reports/human_review_queue.html` for flagged items
- Run `python3 scripts/test_vector_store.py` to verify assistant functionality

---

## References

- **Bluebook**: The Bluebook: A Uniform System of Citation (21st ed.)
- **OpenAI Assistants API**: https://platform.openai.com/docs/assistants/overview
- **File Search Tool**: https://platform.openai.com/docs/assistants/tools/file-search
- **Python-docx**: https://python-docx.readthedocs.io/
- **PyMuPDF**: https://pymupdf.readthedocs.io/

---

*This document serves as a handoff for continuation of the project.*
