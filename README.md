# Stanford Law Review Workflow Management System

A comprehensive workflow management system for the Stanford Law Review, consisting of a user-facing web application and a three-stage automated editorial pipeline.

## System Architecture

The system is designed as a sequential pipeline that automates the entire cite-checking process:

1. **Google Apps Script Web App**: User-facing frontend for managing tasks, attendance, and administrative duties
2. **sp_machine (Sourcepull Machine)**: Retrieves raw, format-preserving source files based on citations
3. **r1_machine (Preparation Machine)**: Prepares sources for review by cleaning PDFs and performing metadata redboxing
4. **r2_machine (Validation Machine)**: Performs LLM-powered validation including Bluebook checking and proposition support verification

## Project Structure

```
slr/
├── google_apps_script/     # Web app frontend (Google Apps Script)
│   ├── Code.js             # Main backend logic
│   ├── DAL.js              # Data Abstraction Layer
│   ├── html/               # HTML templates
│   ├── css/                # Stylesheets
│   └── js/                 # Client-side JavaScript
├── sp_machine/             # Stage 1: Source retrieval
│   ├── main.py
│   └── src/
├── r1_machine/             # Stage 2: PDF preparation & redboxing
│   ├── main.py
│   └── src/
├── r2_machine/             # Stage 3: LLM-powered validation
│   ├── main.py
│   ├── src/
│   └── prompts/
├── shared_utils/           # Shared utilities across machines
├── tests/                  # Unit and integration tests
├── docs/                   # Additional documentation
├── scripts/                # Deployment and utility scripts
├── info/                   # Project specifications
└── reference_files/        # Reference materials (handbooks, rules)
```

## Installation

### Prerequisites

- Python 3.9+
- Node.js and npm (for Google Apps Script development with clasp)
- Google Workspace account (@stanford.edu)

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd slr
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Install clasp for Google Apps Script development:
```bash
npm install -g @google/clasp
```

4. Configure Google Apps Script:
```bash
cd google_apps_script
clasp login
clasp create --type webapp --title "SLR Workflow Dashboard"
```

## Usage

### Running the Pipeline

Each article goes through the three-stage pipeline:

```bash
# Stage 1: Retrieve sources
cd sp_machine
python main.py --article-id "79.1.article_name"

# Stage 2: Prepare PDFs
cd ../r1_machine
python main.py --input ../sp_machine/output --article-id "79.1.article_name"

# Stage 3: Validate citations
cd ../r2_machine
python main.py --input ../r1_machine/output --article-id "79.1.article_name"
```

### Deploying the Web App

```bash
cd google_apps_script
clasp push
clasp deploy
```

## Documentation

- [Implementation Plan](info/implementation.md) - Technical implementation details
- [Substantive Content](info/substantive_content.md) - Functionality and workflows
- [Architectural Blueprint](info/Architectural_Blueprint.md) - Comprehensive system design

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/
```

### Code Style

- Python: Follow PEP 8
- JavaScript: Follow Google JavaScript Style Guide
- Use type hints in Python code
- Document all public functions and classes

## Security

- All web app access restricted to @stanford.edu domain
- OAuth 2.0 authentication for Google services
- LockService for concurrency control
- Follows Stanford University IT policies

## License

See [LICENSE](LICENSE) file for details.

## Contributing

This is an internal Stanford Law Review project. For questions or contributions, contact the development team.
