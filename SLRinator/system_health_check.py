#!/usr/bin/env python3
"""
SLRinator System Health Check
Verifies all components are properly configured and functional
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import importlib
import subprocess
from typing import Dict, List, Tuple, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


class SystemHealthChecker:
    """Comprehensive system health checker for SLRinator"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "UNKNOWN",
            "checks": {},
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
    
    def log_check(self, name: str, status: str, message: str = ""):
        """Log a health check result"""
        symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        self.logger.info(f"  {symbol} {name}: {status} {message}")
        self.results["checks"][name] = {
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_python_version(self) -> bool:
        """Check Python version"""
        self.logger.info("\n1. PYTHON ENVIRONMENT")
        self.logger.info("=" * 50)
        
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version.major >= 3 and version.minor >= 8:
            self.log_check("Python Version", "PASS", f"(v{version_str})")
            return True
        else:
            self.log_check("Python Version", "FAIL", f"(v{version_str} - requires 3.8+)")
            self.results["errors"].append(f"Python {version_str} detected, requires 3.8+")
            return False
    
    def check_required_packages(self) -> bool:
        """Check if required packages are installed"""
        self.logger.info("\n2. REQUIRED PACKAGES")
        self.logger.info("=" * 50)
        
        required_packages = [
            ("openai", "OpenAI GPT API"),
            ("PyMuPDF", "PDF processing and redboxing"),
            ("python-docx", "Word document processing"),
            ("requests", "HTTP requests"),
            ("beautifulsoup4", "HTML parsing"),
            ("pandas", "Data processing"),
            ("PyYAML", "Configuration files")
        ]
        
        all_installed = True
        
        for package, description in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                self.log_check(package, "PASS", f"- {description}")
            except ImportError:
                self.log_check(package, "FAIL", f"- {description}")
                self.results["errors"].append(f"Package '{package}' not installed")
                all_installed = False
        
        return all_installed
    
    def check_directory_structure(self) -> bool:
        """Check if required directories exist"""
        self.logger.info("\n3. DIRECTORY STRUCTURE")
        self.logger.info("=" * 50)
        
        required_dirs = [
            "src",
            "src/core",
            "src/utils",
            "src/stage1",
            "src/retrievers",
            "config",
            "output",
            "output/logs",
            "output/data"
        ]
        
        all_exist = True
        base_path = Path(__file__).parent
        
        for dir_path in required_dirs:
            full_path = base_path / dir_path
            if full_path.exists():
                self.log_check(dir_path, "PASS")
            else:
                self.log_check(dir_path, "FAIL", "- Directory missing")
                self.results["errors"].append(f"Directory '{dir_path}' not found")
                all_exist = False
        
        return all_exist
    
    def check_core_modules(self) -> bool:
        """Check if core modules can be imported"""
        self.logger.info("\n4. CORE MODULES")
        self.logger.info("=" * 50)
        
        core_modules = [
            ("src.core.enhanced_gpt_parser", "GPT citation parser"),
            ("src.core.fallback_citation_parser", "Fallback parser"),
            ("src.core.pdf_retriever", "PDF retrieval"),
            ("src.core.sourcepull_system", "Main system"),
            ("src.utils.api_logger", "API logging"),
            ("src.utils.action_logger", "Action logging"),
            ("src.utils.retry_handler", "Retry logic"),
            ("src.processors.footnote_extractor", "Footnote extraction"),
            ("src.stage1.enhanced_source_retriever", "Source retrieval")
        ]
        
        all_importable = True
        
        for module_name, description in core_modules:
            try:
                importlib.import_module(module_name)
                self.log_check(module_name.split(".")[-1], "PASS", f"- {description}")
            except ImportError as e:
                self.log_check(module_name.split(".")[-1], "FAIL", f"- {str(e)}")
                self.results["errors"].append(f"Cannot import {module_name}: {e}")
                all_importable = False
        
        return all_importable
    
    def check_api_configuration(self) -> Dict[str, bool]:
        """Check API key configuration"""
        self.logger.info("\n5. API CONFIGURATION")
        self.logger.info("=" * 50)
        
        api_status = {}
        
        # Check config file
        config_file = Path("config/api_keys.json")
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                
                # Check OpenAI
                if config.get("openai", {}).get("api_key"):
                    if config["openai"]["api_key"] != "your-api-key-here":
                        self.log_check("OpenAI API", "PASS", "- Configured")
                        api_status["openai"] = True
                    else:
                        self.log_check("OpenAI API", "WARN", "- Template value detected")
                        self.results["warnings"].append("OpenAI API key not configured")
                        api_status["openai"] = False
                else:
                    self.log_check("OpenAI API", "WARN", "- Not configured")
                    api_status["openai"] = False
                
                # Check CourtListener
                if config.get("courtlistener", {}).get("token"):
                    self.log_check("CourtListener API", "PASS", "- Configured")
                    api_status["courtlistener"] = True
                else:
                    self.log_check("CourtListener API", "WARN", "- Not configured")
                    api_status["courtlistener"] = False
                
                # Check GovInfo
                if config.get("govinfo", {}).get("api_key"):
                    self.log_check("GovInfo API", "PASS", "- Configured")
                    api_status["govinfo"] = True
                else:
                    self.log_check("GovInfo API", "WARN", "- Not configured")
                    api_status["govinfo"] = False
                    
            except Exception as e:
                self.log_check("Config File", "FAIL", f"- Error reading: {e}")
                self.results["errors"].append(f"Cannot read config file: {e}")
        else:
            self.log_check("Config File", "FAIL", "- Not found")
            self.results["errors"].append("API configuration file not found")
            
            # Check environment variables as fallback
            if os.getenv("OPENAI_API_KEY"):
                self.log_check("OpenAI API (env)", "PASS", "- Found in environment")
                api_status["openai"] = True
            else:
                api_status["openai"] = False
        
        return api_status
    
    def check_sample_files(self) -> bool:
        """Check for sample/test files"""
        self.logger.info("\n6. SAMPLE FILES")
        self.logger.info("=" * 50)
        
        sample_files = [
            ("output/data/SherkowGugliuzza_PostSP_PostEEFormatting[70].docx", "Sample document"),
            ("readme/WORKFLOW.md", "Workflow documentation"),
            ("requirements.txt", "Dependencies list")
        ]
        
        all_exist = True
        
        for file_path, description in sample_files:
            if Path(file_path).exists():
                self.log_check(Path(file_path).name, "PASS", f"- {description}")
            else:
                self.log_check(Path(file_path).name, "WARN", f"- {description} not found")
                self.results["warnings"].append(f"Sample file '{file_path}' not found")
        
        return all_exist
    
    def check_log_files(self) -> bool:
        """Check log file generation"""
        self.logger.info("\n7. LOGGING SYSTEM")
        self.logger.info("=" * 50)
        
        log_dir = Path("output/logs")
        
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                self.log_check("Log Files", "PASS", f"- {len(log_files)} log files found")
                
                # Check recent logs
                recent_logs = sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]
                for log_file in recent_logs:
                    size_kb = log_file.stat().st_size / 1024
                    self.logger.info(f"    • {log_file.name} ({size_kb:.1f} KB)")
                
                return True
            else:
                self.log_check("Log Files", "WARN", "- No log files found")
                self.results["warnings"].append("No log files generated yet")
                return False
        else:
            self.log_check("Log Directory", "FAIL", "- Directory not found")
            self.results["errors"].append("Log directory not found")
            return False
    
    def test_basic_functionality(self) -> bool:
        """Test basic system functionality"""
        self.logger.info("\n8. BASIC FUNCTIONALITY TEST")
        self.logger.info("=" * 50)
        
        try:
            # Test footnote extraction
            from src.processors.footnote_extractor import FootnoteExtractor
            extractor = FootnoteExtractor()
            self.log_check("Footnote Extractor", "PASS", "- Module loads successfully")
            
            # Test fallback parser
            from src.core.fallback_citation_parser import FallbackCitationParser
            parser = FallbackCitationParser()
            test_text = "See Alice Corp. v. CLS Bank, 573 U.S. 208 (2014)"
            citations = parser.parse(test_text)
            if citations:
                self.log_check("Citation Parser", "PASS", f"- Found {len(citations)} citations")
            else:
                self.log_check("Citation Parser", "WARN", "- No citations found in test")
            
            return True
            
        except Exception as e:
            self.log_check("Functionality Test", "FAIL", f"- {str(e)}")
            self.results["errors"].append(f"Functionality test failed: {e}")
            return False
    
    def generate_recommendations(self):
        """Generate recommendations based on checks"""
        
        if not self.results["checks"].get("Python Version", {}).get("status") == "PASS":
            self.results["recommendations"].append(
                "Upgrade Python to version 3.8 or higher"
            )
        
        missing_packages = [
            name for name, check in self.results["checks"].items()
            if "Package" in name and check["status"] == "FAIL"
        ]
        if missing_packages:
            self.results["recommendations"].append(
                f"Install missing packages: pip install -r requirements.txt"
            )
        
        if not Path("config/api_keys.json").exists():
            self.results["recommendations"].append(
                "Create API configuration: cp config/api_keys_template.json config/api_keys.json"
            )
        
        if self.results["warnings"]:
            self.results["recommendations"].append(
                "Review and address warnings to improve system functionality"
            )
        
        if not self.results["errors"]:
            self.results["recommendations"].append(
                "System is ready for use! Run: python enhanced_sourcepull_workflow.py <document.docx>"
            )
    
    def run_health_check(self) -> Dict[str, Any]:
        """Run complete health check"""
        
        self.logger.info("=" * 70)
        self.logger.info("SLRINATOR SYSTEM HEALTH CHECK")
        self.logger.info("=" * 70)
        self.logger.info(f"Timestamp: {self.results['timestamp']}")
        
        # Run all checks
        checks_passed = 0
        checks_total = 0
        
        # Basic checks
        if self.check_python_version():
            checks_passed += 1
        checks_total += 1
        
        if self.check_required_packages():
            checks_passed += 1
        checks_total += 1
        
        if self.check_directory_structure():
            checks_passed += 1
        checks_total += 1
        
        if self.check_core_modules():
            checks_passed += 1
        checks_total += 1
        
        # API configuration
        api_status = self.check_api_configuration()
        if any(api_status.values()):
            checks_passed += 0.5  # Partial credit if any API configured
        checks_total += 1
        
        # Optional checks
        self.check_sample_files()
        self.check_log_files()
        self.test_basic_functionality()
        
        # Generate recommendations
        self.generate_recommendations()
        
        # Determine overall status
        if self.results["errors"]:
            self.results["overall_status"] = "CRITICAL"
        elif self.results["warnings"]:
            self.results["overall_status"] = "WARNING"
        else:
            self.results["overall_status"] = "HEALTHY"
        
        # Print summary
        self.logger.info("\n" + "=" * 70)
        self.logger.info("SUMMARY")
        self.logger.info("=" * 70)
        
        status_symbol = {
            "HEALTHY": "✅",
            "WARNING": "⚠️",
            "CRITICAL": "❌"
        }[self.results["overall_status"]]
        
        self.logger.info(f"\nOverall Status: {status_symbol} {self.results['overall_status']}")
        self.logger.info(f"Checks Passed: {checks_passed}/{checks_total}")
        
        if self.results["errors"]:
            self.logger.info(f"\n❌ ERRORS ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                self.logger.info(f"  • {error}")
        
        if self.results["warnings"]:
            self.logger.info(f"\n⚠️  WARNINGS ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"]:
                self.logger.info(f"  • {warning}")
        
        if self.results["recommendations"]:
            self.logger.info(f"\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(self.results["recommendations"], 1):
                self.logger.info(f"  {i}. {rec}")
        
        # Save results to file
        output_file = Path("output/logs") / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        self.logger.info(f"\n📄 Full report saved to: {output_file}")
        
        return self.results


def main():
    """Run system health check"""
    checker = SystemHealthChecker()
    results = checker.run_health_check()
    
    # Return exit code based on status
    if results["overall_status"] == "CRITICAL":
        return 1
    elif results["overall_status"] == "WARNING":
        return 0
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())