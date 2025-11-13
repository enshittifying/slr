#!/usr/bin/env python3
"""
Test OCR quality detection on R1-085-01-076-Lira.pdf
"""
import sys
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.pdf_processor import process_r1_pdf

def test_pdf_quality():
    """Test quality detection on the problematic R1-085 PDF."""

    r1_pdf = Path("/Users/ben/app/slrapp/78 SLR V2 R2 F/78 SLR V2 R1/R1-085-01-076-Lira.pdf")

    if not r1_pdf.exists():
        print(f"❌ PDF not found: {r1_pdf}")
        return

    print(f"\n{'='*80}")
    print(f"Testing OCR Quality Detection on: {r1_pdf.name}")
    print(f"{'='*80}\n")

    # Process the PDF
    result = process_r1_pdf(r1_pdf)

    if not result["success"]:
        print(f"❌ Failed to process PDF: {result['error']}")
        return

    print(f"\n✓ Processing completed")
    print(f"  Has quality issues: {result.get('has_quality_issues', 'Unknown')}")
    print(f"  Redboxed regions found: {len(result['redboxed_regions'])}")

    # Show detailed quality assessment for each region
    for i, region in enumerate(result['redboxed_regions']):
        print(f"\n{'─'*80}")
        print(f"Region {i+1} (Page {region['page']})")
        print(f"{'─'*80}")

        quality = region.get('quality_assessment')
        if quality:
            print(f"\n  Quality Score: {quality['score']:.2f}/1.0")
            print(f"  Is Corrupted: {quality['is_corrupted']}")

            if quality['issues']:
                print(f"\n  ❌ ISSUES:")
                for issue in quality['issues']:
                    print(f"     • {issue}")

            if quality['warnings']:
                print(f"\n  ⚠️  WARNINGS:")
                for warning in quality['warnings']:
                    print(f"     • {warning}")

            print(f"\n  Metrics:")
            for metric, value in quality['metrics'].items():
                if isinstance(value, float):
                    print(f"     {metric}: {value:.2%}" if value < 1 else f"     {metric}: {value:.2f}")
                else:
                    print(f"     {metric}: {value}")

        # Show first 300 characters of extracted text
        print(f"\n  Extracted Text (first 300 chars):")
        print(f"  {'-'*76}")
        text_preview = region['text'][:300].replace('\n', '\\n')
        print(f"  {text_preview}")
        if len(region['text']) > 300:
            print(f"  ... ({len(region['text']) - 300} more characters)")

    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    test_pdf_quality()
