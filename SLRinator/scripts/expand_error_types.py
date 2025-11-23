#!/usr/bin/env python3
"""
Expand error types to ensure comprehensive coverage (250+ error types)
"""

import json
from pathlib import Path

analysis_path = Path("/home/user/slr/SLRinator/output/analysis/redbook_ALL_115_RULES_FIXED.json")

with open(analysis_path, 'r') as f:
    analysis = json.load(f)

# Add additional error types to key rules for comprehensive coverage
additional_errors = {
    "1.1": [
        {"id": "RB_1.1_E4", "name": "nested_quote_depth_excessive", "description": "Quote with multiple levels of nesting not properly attributed", "severity": "error", "auto_fix": "no"},
        {"id": "RB_1.1_E5", "name": "quoting_source_mismatch", "description": "Quoting parenthetical source doesn't match actual nested quote source", "severity": "error", "auto_fix": "no"}
    ],
    "1.2": [
        {"id": "RB_1.2_E5", "name": "identifying_vs_supporting_ambiguity", "description": "Unclear whether citation identifies or supports proposition", "severity": "warning", "auto_fix": "no"}
    ],
    "1.3": [
        {"id": "RB_1.3_E4", "name": "case_name_form_ambiguity", "description": "Ambiguous whether text case name is sufficient for citation type", "severity": "warning", "auto_fix": "no"}
    ],
    "1.4": [
        {"id": "RB_1.4_E3", "name": "partial_support_unclear", "description": "Unclear which portion of sentence citation supports", "severity": "warning", "auto_fix": "no"}
    ],
    "1.5": [
        {"id": "RB_1.5_E3", "name": "compare_sources_ordering", "description": "Sources in compare/with not properly ordered", "severity": "warning", "auto_fix": "no"}
    ],
    "1.6": [
        {"id": "RB_1.6_E3", "name": "verb_signal_multiple_types", "description": "Mixed signal types incorrectly used as verbs in same sentence", "severity": "error", "auto_fix": "no"}
    ],
    "1.7": [
        {"id": "RB_1.7_E3", "name": "citation_chain_too_deep", "description": "Citation through multiple layers creates reader confusion", "severity": "warning", "auto_fix": "no"}
    ],
    "1.8": [
        {"id": "RB_1.8_E3", "name": "preferred_source_unavailable", "description": "Preferred source exists but quote not found in it", "severity": "error", "auto_fix": "no"}
    ],
    "1.10": [
        {"id": "RB_1.10_E3", "name": "parenthetical_substance_vs_length", "description": "Parenthetical short but still too complex for clarity", "severity": "info", "auto_fix": "no"}
    ],
    "1.11": [
        {"id": "RB_1.11_E6", "name": "participial_phrase_ambiguous", "description": "Present participle could modify multiple subjects", "severity": "warning", "auto_fix": "no"},
        {"id": "RB_1.11_E7", "name": "quote_fragment_improper", "description": "Quoted fragment improperly punctuated in parenthetical", "severity": "error", "auto_fix": "manual"}
    ],
    "1.13": [
        {"id": "RB_1.13_E4", "name": "multiple_alteration_types", "description": "Multiple types of alterations not properly consolidated", "severity": "warning", "auto_fix": "yes"}
    ],
    "1.14": [
        {"id": "RB_1.14_E3", "name": "original_emphasis_unclear", "description": "Unclear whether emphasis in original or added", "severity": "warning", "auto_fix": "no"}
    ],
    "1.15": [
        {"id": "RB_1.15_E3", "name": "in_citation_ambiguous_referent", "description": "Unclear whether parenthetical refers to source or collection", "severity": "warning", "auto_fix": "no"}
    ],
    "1.16": [
        {"id": "RB_1.16_E2", "name": "parenthetical_ordering_multiple_errors", "description": "Multiple parenthetical ordering violations in single citation", "severity": "error", "auto_fix": "manual"}
    ],
    "2.1": [
        {"id": "RB_2.1_E3", "name": "underline_vs_italic_inconsistent", "description": "Underlining and italics mixed inconsistently", "severity": "warning", "auto_fix": "yes"}
    ],
    "2.2": [
        {"id": "RB_2.2_E3", "name": "bold_emphasis_inappropriate", "description": "Bold used for emphasis outside permitted circumstances", "severity": "error", "auto_fix": "yes"}
    ],
    "2.3": [
        {"id": "RB_2.3_E3", "name": "punctuation_italicization_inconsistent", "description": "Punctuation italicization not consistently applied", "severity": "warning", "auto_fix": "yes"}
    ],
    "3.6": [
        {"id": "RB_3.6_E3", "name": "pincite_precision_insufficient", "description": "Pincite not precise enough for quoted material", "severity": "warning", "auto_fix": "no"},
        {"id": "RB_3.6_E4", "name": "pincite_range_inappropriate", "description": "Pincite range used when specific page required", "severity": "error", "auto_fix": "no"}
    ],
    "4.1": [
        {"id": "RB_4.1_E3", "name": "id_five_footnote_boundary", "description": "Id. used at exactly 5-footnote boundary (ambiguous)", "severity": "warning", "auto_fix": "no"},
        {"id": "RB_4.1_E4", "name": "id_vs_supra_choice_unclear", "description": "Unclear whether id. or supra more appropriate", "severity": "info", "auto_fix": "no"}
    ],
    "4.2": [
        {"id": "RB_4.2_E3", "name": "id_at_missing", "description": "Pincite given with id. but 'at' omitted", "severity": "error", "auto_fix": "yes"}
    ],
    "4.4": [
        {"id": "RB_4.4_E3", "name": "hereinafter_overused", "description": "Hereinafter used when simple supra would suffice", "severity": "warning", "auto_fix": "no"},
        {"id": "RB_4.4_E4", "name": "hereinafter_designation_unclear", "description": "Hereinafter designation too similar to other sources", "severity": "error", "auto_fix": "no"}
    ],
    "5.2": [
        {"id": "RB_5.2_E3", "name": "block_quote_unnecessary", "description": "Block quote used for less than 50 words", "severity": "info", "auto_fix": "no"},
        {"id": "RB_5.2_E4", "name": "block_quote_avoided_improperly", "description": "Block quote avoided by improper truncation", "severity": "warning", "auto_fix": "no"}
    ],
    "5.3": [
        {"id": "RB_5.3_E3", "name": "ellipsis_spacing_incorrect", "description": "Ellipsis spacing not properly formatted", "severity": "error", "auto_fix": "yes"},
        {"id": "RB_5.3_E4", "name": "ellipsis_changes_meaning", "description": "Omission via ellipsis alters quote meaning", "severity": "error", "auto_fix": "no"}
    ],
    "5.4": [
        {"id": "RB_5.4_E3", "name": "bracket_alteration_unclear", "description": "Bracketed alteration doesn't clearly show change", "severity": "warning", "auto_fix": "manual"},
        {"id": "RB_5.4_E4", "name": "sic_overused", "description": "[sic] used for acceptable alternate spelling", "severity": "info", "auto_fix": "yes"}
    ],
    "10.1": [
        {"id": "RB_10.1_E3", "name": "case_good_law_not_verified", "description": "Case good law status not verified during citechecking", "severity": "error", "auto_fix": "no"},
        {"id": "RB_10.1_E4", "name": "negative_treatment_not_noted", "description": "Case has negative treatment not reflected in citation", "severity": "error", "auto_fix": "no"}
    ],
    "10.9": [
        {"id": "RB_10.9_E3", "name": "five_footnote_rule_violated", "description": "Short form used outside 5-footnote window", "severity": "error", "auto_fix": "no"},
        {"id": "RB_10.9_E4", "name": "short_form_ambiguous_referent", "description": "Short form could refer to multiple cases", "severity": "error", "auto_fix": "no"}
    ],
    "12.1": [
        {"id": "RB_12.1_E3", "name": "usc_edition_not_current", "description": "U.S.C. edition cited not current published version", "severity": "error", "auto_fix": "manual"},
        {"id": "RB_12.1_E4", "name": "supplement_needed_not_cited", "description": "Statute amended in supplement but supplement not cited", "severity": "error", "auto_fix": "no"}
    ],
    "18.1": [
        {"id": "RB_18.1_E3", "name": "url_not_permanent", "description": "URL not permanent/archived link", "severity": "warning", "auto_fix": "no"},
        {"id": "RB_18.1_E4", "name": "perma_cc_not_used", "description": "Perma.cc or archive.org not used for web source", "severity": "info", "auto_fix": "no"}
    ],
    "24.5": [
        {"id": "RB_24.5_E3", "name": "oxford_comma_omitted", "description": "Oxford comma omitted in list of 3+ items", "severity": "error", "auto_fix": "yes"},
        {"id": "RB_24.5_E4", "name": "comma_splice_error", "description": "Comma splice error in sentence", "severity": "error", "auto_fix": "manual"}
    ],
    "24.7": [
        {"id": "RB_24.7_E3", "name": "double_space_after_period", "description": "Two spaces after period instead of one", "severity": "error", "auto_fix": "yes"},
        {"id": "RB_24.7_E4", "name": "spacing_inconsistent_throughout", "description": "Spacing after punctuation inconsistent", "severity": "warning", "auto_fix": "yes"}
    ]
}

# Apply additional error types
for rule in analysis['rules']:
    rule_id = rule['id']
    if rule_id in additional_errors:
        rule['error_types'].extend(additional_errors[rule_id])

# Recalculate total
analysis['total_error_types'] = sum(len(r['error_types']) for r in analysis['rules'])

# Write output
with open(analysis_path, 'w') as f:
    json.dump(analysis, f, indent=2)

print(f"Expanded error types:")
print(f"- Total error types: {analysis['total_error_types']}")
print(f"- Enhanced {len(additional_errors)} rules with additional error types")
print(f"- Average error types per rule: {analysis['total_error_types'] / len(analysis['rules']):.1f}")
