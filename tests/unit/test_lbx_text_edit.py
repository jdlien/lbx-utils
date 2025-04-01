#!/usr/bin/env python3
"""
Test Suite for LBX Text Editor

This test suite validates the functionality of the lbx_text_edit.py tool by performing
various text manipulation operations on LBX label files.
"""

import os
import sys
import pytest
from pathlib import Path

from lbx_utils.lbx_text_edit import LBXTextEditor, TextObject, StringItem, FontInfo, NAMESPACES

# Path aliases used by tests in this module
TEST_SAMPLE = "data/label_examples/30182.lbx"
TEMP_DIR = "test_output"

# Test functions
@pytest.mark.unit
def test_delete_first_string_item(lbx_text_editor, test_sample, temp_dir):
    """Test deleting the first string item."""
    # Create output path
    output_path = os.path.join(temp_dir, "test1_delete_first_item.lbx")

    # Extract and load the label.xml
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Get the first text object
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_text = text_obj.text
    original_items_count = len(text_obj.string_items)

    print(f"Original text: {repr(original_text)}")
    print(f"Original string items: {original_items_count}")

    # Delete the first string item
    text_obj.delete_string_item(0)

    # Verify the change
    assert len(text_obj.string_items) == original_items_count - 1
    print(f"New text: {repr(text_obj.text)}")
    print(f"New string items: {len(text_obj.string_items)}")

    # Save the result
    lbx_text_editor.update_lbx(test_sample, output_path)
    print(f"Saved result to: {output_path}")

    # Additional assertion
    assert os.path.exists(output_path)

@pytest.mark.unit
def test_merge_all_string_items(lbx_text_editor, test_sample, temp_dir):
    """Test merging all string items into one."""
    # Create output path
    output_path = os.path.join(temp_dir, "test2_merge_all_items.lbx")

    # Extract and load the label.xml
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Get the first text object
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_text = text_obj.text
    original_items_count = len(text_obj.string_items)

    print(f"Original text: {repr(original_text)}")
    print(f"Original string items: {original_items_count}")

    # Merge all string items
    if len(text_obj.string_items) > 1:
        text_obj.merge_string_items(0, len(text_obj.string_items) - 1)

    # Verify the change
    assert len(text_obj.string_items) == 1
    print(f"New text: {repr(text_obj.text)}")
    print(f"New string items: {len(text_obj.string_items)}")

    # Save the result
    lbx_text_editor.update_lbx(test_sample, output_path)
    print(f"Saved result to: {output_path}")

    # Additional assertion
    assert os.path.exists(output_path)

@pytest.mark.unit
def test_remove_first_newline(lbx_text_editor, test_sample, temp_dir):
    """Test removing the first newline from a text object."""
    # Create output path
    output_path = os.path.join(temp_dir, "test3_remove_first_newline.lbx")

    # Extract and load the label.xml
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Get the first text object
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_text = text_obj.text

    print(f"Original text: {repr(original_text)}")

    # Find the first newline and remove it
    if "\n" in text_obj.text:
        first_nl_pos = text_obj.text.find("\n")
        new_text = text_obj.text[:first_nl_pos] + text_obj.text[first_nl_pos+1:]
        text_obj.edit_text(new_text)

    # Verify the change
    assert original_text != text_obj.text
    print(f"New text: {repr(text_obj.text)}")

    # Save the result
    lbx_text_editor.update_lbx(test_sample, output_path)
    print(f"Saved result to: {output_path}")

    # Additional assertion
    assert os.path.exists(output_path)

@pytest.mark.unit
def test_replace_all_newlines(lbx_text_editor, test_sample, temp_dir):
    """Test replacing all newlines in a text object."""
    # Create output path
    output_path = os.path.join(temp_dir, "test4_replace_all_newlines.lbx")

    # Extract and load the label.xml
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Get the first text object
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_text = text_obj.text

    print(f"Original text: {repr(original_text)}")

    # Replace all newlines with spaces
    count = text_obj.find_replace("\n", " ")

    # Verify the change
    assert original_text != text_obj.text
    print(f"New text: {repr(text_obj.text)}")
    print(f"Replaced {count} newlines")

    # Save the result
    lbx_text_editor.update_lbx(test_sample, output_path)
    print(f"Saved result to: {output_path}")

    # Additional assertion
    assert os.path.exists(output_path)

