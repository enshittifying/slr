# R1 Machine Cite Checking Integration Plan

## Executive Summary

This document outlines the plan to integrate R2-style cite checking capabilities into the R1 Machine (SLRinator), ensuring compliance with the Stanford Law Review Redbook and Member Handbook requirements.

## Current State Analysis

### R2 Pipeline Cite Checking Features
- **Citation Validation** (citation_validator.py)
  - Deterministic checks: curly quotes, non-breaking spaces, parenthetical capitalization
  - Rule retrieval from Bluebook.json (239 rules) and Redbook (115 rules)
  - LLM-powered validation using GPT-4o-mini with vector search
  - Evidence validation to ensure GPT cites actual rules

- **Support Checking** (support_checker.py)
  - Verifies if source text supports the proposition in main text
  - Uses LLM to analyze support level (yes/maybe/no)
  - Provides detailed reasoning and suggested actions

- **Quote Verification** (quote_verifier.py)
  - Character-by-character comparison
  - Bracket usage verification (alterations, [sic], etc.)
  - Ellipsis formatting checks (proper spacing)
  - Nested quote validation (single vs double quotes)
  - Deterministic accuracy scoring

### SLRinator (R1 Machine) Current Capabilities
- Footnote extraction from Word documents
- Citation parsing with GPT-5
- Multi-database source retrieval (CourtListener, GovInfo, HeinOnline, etc.)
- Basic Bluebook validation (~2784 lines across multiple files)
- PDF redboxing with intelligent highlighting
- Google Sheets integration
- Comprehensive report generation

### Gap Analysis
**Missing from R1:**
1. Comprehensive cite format validation during sourcepull
2. Support checking against retrieved sources
3. Quote accuracy verification
4. Integration with Redbook rules (115 rules)
5. Structured validation reporting
6. Human review queue for ambiguous citations

## Integration Architecture

### Phase 1: Core Module Creation

Create new module: `SLRinator/src/validation/`

```
SLRinator/src/validation/
├── __init__.py
├── citation_validator.py      # Adapted from R2
├── support_checker.py          # Adapted from R2
├── quote_verifier.py           # Adapted from R2
├── rule_retrieval.py           # Adapted from R2
├── llm_interface.py            # Shared LLM interface
└── validation_reporter.py      # Generate validation reports
```

### Phase 2: R2 Component Adaptation

**Step 1: Copy and Adapt R2 Validation Code**
- Copy R2 validation modules to SLRinator
- Update imports and paths
- Ensure compatibility with SLRinator's existing structure
- Add configuration for API keys (already exists in SLRinator/config/)

**Step 2: Rule Integration**
- Copy Bluebook.json from reference_files/ to SLRinator/config/
- Create comprehensive_rules.json combining Bluebook + Redbook
- Implement rule retrieval system matching R2's approach
- Add evidence validation to ensure AI cites real rules

**Step 3: LLM Interface Setup**
- Create unified LLM interface supporting:
  - GPT-4o-mini for validation (cost-effective)
  - GPT-5 for complex citation parsing (existing)
  - Vector search with Assistants API (optional)
- Implement cost tracking and API usage logging

### Phase 3: Workflow Integration

**Update: `SLRinator/slrinator_workflow.py`**

New workflow steps:
```
1. Extract footnotes (existing)
2. Parse citations with GPT-5 (existing)
3. ✨ NEW: Pre-retrieval validation
   - Check citation format
   - Flag obvious errors
   - Validate against Bluebook/Redbook
4. Retrieve sources (existing)
5. ✨ NEW: Post-retrieval validation
   - Verify quotes against source text
   - Check proposition support
   - Redbox validation elements
6. Generate comprehensive report (enhanced)
```

**Validation Checkpoints:**

```python
# Checkpoint 1: After citation parsing
for citation in parsed_citations:
    validation_result = citation_validator.validate_citation(
        citation=citation,
        position="footnote"  # or "middle", "end"
    )

    if not validation_result["validation"]["is_correct"]:
        # Flag for human review
        add_to_review_queue(citation, validation_result)

    # Store validation for report
    store_validation_result(citation, validation_result)

# Checkpoint 2: After source retrieval (if PDF retrieved)
if pdf_path and has_quotes:
    # Extract text from PDF
    source_text = extract_pdf_text(pdf_path)

    # Verify quotes
    quote_result = quote_verifier.verify_quote(
        quoted_text=extract_quotes(citation),
        source_text=source_text
    )

    # Check support (if main text available)
    if proposition:
        support_result = support_checker.check_support(
            proposition=proposition,
            source_text=source_text,
            citation_text=citation.full_text
        )
```

