# Automated R2 Citecheck Pipeline

This project automates the R2 citechecking process for the Stanford Law Review, as outlined in the Volume 78 Member Editor Handbook.

## Overview

The pipeline dynamically finds the correct R1 PDF for each footnote by searching for keywords from the citation within the text of the R1 PDFs. This removes the need for a strict filename-to-footnote mapping. It also updates the master spreadsheet and the article's Word document with tracked changes.

Items that cannot be automatically verified are flagged for human review in a web-based UI.

## Features

- **PDF Text and Annotation Extraction**: Extracts text and redbox annotations from R1 PDFs.
- **Citation Parsing**: Parses footnotes into structured citation data.
- **LLM-Powered Validation**: Uses GPT-4o-mini to validate citation formatting and proposition support.
- **Quote Accuracy Checking**: Deterministically verifies quoted text character-by-character.
- **Automated Document Generation**: Creates R2 PDFs with annotations, updates Excel spreadsheets, and generates Word documents with tracked changes.
- **Human Review Queue**: Generates an HTML report and a Flask-based web UI for items that require manual review.

## Project Structure

```
r2_pipeline/
├── config/                # Configuration files
├── src/                    # Source code
│   ├── templates/          # Flask templates
│   ├── __init__.py
│   ├── citation_parser.py
│   ├── ... (other source files)
├── prompts/               # Prompts for the LLM
├── data/
│   ├── input/              # Input files (PDFs, spreadsheet, Word doc)
│   └── output/             # Generated files (R2 PDFs, logs, reports)
├── requirements.txt
└── main.py                 # Main pipeline orchestrator
README.md
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd r2_pipeline
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Set up your OpenAI API key:**
    - Create a `.env` file in the project root.
    - Add your OpenAI API key to the `.env` file:
      ```
      OPENAI_API_KEY="your-api-key-here"
      ```

4.  **Place your input files in the `data/input` directory:**
    - R1 PDFs in `data/input/r1_pdfs/`
    - Master spreadsheet in `data/input/spreadsheet/`
    - Word document in `data/input/word_doc/`

## Running the Pipeline

To run the entire pipeline, execute the `main.py` script:

```bash
python main.py
```

This will:
1.  Process all input files.
2.  Generate R2 PDFs, an updated spreadsheet, and a new Word document in the `data/output` directory.
3.  Create a `full_pipeline_log.json` in `data/output/logs/`.
4.  Generate a `human_review_queue.html` report in `data/output/reports/`.

## Human Review UI

To start the web-based review UI, run the `review_ui.py` script:

```bash
python src/review_ui.py
```

Then, open your web browser and navigate to `http://127.0.0.1:5001`.
