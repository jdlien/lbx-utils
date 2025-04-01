#!/usr/bin/env python3
"""
Integration tests for creating LBX files.

These tests validate that LBX files can be created correctly with various settings.
"""

import os
import sys
import pytest
from pathlib import Path
import zipfile

# Import the functionality from create_test_lbx.py
from tests.integration.create_test_lbx import create_test_lbx
from lbx_utils import LBXTextEditor, TextObject, StringItem, FontInfo, NAMESPACES, LabelConfig, LBXCreator

@pytest.mark.integration
def test_create_basic_lbx(temp_dir, create_test_lbx_file):
    """Test creating a basic LBX file with dimension text."""
    # Create a test file
    output_path = os.path.join(temp_dir, "basic_dimension.lbx")
    lbx_path = create_test_lbx_file(output_path)

    # Verify the file exists
    assert os.path.exists(lbx_path)

    # Verify it's a valid zip file
    with zipfile.ZipFile(lbx_path, 'r') as zip_ref:
        assert 'label.xml' in zip_ref.namelist()

        # Extract and check the XML content
        with zip_ref.open('label.xml') as xml_file:
            xml_content = xml_file.read().decode('utf-8')
            assert 'Brick' in xml_content
            assert 'Arial' in xml_content

@pytest.mark.integration
def test_create_and_modify_label(temp_dir):
    """Test creating a label and then modifying it with LBXTextEditor."""
    # Create the test file using create_test_lbx
    label_path = os.path.join(temp_dir, "test_create_modify.lbx")
    create_test_lbx(label_path)

    # Now modify it with LBXTextEditor
    editor = LBXTextEditor()
    xml_path = editor.extract_from_lbx(label_path)
    editor.load(xml_path)

    # Verify text objects were loaded
    assert len(editor.get_text_objects()) > 0
    text_obj = editor.get_text_object_by_index(0)

    # Make a simple edit
    text_obj.edit_text("Modified 4×4 Brick")

    # Save to a new file
    modified_path = os.path.join(temp_dir, "modified_label.lbx")
    editor.update_lbx(label_path, modified_path)

    # Verify the modified file exists
    assert os.path.exists(modified_path)

    # Open the modified file to verify changes
    new_editor = LBXTextEditor()
    xml_path = new_editor.extract_from_lbx(modified_path)
    new_editor.load(xml_path)

    # Verify the text was changed
    modified_text_obj = new_editor.get_text_object_by_index(0)
    assert "Modified" in modified_text_obj.text
    assert "×" in modified_text_obj.text  # Unicode multiplication symbol

@pytest.mark.integration
def test_create_with_label_config(temp_dir):
    """Test using LabelConfig to create a label structure."""
    # Create a simple LabelConfig for testing
    config = LabelConfig(
        size_mm=24,
        auto_length=True
    )

    # Create an output path
    output_path = os.path.join(temp_dir, "config_label.lbx")

    # Initialize LBXCreator with the config
    creator = LBXCreator(config)

    # Verify creator was initialized
    assert creator is not None

    # We can't fully test the creation without mock objects for the XML structure
    # but we can at least check the creator was initialized with the config
    assert creator.config.size_mm == 24
    assert creator.config.auto_length is True