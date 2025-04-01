#!/usr/bin/env python3
"""
Test Suite for LBX Text Editor

This test suite validates the functionality of the lbx_text_edit.py tool by performing
various text manipulation operations on LBX label files.
"""

import os
import sys
import shutil
import unittest
import tempfile
import importlib.util
import xml.etree.ElementTree as ET
from lbx_utils.lbx_text_edit import LBXTextEditor, TextObject, StringItem, FontInfo, NAMESPACES
from typing import Optional, Any, Dict, List, TYPE_CHECKING

# To appease the linter, add stub type hints
if TYPE_CHECKING:
    # These imports are only used by the type checker, not at runtime
    from typing import Protocol

    class LBXTextEditor:
        """Type stub for LBXTextEditor class."""
        text_objects: List[Any]
        def load(self, file_path: str) -> None: ...
        def save(self, output_path: Optional[str] = None) -> None: ...

    class TextObject:
        """Type stub for TextObject class."""
        text: str
        string_items: List[Any]
        def edit_text(self, new_text: str) -> None: ...
        def find_replace(self, find_text: str, replace_text: str, case_sensitive: bool = True) -> int: ...
        def regex_find_replace(self, pattern: str, replace_text: str, case_sensitive: bool = True) -> int: ...
        def validate(self) -> bool: ...
        def add_string_item(self, text: str, font_name: str = "", font_weight: int = 0) -> Any: ...

    class StringItem:
        """Type stub for StringItem class."""
        char_len: int
        font_info: Any
        start_pos: int

    class FontInfo:
        """Type stub for FontInfo class."""
        name: str
        weight: int

    NAMESPACES: Dict[str, str]

