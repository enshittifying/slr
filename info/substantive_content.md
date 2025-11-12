# Substantive Content: Stanford Law Review Workflow Management System

This document describes the functionality and content of the Stanford Law Review's workflow management system.

## 1. Core Purpose

The system is designed to streamline and automate the administrative and editorial workflows of the Stanford Law Review. It provides a central platform for managing members, tasks, and the entire citation checking process, from source pulling to final verification.

The editorial process is cyclical, revolving around the publication of an annual **Volume** (e.g., Volume 78, Volume 79), which is composed of six **Issues**. The entire three-stage automated pipeline is designed to be executed independently for each article within each issue. For example, an article for Volume 79, Issue 1 (referred to as "79.1") will have its own dedicated Sourcepull, R1, and R2 processes.

## 2. The Automated Editorial Pipeline

The core of the system is a three-stage automated pipeline that handles the entire citation checking process, from finding the sources to performing the final validation.

### 2.1. Stage 1: The Sourcepull Machine (`sp_machine`)

This is the first step in the pipeline. Its function is to **find and retrieve** the raw source material for every citation in an article.

-   **Functionality**: It reads a list of citations from the master spreadsheet, identifies the source type (e.g., case, article, website), and uses a variety of "pullers" to connect to legal databases and websites to download a format-preserving PDF of the source.
-   **Output**: A collection of raw, unprepared source PDFs.

### 2.2. Stage 2: The R1 Machine (Preparation & Redboxing)

The R1 Machine is a proposed system that takes the raw PDFs from the Sourcepull Machine and **prepares** them for substantive review. This stage automates the mechanical parts of the "Sourcepull" process as defined in the handbook.

-   **Functionality**:
    -   **PDF Cleaning**: It removes extraneous pages (like database cover sheets) from the raw source files.
    -   **Metadata Redboxing**: It automatically identifies and draws red boxes around the key citation information (author, title, reporter, volume, year, etc.) on the face of the source PDF. This provides the necessary metadata for the final validation stage.
-   **Output**: A collection of "R1 PDFs" that are clean and have their citation metadata redboxed. These PDFs are the direct input for the final stage of the pipeline.

### 2.3. Stage 3: The R2 Machine / SLRinator (`r2_pipeline`)

This is the final and most complex stage of the pipeline, performing the substantive validation of the author's work. It consumes the prepared R1 PDFs from the R2 machine.

-   **Functionality**:
    -   **LLM-Powered Citation Formatting**: Using the `Bluebook.json` and `Redbook` rules, it validates that every citation is perfectly formatted and suggests corrections.
    -   **LLM-Powered Proposition Support Checking**: It analyzes the text of the source (as identified by redboxes) to determine if it truly supports the legal proposition the author has made.
    -   **Quote Verification**: It performs a character-by-character check to ensure all quoted material is transcribed perfectly.
    -   **Report and Document Generation**: It produces the final R2 documents, including annotated PDFs, an updated spreadsheet, a Word document with tracked changes, and a queue of items that require human review.

## 3. Web Dashboard (Google Apps Script)

The primary user interface for human editors is a web-based dashboard that provides the following features:

-   **Task Management**: Members can view and mark tasks as complete. The dashboard displays a personalized list of assignments for each user.
-   **Form Engine**: The system includes a dynamic form engine that can generate and process forms.
-   **Attendance Tracking**: An attendance engine allows for tracking member attendance at events.
-   **User Management**: The system manages a list of members and their roles.

All of this functionality is backed by a master Google Sheet, which serves as the central database for the application.

## 4. Reference Materials

The system relies on a set of key reference materials to perform its functions:

-   **`Bluebook.json`**: A JSON file containing a structured representation of the Bluebook and Redbook citation rules. This file is used by the LLM to ensure that its format checking is accurate and consistent.
-   **`redbook_processed/`**: A directory containing an HTML version of the Redbook.
-   **`r1_handbook_summary.md`**: A structured summary of the R1 process, derived from the Member Editor Handbook, which informs the design of the R1 Machine.
-   **`78.6 Sanders Master Sheet.xlsx`**: The master spreadsheet that serves as the database for the entire system. It is a living document that is continuously updated by editors throughout the lifecycle of a volume. Its specific structure and content will evolve over time.
-   **`Volume 78 Member Editor Handbook.pdf`**: The official handbook that outlines the manual cite-checking process that the automated pipeline is designed to replace.
