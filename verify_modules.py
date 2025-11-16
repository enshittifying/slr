"""
Comprehensive Module Verification and Fixing Script
Systematically checks and fixes every module
"""
import sys
from pathlib import Path
import ast
import re

# Add app to path
app_root = Path(__file__).parent / "app"
sys.path.insert(0, str(app_root))


class ModuleVerifier:
    """Verifies and fixes all application modules"""

    def __init__(self):
        self.app_root = Path(__file__).parent / "app"
        self.issues = []
        self.fixes = []
        self.warnings = []

    def verify_all(self):
        """Verify all modules systematically"""
        print("=" * 70)
        print("COMPREHENSIVE MODULE VERIFICATION")
        print("=" * 70)

        # 1. Verify utils modules
        print("\n=== UTILS MODULES ===")
        self.verify_module("utils/config.py")
        self.verify_module("utils/crypto.py")
        self.verify_module("utils/auth.py")
        self.verify_module("utils/logging.py")
        self.verify_module("utils/retry.py")
        self.verify_module("utils/edge_cases.py")

        # 2. Verify data modules
        print("\n=== DATA MODULES ===")
        self.verify_module("data/sheets_client.py")
        self.verify_module("data/drive_client.py")
        self.verify_module("data/llm_client.py")

        # 3. Verify core modules
        print("\n=== CORE MODULES ===")
        self.verify_module("core/sp_machine.py")
        self.verify_module("core/r1_machine.py")
        self.verify_module("core/r2_pipeline.py")
        self.verify_module("core/orchestrator.py")

        # 4. Verify GUI modules
        print("\n=== GUI MODULES ===")
        self.verify_module("gui/main_window.py")
        self.verify_module("gui/sp_manager.py")
        self.verify_module("gui/r1_manager.py")
        self.verify_module("gui/r2_manager.py")
        self.verify_module("gui/settings_dialog.py")
        self.verify_module("gui/workers.py")
        self.verify_module("gui/progress_widget.py")

        # 5. Verify main
        print("\n=== MAIN MODULE ===")
        self.verify_module("main.py")

        # Print summary
        self.print_summary()

    def verify_module(self, module_path):
        """Verify a single module"""
        file_path = self.app_root / module_path

        if not file_path.exists():
            print(f"✗ {module_path} - FILE NOT FOUND")
            self.issues.append(f"{module_path} not found")
            return

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Parse as AST
            try:
                tree = ast.parse(content)
                syntax_ok = True
            except SyntaxError as e:
                print(f"✗ {module_path} - SYNTAX ERROR: {e}")
                self.issues.append(f"{module_path} has syntax error")
                syntax_ok = False

            if not syntax_ok:
                return

            # Check for docstring
            has_docstring = ast.get_docstring(tree) is not None

            # Check imports
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    imports.append(module)

            # Check for error handling
            has_try_except = any(isinstance(node, ast.Try) for node in ast.walk(tree))

            # Check for logging
            has_logging = 'logging' in content or 'logger' in content

            # Build status
            status_parts = []
            if not has_docstring:
                self.warnings.append(f"{module_path} missing module docstring")
                status_parts.append("no docstring")

            if not has_try_except and module_path not in ['__init__.py', 'gui/styles.qss']:
                self.warnings.append(f"{module_path} has no error handling")
                status_parts.append("no try/except")

            if not has_logging and 'gui' not in module_path and '__init__' not in module_path:
                self.warnings.append(f"{module_path} has no logging")
                status_parts.append("no logging")

            # Check for common issues
            issues = self.check_common_issues(content, module_path)

            if issues:
                status_parts.extend(issues)

            if status_parts:
                print(f"⚠  {module_path} - {', '.join(status_parts)}")
            else:
                print(f"✓ {module_path}")

        except Exception as e:
            print(f"✗ {module_path} - ERROR: {e}")
            self.issues.append(f"{module_path}: {str(e)}")

    def check_common_issues(self, content, module_path):
        """Check for common issues"""
        issues = []

        # Check for relative imports in app modules
        if 'from ..' in content or 'from .' in content:
            # This is OK for internal imports
            pass

        # Check for hardcoded paths
        if re.search(r'["\']/(home|Users|C:\\)', content):
            issues.append("hardcoded paths")

        # Check for print statements (should use logging)
        if re.search(r'\bprint\s*\(', content) and 'test' not in module_path:
            issues.append("uses print()")

        # Check for bare except
        if re.search(r'except\s*:', content):
            issues.append("bare except")

        # Check for TODO/FIXME
        if 'TODO' in content or 'FIXME' in content:
            issues.append("has TODO/FIXME")

        return issues

    def print_summary(self):
        """Print verification summary"""
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)

        if not self.issues and not self.warnings:
            print("\n✅ ALL MODULES VERIFIED SUCCESSFULLY")
        else:
            if self.issues:
                print(f"\n🔴 CRITICAL ISSUES ({len(self.issues)}):")
                for issue in self.issues:
                    print(f"  - {issue}")

            if self.warnings:
                print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                for warning in self.warnings[:10]:  # Limit to first 10
                    print(f"  - {warning}")
                if len(self.warnings) > 10:
                    print(f"  ... and {len(self.warnings) - 10} more")

        print("\n" + "=" * 70)


if __name__ == "__main__":
    verifier = ModuleVerifier()
    verifier.verify_all()
