"""
Resource Monitoring for R1 Validation
Tracks system resources and prevents resource exhaustion
"""
import time
import psutil
import logging
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from pathlib import Path
from threading import Thread, Event
import functools

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limit configuration."""
    max_memory_percent: float = 85.0  # Max memory usage %
    max_disk_percent: float = 90.0    # Max disk usage %
    max_cpu_percent: float = 95.0     # Max CPU usage %
    min_free_memory_gb: float = 1.0   # Min free memory in GB
    min_free_disk_gb: float = 5.0     # Min free disk in GB
    check_interval_seconds: int = 10  # Resource check interval


@dataclass
class ResourceSnapshot:
    """Snapshot of system resources at a point in time."""
    timestamp: float
    memory_percent: float
    memory_available_gb: float
    memory_used_gb: float
    disk_percent: float
    disk_free_gb: float
    disk_used_gb: float
    cpu_percent: float
    process_memory_mb: float
    process_cpu_percent: float


class ResourceMonitor:
    """
    Monitors system resources during R1 workflow execution.
    Prevents resource exhaustion and provides warnings.
    """

    def __init__(self, limits: ResourceLimits = None):
        """
        Initialize resource monitor.

        Args:
            limits: Resource limits configuration
        """
        self.limits = limits or ResourceLimits()
        self.snapshots = []
        self.warnings_issued = set()
        self.process = psutil.Process()

    def get_current_snapshot(self) -> ResourceSnapshot:
        """
        Get current resource usage snapshot.

        Returns:
            ResourceSnapshot
        """
        # System resources
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(Path.cwd())
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # Process resources
        process_memory = self.process.memory_info().rss / (1024 * 1024)  # MB
        try:
            process_cpu = self.process.cpu_percent(interval=0.1)
        except Exception:
            process_cpu = 0.0

        snapshot = ResourceSnapshot(
            timestamp=time.time(),
            memory_percent=memory.percent,
            memory_available_gb=memory.available / (1024 ** 3),
            memory_used_gb=memory.used / (1024 ** 3),
            disk_percent=disk.percent,
            disk_free_gb=disk.free / (1024 ** 3),
            disk_used_gb=disk.used / (1024 ** 3),
            cpu_percent=cpu_percent,
            process_memory_mb=process_memory,
            process_cpu_percent=process_cpu
        )

        self.snapshots.append(snapshot)
        return snapshot

    def check_resources(self) -> Dict[str, Any]:
        """
        Check if resources are within limits.

        Returns:
            Dict with status and violations
        """
        snapshot = self.get_current_snapshot()
        violations = []
        warnings = []

        # Check memory
        if snapshot.memory_percent > self.limits.max_memory_percent:
            violations.append({
                "resource": "memory",
                "severity": "critical",
                "message": f"Memory usage {snapshot.memory_percent:.1f}% exceeds limit {self.limits.max_memory_percent:.1f}%",
                "current": snapshot.memory_percent,
                "limit": self.limits.max_memory_percent
            })
        elif snapshot.memory_available_gb < self.limits.min_free_memory_gb:
            warnings.append({
                "resource": "memory",
                "severity": "warning",
                "message": f"Low free memory: {snapshot.memory_available_gb:.2f} GB",
                "current": snapshot.memory_available_gb,
                "limit": self.limits.min_free_memory_gb
            })

        # Check disk
        if snapshot.disk_percent > self.limits.max_disk_percent:
            violations.append({
                "resource": "disk",
                "severity": "critical",
                "message": f"Disk usage {snapshot.disk_percent:.1f}% exceeds limit {self.limits.max_disk_percent:.1f}%",
                "current": snapshot.disk_percent,
                "limit": self.limits.max_disk_percent
            })
        elif snapshot.disk_free_gb < self.limits.min_free_disk_gb:
            warnings.append({
                "resource": "disk",
                "severity": "warning",
                "message": f"Low free disk space: {snapshot.disk_free_gb:.2f} GB",
                "current": snapshot.disk_free_gb,
                "limit": self.limits.min_free_disk_gb
            })

        # Check CPU
        if snapshot.cpu_percent > self.limits.max_cpu_percent:
            warnings.append({
                "resource": "cpu",
                "severity": "warning",
                "message": f"High CPU usage: {snapshot.cpu_percent:.1f}%",
                "current": snapshot.cpu_percent,
                "limit": self.limits.max_cpu_percent
            })

        # Log violations
        for violation in violations:
            logger.error(f"Resource violation: {violation['message']}")

        for warning in warnings:
            # Only log each warning type once per session
            warning_key = f"{warning['resource']}_{warning['severity']}"
            if warning_key not in self.warnings_issued:
                logger.warning(f"Resource warning: {warning['message']}")
                self.warnings_issued.add(warning_key)

        return {
            "ok": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "snapshot": snapshot
        }

    def can_proceed(self) -> bool:
        """
        Check if workflow can proceed based on resources.

        Returns:
            True if resources are sufficient
        """
        result = self.check_resources()
        return result["ok"]

    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get resource usage summary.

        Returns:
            Summary statistics
        """
        if not self.snapshots:
            self.get_current_snapshot()

        if not self.snapshots:
            return {}

        # Calculate statistics
        memory_usage = [s.memory_percent for s in self.snapshots]
        disk_usage = [s.disk_percent for s in self.snapshots]
        cpu_usage = [s.cpu_percent for s in self.snapshots]
        process_memory = [s.process_memory_mb for s in self.snapshots]

        latest = self.snapshots[-1]

        return {
            "current": {
                "memory_percent": latest.memory_percent,
                "memory_available_gb": latest.memory_available_gb,
                "disk_percent": latest.disk_percent,
                "disk_free_gb": latest.disk_free_gb,
                "cpu_percent": latest.cpu_percent,
                "process_memory_mb": latest.process_memory_mb
            },
            "peak": {
                "memory_percent": max(memory_usage),
                "disk_percent": max(disk_usage),
                "cpu_percent": max(cpu_usage),
                "process_memory_mb": max(process_memory)
            },
            "average": {
                "memory_percent": sum(memory_usage) / len(memory_usage),
                "disk_percent": sum(disk_usage) / len(disk_usage),
                "cpu_percent": sum(cpu_usage) / len(cpu_usage),
                "process_memory_mb": sum(process_memory) / len(process_memory)
            },
            "snapshots_count": len(self.snapshots),
            "duration_seconds": latest.timestamp - self.snapshots[0].timestamp if len(self.snapshots) > 1 else 0
        }

    def reset(self):
        """Reset monitoring data."""
        self.snapshots = []
        self.warnings_issued = set()


