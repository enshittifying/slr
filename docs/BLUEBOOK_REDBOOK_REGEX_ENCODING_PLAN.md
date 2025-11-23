# Bluebook & Redbook Regex Encoding System - Implementation Plan

## Executive Summary

This document outlines the plan to systematically encode all Bluebook (21st ed.) and Redbook rules as regex patterns, enabling:
1. **Fast, deterministic validation** of citation formats
2. **Fallback mechanism** when LLM APIs are unavailable/rate-limited
3. **Pre-validation** to catch obvious errors before expensive LLM calls
4. **Confidence scoring** for LLM validation results

---

## Current State

### What We Have:
- **comprehensive_bluebook_rules.json** (2.4MB) - Complete Bluebook rules in JSON format
- **bluebook_rules_analysis.json** (165KB) - Analysis of rule structure
- **SLRinator extraction tools** - Web scrapers for Bluebook online
- **LLM-based validation** - OpenAI/Anthropic format checking (app/data/llm_client.py)

### Limitations:
- JSON rules are descriptive, not executable
- No deterministic validation possible
- Fully dependent on LLM APIs (cost, latency, rate limits)
- No granular confidence scoring

---

## Architecture

### Three-Tier Validation System

```
Citation Input
     │
     ├──> Tier 1: Regex Pre-validation (Fast, Deterministic)
     │    ├─ Catches obvious format errors
     │    ├─ Validates basic structure
     │    └─ Confidence: 60-80%
     │
     ├──> Tier 2: LLM Validation (Slow, Intelligent)
     │    ├─ Checks complex rules
     │    ├─ Validates context and exceptions
     │    └─ Confidence: 85-95%
     │
     └──> Tier 3: Hybrid Scoring (Best of Both)
          ├─ Combines regex + LLM results
          ├─ Higher confidence when both agree
          └─ Confidence: 90-99%
```

---

## Rule Categories

### 1. **Case Citations** (Bluebook Rule 10)

#### Pattern Classes:
```python
CASE_PATTERNS = {
    'federal_supreme_court': {
        'pattern': r'(.+?v\.\s+.+?),\s+(\d+)\s+U\.S\.\s+(\d+)\s+\((\d{4})\)',
        'groups': ['case_name', 'volume', 'page', 'year'],
        'confidence': 95,
        'examples': [
            'Roe v. Wade, 410 U.S. 113 (1973)',
            'Brown v. Board of Ed., 347 U.S. 483 (1954)'
        ]
    },
    'federal_circuit': {
        'pattern': r'(.+?v\.\s+.+?),\s+(\d+)\s+F\.\s*(\d+d|3d|2d|App\'x)\s+(\d+)\s+\((\w+\.\s+Cir\.\s+\d{4})\)',
        'groups': ['case_name', 'volume', 'reporter', 'page', 'court_year'],
        'confidence': 90,
        'examples': [
            'Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)',
            'Alice Corp. v. CLS Bank, 573 F.3d 208 (Fed. Cir. 2014)'
        ]
    },
    'federal_district': {
        'pattern': r'(.+?v\.\s+.+?),\s+(\d+)\s+F\.\s*Supp\.\s*(\d+d|2d|3d)?\s+(\d+)\s+\(([NSWE]\.D\.|[NSWE]\.\s+&\s+[NSWE]\.D\.)\s+\w+\.\s+\d{4}\)',
        'groups': ['case_name', 'volume', 'reporter_series', 'page', 'court_year'],
        'confidence': 88,
        'examples': [
            'Doe v. Roe, 789 F. Supp. 2d 123 (S.D.N.Y. 2015)'
        ]
    },
    'state_official': {
        'pattern': r'(.+?v\.\s+.+?),\s+(\d+)\s+(\w+\.(?:\s+\w+\.)?)\s+(\d+)\s+\((\w+\.?\s+\d{4})\)',
        'groups': ['case_name', 'volume', 'reporter', 'page', 'court_year'],
        'confidence': 85,
        'examples': [
            'People v. Smith, 123 Cal. 4th 456 (2020)',
            'State v. Jones, 789 N.Y.S.2d 123 (App. Div. 2019)'
        ]
    }
}
```

