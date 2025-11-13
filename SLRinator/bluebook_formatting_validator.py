#!/usr/bin/env python3
"""
Bluebook Formatting Validator with Real Format Detection
Handles HTML, Markdown, LaTeX, and Word document formatting
"""

import re
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json
from pathlib import Path
from dataclasses import dataclass
from bs4 import BeautifulSoup
import docx
from docx.enum.text import WD_UNDERLINE

class FormatType(Enum):
    """Types of text formatting"""
    PLAIN = "plain"
    HTML = "html"
    MARKDOWN = "markdown"
    LATEX = "latex"
    DOCX = "docx"
    RTF = "rtf"
    BLUEBOOK_MARKUP = "bluebook"  # Custom markup for testing

class FormattingElement(Enum):
    """Formatting elements to check"""
    ITALIC = "italic"
    UNDERLINE = "underline"
    SMALL_CAPS = "small_caps"
    BOLD = "bold"
    SUPERSCRIPT = "superscript"
    SUBSCRIPT = "subscript"

@dataclass
class FormatDetection:
    """Result of format detection"""
    text: str
    has_italic: bool = False
    has_underline: bool = False
    has_small_caps: bool = False
    has_bold: bool = False
    italic_portions: List[str] = None
    underlined_portions: List[str] = None
    small_caps_portions: List[str] = None
    
    def __post_init__(self):
        if self.italic_portions is None:
            self.italic_portions = []
        if self.underlined_portions is None:
            self.underlined_portions = []
        if self.small_caps_portions is None:
            self.small_caps_portions = []

