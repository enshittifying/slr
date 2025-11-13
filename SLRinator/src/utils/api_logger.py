#!/usr/bin/env python3
"""
Secure API Usage Logger for Stanford Law Review
Logs all API key usage in an immutable, append-only format for security auditing
"""

import os
import json
import hashlib
import fcntl
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import threading


class APIUsageLogger:
    """
    Secure, append-only API usage logger with file locking
    Ensures immutable audit trail of all API usage
    """
    
    def __init__(self, log_dir: str = "output/logs/api_usage"):
        """Initialize the API usage logger"""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create daily log file
        today = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"api_usage_{today}.log"
        
        # Thread lock for concurrent access
        self.lock = threading.Lock()
        
        # Initialize log file with header if new
        if not self.log_file.exists():
            self._write_header()
    
    def _write_header(self):
        """Write header to new log file"""
        header = {
            "log_type": "API_USAGE_LOG",
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "format": "JSONL",
            "description": "Stanford Law Review API Usage Audit Log"
        }
        
        with open(self.log_file, 'a') as f:
            # Use file locking for exclusive access
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(f"# {json.dumps(header)}\n")
                f.write("# Each subsequent line is a JSON object representing an API call\n")
                f.write("#" + "="*70 + "\n")
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    
    def log_api_call(self, 
                     api_name: str,
                     endpoint: str,
                     method: str = "GET",
                     parameters: Optional[Dict[str, Any]] = None,
                     response_code: Optional[int] = None,
                     success: bool = False,
                     error_message: Optional[str] = None,
                     footnote_number: Optional[int] = None,
                     citation_text: Optional[str] = None,
                     call_reason: Optional[str] = None,
                     expected_result: Optional[str] = None,
                     citation_type: Optional[str] = None,
                     retrieval_strategy: Optional[str] = None,
                     additional_metadata: Optional[Dict[str, Any]] = None):
        """
        Log an API call with all relevant details and contextual information
        
        Args:
            api_name: Name of the API service (courtlistener, govinfo, etc.)
            endpoint: The API endpoint called
            method: HTTP method used
            parameters: Query parameters (sensitive data will be masked)
            response_code: HTTP response code
            success: Whether the call was successful
            error_message: Any error message received
            footnote_number: Associated footnote number if applicable
            citation_text: Associated citation text if applicable
            call_reason: Explanation of why this API call was made
            expected_result: What we expected to get from this call
            citation_type: Type of citation being retrieved (case, statute, etc.)
            retrieval_strategy: Current retrieval strategy being attempted
            additional_metadata: Any additional context about the call
        """
        with self.lock:
            # Create log entry
            entry = {
                "timestamp": datetime.now().isoformat(),
                "api_name": api_name,
                "endpoint": endpoint,
                "method": method,
                "response_code": response_code,
                "success": success,
                "footnote_number": footnote_number
            }
            
            # Add sanitized parameters (mask sensitive data)
            if parameters:
                entry["parameters"] = self._sanitize_parameters(parameters)
            
            # Add error info if present
            if error_message:
                entry["error"] = error_message
            
            # Add citation info if present (truncated for security)
            if citation_text:
                entry["citation_preview"] = citation_text[:100] if citation_text else None
            
            # Add enhanced contextual information
            if call_reason:
                entry["call_reason"] = call_reason
            
            if expected_result:
                entry["expected_result"] = expected_result
                
            if citation_type:
                entry["citation_type"] = citation_type
                
            if retrieval_strategy:
                entry["retrieval_strategy"] = retrieval_strategy
            
            # Add additional metadata
            if additional_metadata:
                entry["metadata"] = self._sanitize_parameters(additional_metadata)
            
            # Calculate checksum for integrity
            entry["checksum"] = self._calculate_checksum(entry)
            
            # Write to log file with locking
            self._append_to_log(entry)
    
    def _sanitize_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters to mask sensitive data"""
        sanitized = {}
        sensitive_keys = {'token', 'api_key', 'password', 'secret', 'auth'}
        
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                # Mask sensitive values but show they were present
                if value:
                    sanitized[key] = f"***{str(value)[-4:]}" if len(str(value)) > 4 else "***"
                else:
                    sanitized[key] = None
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _calculate_checksum(self, entry: Dict[str, Any]) -> str:
        """Calculate SHA256 checksum of entry for integrity verification"""
        # Remove checksum field if present
        entry_copy = {k: v for k, v in entry.items() if k != 'checksum'}
        entry_json = json.dumps(entry_copy, sort_keys=True)
        return hashlib.sha256(entry_json.encode()).hexdigest()[:16]
    
    def _append_to_log(self, entry: Dict[str, Any]):
        """Append entry to log file with file locking"""
        try:
            with open(self.log_file, 'a') as f:
                # Use file locking for exclusive access
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                try:
                    f.write(json.dumps(entry) + '\n')
                    f.flush()  # Ensure immediate write
                    os.fsync(f.fileno())  # Force write to disk
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except Exception as e:
            # If logging fails, print to stderr but don't crash
            import sys
            print(f"WARNING: Failed to log API usage: {e}", file=sys.stderr)
    
    def verify_log_integrity(self) -> bool:
        """Verify the integrity of the log file by checking checksums"""
        if not self.log_file.exists():
            return True
        
        try:
            with open(self.log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    # Skip comment lines
                    if line.startswith('#'):
                        continue
                    
                    try:
                        entry = json.loads(line.strip())
                        if 'checksum' in entry:
                            expected = entry['checksum']
                            actual = self._calculate_checksum(entry)
                            if expected != actual:
                                print(f"Integrity check failed at line {line_num}")
                                return False
                    except json.JSONDecodeError:
                        print(f"Invalid JSON at line {line_num}")
                        return False
            
            return True
        except Exception as e:
            print(f"Error verifying log integrity: {e}")
            return False
    
    def get_usage_summary(self, api_name: Optional[str] = None) -> Dict[str, Any]:
        """Get usage summary from the log file"""
        if not self.log_file.exists():
            return {"total_calls": 0, "successful_calls": 0, "failed_calls": 0}
        
        summary = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "by_api": {}
        }
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        continue
                    
                    try:
                        entry = json.loads(line.strip())
                        
                        # Filter by API name if specified
                        if api_name and entry.get('api_name') != api_name:
                            continue
                        
                        summary["total_calls"] += 1
                        
                        if entry.get('success'):
                            summary["successful_calls"] += 1
                        else:
                            summary["failed_calls"] += 1
                        
                        # Count by API
                        api = entry.get('api_name', 'unknown')
                        if api not in summary["by_api"]:
                            summary["by_api"][api] = {"total": 0, "success": 0, "failed": 0}
                        
                        summary["by_api"][api]["total"] += 1
                        if entry.get('success'):
                            summary["by_api"][api]["success"] += 1
                        else:
                            summary["by_api"][api]["failed"] += 1
                            
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"Error reading usage summary: {e}")
        
        return summary


# Global logger instance
_logger_instance = None


def get_api_logger() -> APIUsageLogger:
    """Get or create the global API logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = APIUsageLogger()
    return _logger_instance


