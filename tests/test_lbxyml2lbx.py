#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for lbxyml2lbx.py

This script tests the conversion of LBX YAML files to LBX format.
"""

import os
import sys
import zipfile
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.lbx_utils.lbxyml2lbx import YamlParser, LbxGenerator

# Test output directory
TEST_OUTPUT_DIR = 'test_output/lbxyml2lbx'
os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

# Sample files directory
SAMPLE_FILES_DIR = 'data/lbx_yml_examples'

# Create a test image
TEST_IMAGE_DIR = 'tests'
TEST_IMAGE_PATH = os.path.join(TEST_IMAGE_DIR, 'test_image.png')

def create_test_image():
    """Create a simple test image for testing."""
    try:
        from PIL import Image, ImageDraw

        # Create a small test image
        img = Image.new('RGB', (100, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([(20, 20), (80, 80)], outline=(0, 0, 0), fill=(200, 200, 200))

        # Save the image
        img.save(TEST_IMAGE_PATH)
        print(f"Created test image at {TEST_IMAGE_PATH}")
    except ImportError:
        print("PIL not available, skipping test image creation")

@pytest.fixture(scope="session")
def setup_test_environment():
    """Set up the test environment."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    # Create a test image if it doesn't exist
    if not os.path.exists(TEST_IMAGE_PATH):
        create_test_image()

    yield

    # Clean up can be added here if needed
    # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)

def _test_blank_label_size(size_str, size_num):
    """Helper method to test blank labels of various sizes."""
    input_file = os.path.join(SAMPLE_FILES_DIR, f'blank_{size_str}.lbx.yml')
    output_file = os.path.join(TEST_OUTPUT_DIR, f'blank_{size_str}.lbx')
    unzip_dir = os.path.join(TEST_OUTPUT_DIR, f'blank_{size_str}')

    # Parse the YAML file
    parser = YamlParser(input_file)
    config = parser.parse()

    # Verify size is correctly parsed from YAML
    assert config.size == size_str, f"Size should be {size_str}"

    # Generate the LBX file
    generator = LbxGenerator(config)
    generator.generate_lbx(output_file)

    # Unzip the output file for inspection
    os.makedirs(unzip_dir, exist_ok=True)
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)

    # Set expected format codes for each size
    format_codes = {
        "3.5": "263",  # 3.5mm is code 263
        "6": "257",    # 6mm is code 257
        "9": "258",    # 9mm is code 258
        "12": "259",   # 12mm is code 259
        "18": "260",   # 18mm is code 260
        "24": "261"    # 24mm is code 261
    }

    expected_format = format_codes.get(size_num)

    # Check the format code in the XML file
    if expected_format:
        with open(os.path.join(unzip_dir, 'label.xml'), 'r', encoding='utf-8') as f:
            label_xml = f.read()
            assert f'format="{expected_format}"' in label_xml, f"Label size format code not correct for {size_str}"

@pytest.mark.unit
def test_blank_label_3_5mm(setup_test_environment):
    """Test the conversion of a 3.5mm blank label."""
    _test_blank_label_size("3.5mm", "3.5")

@pytest.mark.unit
def test_blank_label_6mm(setup_test_environment):
    """Test the conversion of a 6mm blank label."""
    _test_blank_label_size("6mm", "6")

@pytest.mark.unit
def test_blank_label_9mm(setup_test_environment):
    """Test the conversion of a 9mm blank label."""
    _test_blank_label_size("9mm", "9")

@pytest.mark.unit
def test_blank_label_12mm(setup_test_environment):
    """Test the conversion of a 12mm blank label."""
    _test_blank_label_size("12mm", "12")

@pytest.mark.unit
def test_blank_label_18mm(setup_test_environment):
    """Test the conversion of a 18mm blank label."""
    _test_blank_label_size("18mm", "18")

@pytest.mark.unit
def test_blank_label_24mm(setup_test_environment):
    """Test the conversion of a 24mm blank label."""
    _test_blank_label_size("24mm", "24")

@pytest.mark.unit
def test_basic_text(setup_test_environment):
    """Test the conversion of a label with a single text object."""
    input_file = os.path.join(SAMPLE_FILES_DIR, 'basic_text.lbx.yml')
    output_file = os.path.join(TEST_OUTPUT_DIR, 'basic_text.lbx')
    unzip_dir = os.path.join(TEST_OUTPUT_DIR, 'basic_text')

    # Parse the YAML file
    parser = YamlParser(input_file)
    config = parser.parse()

    # Verify size and width are correctly parsed from YAML
    assert config.size == "24mm", "Size should be 24mm"
    assert config.width == "auto", "Width should be 'auto'"

    # Generate the LBX file
    generator = LbxGenerator(config)
    generator.generate_lbx(output_file)

    # Verify the output file exists
    assert os.path.exists(output_file), f"Output file {output_file} not created"

    # Unzip the output file for inspection
    os.makedirs(unzip_dir, exist_ok=True)
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)

    # Verify the unzipped contents
    assert os.path.exists(os.path.join(unzip_dir, 'label.xml')), "label.xml not found in output"
    assert os.path.exists(os.path.join(unzip_dir, 'prop.xml')), "prop.xml not found in output"

    # Check that the label.xml contains a text element with "Hello World"
    with open(os.path.join(unzip_dir, 'label.xml'), 'r', encoding='utf-8') as f:
        label_xml = f.read()
        assert "Hello World" in label_xml, "Text content not found in label.xml"

        # Verify bold formatting is applied
        assert 'weight="700"' in label_xml, "Bold formatting not applied correctly"

        # Verify centering
        assert 'horizontalAlignment="CENTER"' in label_xml, "Text alignment not set to center"

        # Check for the correct size format code (261 = 24mm)
        assert 'format="261"' in label_xml, "Label size format code not correct for 24mm"

