"""
Logging utilities - adapts SLRinator logging for desktop app
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler
import json


def setup_logging(log_dir: str = None, level: int = logging.INFO,
                 console: bool = True, file: bool = True) -> logging.Logger:
    """
    Set up logging configuration for desktop app

    Args:
        log_dir: Directory for log files
        level: Logging level
        console: Enable console logging
        file: Enable file logging

    Returns:
        Configured logger
    """
    if log_dir is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger('slr_desktop')
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'slr_desktop_{timestamp}.log'

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.info("Logging initialized")
    return logger


class ActionLogger:
    """
    Action logger for tracking operations
    Adapts SLRinator's action logging for desktop app
    """

    def __init__(self, log_dir: str = None):
        """
        Initialize action logger

        Args:
            log_dir: Directory for action logs
        """
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs" / "actions"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f'actions_{self.session_id}.jsonl'

    def log_action(self, action_type: str, details: dict):
        """
        Log an action

        Args:
            action_type: Type of action (e.g., 'SP_START', 'PDF_DOWNLOAD', 'R2_VALIDATE')
            details: Dict with action details
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'action_type': action_type,
            'details': details
        }

        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def log_sp_start(self, article_id: str, source_count: int):
        """Log start of source pull"""
        self.log_action('SP_START', {
            'article_id': article_id,
            'source_count': source_count
        })

    def log_sp_source_complete(self, source_id: str, status: str, drive_link: str = None):
        """Log completion of source pull for one source"""
        self.log_action('SP_SOURCE_COMPLETE', {
            'source_id': source_id,
            'status': status,
            'drive_link': drive_link
        })

    def log_sp_complete(self, article_id: str, success_count: int, fail_count: int):
        """Log completion of source pull"""
        self.log_action('SP_COMPLETE', {
            'article_id': article_id,
            'success_count': success_count,
            'fail_count': fail_count
        })

    def log_r1_start(self, article_id: str, source_count: int):
        """Log start of R1 processing"""
        self.log_action('R1_START', {
            'article_id': article_id,
            'source_count': source_count
        })

    def log_r1_source_complete(self, source_id: str, status: str, r1_drive_link: str = None):
        """Log completion of R1 for one source"""
        self.log_action('R1_SOURCE_COMPLETE', {
            'source_id': source_id,
            'status': status,
            'r1_drive_link': r1_drive_link
        })

    def log_r1_complete(self, article_id: str, success_count: int, fail_count: int):
        """Log completion of R1 processing"""
        self.log_action('R1_COMPLETE', {
            'article_id': article_id,
            'success_count': success_count,
            'fail_count': fail_count
        })

    def log_r2_start(self, article_id: str, footnote_count: int):
        """Log start of R2 validation"""
        self.log_action('R2_START', {
            'article_id': article_id,
            'footnote_count': footnote_count
        })

    def log_r2_citation_check(self, footnote_num: int, citation: str, issues: list):
        """Log R2 citation check"""
        self.log_action('R2_CITATION_CHECK', {
            'footnote_num': footnote_num,
            'citation': citation,
            'issues': issues,
            'has_issues': len(issues) > 0
        })

    def log_r2_complete(self, article_id: str, citations_checked: int, issues_found: int):
        """Log completion of R2 validation"""
        self.log_action('R2_COMPLETE', {
            'article_id': article_id,
            'citations_checked': citations_checked,
            'issues_found': issues_found
        })

    def log_error(self, error_type: str, error_message: str, context: dict = None):
        """Log an error"""
        self.log_action('ERROR', {
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {}
        })

    def get_session_summary(self) -> dict:
        """
        Get summary of current session

        Returns:
            Dict with session statistics
        """
        actions = []
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    actions.append(json.loads(line))

        summary = {
            'session_id': self.session_id,
            'action_count': len(actions),
            'action_types': {},
            'errors': []
        }

        for action in actions:
            action_type = action['action_type']
            summary['action_types'][action_type] = summary['action_types'].get(action_type, 0) + 1

            if action_type == 'ERROR':
                summary['errors'].append(action['details'])

        return summary


# Global logger instance
_logger = None


def get_logger() -> logging.Logger:
    """Get or create global logger"""
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger


def get_action_logger() -> ActionLogger:
    """Get or create global action logger"""
    return ActionLogger()
