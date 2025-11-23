#!/usr/bin/env python3
"""
R1 Validation Setup Script
Sets up the R1 cite checking system with all dependencies and configuration
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Optional

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_header(text: str):
    """Print colored header."""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")


def print_step(num: int, text: str):
    """Print step number."""
    print(f"{GREEN}[Step {num}]{RESET} {text}")


def print_success(text: str):
    """Print success message."""
    print(f"{GREEN}✓{RESET} {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{YELLOW}⚠{RESET} {text}")


def print_error(text: str):
    """Print error message."""
    print(f"{RED}✗{RESET} {text}")


def check_python_version():
    """Ensure Python 3.8+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required. Current: {version.major}.{version.minor}")
        return False
    print_success(f"Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_requirements():
    """Install Python requirements."""
    print_step(1, "Installing Python dependencies...")

    req_file = Path(__file__).parent / "requirements_r1.txt"
    if not req_file.exists():
        print_warning(f"Requirements file not found: {req_file}")
        print("Continuing with existing packages...")
        return True

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            check=True,
            capture_output=True
        )
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        print(e.stderr.decode())
        return False


def setup_config_directory():
    """Create config directory and files."""
    print_step(2, "Setting up configuration...")

    base_dir = Path(__file__).parent
    config_dir = base_dir / "config"
    rules_dir = config_dir / "rules"

    # Create directories
    rules_dir.mkdir(parents=True, exist_ok=True)
    print_success(f"Config directory: {config_dir}")

    # Check for Bluebook.json
    bluebook_path = rules_dir / "Bluebook.json"
    if not bluebook_path.exists():
        print_warning("Bluebook.json not found")
        # Try to copy from reference_files
        reference_bluebook = base_dir.parent / "reference_files" / "Bluebook.json"
        if reference_bluebook.exists():
            import shutil
            shutil.copy(reference_bluebook, bluebook_path)
            print_success(f"Copied Bluebook.json from reference_files")
        else:
            print_error("Bluebook.json not found. Please place it in config/rules/")
            return False
    else:
        print_success("Bluebook.json found")

    # Check/create api_keys.json
    api_keys_path = config_dir / "api_keys.json"
    if not api_keys_path.exists():
        template = {
            "openai": {
                "api_key": "",
                "assistant_id": ""
            },
            "courtlistener": {
                "token": ""
            },
            "govinfo": {
                "api_key": ""
            }
        }
        with open(api_keys_path, 'w') as f:
            json.dump(template, f, indent=2)
        print_warning(f"Created template api_keys.json - please add your API keys")
    else:
        print_success("api_keys.json exists")

    return True


def setup_output_directories():
    """Create output directory structure."""
    print_step(3, "Creating output directories...")

    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"

    dirs = [
        output_dir / "r1_validation",
        output_dir / "data" / "Sourcepull" / "Retrieved",
        output_dir / "data" / "Sourcepull" / "Redboxed",
        output_dir / "logs",
        output_dir / "reports"
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

    print_success(f"Output structure created in {output_dir}")
    return True


def verify_installation():
    """Verify all components are installed."""
    print_step(4, "Verifying installation...")

    errors = []

    # Check imports
    try:
        import openai
        print_success("OpenAI SDK installed")
    except ImportError:
        errors.append("openai package not installed")

    try:
        import fitz  # PyMuPDF
        print_success("PyMuPDF installed")
    except ImportError:
        errors.append("PyMuPDF not installed")

    try:
        from docx import Document
        print_success("python-docx installed")
    except ImportError:
        errors.append("python-docx not installed")

    try:
        import pandas
        print_success("pandas installed")
    except ImportError:
        errors.append("pandas not installed")

    # Check module imports
    base_dir = Path(__file__).parent
    sys.path.insert(0, str(base_dir / "src"))

    try:
        from r1_validation import CitationValidator, QuoteVerifier, LLMInterface
        print_success("R1 validation modules importable")
    except ImportError as e:
        errors.append(f"R1 validation modules not importable: {e}")

    if errors:
        print_error("Installation verification failed:")
        for error in errors:
            print(f"  - {error}")
        return False

    print_success("All components verified")
    return True


def check_api_key():
    """Check if OpenAI API key is configured."""
    print_step(5, "Checking API configuration...")

    config_dir = Path(__file__).parent / "config"
    api_keys_path = config_dir / "api_keys.json"

    if not api_keys_path.exists():
        print_warning("API keys file not found")
        return False

    try:
        with open(api_keys_path, 'r') as f:
            keys = json.load(f)

        openai_key = keys.get('openai', {}).get('api_key', '')
        if openai_key and openai_key != "":
            print_success("OpenAI API key configured")
            return True
        else:
            print_warning("OpenAI API key not set in config/api_keys.json")
            print(f"   Please edit {api_keys_path} and add your API key")
            return False
    except Exception as e:
        print_error(f"Failed to read API keys: {e}")
        return False


def print_next_steps():
    """Print next steps for user."""
    print_header("Setup Complete!")

    print(f"{GREEN}R1 Cite Checking System is ready!{RESET}\n")

    print("Next steps:\n")
    print("1. Configure your API key (if not done):")
    print(f"   {YELLOW}Edit: SLRinator/config/api_keys.json{RESET}")
    print("   Add your OpenAI API key\n")

    print("2. Run your first R1 workflow:")
    print(f"   {BLUE}python r1_workflow.py your_article.docx --footnotes 1-10{RESET}\n")

    print("3. Review the reports:")
    print("   - JSON: output/r1_validation/r1_validation_report_*.json")
    print("   - HTML: output/r1_validation/r1_validation_report_*.html\n")

    print("4. Run tests:")
    print(f"   {BLUE}python tests/test_r1_validation.py{RESET}\n")

    print("For more information:")
    print(f"   {BLUE}cat R1_CITE_CHECKING_README.md{RESET}\n")


def main():
    """Main setup function."""
    print_header("R1 Cite Checking Setup")
    print("Setting up Stanford Law Review R1 validation system\n")

    # Change to SLRinator directory
    os.chdir(Path(__file__).parent)

    # Run setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_requirements),
        ("Setting up configuration", setup_config_directory),
        ("Creating output directories", setup_output_directories),
        ("Verifying installation", verify_installation),
        ("Checking API configuration", check_api_key),
    ]

    all_success = True
    for desc, func in steps:
        if not func():
            all_success = False
            print_error(f"Setup step failed: {desc}")
            print("\nSetup incomplete. Please fix errors and run again.")
            return 1

    print_next_steps()
    return 0


if __name__ == "__main__":
    sys.exit(main())
