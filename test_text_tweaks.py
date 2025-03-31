#!/usr/bin/env python3
"""
Unit test for text tweaks functionality in the LBX utilities.
This tests whether the text replacement is working correctly in both
direct XML modification and when applied through the LBX file workflow.
"""

import os
import tempfile
import zipfile
import shutil
import re
from lxml import etree
from lbx_text_edit import LBXTextEditor

# Create a simple test XML with a dimension notation
TEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<pt:document xmlns:pt="http://schemas.brother.info/ptouch/2007/lbx/main"
             xmlns:text="http://schemas.brother.info/ptouch/2007/lbx/text"
             xmlns:style="http://schemas.brother.info/ptouch/2007/lbx/style">
    <text:text>
        <pt:objectStyle x="10pt" y="20pt" width="100pt" height="30pt" />
        <pt:data>4 x 4 Brick</pt:data>
        <text:stringItem charLen="10">
            <text:ptFontInfo>
                <text:logFont name="Arial" width="0" italic="false" weight="400" charSet="0" pitchAndFamily="34" />
                <text:fontExt effect="NOEFFECT" underline="0" strikeout="0" size="8pt" orgSize="28.8pt"
                              textColor="#000000" textPrintColorNumber="1" />
            </text:ptFontInfo>
        </text:stringItem>
    </text:text>
</pt:document>
"""

def create_test_xml(output_path):
    """Create a test XML file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(TEST_XML)
    print(f"Created test XML at {output_path}")

def create_test_lbx(xml_path, lbx_path):
    """Create a test LBX file from XML"""
    with zipfile.ZipFile(lbx_path, 'w') as zipf:
        zipf.write(xml_path, arcname='label.xml')
    print(f"Created test LBX at {lbx_path}")

def test_direct_editor():
    """Test the LBXTextEditor directly on an XML file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the test XML file
        xml_path = os.path.join(temp_dir, 'label.xml')
        create_test_xml(xml_path)

        # Print the original content
        with open(xml_path, 'r', encoding='utf-8') as f:
            print("Original XML content:")
            print(f.read())

        # Use the LBXTextEditor to modify the XML
        editor = LBXTextEditor()
        editor.load(xml_path)

        # Apply dimension notation replacement
        replacements = editor.regex_find_replace_all(r'(\d+)\s*[xX]\s*(\d+)', r'\1×\2', case_sensitive=False)
        print(f"Made {replacements} replacements")

        # Save the changes
        editor.save(xml_path)

        # Print the modified content
        with open(xml_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
            print("\nModified XML content:")
            print(modified_content)

        # Check if the replacement was successful
        if "4×4" in modified_content:
            print("\nSUCCESS: Text replacement was applied correctly")
        else:
            print("\nFAILED: Text was not replaced as expected")

def test_lbx_workflow():
    """Test the text tweaking in the full LBX workflow using change-lbx.py"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the test XML file
        xml_path = os.path.join(temp_dir, 'label.xml')
        create_test_xml(xml_path)

        # Create a test LBX file
        lbx_path = os.path.join(temp_dir, 'test.lbx')
        create_test_lbx(xml_path, lbx_path)

        # Extract the LBX for testing
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(lbx_path, 'r') as zipf:
            zipf.extractall(extract_dir)

        # Import the tweak_text function from change-lbx.py
        from change_lbx import tweak_text, config

        # Get the label.xml path in the extracted directory
        extracted_xml_path = os.path.join(extract_dir, 'label.xml')

        # Parse the XML for tweaking
        namespaces = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
            'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
        }

        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(extracted_xml_path, parser)
        root = tree.getroot()

        # Print the original content
        with open(extracted_xml_path, 'r', encoding='utf-8') as f:
            print("\nOriginal LBX XML content:")
            print(f.read())

        # Apply text tweaks
        text_options = {
            'convert_dimension_notation': True,
            'custom_replacements': [],
            'regex_replacements': [],
            'ignore_case': False
        }

        tweak_text(root, extracted_xml_path, text_options)

        # Print the modified content
        with open(extracted_xml_path, 'r', encoding='utf-8') as f:
            modified_content = f.read()
            print("\nModified LBX XML content:")
            print(modified_content)

        # Check if the replacement was successful
        if "4×4" in modified_content:
            print("\nSUCCESS: Text replacement was applied correctly in LBX workflow")
        else:
            print("\nFAILED: Text was not replaced as expected in LBX workflow")

if __name__ == "__main__":
    print("Testing direct LBXTextEditor functionality:")
    print("=" * 50)
    test_direct_editor()

    print("\n\nTesting LBX workflow with tweak_text:")
    print("=" * 50)
    try:
        test_lbx_workflow()
    except ImportError as e:
        print(f"Error importing from change-lbx.py: {e}")
        print("Try renaming the file to change_lbx.py for proper module importing")