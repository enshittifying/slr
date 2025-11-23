"""
Health Check and Diagnostics System for R1 Validation
Provides system health monitoring, dependency verification, and self-healing capabilities
"""
import os
import sys
import time
import json
import psutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class ComponentType(Enum):
    """System component types."""
    API = "api"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DEPENDENCY = "dependency"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    component: str
    component_type: ComponentType
    status: HealthStatus
    message: str
    timestamp: float
    details: Optional[Dict] = None
    auto_fixed: bool = False


@dataclass
class SystemHealth:
    """Overall system health status."""
    status: HealthStatus
    timestamp: float
    checks: List[HealthCheckResult]
    resource_usage: Dict[str, Any]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp,
            "checks": [asdict(check) for check in self.checks],
            "resource_usage": self.resource_usage,
            "recommendations": self.recommendations
        }


class HealthCheckManager:
    """
    Manages system health checks and diagnostics.
    Monitors dependencies, resources, and provides self-healing.
    """

    def __init__(self, config_path: Path = None):
        """
        Initialize health check manager.

        Args:
            config_path: Path to configuration directory
        """
        self.config_path = config_path or Path.cwd() / "config"
        self.check_results: List[HealthCheckResult] = []
        self.last_check_time: Optional[float] = None

    def run_full_health_check(self) -> SystemHealth:
        """
        Run comprehensive system health check.

        Returns:
            SystemHealth with all check results
        """
        logger.info("Running full system health check...")
        self.check_results = []

        # Run all checks
        self._check_api_connectivity()
        self._check_filesystem()
        self._check_dependencies()
        self._check_configuration()
        self._check_memory()
        self._check_disk_space()
        self._check_bluebook_json()

        # Analyze results
        overall_status = self._determine_overall_status()
        resource_usage = self._get_resource_usage()
        recommendations = self._generate_recommendations()

        self.last_check_time = time.time()

        health = SystemHealth(
            status=overall_status,
            timestamp=self.last_check_time,
            checks=self.check_results,
            resource_usage=resource_usage,
            recommendations=recommendations
        )

        logger.info(f"Health check complete: {overall_status.value}")
        return health

    def _check_api_connectivity(self):
        """Check OpenAI API connectivity."""
        try:
            from openai import OpenAI

            # Check for API key
            api_key_file = self.config_path / "api_keys.json"
            if not api_key_file.exists():
                self.check_results.append(HealthCheckResult(
                    component="OpenAI API",
                    component_type=ComponentType.API,
                    status=HealthStatus.UNHEALTHY,
                    message="API key file not found",
                    timestamp=time.time(),
                    details={"path": str(api_key_file)}
                ))
                return

            # Load API key
            with open(api_key_file) as f:
                config = json.load(f)

            api_key = config.get("openai", {}).get("api_key")
            if not api_key or api_key == "your-api-key-here":
                self.check_results.append(HealthCheckResult(
                    component="OpenAI API",
                    component_type=ComponentType.API,
                    status=HealthStatus.UNHEALTHY,
                    message="API key not configured",
                    timestamp=time.time()
                ))
                return

            # Test API connectivity with minimal request
            try:
                client = OpenAI(api_key=api_key)
                # Simple models list call to verify connectivity
                models = client.models.list()

                self.check_results.append(HealthCheckResult(
                    component="OpenAI API",
                    component_type=ComponentType.API,
                    status=HealthStatus.HEALTHY,
                    message="API connectivity verified",
                    timestamp=time.time(),
                    details={"models_available": True}
                ))
            except Exception as e:
                self.check_results.append(HealthCheckResult(
                    component="OpenAI API",
                    component_type=ComponentType.API,
                    status=HealthStatus.UNHEALTHY,
                    message=f"API connection failed: {str(e)}",
                    timestamp=time.time()
                ))

        except ImportError:
            self.check_results.append(HealthCheckResult(
                component="OpenAI API",
                component_type=ComponentType.DEPENDENCY,
                status=HealthStatus.UNHEALTHY,
                message="OpenAI package not installed",
                timestamp=time.time()
            ))

    def _check_filesystem(self):
        """Check filesystem access to critical directories."""
        critical_dirs = [
            self.config_path,
            self.config_path / "rules",
            Path.cwd() / "output",
            Path.cwd() / "output" / "r1_validation",
            Path.cwd() / "output" / "progress",
            Path.cwd() / "prompts" / "r1"
        ]

        all_ok = True
        missing_dirs = []
        auto_created = []

        for dir_path in critical_dirs:
            if not dir_path.exists():
                missing_dirs.append(str(dir_path))
                # Auto-fix: create missing directories
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    auto_created.append(str(dir_path))
                    logger.info(f"Auto-created missing directory: {dir_path}")
                except Exception as e:
                    logger.error(f"Failed to create directory {dir_path}: {e}")
                    all_ok = False

            # Check write permissions
            if dir_path.exists() and not os.access(dir_path, os.W_OK):
                all_ok = False
                self.check_results.append(HealthCheckResult(
                    component=f"Filesystem: {dir_path.name}",
                    component_type=ComponentType.FILESYSTEM,
                    status=HealthStatus.UNHEALTHY,
                    message=f"No write permission: {dir_path}",
                    timestamp=time.time()
                ))
                return

        if all_ok:
            status = HealthStatus.HEALTHY
            message = "All critical directories accessible"
            if auto_created:
                message += f" (auto-created {len(auto_created)})"
        else:
            status = HealthStatus.DEGRADED if auto_created else HealthStatus.UNHEALTHY
            message = f"Filesystem issues detected"

        self.check_results.append(HealthCheckResult(
            component="Filesystem",
            component_type=ComponentType.FILESYSTEM,
            status=status,
            message=message,
            timestamp=time.time(),
            details={
                "missing_dirs": missing_dirs,
                "auto_created": auto_created
            },
            auto_fixed=len(auto_created) > 0
        ))

    def _check_dependencies(self):
        """Check Python package dependencies."""
        required_packages = [
            "openai",
            "PyMuPDF",
            "docx",
            "pandas",
            "psutil",
            "tiktoken"
        ]

        missing = []
        installed = []

        for package in required_packages:
            try:
                __import__(package)
                installed.append(package)
            except ImportError:
                missing.append(package)

        if not missing:
            status = HealthStatus.HEALTHY
            message = f"All {len(required_packages)} required packages installed"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Missing {len(missing)} required packages"

        self.check_results.append(HealthCheckResult(
            component="Dependencies",
            component_type=ComponentType.DEPENDENCY,
            status=status,
            message=message,
            timestamp=time.time(),
            details={
                "installed": installed,
                "missing": missing
            }
        ))

    def _check_configuration(self):
        """Check configuration files."""
        config_files = [
            ("api_keys.json", self.config_path / "api_keys.json"),
            ("validation_settings.py", self.config_path / "validation_settings.py")
        ]

        all_ok = True
        missing_files = []

        for name, path in config_files:
            if not path.exists():
                all_ok = False
                missing_files.append(name)

        status = HealthStatus.HEALTHY if all_ok else HealthStatus.DEGRADED
        message = "All config files present" if all_ok else f"Missing: {', '.join(missing_files)}"

        self.check_results.append(HealthCheckResult(
            component="Configuration",
            component_type=ComponentType.FILESYSTEM,
            status=status,
            message=message,
            timestamp=time.time(),
            details={"missing_files": missing_files}
        ))

    def _check_memory(self):
        """Check system memory usage."""
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        available_gb = memory.available / (1024 ** 3)

        if memory_percent > 90:
            status = HealthStatus.CRITICAL
            message = f"Critical memory usage: {memory_percent:.1f}%"
        elif memory_percent > 80:
            status = HealthStatus.DEGRADED
            message = f"High memory usage: {memory_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {memory_percent:.1f}%"

        self.check_results.append(HealthCheckResult(
            component="Memory",
            component_type=ComponentType.MEMORY,
            status=status,
            message=message,
            timestamp=time.time(),
            details={
                "percent_used": memory_percent,
                "available_gb": round(available_gb, 2),
                "total_gb": round(memory.total / (1024 ** 3), 2)
            }
        ))

    def _check_disk_space(self):
        """Check disk space."""
        disk = psutil.disk_usage(Path.cwd())
        disk_percent = disk.percent
        free_gb = disk.free / (1024 ** 3)

        if disk_percent > 95:
            status = HealthStatus.CRITICAL
            message = f"Critical disk usage: {disk_percent:.1f}%"
        elif disk_percent > 85:
            status = HealthStatus.DEGRADED
            message = f"High disk usage: {disk_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk usage normal: {disk_percent:.1f}%"

        self.check_results.append(HealthCheckResult(
            component="Disk Space",
            component_type=ComponentType.DISK,
            status=status,
            message=message,
            timestamp=time.time(),
            details={
                "percent_used": disk_percent,
                "free_gb": round(free_gb, 2),
                "total_gb": round(disk.total / (1024 ** 3), 2)
            }
        ))

    def _check_bluebook_json(self):
        """Check Bluebook.json file integrity."""
        bluebook_path = self.config_path / "rules" / "Bluebook.json"

        if not bluebook_path.exists():
            self.check_results.append(HealthCheckResult(
                component="Bluebook.json",
                component_type=ComponentType.FILESYSTEM,
                status=HealthStatus.UNHEALTHY,
                message="Bluebook.json not found",
                timestamp=time.time(),
                details={"path": str(bluebook_path)}
            ))
            return

        try:
            with open(bluebook_path) as f:
                data = json.load(f)

            # Validate structure
            if "redbook" not in data or "bluebook" not in data:
                self.check_results.append(HealthCheckResult(
                    component="Bluebook.json",
                    component_type=ComponentType.FILESYSTEM,
                    status=HealthStatus.UNHEALTHY,
                    message="Invalid Bluebook.json structure",
                    timestamp=time.time()
                ))
                return

            redbook_count = len(data.get("redbook", []))
            bluebook_count = len(data.get("bluebook", []))

            if redbook_count < 100 or bluebook_count < 200:
                status = HealthStatus.DEGRADED
                message = f"Incomplete rules: {redbook_count} Redbook, {bluebook_count} Bluebook"
            else:
                status = HealthStatus.HEALTHY
                message = f"Rules loaded: {redbook_count} Redbook, {bluebook_count} Bluebook"

            self.check_results.append(HealthCheckResult(
                component="Bluebook.json",
                component_type=ComponentType.FILESYSTEM,
                status=status,
                message=message,
                timestamp=time.time(),
                details={
                    "redbook_rules": redbook_count,
                    "bluebook_rules": bluebook_count
                }
            ))

        except json.JSONDecodeError:
            self.check_results.append(HealthCheckResult(
                component="Bluebook.json",
                component_type=ComponentType.FILESYSTEM,
                status=HealthStatus.UNHEALTHY,
                message="Invalid JSON format",
                timestamp=time.time()
            ))
        except Exception as e:
            self.check_results.append(HealthCheckResult(
                component="Bluebook.json",
                component_type=ComponentType.FILESYSTEM,
                status=HealthStatus.UNHEALTHY,
                message=f"Error loading file: {str(e)}",
                timestamp=time.time()
            ))

    def _determine_overall_status(self) -> HealthStatus:
        """Determine overall system health status."""
        if not self.check_results:
            return HealthStatus.HEALTHY

        # Count statuses
        critical = sum(1 for r in self.check_results if r.status == HealthStatus.CRITICAL)
        unhealthy = sum(1 for r in self.check_results if r.status == HealthStatus.UNHEALTHY)
        degraded = sum(1 for r in self.check_results if r.status == HealthStatus.DEGRADED)

        if critical > 0:
            return HealthStatus.CRITICAL
        elif unhealthy > 0:
            return HealthStatus.UNHEALTHY
        elif degraded > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage(Path.cwd())
        cpu = psutil.cpu_percent(interval=0.1)

        return {
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024 ** 3), 2),
            "disk_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024 ** 3), 2),
            "cpu_percent": cpu,
            "timestamp": time.time()
        }

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on health check results."""
        recommendations = []

        for check in self.check_results:
            if check.status == HealthStatus.UNHEALTHY:
                if check.component == "OpenAI API":
                    if "not configured" in check.message:
                        recommendations.append("Configure OpenAI API key in config/api_keys.json")
                    elif "not found" in check.message:
                        recommendations.append("Create config/api_keys.json with your OpenAI API key")
                    else:
                        recommendations.append("Check OpenAI API connectivity and credentials")

                elif check.component == "Bluebook.json":
                    recommendations.append("Run setup_r1.py to install Bluebook.json")

                elif check.component == "Dependencies":
                    missing = check.details.get("missing", [])
                    if missing:
                        recommendations.append(f"Install missing packages: pip install {' '.join(missing)}")

            elif check.status == HealthStatus.DEGRADED:
                if check.component_type == ComponentType.MEMORY:
                    recommendations.append("Close unused applications to free memory")
                elif check.component_type == ComponentType.DISK:
                    recommendations.append("Free up disk space or change output directory")

            elif check.status == HealthStatus.CRITICAL:
                if check.component_type == ComponentType.MEMORY:
                    recommendations.append("URGENT: System memory critically low - restart or upgrade hardware")
                elif check.component_type == ComponentType.DISK:
                    recommendations.append("URGENT: Disk space critically low - delete old files immediately")

        return recommendations

    def save_diagnostic_report(self, output_path: Path = None):
        """
        Save diagnostic report to file.

        Args:
            output_path: Path to save report
        """
        health = self.run_full_health_check()

        if output_path is None:
            output_dir = Path.cwd() / "output" / "diagnostics"
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"health_report_{timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(health.to_dict(), f, indent=2)

        logger.info(f"Diagnostic report saved to {output_path}")
        return output_path

    def get_quick_status(self) -> str:
        """
        Get quick status summary as formatted string.

        Returns:
            Formatted status string
        """
        health = self.run_full_health_check()

        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.CRITICAL: "🔴"
        }

        lines = [
            f"\n{'='*60}",
            f"R1 System Health Check",
            f"{'='*60}",
            f"{status_emoji[health.status]} Overall Status: {health.status.value.upper()}",
            f"",
            f"Component Status:"
        ]

        for check in health.checks:
            emoji = status_emoji[check.status]
            lines.append(f"  {emoji} {check.component}: {check.message}")

        lines.append(f"\nResource Usage:")
        lines.append(f"  Memory: {health.resource_usage['memory_percent']:.1f}% "
                    f"({health.resource_usage['memory_available_gb']} GB free)")
        lines.append(f"  Disk: {health.resource_usage['disk_percent']:.1f}% "
                    f"({health.resource_usage['disk_free_gb']} GB free)")
        lines.append(f"  CPU: {health.resource_usage['cpu_percent']:.1f}%")

        if health.recommendations:
            lines.append(f"\nRecommendations:")
            for rec in health.recommendations:
                lines.append(f"  • {rec}")

        lines.append(f"{'='*60}\n")

        return "\n".join(lines)
