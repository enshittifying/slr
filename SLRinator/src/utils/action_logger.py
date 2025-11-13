#!/usr/bin/env python3
"""
Action Logger for SLRinator System
Tracks all system operations with comprehensive logging
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import hashlib
import traceback


class ActionLogger:
    """
    Comprehensive action logging system for SLRinator
    Tracks all operations, API calls, and system events
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """Initialize action logger"""
        self.log_dir = log_dir or Path("output/logs/actions")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create daily log file
        self.log_date = datetime.now().strftime("%Y%m%d")
        self.log_file = self.log_dir / f"actions_{self.log_date}.log"
        self.json_log_file = self.log_dir / f"actions_{self.log_date}.json"
        
        # Setup text logger
        self.logger = logging.getLogger('action_logger')
        self.logger.setLevel(logging.DEBUG)
        
        # File handler for detailed logs
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.DEBUG)
        
        # Console handler for important messages
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - [%(levelname)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)
        
        # Initialize JSON log
        self.json_logs = []
        self._load_existing_json_logs()
        
        # Session tracking
        self.session_id = self._generate_session_id()
        self.action_count = 0
        
        # Log session start
        self.log_action(
            action="SESSION_START",
            details={"session_id": self.session_id},
            level="INFO"
        )
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    def _load_existing_json_logs(self):
        """Load existing JSON logs if they exist"""
        if self.json_log_file.exists():
            try:
                with open(self.json_log_file, 'r') as f:
                    self.json_logs = json.load(f)
            except:
                self.json_logs = []
    
    def _save_json_logs(self):
        """Save JSON logs to file"""
        try:
            with open(self.json_log_file, 'w') as f:
                json.dump(self.json_logs, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save JSON logs: {e}")
    
    def log_action(self, action: str, details: Dict[str, Any] = None, 
                   level: str = "INFO", status: str = "SUCCESS") -> str:
        """
        Log an action with comprehensive details
        
        Args:
            action: Action name/type
            details: Additional action details
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            status: Action status (SUCCESS, FAILED, PENDING, IN_PROGRESS)
        
        Returns:
            Action ID for reference
        """
        self.action_count += 1
        action_id = f"{self.session_id}_{self.action_count:04d}"
        
        # Create action record
        action_record = {
            "action_id": action_id,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "action": action,
            "status": status,
            "level": level,
            "details": details or {}
        }
        
        # Add to JSON logs
        self.json_logs.append(action_record)
        self._save_json_logs()
        
        # Log to text file
        log_message = f"[{action_id}] {action} - {status}"
        if details:
            log_message += f" - {json.dumps(details, default=str)}"
        
        # Log at appropriate level
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "CRITICAL":
            self.logger.critical(log_message)
        else:
            self.logger.info(log_message)
        
        return action_id
    
    def log_api_call(self, api_name: str, endpoint: str, 
                     params: Dict[str, Any] = None,
                     response_status: int = None,
                     response_data: Any = None,
                     error: str = None) -> str:
        """Log API call with details"""
        details = {
            "api_name": api_name,
            "endpoint": endpoint,
            "params": params or {},
            "response_status": response_status,
            "error": error
        }
        
        # Add response preview if available
        if response_data:
            if isinstance(response_data, dict):
                details["response_preview"] = str(response_data)[:500]
            else:
                details["response_preview"] = str(response_data)[:500]
        
        status = "SUCCESS" if response_status and 200 <= response_status < 300 else "FAILED"
        level = "INFO" if status == "SUCCESS" else "ERROR"
        
        return self.log_action(
            action=f"API_CALL_{api_name.upper()}",
            details=details,
            level=level,
            status=status
        )
    
    def log_file_operation(self, operation: str, file_path: str,
                          success: bool = True, error: str = None,
                          metadata: Dict[str, Any] = None) -> str:
        """Log file operation"""
        details = {
            "operation": operation,
            "file_path": str(file_path),
            "metadata": metadata or {}
        }
        
        if error:
            details["error"] = error
        
        status = "SUCCESS" if success else "FAILED"
        level = "INFO" if success else "ERROR"
        
        return self.log_action(
            action=f"FILE_{operation.upper()}",
            details=details,
            level=level,
            status=status
        )
    
    def log_citation_parsing(self, footnote_num: int, 
                           citation_text: str,
                           parser_type: str,
                           citations_found: int,
                           confidence: float = None,
                           error: str = None) -> str:
        """Log citation parsing operation"""
        details = {
            "footnote_number": footnote_num,
            "citation_text": citation_text[:200],
            "parser_type": parser_type,
            "citations_found": citations_found,
            "confidence": confidence
        }
        
        if error:
            details["error"] = error
        
        status = "SUCCESS" if citations_found > 0 else "FAILED"
        level = "INFO" if status == "SUCCESS" else "WARNING"
        
        return self.log_action(
            action="CITATION_PARSING",
            details=details,
            level=level,
            status=status
        )
    
    def log_pdf_retrieval(self, citation_id: str, source: str,
                         success: bool = True, file_path: str = None,
                         error: str = None, metadata: Dict[str, Any] = None) -> str:
        """Log PDF retrieval operation"""
        details = {
            "citation_id": citation_id,
            "source": source,
            "file_path": file_path,
            "metadata": metadata or {}
        }
        
        if error:
            details["error"] = error
        
        status = "SUCCESS" if success else "FAILED"
        level = "INFO" if success else "WARNING"
        
        return self.log_action(
            action="PDF_RETRIEVAL",
            details=details,
            level=level,
            status=status
        )
    
    def log_error(self, error_type: str, error_message: str,
                 traceback_info: str = None, context: Dict[str, Any] = None) -> str:
        """Log error with full traceback"""
        details = {
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }
        
        if traceback_info:
            details["traceback"] = traceback_info
        else:
            details["traceback"] = traceback.format_exc()
        
        return self.log_action(
            action="ERROR",
            details=details,
            level="ERROR",
            status="FAILED"
        )
    
    def log_workflow_step(self, step_name: str, step_number: int,
                         total_steps: int, status: str = "IN_PROGRESS",
                         details: Dict[str, Any] = None) -> str:
        """Log workflow step progress"""
        step_details = {
            "step_name": step_name,
            "step_number": step_number,
            "total_steps": total_steps,
            "progress_percentage": round((step_number / total_steps) * 100, 2)
        }
        
        if details:
            step_details.update(details)
        
        level = "INFO"
        if status == "FAILED":
            level = "ERROR"
        elif status == "WARNING":
            level = "WARNING"
        
        return self.log_action(
            action="WORKFLOW_STEP",
            details=step_details,
            level=level,
            status=status
        )
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of current session"""
        summary = {
            "session_id": self.session_id,
            "start_time": self.json_logs[0]["timestamp"] if self.json_logs else None,
            "end_time": datetime.now().isoformat(),
            "total_actions": self.action_count,
            "action_breakdown": {},
            "status_breakdown": {},
            "api_calls": [],
            "errors": [],
            "files_processed": []
        }
        
        # Analyze logs
        for log in self.json_logs:
            if log["session_id"] != self.session_id:
                continue
            
            # Count by action type
            action_type = log["action"]
            summary["action_breakdown"][action_type] = \
                summary["action_breakdown"].get(action_type, 0) + 1
            
            # Count by status
            status = log["status"]
            summary["status_breakdown"][status] = \
                summary["status_breakdown"].get(status, 0) + 1
            
            # Collect API calls
            if "API_CALL" in action_type:
                summary["api_calls"].append({
                    "api": log["details"].get("api_name"),
                    "endpoint": log["details"].get("endpoint"),
                    "status": log["status"],
                    "timestamp": log["timestamp"]
                })
            
            # Collect errors
            if log["status"] == "FAILED" or log["level"] == "ERROR":
                summary["errors"].append({
                    "action": action_type,
                    "error": log["details"].get("error", "Unknown error"),
                    "timestamp": log["timestamp"]
                })
            
            # Collect files
            if "FILE_" in action_type:
                summary["files_processed"].append({
                    "operation": log["details"].get("operation"),
                    "file": log["details"].get("file_path"),
                    "status": log["status"],
                    "timestamp": log["timestamp"]
                })
        
        # Calculate success rate
        total = sum(summary["status_breakdown"].values())
        success = summary["status_breakdown"].get("SUCCESS", 0)
        summary["success_rate"] = round((success / total * 100), 2) if total > 0 else 0
        
        return summary
    
    def save_summary_report(self, output_path: Optional[Path] = None):
        """Save summary report to file"""
        if not output_path:
            output_path = self.log_dir / f"summary_{self.session_id}.json"
        
        summary = self.generate_summary_report()
        
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.log_action(
            action="SUMMARY_REPORT_GENERATED",
            details={"report_path": str(output_path)},
            level="INFO"
        )
        
        return output_path


# Global action logger instance
_action_logger = None

def get_action_logger() -> ActionLogger:
    """Get or create global action logger instance"""
    global _action_logger
    if _action_logger is None:
        _action_logger = ActionLogger()
    return _action_logger


# Convenience functions
def log_action(*args, **kwargs):
    """Convenience function to log action"""
    return get_action_logger().log_action(*args, **kwargs)

def log_api_call(*args, **kwargs):
    """Convenience function to log API call"""
    return get_action_logger().log_api_call(*args, **kwargs)

def log_file_operation(*args, **kwargs):
    """Convenience function to log file operation"""
    return get_action_logger().log_file_operation(*args, **kwargs)

def log_error(*args, **kwargs):
    """Convenience function to log error"""
    return get_action_logger().log_error(*args, **kwargs)

def log_workflow_step(*args, **kwargs):
    """Convenience function to log workflow step"""
    return get_action_logger().log_workflow_step(*args, **kwargs)