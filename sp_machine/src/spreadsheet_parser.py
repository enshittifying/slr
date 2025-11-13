"""
Parse the master spreadsheet to get the list of sources to pull.
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict

class SpreadsheetParser:
    """Parse the master spreadsheet."""

    def __init__(self, spreadsheet_path: str):
        self.spreadsheet_path = spreadsheet_path
        self.df = pd.read_excel(spreadsheet_path, sheet_name="Sourcepull", header=28)
        self.df = self.df.iloc[:, [2, 3, 4]]
        self.df.columns = ["Source Number", "Short Name", "Citation"]
        self.df = self.df.dropna(subset=["Source Number"])
        self.df["Source Number"] = self.df["Source Number"].astype(int)

    def get_sources(self, start_num: int, end_num: int) -> List[Dict]:
        """Get the list of sources to pull."""
        sources = self.df[self.df["Source Number"].between(start_num, end_num)]
        return sources.to_dict('records')