### 2. **Statutory Citations** (Bluebook Rule 12)

```python
STATUTE_PATTERNS = {
    'usc': {
        'pattern': r'(\d+)\s+U\.S\.C\.\s+§+\s*(\d+(?:[a-z])?(?:\(\w+\))?)',
        'groups': ['title', 'section'],
        'confidence': 98,
        'examples': [
            '42 U.S.C. § 1983',
            '35 U.S.C. § 101(a)(1)'
        ]
    },
    'state_code': {
        'pattern': r'(\w+\.(?:\s+\w+\.)*)\s+§+\s*(\d+(?:\.\d+)*(?:[a-z])?)',
        'groups': ['code', 'section'],
        'confidence': 92,
        'examples': [
            'Cal. Civ. Code § 1542',
            'N.Y. Penal Law § 125.25'
        ]
    }
}
```

### 3. **Law Review Articles** (Bluebook Rule 16)

```python
ARTICLE_PATTERNS = {
    'consecutively_paginated': {
        'pattern': r'(.+?),\s+(.+?),\s+(\d+)\s+(.+?)\s+(\d+)(?:,\s+(\d+))?\s+\((\d{4})\)',
        'groups': ['author', 'title', 'volume', 'journal', 'page', 'pinpoint', 'year'],
        'confidence': 93,
        'examples': [
            'John Doe, Patent Law Reform, 100 Harv. L. Rev. 123, 145 (2020)'
        ]
    },
    'nonconsecutively_paginated': {
        'pattern': r'(.+?),\s+(.+?),\s+(.+?),\s+(\w+\.\s+\d+,\s+\d{4}),\s+at\s+(\d+)',
        'groups': ['author', 'title', 'journal', 'date', 'page'],
        'confidence': 90,
        'examples': [
            'Jane Smith, AI Ethics, Tech. Rev., May 2023, at 45'
        ]
    }
}
```

### 4. **Books** (Bluebook Rule 15)

```python
BOOK_PATTERNS = {
    'standard': {
        'pattern': r'(.+?),\s+(.+?)\s+(\d+)\s+\((?:(\d+)(?:st|nd|rd|th)\s+ed\.\s+)?(\d{4})\)',
        'groups': ['author', 'title', 'page', 'edition', 'year'],
        'confidence': 91,
        'examples': [
            'Richard Posner, Economic Analysis of Law 123 (9th ed. 2014)',
            'William Blackstone, Commentaries on the Laws of England 45 (1765)'
        ]
    }
}
```

---

## Implementation Plan

### Phase 1: Rule Extraction (Weeks 1-2)

**Goal:** Convert JSON rules to executable regex patterns

**Tasks:**
1. Create `bluebook_regex_encoder.py` - main encoding engine
2. Parse `comprehensive_bluebook_rules.json`
3. For each rule category:
   - Extract pattern structure
   - Identify required/optional components
   - Build regex with named groups
   - Add confidence scoring
   - Add test examples

**Output:**
```python
# app/resources/bluebook_patterns.py
BLUEBOOK_PATTERNS = {
    'cases': {...},
    'statutes': {...},
    'articles': {...},
    'books': {...},
    # ... all 20+ categories
}
```

### Phase 2: Validation Engine (Weeks 3-4)

**Goal:** Build fast regex validation system

**Tasks:**
1. Create `app/core/regex_validator.py`:
   ```python
   class RegexCitationValidator:
       def __init__(self):
           self.patterns = load_bluebook_patterns()

       def validate(self, citation: str) -> ValidationResult:
           """
           Try to match citation against all patterns
           Returns: match confidence, matched pattern, extracted components
           """
           for category, patterns in self.patterns.items():
               for pattern_name, pattern_info in patterns.items():
                   match = re.match(pattern_info['pattern'], citation)
                   if match:
                       return ValidationResult(
                           matched=True,
                           category=category,
                           pattern=pattern_name,
                           confidence=pattern_info['confidence'],
                           components=match.groupdict(),
                           issues=self._check_component_rules(match.groupdict())
                       )
           return ValidationResult(matched=False, confidence=0)

       def _check_component_rules(self, components: dict) -> List[str]:
           """Check specific rules for each component"""
           issues = []

           # Example: Case name should be italicized
           if 'case_name' in components:
               if not self._check_italicization(components['case_name']):
                   issues.append("Case name should be italicized")

           # Example: Year should be 4 digits
           if 'year' in components:
               if not re.match(r'\d{4}', components['year']):
                   issues.append("Year should be 4 digits")

           return issues
   ```

