"""
Main pipeline orchestrator for R2 citecheck automation.
"""
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
import re
import fitz  # PyMuPDF
import pandas as pd
from docx import Document
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init
from datetime import datetime

# Initialize colorama for colored terminal output
colorama_init(autoreset=True)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import settings
from src.llm_interface import LLMInterface
from src.pdf_processor import process_r1_pdf
from src.citation_parser import CitationParser
from src.citation_validator import CitationValidator
from src.support_checker import SupportChecker
from src.quote_verifier import QuoteVerifier
from src.r2_generator import R2Generator
from src.spreadsheet_updater import SpreadsheetUpdater
from src.markdown_utils import normalize_markdown_spacing
from src.word_editor import WordEditor

# Setup logging
log_file_path = settings.LOG_DIR / "pipeline.log"
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file_path)
    ]
)

logger = logging.getLogger(__name__)

def _parse_footnote_range(range_str: str) -> List[int]:
    """Parses a footnote range string (e.g., '89-100,130') into a list of integers."""
    if not range_str:
        return []

    footnote_numbers = set()
    parts = range_str.split(',')
    for part in parts:
        if '-' in part:
            start_str, end_str = part.split('-')
            try:
                start = int(start_str.strip())
                end = int(end_str.strip())
                footnote_numbers.update(range(start, end + 1))
            except ValueError:
                logger.warning(f"Invalid range part: {part}. Skipping.")
        else:
            try:
                footnote_numbers.add(int(part.strip()))
            except ValueError:
                logger.warning(f"Invalid single footnote number: {part}. Skipping.")
    return sorted(list(footnote_numbers))

