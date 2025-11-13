"""
Pipeline Orchestrator - coordinates SP → R1 → R2 flow
"""
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable
from pathlib import Path

from .sp_machine import SPMachine
from .r1_machine import R1Machine
from .r2_pipeline import R2Pipeline

logger = logging.getLogger(__name__)


class PipelineStage(Enum):
    """Pipeline processing stages"""
    NOT_STARTED = "not_started"
    SP_IN_PROGRESS = "sp_in_progress"
    SP_COMPLETE = "sp_complete"
    R1_IN_PROGRESS = "r1_in_progress"
    R1_COMPLETE = "r1_complete"
    R2_IN_PROGRESS = "r2_in_progress"
    R2_COMPLETE = "r2_complete"
    ERROR = "error"


@dataclass
class ArticleState:
    """State of article processing"""
    article_id: str
    volume_issue: str
    stage: PipelineStage
    sources_total: int
    sources_completed: int
    last_updated: str
    error_message: Optional[str] = None


class PipelineOrchestrator:
    """
    Orchestrates the complete SP → R1 → R2 pipeline
    """

    def __init__(self, sheets_client, drive_client, llm_client, cache_dir: str = None):
        """
        Initialize orchestrator

        Args:
            sheets_client: Google Sheets client
            drive_client: Google Drive client
            llm_client: LLM client
            cache_dir: Directory for caching
        """
        self.sheets = sheets_client
        self.drive = drive_client
        self.llm = llm_client

        cache_base = Path(cache_dir or "cache")

        # Initialize pipeline components
        self.sp_machine = SPMachine(
            sheets_client,
            drive_client,
            str(cache_base / "sp")
        )

        self.r1_machine = R1Machine(
            sheets_client,
            drive_client,
            str(cache_base / "r1")
        )

        self.r2_pipeline = R2Pipeline(
            sheets_client,
            drive_client,
            llm_client,
            str(cache_base / "r2")
        )

    def get_article_state(self, article_id: str) -> ArticleState:
        """
        Get current state of article

        Args:
            article_id: Article identifier

        Returns:
            ArticleState
        """
        articles = self.sheets.get_all_articles()
        article = next((a for a in articles if a['article_id'] == article_id), None)

        if not article:
            raise ValueError(f"Article {article_id} not found")

        return ArticleState(
            article_id=article_id,
            volume_issue=article['volume_issue'],
            stage=PipelineStage(article['stage']),
            sources_total=article['sources_total'],
            sources_completed=article['sources_completed'],
            last_updated=article['last_updated']
        )

    def run_sp(self, article_id: str,
              progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Run Source Pull for an article

        Args:
            article_id: Article identifier
            progress_callback: Progress callback function
        """
        logger.info(f"Starting SP for article {article_id}")

        try:
            self.update_stage(article_id, PipelineStage.SP_IN_PROGRESS)

            result = self.sp_machine.process_article(article_id, progress_callback)

            if result['fail_count'] == 0:
                self.update_stage(article_id, PipelineStage.SP_COMPLETE)
            else:
                self.update_stage(
                    article_id,
                    PipelineStage.SP_COMPLETE,
                    f"Completed with {result['fail_count']} failures"
                )

            logger.info(f"SP complete for {article_id}: {result}")
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"SP failed for {article_id}: {error_msg}", exc_info=True)
            self.update_stage(article_id, PipelineStage.ERROR, error_msg)
            raise

    def run_r1(self, article_id: str,
              progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Run R1 Preparation for an article

        Args:
            article_id: Article identifier
            progress_callback: Progress callback function
        """
        logger.info(f"Starting R1 for article {article_id}")

        # Check prerequisites
        state = self.get_article_state(article_id)
        if state.stage not in [PipelineStage.SP_COMPLETE, PipelineStage.R1_IN_PROGRESS]:
            raise ValueError(f"Cannot run R1: SP not complete (current stage: {state.stage.value})")

        try:
            self.update_stage(article_id, PipelineStage.R1_IN_PROGRESS)

            result = self.r1_machine.process_article(article_id, progress_callback)

            if result['fail_count'] == 0:
                self.update_stage(article_id, PipelineStage.R1_COMPLETE)
            else:
                self.update_stage(
                    article_id,
                    PipelineStage.R1_COMPLETE,
                    f"Completed with {result['fail_count']} failures"
                )

            logger.info(f"R1 complete for {article_id}: {result}")
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"R1 failed for {article_id}: {error_msg}", exc_info=True)
            self.update_stage(article_id, PipelineStage.ERROR, error_msg)
            raise

    def run_r2(self, article_id: str, article_doc_path: str,
              progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """
        Run R2 Validation for an article

        Args:
            article_id: Article identifier
            article_doc_path: Path to article Word document
            progress_callback: Progress callback function
        """
        logger.info(f"Starting R2 for article {article_id}")

        # Check prerequisites
        state = self.get_article_state(article_id)
        if state.stage not in [PipelineStage.R1_COMPLETE, PipelineStage.R2_IN_PROGRESS]:
            raise ValueError(f"Cannot run R2: R1 not complete (current stage: {state.stage.value})")

        try:
            self.update_stage(article_id, PipelineStage.R2_IN_PROGRESS)

            result = self.r2_pipeline.process_article(
                article_id,
                article_doc_path,
                progress_callback
            )

            self.update_stage(article_id, PipelineStage.R2_COMPLETE)

            logger.info(f"R2 complete for {article_id}: {result}")
            return result

        except Exception as e:
            error_msg = str(e)
            logger.error(f"R2 failed for {article_id}: {error_msg}", exc_info=True)
            self.update_stage(article_id, PipelineStage.ERROR, error_msg)
            raise

    def run_full_pipeline(self, article_id: str, article_doc_path: str,
                         progress_callback: Optional[Callable[[str, int, int, str], None]] = None):
        """
        Run complete SP → R1 → R2 pipeline

        Args:
            article_id: Article identifier
            article_doc_path: Path to article Word document
            progress_callback: Progress callback(stage, current, total, message)
        """
        logger.info(f"Starting full pipeline for article {article_id}")

        results = {}

        # SP Stage
        def sp_progress(current, total, message):
            if progress_callback:
                progress_callback('SP', current, total, message)

        results['sp'] = self.run_sp(article_id, sp_progress)

        # R1 Stage
        def r1_progress(current, total, message):
            if progress_callback:
                progress_callback('R1', current, total, message)

        results['r1'] = self.run_r1(article_id, r1_progress)

        # R2 Stage
        def r2_progress(current, total, message):
            if progress_callback:
                progress_callback('R2', current, total, message)

        results['r2'] = self.run_r2(article_id, article_doc_path, r2_progress)

        logger.info(f"Full pipeline complete for {article_id}")
        return results

    def update_stage(self, article_id: str, stage: PipelineStage, error_msg: str = None):
        """
        Update article stage

        Args:
            article_id: Article identifier
            stage: New pipeline stage
            error_msg: Error message if applicable
        """
        self.sheets.update_article_stage(
            article_id,
            stage.value,
            error_msg
        )

    def get_pipeline_status(self, article_id: str) -> dict:
        """
        Get comprehensive status of pipeline for article

        Args:
            article_id: Article identifier

        Returns:
            Dict with status information
        """
        state = self.get_article_state(article_id)
        sp_cache = self.sp_machine.get_cache_status(article_id)
        r1_cache = self.r1_machine.get_cache_status(article_id)

        return {
            'article_id': article_id,
            'current_stage': state.stage.value,
            'sources_total': state.sources_total,
            'sources_completed': state.sources_completed,
            'sp_cached': sp_cache['cached'],
            'r1_cached': r1_cache['cached'],
            'last_updated': state.last_updated,
            'error_message': state.error_message
        }