class FormattingDetector:
    """Detect formatting in various text formats"""
    
    def __init__(self):
        self.format_patterns = self._load_format_patterns()
        
    def _load_format_patterns(self) -> Dict:
        """Load patterns for detecting formatting in different formats"""
        return {
            'html': {
                'italic': [
                    r'<i>(.*?)</i>',
                    r'<em>(.*?)</em>',
                    r'<span[^>]*font-style:\s*italic[^>]*>(.*?)</span>',
                    r'<span[^>]*class="[^"]*italic[^"]*"[^>]*>(.*?)</span>'
                ],
                'underline': [
                    r'<u>(.*?)</u>',
                    r'<span[^>]*text-decoration:\s*underline[^>]*>(.*?)</span>',
                    r'<span[^>]*class="[^"]*underline[^"]*"[^>]*>(.*?)</span>'
                ],
                'small_caps': [
                    r'<span[^>]*font-variant:\s*small-caps[^>]*>(.*?)</span>',
                    r'<span[^>]*class="[^"]*small-caps[^"]*"[^>]*>(.*?)</span>',
                    r'<sc>(.*?)</sc>'
                ],
                'bold': [
                    r'<b>(.*?)</b>',
                    r'<strong>(.*?)</strong>',
                    r'<span[^>]*font-weight:\s*bold[^>]*>(.*?)</span>'
                ]
            },
            'markdown': {
                'italic': [
                    r'\*([^*]+)\*',      # *text*
                    r'_([^_]+)_'         # _text_
                ],
                'bold': [
                    r'\*\*([^*]+)\*\*',  # **text**
                    r'__([^_]+)__'       # __text__
                ],
                'underline': [],  # Markdown doesn't have native underline
                'small_caps': []  # Markdown doesn't have native small caps
            },
            'latex': {
                'italic': [
                    r'\\textit\{([^}]+)\}',
                    r'\\emph\{([^}]+)\}',
                    r'\{\\it\s+([^}]+)\}',
                    r'\{\\em\s+([^}]+)\}'
                ],
                'underline': [
                    r'\\underline\{([^}]+)\}'
                ],
                'small_caps': [
                    r'\\textsc\{([^}]+)\}',
                    r'\{\\sc\s+([^}]+)\}'
                ],
                'bold': [
                    r'\\textbf\{([^}]+)\}',
                    r'\{\\bf\s+([^}]+)\}'
                ]
            },
            'bluebook': {
                # Custom markup for easy testing
                'italic': [
                    r'<i>(.*?)</i>',
                    r'_([^_]+)_'
                ],
                'underline': [
                    r'<u>(.*?)</u>',
                    r'__([^_]+)__'
                ],
                'small_caps': [
                    r'<sc>(.*?)</sc>',
                    r'\^\^([^^]+)\^\^'
                ],
                'bold': [
                    r'<b>(.*?)</b>',
                    r'\*\*([^*]+)\*\*'
                ]
            }
        }
    
    def detect_format_type(self, text: str) -> FormatType:
        """Auto-detect the format type of the text"""
        if '<html' in text.lower() or '<i>' in text or '<em>' in text:
            return FormatType.HTML
        elif '\\textit{' in text or '\\emph{' in text:
            return FormatType.LATEX
        elif re.search(r'\*[^*]+\*|_[^_]+_', text):
            return FormatType.MARKDOWN
        elif '<i>' in text or '<sc>' in text or '^^' in text:
            return FormatType.BLUEBOOK
        else:
            return FormatType.PLAIN
    
    def extract_formatting(self, text: str, format_type: Optional[FormatType] = None) -> FormatDetection:
        """Extract all formatting from text"""
        if format_type is None:
            format_type = self.detect_format_type(text)
        
        result = FormatDetection(text=text)
        
        if format_type == FormatType.PLAIN:
            return result
        
        if format_type == FormatType.HTML:
            return self._extract_html_formatting(text)
        elif format_type == FormatType.MARKDOWN:
            return self._extract_markdown_formatting(text)
        elif format_type == FormatType.LATEX:
            return self._extract_latex_formatting(text)
        elif format_type == FormatType.BLUEBOOK:
            return self._extract_bluebook_formatting(text)
        elif format_type == FormatType.DOCX:
            return self._extract_docx_formatting(text)
        
        return result
    
    def _extract_html_formatting(self, html_text: str) -> FormatDetection:
        """Extract formatting from HTML"""
        result = FormatDetection(text=html_text)
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Extract plain text
        result.text = soup.get_text()
        
        # Find italic elements
        for tag in soup.find_all(['i', 'em']):
            result.has_italic = True
            result.italic_portions.append(tag.get_text())
        
        # Find underlined elements
        for tag in soup.find_all('u'):
            result.has_underline = True
            result.underlined_portions.append(tag.get_text())
        
        # Find elements with CSS styles
        for tag in soup.find_all(style=True):
            style = tag.get('style', '')
            if 'font-style: italic' in style or 'font-style:italic' in style:
                result.has_italic = True
                result.italic_portions.append(tag.get_text())
            if 'text-decoration: underline' in style or 'text-decoration:underline' in style:
                result.has_underline = True
                result.underlined_portions.append(tag.get_text())
            if 'font-variant: small-caps' in style or 'font-variant:small-caps' in style:
                result.has_small_caps = True
                result.small_caps_portions.append(tag.get_text())
        
        return result
    
    def _extract_markdown_formatting(self, text: str) -> FormatDetection:
        """Extract formatting from Markdown"""
        result = FormatDetection(text=text)
        
        # Extract italics
        patterns = self.format_patterns['markdown']['italic']
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                result.has_italic = True
                result.italic_portions.append(match.group(1))
        
        # Remove formatting to get plain text
        plain_text = text
        plain_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', plain_text)  # Remove bold
        plain_text = re.sub(r'\*([^*]+)\*', r'\1', plain_text)      # Remove italic
        plain_text = re.sub(r'__([^_]+)__', r'\1', plain_text)      # Remove bold
        plain_text = re.sub(r'_([^_]+)_', r'\1', plain_text)        # Remove italic
        result.text = plain_text
        
        return result
    
    def _extract_latex_formatting(self, text: str) -> FormatDetection:
        """Extract formatting from LaTeX"""
        result = FormatDetection(text=text)
        
        # Extract italics
        for pattern in self.format_patterns['latex']['italic']:
            matches = re.finditer(pattern, text)
            for match in matches:
                result.has_italic = True
                result.italic_portions.append(match.group(1))
        
        # Extract underlines
        for pattern in self.format_patterns['latex']['underline']:
            matches = re.finditer(pattern, text)
            for match in matches:
                result.has_underline = True
                result.underlined_portions.append(match.group(1))
        
        # Extract small caps
        for pattern in self.format_patterns['latex']['small_caps']:
            matches = re.finditer(pattern, text)
            for match in matches:
                result.has_small_caps = True
                result.small_caps_portions.append(match.group(1))
        
        # Clean LaTeX to get plain text
        plain_text = text
        plain_text = re.sub(r'\\[a-z]+\{([^}]+)\}', r'\1', plain_text)
        plain_text = re.sub(r'\{\\[a-z]+\s+([^}]+)\}', r'\1', plain_text)
        result.text = plain_text
        
        return result
    
    def _extract_bluebook_formatting(self, text: str) -> FormatDetection:
        """Extract formatting from custom Bluebook markup"""
        result = FormatDetection(text=text)
        
        # Extract each format type
        format_types = ['italic', 'underline', 'small_caps', 'bold']
        for format_type in format_types:
            patterns = self.format_patterns['bluebook'][format_type]
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if format_type == 'italic':
                        result.has_italic = True
                        result.italic_portions.append(match.group(1))
                    elif format_type == 'underline':
                        result.has_underline = True
                        result.underlined_portions.append(match.group(1))
                    elif format_type == 'small_caps':
                        result.has_small_caps = True
                        result.small_caps_portions.append(match.group(1))
        
        # Clean markup to get plain text
        plain_text = text
        plain_text = re.sub(r'<[^>]+>', '', plain_text)  # Remove HTML-like tags
        plain_text = re.sub(r'_([^_]+)_', r'\1', plain_text)  # Remove underscores
        plain_text = re.sub(r'\^\^([^^]+)\^\^', r'\1', plain_text)  # Remove carets
        plain_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', plain_text)  # Remove asterisks
        result.text = plain_text
        
        return result
    
    def _extract_docx_formatting(self, docx_path: str) -> FormatDetection:
        """Extract formatting from Word document"""
        result = FormatDetection(text="")
        doc = docx.Document(docx_path)
        
        full_text = []
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                text = run.text
                full_text.append(text)
                
                if run.italic:
                    result.has_italic = True
                    result.italic_portions.append(text)
                
                if run.underline and run.underline != WD_UNDERLINE.NONE:
                    result.has_underline = True
                    result.underlined_portions.append(text)
                
                if run.font.small_caps:
                    result.has_small_caps = True
                    result.small_caps_portions.append(text)
        
        result.text = ''.join(full_text)
        return result

