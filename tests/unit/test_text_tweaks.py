#!/usr/bin/env python3
"""
Test text tweaking functions for LBX files.

This test focuses on the text replacement and tweaking functionality.
"""

import os
import tempfile
import zipfile
from lxml import etree
from lbx_utils.lbx_text_edit import LBXTextEditor

# Add the parent directory to path to resolve imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from lbx_utils.lbx_change import tweak_text
    LXML_AVAILABLE = True
except ImportError as e:
    print(f"Error importing from lbx_change.py: {e}")
    print("Try renaming the file to lbx_change.py for proper module importing")
    LXML_AVAILABLE = False

# Create a simple test XML with a dimension notation
TEST_XML = """<?xml version="1.0" encoding="UTF-8"?>
<pt:document xmlns:pt="http://schemas.brother.info/ptouch/2007/lbx/main"
             xmlns:text="http://schemas.brother.info/ptouch/2007/lbx/text">
    <text:text>
        <pt:data>4 x 4 Brick</pt:data>
    </text:text>
</pt:document>
"""

def create_test_xml(path):
    """Create a test XML file with dimension notation."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(TEST_XML)

def create_test_lbx(xml_path, lbx_path):
    """Create a test LBX file from an XML file."""
    with zipfile.ZipFile(lbx_path, "w") as zipf:
        zipf.write(xml_path, arcname="label.xml")

def test_direct_editor():
    """Test direct use of LBXTextEditor for text replacement."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the test XML file
        xml_path = os.path.join(temp_dir, 'label.xml')
        create_test_xml(xml_path)

        # Use LBXTextEditor directly
        editor = LBXTextEditor()
        editor.load(xml_path)

        print("\nOriginal text content:")
        text_obj = editor.get_text_object_by_index(0)
        original_text = text_obj.text
        print(original_text)

        # Replace "x" with "×" (multiplication sign)
        replacements = editor.regex_find_replace_all(r'(\d+)\s*x\s*(\d+)', r'\1×\2')
        editor.save(xml_path)

        # Reload and check content
        editor.load(xml_path)
        text_obj = editor.get_text_object_by_index(0)
        modified_text = text_obj.text
        print("\nModified text content:")
        print(modified_text)

        if "4×4" in modified_text:
            print("\nSUCCESS: Text replacement was applied correctly")
        else:
            print("\nFAILED: Text was not replaced as expected")

def test_tweak_text_with_lbx_workflow():
    """Test the text tweaking in the full LBX workflow using lbx_change.py"""
    # Skip test if lxml or tweak_text not available
    if not LXML_AVAILABLE:
        print("Skipping test_tweak_text_with_lbx_workflow - required modules not available")
        return

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
    test_tweak_text_with_lbx_workflow()