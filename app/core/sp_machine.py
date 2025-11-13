"""
Source Pull Machine - wraps SLRinator functionality for desktop app
"""
import sys
from pathlib import Path
import logging
from typing import List, Dict, Callable, Optional

# Add SLRinator to path
slrinator_path = Path(__file__).parent.parent.parent / "SLRinator"
sys.path.insert(0, str(slrinator_path))

from src.retrievers.unified_retriever import SourceRetriever
from src.core.retrieval_framework import SourceClassifier
from src.processors.footnote_extractor import FootnoteExtractor

logger = logging.getLogger(__name__)


class SPMachine:
    """
    Source Pull Machine
    Wraps SLRinator source retrieval functionality with progress callbacks
    """

    def __init__(self, sheets_client, drive_client, cache_dir: str = None):
        """
        Initialize SP Machine

        Args:
            sheets_client: Google Sheets client
            drive_client: Google Drive client
            cache_dir: Directory for caching
        """
        self.sheets = sheets_client
        self.drive = drive_client
        self.cache_dir = Path(cache_dir or "cache/sp")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SLRinator components
        self.retriever = SourceRetriever()
        self.classifier = SourceClassifier()
        self.footnote_extractor = FootnoteExtractor()

    def process_article(self, article_id: str,
                       progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Process all sources for an article

        Args:
            article_id: Article identifier
            progress_callback: Callback function(current, total, message)
        """
        logger.info(f"Starting SP processing for article: {article_id}")

        # Get sources from Google Sheets
        sources = self.sheets.get_sources_for_article(article_id)
        total = len(sources)

        logger.info(f"Found {total} sources to process")

        success_count = 0
        fail_count = 0

        for i, source in enumerate(sources):
            source_id = source['source_id']
            citation = source['citation']

            try:
                if progress_callback:
                    progress_callback(i, total, f"Processing {citation[:50]}...")

                # Check if already processed
                cached_path = self.cache_dir / f"{source_id}.pdf"
                if cached_path.exists():
                    logger.info(f"Source {source_id} already cached")
                    if progress_callback:
                        progress_callback(i+1, total, f"Skipped (cached): {source_id}")
                    success_count += 1
                    continue

                # Classify citation
                source_type, components = self.classifier.classify(citation)
                logger.info(f"Classified as {source_type}: {citation[:50]}...")

                # Retrieve PDF
                pdf_path = self.retriever.retrieve_source(
                    footnote_num=int(source['footnote_num']) if source['footnote_num'] else i+1,
                    citation_text=citation
                )

                if pdf_path and Path(pdf_path).exists():
                    # Upload to Drive
                    file_id = self.drive.upload_source_pdf(
                        pdf_path,
                        source_id,
                        article_id
                    )

                    drive_link = self.drive.get_file_link(file_id)

                    # Update Sheet
                    self.sheets.update_source_status(
                        source_id,
                        status='downloaded',
                        drive_link=drive_link
                    )

                    # Cache locally
                    if not cached_path.exists():
                        import shutil
                        shutil.copy(pdf_path, cached_path)

                    success_count += 1
                    logger.info(f"Successfully processed {source_id}")

                    if progress_callback:
                        progress_callback(i+1, total, f"Completed: {source_id}")

                else:
                    # Failed to retrieve
                    fail_count += 1
                    error_msg = "PDF retrieval failed"

                    self.sheets.update_source_status(
                        source_id,
                        status='error',
                        error_message=error_msg
                    )

                    logger.error(f"Failed to retrieve {source_id}: {error_msg}")

                    if progress_callback:
                        progress_callback(i+1, total, f"Failed: {source_id}")

            except Exception as e:
                fail_count += 1
                error_msg = str(e)

                logger.error(f"Error processing {source_id}: {e}", exc_info=True)

                # Update Sheet with error
                try:
                    self.sheets.update_source_status(
                        source_id,
                        status='error',
                        error_message=error_msg
                    )
                except Exception as sheet_error:
                    logger.error(f"Failed to update sheet: {sheet_error}")

                if progress_callback:
                    progress_callback(i+1, total, f"Error: {source_id}")

        logger.info(f"SP complete for {article_id}: {success_count} succeeded, {fail_count} failed")

        # Update article stage
        if fail_count == 0:
            self.sheets.update_article_stage(article_id, 'sp_complete')
        else:
            self.sheets.update_article_stage(article_id, 'sp_complete_with_errors')

        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'total': total
        }

    def process_from_document(self, document_path: str, article_id: str,
                             footnote_range: str = None,
                             progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Process sources extracted from a Word document

        Args:
            document_path: Path to Word document
            article_id: Article identifier
            footnote_range: Optional range like "1-50"
            progress_callback: Progress callback function
        """
        logger.info(f"Extracting footnotes from {document_path}")

        # Extract footnotes
        footnotes = self.footnote_extractor.extract_from_docx(
            document_path,
            range_filter=footnote_range
        )

        logger.info(f"Extracted {len(footnotes)} footnotes")

        # For now, just process existing sources from Sheet
        # TODO: Could create sources from extracted footnotes if not in sheet
        return self.process_article(article_id, progress_callback)

    def get_cache_status(self, article_id: str) -> Dict:
        """
        Get cache status for article sources

        Args:
            article_id: Article identifier

        Returns:
            Dict with cache statistics
        """
        sources = self.sheets.get_sources_for_article(article_id)
        cached_count = 0

        for source in sources:
            source_id = source['source_id']
            cached_path = self.cache_dir / f"{source_id}.pdf"
            if cached_path.exists():
                cached_count += 1

        return {
            'total': len(sources),
            'cached': cached_count,
            'pending': len(sources) - cached_count
        }
