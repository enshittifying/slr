# Summary of the R1 Process (Sourcepull & Round 1 Citecheck)

This document summarizes the "R1" (First Round) editing process as described in the Volume 78 Member Editor Handbook. It is intended to inform the design of an "R1 Machine" to automate these steps.

The R1 process consists of two main phases: **Sourcepull** and **Round 1 Citecheck**.

---

## Phase 1: Sourcepull (SP)

**Goal:** To find, prepare, and log a format-preserving PDF for every source cited in the article.

### Step 1: Finding the Source
- **Action:** Locate a format-preserving version of the source. The preferred version is dictated by the Bluebook and the SLR Redbook.
- **Automation Opportunity (R1 Machine):**
    - Connect to legal databases (Westlaw, Lexis, HeinOnline), library catalogs (SearchWorks), and general web resources (Google Books, SSRN).
    - Use the citation text to query these databases via APIs.
    - Prioritize sources as defined in the handbook (e.g., HeinOnline for Supreme Court cases, official PDFs for statutes).
    - Flag sources that require manual intervention (e.g., physical books, ILL requests).

### Step 2: Preparing the Redboxed PDF
- **Action:** Once the source PDF is acquired, it must be cleaned and annotated.
- **Sub-steps:**
    1.  **Delete Front Matter:** Remove extraneous pages from database-provided PDFs (e.g., HeinOnline cover pages).
    2.  **Redbox Citation Information:** Draw a red box around all elements required for a full Bluebook citation (author, title, journal, volume, page, year, etc.). This is for metadata, not substantive support.
    3.  **Add Additional Pages:** Merge supplementary material into the PDF, such as:
        - The table of contents for a journal issue.
        - Subsequent history or negative treatment for a case.
        - Front matter for a book.
- **Automation Opportunity (R1 Machine):**
    - **PDF Manipulation:** Use libraries to delete pages and merge PDFs.
    - **Automated Redboxing:** This is a significant computer vision and NLP challenge. The machine would need to:
        - Perform OCR on the PDF.
        - Identify key citation elements in the text.
        - Draw bounding boxes (redboxes) around these elements in the PDF.

### Step 3: Filing the Source
- **Action:** Save the prepared PDF to a designated Google Drive folder.
- **Naming Convention:** `SP-[source number]-[short name].pdf`
- **Automation Opportunity (R1 Machine):**
    - Integrate with the Google Drive API.
    - Automatically rename and upload the generated PDF to the correct, article-specific folder.

### Step 4: Logging the Source
- **Action:** Update the master Sourcepull spreadsheet with the status, a link to the filed PDF, and notes on any issues.
- **Automation Opportunity (R1 Machine):**
    - Integrate with the Google Sheets API.
    - Automatically fill in the row for the corresponding source with a direct link to the PDF in Google Drive.
    - Log errors or missing sources in the designated columns.

---

## Phase 2: Round 1 (R1) Citecheck

**Goal:** To substantively evaluate the author's claims against the pulled sources and perform an initial round of edits. While the R2 pipeline automates much of the *validation*, the R1 process involves more manual evaluation and judgment.

### Step 1: Create the Citecheck PDF
- **Action:** For each citation, download the corresponding Sourcepull PDF and rename it for the R1 process.
- **Naming Convention:** `R1-[footnote number]-[citation order]-[source ID]-[short name].pdf`

### Step 2: Evaluate and Redbox the Source
- **Action:** This is the core substantive check. The editor reads the source and redboxes the *specific information* that supports or contradicts the author's proposition. This is distinct from the metadata redboxing in the Sourcepull phase.
- **Key Principle:** "Assume the author is wrong until you are convinced otherwise."

### Step 3: Fill out the Citecheck Spreadsheet
- **Action:** Log the findings of the substantive check in the citecheck spreadsheet, noting whether the source provides support.

### Step 4: In-Document Editing
- **Action:** Make direct edits (with track changes) to the Word document for clear errors. Leave comments for the author (`[AA:]`) or Senior Editor (`[SE:]`) for ambiguous or significant issues.

**Note on Automation:** The R1 Citecheck phase is more interpretive and less mechanical than the Sourcepull phase. While the R2 pipeline automates the *validation* part of this, the initial *evaluation* described in the R1 checklist is a manual human process. An "R1 Machine" would therefore focus primarily on automating the entire **Sourcepull** phase to prepare the materials for the human editor.
