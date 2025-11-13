#!/usr/bin/env python3
"""
GPT-5 Citation Parser for Stanford Law Review
Extracts and classifies citations from footnotes using GPT-5
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests
from pathlib import Path
import logging

from src.utils.api_logger import log_api_usage

logger = logging.getLogger(__name__)


@dataclass
class ParsedCitation:
    """A single parsed citation from a footnote"""
    citation_text: str  # The full citation text
    citation_type: str  # case, statute, regulation, article, book, website, etc.
    
    # Case fields
    case_name: Optional[str] = None
    party1: Optional[str] = None
    party2: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    court: Optional[str] = None
    year: Optional[str] = None
    
    # Statute/Regulation fields
    title_number: Optional[str] = None
    code_type: Optional[str] = None  # U.S.C., C.F.R., etc.
    section: Optional[str] = None
    subsection: Optional[str] = None
    
    # Article/Book fields
    author: Optional[str] = None
    article_title: Optional[str] = None
    book_title: Optional[str] = None
    journal: Optional[str] = None
    publisher: Optional[str] = None
    edition: Optional[str] = None
    
    # Other fields
    url: Optional[str] = None
    database: Optional[str] = None
    docket_number: Optional[str] = None
    document_type: Optional[str] = None
    
    # Metadata
    confidence: float = 1.0
    is_short_form: bool = False
    refers_to_footnote: Optional[int] = None  # For "supra note X" references


@dataclass
class ParsedFootnote:
    """A parsed footnote containing multiple citations"""
    footnote_number: int
    original_text: str
    citations: List[ParsedCitation]
    has_signal: bool = False  # See, See also, Cf., etc.
    signal_type: Optional[str] = None
    explanatory_text: Optional[str] = None  # Non-citation text


class GPTCitationParser:
    """Parse citations from footnotes using GPT-5"""
    
    # System prompt for GPT-5
    SYSTEM_PROMPT = """You are a legal citation parser for the Stanford Law Review. 
Extract and classify all citations from the given footnote text.

Return a JSON object with this structure:
{
  "citations": [
    {
      "citation_text": "full citation text",
      "citation_type": "case|statute|regulation|article|book|website|brief|legislative|other",
      "case_name": "for cases only",
      "party1": "first party name",
      "party2": "second party name", 
      "volume": "volume number",
      "reporter": "reporter abbreviation",
      "page": "starting page",
      "pincite": "specific page cited",
      "court": "court abbreviation",
      "year": "year",
      "title_number": "for statutes/regulations",
      "code_type": "U.S.C.|C.F.R.|state code",
      "section": "section number",
      "author": "for articles/books",
      "article_title": "article title",
      "journal": "journal name",
      "book_title": "book title",
      "url": "if present",
      "is_short_form": false,
      "confidence": 0.95
    }
  ],
  "has_signal": false,
  "signal_type": null,
  "explanatory_text": "any non-citation text"
}

Rules:
1. Extract ALL citations, including those after signals like "See" or "See also"
2. For "Id." citations, mark as short form and include what's known
3. For "supra note X" references, include refers_to_footnote field
4. Parse parentheticals as separate fields when they contain dates/courts
5. Include pincites (specific pages) when present
6. Set confidence between 0 and 1 based on parsing certainty
7. Use "other" type for unclear citations

