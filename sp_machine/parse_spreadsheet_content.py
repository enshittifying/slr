import csv
import re

with open("/Users/ben/app/slrapp/sp_machine/spreadsheet_content.txt", "r") as f_in, open("/Users/ben/app/slrapp/sp_machine/data/input/source_list.csv", "w", newline="") as f_out:
    writer = csv.writer(f_out)
    writer.writerow(["Source Number", "Short Name", "Citation"])

    for line in f_in:
        # Use a regular expression to find the source number
        match = re.search(r'Row (\d+):', line)
        if match:
            row_num = int(match.group(1))
            if 281 <= row_num <= 327:
                # This is a very brittle way to parse this data, but it's the only way
                # without a properly formatted spreadsheet.
                parts = line.split("'")
                if len(parts) > 7:
                    source_num = row_num
                    short_name = parts[3]
                    citation = parts[7]
                    writer.writerow([source_num, short_name, citation])