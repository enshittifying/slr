"""
Performance Monitoring and Optimization Module
Tracks system performance and provides optimization recommendations
"""

import time
import psutil
import logging
import functools
from typing import Dict, Any, Callable, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json
import threading
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    operation: str
    start_time: float
    end_time: float = 0.0
    duration: float = 0.0
    memory_before: float = 0.0
    memory_after: float = 0.0
    memory_delta: float = 0.0
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self):
        """Mark operation as complete and calculate metrics"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.memory_after = psutil.Process().memory_info().rss / 1024 / 1024
        self.memory_delta = self.memory_after - self.memory_before


class PerformanceMonitor:
    """Monitors and tracks system performance"""
    
    def __init__(self, max_history: int = 1000):
        self.metrics_history = deque(maxlen=max_history)
        self.current_operations = {}
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # Performance thresholds
        self.thresholds = {
            'operation_time': 30.0,  # seconds
            'memory_increase': 100.0,  # MB
            'error_rate': 0.1,  # 10%
        }
        
        # Statistics
        self.stats = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'total_time': 0.0,
            'peak_memory': 0.0,
        }
    
    def start_operation(self, operation_name: str, metadata: Dict[str, Any] = None) -> str:
        """Start tracking an operation"""
        operation_id = f"{operation_name}_{time.time()}"
        
        metrics = PerformanceMetrics(
            operation=operation_name,
            start_time=time.time(),
            memory_before=psutil.Process().memory_info().rss / 1024 / 1024,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.current_operations[operation_id] = metrics
            self.stats['total_operations'] += 1
        
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, error: str = None):
        """End tracking an operation"""
        with self.lock:
            if operation_id in self.current_operations:
                metrics = self.current_operations.pop(operation_id)
                metrics.complete()
                metrics.success = success
                metrics.error = error
                
                # Update statistics
                if success:
                    self.stats['successful_operations'] += 1
                else:
                    self.stats['failed_operations'] += 1
                
                self.stats['total_time'] += metrics.duration
                
                current_memory = psutil.Process().memory_info().rss / 1024 / 1024
                if current_memory > self.stats['peak_memory']:
                    self.stats['peak_memory'] = current_memory
                
                # Add to history
                self.metrics_history.append(metrics)
                
                # Check for performance issues
                self._check_performance_issues(metrics)
    
    def _check_performance_issues(self, metrics: PerformanceMetrics):
        """Check for performance issues and log warnings"""
        if metrics.duration > self.thresholds['operation_time']:
            logger.warning(
                f"Slow operation: {metrics.operation} took {metrics.duration:.2f}s "
                f"(threshold: {self.thresholds['operation_time']}s)"
            )
        
        if metrics.memory_delta > self.thresholds['memory_increase']:
            logger.warning(
                f"High memory usage: {metrics.operation} increased memory by "
                f"{metrics.memory_delta:.2f}MB (threshold: {self.thresholds['memory_increase']}MB)"
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.lock:
            error_rate = (self.stats['failed_operations'] / 
                         max(self.stats['total_operations'], 1))
            
            avg_duration = (self.stats['total_time'] / 
                          max(self.stats['successful_operations'], 1))
            
            # Calculate recent performance
            recent_metrics = list(self.metrics_history)[-100:]
            recent_errors = sum(1 for m in recent_metrics if not m.success)
            recent_error_rate = recent_errors / max(len(recent_metrics), 1)
            
            # Operation-specific stats
            operation_stats = {}
            for metrics in self.metrics_history:
                op = metrics.operation
                if op not in operation_stats:
                    operation_stats[op] = {
                        'count': 0,
                        'total_time': 0.0,
                        'errors': 0,
                        'avg_time': 0.0,
                        'max_time': 0.0,
                        'min_time': float('inf'),
                    }
                
                stats = operation_stats[op]
                stats['count'] += 1
                stats['total_time'] += metrics.duration
                stats['max_time'] = max(stats['max_time'], metrics.duration)
                stats['min_time'] = min(stats['min_time'], metrics.duration)
                
                if not metrics.success:
                    stats['errors'] += 1
            
            # Calculate averages
            for stats in operation_stats.values():
                if stats['count'] > 0:
                    stats['avg_time'] = stats['total_time'] / stats['count']
                    stats['error_rate'] = stats['errors'] / stats['count']
            
            return {
                'uptime': time.time() - self.start_time,
                'total_operations': self.stats['total_operations'],
                'successful_operations': self.stats['successful_operations'],
                'failed_operations': self.stats['failed_operations'],
                'error_rate': error_rate,
                'recent_error_rate': recent_error_rate,
                'average_duration': avg_duration,
                'peak_memory_mb': self.stats['peak_memory'],
                'current_memory_mb': psutil.Process().memory_info().rss / 1024 / 1024,
                'cpu_percent': psutil.Process().cpu_percent(),
                'operation_stats': operation_stats,
            }
    
    def generate_report(self, output_path: str = "performance_report.json"):
        """Generate a detailed performance report"""
        stats = self.get_statistics()
        
        # Add recommendations
        recommendations = []
        
        if stats['error_rate'] > self.thresholds['error_rate']:
            recommendations.append(
                f"High error rate ({stats['error_rate']:.1%}). "
                "Check error logs and implement better error handling."
            )
        
        if stats['peak_memory_mb'] > 500:
            recommendations.append(
                f"High memory usage ({stats['peak_memory_mb']:.0f}MB). "
                "Consider implementing pagination or streaming for large datasets."
            )
        
        if stats['average_duration'] > 10:
            recommendations.append(
                f"Slow average operation time ({stats['average_duration']:.2f}s). "
                "Consider implementing caching or parallel processing."
            )
        
        # Find slowest operations
        if stats['operation_stats']:
            slowest = sorted(
                stats['operation_stats'].items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )[:5]
            
            stats['slowest_operations'] = [
                {'name': name, **data} for name, data in slowest
            ]
        
        stats['recommendations'] = recommendations
        stats['report_generated'] = datetime.now().isoformat()
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        
        logger.info(f"Performance report saved to {output_path}")
        return stats


def performance_tracked(monitor: PerformanceMonitor = None):
    """Decorator to track function performance"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided monitor or create a new one
            perf_monitor = monitor or getattr(wrapper, '_monitor', None)
            if not perf_monitor:
                perf_monitor = PerformanceMonitor()
                wrapper._monitor = perf_monitor
            
            # Start tracking
            operation_name = f"{func.__module__}.{func.__name__}"
            operation_id = perf_monitor.start_operation(
                operation_name,
                metadata={'args_count': len(args), 'kwargs_count': len(kwargs)}
            )
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                perf_monitor.end_operation(operation_id, success=True)
                return result
            
            except Exception as e:
                perf_monitor.end_operation(
                    operation_id,
                    success=False,
                    error=str(e)
                )
                raise
        
        return wrapper
    return decorator