Think step by step but respond only with valid JSON."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the GPT citation parser"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            # Try to load from config
            config_path = Path("config/api_keys.json")
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)
                    self.api_key = config.get("openai", {}).get("api_key")
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured")
    
    def parse_footnote(self, footnote_number: int, footnote_text: str) -> ParsedFootnote:
        """
        Parse a single footnote using GPT-5
        
        Args:
            footnote_number: The footnote number
            footnote_text: The full text of the footnote
            
        Returns:
            ParsedFootnote with extracted citations
        """
        if not self.api_key:
            # Fallback to basic parsing
            return self._basic_parse(footnote_number, footnote_text)
        
        try:
            # Call OpenAI API with low-latency settings
            response = self._call_gpt(footnote_text)
            
            # Parse the response
            parsed_data = json.loads(response)
            
            # Convert to ParsedFootnote
            citations = []
            for cite_data in parsed_data.get("citations", []):
                citation = ParsedCitation(
                    citation_text=cite_data.get("citation_text", ""),
                    citation_type=cite_data.get("citation_type", "other"),
                    case_name=cite_data.get("case_name"),
                    party1=cite_data.get("party1"),
                    party2=cite_data.get("party2"),
                    volume=cite_data.get("volume"),
                    reporter=cite_data.get("reporter"),
                    page=cite_data.get("page"),
                    pincite=cite_data.get("pincite"),
                    court=cite_data.get("court"),
                    year=cite_data.get("year"),
                    title_number=cite_data.get("title_number"),
                    code_type=cite_data.get("code_type"),
                    section=cite_data.get("section"),
                    subsection=cite_data.get("subsection"),
                    author=cite_data.get("author"),
                    article_title=cite_data.get("article_title"),
                    book_title=cite_data.get("book_title"),
                    journal=cite_data.get("journal"),
                    url=cite_data.get("url"),
                    confidence=cite_data.get("confidence", 1.0),
                    is_short_form=cite_data.get("is_short_form", False),
                    refers_to_footnote=cite_data.get("refers_to_footnote")
                )
                citations.append(citation)
            
            return ParsedFootnote(
                footnote_number=footnote_number,
                original_text=footnote_text,
                citations=citations,
                has_signal=parsed_data.get("has_signal", False),
                signal_type=parsed_data.get("signal_type"),
                explanatory_text=parsed_data.get("explanatory_text")
            )
            
        except Exception as e:
            logger.error(f"Error parsing footnote {footnote_number} with GPT: {e}")
            # Fallback to basic parsing
            return self._basic_parse(footnote_number, footnote_text)
    
    def _call_gpt(self, footnote_text: str) -> str:
        """Call GPT-5 API with low-latency settings"""
        url = "https://api.openai.com/v1/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use gpt-5 model
        data = {
            "model": "gpt-5",
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"Parse this footnote:\n{footnote_text}"}
            ],
            "temperature": 0.1,  # Low temperature for consistency
            "max_tokens": 1000,
            "response_format": {"type": "json_object"}  # Force JSON response
        }
        
        # Log API call
        log_api_usage(
            api_name="openai",
            endpoint=url,
            method="POST",
            parameters={"model": data["model"], "max_tokens": data["max_tokens"]},
            citation_text=footnote_text[:100]
        )
        
        response = requests.post(url, headers=headers, json=data, timeout=10)
        
        # Log response
        log_api_usage(
            api_name="openai",
            endpoint=url,
            method="POST",
            response_code=response.status_code,
            success=(response.status_code == 200)
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            raise Exception(f"GPT API error: {response.status_code}")
    
    def _basic_parse(self, footnote_number: int, footnote_text: str) -> ParsedFootnote:
        """Basic fallback parsing without GPT"""
        # Simple extraction of obvious citations
        citations = []
        
        # Look for U.S.C. citations
        import re
        usc_pattern = r"(\d+)\s+(U\.S\.C\.)\s*§+\s*([0-9a-zA-Z\-\.]+)"
        for match in re.finditer(usc_pattern, footnote_text):
            citations.append(ParsedCitation(
                citation_text=match.group(0),
                citation_type="statute",
                title_number=match.group(1),
                code_type="U.S.C.",
                section=match.group(3)
            ))
        
        # Look for case citations (v. or v pattern)
        case_pattern = r"([A-Z][^,]+?)\s+v\.?\s+([^,]+?),\s*(\d+)\s+([A-Za-z.\s']+?)\s+(\d+)"
        for match in re.finditer(case_pattern, footnote_text):
            citations.append(ParsedCitation(
                citation_text=match.group(0),
                citation_type="case",
                party1=match.group(1).strip(),
                party2=match.group(2).strip(),
                volume=match.group(3),
                reporter=match.group(4).strip(),
                page=match.group(5)
            ))
        
        return ParsedFootnote(
            footnote_number=footnote_number,
            original_text=footnote_text,
            citations=citations if citations else [
                ParsedCitation(
                    citation_text=footnote_text,
                    citation_type="other",
                    confidence=0.3
                )
            ],
            has_signal=bool(re.match(r"^(See|See also|Cf\.|E\.g\.,|But see)", footnote_text)),
            explanatory_text=None
        )
    
    def parse_footnotes_batch(self, footnotes: Dict[int, str]) -> Dict[int, ParsedFootnote]:
        """
        Parse multiple footnotes in batch
        
        Args:
            footnotes: Dictionary mapping footnote numbers to text
            
        Returns:
            Dictionary mapping footnote numbers to ParsedFootnote objects
        """
        parsed = {}
        for fn_num, fn_text in footnotes.items():
            logger.info(f"Parsing footnote {fn_num}")
            parsed[fn_num] = self.parse_footnote(fn_num, fn_text)
        
        return parsed
    
    def export_to_json(self, parsed_footnotes: Dict[int, ParsedFootnote], 
                      output_path: str = "output/data/parsed_citations.json"):
        """Export parsed citations to JSON file"""
        output_data = {}
        
        for fn_num, parsed_fn in parsed_footnotes.items():
            output_data[str(fn_num)] = {
                "original_text": parsed_fn.original_text,
                "has_signal": parsed_fn.has_signal,
                "signal_type": parsed_fn.signal_type,
                "explanatory_text": parsed_fn.explanatory_text,
                "citations": [asdict(cite) for cite in parsed_fn.citations]
            }
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Exported parsed citations to {output_file}")
        return output_file


def test_parser():
    """Test the GPT citation parser"""
    parser = GPTCitationParser()
    
    test_footnotes = {
        1: "Alice Corp. v. CLS Bank Int'l, 573 U.S. 208, 216 (2014).",
        2: "35 U.S.C. § 101 (2018).",
        3: "See Mark A. Lemley, Software Patents and the Return of Functional Claiming, 2013 Wis. L. Rev. 905, 907-08.",
        4: "Id. at 910.",
        5: "See supra note 1.",
    }
    
    parsed = parser.parse_footnotes_batch(test_footnotes)
    
    for fn_num, parsed_fn in parsed.items():
        print(f"\nFootnote {fn_num}:")
        print(f"  Original: {parsed_fn.original_text[:50]}...")
        print(f"  Citations found: {len(parsed_fn.citations)}")
        for cite in parsed_fn.citations:
            print(f"    - Type: {cite.citation_type}")
            print(f"      Text: {cite.citation_text}")
            if cite.party1:
                print(f"      Parties: {cite.party1} v. {cite.party2}")
            if cite.title_number:
                print(f"      Statute: {cite.title_number} {cite.code_type} § {cite.section}")


if __name__ == "__main__":
    test_parser()