@pytest.mark.unit
def test_replace_x_with_multiplication(lbx_text_editor, test_sample, temp_dir):
    """Test replacing 'x' with the multiplication symbol."""
    # Create output path
    output_path = os.path.join(temp_dir, "test5_replace_x_with_multiplication.lbx")

    # Extract and load the label.xml
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Use regex to replace '4 x 4' with '4×4'
    count = lbx_text_editor.regex_find_replace_all(r"(\d+)\s*x\s*(\d+)", r"\1×\2")

    print(f"Replaced {count} occurrences")

    # Get the first text object to verify
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    print(f"New text: {repr(text_obj.text)}")

    # Save the result
    lbx_text_editor.update_lbx(test_sample, output_path)
    print(f"Saved result to: {output_path}")

    # Additional assertion
    assert os.path.exists(output_path)

@pytest.mark.unit
def test_add_new_string_item_comic_sans(lbx_text_editor, test_sample, temp_dir):
    """Test adding a new string item with Comic Sans MS font."""
    # Create output path
    output_path = os.path.join(temp_dir, "test6_add_comic_sans.lbx")

    # Extract and load the label.xml
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Get the first text object
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_items_count = len(text_obj.string_items)

    # Append a new string item with Comic Sans MS
    text_obj.add_string_item(" (Comic Sans)", font_name="Comic Sans MS", font_weight=700)

    # Verify the change
    assert len(text_obj.string_items) == original_items_count + 1

    # Check the font name in the last string item
    last_item = text_obj.string_items[-1]
    assert last_item.font_info.name == "Comic Sans MS"
    assert last_item.font_info.weight == 700

    print(f"New text: {repr(text_obj.text)}")
    print(f"New string items: {len(text_obj.string_items)}")

    # Save the result
    lbx_text_editor.update_lbx(test_sample, output_path)
    print(f"Saved result to: {output_path}")

    # Additional assertion
    assert os.path.exists(output_path)

@pytest.mark.unit
def test_combined_operations(lbx_text_editor, test_sample, temp_dir):
    """Test a combination of operations."""
    # Create output path
    output_path = os.path.join(temp_dir, "test7_combined_operations.lbx")

    # Extract and load the label.xml
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Get the first text object
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_text = text_obj.text

    print(f"Original text: {repr(original_text)}")

    # 1. First, replace 'x' with '×'
    text_obj.regex_find_replace(r"(\d+)\s*x\s*(\d+)", r"\1×\2")

    # 2. Then capitalize the first letter of each word
    words = text_obj.text.split(" ")
    capitalized_words = [word.capitalize() if word else word for word in words]
    text_obj.edit_text(" ".join(capitalized_words))

    # 3. Finally, add a prefix
    text_obj.edit_text("LEGO® " + text_obj.text)

    # Verify the change
    assert original_text != text_obj.text
    print(f"New text: {repr(text_obj.text)}")

    # Save the result
    lbx_text_editor.update_lbx(test_sample, output_path)
    print(f"Saved result to: {output_path}")

    # Additional assertion
    assert os.path.exists(output_path)

# More detailed tests for specific functionality
@pytest.mark.unit
def test_load_text_objects(lbx_text_editor, test_sample):
    """Test loading text objects from an LBX file."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)
    assert len(lbx_text_editor.text_objects) > 0

@pytest.mark.unit
def test_string_items_loaded(lbx_text_editor, test_sample):
    """Test that string items are loaded correctly."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    assert len(text_obj.string_items) > 0
    assert text_obj.string_items[0].char_len > 0

@pytest.mark.unit
def test_edit_text_single_item(lbx_text_editor, test_sample):
    """Test editing text with a single string item."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    text_obj = lbx_text_editor.get_text_object_by_index(0)

    # Merge all string items into one
    if len(text_obj.string_items) > 1:
        text_obj.merge_string_items(0, len(text_obj.string_items) - 1)

    # Edit the text
    new_text = "New Single Item Text"
    text_obj.edit_text(new_text)

    # Verify changes
    assert text_obj.text == new_text
    assert len(text_obj.string_items) == 1
    assert text_obj.string_items[0].char_len == len(new_text)

@pytest.mark.unit
def test_edit_text_multiple_items(lbx_text_editor, test_sample):
    """Test editing text with multiple string items."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    text_obj = lbx_text_editor.get_text_object_by_index(0)

    # Ensure we have at least 2 string items
    original_text = text_obj.text
    if len(text_obj.string_items) < 2:
        # Split the first string item
        split_pos = len(original_text) // 2
        text_obj.split_string_item(0, split_pos)

    # Now edit the text
    new_text = "This is a multi-part string that should be distributed across string items"
    text_obj.edit_text(new_text)

    # Verify changes
    assert text_obj.text == new_text
    assert len(text_obj.string_items) >= 2

    # Check that the sum of charLen attributes equals the total text length
    char_len_sum = sum(item.char_len for item in text_obj.string_items)
    assert char_len_sum == len(new_text)