@pytest.mark.unit
def test_formatted_text(setup_test_environment):
    """Test the conversion of a label with formatted text objects."""
    input_file = os.path.join(SAMPLE_FILES_DIR, 'formatted_text.lbx.yml')
    output_file = os.path.join(TEST_OUTPUT_DIR, 'formatted_text.lbx')
    unzip_dir = os.path.join(TEST_OUTPUT_DIR, 'formatted_text')

    # Parse the YAML file
    parser = YamlParser(input_file)
    config = parser.parse()

    # Generate the LBX file
    generator = LbxGenerator(config)
    generator.generate_lbx(output_file)

    # Verify the output file exists
    assert os.path.exists(output_file), f"Output file {output_file} not created"

    # Unzip the output file for inspection
    os.makedirs(unzip_dir, exist_ok=True)
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)

    # Verify the unzipped contents
    assert os.path.exists(os.path.join(unzip_dir, 'label.xml')), "label.xml not found in output"
    assert os.path.exists(os.path.join(unzip_dir, 'prop.xml')), "prop.xml not found in output"

    # Check that the label.xml contains all the text elements
    with open(os.path.join(unzip_dir, 'label.xml'), 'r', encoding='utf-8') as f:
        label_xml = f.read()
        assert "Bold Text" in label_xml, "Bold text content not found in label.xml"
        assert "Italic Text" in label_xml, "Italic text content not found in label.xml"
        assert "Underlined Text" in label_xml, "Underlined text content not found in label.xml"

        # Check for formatting attributes
        assert 'weight="700"' in label_xml, "Bold formatting not found in label.xml"
        assert 'italic="true"' in label_xml, "Italic formatting not found in label.xml"
        assert 'underline="1"' in label_xml, "Underline formatting not found in label.xml"

@pytest.mark.unit
def test_image_label(setup_test_environment):
    """Test the conversion of a label with an image."""
    input_file = os.path.join(SAMPLE_FILES_DIR, 'image_label.lbx.yml')
    output_file = os.path.join(TEST_OUTPUT_DIR, 'image_label.lbx')
    unzip_dir = os.path.join(TEST_OUTPUT_DIR, 'image_label')

    # Parse the YAML file
    parser = YamlParser(input_file)
    config = parser.parse()

    # Generate the LBX file
    generator = LbxGenerator(config)
    generator.generate_lbx(output_file)

    # Verify the output file exists
    assert os.path.exists(output_file), f"Output file {output_file} not created"

    # Unzip the output file for inspection
    os.makedirs(unzip_dir, exist_ok=True)
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)

    # Verify the unzipped contents
    assert os.path.exists(os.path.join(unzip_dir, 'label.xml')), "label.xml not found in output"
    assert os.path.exists(os.path.join(unzip_dir, 'prop.xml')), "prop.xml not found in output"

    # Check that the label.xml contains an image element
    with open(os.path.join(unzip_dir, 'label.xml'), 'r', encoding='utf-8') as f:
        label_xml = f.read()
        assert "image:image" in label_xml, "Image element not found in label.xml"
        assert "test_image.png" in label_xml, "Image source not found in label.xml"

@pytest.mark.unit
def test_configured_size_and_width(setup_test_environment):
    """Test that specified size and width are correctly applied."""
    # Create a temporary YAML file with specific size and width
    test_content = """
    # Fixed width label
    size: 12mm
    width: 90mm
    orientation: landscape

    objects:
      - type: text
        content: "Fixed Width Text"
        x: 10
        y: 12
        font: Helsinki
        size: 14
        bold: true
        align: center
    """
    temp_yml_path = os.path.join(SAMPLE_FILES_DIR, 'fixed_width_test.lbx.yml')
    with open(temp_yml_path, 'w', encoding='utf-8') as f:
        f.write(test_content)

    output_file = os.path.join(TEST_OUTPUT_DIR, 'fixed_width.lbx')
    unzip_dir = os.path.join(TEST_OUTPUT_DIR, 'fixed_width')

    # Parse the YAML file
    parser = YamlParser(temp_yml_path)
    config = parser.parse()

    # Verify size and width are correctly parsed from YAML
    assert config.size == "12mm", "Size should be 12mm"
    assert config.width == "90mm", "Width should be '90mm'"

    # Generate the LBX file
    generator = LbxGenerator(config)
    generator.generate_lbx(output_file)

    # Unzip the output file for inspection
    os.makedirs(unzip_dir, exist_ok=True)
    with zipfile.ZipFile(output_file, 'r') as zip_ref:
        zip_ref.extractall(unzip_dir)

    # Check the label.xml file for correct size and width settings
    with open(os.path.join(unzip_dir, 'label.xml'), 'r', encoding='utf-8') as f:
        label_xml = f.read()

        # Check for the correct size format code (259 = 12mm)
        assert 'format="259"' in label_xml, "Label size format code not correct for 12mm"

        # Check that autoLength is set to false
        assert 'autoLength="false"' in label_xml, "autoLength should be false for fixed width"

        # Check for bold formatting
        assert 'weight="700"' in label_xml, "Bold formatting not applied correctly"

        # Check for width - converted from 90mm to points (approx 254.7pt)
        # The value might have decimals, so we need to check more flexibly
        assert 'height="254.7' in label_xml, "Label width not set correctly"

        # Also check that the background width is set to the same value
        assert 'width="254.7' in label_xml, "Background width not set correctly"