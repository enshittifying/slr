"""
Quote Checker Module for Stanford Law Review
Verifies quotes against source PDFs
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import fitz  # PyMuPDF
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import difflib

from stage3.footnote_processor import Footnote

logger = logging.getLogger(__name__)


@dataclass
class QuoteVerification:
    """Result of quote verification"""
    quote_text: str
    found: bool
    source_file: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 0.0
    exact_match: bool = False
    differences: List[str] = None
    context: str = ""
    suggestions: List[str] = None
    

class QuoteChecker:
    """Checks quotes against source PDFs"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.min_confidence = self.config.get('min_quote_confidence', 0.85)
        self.context_chars = self.config.get('context_chars', 100)
        self.fuzzy_threshold = self.config.get('fuzzy_threshold', 80)
        
    def check_footnote(self, footnote: Footnote, sources: Dict[str, str]) -> Dict[str, Any]:
        """Check all quotes in a footnote against available sources"""
        results = {
            'footnote_num': footnote.number,
            'quotes': [],
            'citations': [],
            'overall_verified': True
        }
        
        # Check each quote
        for quote in footnote.quotes:
            quote_result = self.verify_quote(quote, sources, footnote)
            results['quotes'].append(quote_result)
            
            if not quote_result['verified']:
                results['overall_verified'] = False
        
        # Check support for each citation
        for citation in footnote.citations:
            cite_result = {
                'text': citation.get('text', ''),
                'source_id': self._extract_source_id(citation),
                'supported': 'Unknown',
                'issues': [],
                'notes': ''
            }
            
            # Find corresponding source
            source_id = cite_result['source_id']
            if source_id and source_id in sources:
                source_path = sources[source_id]
                
                # Check if quotes are found in this source
                for quote in footnote.quotes:
                    verification = self.verify_quote_in_pdf(quote, source_path)
                    if verification.found:
                        cite_result['supported'] = 'Yes'
                        cite_result['page_found'] = verification.page_number
                    else:
                        cite_result['issues'].append(f"Quote not found: {quote[:50]}...")
            
            results['citations'].append(cite_result)
        
        return results
    
    def verify_quote(self, quote: str, sources: Dict[str, str], 
                     footnote: Optional[Footnote] = None) -> Dict[str, Any]:
        """Verify a single quote against all available sources"""
        result = {
            'quote': quote,
            'verified': False,
            'source_found': None,
            'page_number': None,
            'confidence': 0.0,
            'exact_match': False,
            'issues': []
        }
        
        # Clean the quote
        cleaned_quote = self._clean_quote(quote)
        
        # Search through all sources
        best_match = None
        best_confidence = 0.0
        
        for source_id, source_path in sources.items():
            if not Path(source_path).exists():
                logger.warning(f"Source file not found: {source_path}")
                continue
            
            verification = self.verify_quote_in_pdf(cleaned_quote, source_path)
            
            if verification.confidence > best_confidence:
                best_confidence = verification.confidence
                best_match = verification
                best_match.source_file = source_path
        
        # Update result with best match
        if best_match and best_match.confidence >= self.min_confidence:
            result['verified'] = True
            result['source_found'] = Path(best_match.source_file).name
            result['page_number'] = best_match.page_number
            result['confidence'] = best_match.confidence
            result['exact_match'] = best_match.exact_match
            
            if not best_match.exact_match and best_match.differences:
                result['issues'] = best_match.differences
        else:
            result['issues'].append("Quote not found in any source")
            if best_match:
                result['confidence'] = best_match.confidence
                result['issues'].append(f"Best match only {best_match.confidence:.1%} confident")
        
        return result
    
    def verify_quote_in_pdf(self, quote: str, pdf_path: str) -> QuoteVerification:
        """Verify a quote in a specific PDF"""
        verification = QuoteVerification(
            quote_text=quote,
            found=False
        )
        
        try:
            doc = fitz.open(pdf_path)
            
            # First try exact match
            exact_result = self._search_exact_quote(quote, doc)
            if exact_result['found']:
                verification.found = True
                verification.exact_match = True
                verification.page_number = exact_result['page']
                verification.confidence = 1.0
                verification.context = exact_result['context']
                doc.close()
                return verification
            
            # Try fuzzy matching
            fuzzy_result = self._search_fuzzy_quote(quote, doc)
            if fuzzy_result['found']:
                verification.found = True
                verification.exact_match = False
                verification.page_number = fuzzy_result['page']
                verification.confidence = fuzzy_result['confidence']
                verification.context = fuzzy_result['context']
                verification.differences = fuzzy_result['differences']
                verification.suggestions = fuzzy_result['suggestions']
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error checking quote in {pdf_path}: {e}")
        
        return verification
    
    def _search_exact_quote(self, quote: str, doc: fitz.Document) -> Dict[str, Any]:
        """Search for exact quote match in PDF"""
        result = {'found': False, 'page': None, 'context': ''}
        
        # Handle quotes that may span multiple lines
        search_text = quote.replace('\n', ' ').replace('  ', ' ')
        
        for page_num, page in enumerate(doc):
            # Search on page
            text_instances = page.search_for(search_text, hit_max=10)
            
            if text_instances:
                result['found'] = True
                result['page'] = page_num + 1
                
                # Get context
                page_text = page.get_text()
                quote_pos = page_text.find(search_text)
                if quote_pos != -1:
                    start = max(0, quote_pos - self.context_chars)
                    end = min(len(page_text), quote_pos + len(search_text) + self.context_chars)
                    result['context'] = page_text[start:end]
                
                return result
        
        # Try searching without special characters
        cleaned = re.sub(r'[^\w\s]', ' ', search_text)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            page_cleaned = re.sub(r'[^\w\s]', ' ', page_text)
            page_cleaned = re.sub(r'\s+', ' ', page_cleaned)
            
            if cleaned.lower() in page_cleaned.lower():
                result['found'] = True
                result['page'] = page_num + 1
                
                # Find position for context
                pos = page_cleaned.lower().find(cleaned.lower())
                if pos != -1:
                    start = max(0, pos - self.context_chars)
                    end = min(len(page_text), pos + len(cleaned) + self.context_chars)
                    result['context'] = page_text[start:end]
                
                return result
        
        return result
    
    def _search_fuzzy_quote(self, quote: str, doc: fitz.Document) -> Dict[str, Any]:
        """Search for fuzzy quote match in PDF"""
        result = {
            'found': False,
            'page': None,
            'context': '',
            'confidence': 0.0,
            'differences': [],
            'suggestions': []
        }
        
        # Clean and prepare quote
        search_text = self._clean_quote(quote)
        search_words = search_text.lower().split()
        
        if len(search_words) < 3:  # Too short for fuzzy matching
            return result
        
        best_match = None
        best_score = 0
        best_page = None
        
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            
            # Split into sentences for better matching
            sentences = self._split_into_sentences(page_text)
            
            for sentence in sentences:
                # Calculate similarity
                score = fuzz.partial_ratio(search_text.lower(), sentence.lower())
                
                if score > best_score and score >= self.fuzzy_threshold:
                    best_score = score
                    best_match = sentence
                    best_page = page_num + 1
            
            # Also try sliding window approach for longer quotes
            if len(search_text) > 100:
                windows = self._create_text_windows(page_text, len(search_text))
                
                for window in windows:
                    score = fuzz.ratio(search_text.lower(), window.lower())
                    
                    if score > best_score and score >= self.fuzzy_threshold:
                        best_score = score
                        best_match = window
                        best_page = page_num + 1
        
        if best_match and best_score >= self.fuzzy_threshold:
            result['found'] = True
            result['page'] = best_page
            result['context'] = best_match
            result['confidence'] = best_score / 100.0
            
            # Find differences
            differences = self._find_differences(search_text, best_match)
            result['differences'] = differences
            
            # Generate suggestions
            if differences:
                result['suggestions'] = self._generate_suggestions(search_text, best_match)
        
        return result
    
    def _clean_quote(self, quote: str) -> str:
        """Clean quote for searching"""
        # Remove footnote numbers
        cleaned = re.sub(r'\[\d+\]', '', quote)
        cleaned = re.sub(r'\d+$', '', cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Remove leading/trailing punctuation but keep internal
        cleaned = cleaned.strip(' .,;:')
        
        return cleaned
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        # Clean and filter
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return sentences
    
    def _create_text_windows(self, text: str, window_size: int) -> List[str]:
        """Create sliding windows of text"""
        windows = []
        words = text.split()
        
        # Adjust window size to word count
        window_words = len(self._clean_quote(text[:window_size]).split())
        
        for i in range(len(words) - window_words + 1):
            window = ' '.join(words[i:i + window_words])
            windows.append(window)
        
        return windows
    
    def _find_differences(self, original: str, found: str) -> List[str]:
        """Find differences between original quote and found text"""
        differences = []
        
        # Use difflib to find differences
        differ = difflib.unified_diff(
            original.split(),
            found.split(),
            lineterm='',
            n=0
        )
        
        for line in differ:
            if line.startswith('-'):
                differences.append(f"Missing: {line[1:].strip()}")
            elif line.startswith('+'):
                differences.append(f"Added: {line[1:].strip()}")
        
        # Check for alterations
        if '...' in original and '...' not in found:
            differences.append("Ellipsis in quote not found in source")
        
        if '[' in original and ']' in original:
            differences.append("Bracketed alterations present")
        
        return differences[:5]  # Limit to 5 differences
    
    def _generate_suggestions(self, original: str, found: str) -> List[str]:
        """Generate suggestions for fixing quote issues"""
        suggestions = []
        
        # Check if quote is too long
        if len(original) > len(found) * 1.5:
            suggestions.append("Quote may be combining multiple passages")
        
        # Check if quote is missing context
        if len(found) > len(original) * 1.5:
            suggestions.append("Consider using ellipsis (...) to indicate omitted text")
        
        # Check capitalization
        if original[0].islower() and found[0].isupper():
            suggestions.append("Use brackets to indicate capitalization change: '[C]...'")
        
        return suggestions
    
    def _extract_source_id(self, citation: Dict[str, Any]) -> Optional[str]:
        """Extract source ID from citation"""
        # This would need to be implemented based on your citation format
        # For now, return a placeholder
        cite_text = citation.get('text', '')
        
        # Try to extract from citation text
        # Look for patterns like "SP-001" or similar
        match = re.search(r'SP-(\d{3})', cite_text)
        if match:
            return match.group(1)
        
        return None
    
    def check_alterations(self, quote: str) -> Dict[str, Any]:
        """Check if quote has proper alteration indicators"""
        alterations = {
            'has_ellipsis': False,
            'has_brackets': False,
            'has_emphasis_added': False,
            'issues': []
        }
        
        # Check for ellipsis
        if '...' in quote or '. . .' in quote:
            alterations['has_ellipsis'] = True
            
            # Check if ellipsis is properly formatted
            if '. . .' in quote and '...' in quote:
                alterations['issues'].append("Inconsistent ellipsis format")
        
        # Check for brackets
        if '[' in quote and ']' in quote:
            alterations['has_brackets'] = True
            
            # Check if brackets are balanced
            if quote.count('[') != quote.count(']'):
                alterations['issues'].append("Unbalanced brackets")
        
        # Check for emphasis added
        if '(emphasis added)' in quote.lower():
            alterations['has_emphasis_added'] = True
        
        # Check for suspicious alterations
        if re.search(r'\[[A-Z][a-z]+\]', quote):  # [He], [She], etc.
            if not alterations['has_brackets']:
                alterations['issues'].append("Pronoun substitution without proper brackets")
        
        return alterations
    
    def generate_report(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary report of quote checking results"""
        report = {
            'total_footnotes': len(results),
            'total_quotes': 0,
            'verified_quotes': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'not_found': 0,
            'confidence_scores': [],
            'issues_summary': {},
            'problematic_footnotes': []
        }
        
        for result in results:
            footnote_has_issues = False
            
            for quote_result in result.get('quotes', []):
                report['total_quotes'] += 1
                
                if quote_result['verified']:
                    report['verified_quotes'] += 1
                    
                    if quote_result['exact_match']:
                        report['exact_matches'] += 1
                    else:
                        report['fuzzy_matches'] += 1
                    
                    report['confidence_scores'].append(quote_result['confidence'])
                else:
                    report['not_found'] += 1
                    footnote_has_issues = True
                
                # Track issues
                for issue in quote_result.get('issues', []):
                    issue_type = issue.split(':')[0] if ':' in issue else issue
                    report['issues_summary'][issue_type] = \
                        report['issues_summary'].get(issue_type, 0) + 1
            
            if footnote_has_issues:
                report['problematic_footnotes'].append(result['footnote_num'])
        
        # Calculate statistics
        if report['confidence_scores']:
            report['avg_confidence'] = sum(report['confidence_scores']) / len(report['confidence_scores'])
        else:
            report['avg_confidence'] = 0.0
        
        report['verification_rate'] = (report['verified_quotes'] / report['total_quotes'] * 100) \
            if report['total_quotes'] > 0 else 0
        
        return report