class BluebookFormattingValidator:
    """Validate Bluebook formatting rules"""
    
    def __init__(self):
        self.detector = FormattingDetector()
        self.formatting_rules = self._load_formatting_rules()
    
    def _load_formatting_rules(self) -> Dict:
        """Load Bluebook formatting rules"""
        return {
            'case_names': {
                'law_review': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Case names must be italicized in law review articles'
                },
                'court_documents': {
                    'format': FormattingElement.UNDERLINE,
                    'message': 'Case names must be underlined in court documents and briefs'
                },
                'textual_sentences': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Case names in textual sentences must be italicized'
                }
            },
            'signals': {
                'all_contexts': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Signals (See, Cf., But see, etc.) must be italicized'
                }
            },
            'id_citations': {
                'all_contexts': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Id. must always be italicized'
                }
            },
            'legislative_materials': {
                'bills': {
                    'format': FormattingElement.SMALL_CAPS,
                    'message': 'Bill numbers should be in small caps'
                },
                'resolutions': {
                    'format': FormattingElement.SMALL_CAPS,
                    'message': 'Resolution numbers should be in small caps'
                }
            },
            'books': {
                'titles': {
                    'format': FormattingElement.SMALL_CAPS,
                    'message': 'Book titles should be in small caps'
                },
                'authors': {
                    'format': FormattingElement.SMALL_CAPS,
                    'message': 'Book authors in citations should be in small caps'
                }
            },
            'articles': {
                'titles': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Article titles should be italicized'
                }
            },
            'constitutions': {
                'all_contexts': {
                    'format': FormattingElement.SMALL_CAPS,
                    'message': 'Constitution citations should be in small caps'
                }
            },
            'emphasis': {
                'added': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Added emphasis must be italicized'
                }
            },
            'foreign_words': {
                'latin': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Latin phrases (e.g., inter alia, sui generis) must be italicized'
                }
            },
            'procedural_phrases': {
                'ex_parte': {
                    'format': FormattingElement.ITALIC,
                    'message': 'Ex parte must be italicized'
                },
                'in_re': {
                    'format': FormattingElement.ITALIC,
                    'message': 'In re must be italicized'
                }
            }
        }
    
    def validate_citation_formatting(self, citation: str, context: Dict = None) -> Dict:
        """Validate formatting of a citation"""
        # Detect format type and extract formatting
        format_detection = self.detector.extract_formatting(citation)
        
        # Determine citation type from plain text
        citation_type = self._determine_citation_type(format_detection.text)
        
        # Set default context
        if context is None:
            context = {'document_type': 'law_review'}
        
        violations = []
        suggestions = []
        
        # Check case name formatting
        if citation_type == 'case':
            case_name = self._extract_case_name(format_detection.text)
            if case_name:
                # Check if case name is properly formatted
                if context.get('document_type') == 'brief':
                    if case_name not in format_detection.underlined_portions:
                        violations.append({
                            'rule': 'case_name_underline',
                            'message': self.formatting_rules['case_names']['court_documents']['message'],
                            'text': case_name,
                            'required_format': 'underline'
                        })
                        suggestions.append(f'Underline: {case_name}')
                else:  # law review
                    if case_name not in format_detection.italic_portions:
                        violations.append({
                            'rule': 'case_name_italic',
                            'message': self.formatting_rules['case_names']['law_review']['message'],
                            'text': case_name,
                            'required_format': 'italic'
                        })
                        suggestions.append(f'Italicize: {case_name}')
        
        # Check signal formatting
        signal = self._extract_signal(format_detection.text)
        if signal and signal not in format_detection.italic_portions:
            violations.append({
                'rule': 'signal_italic',
                'message': self.formatting_rules['signals']['all_contexts']['message'],
                'text': signal,
                'required_format': 'italic'
            })
            suggestions.append(f'Italicize signal: {signal}')
        
        # Check Id. formatting
        if 'Id.' in format_detection.text and 'Id.' not in format_detection.italic_portions:
            violations.append({
                'rule': 'id_italic',
                'message': self.formatting_rules['id_citations']['all_contexts']['message'],
                'text': 'Id.',
                'required_format': 'italic'
            })
            suggestions.append('Italicize: Id.')
        
        # Check for procedural phrases
        if 'ex parte' in format_detection.text.lower() and 'ex parte' not in ' '.join(format_detection.italic_portions).lower():
            violations.append({
                'rule': 'ex_parte_italic',
                'message': self.formatting_rules['procedural_phrases']['ex_parte']['message'],
                'text': 'ex parte',
                'required_format': 'italic'
            })
        
        # Check constitution formatting
        if 'Const.' in format_detection.text and not any('Const.' in portion for portion in format_detection.small_caps_portions):
            violations.append({
                'rule': 'constitution_small_caps',
                'message': self.formatting_rules['constitutions']['all_contexts']['message'],
                'text': 'Constitution',
                'required_format': 'small_caps'
            })
            suggestions.append('Use small caps for constitutional citations')
        
        return {
            'citation': citation,
            'plain_text': format_detection.text,
            'format_detected': {
                'has_italic': format_detection.has_italic,
                'has_underline': format_detection.has_underline,
                'has_small_caps': format_detection.has_small_caps,
                'italic_portions': format_detection.italic_portions,
                'underlined_portions': format_detection.underlined_portions,
                'small_caps_portions': format_detection.small_caps_portions
            },
            'valid': len(violations) == 0,
            'violations': violations,
            'suggestions': suggestions
        }
    
    def _determine_citation_type(self, text: str) -> str:
        """Determine type of citation from text"""
        if ' v. ' in text or ' v ' in text:
            return 'case'
        elif 'U.S.C.' in text or 'C.F.R.' in text:
            return 'statute'
        elif 'Const.' in text:
            return 'constitution'
        elif 'Id.' in text:
            return 'id'
        else:
            return 'other'
    
    def _extract_case_name(self, text: str) -> Optional[str]:
        """Extract case name from citation"""
        match = re.search(r'^([^,]+v\.\s+[^,]+)', text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_signal(self, text: str) -> Optional[str]:
        """Extract signal from citation"""
        signals = ['See', 'See also', 'Cf.', 'Compare', 'But see', 'But cf.', 'See generally', 'E.g.', 'Accord', 'Contra']
        for signal in signals:
            if text.startswith(signal):
                return signal
        return None

def demonstrate_formatting_validation():
    """Demonstrate the formatting validator"""
    validator = BluebookFormattingValidator()
    
    print("BLUEBOOK FORMATTING VALIDATOR DEMONSTRATION")
    print("=" * 70)
    
    # Test cases with different formatting
    test_cases = [
        {
            'description': 'HTML formatted case (correct italics)',
            'citation': '<i>Smith v. Jones</i>, 123 F.3d 456 (2d Cir. 2020)',
            'context': {'document_type': 'law_review'}
        },
        {
            'description': 'HTML case missing italics',
            'citation': 'Smith v. Jones, 123 F.3d 456 (2d Cir. 2020)',
            'context': {'document_type': 'law_review'}
        },
        {
            'description': 'Markdown formatted case',
            'citation': '*Smith v. Jones*, 123 F.3d 456 (2d Cir. 2020)',
            'context': {'document_type': 'law_review'}
        },
        {
            'description': 'LaTeX formatted case',
            'citation': '\\textit{Smith v. Jones}, 123 F.3d 456 (2d Cir. 2020)',
            'context': {'document_type': 'law_review'}
        },
        {
            'description': 'Underlined case for brief',
            'citation': '<u>Smith v. Jones</u>, 123 F.3d 456 (2d Cir. 2020)',
            'context': {'document_type': 'brief'}
        },
        {
            'description': 'Signal with correct formatting',
            'citation': '<i>See</i> <i>Smith v. Jones</i>, 123 F.3d 456 (2d Cir. 2020)',
            'context': {'document_type': 'law_review'}
        },
        {
            'description': 'Id. citation with formatting',
            'citation': '<i>Id.</i> at 458',
            'context': {}
        },
        {
            'description': 'Constitution with small caps',
            'citation': '<sc>U.S. Const.</sc> art. I, § 8',
            'context': {}
        },
        {
            'description': 'Mixed formatting',
            'citation': '<i>See</i> <i>Ex parte Smith</i>, 123 F.3d 456 (2d Cir. 2020); <i>But see</i> <u>Jones v. State</u>, 789 P.2d 123 (Cal. 1990)',
            'context': {'document_type': 'law_review'}
        }
    ]
    
    for test in test_cases:
        print(f"\n{test['description']}")
        print("-" * 60)
        print(f"Citation: {test['citation']}")
        
        result = validator.validate_citation_formatting(test['citation'], test.get('context'))
        
        print(f"Plain text: {result['plain_text']}")
        print(f"Valid: {'✓' if result['valid'] else '✗'}")
        
        if result['format_detected']['has_italic']:
            print(f"  Italic portions: {', '.join(result['format_detected']['italic_portions'])}")
        if result['format_detected']['has_underline']:
            print(f"  Underlined portions: {', '.join(result['format_detected']['underlined_portions'])}")
        if result['format_detected']['has_small_caps']:
            print(f"  Small caps portions: {', '.join(result['format_detected']['small_caps_portions'])}")
        
        if result['violations']:
            print("  Violations:")
            for violation in result['violations']:
                print(f"    ✗ {violation['message']}")
                print(f"      Text: '{violation['text']}' needs {violation['required_format']}")
        
        if result['suggestions']:
            print("  Fixes:")
            for suggestion in result['suggestions']:
                print(f"    → {suggestion}")

if __name__ == "__main__":
    demonstrate_formatting_validation()