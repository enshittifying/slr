# Enhanced API Logging System - Complete

## Overview

Enhanced the API logging system to include detailed explanations for why each API call was made and comprehensive metadata about the retrieval process. Every API call now provides full context for debugging, auditing, and performance analysis.

## Enhanced Log Fields

### Core Fields (existing)
- `timestamp`: When the call was made
- `api_name`: Which API service was used
- `endpoint`: Specific API endpoint URL
- `method`: HTTP method (GET, POST, etc.)
- `response_code`: HTTP response code
- `success`: Whether the call succeeded
- `footnote_number`: Associated footnote
- `citation_preview`: Truncated citation text

### New Enhanced Fields
- `call_reason`: **WHY** this API call was made
- `expected_result`: What we expected to get from this call
- `citation_type`: Type of citation being retrieved (case, statute, etc.)
- `retrieval_strategy`: Current retrieval strategy being attempted
- `metadata`: Additional context about the call

## Example Enhanced Log Entries

### 1. GPT Citation Parsing

```json
{
  "timestamp": "2025-08-09T00:30:15.123456",
  "api_name": "openai_gpt5",
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "method": "POST",
  "response_code": 200,
  "success": true,
  "footnote_number": 23,
  "citation_preview": "Caraco Pharm. Lab'ys, Ltd. v. Novo Nordisk A/S, 566 U.S. 399, 415 (2012) (\"The statutory scheme...",
  "call_reason": "Parse footnote 23 to extract all citations and their metadata",
  "expected_result": "JSON with structured citations including types, case names, reporters, statute sections, etc.",
  "citation_type": "unknown_mixed",
  "retrieval_strategy": "gpt_parsing",
  "metadata": {
    "footnote_length": 287,
    "parsing_mode": "comprehensive",
    "legal_standards": "Bluebook/Redbook",
    "max_tokens": 2000,
    "citations_extracted": 3,
    "parsing_confidence": 0.95,
    "tokens_used": 456,
    "response_format": "structured_json",
    "gpt_reasoning_length": 145
  },
  "checksum": "a7b3d5f1c9e2"
}
```

### 2. Supreme Court PDF Retrieval

```json
{
  "timestamp": "2025-08-09T00:30:45.789012",
  "api_name": "supreme_court",
  "endpoint": "https://www.supremecourt.gov/opinions/boundvolumes/566bv.pdf",
  "method": "HEAD",
  "response_code": 200,
  "success": true,
  "footnote_number": 23,
  "citation_preview": "Caraco Pharm. Lab'ys, Ltd. v. Novo Nordisk A/S, 566 U.S. 399",
  "call_reason": "Check availability of Supreme Court bound volume 566 for case Caraco Pharm. Lab'ys, Ltd. v. Novo Nordisk A/S",
  "expected_result": "HTTP 200 if volume 566 PDF exists on supremecourt.gov",
  "citation_type": "case",
  "retrieval_strategy": "supreme_court_official",
  "metadata": {
    "volume_number": "566",
    "case_name": "Caraco Pharm. Lab'ys, Ltd. v. Novo Nordisk A/S",
    "page_number": "399",
    "source_priority": 1,
    "file_type_expected": "pdf",
    "estimated_size_mb": "10-50"
  },
  "checksum": "f2a8c5d3e7b1"
}
```

### 3. Supreme Court PDF Download

```json
{
  "timestamp": "2025-08-09T00:30:46.234567",
  "api_name": "supreme_court", 
  "endpoint": "https://www.supremecourt.gov/opinions/boundvolumes/566bv.pdf",
  "method": "GET",
  "response_code": 200,
  "success": true,
  "footnote_number": 23,
  "citation_preview": "Caraco Pharm. Lab'ys, Ltd. v. Novo Nordisk A/S, 566 U.S. 399",
  "call_reason": "Download Supreme Court bound volume 566 containing case Caraco Pharm. Lab'ys, Ltd. v. Novo Nordisk A/S",
  "expected_result": "Complete bound volume PDF for volume 566",
  "citation_type": "case",
  "retrieval_strategy": "supreme_court_official",
  "metadata": {
    "file_size_bytes": 15728640,
    "file_size_mb": 15.0,
    "pdf_pages": 652,
    "validation_status": "valid_pdf",
    "download_success": true,
    "file_saved_as": "/path/to/fn23_1_SCOTUS_Vol566.pdf"
  },
  "checksum": "b9e4f1a6c8d2"
}
```

### 4. CourtListener Search