class BackgroundResourceMonitor:
    """
    Background thread that continuously monitors resources.
    """

    def __init__(self, limits: ResourceLimits = None, on_violation: Optional[Callable] = None):
        """
        Initialize background monitor.

        Args:
            limits: Resource limits
            on_violation: Callback when violation detected
        """
        self.monitor = ResourceMonitor(limits)
        self.on_violation = on_violation
        self.stop_event = Event()
        self.thread: Optional[Thread] = None
        self.running = False

    def start(self):
        """Start background monitoring."""
        if self.running:
            logger.warning("Background monitor already running")
            return

        self.running = True
        self.stop_event.clear()
        self.thread = Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        logger.info("Background resource monitoring started")

    def stop(self):
        """Stop background monitoring."""
        if not self.running:
            return

        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background resource monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while not self.stop_event.is_set():
            try:
                result = self.monitor.check_resources()

                if not result["ok"] and self.on_violation:
                    self.on_violation(result)

                # Wait for next check
                self.stop_event.wait(self.monitor.limits.check_interval_seconds)

            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}", exc_info=True)
                self.stop_event.wait(self.monitor.limits.check_interval_seconds)

    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary."""
        return self.monitor.get_resource_summary()


def with_resource_check(monitor: ResourceMonitor = None):
    """
    Decorator to check resources before function execution.

    Args:
        monitor: ResourceMonitor instance (creates new if None)

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal monitor
            if monitor is None:
                monitor = ResourceMonitor()

            # Check resources before execution
            if not monitor.can_proceed():
                result = monitor.check_resources()
                violations = result.get("violations", [])
                error_msg = "Cannot proceed due to resource constraints: " + \
                           ", ".join(v["message"] for v in violations)
                raise ResourceError(error_msg)

            # Execute function
            return func(*args, **kwargs)

        return wrapper
    return decorator


