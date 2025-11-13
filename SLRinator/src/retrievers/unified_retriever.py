#!/usr/bin/env python3
"""
Unified Source Retriever for Stanford Law Review
Implements actual retrieval from various databases following Member Handbook hierarchy
"""

import os
import time
import requests
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass
import PyPDF2

# Import our framework
from src.core.retrieval_framework import (
    SourceType, RetrievalSource, RetrievalPriority,
    RetrievalAttempt, RetrievalRecord, CitationComponents,
    SourceClassifier, RetrievalStrategy, RetrievalEngine
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SourceRetriever:
    """
    Unified retriever that attempts to get sources from multiple databases
    following the Member Handbook hierarchy
    """
    
    def __init__(self, output_dir: str = "output/data/Sourcepull"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        self.engine = RetrievalEngine()
        self.retrieved_dir = self.output_dir / "Retrieved"
        self.retrieved_dir.mkdir(exist_ok=True)
        
        # Track all retrieval attempts
        self.retrieval_log = []
    
    def retrieve_source(self, footnote_number: int, citation_text: str) -> Optional[str]:
        """
        Main retrieval method that follows the systematic hierarchy
        Returns: Path to retrieved PDF or None
        """
        # Process through the engine to get classification and strategy
        record = self.engine.process_footnote(footnote_number, citation_text)
        
        # Get retrieval strategies in order
        strategies = self.engine.strategy.get_retrieval_order(record.citation.type)
        
        logger.info(f"Attempting retrieval for FN{footnote_number}: {record.citation.type.name}")
        
        # Try each strategy in order
        for source, priority, reasoning in strategies:
            logger.info(f"  Trying {source.value}: {reasoning}")
            
            attempt = RetrievalAttempt(
                source=source,
                timestamp=datetime.now(),
                success=False,
                priority=priority,
                reasoning=reasoning
            )
            
            # Route to appropriate retrieval method
            file_path = None
            
            if source == RetrievalSource.GOVINFO:
                file_path = self._retrieve_from_govinfo(record.citation)
            elif source == RetrievalSource.SUPREMECOURT_GOV:
                file_path = self._retrieve_from_supremecourt(record.citation)
            elif source == RetrievalSource.COURTLISTENER:
                file_path = self._retrieve_from_courtlistener(record.citation)
            elif source == RetrievalSource.CORNELL_LAW:
                file_path = self._retrieve_from_cornell(record.citation)
            elif source == RetrievalSource.AUTHOR_PROVIDED:
                file_path = self._check_author_provided(record.citation)
            # Add more sources as needed
            
            if file_path and Path(file_path).exists():
                # Validate it's actually a PDF
                if self._validate_pdf(file_path):
                    attempt.success = True
                    attempt.file_path = file_path
                    record.add_attempt(attempt)
                    
                    # Generate proper filename
                    final_path = self._generate_filename(footnote_number, record.citation)
                    if file_path != final_path:
                        Path(file_path).rename(final_path)
                        attempt.file_path = str(final_path)
                    
                    logger.info(f"  ✅ Success: Retrieved from {source.value}")
                    
                    # Save to retrieval log
                    self._update_retrieval_log(record)
                    return str(final_path)
                else:
                    attempt.error_message = "Retrieved file is not a valid PDF"
                    logger.warning(f"  ⚠️ Invalid PDF from {source.value}")
            else:
                attempt.error_message = "Could not retrieve from this source"
            
            record.add_attempt(attempt)
            time.sleep(0.5)  # Be respectful between attempts
        
        # All attempts failed
        record.final_status = "failed"
        record.notes.append(f"Failed after {len(record.attempts)} attempts")
        self._update_retrieval_log(record)
        
        logger.error(f"  ❌ Failed to retrieve FN{footnote_number}")
        return None
    
    def _retrieve_from_govinfo(self, citation: CitationComponents) -> Optional[str]:
        """Retrieve from GovInfo (for statutes and regulations)"""
        if citation.type == SourceType.STATUTE_FEDERAL and citation.title and citation.section:
            # Construct GovInfo URL for U.S. Code
            base_url = "https://www.govinfo.gov/content/pkg/USCODE-2018-title{}/pdf/USCODE-2018-title{}-chap{}-sec{}.pdf"
            
            # This is simplified - real implementation would need proper chapter mapping
            try:
                # Try to download
                url = f"https://www.govinfo.gov/content/pkg/USCODE-2018-title{citation.title}/pdf/"
                temp_file = self.retrieved_dir / f"temp_{citation.title}_{citation.section}.pdf"
                
                response = self.session.get(url, timeout=30)
                if response.status_code == 200 and 'pdf' in response.headers.get('content-type', '').lower():
                    with open(temp_file, 'wb') as f:
                        f.write(response.content)
                    return str(temp_file)
            except Exception as e:
                logger.debug(f"GovInfo retrieval failed: {e}")
        
        return None
    
    def _retrieve_from_supremecourt(self, citation: CitationComponents) -> Optional[str]:
        """Retrieve from supremecourt.gov"""
        if citation.type == SourceType.CASE and citation.volume and citation.reporter == "U.S.":
            # Map to Supreme Court website format
            # This would need a proper mapping database
            if citation.year and int(citation.year) >= 2000:
                # Modern cases have predictable URLs
                term_year = int(citation.year) - 1
                # Simplified - would need actual docket number mapping
                temp_file = self.retrieved_dir / f"temp_scotus_{citation.volume}_{citation.page}.pdf"
                
                # Try common patterns
                for suffix in ['_1', '_2', '']:
                    url = f"https://www.supremecourt.gov/opinions/{term_year % 100:02d}pdf/##-#####{suffix}.pdf"
                    # This is placeholder - would need actual mapping
                    logger.debug(f"Would try: {url}")
        
        return None
    
    def _retrieve_from_courtlistener(self, citation: CitationComponents) -> Optional[str]:
        """Retrieve from CourtListener"""
        # This would integrate with the courtlistener_retriever.py we created earlier
        if citation.type == SourceType.CASE:
            # Import and use the CourtListener retriever
            try:
                from courtlistener_retriever import CourtListenerRetriever
                cl = CourtListenerRetriever()
                
                # Search by citation
                results = cl.search_by_citation(
                    f"{citation.volume} {citation.reporter} {citation.page}"
                )
                
                if results:
                    # Get the PDF
                    pdf_content = cl.get_opinion_pdf(results[0]['id'])
                    if pdf_content:
                        temp_file = self.retrieved_dir / f"temp_cl_{citation.volume}_{citation.reporter}_{citation.page}.pdf"
                        with open(temp_file, 'wb') as f:
                            f.write(pdf_content)
                        return str(temp_file)
            except Exception as e:
                logger.debug(f"CourtListener retrieval failed: {e}")
        
        return None
    
    def _retrieve_from_cornell(self, citation: CitationComponents) -> Optional[str]:
        """Retrieve from Cornell Law"""
        if citation.type == SourceType.STATUTE_FEDERAL and citation.title:
            # Cornell has U.S. Code in a specific format
            base_url = f"https://www.law.cornell.edu/uscode/text/{citation.title}"
            if citation.section:
                base_url += f"/{citation.section}"
            
            # Cornell typically provides HTML, not PDF
            # Would need to convert or find their PDF endpoint
            logger.debug(f"Cornell URL would be: {base_url}")
        
        return None
    
    def _check_author_provided(self, citation: CitationComponents) -> Optional[str]:
        """Check if author provided the source"""
        author_dir = self.output_dir.parent / "Sources from Author"
        if author_dir.exists():
            # Search for files matching the citation
            for file in author_dir.glob("*.pdf"):
                # Simple matching - could be more sophisticated
                if citation.party1 and citation.party1.lower() in file.name.lower():
                    return str(file)
                if citation.title and citation.title in file.name:
                    return str(file)
        
        return None
    
    def _validate_pdf(self, file_path: str) -> bool:
        """Validate that a file is actually a PDF"""
        try:
            with open(file_path, 'rb') as f:
                # Check PDF header
                header = f.read(5)
                if header != b'%PDF-':
                    return False
                
                # Try to open with PyPDF2
                try:
                    PyPDF2.PdfReader(file_path)
                    return True
                except:
                    return False
        except:
            return False
    
    def _generate_filename(self, footnote_number: int, citation: CitationComponents) -> Path:
        """Generate standardized filename following SLR conventions"""
        # Format: SP-###-ShortName.pdf
        
        # Generate short name based on citation type
        short_name = ""
        
        if citation.type == SourceType.CASE:
            if citation.party1 and citation.party2:
                # Clean party names
                p1 = re.sub(r'[^\w\s]', '', citation.party1)[:20]
                p2 = re.sub(r'[^\w\s]', '', citation.party2)[:20]
                short_name = f"{p1}_v_{p2}"
            elif citation.party1:
                short_name = re.sub(r'[^\w\s]', '', citation.party1)[:30]
        
        elif citation.type == SourceType.STATUTE_FEDERAL:
            short_name = f"{citation.title}USC{citation.section}"
        
        elif citation.type == SourceType.JOURNAL_ARTICLE:
            if citation.author:
                author_last = citation.author.split()[-1] if citation.author else "Unknown"
                short_name = re.sub(r'[^\w]', '', author_last)[:20]
        
        else:
            # Fallback to first few words
            words = citation.raw_text.split()[:3]
            short_name = '_'.join(words)
        
        # Clean filename
        short_name = re.sub(r'[^\w\-_]', '_', short_name)
        
        filename = f"SP-{footnote_number:03d}-{short_name}.pdf"
        return self.retrieved_dir / filename
    
    def _update_retrieval_log(self, record: RetrievalRecord):
        """Update the retrieval log"""
        self.retrieval_log.append(record)
        
        # Save to JSON
        log_file = self.output_dir / "retrieval_log.json"
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'total_attempts': len(self.retrieval_log),
            'successful': sum(1 for r in self.retrieval_log if r.final_status == 'success'),
            'failed': sum(1 for r in self.retrieval_log if r.final_status == 'failed'),
            'records': [r.to_dict() for r in self.retrieval_log]
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def generate_sourcepull_report(self) -> str:
        """Generate a report of all retrieval attempts"""
        report = []
        report.append("="*80)
        report.append("STANFORD LAW REVIEW - SOURCEPULL RETRIEVAL REPORT")
        report.append("="*80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Statistics
        total = len(self.retrieval_log)
        successful = sum(1 for r in self.retrieval_log if r.final_status == 'success')
        failed = total - successful
        
        report.append(f"Total Footnotes Processed: {total}")
        report.append(f"Successfully Retrieved: {successful} ({successful/total*100:.1f}%)")
        report.append(f"Failed Retrievals: {failed} ({failed/total*100:.1f}%)")
        report.append("")
        
        # Breakdown by source type
        report.append("BY SOURCE TYPE:")
        type_counts = {}
        for record in self.retrieval_log:
            source_type = record.citation.type.name
            if source_type not in type_counts:
                type_counts[source_type] = {'total': 0, 'success': 0}
            type_counts[source_type]['total'] += 1
            if record.final_status == 'success':
                type_counts[source_type]['success'] += 1
        
        for stype, counts in sorted(type_counts.items()):
            success_rate = counts['success'] / counts['total'] * 100
            report.append(f"  {stype}: {counts['success']}/{counts['total']} ({success_rate:.1f}%)")
        
        report.append("")
        report.append("RETRIEVAL SOURCES USED:")
        source_counts = {}
        for record in self.retrieval_log:
            for attempt in record.attempts:
                if attempt.success:
                    source = attempt.source.value
                    source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {source}: {count} successful retrievals")
        
        report.append("")
        report.append("FAILED RETRIEVALS:")
        for record in self.retrieval_log:
            if record.final_status == 'failed':
                report.append(f"  FN{record.footnote_number}: {record.citation.raw_text[:60]}...")
                report.append(f"    Attempted sources: {', '.join([a.source.value for a in record.attempts])}")
        
        report_text = '\n'.join(report)
        
        # Save report
        report_file = self.output_dir / "sourcepull_report.txt"
        with open(report_file, 'w') as f:
            f.write(report_text)
        
        return report_text


def main():
    """Test the unified retriever"""
    retriever = SourceRetriever()
    
    # Test with Sherkow & Gugliuzza footnotes
    from footnote_processor import SHERKOW_GUGLIUZZA_FOOTNOTES
    
    print("\nTesting Unified Source Retriever")
    print("="*60)
    
    # Test first 5 footnotes
    for i, footnote in enumerate(SHERKOW_GUGLIUZZA_FOOTNOTES[:5], 1):
        print(f"\nFootnote {i}: {footnote[:50]}...")
        result = retriever.retrieve_source(i, footnote)
        if result:
            print(f"  ✅ Retrieved: {Path(result).name}")
        else:
            print(f"  ❌ Failed to retrieve")
    
    # Generate report
    print("\n" + retriever.generate_sourcepull_report())


if __name__ == "__main__":
    main()