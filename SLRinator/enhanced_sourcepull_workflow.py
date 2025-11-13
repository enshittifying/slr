#!/usr/bin/env python3
"""
Enhanced Sourcepull Workflow for Stanford Law Review
Complete workflow: DOCX → GPT parsing → PDF retrieval → Validation

Steps:
1. Extract footnotes from DOCX
2. Parse each footnote with GPT-5 to identify citations
3. Retrieve actual readable PDFs for each citation
4. Validate all files and generate report
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from src.processors.footnote_extractor import FootnoteExtractor
from src.core.enhanced_gpt_parser import EnhancedGPTParser, ParsedFootnote
from src.core.fallback_citation_parser import FallbackCitationParser
from src.core.pdf_retriever import PDFRetriever, RetrievalResult
from src.utils.api_logger import get_api_logger


class EnhancedSourcepullWorkflow:
    """Complete sourcepull workflow with GPT parsing and PDF retrieval"""
    
    def __init__(self, config_path: str = "config/api_keys.json"):
        """Initialize workflow with configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Setup logging
        self.logger = self._setup_logging()
        
        # Initialize components
        self.footnote_extractor = FootnoteExtractor()
        
        # Check for OpenAI API key
        openai_key = self.config.get("openai", {}).get("api_key")
        if not openai_key or openai_key == "YOUR_OPENAI_API_KEY_HERE":
            self.logger.warning("No OpenAI API key - GPT parsing disabled")
            self.gpt_parser = None
        else:
            self.gpt_parser = EnhancedGPTParser(openai_key)
        
        # Initialize fallback parser
        self.fallback_parser = FallbackCitationParser()
        
        # Output directories
        self.output_base = Path("output/data/Enhanced_Sourcepull")
        self.output_base.mkdir(parents=True, exist_ok=True)
        
        self.pdf_retriever = PDFRetriever(
            api_keys=self.config,
            output_dir=self.output_base / "Retrieved_PDFs"
        )
    
    def _load_config(self) -> Dict:
        """Load API configuration"""
        config_file = Path(self.config_path)
        if not config_file.exists():
            self.logger.warning(f"Config file not found: {self.config_path}")
            return {}
        
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the workflow"""
        logger = logging.getLogger("enhanced_sourcepull")
        logger.setLevel(logging.INFO)
        
        # File handler
        log_file = Path("output/logs") / f"enhanced_sourcepull_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def process_document(self, docx_path: str, footnote_range: Optional[str] = None, 
                        use_gpt: bool = True) -> Dict:
        """
        Process a complete document through the enhanced sourcepull workflow
        
        Args:
            docx_path: Path to DOCX file
            footnote_range: Optional range like "1-50" or "10,20,30"
            use_gpt: Whether to use GPT parsing (requires API key)
            
        Returns:
            Dict with workflow results
        """
        
        self.logger.info("="*70)
        self.logger.info("ENHANCED SOURCEPULL WORKFLOW")
        self.logger.info("Stanford Law Review - Readable PDF Retrieval")
        self.logger.info("="*70)
        
        start_time = datetime.now()
        results = {
            "document": docx_path,
            "started_at": start_time.isoformat(),
            "footnote_range": footnote_range,
            "used_gpt": use_gpt and self.gpt_parser is not None,
            "footnotes_processed": 0,
            "total_citations": 0,
            "successful_retrievals": 0,
            "failed_retrievals": 0,
            "pdf_files": [],
            "parsing_results": [],
            "retrieval_results": []
        }
        
        try:
            # Step 1: Extract footnotes
            self.logger.info("Step 1: Extracting footnotes from document...")
            footnotes = self.footnote_extractor.extract_from_docx(docx_path)
            
            # Filter footnotes if range specified
            if footnote_range:
                footnotes = self._filter_footnotes(footnotes, footnote_range)
            
            results["footnotes_processed"] = len(footnotes)
            self.logger.info(f"  Extracted {len(footnotes)} footnotes")
            
            # Step 2: Parse citations with GPT
            self.logger.info("Step 2: Parsing citations with GPT...")
            
            if use_gpt and self.gpt_parser:
                parsed_footnotes = []
                for footnote in footnotes:
                    self.logger.info(f"  Parsing footnote {footnote.number}...")
                    parsed = self.gpt_parser.parse_footnote(footnote.number, footnote.text)
                    
                    # If GPT fails due to quota/error, fallback to rule-based parsing
                    if len(parsed.citations) == 0 and "error" in parsed.gpt_reasoning.lower():
                        self.logger.info(f"    GPT failed, trying fallback parser...")
                        fallback_parsed = self.fallback_parser.parse_footnote(footnote.number, footnote.text)
                        if len(fallback_parsed.citations) > 0:
                            # Use fallback results but note the source
                            fallback_parsed.gpt_reasoning = f"Fallback parsing used due to GPT error: {parsed.gpt_reasoning}"
                            parsed = fallback_parsed
                            self.logger.info(f"    Fallback found {len(parsed.citations)} citations")
                    
                    parsed_footnotes.append(parsed)
                    self.logger.info(f"    Found {len(parsed.citations)} citations (confidence: {parsed.parsing_confidence:.2f})")
                    
                results["parsing_results"] = [self._parsed_footnote_to_dict(pf) for pf in parsed_footnotes]
                
            else:
                self.logger.warning("  GPT parsing disabled - using fallback rule-based parsing")
                parsed_footnotes = []
                for footnote in footnotes:
                    self.logger.info(f"  Parsing footnote {footnote.number} with fallback parser...")
                    parsed = self.fallback_parser.parse_footnote(footnote.number, footnote.text)
                    parsed_footnotes.append(parsed)
                    self.logger.info(f"    Found {len(parsed.citations)} citations (confidence: {parsed.parsing_confidence:.2f})")
                
                results["parsing_results"] = [self._parsed_footnote_to_dict(pf) for pf in parsed_footnotes]
            
            # Collect all citations
            all_citations = []
            for parsed_footnote in parsed_footnotes:
                all_citations.extend(parsed_footnote.citations)
            
            results["total_citations"] = len(all_citations)
            self.logger.info(f"  Total citations identified: {len(all_citations)}")
            
            # Step 3: Retrieve PDFs
            self.logger.info("Step 3: Retrieving readable PDFs...")
            
            retrieval_results = []
            for citation in all_citations:
                self.logger.info(f"  Retrieving: {citation.citation_id}")
                retrieval_result = self.pdf_retriever.retrieve_citation(citation)
                retrieval_results.append(retrieval_result)
                
                # Accept PDFs for cases, or any successful file for statutes
                if retrieval_result.success and (retrieval_result.is_valid_pdf or citation.citation_type == 'statute'):
                    results["successful_retrievals"] += 1
                    
                    file_type = "PDF" if retrieval_result.is_valid_pdf else "text"
                    results["pdf_files"].append({
                        "citation_id": citation.citation_id,
                        "file_path": retrieval_result.file_path,
                        "source": retrieval_result.source_name,
                        "pages": retrieval_result.page_count,
                        "size_mb": round(retrieval_result.file_size_bytes / 1024 / 1024, 2) if retrieval_result.file_size_bytes else 0
                    })
                    
                    if retrieval_result.is_valid_pdf:
                        self.logger.info(f"    ✓ Retrieved {retrieval_result.page_count}p PDF from {retrieval_result.source_name}")
                    else:
                        self.logger.info(f"    ✓ Retrieved {file_type} file from {retrieval_result.source_name}")
                else:
                    results["failed_retrievals"] += 1
                    self.logger.info(f"    ✗ Failed: {retrieval_result.error_message}")
            
            results["retrieval_results"] = [self._retrieval_result_to_dict(rr) for rr in retrieval_results]
            
            # Step 4: Generate final report
            self.logger.info("Step 4: Generating final report...")
            
            end_time = datetime.now()
            results["completed_at"] = end_time.isoformat()
            results["duration_seconds"] = (end_time - start_time).total_seconds()
            results["success_rate"] = (results["successful_retrievals"] / max(results["total_citations"], 1)) * 100
            
            # Save comprehensive report
            report_path = self.output_base / f"enhanced_sourcepull_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            results["report_path"] = str(report_path)
            
            # Summary
            self.logger.info("="*70)
            self.logger.info("WORKFLOW COMPLETE")
            self.logger.info("="*70)
            self.logger.info(f"Footnotes processed: {results['footnotes_processed']}")
            self.logger.info(f"Citations identified: {results['total_citations']}")
            self.logger.info(f"PDFs retrieved: {results['successful_retrievals']}/{results['total_citations']}")
            self.logger.info(f"Success rate: {results['success_rate']:.1f}%")
            self.logger.info(f"Report saved: {report_path}")
            self.logger.info("="*70)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {e}")
            results["error"] = str(e)
            results["completed_at"] = datetime.now().isoformat()
            return results
    
    def _filter_footnotes(self, footnotes, range_str: str):
        """Filter footnotes by range specification"""
        target_numbers = set()
        
        for part in range_str.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                target_numbers.update(range(start, end + 1))
            else:
                target_numbers.add(int(part))
        
        return [fn for fn in footnotes if fn.number in target_numbers]
    
    def _basic_citation_extraction(self, footnotes):
        """Basic citation extraction when GPT is not available"""
        # Simplified fallback - just return empty citations
        from src.core.enhanced_gpt_parser import ParsedFootnote
        
        results = []
        for footnote in footnotes:
            parsed = ParsedFootnote(
                footnote_number=footnote.number,
                original_text=footnote.text,
                citations=[],  # No citations extracted
                parsing_confidence=0.0,
                gpt_reasoning="GPT parsing disabled",
                parsed_at=datetime.now().isoformat()
            )
            results.append(parsed)
        
        return results
    
    def _parsed_footnote_to_dict(self, pf: ParsedFootnote) -> Dict:
        """Convert ParsedFootnote to dict for JSON serialization"""
        return {
            "footnote_number": pf.footnote_number,
            "original_text": pf.original_text[:200] + "..." if len(pf.original_text) > 200 else pf.original_text,
            "citations_count": len(pf.citations),
            "parsing_confidence": pf.parsing_confidence,
            "gpt_reasoning": pf.gpt_reasoning,
            "parsed_at": pf.parsed_at,
            "citations": [
                {
                    "citation_id": c.citation_id,
                    "type": c.citation_type,
                    "full_text": c.full_text,
                    "retrieval_priority": c.retrieval_priority
                } for c in pf.citations
            ]
        }
    
    def _retrieval_result_to_dict(self, rr: RetrievalResult) -> Dict:
        """Convert RetrievalResult to dict for JSON serialization"""
        return {
            "citation_id": rr.citation_id,
            "source_name": rr.source_name,
            "success": rr.success,
            "file_path": rr.file_path,
            "file_size_bytes": rr.file_size_bytes,
            "is_valid_pdf": rr.is_valid_pdf,
            "page_count": rr.page_count,
            "error_message": rr.error_message,
            "retrieval_url": rr.retrieval_url,
            "retrieved_at": rr.retrieved_at
        }


def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(description='Enhanced Sourcepull Workflow')
    parser.add_argument('docx_file', help='Path to DOCX file')
    parser.add_argument('--footnotes', help='Footnote range (e.g., "1-50" or "1,5,10")')
    parser.add_argument('--no-gpt', action='store_true', help='Disable GPT parsing')
    parser.add_argument('--config', default='config/api_keys.json', help='Config file path')
    
    args = parser.parse_args()
    
    # Initialize workflow
    workflow = EnhancedSourcepullWorkflow(config_path=args.config)
    
    # Process document
    results = workflow.process_document(
        docx_path=args.docx_file,
        footnote_range=args.footnotes,
        use_gpt=not args.no_gpt
    )
    
    # Print summary
    print(f"\\n✅ Workflow complete!")
    print(f"Report: {results.get('report_path', 'N/A')}")
    if results.get('successful_retrievals', 0) > 0:
        print(f"📄 {results['successful_retrievals']} readable PDFs retrieved")
    
    return 0 if not results.get('error') else 1


if __name__ == "__main__":
    exit(main())