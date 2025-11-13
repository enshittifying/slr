# Comprehensive Plan: Source Pull & Redboxing Automation

This document outlines a detailed plan for building the "Source Pull machine," a comprehensive tool to automate the source pulling and redboxing process for the Stanford Law Review.

## 1. Project Goal

The primary objective is to create a robust and user-friendly tool that automates the tedious and error-prone tasks of source pulling and redboxing. The tool will read a list of citations from a master spreadsheet, retrieve the corresponding sources, and prepare them for the citation checking process.

## 2. Core Features

The Source Pull machine will have the following core features:

*   **Automated Source Retrieval:** The tool will automatically pull sources from a variety of online databases, including websites, legal databases (Westlaw, Lexis), and journal archives (HeinOnline, JSTOR).
*   **Source Type Detection:** The tool will be able to accurately identify the type of a source (e.g., case, article, book) based on its citation string.
*   **Automated Redboxing:** The tool will use AI to automatically identify and redbox the key citation information in the pulled PDFs.
*   **Reflexive Reference Resolution:** The tool will be able to handle "supra" and "infra" references by finding the original source they refer to.
*   **User-Friendly Interface:** The tool will have a simple web-based interface that allows users to manage the source pulling process and review the results.

## 3. Architecture

The Source Pull machine will be a Python-based application with the following components:

*   **`sp_machine` directory:** The main project directory.
    *   **`src`:** Contains the core application logic.
        *   **`main.py`:** The main pipeline orchestrator.
        *   **`doc_parser.py`:** Parses the main article/note Word document to extract footnotes and build a citation map.
        *   **`spreadsheet_parser.py`:** Parses the master spreadsheet to get the list of sources to pull.
        *   **`citation_parser.py`:** Parses individual citation strings into structured data.
        *   **`source_detector.py`:** Detects the type of a source based on its citation.
        *   **`pullers.py`:** Contains functions for pulling different types of sources.
        *   **`llm.py`:** Handles all interactions with the GPT-4o API.
        *   **`redboxer.py`:** Applies redboxes to the pulled PDFs.
    *   **`config`:** Contains configuration files.
    *   **`prompts`:** Contains prompt templates for the GPT-4o calls.
    *   **`data`:** Contains input and output data.
        *   **`input`:** The master spreadsheet and the main article/note Word document.
        *   **`output`:** The pulled sources and the redboxed PDFs.
    *   **`templates`:** Contains HTML templates for the Flask web interface.
    *   **`static`:** Contains static files (CSS, JavaScript) for the web interface.
*   **`requirements.txt`:** Lists the project dependencies.
*   **`.venv`:** A virtual environment for the project.

## 4. Implementation Plan

The implementation will be broken down into the following steps:

### Step 1: Project Setup

1.  Create the directory structure as described above.
2.  Create the `requirements.txt` file with the following dependencies:
    ```
    selenium
    pypdf2
    reportlab
    openai
    openpyxl
    weasyprint
    python-docx
    flask
    pandas
    ```
3.  Create a virtual environment and install the dependencies.

### Step 2: Spreadsheet Parsing

1.  Create the `spreadsheet_parser.py` module.
2.  Use the `pandas` library to read the `V78.4 Bersh Master Sheet.xlsx` file. `pandas` is more robust for handling complex Excel files.
3.  Implement logic to find the header row and the data, even with the complex formatting.
4.  Extract the "Source Number", "Short Name", and "Full Citation" for each source.

### Step 3: Word Document Parsing

1.  Create the `doc_parser.py` module.
2.  Use the `python-docx` library to read the `Bersh_PreR2.docx` file.
3.  Extract all footnotes from the document.
4.  Build a citation map (a dictionary where the keys are footnote numbers and the values are the citation strings).

### Step 4: Citation Parsing and Source Type Detection

1.  Create the `citation_parser.py` module (I have already done this).
2.  Create the `source_detector.py` module.
3.  Implement a `detect_source_type` function that uses a combination of regex, keyword matching, and a GPT-4o call to determine the source type.

### Step 5: Source Pulling

1.  Create the `pullers.py` module.
2.  Implement the `pull_website` function (I have already done this).
3.  Implement `pull_case` and `pull_article` functions. This will require using `selenium` to interact with Westlaw, Lexis, HeinOnline, and JSTOR. I will need to ask the user for credentials for these services.

### Step 6: Automated Redboxing

1.  Create the `llm.py` module.
2.  Implement a `get_redbox_snippets` function that uses GPT-4o to identify the text snippets that need to be redboxed.
3.  Create the `redboxer.py` module.
4.  Implement a `redbox_pdf` function that uses `PyMuPDF` (fitz) and `reportlab` to apply the redboxes to the PDFs.

### Step 7: Reflexive Reference Resolution

1.  In `main.py`, after building the citation map, implement logic to resolve "supra" and "infra" references.
2.  When a reflexive reference is encountered, use the citation map to find the original source and then pull that source instead.

### Step 8: Web Interface (Flask)

1.  Create a `app.py` file for the Flask application.
2.  Create HTML templates for the user interface.
3.  Implement routes for:
    *   Uploading the master spreadsheet and the Word document.
    *   Starting the source pull process.
    *   Viewing the progress of the pipeline.
    *   Viewing the pulled sources and the redboxed PDFs.

## 5. Next Steps

I will start by implementing Step 1 and Step 2 of the plan. I will create the project structure and the `spreadsheet_parser.py` module. I will use `pandas` to read the `V78.4 Bersh Master Sheet.xlsx` file and extract the source list.
