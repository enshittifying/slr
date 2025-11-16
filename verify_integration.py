"""
Cross-Reference Verification Script
Validates all integration points across the application
"""
import sys
from pathlib import Path
import importlib.util
from typing import Dict, List, Set
import ast

# Add app to path
sys.path.insert(0, str(Path(__file__).parent / "app"))


class CrossReferenceValidator:
    """Validates cross-references between all application modules"""

    def __init__(self):
        self.app_root = Path(__file__).parent / "app"
        self.issues = []
        self.warnings = []
        self.module_imports = {}
        self.module_exports = {}

    def analyze_file(self, file_path: Path):
        """Analyze a Python file for imports and exports"""
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            imports = []
            exports = []

            for node in ast.walk(tree):
                # Track imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")

                # Track class/function definitions (exports)
                elif isinstance(node, ast.ClassDef):
                    exports.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    exports.append(node.name)

            rel_path = file_path.relative_to(self.app_root)
            self.module_imports[str(rel_path)] = imports
            self.module_exports[str(rel_path)] = exports

        except Exception as e:
            self.issues.append(f"Failed to parse {file_path}: {e}")

    def verify_core_pipeline_integration(self):
        """Verify core pipeline components integrate correctly"""
        print("\n=== Core Pipeline Integration ===")

        # Check SP Machine
        sp_file = self.app_root / "core" / "sp_machine.py"
        if sp_file.exists():
            sp_imports = self.module_imports.get("core/sp_machine.py", [])

            # Should import SLRinator components
            required = [
                'src.retrievers.unified_retriever',
                'src.core.retrieval_framework',
                'src.processors.footnote_extractor'
            ]
            for req in required:
                if not any(req in imp for imp in sp_imports):
                    self.warnings.append(f"SP Machine missing import: {req}")
                else:
                    print(f"✓ SP Machine imports {req}")

        # Check R1 Machine
        r1_file = self.app_root / "core" / "r1_machine.py"
        if r1_file.exists():
            r1_imports = self.module_imports.get("core/r1_machine.py", [])

            required = [
                'src.processors.redboxer',
                'src.core.retrieval_framework'
            ]
            for req in required:
                if not any(req in imp for imp in r1_imports):
                    self.warnings.append(f"R1 Machine missing import: {req}")
                else:
                    print(f"✓ R1 Machine imports {req}")

            # Should import PyMuPDF
            if not any('fitz' in imp or 'PyMuPDF' in imp for imp in r1_imports):
                self.issues.append("R1 Machine missing PyMuPDF (fitz) import")
            else:
                print("✓ R1 Machine imports PyMuPDF")

        # Check R2 Pipeline
        r2_file = self.app_root / "core" / "r2_pipeline.py"
        if r2_file.exists():
            r2_imports = self.module_imports.get("core/r2_pipeline.py", [])

            required = [
                'src.processors.footnote_extractor',
                'docx'
            ]
            for req in required:
                if not any(req in imp for imp in r2_imports):
                    self.warnings.append(f"R2 Pipeline missing import: {req}")
                else:
                    print(f"✓ R2 Pipeline imports {req}")

    def verify_data_layer_integration(self):
        """Verify data layer components"""
        print("\n=== Data Layer Integration ===")

        # Check Sheets Client
        sheets_exports = self.module_exports.get("data/sheets_client.py", [])
        required_methods = ['SheetsClient', 'get_all_articles', 'get_sources_for_article']
        for method in required_methods:
            if method in sheets_exports or any(method in exp for exp in sheets_exports):
                print(f"✓ Sheets Client exports {method}")
            else:
                self.warnings.append(f"Sheets Client may be missing: {method}")

        # Check Drive Client
        drive_exports = self.module_exports.get("data/drive_client.py", [])
        required_methods = ['DriveClient', 'upload_file', 'download_file']
        for method in required_methods:
            if method in drive_exports or any(method in exp for exp in drive_exports):
                print(f"✓ Drive Client exports {method}")

        # Check LLM Client
        llm_exports = self.module_exports.get("data/llm_client.py", [])
        required = ['OpenAIClient', 'AnthropicClient', 'create_llm_client']
        for item in required:
            if item in llm_exports:
                print(f"✓ LLM Client exports {item}")

    def verify_orchestrator_dependencies(self):
        """Verify orchestrator has all required dependencies"""
        print("\n=== Orchestrator Dependencies ===")

        orch_imports = self.module_imports.get("core/orchestrator.py", [])

        required_imports = [
            'sp_machine.SPMachine',
            'r1_machine.R1Machine',
            'r2_pipeline.R2Pipeline'
        ]

        for req in required_imports:
            if any(req in imp for imp in orch_imports):
                print(f"✓ Orchestrator imports {req}")
            else:
                self.issues.append(f"Orchestrator missing critical import: {req}")

    def verify_gui_integration(self):
        """Verify GUI components integrate with core"""
        print("\n=== GUI Integration ===")

        # Check main window
        main_window_imports = self.module_imports.get("gui/main_window.py", [])

        required = [
            'config.ConfigManager',
            'orchestrator.PipelineOrchestrator',
            'sp_manager.SPManagerWidget',
            'r1_manager.R1ManagerWidget',
            'r2_manager.R2ManagerWidget'
        ]

        for req in required:
            if any(req in imp for imp in main_window_imports):
                print(f"✓ Main Window imports {req}")
            else:
                self.warnings.append(f"Main Window may be missing: {req}")

        # Check if all manager widgets exist
        managers = ['sp_manager.py', 'r1_manager.py', 'r2_manager.py']
        for manager in managers:
            if (self.app_root / "gui" / manager).exists():
                print(f"✓ GUI manager exists: {manager}")
            else:
                self.issues.append(f"Missing GUI manager: {manager}")

    def verify_configuration_consistency(self):
        """Verify configuration is used consistently"""
        print("\n=== Configuration Consistency ===")

        config_file = self.app_root / "utils" / "config.py"
        if config_file.exists():
            with open(config_file, 'r') as f:
                content = f.read()

            # Check for default config structure
            config_keys = [
                'google.spreadsheet_id',
                'google.drive_folder_id',
                'llm.provider',
                'llm.model',
                'llm.api_key',
                'paths.credentials',
                'paths.cache_dir'
            ]

            for key in config_keys:
                if key in content:
                    print(f"✓ Config defines: {key}")
                else:
                    self.warnings.append(f"Config may be missing: {key}")

    def verify_error_handling(self):
        """Verify error handling patterns"""
        print("\n=== Error Handling ===")

        core_files = list((self.app_root / "core").glob("*.py"))

        for file in core_files:
            if file.name == "__init__.py":
                continue

            with open(file, 'r') as f:
                content = f.read()

            # Check for try/except blocks
            if 'try:' in content and 'except' in content:
                print(f"✓ {file.name} has error handling")
            else:
                self.warnings.append(f"{file.name} may lack error handling")

            # Check for logging
            if 'logger' in content or 'logging' in content:
                print(f"✓ {file.name} has logging")
            else:
                self.warnings.append(f"{file.name} may lack logging")

    def verify_slrinator_integration(self):
        """Verify SLRinator is properly integrated"""
        print("\n=== SLRinator Integration ===")

        slrinator_path = Path(__file__).parent / "SLRinator"

        if slrinator_path.exists():
            print("✓ SLRinator directory exists")

            # Check key SLRinator files
            required_files = [
                "src/retrievers/unified_retriever.py",
                "src/processors/redboxer.py",
                "src/processors/footnote_extractor.py",
                "src/core/retrieval_framework.py"
            ]

            for file in required_files:
                if (slrinator_path / file).exists():
                    print(f"✓ SLRinator has: {file}")
                else:
                    self.issues.append(f"SLRinator missing: {file}")
        else:
            self.issues.append("SLRinator directory not found!")

    def verify_resources(self):
        """Verify all required resources exist"""
        print("\n=== Resources ===")

        resources = self.app_root / "resources"

        required_resources = [
            "bluebook_rules.json",
            "prompts/citation_format.txt",
            "prompts/support_check.txt"
        ]

        for resource in required_resources:
            if (resources / resource).exists():
                print(f"✓ Resource exists: {resource}")
            else:
                self.warnings.append(f"Resource missing: {resource}")

    def run_all_validations(self):
        """Run all validation checks"""
        print("=" * 60)
        print("CROSS-REFERENCE VALIDATION REPORT")
        print("=" * 60)

        # Analyze all Python files
        for py_file in self.app_root.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                self.analyze_file(py_file)

        # Run all verification checks
        self.verify_core_pipeline_integration()
        self.verify_data_layer_integration()
        self.verify_orchestrator_dependencies()
        self.verify_gui_integration()
        self.verify_configuration_consistency()
        self.verify_error_handling()
        self.verify_slrinator_integration()
        self.verify_resources()

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if not self.issues and not self.warnings:
            print("✅ ALL CHECKS PASSED - No issues found!")
        else:
            if self.issues:
                print(f"\n🔴 CRITICAL ISSUES ({len(self.issues)}):")
                for issue in self.issues:
                    print(f"  - {issue}")

            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for warning in self.warnings:
                    print(f"  - {warning}")

        print("\n" + "=" * 60)

        return len(self.issues) == 0


if __name__ == "__main__":
    validator = CrossReferenceValidator()
    success = validator.run_all_validations()
    sys.exit(0 if success else 1)