@pytest.mark.unit
def test_find_replace(lbx_text_editor, test_sample):
    """Test find and replace functionality."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_text = text_obj.text

    # Replace something simple
    count = text_obj.find_replace("a", "X")

    if "a" in original_text:
        assert count > 0
        assert "X" in text_obj.text
    else:
        assert count == 0

@pytest.mark.unit
def test_regex_find_replace(lbx_text_editor, test_sample):
    """Test regex find and replace functionality."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    text_obj = lbx_text_editor.get_text_object_by_index(0)

    # Replace digits with X
    count = text_obj.regex_find_replace(r"\d+", "X")

    # If there were any digits in the text, they should be replaced
    if count > 0:
        assert "X" in text_obj.text

@pytest.mark.unit
def test_save_and_reload(lbx_text_editor, test_sample, temp_dir):
    """Test saving and reloading a file after edits."""
    # Extract the original file
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    # Get the first text object
    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_text = text_obj.text

    # Make an edit
    new_text = "CHANGED: " + original_text
    text_obj.edit_text(new_text)

    # Save to a new file
    output_path = os.path.join(temp_dir, "test_save_reload.lbx")
    lbx_text_editor.update_lbx(test_sample, output_path)

    # Create a new editor instance
    new_editor = LBXTextEditor()

    # Load the saved file
    xml_path = new_editor.extract_from_lbx(output_path)
    new_editor.load(xml_path)

    # Get the text object from the reloaded file
    reloaded_text_obj = new_editor.get_text_object_by_index(0)

    # Verify the text was preserved
    assert reloaded_text_obj.text == new_text

    # Verify string items were preserved
    assert len(reloaded_text_obj.string_items) == len(text_obj.string_items)

    # Verify charLen attributes are correct
    char_len_sum = sum(item.char_len for item in reloaded_text_obj.string_items)
    assert char_len_sum == len(new_text)

@pytest.mark.unit
def test_validation(lbx_text_editor, test_sample):
    """Test text object validation."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    text_obj = lbx_text_editor.get_text_object_by_index(0)

    # Should be valid initially
    assert text_obj.validate()

    # Make invalid by manually modifying a charLen attribute
    if text_obj.string_items:
        original_char_len = text_obj.string_items[0].char_len
        text_obj.string_items[0].char_len += 5  # Make it invalid

        # Should be invalid now
        assert not text_obj.validate()

        # Fix it
        text_obj.string_items[0].char_len = original_char_len
        assert text_obj.validate()

@pytest.mark.unit
def test_empty_text(lbx_text_editor, test_sample):
    """Test handling empty text."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    text_obj = lbx_text_editor.get_text_object_by_index(0)

    # Set text to empty string
    text_obj.edit_text("")

    # Should still be valid
    assert text_obj.validate()

    # Should have at least one string item with charLen=0
    assert len(text_obj.string_items) > 0
    assert text_obj.string_items[0].char_len == 0

    # Add text back
    text_obj.edit_text("New text after empty")
    assert text_obj.validate()

@pytest.mark.unit
def test_add_string_item(lbx_text_editor, test_sample):
    """Test adding a string item."""
    xml_path = lbx_text_editor.extract_from_lbx(test_sample)
    lbx_text_editor.load(xml_path)

    text_obj = lbx_text_editor.get_text_object_by_index(0)
    original_count = len(text_obj.string_items)

    # Add a string item
    text_obj.add_string_item(" - Added Text", font_name="Arial", font_weight=700)

    # Verify it was added
    assert len(text_obj.string_items) == original_count + 1

    # Verify the new item has the correct font properties
    added_item = text_obj.string_items[-1]
    assert added_item.font_info.name == "Arial"
    assert added_item.font_info.weight == 700
    assert added_item.char_len == len(" - Added Text")