# Implementation Plan: Stanford Law Review Workflow Management System

This document outlines the technical implementation of the Stanford Law Review's workflow management system. The system is comprised of a user-facing web application and a three-stage automated editorial pipeline.

## 1. High-Level Architecture

The system is designed as a sequential pipeline that automates the entire cite-checking process, from source retrieval to final validation.

-   **Google Apps Script Web App**: The user-facing frontend for managing tasks, attendance, and other administrative duties. It communicates with a Google Sheet that acts as the database.
-   **Stage 1: `sp_machine` (The Sourcepull Machine)**: This machine is the first step in the pipeline. Its sole responsibility is to **retrieve** raw, format-preserving source files (e.g., PDFs) based on a list of citations from the master spreadsheet.
-   **Stage 2: R1 Machine (The Preparation Machine)**: This proposed machine takes the raw source files from the `sp_machine` as input. Its job is to **prepare** the sources for substantive review by cleaning them, merging necessary pages, and performing the initial **metadata redboxing** as outlined in the Sourcepull process.
-   **Stage 3: `r2_pipeline` (The R2 Validation Machine)**: This is the final stage. It consumes the prepared R1 PDFs from the R1 Machine. It performs the advanced, LLM-powered validation, including checking citation formatting against the Bluebook, verifying proposition support, and generating final, annotated R2 documents.

This structure creates a clear flow: the `sp_machine` gets the sources, the `R1 Machine` prepares them, and the `r2_pipeline` validates them. The entire pipeline is executed on a per-article basis for each of the six issues within a volume (e.g., an article in Volume 79, Issue 1 will undergo its own SP, R1, and R2 process).

## 2. Google Apps Script Web App

The frontend is a Google Apps Script web app that provides a dashboard for members of the Law Review.

### Key Files:

-   **`Code.js`**: The main backend logic for the web app. It handles user authentication, routing, and serves the main HTML page. It also contains functions for setting up the Google Sheet database.
-   **`DAL.js`**: The Data Abstraction Layer, responsible for all interactions with the Google Sheet that serves as the master database. It includes functions for reading and writing data to different tabs (Members, Tasks, etc.).
-   **`Dashboard.js`**, **`FormEngine.js`**, **`AttendanceEngine.js`**, **`TaskEngine.js`**: These files contain the specific business logic for the different features of the web app.
-   **`index.html`** and **`client_side_script.html`**: The HTML and JavaScript for the user interface. The UI is built using standard HTML and JavaScript, with `google.script.run` used to communicate with the backend Apps Script functions.
-   **`appsscript.json`**: The manifest file for the Google Apps Script project, defining permissions and other settings.
-   **`.clasp.json`**: The configuration file for `clasp`, the command-line tool used to manage the Apps Script project.

### Implementation Details:

-   **Database**: A single Google Sheet (`78.6 Sanders Master Sheet.xlsx`) with multiple tabs acts as the database. The schema is defined in `Code.js`.
-   **Concurrency**: `LockService` is used to prevent race conditions when multiple users are accessing the system simultaneously.
-   **Deployment**: The project is deployed as a web app using `clasp`.

## 3. `sp_machine` (The Sourcepull Machine)

This machine is the first step of the automated pipeline. Its exclusive role is to find and download the raw source files.

### Key Files:

-   **`main.py`**: The main script for the `sp_machine`. It reads sources from the spreadsheet, parses their citations, and then uses the pullers to retrieve the source material.
-   **`src/spreadsheet_parser.py`**: A parser for reading the list of sources from the master spreadsheet.
-   **`src/citation_parser.py`**: A citation parser to understand what to search for.
-   **`src/pullers.py`**: A module containing functions to fetch content from various locations (e.g., websites, APIs for legal databases).

### Implementation Details:
-   **Input**: A list of citations from the master spreadsheet.
-   **Note on Data Volatility**: The implementation must account for the fact that the master spreadsheet is a living document. It will be continuously updated by editors, and its structure or content may change from one volume to the next. The machine must read the current state of the spreadsheet at runtime to ensure it is working with the most up-to-date information.
-   **Process**: For each citation, it determines the likely location (e.g., Westlaw, JSTOR, a specific website) and uses the appropriate puller to download a format-preserving PDF.
-   **Output**: A directory of raw, unprepared source PDFs. These files serve as the input for the R1 Machine.

## 4. R1 Machine (The Preparation Machine - Proposed)

This proposed second stage of the pipeline processes the raw sources retrieved by the `sp_machine`. Its goal is to prepare these sources for the final validation step.

### Implementation Steps:

1.  **Source Ingestion**:
    -   **Action**: Consume the raw PDFs from the output of the `sp_machine`.

2.  **PDF Preparation & Metadata Redboxing**:
    -   **Action**: Clean the PDF and redbox the citation metadata.
    -   **Implementation**:
        -   Use a library like `PyMuPDF` to manipulate the PDFs, including deleting cover pages and merging additional required pages.
        -   Use a computer vision or NLP model to perform OCR, identify essential citation elements (author, title, etc.), and draw red boxes around them.

3.  **Filing and Logging**:
    -   **Action**: Save the prepared PDF (now an "R1 PDF") to a designated "R1" folder in Google Drive and update the spreadsheet.
    -   **Implementation**: Use the Google Drive and Google Sheets APIs to upload the file and log its status and location.

-   **Output**: A directory of prepared R1 PDFs, with citation metadata redboxed. This output is the direct input for the `r2_pipeline`.

## 5. `r2_pipeline` (The R2 Validation Machine)

The `r2_pipeline` (also known as the SLRinator) is the final and most sophisticated stage of the pipeline. It consumes the prepared R1 PDFs and performs the substantive validation.

### Key Files:

-   **`main.py`**: The main orchestrator for the pipeline. It finds the appropriate R1 PDF for a given footnote and initiates the validation process.
-   **`src/pdf_processor.py`**: A utility for processing the R1 PDFs, but now focusing on extracting the *substantive text* needed for support checking (not just the metadata).
-   **`src/citation_validator.py`**, **`src/support_checker.py`**, **`src/quote_verifier.py`**: The core LLM-powered modules that perform the validation against Bluebook/Redbook rules and check for proposition support.
-   **`src/r2_generator.py`**, **`src/word_editor.py`**: Modules for generating the final output documents, including the annotated R2 PDF and the Word document with tracked changes.
-   **`prompts/`**: Contains the prompts for the LLM.

### Implementation Details:

-   **Workflow**: The pipeline receives a prepared R1 PDF from the R1 Machine. It then uses its LLM-based components to validate the citation's formatting and to check if the source text (as identified by the R1 substantive redboxing, if available) supports the author's proposition.
-   **Input**: Prepared R1 PDFs from the R1 Machine.
-   **Output**: A complete set of R2 materials: annotated R2 PDFs, an updated spreadsheet with validation status, a Word document with tracked changes, and a report for items requiring human review.