# Dynamically import the lbx_text_edit module (handling the hyphen in the name)
# This approach is used because Python module names cannot contain hyphens
def import_module_from_path(module_name: str, file_path: str) -> Any:
    """Import a module from a file path, handling any import errors."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Could not find module at {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    if spec.loader is None:
        raise ImportError(f"Could not load module at {file_path}")

    spec.loader.exec_module(module)
    return module

# Import the module, assuming it's in the current directory
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Find the lbx_text_edit.py file in the current directory or parent directory
    script_path = os.path.join(current_dir, "lbx_text_edit.py")
    if not os.path.exists(script_path):
        # Try parent directory
        parent_dir = os.path.dirname(current_dir)
        script_path = os.path.join(parent_dir, "lbx_text_edit.py")

    lbx_text_edit = import_module_from_path("lbx_text_edit", script_path)

    # Import necessary classes and constants
    LBXTextEditor = lbx_text_edit.LBXTextEditor
    TextObject = lbx_text_edit.TextObject
    StringItem = lbx_text_edit.StringItem
    FontInfo = lbx_text_edit.FontInfo
    NAMESPACES = lbx_text_edit.NAMESPACES
except ImportError as e:
    print(f"Error importing lbx_text_edit.py: {e}")
    sys.exit(1)

# Path to the test sample
TEST_SAMPLE = "data/label_examples/30182.lbx"
TEMP_DIR = "test_output"


class LBXTextEditTests(unittest.TestCase):
    """Tests for the LBX Text Editor functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment."""
        # Create a temporary directory for test output
        if not os.path.exists(TEMP_DIR):
            os.makedirs(TEMP_DIR)

        # Verify the test sample exists
        if not os.path.exists(TEST_SAMPLE):
            raise FileNotFoundError(f"Test sample {TEST_SAMPLE} not found")

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests if needed."""
        # Comment this out to keep test outputs for inspection
        # if os.path.exists(TEMP_DIR):
        #     shutil.rmtree(TEMP_DIR)
        pass

    def setUp(self):
        """Set up each test."""
        # Create a fresh editor instance for each test
        self.editor = LBXTextEditor()

    def test_1_delete_first_string_item(self):
        """Test deleting the first string item."""
        print("\nTest 1: Deleting first string item...")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "test1_delete_first_item.lbx")

        # Extract and load the label.xml
        xml_path = self.editor.extract_from_lbx(TEST_SAMPLE)
        self.editor.load(xml_path)

        # Get the first text object
        text_obj = self.editor.get_text_object_by_index(0)
        original_text = text_obj.text
        original_items_count = len(text_obj.string_items)

        print(f"Original text: {repr(original_text)}")
        print(f"Original string items: {original_items_count}")

        # Delete the first string item
        text_obj.delete_string_item(0)

        # Verify the change
        self.assertEqual(len(text_obj.string_items), original_items_count - 1)
        print(f"New text: {repr(text_obj.text)}")
        print(f"New string items: {len(text_obj.string_items)}")

        # Save the result
        self.editor.update_lbx(TEST_SAMPLE, output_path)
        print(f"Saved result to: {output_path}")

        # Additional assertion
        self.assertTrue(os.path.exists(output_path))

    def test_2_merge_all_string_items(self):
        """Test merging all string items into one."""
        print("\nTest 2: Merging all string items...")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "test2_merge_all_items.lbx")

        # Extract and load the label.xml
        xml_path = self.editor.extract_from_lbx(TEST_SAMPLE)
        self.editor.load(xml_path)

        # Get the first text object
        text_obj = self.editor.get_text_object_by_index(0)
        original_text = text_obj.text
        original_items_count = len(text_obj.string_items)

        print(f"Original text: {repr(original_text)}")
        print(f"Original string items: {original_items_count}")

        # Merge all string items
        if len(text_obj.string_items) > 1:
            text_obj.merge_string_items(0, len(text_obj.string_items) - 1)

        # Verify the change
        self.assertEqual(len(text_obj.string_items), 1)
        print(f"New text: {repr(text_obj.text)}")
        print(f"New string items: {len(text_obj.string_items)}")

        # Save the result
        self.editor.update_lbx(TEST_SAMPLE, output_path)
        print(f"Saved result to: {output_path}")

        # Additional assertion
        self.assertTrue(os.path.exists(output_path))

    def test_3_remove_first_newline(self):
        """Test removing the first newline from a text object."""
        print("\nTest 3: Removing first newline...")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "test3_remove_first_newline.lbx")

        # Extract and load the label.xml
        xml_path = self.editor.extract_from_lbx(TEST_SAMPLE)
        self.editor.load(xml_path)

        # Get the first text object
        text_obj = self.editor.get_text_object_by_index(0)
        original_text = text_obj.text

        print(f"Original text: {repr(original_text)}")

        # Find the first newline and remove it
        if "\n" in text_obj.text:
            first_nl_pos = text_obj.text.find("\n")
            new_text = text_obj.text[:first_nl_pos] + text_obj.text[first_nl_pos+1:]
            text_obj.edit_text(new_text)

        # Verify the change
        self.assertNotEqual(original_text, text_obj.text)
        print(f"New text: {repr(text_obj.text)}")

        # Save the result
        self.editor.update_lbx(TEST_SAMPLE, output_path)
        print(f"Saved result to: {output_path}")

        # Additional assertion
        self.assertTrue(os.path.exists(output_path))

    def test_4_replace_all_newlines(self):
        """Test replacing all newlines in a text object."""
        print("\nTest 4: Replacing all newlines...")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "test4_replace_all_newlines.lbx")

        # Extract and load the label.xml
        xml_path = self.editor.extract_from_lbx(TEST_SAMPLE)
        self.editor.load(xml_path)

        # Get the first text object
        text_obj = self.editor.get_text_object_by_index(0)
        original_text = text_obj.text

        print(f"Original text: {repr(original_text)}")

        # Replace all newlines with spaces
        count = text_obj.find_replace("\n", " ")

        # Verify the change
        self.assertNotEqual(original_text, text_obj.text)
        print(f"New text: {repr(text_obj.text)}")
        print(f"Replaced {count} newlines")

        # Save the result
        self.editor.update_lbx(TEST_SAMPLE, output_path)
        print(f"Saved result to: {output_path}")

        # Additional assertion
        self.assertTrue(os.path.exists(output_path))

    def test_5_replace_x_with_multiplication(self):
        """Test replacing 'x' with the multiplication symbol."""
        print("\nTest 5: Replacing 'x' with multiplication symbol...")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "test5_replace_x_with_multiplication.lbx")

        # Extract and load the label.xml
        xml_path = self.editor.extract_from_lbx(TEST_SAMPLE)
        self.editor.load(xml_path)

        # Use regex to replace '4 x 4' with '4×4'
        count = self.editor.regex_find_replace_all(r"(\d+)\s*x\s*(\d+)", r"\1×\2")

        print(f"Replaced {count} occurrences")

        # Get the first text object to verify
        text_obj = self.editor.get_text_object_by_index(0)
        print(f"New text: {repr(text_obj.text)}")

        # Save the result
        self.editor.update_lbx(TEST_SAMPLE, output_path)
        print(f"Saved result to: {output_path}")

        # Additional assertion
        self.assertTrue(os.path.exists(output_path))

    def test_6_add_new_string_item_comic_sans(self):
        """Test adding a new string item with Comic Sans MS font."""
        print("\nTest 6: Adding new string item with Comic Sans MS...")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "test6_add_comic_sans.lbx")

        # Extract and load the label.xml
        xml_path = self.editor.extract_from_lbx(TEST_SAMPLE)
        self.editor.load(xml_path)

        # Get the first text object
        text_obj = self.editor.get_text_object_by_index(0)
        original_items_count = len(text_obj.string_items)

        print(f"Original text: {repr(text_obj.text)}")
        print(f"Original string items: {original_items_count}")

        # Add a new string item with Comic Sans MS
        new_item = text_obj.add_string_item(" (Fun!)", "Comic Sans MS", 400, "8pt")

        # Verify the change
        self.assertEqual(len(text_obj.string_items), original_items_count + 1)
        self.assertEqual(new_item.font_info.name, "Comic Sans MS")
        print(f"New text: {repr(text_obj.text)}")
        print(f"New string items: {len(text_obj.string_items)}")

        # Save the result
        self.editor.update_lbx(TEST_SAMPLE, output_path)
        print(f"Saved result to: {output_path}")

        # Additional assertion
        self.assertTrue(os.path.exists(output_path))

    def test_7_combined_operations(self):
        """Test multiple operations in sequence."""
        print("\nTest 7: Combined operations...")

        # Create output path
        output_path = os.path.join(TEMP_DIR, "test7_combined_operations.lbx")

        # Extract and load the label.xml
        xml_path = self.editor.extract_from_lbx(TEST_SAMPLE)
        self.editor.load(xml_path)

        # Get the first text object
        text_obj = self.editor.get_text_object_by_index(0)

        # 1. Replace 'x' with '×'
        text_obj.regex_find_replace(r"(\d+)\s*x\s*(\d+)", r"\1×\2")

        # 2. Add a bold string item
        text_obj.add_string_item("\nModified", "Arial", 700, "10pt")

        # 3. Split an existing string item if possible
        if len(text_obj.string_items) > 0 and text_obj.string_items[0].char_len > 3:
            text_obj.split_string_item(0, 3)

        # Verify the changes
        print(f"Final text: {repr(text_obj.text)}")
        print(f"Final string items: {len(text_obj.string_items)}")

        # Save the result
        self.editor.update_lbx(TEST_SAMPLE, output_path)
        print(f"Saved result to: {output_path}")

        # Additional assertion
        self.assertTrue(os.path.exists(output_path))


