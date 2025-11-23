"""
Integration Layer - Connect all supercharged modules
Provides unified interface for all enhanced features
"""
import logging
from typing import Dict, Optional, List
from pathlib import Path

from app.core.batch_processor import BatchProcessor
from app.core.review_queue import ReviewQueue
from app.core.cost_optimizer import CostOptimizer
from app.analytics.analytics_engine import AnalyticsEngine
from app.ml.citation_predictor import CitationPredictor
from app.data.sheets_batch_client import SheetsBatchClient, BatchUpdateContext
from app.data.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class IntegrationManager:
    """
    Integration manager for all supercharged features

    Features:
    - Centralized access to all enhanced modules
    - Coordinated workflows across modules
    - Smart routing and optimization
    - Performance monitoring
    - Error handling and recovery
    """

    def __init__(
        self,
        orchestrator,
        cache_manager: CacheManager,
        sheets_service=None
    ):
        """
        Initialize integration manager

        Args:
            orchestrator: PipelineOrchestrator instance
            cache_manager: CacheManager instance
            sheets_service: Google Sheets API service (optional)
        """
        self.orchestrator = orchestrator
        self.cache = cache_manager

        # Initialize supercharged modules
        self.analytics = AnalyticsEngine(cache_manager)
        self.cost_optimizer = CostOptimizer(cache_manager, self.analytics)
        self.citation_predictor = CitationPredictor(cache_manager)
        self.review_queue = ReviewQueue(cache_manager)
        self.batch_processor = BatchProcessor(orchestrator, cache_manager)

        # Initialize batch client if sheets service provided
        self.batch_client = None
        if sheets_service and hasattr(orchestrator, 'sp_machine'):
            spreadsheet_id = orchestrator.sp_machine.sheets_client.spreadsheet_id
            self.batch_client = SheetsBatchClient(sheets_service, spreadsheet_id)

        logger.info("Initialized IntegrationManager with all supercharged modules")

    def validate_citation_optimized(
        self,
        citation: str,
        proposition: str = None,
        source_text: str = None,
        validation_type: str = 'format'
    ) -> Dict:
        """
        Validate citation with optimization

        This method:
        1. Checks cache first
        2. Uses ML prediction to decide if LLM needed
        3. Selects optimal model if LLM used
        4. Caches result for future use

        Args:
            citation: Citation text
            proposition: Proposition being supported
            source_text: Source text
            validation_type: 'format' or 'support'

        Returns:
            Validation result
        """
        try:
            # Check cache
            use_cache, cached_result = self.cost_optimizer.should_use_cache(
                citation, validation_type
            )

            if use_cache and cached_result:
                logger.info(f"Using cached validation for: {citation[:50]}")
                return cached_result

            # Use ML prediction
            ml_prediction = self.citation_predictor.predict(
                citation, proposition, source_text
            )

            # If ML is confident, skip LLM
            if not ml_prediction.should_validate_with_llm:
                logger.info(f"ML prediction bypassed LLM: {ml_prediction.reasoning}")
                result = {
                    'source': 'ml_prediction',
                    'citation_type': ml_prediction.citation_type,
                    'confidence': ml_prediction.confidence,
                    'predicted_issues': ml_prediction.predicted_issues,
                    'reasoning': ml_prediction.reasoning
                }

                # Cache result
                self.cost_optimizer.cache_result(citation, validation_type, result)

                return result

            # Need LLM validation - select optimal model
            task_type = 'citation_format_simple' if len(ml_prediction.predicted_issues) <= 1 else 'citation_format_complex'
            provider, model = self.cost_optimizer.select_optimal_model(task_type)

            logger.info(f"Using LLM validation: {provider}/{model}")

            # Perform LLM validation
            # TODO: Call actual LLM validation through orchestrator
            result = {
                'source': 'llm_validation',
                'provider': provider,
                'model': model,
                'ml_prediction': ml_prediction.to_dict() if hasattr(ml_prediction, 'to_dict') else {},
                # LLM result would go here
            }

            # Cache result
            self.cost_optimizer.cache_result(citation, validation_type, result)

            return result

        except Exception as e:
            logger.error(f"Error in optimized validation: {e}", exc_info=True)
            raise

    def process_article_batch_optimized(
        self,
        article_ids: List[str],
        stage: str = "FULL",
        priority: str = "NORMAL"
    ) -> str:
        """
        Process multiple articles with optimization

        This method:
        1. Creates batch job
        2. Uses batch processor for parallel execution
        3. Uses batch API for Sheets updates
        4. Tracks costs and performance

        Args:
            article_ids: List of article IDs
            stage: Pipeline stage ('SP', 'R1', 'R2', 'FULL')
            priority: Priority level

        Returns:
            Batch job ID
        """
        try:
            logger.info(f"Starting optimized batch processing for {len(article_ids)} articles")

            # Create batch job
            job_id = self.batch_processor.create_batch_job(
                name=f"Batch {stage} - {len(article_ids)} articles",
                article_ids=article_ids,
                stage=stage,
                priority=priority
            )

            # Start batch processing
            def progress_callback(job_status):
                logger.debug(f"Batch progress: {job_status['completed_count']}/{job_status['total_count']}")

            self.batch_processor.start_batch_job(job_id, progress_callback)

            logger.info(f"Started batch job: {job_id}")

            return job_id

        except Exception as e:
            logger.error(f"Error in batch processing: {e}", exc_info=True)
            raise

    def update_sheets_batch(self, updates: List[Dict]) -> bool:
        """
        Update Google Sheets with batch API

        Args:
            updates: List of update dictionaries

        Returns:
            True if successful
        """
        try:
            if not self.batch_client:
                logger.warning("Batch client not initialized")
                return False

            # Use batch update context for automatic execution
            with BatchUpdateContext(self.batch_client) as batch:
                # Queue all updates
                for update in updates:
                    update_type = update.get('type')

                    if update_type == 'source':
                        batch.queue_update_sources_batch([update['data']])
                    elif update_type == 'article':
                        batch.queue_update_articles_batch([update['data']])

            logger.info(f"Batch updated {len(updates)} items in Google Sheets")
            return True

        except Exception as e:
            logger.error(f"Error in batch update: {e}", exc_info=True)
            return False

    def add_to_review_queue(
        self,
        source_id: str,
        citation: str,
        footnote_number: int,
        validation_result: Dict
    ) -> str:
        """
        Add citation to review queue

        Args:
            source_id: Source ID
            citation: Citation text
            footnote_number: Footnote number
            validation_result: Validation result from LLM

        Returns:
            Review item ID
        """
        try:
            item_id = self.review_queue.add_item(
                source_id=source_id,
                citation=citation,
                footnote_number=footnote_number,
                format_issues=validation_result.get('format_issues', []),
                support_issues=validation_result.get('support_issues', []),
                confidence_score=validation_result.get('confidence_score', 0),
                llm_suggestion=validation_result.get('suggestion'),
                priority=self.review_queue.ReviewPriority.NORMAL
            )

            logger.info(f"Added to review queue: {item_id}")

            return item_id

        except Exception as e:
            logger.error(f"Error adding to review queue: {e}", exc_info=True)
            raise

    def get_dashboard_summary(self) -> Dict:
        """
        Get comprehensive dashboard summary

        Returns:
            Dashboard data
        """
        try:
            summary = self.analytics.generate_dashboard_summary()

            # Add optimization data
            summary['optimization'] = {
                'recommendations': [
                    r.__dict__ for r in self.cost_optimizer.get_optimization_recommendations()
                ],
                'forecast': self.cost_optimizer.forecast_monthly_cost(
                    articles_per_month=50
                )
            }

            # Add review queue stats
            summary['review_queue'] = self.review_queue.get_stats()

            # Add batch processing stats
            summary['batch_jobs'] = {
                'active': len([
                    j for j in self.batch_processor.jobs.values()
                    if j.status == self.batch_processor.BatchJobStatus.IN_PROGRESS
                ]),
                'total': len(self.batch_processor.jobs)
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting dashboard summary: {e}", exc_info=True)
            return {}

    def get_stats(self) -> Dict:
        """
        Get integration stats

        Returns:
            Statistics dictionary
        """
        try:
            stats = {
                'analytics': {
                    'cache_stats': self.cache.get_cache_stats(),
                },
                'batch_processor': {
                    'jobs': len(self.batch_processor.jobs),
                    'active': len([
                        j for j in self.batch_processor.jobs.values()
                        if j.status == self.batch_processor.BatchJobStatus.IN_PROGRESS
                    ])
                },
                'review_queue': self.review_queue.get_stats(),
                'cost_optimizer': {
                    'cache_size': len(self.cost_optimizer.optimization_cache)
                }
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting stats: {e}", exc_info=True)
            return {}


def create_integration_manager(
    orchestrator,
    cache_manager: CacheManager,
    sheets_service=None
) -> IntegrationManager:
    """
    Factory function to create IntegrationManager

    Args:
        orchestrator: PipelineOrchestrator instance
        cache_manager: CacheManager instance
        sheets_service: Google Sheets API service (optional)

    Returns:
        IntegrationManager instance
    """
    return IntegrationManager(orchestrator, cache_manager, sheets_service)