```json
{
  "timestamp": "2025-08-09T00:31:02.456789",
  "api_name": "courtlistener",
  "endpoint": "https://www.courtlistener.com/api/rest/v3/search/",
  "method": "GET",
  "response_code": 200,
  "success": true,
  "footnote_number": 25,
  "citation_preview": "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208",
  "call_reason": "Search CourtListener for case Alice Corp. v. CLS Bank Int'l to find PDF download link",
  "expected_result": "JSON with search results containing case opinions and PDF download URLs",
  "citation_type": "case",
  "retrieval_strategy": "courtlistener_pdf",
  "parameters": {
    "q": "Alice Corp CLS Bank",
    "type": "o",
    "order_by": "score desc"
  },
  "metadata": {
    "search_query": "Alice Corp. v. CLS Bank Int'l",
    "search_type": "opinions",
    "api_version": "v3",
    "expected_results": "1-10 case matches",
    "source_priority": 2,
    "free_api": true,
    "results_found": 5,
    "top_match_score": 0.95
  },
  "checksum": "d3c7e5a2f8b6"
}
```

### 5. Failed API Call

```json
{
  "timestamp": "2025-08-09T00:31:30.987654",
  "api_name": "govinfo",
  "endpoint": "https://api.govinfo.gov/collections/USCODE",
  "method": "GET",
  "response_code": 500,
  "success": false,
  "error": "Internal server error",
  "footnote_number": 18,
  "citation_preview": "35 U.S.C. § 271(b)",
  "call_reason": "Retrieve U.S. Code title 35 section 271 from official GovInfo database",
  "expected_result": "PDF or metadata for 35 U.S.C. § 271 from official government source",
  "citation_type": "statute",
  "retrieval_strategy": "govinfo_pdf",
  "metadata": {
    "title_requested": "35",
    "section_requested": "271",
    "subsection_requested": "b",
    "error_type": "HTTPError",
    "failure_point": "api_response",
    "retry_eligible": true,
    "next_fallback": "cornell_lii"
  },
  "checksum": "e8f2a9b5c1d7"
}
```

## Benefits of Enhanced Logging

### 1. **Debugging & Troubleshooting**
- **Why calls fail**: Clear reasons and expected results
- **Context preservation**: Full retrieval strategy context
- **Error classification**: Detailed error metadata

### 2. **Performance Analysis** 
- **Token usage tracking**: Monitor GPT API costs
- **File size monitoring**: Track download sizes
- **Response time analysis**: Identify slow sources

### 3. **Audit Trail**
- **Decision reasoning**: Why each source was tried
- **Strategy tracking**: Which retrieval path was followed
- **Success metrics**: Detailed success/failure context

### 4. **Cost Optimization**
- **API usage patterns**: Which APIs are most/least effective
- **Token consumption**: Optimize GPT prompts
- **Bandwidth usage**: Monitor large file downloads

## Log Analysis Examples

### Success Rate by Source
```bash
# Analyze which sources work best
grep '"success": true' api_usage.log | grep '"api_name"' | sort | uniq -c
# Example output:
#   45 "api_name": "cornell_lii"
#   23 "api_name": "supreme_court"
#   12 "api_name": "courtlistener"
#    3 "api_name": "govinfo"
```

### GPT Token Usage
```bash
# Track GPT costs
grep 'tokens_used' api_usage.log | jq -r '.metadata.tokens_used' | awk '{sum+=$1} END {print "Total tokens:", sum}'
```

### Failed Retrievals by Reason
```bash
# Understand failure patterns
grep '"success": false' api_usage.log | jq -r '.call_reason' | sort | uniq -c
```

## Implementation

### Enhanced Logger Usage
```python
from src.utils.api_logger import log_api_usage

log_api_usage(
    api_name="openai_gpt5",
    endpoint="https://api.openai.com/v1/chat/completions",
    method="POST",
    response_code=200,
    success=True,
    footnote_number=23,
    citation_text="Case citation...",
    call_reason="Parse footnote to extract structured citations",
    expected_result="JSON with citation metadata",
    citation_type="case",
    retrieval_strategy="gpt_parsing",
    additional_metadata={
        "tokens_used": 456,
        "parsing_confidence": 0.95,
        "citations_found": 3
    }
)
```

## Security Features Maintained

- ✅ **API key masking**: Sensitive data still masked
- ✅ **File locking**: Concurrent access protection
- ✅ **Checksums**: Data integrity verification
- ✅ **Append-only**: Immutable audit trail
- ✅ **Daily rotation**: Automatic log file management

## Log File Structure

```
output/logs/api_usage/
├── api_usage_20250809.log     # Today's enhanced logs
├── api_usage_20250808.log     # Previous days
└── api_usage_20250807.log
```

Each log entry is now a comprehensive record that explains not just what happened, but **why it happened** and **what we expected to achieve**. This makes debugging, performance optimization, and system understanding dramatically easier.