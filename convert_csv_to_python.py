#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility script to convert CSV font data into Python dictionary format for PTOUCH_REFERENCE_DATA.
"""

import csv
import os
from typing import List, Dict

def read_csv(csv_path: str) -> List[Dict]:
    """Read font data from CSV file."""
    data = []
    with open(csv_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Convert string values to appropriate types
            row['size'] = float(row['size'])
            row['width'] = float(row['width'])
            row['height'] = float(row['height'])
            row['italic'] = row['italic'].lower() == 'true'
            data.append(row)
    return data

def format_python_dict(data: List[Dict]) -> str:
    """Format the data as a Python dictionary string."""
    lines = []
    for item in data:
        lines.append("    {")
        lines.append(f'        "text": "{item["text"]}",')
        lines.append(f'        "font_name": "{item["font_name"]}",')
        lines.append(f'        "size": {item["size"]},')
        lines.append(f'        "weight": "{item["weight"]}",')
        lines.append(f'        "italic": {str(item["italic"])},')
        lines.append(f'        "width": {item["width"]},')
        lines.append(f'        "height": {item["height"]}')
        lines.append("    },")
    return "\n".join(lines)

def main():
    # Path to the CSV file
    csv_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "label_examples",
        "multi-font-grid",
        "font_data.csv"
    )

    try:
        # Read CSV data
        data = read_csv(csv_path)

        # Format as Python dictionary
        python_dict = format_python_dict(data)

        print("Copy and paste the following into PTOUCH_REFERENCE_DATA in test_text_dimensions.py:")
        print("\nPTOUCH_REFERENCE_DATA = [")
        print(python_dict)
        print("]")

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())