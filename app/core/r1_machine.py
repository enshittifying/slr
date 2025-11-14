"""
R1 Machine - PDF preparation and redboxing
Uses SLRinator redboxer for automated highlighting
"""
import sys
from pathlib import Path
import logging
from typing import List, Dict, Callable, Optional
import fitz

# Add SLRinator to path
slrinator_path = Path(__file__).parent.parent.parent / "SLRinator"
sys.path.insert(0, str(slrinator_path))

from src.processors.redboxer import SmartRedboxer
from src.core.retrieval_framework import SourceClassifier

logger = logging.getLogger(__name__)


class R1Machine:
    """
    R1 Preparation Machine
    Cleans PDFs and applies redboxing to highlight citation elements
    """

    def __init__(self, sheets_client, drive_client, cache_dir: str = None):
        """
        Initialize R1 Machine

        Args:
            sheets_client: Google Sheets client
            drive_client: Google Drive client
            cache_dir: Directory for caching
        """
        self.sheets = sheets_client
        self.drive = drive_client
        self.cache_dir = Path(cache_dir or "cache/r1")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SLRinator redboxer
        self.redboxer = SmartRedboxer()
        self.classifier = SourceClassifier()

    def process_article(self, article_id: str,
                       progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Process all sources for R1 preparation

        Args:
            article_id: Article identifier
            progress_callback: Callback function(current, total, message)
        """
        logger.info(f"Starting R1 processing for article: {article_id}")

        # Get sources from Google Sheets
        sources = self.sheets.get_sources_for_article(article_id)

        # Filter to only sources that have been downloaded
        sources_to_process = [s for s in sources if s['status'] == 'downloaded' and s['drive_link']]
        total = len(sources_to_process)

        logger.info(f"Found {total} sources ready for R1 processing")

        success_count = 0
        fail_count = 0

        for i, source in enumerate(sources_to_process):
            source_id = source['source_id']
            citation = source['citation']

            try:
                if progress_callback:
                    progress_callback(i, total, f"Processing {citation[:50]}...")

                # Check if already processed
                cached_path = self.cache_dir / f"{source_id}_R1.pdf"
                if cached_path.exists():
                    logger.info(f"R1 for {source_id} already cached")
                    if progress_callback:
                        progress_callback(i+1, total, f"Skipped (cached): {source_id}")
                    success_count += 1
                    continue

                # Download raw PDF from Drive
                raw_pdf_path = self.drive.download_file(file_link=source['drive_link'])

                # Clean PDF (remove cover pages, etc.)
                cleaned_path = self.clean_pdf(raw_pdf_path, source['type'])

                # Apply redboxing
                r1_pdf_path = self.redbox_citation_metadata(
                    cleaned_path,
                    citation,
                    source['type'],
                    source_id
                )

                # Upload to Drive
                file_id = self.drive.upload_r1_pdf(
                    r1_pdf_path,
                    source_id,
                    article_id
                )

                r1_drive_link = self.drive.get_file_link(file_id)

                # Update Sheet
                self.sheets.update_r1_status(
                    source_id,
                    status='r1_complete',
                    r1_drive_link=r1_drive_link
                )

                # Cache locally
                if not cached_path.exists():
                    import shutil
                    shutil.copy(r1_pdf_path, cached_path)

                success_count += 1
                logger.info(f"Successfully processed R1 for {source_id}")

                if progress_callback:
                    progress_callback(i+1, total, f"Completed: {source_id}")

                # Clean up temp files
                try:
                    Path(raw_pdf_path).unlink(missing_ok=True)
                    Path(cleaned_path).unlink(missing_ok=True)
                    if r1_pdf_path != cached_path:
                        Path(r1_pdf_path).unlink(missing_ok=True)
                except:
                    pass

            except Exception as e:
                fail_count += 1
                error_msg = str(e)

                logger.error(f"Error processing R1 for {source_id}: {e}", exc_info=True)

                # Update Sheet with error
                try:
                    self.sheets.update_r1_status(
                        source_id,
                        status='r1_error',
                        error_message=error_msg
                    )
                except Exception as sheet_error:
                    logger.error(f"Failed to update sheet: {sheet_error}")

                if progress_callback:
                    progress_callback(i+1, total, f"Error: {source_id}")

        logger.info(f"R1 complete for {article_id}: {success_count} succeeded, {fail_count} failed")

        # Update article stage
        if fail_count == 0:
            self.sheets.update_article_stage(article_id, 'r1_complete')
        else:
            self.sheets.update_article_stage(article_id, 'r1_complete_with_errors')

        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'total': total
        }

    def clean_pdf(self, pdf_path: str, source_type: str) -> str:
        """
        Remove extraneous pages from PDF

        Args:
            pdf_path: Path to PDF
            source_type: Type of source (case, statute, etc.)

        Returns:
            Path to cleaned PDF
        """
        doc = fitz.open(pdf_path)
        pdf_name = Path(pdf_path).stem

        # HeinOnline PDFs have cover page - remove first page
        if 'hein' in pdf_name.lower() or source_type == 'case':
            if len(doc) > 1:
                doc.delete_page(0)
                logger.debug(f"Removed HeinOnline cover page from {pdf_name}")

        # Westlaw PDFs have header - remove first 2 pages
        if 'westlaw' in pdf_name.lower():
            pages_to_remove = min(2, len(doc) - 1)
            for _ in range(pages_to_remove):
                if len(doc) > 1:
                    doc.delete_page(0)
            logger.debug(f"Removed Westlaw header pages from {pdf_name}")

        output_path = pdf_path.replace('.pdf', '_cleaned.pdf')
        doc.save(output_path)
        doc.close()

        return output_path

    def redbox_citation_metadata(self, pdf_path: str, citation: str,
                                source_type: str, source_id: str) -> str:
        """
        Draw red boxes around citation elements using SLRinator redboxer

        Args:
            pdf_path: Path to cleaned PDF
            citation: Citation text
            source_type: Type of source
            source_id: Source identifier

        Returns:
            Path to redboxed PDF
        """
        output_path = self.cache_dir / f"{source_id}_R1.pdf"

        try:
            # Classify citation to get components
            _, components = self.classifier.classify(citation)

            # Map source type to redboxer format
            citation_type_map = {
                'case': 'case',
                'statute': 'statute',
                'article': 'article',
                'book': 'book',
                'regulation': 'regulation'
            }

            redbox_type = citation_type_map.get(source_type, 'case')

            # Prepare citation data for redboxer
            citation_data = self._prepare_citation_data(components, redbox_type)

            # Apply redboxing
            self.redboxer.redbox_citation(
                input_path=pdf_path,
                output_path=str(output_path),
                citation_type=redbox_type,
                citation_data=citation_data
            )

            logger.info(f"Applied redboxing to {source_id}")

        except Exception as e:
            logger.warning(f"Redboxing failed for {source_id}, using cleaned PDF: {e}")
            # If redboxing fails, just use the cleaned PDF
            import shutil
            shutil.copy(pdf_path, output_path)

        return str(output_path)

    def _prepare_citation_data(self, components: Dict, citation_type: str) -> Dict:
        """
        Prepare citation data for redboxer

        Args:
            components: Parsed citation components
            citation_type: Type of citation

        Returns:
            Dict formatted for redboxer
        """
        data = {}

        if citation_type == 'case':
            data = {
                'party1': components.get('plaintiff', ''),
                'party2': components.get('defendant', ''),
                'volume': components.get('volume', ''),
                'reporter': components.get('reporter', ''),
                'page': components.get('page', ''),
                'year': components.get('year', '')
            }
        elif citation_type == 'statute':
            data = {
                'title': components.get('title', ''),
                'code': components.get('code', ''),
                'section': components.get('section', ''),
                'year': components.get('year', '')
            }
        elif citation_type == 'article':
            data = {
                'author': components.get('author', ''),
                'title': components.get('title', ''),
                'journal': components.get('journal', ''),
                'volume': components.get('volume', ''),
                'page': components.get('page', ''),
                'year': components.get('year', '')
            }
        elif citation_type == 'book':
            data = {
                'author': components.get('author', ''),
                'title': components.get('title', ''),
                'year': components.get('year', ''),
                'publisher': components.get('publisher', '')
            }

        return data

    def get_cache_status(self, article_id: str) -> Dict:
        """
        Get R1 cache status for article

        Args:
            article_id: Article identifier

        Returns:
            Dict with cache statistics
        """
        sources = self.sheets.get_sources_for_article(article_id)
        cached_count = 0

        for source in sources:
            source_id = source['source_id']
            cached_path = self.cache_dir / f"{source_id}_R1.pdf"
            if cached_path.exists():
                cached_count += 1

        return {
            'total': len(sources),
            'cached': cached_count,
            'pending': len(sources) - cached_count
        }