### Phase 4: Redbook & Handbook Compliance

**R1 Process Requirements (from r1_handbook_summary.md):**

**Sourcepull Phase:**
1. ✅ Find format-preserving source (existing in SLRinator)
2. ✅ Prepare redboxed PDF (existing in SLRinator)
3. ✅ File source to Google Drive (existing in SLRinator)
4. ✅ Log to spreadsheet (existing in SLRinator)
5. ✨ NEW: Validate citation format during logging
6. ✨ NEW: Flag quotes for verification

**Enhanced Redboxing:**
- Current: Redbox citation metadata (author, title, volume, page, year)
- ✨ NEW: Also redbox validation elements:
  - Quoted text passages
  - Supporting evidence for propositions
  - Any text cited in parentheticals
  - Use different colors:
    - Red: Citation metadata (existing)
    - Yellow: Quoted text
    - Green: Supporting evidence
    - Blue: Additional context

**Validation Rules Implementation:**

```python
# Redbook rules to implement
REDBOOK_RULES = {
    "24.4": "curly_quotes_check",           # Deterministic
    "24.8": "non_breaking_spaces_check",    # Deterministic
    "1.16": "parenthetical_capitalization", # Deterministic
    "10.2.1": "explanatory_parentheticals", # AI-assisted
    # ... all 115 Redbook rules
}

# Bluebook rules to implement
BLUEBOOK_RULES = {
    "10.2": "case_names",
    "10.3": "reporter_abbreviations",
    # ... all 239 Bluebook rules
}

# Priority: Redbook > Bluebook (as per R2's approach)
```

### Phase 5: Reporting & Human Review

**Enhanced Report Generation:**

```json
{
  "sourcepull_report": {
    "footnotes_processed": 50,
    "citations_found": 73,
    "sources_retrieved": 28,
    "success_rate": "38.4%",

    "validation_summary": {
      "citations_validated": 73,
      "citations_correct": 45,
      "citations_with_errors": 28,
      "quotes_verified": 12,
      "quotes_accurate": 10,
      "quotes_need_review": 2,
      "support_checks_performed": 15,
      "support_confirmed": 12,
      "support_questionable": 3
    },

    "citations": [
      {
        "citation_num": 1,
        "footnote_num": 1,
        "text": "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014)",
        "type": "case",
        "retrieval_status": "success",
        "pdf_path": "SP-001-Alice_v_CLS.pdf",

        "validation": {
          "format_check": {
            "is_correct": true,
            "errors": [],
            "confidence": 1.0
          },
          "quote_check": {
            "applicable": false
          },
          "support_check": {
            "applicable": false,
            "reason": "no_proposition_in_footnote"
          }
        }
      },
      {
        "citation_num": 2,
        "footnote_num": 2,
        "text": "John Doe, Patent Law, 100 HARV. L. REV. 123, 125 (2020) (\"patents are important\").",
        "type": "article",
        "retrieval_status": "success",
        "pdf_path": "SP-002-Doe.pdf",

        "validation": {
          "format_check": {
            "is_correct": false,
            "errors": [
              {
                "error_type": "curly_quotes_error",
                "rb_rule": "24.4",
                "description": "Use curly quotes instead of straight quotes",
                "current": "\"patents are important\"",
                "correct": ""patents are important""
              }
            ]
          },
          "quote_check": {
            "accurate": true,
            "confidence": 1.0,
            "issues": []
          },
          "support_check": {
            "applicable": false
          }
        },

        "needs_human_review": true,
        "review_reasons": ["citation_format_error"]
      }
    ],

    "human_review_queue": [
      {
        "citation_num": 2,
        "footnote_num": 2,
        "issue": "Citation format error",
        "severity": "minor",
        "details": "Curly quotes needed"
      }
    ]
  }
}
```

