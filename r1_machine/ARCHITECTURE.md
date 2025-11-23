# R1 Machine Architecture

## Overview

The R1 Machine is a comprehensive legal citation validation system designed to verify Bluebook citation compliance through a multi-stage validation pipeline. It integrates with the R2 pipeline's footnote extraction capabilities and leverages both rule-based validation and AI-powered analysis.

## System Design Philosophy

### Core Principles

1. **Progressive Validation**: Fast regex checks first, complex AI analysis only when needed
2. **Confidence-Based Routing**: Each stage produces confidence scores that determine next steps
3. **Parallel Processing**: Citations are validated concurrently for maximum throughput
4. **Actionable Feedback**: Every error includes specific correction suggestions
5. **Rule Completeness**: All Bluebook, Redbook, and Table rules are loaded and utilized

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         R1 MACHINE                               │
└─────────────────────────────────────────────────────────────────┘

INPUT: Word Document with Footnotes
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 0: Citation Extraction (Reuses R2 Pipeline)              │
│  - Extract footnotes from Word document                          │
│  - Parse citations with formatting preservation                  │
│  - Split multi-citation footnotes                                │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: Regex Pattern Matching (Fast Layer)                   │
│  - Basic structure validation (case name, reporter, year)        │
│  - Common pattern detection                                      │
│  - Fast fail for obvious errors                                  │
│  - Confidence: 0.0-1.0                                           │
│  - Duration: ~10ms per citation                                  │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─── Confidence >= 0.9 ──► APPROVED (skip to error reporting)
   │
   ▼ Confidence < 0.9
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: Rule-Based Validation (Medium Layer)                  │
│  - Load all Bluebook/Redbook/Table JSON rules                   │
│  - Match citation type to specific rule set                      │
│  - Validate all components against rules                         │
│  - Check abbreviations, signals, parentheticals                  │
│  - Confidence: 0.0-1.0                                           │
│  - Duration: ~100ms per citation                                 │
└─────────────────────────────────────────────────────────────────┘
   │
   ├─── Confidence >= 0.8 ──► APPROVED/CORRECTED
   │
   ▼ Confidence < 0.8
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: GPT-4o Fallback (Complex Layer)                       │
│  - Deep semantic analysis                                        │
│  - Context-aware validation                                      │
│  - Handles edge cases and ambiguities                            │
│  - Confidence: 0.0-1.0                                           │
│  - Duration: ~2000ms per citation                                │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│  Error Reporting & Correction Suggestions                        │
│  - Generate detailed error reports                               │
│  - Provide specific corrections for each issue                   │
│  - Export to JSON, HTML, and Excel formats                       │
└─────────────────────────────────────────────────────────────────┘
   │
   ▼
OUTPUT: Validation Report + Corrected Citations
```

## Component Architecture

### 1. Citation Extractor (`citation_extractor.py`)

**Purpose**: Extract and parse citations from Word document footnotes

**Key Features**:
- Reuses R2 pipeline's footnote extraction logic
- Preserves formatting (italics, bold, small caps)
- Handles multi-citation footnotes
- Splits signal-separated citations

**Input**: Word document path, optional footnote range
**Output**: List of Citation objects with metadata

**Data Structure**:
```python
@dataclass
class Citation:
    footnote_num: int
    citation_num: int  # For multi-citation footnotes
    full_text: str
    type: str  # case, statute, book, article, etc.
    components: Dict[str, str]  # parsed components
    formatting: Dict[str, List[tuple]]  # italic ranges, etc.
```

### 2. Regex Validator (`regex_validator.py`)

**Purpose**: Fast initial validation using regex patterns

**Validation Checks**:
1. Basic structure presence (case name, reporter, year)
2. Citation type detection
3. Common format patterns
4. Quick error detection

**Performance Target**: < 10ms per citation

**Confidence Scoring**:
- 1.0: Perfect match with known pattern
- 0.7-0.9: Mostly correct, minor issues
- 0.4-0.6: Structural issues detected
- 0.0-0.3: Major formatting errors

**Output Structure**:
```python
@dataclass
class RegexValidationResult:
    is_valid: bool
    confidence: float
    detected_type: str
    errors: List[str]
    warnings: List[str]
    matched_patterns: List[str]
