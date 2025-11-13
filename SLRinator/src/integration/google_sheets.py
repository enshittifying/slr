#!/usr/bin/env python3
"""
Google Sheets Integration for Stanford Law Review Sourcepull
Manages the sourcepull spreadsheet following SLR conventions
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from pathlib import Path

# For Google Sheets integration (install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client)
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("Warning: Google Sheets API not available. Install with: pip install google-api-python-client google-auth")

from src.core.retrieval_framework import RetrievalRecord, SourceType

logger = logging.getLogger(__name__)


class SourcepullSpreadsheet:
    """
    Manages the Google Sheets sourcepull spreadsheet
    Follows SLR formatting conventions from Member Handbook
    """
    
    # Standard columns for SLR sourcepull spreadsheet
    COLUMNS = [
        'Source #',           # 3-digit number (001, 002, etc.)
        'Footnote',          # Footnote number where first cited
        'Short Name',        # Short name for file naming
        'Full Citation',     # Complete citation text
        'Source Type',       # Case, Statute, Article, etc.
        'Status',           # Pulled, Missing, ILL Requested, etc.
        'Sourcepuller',     # Name of person who pulled
        'Date Pulled',      # Date source was pulled
        'File Location',    # Drive path or physical location
        'ILL Request Date', # For interlibrary loans
        'ILL Due Date',     # When ILL is due back
        'Physical Location', # For books - shelf location
        'Redboxed',         # Yes/No/Partial
        'Consecutively Paginated', # For journals
        'Subsequent History', # For cases
        'Negative Treatment', # For cases
        'Notes',            # Any additional notes
        'Drive Link',       # Link to file in Google Drive
        'Check',           # Validation checkmark
    ]
    
    def __init__(self, spreadsheet_id: Optional[str] = None, credentials_file: Optional[str] = None):
        """
        Initialize connection to Google Sheets
        
        Args:
            spreadsheet_id: Google Sheets ID (from URL)
            credentials_file: Path to service account credentials JSON
        """
        self.spreadsheet_id = spreadsheet_id
        self.service = None
        
        if SHEETS_AVAILABLE and credentials_file and os.path.exists(credentials_file):
            try:
                creds = service_account.Credentials.from_service_account_file(
                    credentials_file,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.service = build('sheets', 'v4', credentials=creds)
                logger.info("Connected to Google Sheets API")
            except Exception as e:
                logger.error(f"Failed to connect to Google Sheets: {e}")
        
        # Local cache of spreadsheet data
        self.local_data = []
        self.next_source_number = 1
    
    def initialize_spreadsheet(self, sheet_name: str = "Sourcepull"):
        """Initialize a new sourcepull spreadsheet with headers"""
        if not self.service or not self.spreadsheet_id:
            logger.warning("Cannot initialize spreadsheet - no connection")
            return False
        
        try:
            # Create header row
            values = [self.COLUMNS]
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A1:S1",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"Initialized spreadsheet with {len(self.COLUMNS)} columns")
            
            # Format header row (would need additional API calls for formatting)
            self._format_header_row(sheet_name)
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize spreadsheet: {e}")
            return False
    
    def add_source(self, record: RetrievalRecord, sourcepuller_name: str = "System") -> Dict[str, Any]:
        """
        Add a source to the spreadsheet
        
        Args:
            record: RetrievalRecord from retrieval system
            sourcepuller_name: Name of person/system pulling source
        
        Returns:
            Dictionary of spreadsheet row data
        """
        # Generate source number
        source_num = f"{self.next_source_number:03d}"
        self.next_source_number += 1
        
        # Generate short name
        short_name = self._generate_short_name(record.citation)
        
        # Determine status
        status = "Pulled" if record.final_status == "success" else "Missing"
        
        # Build row data
        row_data = {
            'Source #': source_num,
            'Footnote': record.footnote_number,
            'Short Name': short_name,
            'Full Citation': record.citation.raw_text,
            'Source Type': record.citation.type.name,
            'Status': status,
            'Sourcepuller': sourcepuller_name,
            'Date Pulled': datetime.now().strftime('%Y-%m-%d') if status == "Pulled" else "",
            'File Location': record.final_file_path if record.final_file_path else "",
            'ILL Request Date': "",
            'ILL Due Date': "",
            'Physical Location': "",
            'Redboxed': "No",
            'Consecutively Paginated': "",
            'Subsequent History': "",
            'Negative Treatment': "",
            'Notes': '\n'.join(record.notes),
            'Drive Link': self._generate_drive_link(record.final_file_path) if record.final_file_path else "",
            'Check': "✓" if status == "Pulled" else "✗"
        }
        
        # Add type-specific data
        if record.citation.type == SourceType.CASE:
            # Check for subsequent history and negative treatment
            if any('subsequent' in note.lower() for note in record.notes):
                row_data['Subsequent History'] = "Check needed"
            if any('negative' in note.lower() for note in record.notes):
                row_data['Negative Treatment'] = "Check needed"
        
        elif record.citation.type == SourceType.JOURNAL_ARTICLE:
            row_data['Consecutively Paginated'] = "Check TOC"
        
        elif record.citation.type == SourceType.BOOK:
            if not record.final_file_path:
                row_data['Status'] = "ILL Requested"
                row_data['ILL Request Date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Store locally
        self.local_data.append(row_data)
        
        # Update Google Sheets if connected
        if self.service and self.spreadsheet_id:
            self._update_sheet_row(row_data)
        
        return row_data
    
    def _generate_short_name(self, citation) -> str:
        """Generate short name following SLR conventions"""
        if citation.type == SourceType.CASE:
            if citation.party1:
                # Take first significant word from party1
                words = citation.party1.split()
                for word in words:
                    if len(word) > 3 and word not in ['Corp.', 'Inc.', 'Ltd.', 'LLC']:
                        return word
                return words[0] if words else "Case"
        
        elif citation.type == SourceType.JOURNAL_ARTICLE:
            if citation.author:
                # Last name of first author
                return citation.author.split()[-1] if citation.author else "Article"
        
        elif citation.type == SourceType.STATUTE_FEDERAL:
            if citation.title and citation.section:
                return f"{citation.title}USC{citation.section}"
        
        elif citation.type == SourceType.BOOK:
            if citation.author:
                return citation.author.split()[-1] if citation.author else "Book"
        
        # Fallback
        return citation.raw_text[:20].replace(' ', '_')
    
    def _generate_drive_link(self, file_path: Optional[str]) -> str:
        """Generate Google Drive link format"""
        if not file_path:
            return ""
        
        # This would need actual Drive API integration
        # For now, return a placeholder format
        filename = Path(file_path).name
        return f"=HYPERLINK(\"drive/path/{filename}\", \"📎\")"
    
    def _update_sheet_row(self, row_data: Dict[str, Any]):
        """Update a row in the Google Sheet"""
        if not self.service or not self.spreadsheet_id:
            return
        
        try:
            # Convert dict to list in column order
            values = [[row_data.get(col, "") for col in self.COLUMNS]]
            
            # Find next empty row (simplified - would need to query sheet)
            next_row = len(self.local_data) + 1  # +1 for header
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"Sourcepull!A{next_row}",
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            logger.info(f"Added row {next_row} to spreadsheet")
        except Exception as e:
            logger.error(f"Failed to update sheet: {e}")
    
    def _format_header_row(self, sheet_name: str):
        """Apply formatting to header row"""
        # This would use the batchUpdate API to format cells
        # Simplified for now
        pass
    
    def mark_source_redboxed(self, source_number: str, redboxed: bool = True):
        """Mark a source as redboxed"""
        for row in self.local_data:
            if row['Source #'] == source_number:
                row['Redboxed'] = "Yes" if redboxed else "No"
                if self.service:
                    self._update_sheet_row(row)
                break
    
    def update_physical_location(self, source_number: str, shelf: str):
        """Update physical location for a book"""
        for row in self.local_data:
            if row['Source #'] == source_number:
                row['Physical Location'] = shelf
                if self.service:
                    self._update_sheet_row(row)
                break
    
    def export_to_csv(self, filepath: str):
        """Export local data to CSV format"""
        import csv
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.COLUMNS)
            writer.writeheader()
            writer.writerows(self.local_data)
        
        logger.info(f"Exported {len(self.local_data)} rows to {filepath}")
    
    def export_to_json(self, filepath: str):
        """Export local data to JSON"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_sources': len(self.local_data),
            'columns': self.COLUMNS,
            'data': self.local_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported {len(self.local_data)} rows to {filepath}")
    
    def generate_sourcepull_checklist(self) -> str:
        """Generate a checklist for MEMs based on current status"""
        checklist = []
        checklist.append("SOURCEPULL CHECKLIST")
        checklist.append("="*50)
        checklist.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        checklist.append("")
        
        # Count by status
        status_counts = {}
        for row in self.local_data:
            status = row['Status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        checklist.append("STATUS SUMMARY:")
        for status, count in sorted(status_counts.items()):
            checklist.append(f"  {status}: {count}")
        checklist.append("")
        
        # List missing sources
        checklist.append("MISSING SOURCES:")
        missing = [row for row in self.local_data if row['Status'] == 'Missing']
        if missing:
            for row in missing:
                checklist.append(f"  FN{row['Footnote']}: {row['Short Name']}")
                checklist.append(f"    Type: {row['Source Type']}")
                checklist.append(f"    Citation: {row['Full Citation'][:60]}...")
        else:
            checklist.append("  None - all sources retrieved!")
        checklist.append("")
        
        # List ILL requests
        checklist.append("PENDING ILL REQUESTS:")
        ills = [row for row in self.local_data if 'ILL' in row['Status']]
        if ills:
            for row in ills:
                checklist.append(f"  FN{row['Footnote']}: {row['Short Name']}")
                checklist.append(f"    Requested: {row['ILL Request Date']}")
                if row['ILL Due Date']:
                    checklist.append(f"    Due: {row['ILL Due Date']}")
        else:
            checklist.append("  None")
        checklist.append("")
        
        # List sources needing redboxing
        checklist.append("SOURCES NEEDING REDBOXING:")
        need_redbox = [row for row in self.local_data 
                      if row['Status'] == 'Pulled' and row['Redboxed'] != 'Yes']
        if need_redbox:
            for row in need_redbox[:10]:  # First 10
                checklist.append(f"  {row['Source #']}: {row['Short Name']}")
        else:
            checklist.append("  None - all pulled sources redboxed!")
        
        return '\n'.join(checklist)


def test_spreadsheet():
    """Test the spreadsheet functionality"""
    # Create spreadsheet manager
    sheet = SourcepullSpreadsheet()
    
    # Create some test records
    from systematic_retrieval_framework import RetrievalEngine
    engine = RetrievalEngine()
    
    test_citations = [
        (1, "Alice Corp. Pty. Ltd. v. CLS Bank Int'l, 573 U.S. 208, 216 (2014)."),
        (2, "35 U.S.C. § 101 (2018)."),
        (3, "Mark A. Lemley, Software Patents, 2013 Wis. L. Rev. 905."),
    ]
    
    for fn, citation in test_citations:
        record = engine.process_footnote(fn, citation)
        record.final_status = "success" if fn != 3 else "failed"
        record.final_file_path = f"output/data/Sourcepull/SP-{fn:03d}-test.pdf" if fn != 3 else None
        
        row = sheet.add_source(record, "Test System")
        print(f"Added FN{fn}: {row['Short Name']} - {row['Status']}")
    
    # Export to files
    sheet.export_to_csv("sourcepull_test.csv")
    sheet.export_to_json("sourcepull_test.json")
    
    # Generate checklist
    print("\n" + sheet.generate_sourcepull_checklist())


if __name__ == "__main__":
    test_spreadsheet()