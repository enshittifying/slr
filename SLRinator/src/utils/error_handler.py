"""
Enhanced Error Handling and Recovery Module
Provides robust error handling, recovery strategies, and logging
"""

import logging
import traceback
import functools
import time
import json
from typing import Any, Callable, Optional, Dict, List, Type
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    CRITICAL = "critical"  # System cannot continue
    HIGH = "high"         # Major functionality affected
    MEDIUM = "medium"     # Some functionality affected
    LOW = "low"          # Minor issue, can be ignored
    WARNING = "warning"   # Potential issue


class RecoveryStrategy(Enum):
    """Recovery strategies for errors"""
    RETRY = "retry"              # Retry the operation
    FALLBACK = "fallback"        # Use fallback method
    SKIP = "skip"               # Skip and continue
    CACHE = "cache"             # Use cached data
    DEFAULT = "default"         # Use default value
    MANUAL = "manual"           # Require manual intervention
    ABORT = "abort"             # Abort operation


@dataclass
class ErrorContext:
    """Context information for an error"""
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: datetime
    operation: str
    traceback: str
    recovery_attempted: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None
    recovery_successful: bool = False
    metadata: Dict[str, Any] = None


class ErrorHandler:
    """Centralized error handling and recovery"""
    
    def __init__(self, log_file: str = "errors.log", max_retries: int = 3):
        self.log_file = Path(log_file)
        self.max_retries = max_retries
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies: Dict[Type[Exception], RecoveryStrategy] = {
            # Network errors - retry
            ConnectionError: RecoveryStrategy.RETRY,
            TimeoutError: RecoveryStrategy.RETRY,
            
            # File errors - fallback
            FileNotFoundError: RecoveryStrategy.FALLBACK,
            PermissionError: RecoveryStrategy.SKIP,
            
            # Data errors - use default
            ValueError: RecoveryStrategy.DEFAULT,
            KeyError: RecoveryStrategy.DEFAULT,
            
            # Memory errors - abort
            MemoryError: RecoveryStrategy.ABORT,
            
            # Default - skip
            Exception: RecoveryStrategy.SKIP,
        }
        
        # Set up file handler for errors
        self._setup_error_logging()
    
    def _setup_error_logging(self):
        """Set up dedicated error logging"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def handle_error(self, error: Exception, operation: str = "Unknown",
                    severity: ErrorSeverity = None, 
                    metadata: Dict[str, Any] = None) -> ErrorContext:
        """Handle an error and determine recovery strategy"""
        
        # Determine severity if not provided
        if severity is None:
            severity = self._determine_severity(error)
        
        # Create error context
        context = ErrorContext(
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            timestamp=datetime.now(),
            operation=operation,
            traceback=traceback.format_exc(),
            metadata=metadata or {}
        )
        
        # Add to history
        self.error_history.append(context)
        
        # Log error
        self._log_error(context)
        
        # Determine recovery strategy
        context.recovery_strategy = self._determine_recovery_strategy(error)
        
        return context
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type"""
        critical_errors = (SystemExit, KeyboardInterrupt, MemoryError)
        high_errors = (IOError, OSError, RuntimeError)
        medium_errors = (ValueError, TypeError, AttributeError)
        low_errors = (Warning, DeprecationWarning)
        
        if isinstance(error, critical_errors):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, high_errors):
            return ErrorSeverity.HIGH
        elif isinstance(error, medium_errors):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, low_errors):
            return ErrorSeverity.LOW
        else:
            return ErrorSeverity.WARNING
    
    def _determine_recovery_strategy(self, error: Exception) -> RecoveryStrategy:
        """Determine appropriate recovery strategy"""
        for error_type, strategy in self.recovery_strategies.items():
            if isinstance(error, error_type):
                return strategy
        return RecoveryStrategy.SKIP
    
    def _log_error(self, context: ErrorContext):
        """Log error with appropriate level"""
        log_message = (
            f"Error in {context.operation}: {context.error_type} - "
            f"{context.error_message}"
        )
        
        if context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif context.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif context.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # Log full traceback for high severity errors
        if context.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.debug(f"Traceback:\n{context.traceback}")
    
    def recover(self, context: ErrorContext, retry_func: Callable = None,
               fallback_func: Callable = None, default_value: Any = None) -> Any:
        """Attempt to recover from an error"""
        
        context.recovery_attempted = True
        
        if context.recovery_strategy == RecoveryStrategy.RETRY and retry_func:
            return self._retry_operation(retry_func, context)
        
        elif context.recovery_strategy == RecoveryStrategy.FALLBACK and fallback_func:
            try:
                result = fallback_func()
                context.recovery_successful = True
                logger.info(f"Successfully used fallback for {context.operation}")
                return result
            except Exception as e:
                logger.error(f"Fallback failed: {e}")
                context.recovery_successful = False
        
        elif context.recovery_strategy == RecoveryStrategy.DEFAULT:
            context.recovery_successful = True
            return default_value
        
        elif context.recovery_strategy == RecoveryStrategy.SKIP:
            context.recovery_successful = True
            logger.info(f"Skipping failed operation: {context.operation}")
            return None
        
        elif context.recovery_strategy == RecoveryStrategy.ABORT:
            logger.critical(f"Aborting due to critical error in {context.operation}")
            raise SystemExit(1)
        
        return None
    
    def _retry_operation(self, func: Callable, context: ErrorContext) -> Any:
        """Retry an operation with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                # Exponential backoff
                if attempt > 0:
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying {context.operation} in {wait_time}s (attempt {attempt + 1})")
                    time.sleep(wait_time)
                
                result = func()
                context.recovery_successful = True
                logger.info(f"Successfully recovered {context.operation} after {attempt + 1} attempts")
                return result
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"All retry attempts failed for {context.operation}")
                    context.recovery_successful = False
                    raise
        
        return None
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors"""
        if not self.error_history:
            return {"total_errors": 0}
        
        summary = {
            "total_errors": len(self.error_history),
            "by_severity": {},
            "by_type": {},
            "by_operation": {},
            "recovery_stats": {
                "attempted": 0,
                "successful": 0,
                "failed": 0
            },
            "recent_errors": []
        }
        
        for context in self.error_history:
            # Count by severity
            severity = context.severity.value
            summary["by_severity"][severity] = summary["by_severity"].get(severity, 0) + 1
            
            # Count by type
            error_type = context.error_type
            summary["by_type"][error_type] = summary["by_type"].get(error_type, 0) + 1
            
            # Count by operation
            operation = context.operation
            summary["by_operation"][operation] = summary["by_operation"].get(operation, 0) + 1
            
            # Recovery stats
            if context.recovery_attempted:
                summary["recovery_stats"]["attempted"] += 1
                if context.recovery_successful:
                    summary["recovery_stats"]["successful"] += 1
                else:
                    summary["recovery_stats"]["failed"] += 1
        
        # Add recent errors
        for context in self.error_history[-10:]:
            summary["recent_errors"].append({
                "timestamp": context.timestamp.isoformat(),
                "operation": context.operation,
                "error": context.error_message,
                "severity": context.severity.value,
                "recovered": context.recovery_successful
            })
        
        return summary
    
    def save_error_report(self, output_path: str = "error_report.json"):
        """Save detailed error report"""
        report = {
            "generated": datetime.now().isoformat(),
            "summary": self.get_error_summary(),
            "errors": [
                {
                    "timestamp": ctx.timestamp.isoformat(),
                    "operation": ctx.operation,
                    "error_type": ctx.error_type,
                    "error_message": ctx.error_message,
                    "severity": ctx.severity.value,
                    "recovery_strategy": ctx.recovery_strategy.value if ctx.recovery_strategy else None,
                    "recovery_successful": ctx.recovery_successful,
                    "metadata": ctx.metadata
                }
                for ctx in self.error_history
            ]
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Error report saved to {output_path}")


def error_handled(handler: ErrorHandler = None, 
                 operation: str = None,
                 severity: ErrorSeverity = None,
                 fallback: Callable = None,
                 default: Any = None):
    """Decorator for automatic error handling"""
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided handler or create new one
            error_handler = handler or getattr(wrapper, '_handler', None)
            if not error_handler:
                error_handler = ErrorHandler()
                wrapper._handler = error_handler
            
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            try:
                return func(*args, **kwargs)
            
            except Exception as e:
                # Handle the error
                context = error_handler.handle_error(
                    e, 
                    operation=op_name,
                    severity=severity,
                    metadata={'args': len(args), 'kwargs': list(kwargs.keys())}
                )
                
                # Attempt recovery
                return error_handler.recover(
                    context,
                    retry_func=lambda: func(*args, **kwargs),
                    fallback_func=fallback,
                    default_value=default
                )
        
        return wrapper
    return decorator


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class InputValidator:
    """Validates and sanitizes input data"""
    
    @staticmethod
    def validate_citation(citation_text: str) -> str:
        """Validate and sanitize citation text"""
        if not citation_text:
            raise ValidationError("Citation text cannot be empty")
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '{', '}', '\\', '\0', '\x00']
        for char in dangerous_chars:
            citation_text = citation_text.replace(char, '')
        
        # Limit length
        max_length = 5000
        if len(citation_text) > max_length:
            citation_text = citation_text[:max_length]
            logger.warning(f"Citation truncated to {max_length} characters")
        
        # Remove excessive whitespace
        citation_text = ' '.join(citation_text.split())
        
        return citation_text
    
    @staticmethod
    def validate_filename(filename: str) -> str:
        """Validate and sanitize filename"""
        if not filename:
            raise ValidationError("Filename cannot be empty")
        
        # Remove path traversal attempts
        filename = Path(filename).name
        
        # Remove invalid characters
        invalid_chars = '<>:"|?*\0'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Handle reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 
                         'COM3', 'COM4', 'LPT1', 'LPT2', 'LPT3']
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            filename = f"_{filename}"
        
        # Limit length
        max_length = 255
        if len(filename) > max_length:
            ext = Path(filename).suffix
            stem = Path(filename).stem[:max_length - len(ext) - 1]
            filename = f"{stem}{ext}"
        
        return filename
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate and sanitize URL"""
        if not url:
            raise ValidationError("URL cannot be empty")
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            raise ValidationError("URL must start with http:// or https://")
        
        # Remove dangerous characters
        url = url.replace('\n', '').replace('\r', '').replace('\t', '')
        
        # Limit length
        max_length = 2000
        if len(url) > max_length:
            raise ValidationError(f"URL too long: {len(url)} > {max_length}")
        
        return url
    
    @staticmethod
    def validate_spreadsheet_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate spreadsheet data"""
        if not data:
            raise ValidationError("Spreadsheet data cannot be empty")
        
        # Validate required fields
        required_fields = ['source_id', 'citation']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Sanitize string fields
        for key, value in data.items():
            if isinstance(value, str):
                # Remove formula injection attempts
                if value.startswith(('=', '+', '-', '@')):
                    data[key] = f"'{value}"
                
                # Limit cell content length
                max_cell_length = 32767  # Excel limit
                if len(value) > max_cell_length:
                    data[key] = value[:max_cell_length]
        
        return data