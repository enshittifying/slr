from openpyxl import load_workbook
import pandas as pd
from pathlib import Path

xls = pd.ExcelFile(Path(__file__).parent.parent / "78.6 Sanders Master Sheet.xlsx")
print(xls.sheet_names)