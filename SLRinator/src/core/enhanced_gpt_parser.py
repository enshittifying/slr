#!/usr/bin/env python3
"""
Enhanced GPT-5 Citation Parser for Stanford Law Review
Parses footnotes into structured citation data using GPT
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import openai
import os

from src.utils.api_logger import log_api_usage
from src.utils.retry_handler import retry_on_failure, RetryHandler
from src.utils.action_logger import get_action_logger


@dataclass
class Citation:
    """Structured citation data"""
    # Identification
    citation_id: str
    citation_type: str  # case, statute, regulation, article, book, website, etc.
    full_text: str
    
    # Case-specific fields
    case_name: Optional[str] = None
    plaintiff: Optional[str] = None
    defendant: Optional[str] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    pincite: Optional[str] = None
    court: Optional[str] = None
    year: Optional[str] = None
    
    # Statute/Regulation fields
    title_number: Optional[str] = None
    code_name: Optional[str] = None  # U.S.C., C.F.R., etc.
    section: Optional[str] = None
    subsection: Optional[str] = None
    
    # Article/Book fields
    author: Optional[str] = None
    title: Optional[str] = None
    journal: Optional[str] = None
    book_title: Optional[str] = None
    publisher: Optional[str] = None
    volume_number: Optional[str] = None
    
    # Other metadata
    url: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    retrieval_priority: int = 1  # 1=highest, lower numbers = higher priority
    notes: Optional[str] = None


@dataclass
class ParsedFootnote:
    """Complete footnote parsing result"""
    footnote_number: int
    original_text: str
    citations: List[Citation]
    parsing_confidence: float  # 0-1 score
    gpt_reasoning: str
    parsed_at: str


class EnhancedGPTParser:
    """GPT-4o powered citation parser following legal citation standards"""
    
    def __init__(self, api_key: str = None):
        """Initialize with OpenAI API key"""
        # Try to get API key from environment if not provided
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
            self.api_available = True
        else:
            self.client = None
            self.api_available = False
            
        self.logger = logging.getLogger(__name__)
        self.action_logger = get_action_logger()
        self.retry_handler = RetryHandler(max_retries=3, base_delay=2.0)
        
        # Enhanced system prompt with detailed citation parsing requirements
        self.system_prompt = """Legal citation parser. Extract ALL citations from footnotes and parse into structured data.

CRITICAL: For CASE citations, you MUST extract these components:
- case_name: Full case name before comma (e.g., "Grunenthal GMBH v. Alkem Lab'ys Ltd.")
- volume: Number before reporter (e.g., "919")
- reporter: Reporter abbreviation (e.g., "F.3d")
- page: First page number (e.g., "1333")
- court: Court abbreviation in parentheses (e.g., "Fed. Cir.")
- year: Year in parentheses (e.g., "2019")

For STATUTE citations, extract:
- title_number: Title number (e.g., "21")
- code_name: Code name (e.g., "U.S.C.")
- section: Section reference (e.g., "355(c)(3)(C)")

Example: "Grunenthal GMBH v. Alkem Lab'ys Ltd., 919 F.3d 1333, 1339 (Fed. Cir. 2019)"
{
  "citation_id": "1",
  "citation_type": "case",
  "full_text": "Grunenthal GMBH v. Alkem Lab'ys Ltd., 919 F.3d 1333, 1339 (Fed. Cir. 2019)",
  "case_name": "Grunenthal GMBH v. Alkem Lab'ys Ltd.",
  "volume": "919",
  "reporter": "F.3d",
  "page": "1333",
  "pincite": "1339",
  "court": "Fed. Cir.",
  "year": "2019",
  "retrieval_priority": 1
}

