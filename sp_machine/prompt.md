# Source Pull and Redboxing Automation for Legal Documents

## 1. Project Overview

The goal of this project is to create a "Source Pull machine" that automates the process of retrieving and preparing legal sources for citation checking, as described in the "Volume 78 Member Editor Handbook" of the Stanford Law Review. This involves:

1.  **Reading a list of citations** from a master spreadsheet.
2.  **Identifying the type of each source** (e.g., case, article, website).
3.  **Pulling a "format-preserving version"** of each source from the internet or other databases.
4.  **Preparing a "redboxed" PDF** of each source, which involves highlighting the key citation information.
5.  **Handling reflexive references** like "supra" and "infra".

## 2. Current State of the Project

### 2.1. Existing Code and Scripts

We have the following components:

*   **`sp_machine` directory:** This is the main project directory, containing the following subdirectories: `src`, `config`, `prompts`, `data/input`, `data/output/pulled_sources`, `data/output/redboxed_pdfs`.
*   **`requirements.txt`:** Lists the project dependencies: `selenium`, `pypdf2`, `reportlab`, `openai`, `openpyxl`, `weasyprint`, `python-docx`.
*   **`main.py`:** The main pipeline orchestrator. It is currently able to:
    *   Read a list of sources from a CSV file (`source_list.csv`).
    *   Parse the citations using a `CitationParser`.
    *   Detect the source type (currently only for websites).
    *   Call a `pull_website` function to download a website and save it as a PDF.
*   **`citation_parser.py`:** A module for parsing citation strings into structured data.
*   **`pullers.py`:** A module containing functions for pulling different types of sources. Currently, it only has a `pull_website` function.
*   **`doc_parser.py`:** A module for parsing Word documents and extracting footnotes.

### 2.2. Challenges and Limitations

The main challenge so far has been reliably reading the source list from the provided `V78.4 Bersh Master Sheet.xlsx` file. The spreadsheet has a complex, multi-row header and is not in a simple tabular format, which makes it difficult to parse with `openpyxl`.

My attempts to programmatically find the header row and the data have failed. I have tried:

*   Searching for specific header strings ("Source Number", "Fn #", etc.).
*   Searching for rows with a certain number of non-empty cells.
*   Manually inspecting the spreadsheet content.

Due to these difficulties, I have switched to using a manually created `source_list.csv` file, but this is not an ideal long-term solution.

Another challenge is the implementation of the "reflexive reference detection" and the automated redboxing. These are complex tasks that will require a sophisticated understanding of the document structure and the citation rules.

## 3. Desired Outcome

The desired outcome is a fully functional "Source Pull machine" that can:

1.  **Reliably read the source list** from the `V78.4 Bersh Master Sheet.xlsx` file.
2.  **Accurately identify the type** of each source.
3.  **Pull a format-preserving version** of each source from the correct location.
4.  **Automatically redbox** the key citation information in the pulled PDFs.
5.  **Handle reflexive references** correctly.
6.  **Provide a user-friendly interface** for running the pipeline and reviewing the results.

## 4. Request for Assistance

I am looking for a comprehensive solution to the challenges I am facing. Specifically, I need help with:

1.  **Parsing the `V78.4 Bersh Master Sheet.xlsx` file:** Please provide a robust Python script that can reliably extract the source information (Source Number, Short Name, Full Citation) from this spreadsheet, despite its complex formatting.

2.  **Implementing the full source pulling pipeline:** Please provide a detailed plan and code for the following:
    *   **Source Type Detection:** A function that can accurately determine the type of a source based on its citation string. This should handle all the source types listed in Appendix A of the Member Editor Handbook. A GPT-4o call that returns a JSON object with the source type and any extracted information would be ideal.
    *   **Pullers for all source types:** Functions for pulling all the different types of sources mentioned in the handbook (cases, articles, books, etc.). This will involve interacting with various legal databases like HeinOnline, Westlaw, and Lexis.
    *   **Automated Redboxing:** A process for automatically identifying and redboxing the key citation information in the pulled PDFs. This should use GPT-4o to determine what to redbox.
    *   **Reflexive Reference Resolution:** A system for handling "supra" and "infra" references.

3.  **Overall Architecture:** Please provide recommendations for the overall architecture of the `sp_machine`, including how the different modules should interact with each other.

Please provide the solution in the form of Python code and detailed explanations. I am looking for a practical and robust solution that I can implement and use for the Stanford Law Review's source pulling process.
