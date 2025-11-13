"""
Main pipeline orchestrator for the Source Pull machine.
"""
import sys
import logging
from pathlib import Path
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from doc_parser import DocParser
from citation_parser import Citation, CitationParser
from pullers import pull_website
from spreadsheet_parser import SpreadsheetParser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

class SpMachine:
    def __init__(self):
        self.source_list_path = Path(__file__).parent.parent / "78.6 Sanders Master Sheet.xlsx"
        self.doc_path = Path(__file__).parent.parent / "78 SLR V2 R2 F" / "References" / "Bersh_PreR2.docx"
        self.spreadsheet_parser = SpreadsheetParser(str(self.source_list_path))
        self.sources = self.spreadsheet_parser.get_sources(281, 327)
        self.doc_parser = DocParser(str(self.doc_path))
        self.citation_map = self.doc_parser.get_citation_map()

    def run(self):
        """Main pipeline execution."""
        print("--- Citation Map ---")
        print(self.citation_map)
        print("--- Sources ---")
        print(self.sources)

        for source in self.sources:
            logging.info(f"Processing source #{source['Source Number']}: {source['Citation']}")

            # Parse the citation
            parser = CitationParser(source["Citation"], source["Source Number"])
            parsed_citations = parser.parse()

            for parsed_citation in parsed_citations:
                print(f"  - Parsed citation: {parsed_citation}")

                source_type = self.detect_source_type(parsed_citation)
                if source_type == 'website':
                    pull_website(
                        url=parsed_citation.full_text,
                        output_dir=str(Path(__file__).parent / "data" / "output" / "pulled_sources"),
                        source_number=source['Source Number'],
                        short_name=source['Short Name']
                    )

    def detect_source_type(self, citation: Citation) -> str:
        """Detect the type of a source based on the citation."""
        if citation.full_text.startswith("http"):
            return "website"
        elif citation.type == "case":
            return "case"
        elif citation.type == "article":
            return "article"
        else:
            return "unknown"

if __name__ == "__main__":
    machine = SpMachine()
    machine.run()