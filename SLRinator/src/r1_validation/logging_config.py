"""
Advanced Logging and Monitoring Configuration for R1 Validation
Provides structured logging, performance monitoring, and audit trails
"""
import logging
import sys
import time
import json
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import functools


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as structured JSON.

        Args:
            record: Log record

        Returns:
            JSON formatted string
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "citation_num"):
            log_data["citation_num"] = record.citation_num
        if hasattr(record, "footnote_num"):
            log_data["footnote_num"] = record.footnote_num
        if hasattr(record, "workflow_id"):
            log_data["workflow_id"] = record.workflow_id
        if hasattr(record, "cost"):
            log_data["cost"] = record.cost
        if hasattr(record, "tokens"):
            log_data["tokens"] = record.tokens
        if hasattr(record, "duration"):
            log_data["duration"] = record.duration

        return json.dumps(log_data)


class PerformanceLogger:
    """
    Tracks and logs performance metrics.
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize performance logger.

        Args:
            logger: Parent logger
        """
        self.logger = logger
        self.metrics = []

    def log_performance(self, operation: str, duration: float, metadata: Dict = None):
        """
        Log performance metric.

        Args:
            operation: Operation name
            duration: Duration in seconds
            metadata: Additional metadata
        """
        metric = {
            "timestamp": time.time(),
            "operation": operation,
            "duration_seconds": duration,
            "metadata": metadata or {}
        }
        self.metrics.append(metric)

        # Log with structured data
        extra = {
            "duration": duration,
            **metric["metadata"]
        }
        self.logger.info(f"Performance: {operation} took {duration:.3f}s", extra=extra)

    def get_summary(self) -> Dict:
        """Get performance summary statistics."""
        if not self.metrics:
            return {}

        operations = {}
        for metric in self.metrics:
            op = metric["operation"]
            duration = metric["duration_seconds"]

            if op not in operations:
                operations[op] = []
            operations[op].append(duration)

        summary = {}
        for op, durations in operations.items():
            summary[op] = {
                "count": len(durations),
                "total": sum(durations),
                "average": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations)
            }

        return summary


class AuditLogger:
    """
    Audit trail logger for compliance and debugging.
    """

    def __init__(self, audit_file: Path = None):
        """
        Initialize audit logger.

        Args:
            audit_file: Path to audit log file
        """
        if audit_file is None:
            audit_dir = Path.cwd() / "output" / "audit"
            audit_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now().strftime("%Y%m%d")
            audit_file = audit_dir / f"audit_{date_str}.jsonl"

        self.audit_file = audit_file
        self.logger = logging.getLogger("audit")

    def log_action(self, action: str, user: str = "system", details: Dict = None):
        """
        Log an auditable action.

        Args:
            action: Action description
            user: User performing action
            details: Additional details
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "user": user,
            "details": details or {}
        }

        # Append to audit file
        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        self.logger.info(f"Audit: {action}", extra={"user": user, **entry["details"]})

    def log_citation_validation(self, citation_num: int, is_correct: bool, errors: list):
        """Log citation validation event."""
        self.log_action(
            action="citation_validation",
            details={
                "citation_num": citation_num,
                "is_correct": is_correct,
                "error_count": len(errors)
            }
        )

    def log_api_call(self, endpoint: str, cost: float, tokens: int):
        """Log API call event."""
        self.log_action(
            action="api_call",
            details={
                "endpoint": endpoint,
                "cost": cost,
                "tokens": tokens
            }
        )

    def log_workflow_start(self, workflow_id: str, document_path: str):
        """Log workflow start event."""
        self.log_action(
            action="workflow_start",
            details={
                "workflow_id": workflow_id,
                "document_path": document_path
            }
        )

    def log_workflow_complete(self, workflow_id: str, total_citations: int, success_rate: float):
        """Log workflow completion event."""
        self.log_action(
            action="workflow_complete",
            details={
                "workflow_id": workflow_id,
                "total_citations": total_citations,
                "success_rate": success_rate
            }
        )


def setup_logging(
    log_dir: Path = None,
    log_level: str = "INFO",
    enable_console: bool = True,
    enable_file: bool = True,
    enable_structured: bool = False,
    max_file_size_mb: int = 10,
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup comprehensive logging configuration.

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Enable console logging
        enable_file: Enable file logging
        enable_structured: Use structured JSON logging
        max_file_size_mb: Max log file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured root logger
    """
    if log_dir is None:
        log_dir = Path.cwd() / "output" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        if enable_structured:
            console_handler.setFormatter(StructuredFormatter())
        else:
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)

        root_logger.addHandler(console_handler)

    # File handlers
    if enable_file:
        # Main log file (rotating by size)
        main_log_file = log_dir / "r1_validation.log"
        file_handler = RotatingFileHandler(
            main_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)

        if enable_structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)

        root_logger.addHandler(file_handler)

        # Error log file (errors only)
        error_log_file = log_dir / "r1_errors.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter if not enable_structured else StructuredFormatter())
        root_logger.addHandler(error_handler)

        # Daily log file (rotating by time)
        daily_log_file = log_dir / "r1_daily.log"
        daily_handler = TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30  # Keep 30 days
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(file_formatter if not enable_structured else StructuredFormatter())
        root_logger.addHandler(daily_handler)

    # Configure specific loggers
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    return root_logger


def log_function_call(logger: logging.Logger = None):
    """
    Decorator to log function calls with timing.

    Args:
        logger: Logger to use (defaults to function's module logger)

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = logging.getLogger(func.__module__)

            func_name = func.__name__
            logger.debug(f"Calling {func_name}")

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.debug(f"{func_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"{func_name} failed after {duration:.3f}s: {e}", exc_info=True)
                raise

        return wrapper
    return decorator


def log_citation_processing(citation_num: int):
    """
    Decorator to log citation processing.

    Args:
        citation_num: Citation number

    Returns:
        Decorated function
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            logger.info(f"Processing citation {citation_num}", extra={"citation_num": citation_num})

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    f"Citation {citation_num} processed successfully",
                    extra={"citation_num": citation_num, "duration": duration}
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    f"Citation {citation_num} processing failed: {e}",
                    extra={"citation_num": citation_num, "duration": duration},
                    exc_info=True
                )
                raise

        return wrapper
    return decorator


class CostTracker:
    """
    Tracks and logs API costs.
    """

    def __init__(self):
        """Initialize cost tracker."""
        self.total_cost = 0.0
        self.total_tokens = 0
        self.api_calls = []
        self.logger = logging.getLogger("cost_tracker")

    def log_api_cost(self, cost: float, tokens: int, operation: str = "api_call"):
        """
        Log API cost.

        Args:
            cost: Cost in USD
            tokens: Number of tokens
            operation: Operation name
        """
        self.total_cost += cost
        self.total_tokens += tokens

        call_data = {
            "timestamp": time.time(),
            "operation": operation,
            "cost": cost,
            "tokens": tokens
        }
        self.api_calls.append(call_data)

        self.logger.info(
            f"{operation}: ${cost:.4f} ({tokens} tokens)",
            extra={"cost": cost, "tokens": tokens}
        )

    def get_summary(self) -> Dict:
        """Get cost summary."""
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "total_calls": len(self.api_calls),
            "average_cost_per_call": self.total_cost / len(self.api_calls) if self.api_calls else 0,
            "average_tokens_per_call": self.total_tokens // len(self.api_calls) if self.api_calls else 0
        }

    def reset(self):
        """Reset cost tracking."""
        self.total_cost = 0.0
        self.total_tokens = 0
        self.api_calls = []
        self.logger.info("Cost tracker reset")
