"""
Worker threads for background processing
"""
from PyQt6.QtCore import QThread, pyqtSignal
import logging

logger = logging.getLogger(__name__)


class SPWorkerThread(QThread):
    """Worker thread for Source Pull processing"""

    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    source_completed = pyqtSignal(str, str)  # source_id, status
    finished_with_result = pyqtSignal(dict)  # result dict
    error_occurred = pyqtSignal(str)  # error message

    def __init__(self, orchestrator, article_id):
        super().__init__()
        self.orchestrator = orchestrator
        self.article_id = article_id
        self._is_running = True

    def run(self):
        """Run SP processing in background"""
        try:
            logger.info(f"SP worker starting for article {self.article_id}")

            result = self.orchestrator.run_sp(
                self.article_id,
                progress_callback=self._progress_callback
            )

            self.finished_with_result.emit(result)
            logger.info(f"SP worker completed for article {self.article_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"SP worker error: {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)

    def _progress_callback(self, current, total, message):
        """Progress callback from orchestrator"""
        if self._is_running:
            self.progress_updated.emit(current, total, message)

    def stop(self):
        """Stop the worker"""
        self._is_running = False
        self.requestInterruption()


class R1WorkerThread(QThread):
    """Worker thread for R1 processing"""

    progress_updated = pyqtSignal(int, int, str)
    finished_with_result = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, orchestrator, article_id):
        super().__init__()
        self.orchestrator = orchestrator
        self.article_id = article_id
        self._is_running = True

    def run(self):
        """Run R1 processing in background"""
        try:
            logger.info(f"R1 worker starting for article {self.article_id}")

            result = self.orchestrator.run_r1(
                self.article_id,
                progress_callback=self._progress_callback
            )

            self.finished_with_result.emit(result)
            logger.info(f"R1 worker completed for article {self.article_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"R1 worker error: {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)

    def _progress_callback(self, current, total, message):
        if self._is_running:
            self.progress_updated.emit(current, total, message)

    def stop(self):
        self._is_running = False
        self.requestInterruption()


class R2WorkerThread(QThread):
    """Worker thread for R2 validation"""

    progress_updated = pyqtSignal(int, int, str)
    finished_with_result = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, orchestrator, article_id, article_doc_path):
        super().__init__()
        self.orchestrator = orchestrator
        self.article_id = article_id
        self.article_doc_path = article_doc_path
        self._is_running = True

    def run(self):
        """Run R2 processing in background"""
        try:
            logger.info(f"R2 worker starting for article {self.article_id}")

            result = self.orchestrator.run_r2(
                self.article_id,
                self.article_doc_path,
                progress_callback=self._progress_callback
            )

            self.finished_with_result.emit(result)
            logger.info(f"R2 worker completed for article {self.article_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"R2 worker error: {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)

    def _progress_callback(self, current, total, message):
        if self._is_running:
            self.progress_updated.emit(current, total, message)

    def stop(self):
        self._is_running = False
        self.requestInterruption()


class FullPipelineWorkerThread(QThread):
    """Worker thread for complete SP→R1→R2 pipeline"""

    stage_changed = pyqtSignal(str)  # stage name
    progress_updated = pyqtSignal(str, int, int, str)  # stage, current, total, message
    finished_with_result = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, orchestrator, article_id, article_doc_path):
        super().__init__()
        self.orchestrator = orchestrator
        self.article_id = article_id
        self.article_doc_path = article_doc_path
        self._is_running = True

    def run(self):
        """Run full pipeline in background"""
        try:
            logger.info(f"Full pipeline worker starting for article {self.article_id}")

            result = self.orchestrator.run_full_pipeline(
                self.article_id,
                self.article_doc_path,
                progress_callback=self._progress_callback
            )

            self.finished_with_result.emit(result)
            logger.info(f"Full pipeline worker completed for article {self.article_id}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Full pipeline worker error: {error_msg}", exc_info=True)
            self.error_occurred.emit(error_msg)

    def _progress_callback(self, stage, current, total, message):
        if self._is_running:
            self.stage_changed.emit(stage)
            self.progress_updated.emit(stage, current, total, message)

    def stop(self):
        self._is_running = False
        self.requestInterruption()
