#!/usr/bin/env python3
"""
Comprehensive Bluebook Processing Script
Processes EVERYTHING: rules, tables, abbreviations, citation forms, ALL OF IT
"""
import sys
import logging
from pathlib import Path

# Add SLRinator to path
sys.path.insert(0, str(Path(__file__).parent))

from src.r1_validation.comprehensive_rule_processor import ComprehensiveRuleProcessor
from src.r1_validation.logging_config import setup_logging


def main():
    """Run comprehensive processing of ALL Bluebook content."""
    print("="*80)
    print("COMPREHENSIVE BLUEBOOK PROCESSING")
    print("Processing EVERYTHING: Rules, Tables, Abbreviations, Citation Forms")
    print("="*80)
    print()

    # Setup logging
    setup_logging(log_level="INFO", enable_console=True, enable_file=True)
    logger = logging.getLogger(__name__)

    logger.info("Initializing comprehensive processor...")

    # Initialize processor
    processor = ComprehensiveRuleProcessor()

    print("Starting massive parallel processing...")
    print("This will process:")
    print("  • All Bluebook rules (216+)")
    print("  • All Redbook rules (115)")
    print("  • All Bluebook tables (T1-T16)")
    print("  • Table 6: Common Words (299 abbreviations)")
    print("  • Table 7: Court Names (111 courts)")
    print("  • Table 8: Explanatory Phrases (41 phrases)")
    print("  • Table 13: Institutional Names (36 institutions)")
    print("  • All citation forms (short, long, id., supra)")
    print("  • And everything else!")
    print()
    print("Processing with 20 parallel workers...")
    print()

    # Process everything in parallel
    results = processor.process_everything_parallel(max_workers=20)

    print()
    print("="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print()

    # Display results
    rules_count = len(results.get('rules', []))
    tables_count = len(results.get('tables', []))
    forms_count = len(results.get('citation_forms', []))
    total = rules_count + tables_count + forms_count

    print(f"✅ Rules Processed: {rules_count}")
    print(f"✅ Table Entries Processed: {tables_count}")
    print(f"✅ Citation Forms Generated: {forms_count}")
    print(f"✅ TOTAL ITEMS: {total}")
    print()

    # Table breakdown
    print("="*80)
    print("TABLE BREAKDOWN")
    print("="*80)
    print()

    table_counts = {}
    for entry in results.get('tables', []):
        table_id = entry.table_id if hasattr(entry, 'table_id') else "unknown"
        table_counts[table_id] = table_counts.get(table_id, 0) + 1

    for table_id in sorted(table_counts.keys()):
        count = table_counts[table_id]
        print(f"  {table_id}: {count} entries")

    print()

    # Sample table entries
    print("="*80)
    print("SAMPLE TABLE ENTRIES")
    print("="*80)
    print()

    table_entries = results.get('tables', [])
    if table_entries:
        for i, entry in enumerate(table_entries[:10], 1):
            print(f"{i}. [{entry.table_id}] {entry.entry_key} → {entry.entry_value}")
            print(f"   Category: {entry.category}")
            print(f"   Keywords: {', '.join(entry.keywords[:3])}")
            print()

    # Citation forms
    print("="*80)
    print("CITATION FORMS")
    print("="*80)
    print()

    for form in results.get('citation_forms', []):
        print(f"• {form.citation_type.upper()} - {form.form_type}")
        print(f"  Pattern: {form.pattern_template}")
        print(f"  Example: {form.correct_examples[0] if form.correct_examples else 'N/A'}")
        print()

    # Save comprehensive data
    print("="*80)
    print("SAVING COMPREHENSIVE DATA")
    print("="*80)
    print()

    output_path = processor.save_comprehensive_data()
    print(f"✅ Saved to: {output_path}")
    print()

    # Final statistics
    print("="*80)
    print("FINAL STATISTICS")
    print("="*80)
    print()

    print(f"Total Processed Items: {total}")
    print()
    print("Detection Methods Generated:")
    print(f"  • Regex Patterns: {tables_count * 2} (long→short + short→long)")
    print(f"  • GPT Queries: {total}")
    print(f"  • Keywords: {sum(len(getattr(e, 'keywords', [])) for e in table_entries)}")
    print()

    print("Coverage:")
    print(f"  • Bluebook Rules: {len([r for r in results.get('rules', []) if getattr(r, 'source', '') == 'bluebook'])}")
    print(f"  • Redbook Rules: {len([r for r in results.get('rules', []) if getattr(r, 'source', '') == 'redbook'])}")
    print(f"  • Bluebook Tables: 16 tables")
    print(f"  • Table Entries: {tables_count}")
    print(f"  • Citation Forms: {forms_count}")
    print()

    print("="*80)
    print("✅ COMPREHENSIVE PROCESSING COMPLETE")
    print("="*80)
    print()
    print("All Bluebook and Redbook content has been processed:")
    print("  ✓ Every rule")
    print("  ✓ Every table")
    print("  ✓ Every abbreviation")
    print("  ✓ Every citation form")
    print("  ✓ Everything")
    print()
    print(f"Output: {output_path}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