2. Integrate with R2 Pipeline:
   ```python
   # In app/core/r2_pipeline.py
   def validate_citation(self, citation: str):
       # Try regex first (fast)
       regex_result = self.regex_validator.validate(citation)

       if regex_result.confidence >= 85:
           # High confidence - may skip LLM
           return regex_result

       # Low confidence or no match - use LLM
       llm_result = self.llm.check_format(citation, ...)

       # Combine results for hybrid confidence
       return self._combine_results(regex_result, llm_result)
   ```

### Phase 3: Redbook Rules (Weeks 5-6)

**Goal:** Add Stanford Law Review-specific rules (Redbook)

**Source:** `reference_files/redbook_processed/`

**Special Rules:**
```python
REDBOOK_PATTERNS = {
    'slr_case_citation': {
        # SLR requires full case names, no "et al."
        'pattern': r'(.+?v\.\s+.+?),\s+',  # No truncation allowed
        'slr_specific': True,
        'overrides': ['bluebook_case_truncation']
    },
    'slr_article_citation': {
        # SLR requires author's full first name
        'pattern': r'([A-Z][a-z]+\s+(?:[A-Z]\.\s+)?[A-Z][a-z]+),',
        'slr_specific': True
    }
}
```

### Phase 4: Testing & Validation (Weeks 7-8)

**Goal:** Ensure 95%+ accuracy

**Test Suite:**
```python
# tests/test_regex_validator.py
def test_supreme_court_cases():
    validator = RegexCitationValidator()

    # Positive cases
    assert validator.validate("Roe v. Wade, 410 U.S. 113 (1973)").matched
    assert validator.validate("Brown v. Board of Ed., 347 U.S. 483 (1954)").confidence >= 90

    # Negative cases (should catch errors)
    result = validator.validate("Roe v Wade 410 U.S. 113 (1973)")  # Missing period
    assert len(result.issues) > 0
    assert "missing period" in result.issues[0].lower()

def test_statute_citations():
    validator = RegexCitationValidator()

    assert validator.validate("42 U.S.C. § 1983").matched
    assert validator.validate("35 U.S.C. § 101(a)").confidence >= 95

def test_edge_cases():
    validator = RegexCitationValidator()

    # Complex case names
    assert validator.validate("NLRB v. Jones & Laughlin Steel Corp., 301 U.S. 1 (1937)").matched

    # Multiple pinpoint citations
    assert validator.validate("Smith, supra note 12, at 45, 67").matched

    # Signals
    assert validator.validate("See generally Brown v. Board of Ed., 347 U.S. 483").matched
```

**Validation Dataset:**
- 1000+ real SLR citations from past volumes
- Edge cases from Bluebook examples
- Common errors to detect

---

## Performance Optimization

### Compiled Regex Patterns

```python
import re
from functools import lru_cache

class CompiledPatterns:
    """Pre-compile all regex patterns for speed"""

    def __init__(self):
        self._patterns = {}
        self._compile_all()

    def _compile_all(self):
        for category, patterns in BLUEBOOK_PATTERNS.items():
            self._patterns[category] = {}
            for name, info in patterns.items():
                self._patterns[category][name] = {
                    'compiled': re.compile(info['pattern']),
                    'confidence': info['confidence'],
                    'groups': info['groups']
                }

    @lru_cache(maxsize=1000)
    def match(self, citation: str, category: str = None):
        """Cached pattern matching"""
        if category:
            categories = [category]
        else:
            categories = self._patterns.keys()

        for cat in categories:
            for name, pattern_info in self._patterns[cat].items():
                match = pattern_info['compiled'].match(citation)
                if match:
                    return cat, name, match, pattern_info['confidence']

        return None, None, None, 0
```

### Parallel Validation

