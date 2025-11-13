from xml.etree import ElementTree as ET
from pathlib import Path
import csv
import zipfile

# Path to the master spreadsheet
spreadsheet_path = Path(__file__).parent.parent / "78.6 Sanders Master Sheet.xlsx"

# Unzip the .xlsx file to access the raw XML
with zipfile.ZipFile(spreadsheet_path, 'r') as z:
    # Find the right sheet file (e.g., 'sheet1.xml', 'sheet2.xml', etc.)
    # This is a bit of a hack, we're assuming the sheet we want is the last one
    # in the list of worksheets.
    sheet_files = [f for f in z.namelist() if f.startswith('xl/worksheets/sheet')]
    sheet_to_read = sorted(sheet_files)[-1]

    with z.open(sheet_to_read) as f:
        tree = ET.parse(f)
        root = tree.getroot()

# Namespace for spreadsheet XML
ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

# Find all rows
rows = root.findall('.//main:row', ns)

with open(Path(__file__).parent / "data" / "input" / "source_list.csv", 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["Source Number", "Short Name", "Citation"])

    for row in rows:
        cells = row.findall('main:c', ns)
        if len(cells) > 4:
            # Source number is in column C (index 2)
            source_num_cell = cells[2]
            # Short name is in column D (index 3)
            short_name_cell = cells[3]
            # Citation is in column E (index 4)
            citation_cell = cells[4]

            # The actual value is in a 'v' child element
            source_num_elem = source_num_cell.find('main:v', ns)
            short_name_elem = short_name_cell.find('main:v', ns)
            citation_elem = citation_cell.find('main:v', ns)

            if source_num_elem is not None and source_num_elem.text.isdigit():
                source_num = int(source_num_elem.text)
                if 281 <= source_num <= 327:
                    short_name = short_name_elem.text if short_name_elem is not None else ""
                    citation = citation_elem.text if citation_elem is not None else ""
                    writer.writerow([source_num, short_name, citation])