class ResourceManager:
    """Manages system resources and prevents overload"""
    
    def __init__(self, max_memory_mb: int = 1000, max_cpu_percent: int = 80):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.process = psutil.Process()
        
    def check_resources(self) -> Tuple[bool, str]:
        """Check if resources are within limits"""
        # Check memory
        current_memory = self.process.memory_info().rss / 1024 / 1024
        if current_memory > self.max_memory_mb:
            return False, f"Memory limit exceeded: {current_memory:.0f}MB > {self.max_memory_mb}MB"
        
        # Check CPU
        cpu_percent = self.process.cpu_percent(interval=0.1)
        if cpu_percent > self.max_cpu_percent:
            return False, f"CPU limit exceeded: {cpu_percent:.0f}% > {self.max_cpu_percent}%"
        
        # Check disk space
        disk_usage = psutil.disk_usage('/')
        if disk_usage.percent > 90:
            return False, f"Low disk space: {disk_usage.percent:.0f}% used"
        
        return True, "Resources OK"
    
    def wait_for_resources(self, timeout: int = 60) -> bool:
        """Wait for resources to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            ok, message = self.check_resources()
            if ok:
                return True
            
            logger.warning(f"Waiting for resources: {message}")
            time.sleep(5)
        
        return False
    
    def optimize_memory(self):
        """Trigger garbage collection and memory optimization"""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Log memory status
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        logger.info(f"Memory after optimization: {memory_mb:.0f}MB")


class BatchProcessor:
    """Optimized batch processing with resource management"""
    
    def __init__(self, batch_size: int = 100, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.monitor = PerformanceMonitor()
        self.resource_manager = ResourceManager()
    
    def process_batch(self, items: list, process_func: Callable,
                     description: str = "Processing") -> list:
        """Process items in optimized batches"""
        results = []
        total_items = len(items)
        
        # Check resources before starting
        ok, message = self.resource_manager.check_resources()
        if not ok:
            logger.warning(f"Resource constraint: {message}")
            if not self.resource_manager.wait_for_resources():
                raise RuntimeError("Insufficient resources for batch processing")
        
        # Process in batches
        for i in range(0, total_items, self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (total_items + self.batch_size - 1) // self.batch_size
            
            logger.info(f"{description}: Batch {batch_num}/{total_batches}")
            
            # Track batch performance
            op_id = self.monitor.start_operation(
                f"batch_{description}",
                metadata={'batch_size': len(batch), 'batch_num': batch_num}
            )
            
            try:
                # Process batch with threading for I/O operations
                import concurrent.futures
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    batch_results = list(executor.map(process_func, batch))
                
                results.extend(batch_results)
                self.monitor.end_operation(op_id, success=True)
                
            except Exception as e:
                self.monitor.end_operation(op_id, success=False, error=str(e))
                logger.error(f"Batch processing error: {e}")
                raise
            
            # Check resources after each batch
            if not self.resource_manager.check_resources()[0]:
                logger.info("Optimizing memory between batches")
                self.resource_manager.optimize_memory()
                time.sleep(1)  # Brief pause
        
        # Generate performance report
        stats = self.monitor.get_statistics()
        logger.info(
            f"Batch processing complete: {total_items} items, "
            f"{stats['successful_operations']} successful, "
            f"{stats['failed_operations']} failed"
        )
        
        return results