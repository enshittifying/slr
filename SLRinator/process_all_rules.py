#!/usr/bin/env python3
"""
Massively Parallel Rule Processing Script
Processes all 354 Bluebook + Redbook rules to generate comprehensive detection methods
"""
import sys
import logging
from pathlib import Path

# Add SLRinator to path
sys.path.insert(0, str(Path(__file__).parent))

from src.r1_validation.rule_processor import RuleProcessor
from src.r1_validation.logging_config import setup_logging


def main():
    """Run parallel rule processing."""
    print("="*80)
    print("MASSIVE PARALLEL RULE PROCESSING")
    print("="*80)
    print()

    # Setup logging
    setup_logging(
        log_level="INFO",
        enable_console=True,
        enable_file=True
    )

    logger = logging.getLogger(__name__)

    logger.info("Initializing rule processor...")

    # Initialize processor
    processor = RuleProcessor()

    # Get rule count
    all_rules = processor.get_all_rules()
    logger.info(f"Found {len(all_rules)} total rules to process")

    bluebook_count = len([r for r in all_rules if r["source"] == "bluebook"])
    redbook_count = len([r for r in all_rules if r["source"] == "redbook"])

    print(f"Total Rules: {len(all_rules)}")
    print(f"  Bluebook: {bluebook_count}")
    print(f"  Redbook: {redbook_count}")
    print()

    # Process all rules in parallel (max 20 workers for massive parallelism)
    print("Processing all rules in parallel (20 workers)...")
    print("This may take a few minutes...")
    print()

    processed_rules = processor.process_all_rules_parallel(max_workers=20)

    print()
    print("="*80)
    print("PROCESSING COMPLETE")
    print("="*80)
    print()

    # Generate summary
    summary = processor.generate_summary_report()
    print(summary)
    print()

    # Save results
    print("Saving processed rules...")
    output_path = processor.save_processed_rules()
    print(f"✅ Saved to: {output_path}")
    print()

    # Display sample processed rules
    print("="*80)
    print("SAMPLE PROCESSED RULES")
    print("="*80)
    print()

    for i, rule in enumerate(processed_rules[:5], 1):
        print(f"{i}. Rule {rule.rule_id} ({rule.source}): {rule.rule_title}")
        print(f"   Complexity: {rule.complexity}")
        print(f"   Keywords: {', '.join(rule.keywords[:5])}")
        print(f"   Regex Patterns: {len(rule.regex_patterns)}")
        print(f"   Citation Types: {', '.join(rule.citation_types)}")
        print()

    print("="*80)
    print("STATISTICS")
    print("="*80)
    print()

    # Calculate statistics
    total_regex = sum(len(r.regex_patterns) for r in processed_rules)
    total_keywords = sum(len(r.keywords) for r in processed_rules)

    print(f"Total Rules: {len(processed_rules)}")
    print(f"Total Regex Patterns: {total_regex}")
    print(f"Total Keywords: {total_keywords}")
    print(f"Total GPT Queries: {len(processed_rules) * 2}")  # Primary + fallback
    print()

    # Complexity breakdown
    simple = len([r for r in processed_rules if r.complexity == "simple"])
    moderate = len([r for r in processed_rules if r.complexity == "moderate"])
    complex_rules = len([r for r in processed_rules if r.complexity == "complex"])

    print("Complexity Distribution:")
    print(f"  Simple: {simple} rules")
    print(f"  Moderate: {moderate} rules")
    print(f"  Complex: {complex_rules} rules")
    print()

    # Citation types coverage
    all_types = set()
    for rule in processed_rules:
        all_types.update(rule.citation_types)

    print(f"Citation Types Covered: {', '.join(sorted(all_types))}")
    print()

    print("="*80)
    print("✅ ALL RULES PROCESSED SUCCESSFULLY")
    print("="*80)
    print()
    print(f"Enhanced rules saved to: {output_path}")
    print()
    print("Next steps:")
    print("  1. Review enhanced_rules.json")
    print("  2. Integrate enhanced detection methods into citation_validator.py")
    print("  3. Add rule-specific validation functions")
    print("  4. Test enhanced validation")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