Required JSON:
{
  "citations": [
    {
      "citation_id": "unique_id",
      "citation_type": "case|statute|regulation|article|book|website",
      "full_text": "exact citation text",
      "case_name": "REQUIRED for cases",
      "volume": "REQUIRED for cases", 
      "reporter": "REQUIRED for cases",
      "page": "REQUIRED for cases",
      "pincite": "pinpoint cite if exists",
      "court": "REQUIRED for cases",
      "year": "REQUIRED",
      "title_number": "REQUIRED for statutes",
      "code_name": "REQUIRED for statutes",
      "section": "REQUIRED for statutes",
      "author": "if article/book",
      "title": "if article/book",
      "retrieval_priority": 1
    }
  ],
  "parsing_confidence": 0.95,
  "reasoning": "brief explanation"
}

Do NOT leave case_name, volume, reporter, page, court, or year blank for case citations."""

    def _make_gpt_call(self, footnote_number: int, footnote_text: str) -> dict:
        """Make GPT API call with proper error handling"""
        if not self.api_available:
            raise Exception("OpenAI API key not configured")
        
        # Use GPT-4o model with optimized settings for minimal token usage
        response = self.client.chat.completions.create(
            model="gpt-4o",  # GPT-4o model (reliable)
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Parse this footnote #{footnote_number}:\n\n{footnote_text}"}
            ],
            max_tokens=1200,  # Optimized for GPT-4o
            temperature=0  # Deterministic responses
        )
        
        return response
    
    def parse_footnote(self, footnote_number: int, footnote_text: str) -> ParsedFootnote:
        """Parse a single footnote using GPT"""
        
        # Log the parsing attempt
        self.action_logger.log_action(
            action="PARSE_FOOTNOTE_START",
            details={
                "footnote_number": footnote_number,
                "text_length": len(footnote_text),
                "api_available": self.api_available
            }
        )
        
        try:
            # Log API request with detailed context
            log_api_usage(
                api_name="openai_gpt4o",
                endpoint="https://api.openai.com/v1/chat/completions",
                method="POST",
                parameters={"model": "gpt-4o", "footnote_number": footnote_number, "temperature": 0},
                footnote_number=footnote_number,
                citation_text=footnote_text[:100] + "...",
                call_reason=f"Parse footnote {footnote_number} to extract all citations and their metadata",
                expected_result="JSON with structured citations including types, case names, reporters, statute sections, etc.",
                citation_type="unknown_mixed",  # Footnote may contain multiple types
                retrieval_strategy="gpt_parsing",
                additional_metadata={
                    "footnote_length": len(footnote_text),
                    "parsing_mode": "comprehensive",
                    "legal_standards": "Bluebook/Redbook",
                    "max_tokens": 2000
                }
            )
            
            # Make GPT API call with retry logic
            response = self.retry_handler.execute_with_retry(
                self._make_gpt_call,
                footnote_number,
                footnote_text,
                operation_name=f"gpt_parse_footnote_{footnote_number}"
            )
            
            # Parse GPT response
            gpt_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "```json" in gpt_text:
                json_start = gpt_text.find("```json") + 7
                json_end = gpt_text.find("```", json_start)
                json_text = gpt_text[json_start:json_end].strip()
            else:
                json_text = gpt_text.strip()
            
            # Handle empty or invalid JSON
            if not json_text:
                raise ValueError("GPT returned empty response")
            
            # Parse JSON with better error handling
            try:
                parsed_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                # Log the actual GPT response for debugging
                self.logger.error(f"GPT JSON parse error. Raw response: {gpt_text[:200]}...")
                raise ValueError(f"Invalid JSON from GPT: {str(e)}")
            
            # Log success with results
            citations_found = len(parsed_data.get("citations", []))
            confidence = parsed_data.get("parsing_confidence", 0.0)
            
            log_api_usage(
                api_name="openai_gpt4o",
                endpoint="https://api.openai.com/v1/chat/completions",
                method="POST",
                response_code=200,
                success=True,
                footnote_number=footnote_number,
                call_reason=f"Parse footnote {footnote_number} to extract all citations and their metadata",
                expected_result="JSON with structured citations including types, case names, reporters, statute sections, etc.",
                citation_type="mixed_types",
                retrieval_strategy="gpt_parsing",
                additional_metadata={
                    "citations_extracted": citations_found,
                    "parsing_confidence": confidence,
                    "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None,
                    "response_format": "structured_json",
                    "gpt_reasoning_length": len(parsed_data.get("reasoning", ""))
                }
            )
            
            # Convert to Citation objects
            citations = []
            for i, cite_data in enumerate(parsed_data.get("citations", [])):
                citation = Citation(
                    citation_id=cite_data.get("citation_id", f"fn{footnote_number}_{i}"),
                    citation_type=cite_data.get("citation_type", "other"),
                    full_text=cite_data.get("full_text", ""),
                    case_name=cite_data.get("case_name"),
                    plaintiff=cite_data.get("plaintiff"),
                    defendant=cite_data.get("defendant"),
                    volume=cite_data.get("volume"),
                    reporter=cite_data.get("reporter"),
                    page=cite_data.get("page"),
                    pincite=cite_data.get("pincite"),
                    court=cite_data.get("court"),
                    year=cite_data.get("year"),
                    title_number=cite_data.get("title_number"),
                    code_name=cite_data.get("code_name"),
                    section=cite_data.get("section"),
                    subsection=cite_data.get("subsection"),
                    author=cite_data.get("author"),
                    title=cite_data.get("title"),
                    journal=cite_data.get("journal"),
                    book_title=cite_data.get("book_title"),
                    publisher=cite_data.get("publisher"),
                    volume_number=cite_data.get("volume_number"),
                    url=cite_data.get("url"),
                    doi=cite_data.get("doi"),
                    isbn=cite_data.get("isbn"),
                    retrieval_priority=cite_data.get("retrieval_priority", 1),
                    notes=cite_data.get("notes")
                )
                citations.append(citation)
            
            return ParsedFootnote(
                footnote_number=footnote_number,
                original_text=footnote_text,
                citations=citations,
                parsing_confidence=parsed_data.get("parsing_confidence", 0.8),
                gpt_reasoning=parsed_data.get("reasoning", ""),
                parsed_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            # Log error with detailed context
            self.action_logger.log_error(
                error_type="GPT_PARSING_ERROR",
                error_message=str(e),
                context={
                    "footnote_number": footnote_number,
                    "text_length": len(footnote_text)
                }
            )
            
            log_api_usage(
                api_name="openai_gpt4o",
                endpoint="https://api.openai.com/v1/chat/completions",
                method="POST",
                success=False,
                error_message=str(e),
                footnote_number=footnote_number,
                call_reason=f"Parse footnote {footnote_number} to extract all citations and their metadata",
                expected_result="JSON with structured citations including types, case names, reporters, statute sections, etc.",
                citation_type="unknown",
                retrieval_strategy="gpt_parsing",
                additional_metadata={
                    "error_type": type(e).__name__,
                    "footnote_length": len(footnote_text),
                    "parsing_attempt": "failed"
                }
            )
            
            self.logger.error(f"GPT parsing failed for footnote {footnote_number}: {e}")
            
            # Return minimal result
            return ParsedFootnote(
                footnote_number=footnote_number,
                original_text=footnote_text,
                citations=[],
                parsing_confidence=0.0,
                gpt_reasoning=f"Parsing failed: {str(e)}",
                parsed_at=datetime.now().isoformat()
            )
    
    def parse_multiple_footnotes(self, footnotes: List[tuple]) -> List[ParsedFootnote]:
        """Parse multiple footnotes"""
        results = []
        
        for footnote_number, footnote_text in footnotes:
            self.logger.info(f"Parsing footnote {footnote_number}...")
            result = self.parse_footnote(footnote_number, footnote_text)
            results.append(result)
            
            # Log progress
            self.logger.info(f"  Found {len(result.citations)} citations with confidence {result.parsing_confidence:.2f}")
        
        return results