def log_api_usage(api_name: str, endpoint: str, method: str = "GET", 
                  response_code: Optional[int] = None, success: Optional[bool] = None,
                  parameters: Optional[Dict] = None, error_message: Optional[str] = None,
                  footnote_number: Optional[int] = None, citation_text: Optional[str] = None,
                  call_reason: Optional[str] = None, expected_result: Optional[str] = None,
                  citation_type: Optional[str] = None, retrieval_strategy: Optional[str] = None,
                  additional_metadata: Optional[Dict] = None):
    """
    Convenience function to log API usage with enhanced context
    
    Args:
        api_name: Name of the API service
        endpoint: API endpoint URL
        method: HTTP method
        response_code: HTTP response code
        success: Whether call succeeded
        parameters: API parameters (sensitive data masked)
        error_message: Error message if failed
        footnote_number: Associated footnote number
        citation_text: Citation being processed
        call_reason: Why this API call was made
        expected_result: What we expected to get
        citation_type: Type of citation (case, statute, etc.)
        retrieval_strategy: Current retrieval strategy
        additional_metadata: Extra context about the call
    """
    logger = get_api_logger()
    logger.log_api_call(
        api_name=api_name,
        endpoint=endpoint,
        method=method,
        parameters=parameters,
        response_code=response_code,
        success=success,
        error_message=error_message,
        footnote_number=footnote_number,
        citation_text=citation_text,
        call_reason=call_reason,
        expected_result=expected_result,
        citation_type=citation_type,
        retrieval_strategy=retrieval_strategy,
        additional_metadata=additional_metadata
    )


def verify_api_logs() -> bool:
    """Verify the integrity of API logs"""
    logger = get_api_logger()
    return logger.verify_log_integrity()


def get_api_usage_summary(api_name: Optional[str] = None) -> Dict[str, Any]:
    """Get API usage summary"""
    logger = get_api_logger()
    return logger.get_usage_summary(api_name)


if __name__ == "__main__":
    # Test the logger
    logger = APIUsageLogger()
    
    # Test logging
    logger.log_api_call(
        api_name="courtlistener",
        endpoint="/api/rest/v3/search/",
        method="GET",
        parameters={"q": "Alice Corp", "token": "secret123"},
        response_code=200,
        success=True,
        footnote_number=1,
        citation_text="Alice Corp. v. CLS Bank Int'l, 573 U.S. 208 (2014)"
    )
    
    logger.log_api_call(
        api_name="govinfo",
        endpoint="/collections/USCODE/",
        method="GET",
        parameters={"api_key": "key456"},
        response_code=404,
        success=False,
        error_message="Document not found",
        footnote_number=3,
        citation_text="35 U.S.C. § 101"
    )
    
    # Verify integrity
    print("Log integrity check:", logger.verify_log_integrity())
    
    # Get summary
    summary = logger.get_usage_summary()
    print("\nUsage Summary:")
    print(json.dumps(summary, indent=2))