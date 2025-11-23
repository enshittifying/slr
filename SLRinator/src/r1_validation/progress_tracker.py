"""
Progress Tracking and Resumability for R1 Validation
Enables checkpoint/resume functionality for long-running workflows
"""
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class CitationProgress:
    """Progress state for a single citation."""
    citation_num: int
    footnote_num: int
    citation_text: str
    status: str  # pending, validating, retrieving, verified, completed, failed, skipped
    validation_complete: bool = False
    retrieval_complete: bool = False
    quote_check_complete: bool = False
    support_check_complete: bool = False
    error: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None


@dataclass
class WorkflowProgress:
    """Overall workflow progress state."""
    workflow_id: str
    document_path: str
    total_citations: int
    completed_citations: int
    failed_citations: int
    skipped_citations: int
    started_at: float
    last_checkpoint_at: float
    checkpoint_interval: int = 10  # Save checkpoint every N citations
    citations: List[CitationProgress] = None

    def __post_init__(self):
        if self.citations is None:
            self.citations = []


class ProgressTracker:
    """
    Tracks and persists workflow progress for resumability.
    """

    def __init__(self, checkpoint_dir: Path = None):
        """
        Initialize progress tracker.

        Args:
            checkpoint_dir: Directory for saving progress checkpoints
        """
        self.checkpoint_dir = checkpoint_dir or Path.cwd() / "output" / "progress"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_progress: Optional[WorkflowProgress] = None

    def start_workflow(self, document_path: str, total_citations: int) -> str:
        """
        Start new workflow or resume existing one.

        Args:
            document_path: Path to document being processed
            total_citations: Total number of citations

        Returns:
            Workflow ID
        """
        # Generate workflow ID from document path and timestamp
        workflow_id = self._generate_workflow_id(document_path)

        # Try to load existing progress
        existing = self.load_progress(workflow_id)
        if existing:
            logger.info(f"Resuming workflow {workflow_id}")
            logger.info(f"  Completed: {existing.completed_citations}/{existing.total_citations}")
            logger.info(f"  Failed: {existing.failed_citations}")
            self.current_progress = existing
            return workflow_id

        # Start new workflow
        logger.info(f"Starting new workflow {workflow_id}")
        self.current_progress = WorkflowProgress(
            workflow_id=workflow_id,
            document_path=document_path,
            total_citations=total_citations,
            completed_citations=0,
            failed_citations=0,
            skipped_citations=0,
            started_at=time.time(),
            last_checkpoint_at=time.time()
        )
        self.save_progress()
        return workflow_id

    def add_citation(self, citation_num: int, footnote_num: int, citation_text: str):
        """
        Add citation to tracking.

        Args:
            citation_num: Citation number
            footnote_num: Footnote number
            citation_text: Citation text
        """
        if not self.current_progress:
            raise ValueError("No active workflow")

        citation_progress = CitationProgress(
            citation_num=citation_num,
            footnote_num=footnote_num,
            citation_text=citation_text,
            status="pending",
            started_at=time.time()
        )
        self.current_progress.citations.append(citation_progress)

    def update_citation_status(self, citation_num: int, status: str, error: str = None):
        """
        Update citation status.

        Args:
            citation_num: Citation number
            status: New status
            error: Error message if failed
        """
        citation = self._get_citation(citation_num)
        if citation:
            citation.status = status
            if error:
                citation.error = error
            if status in ["completed", "failed", "skipped"]:
                citation.completed_at = time.time()

            # Update workflow counters
            if status == "completed":
                self.current_progress.completed_citations += 1
            elif status == "failed":
                self.current_progress.failed_citations += 1
            elif status == "skipped":
                self.current_progress.skipped_citations += 1

            # Auto-checkpoint periodically
            if self.current_progress.completed_citations % self.current_progress.checkpoint_interval == 0:
                self.save_progress()

    def mark_validation_complete(self, citation_num: int):
        """Mark validation as complete for citation."""
        citation = self._get_citation(citation_num)
        if citation:
            citation.validation_complete = True

    def mark_retrieval_complete(self, citation_num: int):
        """Mark retrieval as complete for citation."""
        citation = self._get_citation(citation_num)
        if citation:
            citation.retrieval_complete = True

    def mark_quote_check_complete(self, citation_num: int):
        """Mark quote check as complete for citation."""
        citation = self._get_citation(citation_num)
        if citation:
            citation.quote_check_complete = True

    def mark_support_check_complete(self, citation_num: int):
        """Mark support check as complete for citation."""
        citation = self._get_citation(citation_num)
        if citation:
            citation.support_check_complete = True

    def should_process_citation(self, citation_num: int) -> bool:
        """
        Check if citation needs processing (resumability check).

        Args:
            citation_num: Citation number

        Returns:
            True if citation should be processed
        """
        citation = self._get_citation(citation_num)
        if not citation:
            return True  # New citation

        # Skip if already completed or failed
        return citation.status not in ["completed", "failed"]

    def get_pending_citations(self) -> List[CitationProgress]:
        """Get list of pending citations."""
        if not self.current_progress:
            return []
        return [c for c in self.current_progress.citations if c.status == "pending"]

    def get_failed_citations(self) -> List[CitationProgress]:
        """Get list of failed citations."""
        if not self.current_progress:
            return []
        return [c for c in self.current_progress.citations if c.status == "failed"]

    def get_progress_summary(self) -> Dict[str, Any]:
        """Get progress summary."""
        if not self.current_progress:
            return {}

        total = self.current_progress.total_citations
        completed = self.current_progress.completed_citations
        failed = self.current_progress.failed_citations
        skipped = self.current_progress.skipped_citations
        pending = total - completed - failed - skipped

        elapsed = time.time() - self.current_progress.started_at
        rate = completed / elapsed if elapsed > 0 else 0
        eta = (pending / rate) if rate > 0 else 0

        return {
            "workflow_id": self.current_progress.workflow_id,
            "total": total,
            "completed": completed,
            "failed": failed,
            "skipped": skipped,
            "pending": pending,
            "progress_pct": f"{(completed / total * 100):.1f}%" if total > 0 else "0%",
            "elapsed_seconds": elapsed,
            "rate_per_minute": rate * 60,
            "eta_seconds": eta,
            "can_resume": True
        }

    def save_progress(self):
        """Save current progress to disk."""
        if not self.current_progress:
            return

        checkpoint_file = self._get_checkpoint_path(self.current_progress.workflow_id)

        # Convert to dict
        data = {
            "workflow_id": self.current_progress.workflow_id,
            "document_path": self.current_progress.document_path,
            "total_citations": self.current_progress.total_citations,
            "completed_citations": self.current_progress.completed_citations,
            "failed_citations": self.current_progress.failed_citations,
            "skipped_citations": self.current_progress.skipped_citations,
            "started_at": self.current_progress.started_at,
            "last_checkpoint_at": time.time(),
            "checkpoint_interval": self.current_progress.checkpoint_interval,
            "citations": [asdict(c) for c in self.current_progress.citations]
        }

        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Progress saved to {checkpoint_file}")

    def load_progress(self, workflow_id: str) -> Optional[WorkflowProgress]:
        """
        Load progress from disk.

        Args:
            workflow_id: Workflow ID

        Returns:
            WorkflowProgress or None
        """
        checkpoint_file = self._get_checkpoint_path(workflow_id)
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)

            # Convert citations back to objects
            citations = [CitationProgress(**c) for c in data.get("citations", [])]

            progress = WorkflowProgress(
                workflow_id=data["workflow_id"],
                document_path=data["document_path"],
                total_citations=data["total_citations"],
                completed_citations=data["completed_citations"],
                failed_citations=data["failed_citations"],
                skipped_citations=data["skipped_citations"],
                started_at=data["started_at"],
                last_checkpoint_at=data.get("last_checkpoint_at", data["started_at"]),
                checkpoint_interval=data.get("checkpoint_interval", 10),
                citations=citations
            )

            return progress
        except Exception as e:
            logger.error(f"Failed to load progress: {e}")
            return None

    def cleanup_old_checkpoints(self, days: int = 7):
        """
        Remove checkpoints older than specified days.

        Args:
            days: Number of days to keep
        """
        cutoff = time.time() - (days * 24 * 60 * 60)
        removed = 0

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            if checkpoint_file.stat().st_mtime < cutoff:
                checkpoint_file.unlink()
                removed += 1

        if removed > 0:
            logger.info(f"Cleaned up {removed} old checkpoints")

    def _generate_workflow_id(self, document_path: str) -> str:
        """Generate unique workflow ID from document path."""
        # Use document path + date for ID (allows one workflow per document per day)
        date_str = datetime.now().strftime("%Y%m%d")
        path_hash = hashlib.md5(document_path.encode()).hexdigest()[:8]
        return f"workflow_{date_str}_{path_hash}"

    def _get_checkpoint_path(self, workflow_id: str) -> Path:
        """Get path to checkpoint file."""
        return self.checkpoint_dir / f"{workflow_id}.json"

    def _get_citation(self, citation_num: int) -> Optional[CitationProgress]:
        """Get citation by number."""
        if not self.current_progress:
            return None

        for citation in self.current_progress.citations:
            if citation.citation_num == citation_num:
                return citation
        return None