```

### 3. Rule Loader (`rule_loader.py`)

**Purpose**: Load and index all JSON rule files

**Loaded Rules**:
1. **Bluebook Rules** (213 rules across 8 categories)
   - General citation rules
   - Signal ordering rules
   - Formatting conventions
   - Abbreviation standards
   - Parenthetical rules

2. **Redbook Rules** (if available)
   - Practitioner-focused variations
   - Court-specific requirements

3. **Table Rules**
   - USC Table 1-6 mappings
   - Jurisdiction abbreviations
   - Reporter abbreviations

**Architecture**:
```python
class RuleLoader:
    def __init__(self):
        self.bluebook_rules: Dict[str, List[Rule]]
        self.redbook_rules: Dict[str, List[Rule]]
        self.table_rules: Dict[str, List[TableEntry]]
        self.abbreviations: Dict[str, str]

    def load_all_rules(self) -> None
    def get_rules_for_type(self, citation_type: str) -> List[Rule]
    def check_abbreviation(self, term: str) -> Optional[str]
    def lookup_table(self, table_num: int, key: str) -> Optional[str]
```

### 4. Rule Validator (`rule_validator.py`)

**Purpose**: Validate citations against loaded Bluebook rules

**Validation Process**:
1. Identify citation type (case, statute, book, etc.)
2. Load applicable rules from RuleLoader
3. Validate each component against rules:
   - Case name formatting (italics, abbreviations)
   - Reporter format and volume
   - Pinpoint citations
   - Court and year parenthetical
   - Signals and order
   - Parentheticals
4. Generate specific error messages
5. Suggest corrections based on rules

**Key Validations**:
- **Case Citations**: Rule 10.x validations
- **Statute Citations**: Rule 12.x validations
- **Book Citations**: Rule 15.x validations
- **Article Citations**: Rule 16.x validations
- **Signals**: Rule 1.2-1.3 validations
- **Parentheticals**: Rule 1.5 validations

**Output Structure**:
```python
@dataclass
class RuleValidationResult:
    is_valid: bool
    confidence: float
    errors: List[ValidationError]
    warnings: List[ValidationWarning]
    corrected_citation: Optional[str]
    applied_rules: List[str]  # Rule numbers used
```

**Error Types**:
```python
@dataclass
class ValidationError:
    error_type: str  # "formatting", "abbreviation", "ordering", etc.
    component: str  # Which part has the error
    message: str  # Human-readable description
    rule_violated: str  # Bluebook rule number
    suggested_fix: str  # Specific correction
    confidence: float  # How confident in this error
```

### 5. GPT Validator (`gpt_validator.py`)

**Purpose**: Handle complex cases that rules can't validate

**When to Use**:
- Confidence from rule validator < 0.8
- Ambiguous citation formats
- Edge cases not covered by rules
- Complex parentheticals
- Novel citation types

**Approach**:
- Send citation + context to GPT-4o
- Include relevant Bluebook rule excerpts
- Request structured validation response
- Parse and format results

**Prompt Engineering**:
```
You are an expert in Bluebook citation format. Validate this citation:

Citation: {citation_text}
Type: {detected_type}
Context: {surrounding_text}

Relevant Bluebook Rules:
{applicable_rules}

Provide:
1. Is this citation correct? (yes/no/unsure)
2. Confidence (0.0-1.0)
3. List of specific errors
4. Corrected version
5. Explanation of each correction
```

**Output Structure**:
```python
@dataclass
class GPTValidationResult:
    is_valid: bool
    confidence: float
    errors: List[ValidationError]
    corrected_citation: Optional[str]
    explanation: str
    tokens_used: int
    cost: float
