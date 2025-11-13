#!/usr/bin/env python3
"""
Fallback Rule-Based Citation Parser for Stanford Law Review
Handles common citation patterns when GPT is unavailable
"""

import re
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from src.core.enhanced_gpt_parser import Citation, ParsedFootnote


class FallbackCitationParser:
    """Rule-based parser for common legal citation patterns"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common citation patterns
        self.patterns = {
            'usc_statute': re.compile(r'(\d+)\s+U\.S\.C\.\s+§\s+([\d\w\(\)\-\.]+)', re.IGNORECASE),
            'cfr_regulation': re.compile(r'(\d+)\s+C\.F\.R\.\s+§\s+([\d\w\(\)\-\.]+)', re.IGNORECASE),
            'federal_reporter': re.compile(r'(\d+)\s+F\.\s*(\d+d?|4th|3d|2d|Supp\.?\d*)\s+(\d+)', re.IGNORECASE),
            'supreme_court': re.compile(r'(\d+)\s+U\.S\.\s+(\d+)', re.IGNORECASE),
            'state_statute': re.compile(r'([A-Z][a-z]+\.?\s*[A-Z][a-z]*\.?)\s+§\s+([\d\w\(\)\-\.]+)', re.IGNORECASE),
        }
        
        # USC Title names for better identification
        self.usc_titles = {
            '1': 'General Provisions',
            '2': 'The Congress', 
            '3': 'The President',
            '4': 'Flag and Seal, Seat of Government, and the States',
            '5': 'Government Organization and Employees',
            '7': 'Agriculture',
            '8': 'Aliens and Nationality',
            '9': 'Arbitration',
            '10': 'Armed Forces',
            '11': 'Bankruptcy',
            '12': 'Banks and Banking',
            '13': 'Census',
            '14': 'Coast Guard',
            '15': 'Commerce and Trade',
            '16': 'Conservation',
            '17': 'Copyrights',
            '18': 'Crimes and Criminal Procedure',
            '19': 'Customs Duties',
            '20': 'Education',
            '21': 'Food and Drugs',
            '22': 'Foreign Relations and Intercourse',
            '23': 'Highways',
            '24': 'Hospitals and Asylums',
            '25': 'Indians',
            '26': 'Internal Revenue Code',
            '27': 'Intoxicating Liquors',
            '28': 'Judiciary and Judicial Procedure',
            '29': 'Labor',
            '30': 'Mineral Lands and Mining',
            '31': 'Money and Finance',
            '32': 'National Guard',
            '33': 'Navigation and Navigable Waters',
            '34': 'Navy (repealed)',
            '35': 'Patents',
            '36': 'Patriotic and National Observances, Ceremonies, and Organizations',
            '37': 'Pay and Allowances of the Uniformed Services',
            '38': 'Veterans\' Benefits',
            '39': 'Postal Service',
            '40': 'Public Buildings, Property, and Works',
            '41': 'Public Contracts',
            '42': 'The Public Health and Welfare',
            '43': 'Public Lands',
            '44': 'Public Printing and Documents',
            '45': 'Railroads',
            '46': 'Shipping',
            '47': 'Telecommunications',
            '48': 'Territories and Insular Possessions',
            '49': 'Transportation',
            '50': 'War and National Defense',
            '51': 'National and Commercial Space Programs',
            '52': 'Voting and Elections',
            '54': 'National Park Service and Related Programs'
        }

    def parse_footnote(self, footnote_number: int, footnote_text: str) -> ParsedFootnote:
        """Parse footnote using rule-based patterns"""
        
        self.logger.info(f"Fallback parsing footnote {footnote_number}")
        
        citations = []
        confidence = 0.7  # Rule-based parsing has decent confidence
        reasoning = "Rule-based parsing using regex patterns"
        
        # Clean footnote text
        text = footnote_text.strip()
        
        # Check for USC statute
        usc_matches = self.patterns['usc_statute'].findall(text)
        for match in usc_matches:
            title, section = match
            title_name = self.usc_titles.get(title, f"Title {title}")
            
            citation = Citation(
                citation_id=f"fn{footnote_number}_usc_{title}_{section.replace('.', '_')}",
                citation_type="statute",
                full_text=f"{title} U.S.C. § {section}",
                title_number=title,
                code_name="U.S.C.",
                section=section,
                retrieval_priority=1,  # Easy to retrieve
                notes=f"USC {title_name}"
            )
            citations.append(citation)
            reasoning += f"; Found USC {title} § {section}"
        
        # Check for CFR regulation
        cfr_matches = self.patterns['cfr_regulation'].findall(text)
        for match in cfr_matches:
            title, section = match
            
            citation = Citation(
                citation_id=f"fn{footnote_number}_cfr_{title}_{section.replace('.', '_')}",
                citation_type="regulation",
                full_text=f"{title} C.F.R. § {section}",
                title_number=title,
                code_name="C.F.R.",
                section=section,
                retrieval_priority=1,
                notes=f"CFR Title {title}"
            )
            citations.append(citation)
            reasoning += f"; Found CFR {title} § {section}"
        
        # Check for Federal Reporter cases
        fed_matches = self.patterns['federal_reporter'].findall(text)
        for match in fed_matches:
            volume, series, page = match
            reporter = f"F.{series}" if series else "F."
            
            citation = Citation(
                citation_id=f"fn{footnote_number}_fed_{volume}_{page}",
                citation_type="case",
                full_text=f"{volume} {reporter} {page}",
                volume=volume,
                reporter=reporter,
                page=page,
                retrieval_priority=2,
                notes="Federal court case"
            )
            citations.append(citation)
            reasoning += f"; Found case {volume} {reporter} {page}"
        
        # Check for Supreme Court cases  
        scotus_matches = self.patterns['supreme_court'].findall(text)
        for match in scotus_matches:
            volume, page = match
            
            citation = Citation(
                citation_id=f"fn{footnote_number}_us_{volume}_{page}",
                citation_type="case", 
                full_text=f"{volume} U.S. {page}",
                volume=volume,
                reporter="U.S.",
                page=page,
                court="Supreme Court",
                retrieval_priority=1,
                notes="U.S. Supreme Court case"
            )
            citations.append(citation)
            reasoning += f"; Found SCOTUS case {volume} U.S. {page}"
        
        # If no citations found, check for common signals
        if not citations:
            if any(signal in text.lower() for signal in ['see also', 'supra', 'infra', 'id.']):
                confidence = 0.3
                reasoning += "; Contains citation signals but no parseable citations"
            else:
                confidence = 0.1
                reasoning += "; No recognizable citation patterns found"
        
        return ParsedFootnote(
            footnote_number=footnote_number,
            original_text=footnote_text,
            citations=citations,
            parsing_confidence=confidence,
            gpt_reasoning=reasoning,
            parsed_at=datetime.now().isoformat()
        )
    
    def parse_multiple_footnotes(self, footnotes: List[tuple]) -> List[ParsedFootnote]:
        """Parse multiple footnotes with fallback parser"""
        results = []
        
        for footnote_number, footnote_text in footnotes:
            self.logger.info(f"Fallback parsing footnote {footnote_number}...")
            result = self.parse_footnote(footnote_number, footnote_text)
            results.append(result)
            
            self.logger.info(f"  Found {len(result.citations)} citations with confidence {result.parsing_confidence:.2f}")
        
        return results