class TestLBXTextEditor(unittest.TestCase):
    """Test class for LBXTextEditor functionality."""

    def setUp(self):
        """Set up test environment with a sample XML structure."""
        # Create a simple XML structure
        self.xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<pt:document xmlns:pt="http://schemas.brother.info/ptouch/2007/lbx/main" xmlns:style="http://schemas.brother.info/ptouch/2007/lbx/style" xmlns:text="http://schemas.brother.info/ptouch/2007/lbx/text">
  <pt:body>
    <pt:objects>
      <text:text>
        <pt:data>Sample Text</pt:data>
        <text:stringItem charLen="11">
          <text:ptFontInfo>
            <text:logFont name="Arial" width="0" italic="false" weight="400" charSet="0" pitchAndFamily="34"/>
            <text:fontExt effect="NOEFFECT" underline="0" strikeout="0" size="8pt" orgSize="28.8pt" textColor="#000000" textPrintColorNumber="1"/>
          </text:ptFontInfo>
        </text:stringItem>
      </text:text>
      <text:text>
        <pt:data>Multiple Items</pt:data>
        <text:stringItem charLen="8">
          <text:ptFontInfo>
            <text:logFont name="Arial" width="0" italic="false" weight="400" charSet="0" pitchAndFamily="34"/>
            <text:fontExt effect="NOEFFECT" underline="0" strikeout="0" size="8pt" orgSize="28.8pt" textColor="#000000" textPrintColorNumber="1"/>
          </text:ptFontInfo>
        </text:stringItem>
        <text:stringItem charLen="6">
          <text:ptFontInfo>
            <text:logFont name="Arial" width="0" italic="true" weight="700" charSet="0" pitchAndFamily="34"/>
            <text:fontExt effect="NOEFFECT" underline="0" strikeout="0" size="10pt" orgSize="36pt" textColor="#FF0000" textPrintColorNumber="1"/>
          </text:ptFontInfo>
        </text:stringItem>
      </text:text>
    </pt:objects>
  </pt:body>