**Web UI for Human Review:**
- Copy R2's Flask-based review UI
- Adapt for R1 context (sourcepull + validation)
- Show validation errors alongside retrieval status
- Allow editors to:
  - Approve auto-corrections
  - Override validation decisions
  - Mark citations for further review
  - Export corrections to Word document

### Phase 6: Testing & Validation

**Test Suite:**
1. Unit tests for each validation component
2. Integration tests for full workflow
3. Test against actual SLR footnotes
4. Verify Redbook compliance
5. Verify Bluebook compliance
6. Performance testing (ensure < 5 sec per citation)

**Test Cases from Handbook:**
- Test all examples from Member Handbook Volume 78
- Test all Redbook rule examples
- Test edge cases (complex citations, nested quotes, etc.)

## Implementation Plan

### Sprint 1: Foundation (Days 1-3)
- [x] Analyze R2 pipeline
- [x] Analyze SLRinator capabilities
- [x] Create integration plan
- [ ] Create validation module structure
- [ ] Copy R2 components to SLRinator
- [ ] Update imports and paths

### Sprint 2: Core Integration (Days 4-7)
- [ ] Implement citation_validator.py
- [ ] Implement quote_verifier.py
- [ ] Implement support_checker.py
- [ ] Create rule retrieval system
- [ ] Integrate with Bluebook.json and Redbook

### Sprint 3: Workflow Updates (Days 8-10)
- [ ] Update slrinator_workflow.py
- [ ] Add pre-retrieval validation checkpoint
- [ ] Add post-retrieval validation checkpoint
- [ ] Implement enhanced redboxing
- [ ] Update report generation

### Sprint 4: Testing & Refinement (Days 11-14)
- [ ] Create test suite
- [ ] Test with actual SLR articles
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] Documentation updates

### Sprint 5: Human Review UI (Days 15-17)
- [ ] Adapt R2's Flask UI
- [ ] Add R1-specific features
- [ ] Test review workflow
- [ ] User acceptance testing

## Configuration Requirements

**New config files needed:**

1. `SLRinator/config/validation_settings.json`:
```json
{
  "enable_citation_validation": true,
  "enable_quote_verification": true,
  "enable_support_checking": false,  // Optional, requires main text
  "validation_mode": "strict",  // "strict" or "lenient"
  "llm_provider": "openai",
  "llm_model": "gpt-4o-mini",
  "use_vector_search": true,
  "max_retries": 5,
  "deterministic_checks_only": false
}
```

2. Update `SLRinator/config/api_keys.json`:
```json
{
  "openai": {
    "api_key": "sk-...",
    "assistant_id": "asst_..."  // For vector search
  }
}
```

## Success Metrics

1. **Accuracy**: 95%+ citation format validation accuracy
2. **Quote Verification**: 100% accuracy on character-by-character matching
3. **Performance**: < 5 seconds per citation validation
4. **Coverage**: All 115 Redbook + 239 Bluebook rules implemented
5. **Cost**: < $0.01 per citation for LLM calls
6. **User Satisfaction**: 90%+ of editors find validation helpful

## Risk Mitigation

**Risk 1: API Costs**
- Mitigation: Use GPT-4o-mini (cheaper), cache results, batch requests

**Risk 2: False Positives**
- Mitigation: Implement confidence thresholds, human review queue

**Risk 3: Performance**
- Mitigation: Parallel processing, async API calls, caching

**Risk 4: Complexity**
- Mitigation: Modular design, clear documentation, gradual rollout

## Future Enhancements

1. **Machine Learning**: Train custom model on SLR articles
2. **Auto-Correction**: Automatically fix common errors
3. **Context-Aware Validation**: Use surrounding text for better validation
4. **Integration with Word**: Direct validation in Word with tracked changes
5. **Real-time Validation**: As authors write, validate citations

## Conclusion

This integration will transform the R1 Machine from a pure sourcepull tool into a comprehensive cite checking system that:
- Retrieves sources (existing capability)
- Validates citation format (new)
- Verifies quotes (new)
- Checks support (new, optional)
- Generates detailed validation reports (enhanced)
- Queues issues for human review (new)

All while maintaining strict compliance with the Redbook and Member Handbook requirements.