```python
from concurrent.futures import ThreadPoolExecutor

def validate_citations_parallel(citations: List[str]) -> List[ValidationResult]:
    """Validate multiple citations in parallel"""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(validator.validate, cit) for cit in citations]
        return [f.result() for f in futures]
```

---

## Integration Points

### 1. R2 Pipeline Enhancement

```python
# app/core/r2_pipeline.py
class R2Pipeline:
    def __init__(self, ...):
        ...
        self.regex_validator = RegexCitationValidator()
        self.use_hybrid_validation = True

    def validate_citation(self, citation: str, ...) -> ValidationResult:
        # Step 1: Fast regex pre-check
        regex_result = self.regex_validator.validate(citation)

        if not self.use_hybrid_validation:
            return regex_result

        # Step 2: LLM validation if needed
        if regex_result.confidence < 85 or len(regex_result.issues) > 0:
            llm_result = self.llm.check_format(citation, ...)

            # Combine results
            return self._merge_results(regex_result, llm_result)

        return regex_result

    def _merge_results(self, regex_result, llm_result):
        """Merge regex and LLM results for higher confidence"""
        combined_issues = list(set(regex_result.issues + llm_result.get('issues', [])))

        # If both agree on no issues, higher confidence
        if not combined_issues:
            confidence = max(regex_result.confidence, 95)
        else:
            confidence = (regex_result.confidence + llm_result.get('confidence', 70)) / 2

        return ValidationResult(
            matched=True,
            confidence=confidence,
            issues=combined_issues,
            suggested_fix=llm_result.get('suggestion', ''),
            method='hybrid'
        )
```

### 2. Cost Optimization

```python
class SmartValidationRouter:
    """Route to regex or LLM based on citation complexity"""

    def validate(self, citation: str):
        # Try regex first (free, fast)
        regex_result = self.regex_validator.validate(citation)

        # Only use LLM for:
        # 1. Low regex confidence (<80%)
        # 2. Complex signals (e.g., "see generally; but see")
        # 3. Short form citations (Id., supra)
        if self._needs_llm(citation, regex_result):
            return self.llm_validate(citation)

        return regex_result

    def _needs_llm(self, citation, regex_result):
        if regex_result.confidence < 80:
            return True
        if any(signal in citation.lower() for signal in ['id.', 'supra', 'infra']):
            return True
        if ';' in citation:  # Multiple sources
            return True
        return False
```

---

## Success Metrics

### Accuracy Targets:
- **Regex-only validation**: 85-92% accuracy
- **LLM-only validation**: 93-98% accuracy
- **Hybrid validation**: 96-99% accuracy

### Performance Targets:
- **Regex validation**: <5ms per citation
- **LLM validation**: 500-2000ms per citation
- **Hybrid validation**: 200-800ms per citation (skips LLM when possible)

### Cost Reduction:
- **Current**: $0.001-0.005 per citation (all LLM)
- **With regex**: $0.0002-0.001 per citation (70% regex, 30% LLM)
- **Savings**: 60-80% reduction in API costs

---

## Deliverables

1. **bluebook_patterns.py** - All regex patterns
2. **redbook_patterns.py** - SLR-specific patterns
3. **regex_validator.py** - Validation engine
4. **pattern_compiler.py** - Performance optimization
5. **test_regex_patterns.py** - Comprehensive test suite
6. **PATTERN_REFERENCE.md** - Documentation for all patterns

---

## Timeline

- **Week 1-2**: Extract and encode Bluebook patterns
- **Week 3-4**: Build validation engine
- **Week 5-6**: Add Redbook rules
- **Week 7-8**: Testing and optimization
- **Week 9**: Integration with R2 pipeline
- **Week 10**: Performance tuning and documentation

**Total: 10 weeks to production-ready regex validation system**

---

## Future Enhancements

1. **Machine Learning Patterns**
   - Train on 10,000+ SLR citations
   - Learn common error patterns
   - Improve confidence scoring

2. **Rule Updates**
   - Monitor Bluebook errata
   - Auto-update from online sources
   - Version control for patterns

3. **Custom Rule Builder**
   - UI for editors to create custom patterns
   - Test pattern against citation corpus
   - Export as Python/JSON

---

**Status:** Planning Complete
**Next Step:** Begin Phase 1 implementation
**Owner:** SLR Development Team