</pt:document>
"""
        # Create a temporary XML file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as f:
            f.write(self.xml_content.encode('utf-8'))
            self.temp_xml_file = f.name

        # Initialize the editor
        self.editor = LBXTextEditor()
        self.editor.load(self.temp_xml_file)

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_xml_file):
            os.unlink(self.temp_xml_file)

    def test_load_text_objects(self):
        """Test that text objects are loaded correctly."""
        self.assertEqual(len(self.editor.text_objects), 2)
        self.assertEqual(self.editor.text_objects[0].text, "Sample Text")
        self.assertEqual(self.editor.text_objects[1].text, "Multiple Items")

    def test_string_items_loaded(self):
        """Test that string items are loaded correctly."""
        self.assertEqual(len(self.editor.text_objects[0].string_items), 1)
        self.assertEqual(self.editor.text_objects[0].string_items[0].char_len, 11)

        self.assertEqual(len(self.editor.text_objects[1].string_items), 2)
        self.assertEqual(self.editor.text_objects[1].string_items[0].char_len, 8)
        self.assertEqual(self.editor.text_objects[1].string_items[1].char_len, 6)

    def test_edit_text_single_item(self):
        """Test editing text with a single string item."""
        text_obj = self.editor.text_objects[0]
        text_obj.edit_text("New Sample")

        # Verify text was updated
        self.assertEqual(text_obj.text, "New Sample")

        # Verify string item was updated
        self.assertEqual(len(text_obj.string_items), 1)
        self.assertEqual(text_obj.string_items[0].char_len, 10)

        # Verify validation passes
        self.assertTrue(text_obj.validate())

    def test_edit_text_multiple_items(self):
        """Test editing text with multiple string items."""
        text_obj = self.editor.text_objects[1]
        text_obj.edit_text("Longer Multiple Items Text")

        # Verify text was updated
        self.assertEqual(text_obj.text, "Longer Multiple Items Text")

        # Verify string items were updated proportionally
        self.assertEqual(len(text_obj.string_items), 2)

        # Calculate expected character lengths
        total_original = 8 + 6  # Original string item lengths
        total_new = len("Longer Multiple Items Text")
        scale_factor = total_new / total_original

        expected_first_len = round(8 * scale_factor)
        expected_second_len = total_new - expected_first_len

        self.assertEqual(text_obj.string_items[0].char_len, expected_first_len)
        self.assertEqual(text_obj.string_items[1].char_len, expected_second_len)

        # Verify total length is correct
        self.assertEqual(sum(item.char_len for item in text_obj.string_items), total_new)

        # Verify validation passes
        self.assertTrue(text_obj.validate())

    def test_find_replace(self):
        """Test find and replace functionality."""
        # Replace in first text object
        count = self.editor.text_objects[0].find_replace("Sample", "Modified")
        self.assertEqual(count, 1)
        self.assertEqual(self.editor.text_objects[0].text, "Modified Text")

        # Verify string item was updated
        self.assertEqual(self.editor.text_objects[0].string_items[0].char_len, 13)

        # Verify validation passes
        self.assertTrue(self.editor.text_objects[0].validate())

    def test_regex_find_replace(self):
        """Test regex-based find and replace."""
        # Replace using regex in second text object
        count = self.editor.text_objects[1].regex_find_replace(r"(\w+)\s(\w+)", r"\2 \1")
        self.assertEqual(count, 1)
        self.assertEqual(self.editor.text_objects[1].text, "Items Multiple")

        # Verify string items were updated
        self.assertEqual(sum(item.char_len for item in self.editor.text_objects[1].string_items), 14)

        # Verify validation passes
        self.assertTrue(self.editor.text_objects[1].validate())

    def test_save_and_reload(self):
        """Test saving and reloading the XML file."""
        # Modify text
        self.editor.text_objects[0].edit_text("Modified for save")

        # Save to a new file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as f:
            temp_save_file = f.name

        try:
            self.editor.save(temp_save_file)

            # Load the saved file
            new_editor = LBXTextEditor()
            new_editor.load(temp_save_file)

            # Verify the text was saved correctly
            self.assertEqual(len(new_editor.text_objects), 2)
            self.assertEqual(new_editor.text_objects[0].text, "Modified for save")

            # Verify string items were saved correctly
            self.assertEqual(len(new_editor.text_objects[0].string_items), 1)
            self.assertEqual(new_editor.text_objects[0].string_items[0].char_len, 17)

            # Parse the XML to check structure
            tree = ET.parse(temp_save_file)
            root = tree.getroot()

            # Check string items in the XML
            text_elems = root.findall('.//text:text', NAMESPACES)
            self.assertEqual(len(text_elems), 2)

            data_elem = text_elems[0].find('.//pt:data', NAMESPACES)
            self.assertIsNotNone(data_elem, "pt:data element not found")
            if data_elem is not None:  # Additional null check for linter
                data_text = data_elem.text
                self.assertEqual(data_text or "", "Modified for save")

            string_items = text_elems[0].findall('.//text:stringItem', NAMESPACES)
            self.assertEqual(len(string_items), 1)
            self.assertEqual(string_items[0].get('charLen'), '17')

        finally:
            # Clean up
            if os.path.exists(temp_save_file):
                os.unlink(temp_save_file)

    def test_validation(self):
        """Test validation of text objects."""
        # Valid case is already tested in other tests

        # Test invalid case - mismatched character lengths
        text_obj = self.editor.text_objects[0]
        text_obj.text = "Modified longer text"
        # Don't update string items, leaving char_len at 11

        # Validation should fail
        self.assertFalse(text_obj.validate())

        # Now fix it by calling edit_text
        text_obj.edit_text("Modified longer text")

        # Validation should now pass
        self.assertTrue(text_obj.validate())

    def test_empty_text(self):
        """Test handling of empty text."""
        text_obj = self.editor.text_objects[0]
        text_obj.edit_text("")

        # Verify text was updated
        self.assertEqual(text_obj.text, "")

        # Verify string item was updated
        self.assertEqual(len(text_obj.string_items), 1)
        self.assertEqual(text_obj.string_items[0].char_len, 0)

        # Verify validation passes
        self.assertTrue(text_obj.validate())

    def test_add_string_item(self):
        """Test adding a new string item."""
        text_obj = self.editor.text_objects[0]
        original_text = text_obj.text

        # Add a new string item with text
        text_obj.add_string_item(" - Added", font_name="Courier New", font_weight=700)

        # Verify text was updated
        self.assertEqual(text_obj.text, original_text + " - Added")

        # Verify string items
        self.assertEqual(len(text_obj.string_items), 2)
        self.assertEqual(text_obj.string_items[1].char_len, 8)  # " - Added" length
        self.assertEqual(text_obj.string_items[1].font_info.name, "Courier New")
        self.assertEqual(text_obj.string_items[1].font_info.weight, 700)

        # Verify validation passes
        self.assertTrue(text_obj.validate())


def run_tests():
    """Run the tests."""
    unittest.main(argv=['first-arg-is-ignored'], exit=False)


if __name__ == "__main__":
    run_tests()