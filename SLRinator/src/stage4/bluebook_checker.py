"""
Bluebook Compliance Checker for Stanford Law Review
Validates citations against Bluebook rules (21st Edition)
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import docx

logger = logging.getLogger(__name__)


class ViolationSeverity(Enum):
    HIGH = "High"       # Must fix - clear Bluebook violation
    MEDIUM = "Medium"   # Should fix - stylistic issue
    LOW = "Low"         # Consider fixing - minor issue


@dataclass
class BluebookViolation:
    """Represents a Bluebook compliance violation"""
    footnote_num: int
    citation: str
    violation_type: str
    rule: str
    issue: str
    suggestion: str
    severity: ViolationSeverity
    location: str = ""
    

class BluebookChecker:
    """Checks citations for Bluebook compliance"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.violations: List[BluebookViolation] = []
        
        # Load Bluebook abbreviations (Tables T1-T16)
        self.abbreviations = self._load_abbreviations()
        
        # Track footnotes for id. and supra validation
        self.footnote_history: Dict[int, List[str]] = {}
        self.first_citations: Dict[str, int] = {}  # Track first appearance
        
    def _load_abbreviations(self) -> Dict[str, Dict[str, str]]:
        """Load Bluebook abbreviation tables"""
        return {
            'reporters': {
                # Federal Reporters
                'U.S.': 'United States Reports',
                'S. Ct.': 'Supreme Court Reporter',
                'L. Ed.': "Lawyers' Edition",
                'L. Ed. 2d': "Lawyers' Edition, Second Series",
                'F.': 'Federal Reporter',
                'F.2d': 'Federal Reporter, Second Series',
                'F.3d': 'Federal Reporter, Third Series',
                'F. App\'x': 'Federal Appendix',
                'F. Supp.': 'Federal Supplement',
                'F. Supp. 2d': 'Federal Supplement, Second Series',
                'F. Supp. 3d': 'Federal Supplement, Third Series',
                
                # State Reporters (sample)
                'Cal.': 'California Reports',
                'Cal. App.': 'California Appellate Reports',
                'N.Y.': 'New York Reports',
                'N.E.': 'North Eastern Reporter',
                'N.E.2d': 'North Eastern Reporter, Second Series',
            },
            'courts': {
                # Federal Courts
                'U.S.': 'United States Supreme Court',
                '1st Cir.': 'First Circuit',
                '2d Cir.': 'Second Circuit',
                '3d Cir.': 'Third Circuit',
                '4th Cir.': 'Fourth Circuit',
                '5th Cir.': 'Fifth Circuit',
                '6th Cir.': 'Sixth Circuit',
                '7th Cir.': 'Seventh Circuit',
                '8th Cir.': 'Eighth Circuit',
                '9th Cir.': 'Ninth Circuit',
                '10th Cir.': 'Tenth Circuit',
                '11th Cir.': 'Eleventh Circuit',
                'D.C. Cir.': 'D.C. Circuit',
                'Fed. Cir.': 'Federal Circuit',
                
                # District Courts
                'S.D.N.Y.': 'Southern District of New York',
                'N.D. Cal.': 'Northern District of California',
                'E.D. Tex.': 'Eastern District of Texas',
            },
            'months': {
                'Jan.': 'January',
                'Feb.': 'February',
                'Mar.': 'March',
                'Apr.': 'April',
                'Aug.': 'August',
                'Sept.': 'September',
                'Oct.': 'October',
                'Nov.': 'November',
                'Dec.': 'December',
            },
            'journals': {
                'L. Rev.': 'Law Review',
                'J.': 'Journal',
                'L.J.': 'Law Journal',
                'U.': 'University',
                'Int\'l': 'International',
                'Comp.': 'Comparative',
                'Const.': 'Constitutional',
            },
            'words': {
                # Common words that should be abbreviated
                'Company': 'Co.',
                'Corporation': 'Corp.',
                'Incorporated': 'Inc.',
                'Limited': 'Ltd.',
                'Association': 'Ass\'n',
                'Department': 'Dep\'t',
                'Government': 'Gov\'t',
                'National': 'Nat\'l',
                'International': 'Int\'l',
            }
        }
    
    def check_document(self, docx_path: str) -> List[Dict[str, Any]]:
        """Check all citations in a Word document"""
        self.violations = []
        
        try:
            doc = docx.Document(docx_path)
            
            # Extract and check footnotes
            footnotes = self._extract_footnotes(doc)
            
            for fn_num, fn_text in footnotes.items():
                self.check_footnote(fn_num, fn_text)
            
            # Check cross-references (id., supra, infra)
            self._check_cross_references()
            
        except Exception as e:
            logger.error(f"Error checking document: {e}")
        
        return self._violations_to_dict()
    
    def check_footnote(self, footnote_num: int, text: str):
        """Check all citations in a footnote"""
        # Track citations in this footnote
        self.footnote_history[footnote_num] = []
        
        # Find all citations in the footnote
        citations = self._extract_citations(text)
        
        for citation in citations:
            # Track citation
            self.footnote_history[footnote_num].append(citation)
            
            # Run all checks
            self._check_case_citation(footnote_num, citation)
            self._check_statute_citation(footnote_num, citation)
            self._check_article_citation(footnote_num, citation)
            self._check_book_citation(footnote_num, citation)
            self._check_web_citation(footnote_num, citation)
            self._check_short_forms(footnote_num, citation)
            self._check_signals(footnote_num, citation)
            self._check_punctuation(footnote_num, citation)
            self._check_abbreviations(footnote_num, citation)
            self._check_capitalization(footnote_num, citation)
    
    def _check_case_citation(self, fn_num: int, citation: str):
        """Check case citation format"""
        if ' v. ' not in citation and ' v ' not in citation:
            return
        
        # Rule 10: Cases
        
        # Check "v." format (should be lowercase with periods)
        if ' v ' in citation or ' V. ' in citation or ' V ' in citation:
            self._add_violation(
                fn_num, citation, "Case Citation", "Rule 10.2.1(e)",
                "Incorrect 'versus' format",
                "Use lowercase 'v.' with periods",
                ViolationSeverity.HIGH
            )
        
        # Check case name italicization (can't verify in plain text)
        # This would need Word document format checking
        
        # Check reporter abbreviation
        reporter_pattern = r'\d+\s+([A-Z][A-Za-z0-9.\s]+?)\s+\d+'
        reporter_match = re.search(reporter_pattern, citation)
        if reporter_match:
            reporter = reporter_match.group(1).strip()
            if reporter not in self.abbreviations['reporters']:
                if not reporter.endswith('.'):
                    self._add_violation(
                        fn_num, citation, "Case Citation", "Table T1",
                        f"Reporter abbreviation may need period: {reporter}",
                        f"Use {reporter}.",
                        ViolationSeverity.MEDIUM
                    )
        
        # Check parenthetical information
        paren_match = re.search(r'\(([^)]+)\)$', citation)
        if paren_match:
            paren_content = paren_match.group(1)
            
            # Check court abbreviation
            for court_abbr in self.abbreviations['courts']:
                if court_abbr in paren_content:
                    # Verify correct abbreviation format
                    if court_abbr == 'U.S.' and '(' in citation:
                        self._add_violation(
                            fn_num, citation, "Case Citation", "Rule 10.4",
                            "Supreme Court cases should not include court designation",
                            "Remove '(U.S.)' for Supreme Court cases",
                            ViolationSeverity.HIGH
                        )
            
            # Check year format
            year_match = re.search(r'\d{4}', paren_content)
            if not year_match:
                self._add_violation(
                    fn_num, citation, "Case Citation", "Rule 10.5",
                    "Missing year in case citation",
                    "Add year in parentheses",
                    ViolationSeverity.HIGH
                )
    
    def _check_statute_citation(self, fn_num: int, citation: str):
        """Check statute citation format"""
        if 'U.S.C.' not in citation and 'C.F.R.' not in citation:
            return
        
        # Rule 12: Statutes
        
        # Check section symbol
        if 'U.S.C.' in citation or 'C.F.R.' in citation:
            if '§' not in citation and 'Section' not in citation.lower():
                self._add_violation(
                    fn_num, citation, "Statute Citation", "Rule 12.9",
                    "Missing section symbol",
                    "Use § before section number",
                    ViolationSeverity.HIGH
                )
        
        # Check spacing around section symbol
        if '§' in citation:
            if not re.search(r'§\s+\d', citation):
                self._add_violation(
                    fn_num, citation, "Statute Citation", "Rule 6.2(c)",
                    "Missing space after section symbol",
                    "Add space after §",
                    ViolationSeverity.MEDIUM
                )
        
        # Check year in statute citations
        if 'U.S.C.' in citation:
            if not re.search(r'\(\d{4}\)', citation):
                # Year is optional for current code
                pass  # No violation for current code
    
    def _check_article_citation(self, fn_num: int, citation: str):
        """Check article citation format"""
        # Look for law review pattern
        if not re.search(r'\d+\s+[A-Z].*L\.\s*Rev\.', citation):
            return
        
        # Rule 16: Periodicals
        
        # Check author name format (should be last name only in footnotes)
        if citation.startswith(('Professor ', 'Dr. ', 'Mr. ', 'Ms. ')):
            self._add_violation(
                fn_num, citation, "Article Citation", "Rule 16.2",
                "Unnecessary title before author name",
                "Remove title (Professor, Dr., etc.)",
                ViolationSeverity.MEDIUM
            )
        
        # Check law review abbreviation
        if 'Law Review' in citation or 'Law Rev ' in citation:
            self._add_violation(
                fn_num, citation, "Article Citation", "Table T13",
                "Unabbreviated journal name",
                "Use 'L. Rev.' instead of 'Law Review'",
                ViolationSeverity.HIGH
            )
        
        # Check page numbers
        if not re.search(r'\s+\d+,?\s+\d+', citation):
            if 'L. Rev.' in citation or 'J.' in citation:
                self._add_violation(
                    fn_num, citation, "Article Citation", "Rule 16.4",
                    "Missing or incorrect page numbers",
                    "Include starting page and pincite",
                    ViolationSeverity.HIGH
                )
    
    def _check_book_citation(self, fn_num: int, citation: str):
        """Check book citation format"""
        # Simple check for book pattern (author, TITLE (year))
        if not re.search(r'[A-Z][a-z]+,\s+[A-Z].*\(\d{4}\)', citation):
            return
        
        # Rule 15: Books
        
        # Check for small caps in title (can't verify in plain text)
        # This would need Word format checking
        
        # Check edition notation
        if 'edition' in citation.lower() or 'ed ' in citation:
            if not re.search(r'\d+(?:st|nd|rd|th)\s+ed\.', citation):
                self._add_violation(
                    fn_num, citation, "Book Citation", "Rule 15.4",
                    "Incorrect edition format",
                    "Use format like '2d ed.' or '3d ed.'",
                    ViolationSeverity.MEDIUM
                )
    
    def _check_web_citation(self, fn_num: int, citation: str):
        """Check web citation format"""
        if 'http' not in citation.lower() and 'www.' not in citation.lower():
            return
        
        # Rule 18.2: Internet Sources
        
        # Check for access date
        if not re.search(r'\(last (?:visited|accessed|updated)', citation.lower()):
            self._add_violation(
                fn_num, citation, "Web Citation", "Rule 18.2.2",
                "Missing access date for web source",
                "Add '(last visited [date])' at end",
                ViolationSeverity.HIGH
            )
        
        # Check URL format
        url_match = re.search(r'(https?://[^\s,]+)', citation)
        if url_match:
            url = url_match.group(1)
            if url.endswith('.'):
                self._add_violation(
                    fn_num, citation, "Web Citation", "Rule 18.2",
                    "Period after URL",
                    "Remove period from end of URL",
                    ViolationSeverity.LOW
                )
    
    def _check_short_forms(self, fn_num: int, citation: str):
        """Check short form citations"""
        
        # Rule 4: Short Citation Forms
        
        # Check id. usage
        if citation.strip().startswith('Id.'):
            # Check if id. is properly formatted
            if not citation.startswith('Id.'):
                self._add_violation(
                    fn_num, citation, "Short Form", "Rule 4.1",
                    "Incorrect id. format",
                    "Use 'Id.' with capital I and period",
                    ViolationSeverity.HIGH
                )
            
            # Check if id. can be used (must refer to immediately preceding citation)
            if fn_num > 1 and fn_num - 1 not in self.footnote_history:
                self._add_violation(
                    fn_num, citation, "Short Form", "Rule 4.1",
                    "Id. may not refer to immediately preceding authority",
                    "Verify id. refers to last cited source",
                    ViolationSeverity.MEDIUM
                )
        
        # Check supra usage
        if 'supra' in citation.lower():
            if 'supra' in citation and 'Supra' not in citation:
                # Check if it's formatted correctly
                if not re.search(r',\s+supra\s+note\s+\d+', citation):
                    self._add_violation(
                        fn_num, citation, "Short Form", "Rule 4.2",
                        "Incorrect supra format",
                        "Use format: 'Author, supra note X'",
                        ViolationSeverity.HIGH
                    )
        
        # Check infra usage
        if 'infra' in citation.lower():
            if not re.search(r'infra\s+(?:note\s+\d+|Part\s+[IVX]+)', citation):
                self._add_violation(
                    fn_num, citation, "Short Form", "Rule 3.5",
                    "Incorrect infra format",
                    "Use format: 'infra note X' or 'infra Part II'",
                    ViolationSeverity.MEDIUM
                )
    
    def _check_signals(self, fn_num: int, citation: str):
        """Check citation signals"""
        
        # Rule 1.2: Introductory Signals
        
        signals = {
            'See': 'Direct support',
            'See also': 'Additional support',
            'Cf.': 'Comparison',
            'Compare': 'Comparison between sources',
            'Contra': 'Direct contradiction',
            'But see': 'Qualified contradiction',
            'See generally': 'Background information',
            'E.g.,': 'Example',
        }
        
        # Check signal formatting
        for signal, usage in signals.items():
            if citation.startswith(signal):
                # Check italicization (can't verify in plain text)
                
                # Check punctuation after signal
                if signal == 'E.g.,' and not citation.startswith('E.g.,'):
                    self._add_violation(
                        fn_num, citation, "Signal", "Rule 1.2",
                        f"Missing comma after {signal}",
                        f"Use '{signal},'",
                        ViolationSeverity.MEDIUM
                    )
                elif signal == 'Cf.' and not citation.startswith('Cf.'):
                    self._add_violation(
                        fn_num, citation, "Signal", "Rule 1.2",
                        f"Incorrect signal format",
                        f"Use '{signal}' with period",
                        ViolationSeverity.MEDIUM
                    )
    
    def _check_punctuation(self, fn_num: int, citation: str):
        """Check punctuation in citations"""
        
        # Rule 1.1: Citation Sentences and Clauses
        
        # Check for double periods
        if '..' in citation and '...' not in citation:
            self._add_violation(
                fn_num, citation, "Punctuation", "Rule 1.1",
                "Double period",
                "Remove extra period",
                ViolationSeverity.LOW
            )
        
        # Check spacing around commas
        if ' ,' in citation or ',  ' in citation:
            self._add_violation(
                fn_num, citation, "Punctuation", "Rule 6.1",
                "Incorrect spacing around comma",
                "No space before comma, one space after",
                ViolationSeverity.LOW
            )
        
        # Check semicolon usage between citations
        if ';' in citation:
            if not re.search(r';\s+[A-Z]', citation):
                self._add_violation(
                    fn_num, citation, "Punctuation", "Rule 1.1",
                    "Missing space after semicolon",
                    "Add space after semicolon",
                    ViolationSeverity.LOW
                )
    
    def _check_abbreviations(self, fn_num: int, citation: str):
        """Check proper use of abbreviations"""
        
        # Table T6 & T10: Abbreviations
        
        # Check for unabbreviated words
        for full_word, abbrev in self.abbreviations['words'].items():
            if full_word in citation:
                self._add_violation(
                    fn_num, citation, "Abbreviation", "Table T6",
                    f"Unabbreviated word: {full_word}",
                    f"Use '{abbrev}'",
                    ViolationSeverity.MEDIUM
                )
        
        # Check month abbreviations
        months_full = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        
        for month in months_full:
            if month in citation and month not in ['May', 'June', 'July']:
                abbrev = self.abbreviations['months'].get(month[:3] + '.', month)
                self._add_violation(
                    fn_num, citation, "Abbreviation", "Table T12",
                    f"Unabbreviated month: {month}",
                    f"Use '{abbrev}'",
                    ViolationSeverity.LOW
                )
    
    def _check_capitalization(self, fn_num: int, citation: str):
        """Check proper capitalization"""
        
        # Rule 8: Capitalization
        
        # Check case names
        if ' v. ' in citation:
            case_name = citation.split(',')[0] if ',' in citation else citation.split()[0]
            
            # Check for all caps
            if case_name.isupper():
                self._add_violation(
                    fn_num, citation, "Capitalization", "Rule 8",
                    "Case name in all capitals",
                    "Use normal capitalization",
                    ViolationSeverity.MEDIUM
                )
            
            # Check articles in case names
            for article in [' The ', ' A ', ' An ']:
                if article in case_name:
                    self._add_violation(
                        fn_num, citation, "Capitalization", "Rule 10.2.1(a)",
                        f"Article '{article.strip()}' in case name",
                        f"Remove article from case name",
                        ViolationSeverity.LOW
                    )
    
    def _check_cross_references(self):
        """Check validity of cross-references across footnotes"""
        
        # Check supra references point to valid footnotes
        for fn_num, citations in self.footnote_history.items():
            for citation in citations:
                if 'supra note' in citation:
                    ref_match = re.search(r'supra note (\d+)', citation)
                    if ref_match:
                        ref_num = int(ref_match.group(1))
                        if ref_num >= fn_num:
                            self._add_violation(
                                fn_num, citation, "Cross-reference", "Rule 4.2",
                                f"Supra reference to future footnote {ref_num}",
                                "Supra can only reference earlier footnotes",
                                ViolationSeverity.HIGH
                            )
                        elif ref_num not in self.footnote_history:
                            self._add_violation(
                                fn_num, citation, "Cross-reference", "Rule 4.2",
                                f"Supra reference to non-existent footnote {ref_num}",
                                "Verify footnote number",
                                ViolationSeverity.HIGH
                            )
    
    def _extract_citations(self, text: str) -> List[str]:
        """Extract individual citations from footnote text"""
        # Split by semicolons and periods
        citations = []
        
        # Remove leading footnote number if present
        text = re.sub(r'^\d+\.\s*', '', text)
        
        # Split by semicolons (multiple citations)
        parts = re.split(r';\s*', text)
        
        for part in parts:
            part = part.strip()
            if part and not part.endswith(('.', '!', '?')):
                part += '.'
            if part:
                citations.append(part)
        
        return citations
    
    def _extract_footnotes(self, doc) -> Dict[int, str]:
        """Extract footnotes from Word document"""
        footnotes = {}
        
        # This is simplified - would need proper Word XML parsing
        # For now, return empty dict
        return footnotes
    
    def _add_violation(self, fn_num: int, citation: str, violation_type: str,
                      rule: str, issue: str, suggestion: str, severity: ViolationSeverity):
        """Add a violation to the list"""
        violation = BluebookViolation(
            footnote_num=fn_num,
            citation=citation[:100] + '...' if len(citation) > 100 else citation,
            violation_type=violation_type,
            rule=rule,
            issue=issue,
            suggestion=suggestion,
            severity=severity,
            location=f"Footnote {fn_num}"
        )
        self.violations.append(violation)
    
    def _violations_to_dict(self) -> List[Dict[str, Any]]:
        """Convert violations to dictionary format"""
        return [
            {
                'footnote_num': v.footnote_num,
                'citation': v.citation,
                'type': v.violation_type,
                'rule': v.rule,
                'issue': v.issue,
                'suggestion': v.suggestion,
                'severity': v.severity.value,
                'location': v.location
            }
            for v in self.violations
        ]
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a compliance report"""
        report = {
            'total_violations': len(self.violations),
            'by_severity': {
                'High': sum(1 for v in self.violations if v.severity == ViolationSeverity.HIGH),
                'Medium': sum(1 for v in self.violations if v.severity == ViolationSeverity.MEDIUM),
                'Low': sum(1 for v in self.violations if v.severity == ViolationSeverity.LOW),
            },
            'by_type': {},
            'by_rule': {},
            'most_common_issues': [],
        }
        
        # Count by type
        for v in self.violations:
            report['by_type'][v.violation_type] = report['by_type'].get(v.violation_type, 0) + 1
            report['by_rule'][v.rule] = report['by_rule'].get(v.rule, 0) + 1
        
        # Find most common issues
        issue_counts = {}
        for v in self.violations:
            issue_counts[v.issue] = issue_counts.get(v.issue, 0) + 1
        
        report['most_common_issues'] = sorted(
            issue_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return report