class R2Pipeline:
    """Main class to orchestrate the R2 citecheck pipeline."""
    
    def __init__(self, batch_name: Optional[str] = None):
        self.llm = LLMInterface()
        self.citation_validator = CitationValidator(self.llm)
        self.support_checker = SupportChecker(self.llm)
        self.quote_verifier = QuoteVerifier()
        self.word_editor = WordEditor(settings.WORD_DOC_PATH)
        self.spreadsheet_updater = SpreadsheetUpdater(settings.SPREADSHEET_PATH)

        # Set batch name (manual or auto-generated)
        if batch_name:
            self.batch_name = batch_name
        else:
            # Auto-generate from timestamp
            self.batch_name = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.batch_timestamp = datetime.now().isoformat()

        self.human_review_queue = []
        self.full_log = []
    

    def _extract_citations_from_word(self, target_footnotes: List[int] = None) -> List[Dict]:
        """Extract footnotes and parse them into citations.

        Args:
            target_footnotes: A list of specific footnote numbers to extract.
                              If None, all footnotes are extracted.
        """
        logger.info("Extracting footnotes from Word document...")

        doc = Document(settings.WORD_DOC_PATH)
        all_citations = []

        # Access footnotes through XML structure
        try:
            from docx.oxml import parse_xml
            from docx.opc.constants import RELATIONSHIP_TYPE as RT

            # Get the footnotes part through relationships
            doc_part = doc.part
            footnotes_part = None

            for rel in doc_part.rels.values():
                if "footnotes" in rel.target_ref:
                    footnotes_part = rel.target_part
                    break

            if footnotes_part:
                # Parse footnotes XML
                footnotes_xml = footnotes_part.blob
                from lxml import etree
                root = etree.fromstring(footnotes_xml)

                # Define namespace
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}

                # Find all footnote elements
                for footnote in root.findall('.//w:footnote', ns):
                    fn_id = footnote.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')

                    if fn_id is None:
                        continue

                    # Word XML IDs are off-by-one from displayed footnote numbers
                    # Displayed footnote number = XML ID - 1
                    footnote_num = int(fn_id) - 1

                    # Skip if not in target list
                    if target_footnotes and footnote_num not in target_footnotes:
                        continue

                    # Extract text from all paragraphs in this footnote WITH formatting
                    footnote_text = ""
                    for para in footnote.findall('.//w:p', ns):
                        para_text = []
                        for run in para.findall('.//w:r', ns):
                            # Check for formatting
                            rPr = run.find('./w:rPr', ns)
                            is_italic = False
                            is_bold = False
                            is_smallcaps = False

                            if rPr is not None:
                                is_italic = rPr.find('./w:i', ns) is not None
                                is_bold = rPr.find('./w:b', ns) is not None
                                is_smallcaps = rPr.find('./w:smallCaps', ns) is not None

                            # Get text and apply formatting markers
                            for text_elem in run.findall('.//w:t', ns):
                                if text_elem.text:
                                    text = text_elem.text
                                    if is_italic:
                                        text = f"*{text}*"
                                    if is_bold:
                                        text = f"**{text}**"
                                    if is_smallcaps:
                                        text = f"[SC]{text}[/SC]"
                                    para_text.append(text)

                        footnote_text += ''.join(para_text) + " "

                    if footnote_text.strip():
                        # Normalize markdown spacing (move spaces outside formatting markers)
                        footnote_text = normalize_markdown_spacing(footnote_text.strip())
                        logger.debug(f"DEBUG: Extracted raw footnote {footnote_num} text: {footnote_text[:200]}...")
                        parser = CitationParser(footnote_text, footnote_num)
                        parsed_citations = parser.parse()
                        logger.debug(f"DEBUG: Footnote {footnote_num} parsed into {len(parsed_citations)} structured citations.")
                        for i, cit in enumerate(parsed_citations):
                            logger.debug(f"DEBUG:   Parsed citation {i+1} (FN{cit.footnote_num}, Cite{cit.citation_num}): {cit.full_text[:100]}...")
                        all_citations.extend(parsed_citations)
            else:
                logger.warning("No footnotes part found in document")
                raise AttributeError("No footnotes")

        except (AttributeError, ImportError, Exception) as e:
            logger.error(f"Could not extract footnotes: {e}")
            logger.info("Creating mock citations for testing...")
            # Create mock citations for testing
            for fn_num in (target_footnotes or [78, 79, 80]):
                citation_text = f"Mock Citation for Footnote {fn_num}"
                parser = CitationParser(citation_text, fn_num)
                parsed_citations = parser.parse()
                all_citations.extend(parsed_citations)

        logger.info(f"Extracted {len(all_citations)} citations from {len(target_footnotes) if target_footnotes else 0} footnotes.")
        return all_citations

    def _find_r1_pdf_for_citation(self, citation: Dict) -> Optional[Path]:
        """Find the R1 PDF that corresponds to a given citation."""
        logger.info(f"  Searching for R1 PDF for FN {citation.footnote_num}...")

        # Suppress MuPDF errors during search
        try:
            fitz.TOOLS.mupdf_display_errors(False)
        except:
            pass

        # Look for PDF matching footnote number AND citation number pattern: R1-078-01-*
        r1_dir = settings.R1_PDF_DIR
        pattern = f"R1-{citation.footnote_num:03d}-{citation.citation_num:02d}*.pdf"

        logger.debug(f"DEBUG: R1_PDF_DIR: {r1_dir}")
        logger.debug(f"DEBUG: Pattern being used: {pattern}")
        logger.debug(f"DEBUG: Contents of R1_PDF_DIR: {list(r1_dir.iterdir())}") # List all items in the directory

        matching_pdfs = list(r1_dir.glob(pattern))

        if matching_pdfs:
            pdf_path = matching_pdfs[0]  # Take first match
            logger.info(f"  -> Found matching PDF: {pdf_path.name}")
            return pdf_path

        logger.warning(f"  -> No matching R1 PDF found for FN {citation.footnote_num}, Cite {citation.citation_num}")
        return None

    def run(self, target_footnotes: List[int] = None, parallel: bool = True, max_workers: int = 5):
        """Run the full R2 pipeline.

        Args:
            target_footnotes: A list of specific footnote numbers to process.
            parallel: Whether to process citations in parallel (default: True)
            max_workers: Maximum number of parallel workers (default: 5)
        """
        logger.info(f"{Fore.CYAN}Starting R2 Automated Citecheck Pipeline{Style.RESET_ALL}")
        logger.info(f"{Fore.YELLOW}Batch: {self.batch_name}{Style.RESET_ALL}")

        # 1. Load data from Word doc footnotes
        citations = self._extract_citations_from_word(target_footnotes)
        if not citations:
            logger.error("No citations found. Aborting.")
            return

        # 2. Process citations (parallel or sequential)
        if parallel:
            logger.info(f"{Fore.CYAN}Processing {len(citations)} citations in parallel (max {max_workers} workers){Style.RESET_ALL}")
            from concurrent.futures import ThreadPoolExecutor, as_completed
            import time

            results = []
            retry_queue = []  # Queue for citations that failed all 8 attempts
            retried_citations = set()  # Track which citations have been retried (prevent infinite loops)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Only submit new citations as workers become available
                # Start with first max_workers citations (staggered by 20 seconds)
                future_to_citation = {}
                citation_index = 0

                # Submit initial batch with staggering
                initial_batch = min(max_workers, len(citations))
                for i in range(initial_batch):
                    if i > 0:
                        logger.info(f"Staggering worker {i+1}/{max_workers} - waiting 2 seconds...")
                        time.sleep(2)
                    citation = citations[citation_index]
                    future = executor.submit(self._process_single_citation, citation)
                    future_to_citation[future] = citation
                    citation_index += 1

                # Collect results and submit new citations as workers complete (dynamic scheduling)
                from concurrent.futures import FIRST_COMPLETED, wait
                with tqdm(total=len(citations), desc="Processing citations") as pbar:
                    while future_to_citation:
                        done, _ = wait(list(future_to_citation.keys()), return_when=FIRST_COMPLETED)

                        for finished in done:
                            citation = future_to_citation.pop(finished)
                            try:
                                result = finished.result()

                                # Check if validation failed all attempts (and hasn't been retried yet)
                                citation_key = f"{citation.footnote_num}-{citation.citation_num}"
                                if (result and result.get("citation_validation") is None
                                    and citation_key not in retried_citations):
                                    logger.warning(f"Citation {citation_key} failed all 8 attempts. Adding to retry queue...")
                                    retry_queue.append(citation)
                                    retried_citations.add(citation_key)
                                    # Don't update pbar yet - we'll update when retry completes
                                else:
                                    results.append(result)
                                    pbar.update(1)  # Only update when citation is truly done

                            except Exception as e:
                                logger.error(f"Citation {citation.footnote_num}-{citation.citation_num} failed: {e}")
                                # Create a failure record so it gets logged
                                results.append({
                                    "footnote": citation.footnote_num,
                                    "cite_num": citation.citation_num,
                                    "original_text": citation.full_text,
                                    "citation": citation,
                                    "error": f"Pipeline Error: {e}",
                                    "needs_review": True,
                                })
                                pbar.update(1)

                            # Submit next citation: first from retry queue, then from main list
                            next_citation = None
                            if retry_queue:
                                next_citation = retry_queue.pop(0)
                                citation_key = f"{next_citation.footnote_num}-{next_citation.citation_num}"
                                logger.info(f"Retrying citation {citation_key} (attempt 2/2)...")
                            elif citation_index < len(citations):
                                next_citation = citations[citation_index]
                                citation_index += 1

                            if next_citation:
                                next_future = executor.submit(self._process_single_citation, next_citation)
                                future_to_citation[next_future] = next_citation

            # Safety check: warn if retry queue has unprocessed items
            if retry_queue:
                logger.warning(f"Retry queue still has {len(retry_queue)} unprocessed citations. This should not happen.")
                for citation in retry_queue:
                    logger.warning(f"  - Unprocessed: FN{citation.footnote_num}-{citation.citation_num}")

            # Apply results to shared resources
            for result in results:
                if result:
                    self._apply_citation_result(result)
        else:
            # Sequential processing (original behavior)
            for citation in tqdm(citations, desc="Processing citations"):
                result = self._process_single_citation(citation)
                if result:
                    self._apply_citation_result(result)

        # 3. Save all outputs
        self._save_outputs()

        logger.info(f"{Fore.GREEN}Pipeline finished!{Style.RESET_ALL}")
        self._print_summary()

    def _process_single_citation(self, citation: Dict):
        """Process one citation through all relevant pipeline stages.
        Returns the result dict instead of updating shared resources."""

        fn_num = citation.footnote_num
        cite_num = citation.citation_num

        logger.info(f"{Fore.YELLOW}Processing FN {fn_num}, Cite {cite_num}{Style.RESET_ALL}")

        result_log = {
            "footnote": fn_num,
            "cite_num": cite_num,
            "original_text": citation.full_text,
            "citation_type": citation.type,
            "citation": citation,  # Keep reference for later
            "needs_review": False,
            "needs_word_correction": False,
            "corrected_text": None,
            "r1_pdf_path": None,
            "r2_pdf_path": None
        }

        # STAGE 1: PDF Processing (find relevant PDF) - DO THIS FIRST so R2 PDFs can be generated even if validation fails
        r1_pdf_path = self._find_r1_pdf_for_citation(citation)

        if not r1_pdf_path or not r1_pdf_path.exists():
            logger.warning(f"  -> Could not find R1 PDF for footnote {fn_num}")
            result_log["needs_review"] = True
            return result_log

        result_log["r1_pdf_path"] = r1_pdf_path

        # STAGE 2: Citation Format Validation (do this early but don't stop processing if it fails)
        logger.info("  Validating citation format...")
        validation_result = self.citation_validator.validate_citation(citation)

        # Safely extract validation data - handle None case from API failures
        validation_data = None
        if validation_result and isinstance(validation_result, dict):
            validation_data = validation_result.get("validation") if validation_result.get("success") else None
            result_log["citation_validation"] = validation_data

            if not validation_result.get("success"):
                logger.error(f"  -> Format validation failed: {validation_result.get('error', 'Unknown error')}")
                result_log["needs_review"] = True
                # DON'T return - continue processing to get support analysis and generate R2 PDF

            # Mark if correction is needed
            if validation_data and isinstance(validation_data, dict):
                corrected_cit = validation_data.get("corrected_version")
                if corrected_cit and not validation_data.get("is_correct", True):
                    result_log["needs_word_correction"] = True
                    result_log["corrected_text"] = corrected_cit
                    logger.info(f"  -> Citation needs correction")
            elif validation_result.get("success"):
                logger.warning(f"  -> Validation succeeded but returned invalid data format: {validation_data}")
        else:
            # validation_result is None or not a dict (complete API failure)
            logger.error(f"  -> Format validation completely failed: validation_result is {type(validation_result)}")
            result_log["citation_validation"] = None
            result_log["needs_review"] = True
            # DON'T return - continue processing to get support analysis and generate R2 PDF

        # STAGE 3: PDF Content Processing
        pdf_data = process_r1_pdf(r1_pdf_path)
        if not pdf_data["success"]:
             logger.error(f"  -> PDF processing failed for {r1_pdf_path}")
             result_log["error"] = "PDF processing failed"
             result_log["needs_review"] = True
             return result_log

        result_log["source_pdf"] = pdf_data["metadata"]

        # Check for OCR quality issues
        if pdf_data.get("has_quality_issues", False):
            logger.error(f"  ⚠️  BAD OCR DETECTED in {r1_pdf_path.name}!")
            logger.error("     This PDF has corrupted text extraction. Results may be unreliable.")
            result_log["ocr_quality_warning"] = True
            result_log["needs_review"] = True
        else:
            result_log["ocr_quality_warning"] = False

        # Get all redboxed regions
        if not pdf_data["redboxed_regions"]:
            logger.warning("  -> No redboxed regions found in PDF")
            result_log["error"] = "No redbox found"
            result_log["needs_review"] = True
            return result_log

        # Combine redboxed text - filter out corrupted regions
        all_redbox_text = []
        corrupted_regions = []

        for i, region in enumerate(pdf_data["redboxed_regions"]):
            text = region["text"].strip()

            # Check if this specific region has quality issues
            quality = region.get("quality_assessment", {})
            if quality.get("is_corrupted", False):
                corrupted_regions.append(i+1)
                logger.warning(f"  -> Skipping Region {i+1} due to corrupted OCR (quality: {quality.get('score', 0):.2f})")
                continue

            if text:  # Only skip completely empty text
                all_redbox_text.append(f"[Region {i+1}, Page {region['page']}]: {text}")

        if corrupted_regions:
            logger.warning(f"  -> Excluded {len(corrupted_regions)} corrupted region(s): {corrupted_regions}")
            result_log["corrupted_regions"] = corrupted_regions

        if not all_redbox_text:
            logger.warning("  -> No redboxed text found")
            result_log["error"] = "No redbox text"
            result_log["needs_review"] = True
            return result_log

        source_text = "\n\n".join(all_redbox_text)
        logger.info(f"  -> Using {len(all_redbox_text)} redboxed regions for support check")

        # Get proposition from Word doc (simplified)
        proposition = self._get_proposition_for_footnote(fn_num)

        # STAGE 4: Support Verification
        logger.info("  Verifying if source supports proposition...")
        support_result = self.support_checker.check_support(proposition, source_text, citation.full_text)

        # Safely extract support analysis - handle None case from API failures
        if support_result and support_result.get("success"):
            result_log["support_analysis"] = support_result["analysis"]
        else:
            logger.error(f"  -> Support check failed: {support_result.get('error', 'Unknown error') if support_result else 'API returned None'}")
            result_log["support_analysis"] = None
            result_log["needs_review"] = True
            # DON'T return - continue processing to generate R2 PDF

        # STAGE 5: Quote Accuracy Check
        if citation.quoted_text:
            logger.info("  Verifying quote accuracy...")
            quote_result = self.quote_verifier.verify_quote(citation.quoted_text, source_text)
            result_log["quote_verification"] = quote_result

        # Determine overall action
        recommendation = self._determine_overall_recommendation(result_log)
        result_log["recommendation"] = recommendation

        if recommendation != "approve":
            result_log["needs_review"] = True

        # Generate R2 PDF immediately (before returning)
        if result_log.get("r1_pdf_path"):
            logger.info("  Generating R2 PDF...")
            from src.r2_generator import R2Generator
            r2_gen = R2Generator(result_log["r1_pdf_path"], settings.R2_PDF_DIR)
            r2_gen.add_validation_annotations(result_log)
            r2_pdf_path = r2_gen.save_r2_pdf()
            r2_gen.close()
            result_log["r2_pdf_path"] = str(r2_pdf_path)
            logger.info(f"  ✓ R2 PDF saved: {r2_pdf_path}")
        else:
            logger.warning("  ⚠ No R1 PDF path - skipping R2 PDF generation")

        return result_log

    def _apply_citation_result(self, result: Dict):
        """Apply the results of citation processing to shared resources (thread-safe)."""

        fn_num = result["footnote"]
        cite_num = result["cite_num"]

        # Apply Word doc correction if needed
        if result.get("needs_word_correction") and result.get("corrected_text"):
            self.word_editor.replace_text_tracked(fn_num, result["original_text"], result["corrected_text"])
            logger.info(f"  -> Applied correction for FN {fn_num}, Cite {cite_num}")

        # Update spreadsheet
        self.spreadsheet_updater.update_citation(fn_num, cite_num, result)

        # R2 PDF already generated in _process_single_citation(), no need to regenerate here

        # Convert Path objects to strings (not JSON serializable)
        if "r1_pdf_path" in result and result["r1_pdf_path"]:
            result["r1_pdf_path"] = str(result["r1_pdf_path"])
        if "r2_pdf_path" in result and result["r2_pdf_path"]:
            result["r2_pdf_path"] = str(result["r2_pdf_path"])

        # Remove citation object (not JSON serializable)
        if "citation" in result:
            del result["citation"]

        # Add batch metadata
        result["batch_name"] = self.batch_name
        result["batch_timestamp"] = self.batch_timestamp
        result["processed_at"] = datetime.now().isoformat()

        # Add to queues
        if result.get("needs_review"):
            self.human_review_queue.append(result)

        self.full_log.append(result)

        # Save log incrementally after each citation
        self._save_incremental_log(result)

    def _save_incremental_log(self, new_entry: Dict):
        """Append a single entry to the cumulative pipeline log."""
        log_path = settings.LOG_DIR / "full_pipeline_log.json"

        # Load existing log if it exists
        existing_log = []
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    existing_log = json.load(f)
                if not isinstance(existing_log, list):
                    logger.warning("Log file was not a list. Starting fresh.")
                    existing_log = []
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Could not load existing log: {e}. Starting fresh.")
                existing_log = []

        # Append the new result
        existing_log.append(new_entry)

        # Save the updated cumulative log
        with open(log_path, 'w') as f:
            json.dump(existing_log, f, indent=2)

    def _get_proposition_for_footnote(self, footnote_num: int) -> str:
        """
        Extract the proposition for a footnote.
        The proposition for FN N is the text between FN (N-1) and FN N.
        """
        try:
            from lxml import etree

            # Get document XML
            doc = self.word_editor.doc

            # Extract all text with footnote references
            full_text_parts = []
            footnote_positions = {}  # {footnote_num: position_in_text}
            current_char_pos = 0

            for para in doc.paragraphs:
                para_text = []

                # Parse paragraph XML to find footnote references in order
                for run in para.runs:
                    run_element = run._element

                    # Check for formatting in this run
                    rPr = run_element.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr')
                    is_italic = False
                    is_bold = False
                    is_smallcaps = False

                    if rPr is not None:
                        is_italic = rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}i') is not None
                        is_bold = rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}b') is not None
                        is_smallcaps = rPr.find('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}smallCaps') is not None

                    # Process run children in order (text and footnote refs interspersed)
                    for child in run_element:
                        # Check if it's a text element
                        if child.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t':
                            if child.text:
                                text = child.text
                                # Wrap with formatting markers
                                if is_italic:
                                    text = f"*{text}*"
                                if is_bold:
                                    text = f"**{text}**"
                                if is_smallcaps:
                                    text = f"[SC]{text}[/SC]"
                                para_text.append(text)
                        # Check if it's a footnote reference
                        elif child.tag == '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}footnoteReference':
                            fn_id = child.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
                            if fn_id:
                                fn_num = int(fn_id)
                                # Record position BEFORE adding marker
                                current_pos = current_char_pos + len(''.join(para_text))
                                footnote_positions[fn_num] = current_pos
                                para_text.append(f"[FN{fn_num}]")  # Marker for footnote

                para_combined = ''.join(para_text)
                full_text_parts.append(para_combined)
                # Add to character position (paragraph text + space separator)
                current_char_pos += len(para_combined) + 1  # +1 for space between paragraphs

            # Combine all paragraphs
            combined_text = ' '.join(full_text_parts)

            logger.debug(f"Found {len(footnote_positions)} footnote references in document")
            logger.debug(f"Footnote positions around {footnote_num}: {dict(sorted([(k,v) for k,v in footnote_positions.items() if abs(k-footnote_num) <= 2]))}")

            # Find positions of current footnote and previous footnote
            if footnote_num not in footnote_positions:
                logger.warning(f"Footnote {footnote_num} reference not found in main text")
                return "Proposition could not be automatically extracted (footnote ref not found)."

            current_fn_pos = footnote_positions[footnote_num]

            # Find NEXT footnote position (the text for FN N is between FN N and FN N+1)
            next_fn_num = footnote_num + 1
            if next_fn_num in footnote_positions:
                next_fn_pos = footnote_positions[next_fn_num]
                logger.debug(f"Using FN {footnote_num} at pos {current_fn_pos} to FN {next_fn_num} at pos {next_fn_pos}")
            else:
                # If no next footnote, go to end of combined text or take 500 chars after
                next_fn_pos = min(len(combined_text), current_fn_pos + 500)  # Fallback
                logger.warning(f"FN {next_fn_num} not found, using fallback position {next_fn_pos}")

            # Extract text between current footnote and next footnote
            proposition = combined_text[current_fn_pos:next_fn_pos]
            logger.debug(f"Raw extracted text length: {len(proposition)}")
            logger.debug(f"Raw extracted text: {proposition[:200]}...")

            # Clean up the proposition
            # Remove the current footnote marker at the beginning
            proposition = proposition.replace(f"[FN{footnote_num}]", "").strip()
            # Remove the next footnote marker if it appears at the end
            proposition = proposition.replace(f"[FN{next_fn_num}]", "").strip()

            # Remove extra whitespace
            proposition = ' '.join(proposition.split())

            # Normalize markdown spacing (move spaces outside formatting markers)
            proposition = normalize_markdown_spacing(proposition)

            if proposition:
                logger.info(f"Extracted proposition for FN {footnote_num}: {proposition[:100]}...")
                return proposition
            else:
                return "Proposition could not be automatically extracted (no text between footnotes)."

        except Exception as e:
            logger.error(f"Error extracting proposition for FN {footnote_num}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"Proposition could not be automatically extracted (error: {str(e)})."

    def _determine_overall_recommendation(self, results: Dict) -> str:
        """Determine overall recommendation from individual checks."""

        # Citation check - handle None case from API failures
        citation_val = results.get("citation_validation") or {}
        if citation_val.get("confidence", 1.0) < settings.CONFIDENCE_THRESHOLD:
            return "review_citation_format"

        # Support check - handle None case from API failures
        support_analysis = results.get("support_analysis") or {}
        support_conf = support_analysis.get("confidence", 1.0)
        support_level = support_analysis.get("support_level", "yes")
        if support_conf < settings.CONFIDENCE_THRESHOLD or support_level != "yes":
            return "review_proposition_support"
            
        # Quote check
        if "quote_verification" in results:
            if not results["quote_verification"]["accurate"]:
                return "review_quote_accuracy"
        
        return "approve"
        
    def _save_outputs(self):
        """Save logs, reports, and updated documents."""
        # Save spreadsheet
        self.spreadsheet_updater.save()
        self.spreadsheet_updater.close()

        # Save Word doc
        self.word_editor.save(settings.OUTPUT_DIR / "Bersh_R2_Edited.docx")

        # Log completion
        log_path = settings.LOG_DIR / "full_pipeline_log.json"
        logger.info(f"Batch '{self.batch_name}' processing complete. Full log at {log_path}")

        # Save human review queue
        self._generate_review_report()

    def _generate_review_report(self):
        """Generate HTML report for human review queue."""
        report_path = settings.REPORT_DIR / "human_review_queue.html"
        
        html = "<html><head><title>R2 Review Queue</title>"
        html += "<style>body { font-family: sans-serif; } .item { border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; } </style>"
        html += "</head><body>"
        html += f"<h1>R2 Items for Human Review ({len(self.human_review_queue)} items)</h1>"
        
        for item in self.human_review_queue:
            html += "<div class='item'>"
            html += f"<h2>Footnote {item['footnote']}, Citation {item['cite_num']}</h2>"
            html += f"<p><b>Recommendation:</b> {item.get('recommendation', 'N/A')}</p>"
            html += f"<p><b>Original Text:</b> {item['original_text']}</p>"
            
            if 'support_analysis' in item and item['support_analysis']:
                sa = item['support_analysis']
                html += f"<h4>Support Analysis ({sa['support_level']}, conf: {sa['confidence']:.2f})</h4>"
                html += f"<p><i>{sa['reasoning']}</i></p>"

            if 'citation_validation' in item and item['citation_validation'] and not item['citation_validation'].get('is_correct', True):
                 cv = item['citation_validation']
                 html += f"<h4>Citation Format Issues ({len(cv.get('errors', []))} errors)</h4>"
                 html += f"<p><b>Corrected:</b> {cv.get('corrected_version', 'N/A')}</p>"

            html += "</div>"
            
        html += "</body></html>"
        
        with open(report_path, 'w') as f:
            f.write(html)
        logger.info(f"Human review report generated at {report_path}")

    def _print_summary(self):
        """Print summary of pipeline run."""
        llm_stats = self.llm.get_stats()

        print("\n" + "="*50)
        print(f"{Fore.CYAN}PIPELINE SUMMARY{Style.RESET_ALL}")
        print("="*50)
        print(f"Total citations processed: {len(self.full_log)}")
        print(f"Items flagged for human review: {len(self.human_review_queue)}")
        print("\n--- LLM USAGE ---")
        print(f"Total GPT calls: {llm_stats['total_calls']}")
        print(f"Total tokens used: {llm_stats['total_tokens']}")
        print(f"Estimated cost: ${llm_stats['total_cost']:.4f}")
        print("="*50)
        
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="R2 Citation Checking Pipeline")
    parser.add_argument('--footnotes', type=int, nargs='*', default=[],
                       help='Specific footnote numbers to process (e.g., --footnotes 78 79 80)')
    parser.add_argument('--footnoterange', type=str, default=None,
                       help='Footnote range to process (e.g., "89-100,130"). Combines with --footnotes if both are provided.')
    parser.add_argument('--batch-name', type=str, default=None,
                       help='Manual batch name for this run (e.g., --batch-name "initial_review"). Auto-generated if not specified.')
    parser.add_argument('--parallel', action='store_true', default=True,
                       help='Process citations in parallel (default: True)')
    parser.add_argument('--no-parallel', dest='parallel', action='store_false',
                       help='Process citations sequentially')
    parser.add_argument('--workers', type=int, default=1,
                       help='Maximum number of parallel workers (default: 1, sequential)')
    args = parser.parse_args()

    target_footnotes = []
    if args.footnotes:
        target_footnotes.extend(args.footnotes)
    if args.footnoterange:
        target_footnotes.extend(_parse_footnote_range(args.footnoterange))
    target_footnotes = sorted(list(set(target_footnotes))) # Remove duplicates and sort

    pipeline = R2Pipeline(batch_name=args.batch_name)
    pipeline.run(target_footnotes=target_footnotes, parallel=args.parallel, max_workers=args.workers)