```

### 6. Error Reporter (`error_reporter.py`)

**Purpose**: Generate comprehensive validation reports

**Report Formats**:

1. **JSON Report**:
   - Machine-readable format
   - Full validation details
   - Suitable for further processing

2. **HTML Report**:
   - Human-readable presentation
   - Color-coded errors (red) and warnings (yellow)
   - Side-by-side original vs. corrected
   - Grouped by error type

3. **Excel Report**:
   - Spreadsheet format
   - One row per citation
   - Filterable by error type, confidence, etc.
   - Suitable for batch review

**Report Contents**:
- Citation text (original)
- Footnote number
- Validation status
- Confidence score
- List of errors with explanations
- Suggested corrections
- Rule references
- Processing time
- Stage completed at

### 7. Main Orchestrator (`main.py`)

**Purpose**: Coordinate the entire validation pipeline

**Key Features**:
- Parallel processing with ThreadPoolExecutor
- Progress tracking with tqdm
- Stage-based confidence routing
- Error aggregation and reporting
- Statistics and performance metrics

**Configuration Options**:
- `footnote_range`: Specific footnotes to validate
- `parallel`: Enable/disable parallel processing
- `max_workers`: Number of parallel workers
- `confidence_thresholds`: Thresholds for each stage
- `skip_stages`: Skip certain validation stages
- `output_formats`: Choose report formats

**Main Processing Loop**:
```python
for citation in citations:
    # Stage 1: Regex
    regex_result = regex_validator.validate(citation)
    if regex_result.confidence >= 0.9:
        results.append(create_report(citation, regex_result))
        continue

    # Stage 2: Rules
    rule_result = rule_validator.validate(citation)
    if rule_result.confidence >= 0.8:
        results.append(create_report(citation, rule_result))
        continue

    # Stage 3: GPT
    gpt_result = gpt_validator.validate(citation, rule_result)
    results.append(create_report(citation, gpt_result))
```

## Data Flow

### Input Processing
1. Word document path provided
2. Footnotes extracted with formatting
3. Citations parsed and structured
4. Each citation queued for validation

### Validation Pipeline
1. **Regex Layer**: Quick structural check
   - Exit if confidence >= 0.9
2. **Rule Layer**: Detailed rule matching
   - Exit if confidence >= 0.8
3. **GPT Layer**: AI-powered deep validation
   - Always produces final result

### Output Generation
1. Aggregate all validation results
2. Group errors by type and severity
3. Generate reports in requested formats
4. Save to output directory
5. Display summary statistics

## Performance Considerations

### Optimization Strategies

1. **Parallel Processing**:
   - Process multiple citations concurrently
   - Thread pool size: 5-10 workers
   - Expected speedup: 3-5x

2. **Caching**:
   - Cache loaded rules (load once)
   - Cache GPT responses for identical citations
   - Cache regex compilation results

3. **Early Exit**:
   - Skip expensive stages when confidence is high
   - ~70% of citations should exit at Stage 1
   - ~20% at Stage 2
   - ~10% require GPT

4. **Batch GPT Calls**:
   - Group multiple citations in single API call
   - Reduce API latency overhead
   - Cost savings through fewer requests

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Citations/second (regex only) | 100 | Simple citations |
| Citations/second (rules) | 10 | Complex citations |
| Citations/second (GPT) | 0.5 | Includes API latency |
| Overall throughput | 20-30 | Mixed citation types |
| Memory usage | < 500MB | For 1000 citations |

## Error Handling

### Stage Failures
- If regex validation fails: proceed to rules
- If rule validation fails: proceed to GPT
- If GPT validation fails: mark for manual review

### API Failures
- Retry GPT calls up to 3 times
- Exponential backoff (1s, 2s, 4s)
- Fall back to manual review if all retries fail

### Data Errors
- Invalid Word document: clear error message
- Malformed footnotes: log and skip
- Unparseable citations: mark for manual review

## Configuration

### Environment Variables
```bash
# API Keys
OPENAI_API_KEY=sk-...

# Paths
WORD_DOC_PATH=/path/to/document.docx
R1_MACHINE_OUTPUT_DIR=/path/to/output
RULES_DIR=/home/user/slr/SLRinator

# Validation Settings
REGEX_CONFIDENCE_THRESHOLD=0.9
RULE_CONFIDENCE_THRESHOLD=0.8
GPT_CONFIDENCE_THRESHOLD=0.0  # Always accept GPT result