def monitor_resources(func: Callable) -> Callable:
    """
    Decorator to monitor resources during function execution.

    Args:
        func: Function to monitor

    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        monitor = ResourceMonitor()

        # Initial check
        monitor.get_current_snapshot()

        try:
            # Execute function
            result = func(*args, **kwargs)

            # Final check
            monitor.get_current_snapshot()

            # Log summary
            summary = monitor.get_resource_summary()
            logger.info(
                f"Resource usage for {func.__name__}: "
                f"Peak memory: {summary['peak']['memory_percent']:.1f}%, "
                f"Process memory: {summary['peak']['process_memory_mb']:.1f} MB"
            )

            return result

        except Exception as e:
            # Log resource state on error
            summary = monitor.get_resource_summary()
            logger.error(
                f"Function {func.__name__} failed. Resource state: "
                f"Memory: {summary['current']['memory_percent']:.1f}%, "
                f"Disk: {summary['current']['disk_percent']:.1f}%"
            )
            raise

    return wrapper


class ResourceError(Exception):
    """Raised when resource constraints are violated."""
    pass


def estimate_memory_for_citations(num_citations: int, avg_citation_size_kb: float = 10) -> float:
    """
    Estimate memory needed for processing citations.

    Args:
        num_citations: Number of citations
        avg_citation_size_kb: Average citation size in KB

    Returns:
        Estimated memory in GB
    """
    # Base overhead
    base_mb = 100

    # Citation data
    citation_mb = (num_citations * avg_citation_size_kb) / 1024

    # Processing overhead (assume 5x for caching, etc.)
    processing_mb = citation_mb * 5

    # PDF storage (assume 50% of citations have PDFs, 500KB each)
    pdf_mb = (num_citations * 0.5 * 500) / 1024

    total_mb = base_mb + citation_mb + processing_mb + pdf_mb
    return total_mb / 1024  # Convert to GB


def check_sufficient_resources(num_citations: int, output_dir: Path = None) -> Dict[str, Any]:
    """
    Check if system has sufficient resources for workflow.

    Args:
        num_citations: Number of citations to process
        output_dir: Output directory path

    Returns:
        Dict with status and recommendations
    """
    # Estimate requirements
    estimated_memory_gb = estimate_memory_for_citations(num_citations)
    estimated_disk_gb = (num_citations * 0.5 * 0.5)  # Assume 500KB per PDF for 50% of citations

    # Check current resources
    memory = psutil.virtual_memory()
    available_memory_gb = memory.available / (1024 ** 3)

    if output_dir:
        disk = psutil.disk_usage(output_dir)
        available_disk_gb = disk.free / (1024 ** 3)
    else:
        disk = psutil.disk_usage(Path.cwd())
        available_disk_gb = disk.free / (1024 ** 3)

    # Determine status
    memory_ok = available_memory_gb >= estimated_memory_gb
    disk_ok = available_disk_gb >= estimated_disk_gb

    result = {
        "can_proceed": memory_ok and disk_ok,
        "estimated_requirements": {
            "memory_gb": round(estimated_memory_gb, 2),
            "disk_gb": round(estimated_disk_gb, 2)
        },
        "available_resources": {
            "memory_gb": round(available_memory_gb, 2),
            "disk_gb": round(available_disk_gb, 2)
        },
        "checks": {
            "memory": "ok" if memory_ok else "insufficient",
            "disk": "ok" if disk_ok else "insufficient"
        }
    }

    # Add recommendations
    recommendations = []
    if not memory_ok:
        recommendations.append(
            f"Insufficient memory: need {estimated_memory_gb:.1f} GB, have {available_memory_gb:.1f} GB. "
            f"Close other applications or process fewer citations."
        )
    if not disk_ok:
        recommendations.append(
            f"Insufficient disk space: need {estimated_disk_gb:.1f} GB, have {available_disk_gb:.1f} GB. "
            f"Free up disk space or change output directory."
        )

    result["recommendations"] = recommendations

    return result
