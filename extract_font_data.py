#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility script to extract font data from P-touch Editor label XML files.
Extracts text content, font name, size, weight, and dimensions into a CSV file.
"""

import os
import csv
import xml.etree.ElementTree as ET
from typing import List, Dict

# Define XML namespaces
NAMESPACES = {
    'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
    'text': 'http://schemas.brother.info/ptouch/2007/lbx/text'
}

def extract_font_data(xml_path: str) -> List[Dict]:
    """Extract font data from the XML file."""
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    tree = ET.parse(xml_path)
    root = tree.getroot()

    font_data = []

    # Find all text objects
    text_elements = root.findall('.//text:text', NAMESPACES)

    for text_element in text_elements:
        # Get object style (dimensions)
        obj_style = text_element.find('.//pt:objectStyle', NAMESPACES)
        if obj_style is None:
            continue

        width_attr = obj_style.get('width')
        height_attr = obj_style.get('height')

        if width_attr is None or height_attr is None:
            continue

        width = float(width_attr.rstrip('pt'))
        height = float(height_attr.rstrip('pt'))

        # Get font info
        font_info = text_element.find('.//text:logFont', NAMESPACES)
        if font_info is None:
            continue

        font_name = font_info.get('name')
        weight = "bold" if font_info.get('weight') == "700" else "normal"
        italic = font_info.get('italic') == "true"

        # Get font size
        font_ext = text_element.find('.//text:fontExt', NAMESPACES)
        if font_ext is None:
            continue

        size_attr = font_ext.get('size')
        if size_attr is None:
            continue

        size = float(size_attr.rstrip('pt'))

        # Get text content
        data_element = text_element.find('.//pt:data', NAMESPACES)
        if data_element is None or data_element.text is None:
            continue

        text = data_element.text

        font_data.append({
            "text": text,
            "font_name": font_name,
            "size": size,
            "weight": weight,
            "italic": italic,
            "width": width,
            "height": height
        })

    return font_data

def write_csv(data: List[Dict], output_path: str):
    """Write font data to a CSV file."""
    fieldnames = ["text", "font_name", "size", "weight", "italic", "width", "height"]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    # Path to the XML file
    xml_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "label_examples",
        "multi-font-grid",
        "label.xml"
    )

    # Output CSV path
    output_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "label_examples",
        "multi-font-grid",
        "font_data.csv"
    )

    try:
        # Extract data
        font_data = extract_font_data(xml_path)

        # Write to CSV
        write_csv(font_data, output_path)

        print(f"Successfully extracted {len(font_data)} font entries")
        print(f"CSV file written to: {output_path}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())