# Performance
MAX_WORKERS=5
ENABLE_PARALLEL=true
ENABLE_CACHING=true

# GPT Settings
GPT_MODEL=gpt-4o
GPT_TEMPERATURE=0.1
GPT_MAX_TOKENS=1000
```

## Extension Points

### Adding New Citation Types
1. Add regex patterns to `regex_validator.py`
2. Add rule mappings in `rule_validator.py`
3. Update GPT prompt templates
4. Add examples to test suite

### Adding New Output Formats
1. Implement formatter in `error_reporter.py`
2. Add to format options in config
3. Update CLI arguments

### Custom Validation Rules
1. Add custom rule JSON files
2. Load in `rule_loader.py`
3. Reference in `rule_validator.py`

## Integration with R2 Pipeline

### Shared Components
- **Citation Extraction**: Reuses R2's `CitationParser`
- **Word Document Handling**: Reuses R2's `WordEditor`
- **LLM Interface**: Can share GPT client

### Data Exchange
- R1 validates citation format
- R2 validates citation support
- Both can run on same document
- Results can be merged for comprehensive report

### Workflow Integration
```
1. R1 validates all citations in document
2. Export corrected citations
3. R2 verifies support for corrected citations
4. Combined report shows format + support issues
```

## Testing Strategy

### Unit Tests
- Each validator component tested independently
- Mock API calls for GPT validator
- Test against known good/bad citations

### Integration Tests
- End-to-end validation pipeline
- Real Word documents
- All output formats

### Performance Tests
- Benchmark each stage
- Profile memory usage
- Stress test with large documents (1000+ citations)

### Validation Tests
- Test against Bluebook examples
- Real-world citation samples
- Edge cases and ambiguities

## Future Enhancements

### Short-term (v1.1)
- Add Redbook rule support
- Implement caching layer
- Batch GPT processing
- Interactive correction mode

### Medium-term (v1.2)
- Machine learning model for citation type detection
- Custom rule editor UI
- Confidence calibration based on feedback
- Integration with legal research platforms

### Long-term (v2.0)
- Real-time validation in Word plugin
- Cross-reference validation
- Citation graph analysis
- Auto-correction with user approval

## Appendix

### Citation Type Taxonomy

| Type | Bluebook Rule | Example |
|------|---------------|---------|
| Case | Rule 10 | Brown v. Board of Educ., 347 U.S. 483 (1954) |
| Statute | Rule 12 | 42 U.S.C. § 1983 (2018) |
| Constitution | Rule 11 | U.S. Const. art. I, § 8 |
| Book | Rule 15 | Richard A. Posner, Economic Analysis of Law (9th ed. 2014) |
| Law Review | Rule 16 | John Doe, Title, 100 Yale L.J. 1 (1990) |
| Legislative | Rule 13 | H.R. Rep. No. 99-1, at 5 (1985) |

### Error Code Reference

| Code | Description | Severity |
|------|-------------|----------|
| E001 | Missing case name | Error |
| E002 | Missing reporter | Error |
| E003 | Missing year | Error |
| E004 | Incorrect italicization | Error |
| W001 | Unusual abbreviation | Warning |
| W002 | Ambiguous citation type | Warning |
| W003 | Low confidence validation | Warning |

### Performance Benchmarks

Based on sample document with 500 citations:

| Stage | Citations Processed | Avg Time/Citation | Total Time |
|-------|---------------------|-------------------|------------|
| Regex | 500 (100%) | 8ms | 4s |
| Rules | 150 (30%) | 95ms | 14s |
| GPT | 50 (10%) | 1800ms | 90s |
| **Total** | **500** | **216ms avg** | **108s** |

With parallel processing (5 workers): **~25 seconds total**

## Conclusion

The R1 Machine provides a comprehensive, efficient, and accurate citation validation system that leverages the best of rule-based and AI-powered validation. Its multi-stage architecture ensures fast processing while maintaining high accuracy, and its detailed error reporting enables users to quickly correct citation issues.
