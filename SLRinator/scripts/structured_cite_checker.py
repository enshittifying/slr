#!/usr/bin/env python3
"""
Structured R1 Cite Checker with Proper Context Tracking

Maintains article structure:
- Text propositions
- Footnote numbers
- Multiple citations per footnote
- Errors reported with full context
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from docx import Document
from lxml import etree


@dataclass
class Citation:
    """Single citation within a footnote."""
    citation_number: int  # Order within footnote (1, 2, 3...)
    citation_text: str
    errors: List[Dict] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


@dataclass
class Footnote:
    """Single footnote with potentially multiple citations."""
    footnote_id: str  # From Word document
    footnote_number: int  # Display number (1, 2, 3...)
    footnote_text: str
    citations: List[Citation] = None
    text_context: str = ""  # Text proposition this footnote supports

    def __post_init__(self):
        if self.citations is None:
            self.citations = []


@dataclass
class CitationError:
    """Error found in a specific citation."""
    footnote_number: int
    citation_number: int
    error_id: str
    rule_id: str
    rule_title: str
    description: str
    severity: str
    matched_text: str
    auto_fixable: bool
    source: str  # "Bluebook" or "Redbook"

    def format_for_report(self) -> str:
        """Format error for display."""
        return (f"Footnote {self.footnote_number}, Citation {self.citation_number}: "
                f"[{self.severity.upper()}] {self.rule_id} - {self.description}")


class StructuredCiteChecker:
    """R1 cite checker with proper article structure tracking."""

    def __init__(self, framework_path: Path):
        """Initialize with error detection framework."""
        with open(framework_path, 'r', encoding='utf-8') as f:
            self.framework = json.load(f)

        self.all_errors = (self.framework['bluebook_errors'] +
                          self.framework['redbook_errors'])

    def extract_structured_footnotes(self, docx_path: Path) -> List[Footnote]:
        """Extract footnotes with proper structure and IDs."""
        doc = Document(docx_path)
        footnotes = []

        # Access footnotes through XML structure
        doc_part = doc.part
        footnotes_part = None

        for rel in doc_part.rels.values():
            if "footnotes" in rel.target_ref:
                footnotes_part = rel.target_part
                break

        if not footnotes_part:
            return footnotes

        # Parse footnotes XML
        footnotes_xml = footnotes_part.blob
        root = etree.fromstring(footnotes_xml)

        # Define namespace
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

        # Track footnote number (display number)
        footnote_counter = 0

        # Find all footnote elements
        for footnote in root.findall('.//w:footnote', ns):
            fn_id = footnote.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')

            if fn_id is None or fn_id in ['-1', '0']:  # Skip separators
                continue

            # Extract text from all paragraphs in this footnote
            footnote_text = ""
            for para in footnote.findall('.//w:p', ns):
                para_text = []
                for run in para.findall('.//w:r', ns):
                    for text_elem in run.findall('.//w:t', ns):
                        if text_elem.text:
                            para_text.append(text_elem.text)
                footnote_text += ''.join(para_text) + " "

            if footnote_text.strip():
                footnote_counter += 1
                footnotes.append(Footnote(
                    footnote_id=fn_id,
                    footnote_number=footnote_counter,
                    footnote_text=footnote_text.strip()
                ))

        return footnotes

    def parse_citations_in_footnote(self, footnote: Footnote) -> List[Citation]:
        """Parse individual citations within a single footnote.

        Citations are typically separated by semicolons or periods.
        This handles multiple citations in one footnote.
        """
        citations = []
        text = footnote.footnote_text

        # Split on common citation separators
        # Pattern: semicolon followed by space, or period followed by capital letter
        citation_parts = re.split(r';\s+(?=[A-Z])|\.(?=\s+[A-Z][a-z]+\s+v\.)', text)

        for i, citation_text in enumerate(citation_parts, 1):
            if citation_text.strip():
                citations.append(Citation(
                    citation_number=i,
                    citation_text=citation_text.strip()
                ))

        return citations

    def check_citation(self, citation: Citation, footnote_number: int) -> List[CitationError]:
        """Check a single citation against all error patterns."""
        errors = []

        for error_def in self.all_errors:
            if not error_def.get('regex_detect'):
                continue

            try:
                pattern = error_def['regex_detect']
                match = re.search(pattern, citation.citation_text,
                                re.IGNORECASE | re.MULTILINE)

                if match:
                    error = CitationError(
                        footnote_number=footnote_number,
                        citation_number=citation.citation_number,
                        error_id=error_def.get('error_id', 'unknown'),
                        rule_id=error_def.get('rule_id', 'unknown'),
                        rule_title=error_def.get('rule_title', 'Unknown'),
                        description=error_def.get('description', 'No description'),
                        severity=error_def.get('severity', 'medium'),
                        matched_text=match.group()[:100] if match else '',
                        auto_fixable=error_def.get('auto_fixable') in [True, 'yes', 'manual', 'programmatic'],
                        source=error_def.get('source', 'Unknown')
                    )
                    errors.append(error)
                    citation.errors.append(asdict(error))

            except re.error:
                continue  # Skip invalid patterns

        return errors

    def check_article(self, docx_path: Path) -> Dict:
        """Check entire article with structured reporting."""
        print("="*80)
        print("STRUCTURED R1 CITE CHECKING")
        print("="*80)

        # Extract structured footnotes
        print(f"\n1. Extracting footnotes from {docx_path.name}...")
        footnotes = self.extract_structured_footnotes(docx_path)
        print(f"   ✅ Extracted {len(footnotes)} footnotes")

        # Parse citations within each footnote
        print(f"\n2. Parsing citations within footnotes...")
        total_citations = 0
        for footnote in footnotes:
            footnote.citations = self.parse_citations_in_footnote(footnote)
            total_citations += len(footnote.citations)

        print(f"   ✅ Parsed {total_citations} citations across {len(footnotes)} footnotes")
        print(f"   ℹ️  Average: {total_citations/len(footnotes):.1f} citations per footnote")

        # Check each citation
        print(f"\n3. Checking citations against error framework...")
        all_errors = []

        for footnote in footnotes:
            for citation in footnote.citations:
                errors = self.check_citation(citation, footnote.footnote_number)
                all_errors.extend(errors)

        print(f"   ✅ Found {len(all_errors)} total errors")

        # Compile results
        results = {
            'total_footnotes': len(footnotes),
            'total_citations': total_citations,
            'total_errors': len(all_errors),
            'errors': all_errors,
            'footnotes': [asdict(fn) for fn in footnotes],
            'errors_by_footnote': self._group_errors_by_footnote(all_errors),
            'errors_by_severity': self._group_errors_by_severity(all_errors),
            'errors_by_rule': self._group_errors_by_rule(all_errors)
        }

        return results

    def _group_errors_by_footnote(self, errors: List[CitationError]) -> Dict[int, int]:
        """Group errors by footnote number."""
        by_footnote = {}
        for error in errors:
            fn = error.footnote_number
            by_footnote[fn] = by_footnote.get(fn, 0) + 1
        return by_footnote

    def _group_errors_by_severity(self, errors: List[CitationError]) -> Dict[str, int]:
        """Group errors by severity level."""
        by_severity = {'high': 0, 'error': 0, 'major': 0, 'medium': 0, 'minor': 0, 'warning': 0}
        for error in errors:
            sev = error.severity
            by_severity[sev] = by_severity.get(sev, 0) + 1
        return by_severity

    def _group_errors_by_rule(self, errors: List[CitationError]) -> Dict[str, int]:
        """Group errors by rule ID."""
        by_rule = {}
        for error in errors:
            rule = error.rule_id
            by_rule[rule] = by_rule.get(rule, 0) + 1
        return by_rule

    def print_report(self, results: Dict):
        """Print formatted report with proper structure."""
        print("\n" + "="*80)
        print("R1 CITE CHECKING REPORT")
        print("="*80)

        print(f"\n📊 ARTICLE STRUCTURE:")
        print(f"   • {results['total_footnotes']} footnotes")
        print(f"   • {results['total_citations']} total citations")
        print(f"   • {results['total_citations']/results['total_footnotes']:.1f} citations per footnote (avg)")

        print(f"\n🔍 ERRORS DETECTED:")
        print(f"   • {results['total_errors']} total errors")

        print(f"\n📈 BY SEVERITY:")
        for severity, count in sorted(results['errors_by_severity'].items()):
            if count > 0:
                print(f"   • {severity}: {count}")

        print(f"\n📋 BY RULE (Top 10):")
        sorted_rules = sorted(results['errors_by_rule'].items(),
                            key=lambda x: x[1], reverse=True)[:10]
        for rule, count in sorted_rules:
            print(f"   • {rule}: {count} errors")

        print(f"\n📍 ERRORS BY FOOTNOTE (Footnotes with errors):")
        sorted_footnotes = sorted(results['errors_by_footnote'].items())
        for fn_num, count in sorted_footnotes[:20]:  # Show first 20
            print(f"   • Footnote {fn_num}: {count} error(s)")

        if len(sorted_footnotes) > 20:
            print(f"   ... and {len(sorted_footnotes) - 20} more footnotes with errors")

        # Show sample errors with full context
        print(f"\n🔎 SAMPLE ERRORS (First 10):")
        for i, error in enumerate(results['errors'][:10], 1):
            print(f"\n{i}. {error.format_for_report()}")
            print(f"   Source: {error.source}")
            print(f"   Matched: {error.matched_text[:80]}...")
            print(f"   Auto-fixable: {'Yes' if error.auto_fixable else 'No'}")

        print("\n" + "="*80)


def main():
    """Main function."""
    # Load framework
    framework_path = Path(__file__).parent.parent / "config" / "error_detection_framework_ENHANCED.json"

    # Initialize checker
    checker = StructuredCiteChecker(framework_path)

    # Check Sanders article
    article_path = Path("/home/user/slr/sp_machine/Sanders_PreSP_PostEEFormatting.docx")

    if not article_path.exists():
        print(f"❌ Article not found at {article_path}")
        return 1

    # Run structured check
    results = checker.check_article(article_path)

    # Print report
    checker.print_report(results)

    # Save detailed results to JSON
    output_path = Path(__file__).parent.parent / "output" / "sanders_structured_check.json"
    output_path.parent.mkdir(exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        # Convert CitationError objects to dicts for JSON serialization
        results_serializable = {
            **results,
            'errors': [asdict(e) for e in results['errors']]
        }
        json.dump(results_serializable, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Detailed results saved to: {output_path}")
    print("="*80)

    return 0


if __name__ == '__main__':
    exit(main())
