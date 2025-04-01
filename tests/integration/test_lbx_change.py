#!/usr/bin/env python3
"""
Integration tests for change_lbx.py

These tests verify the functionality of the LBX file modification utility
using actual LBX files and checking the results.
"""

import os
import pytest
import tempfile
import zipfile
import shutil
import lxml.etree as ET
from pathlib import Path
import sys
import re

# Add the parent directory to path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the function under test and related modules
try:
    from src.lbx_utils.lbx_change import modify_lbx, get_current_label_size, update_font_size
    from tests.integration.create_test_lbx import create_test_lbx
except ImportError:
    # Use direct imports for IDE/linter compatibility
    import sys
    import os.path
    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
    from src.lbx_utils.lbx_change import modify_lbx, get_current_label_size, update_font_size
    try:
        from tests.integration.create_test_lbx import create_test_lbx
    except ImportError:
        try:
            from create_test_lbx import create_test_lbx
        except ImportError:
            pytest.skip("Required modules could not be imported", allow_module_level=True)

# Constants
TEST_DIR = Path("test_samples")
NAMESPACES = {
    'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
    'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
    'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
    'image': 'http://schemas.brother.info/ptouch/2007/lbx/image'
}


# Fixtures
@pytest.fixture(scope="session")
def test_dir():
    """Create test directory if it doesn't exist."""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield TEST_DIR
    # Uncomment to clean up after tests
    # shutil.rmtree(TEST_DIR)


@pytest.fixture
def test_lbx(test_dir):
    """Use existing label template 3001.lbx for testing."""
    # Using an existing label template instead of creating one from scratch
    template_path = Path("label_templates/3001.lbx")
    input_path = TEST_DIR / "test_integration.lbx"

    # Copy the template to the test directory
    if template_path.exists():
        shutil.copy(template_path, input_path)
    else:
        # Fallback to creating a test file if template doesn't exist
        create_test_lbx(str(input_path))
        print("Warning: Using generated test file because template was not found.")

    yield input_path


@pytest.fixture
def output_lbx(test_dir, request):
    """Path for output LBX file with unique name based on the test."""
    # Create the output directory for lbx_change tests
    output_dir = Path("test_output/lbx_change")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get the name of the test function
    test_name = request.function.__name__

    # For parametrized tests, add the parameter value to the filename
    if hasattr(request, "param"):
        test_name = f"{test_name}_{request.param}"

    # Create a unique filename
    output_path = output_dir / f"{test_name}.lbx"

    return output_path


@pytest.fixture
def extract_lbx():
    """Fixture to extract and parse an LBX file."""
    def _extract(lbx_path):
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(lbx_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            xml_path = os.path.join(temp_dir, 'label.xml')
            tree = ET.parse(xml_path)
            return tree
    return _extract


@pytest.fixture(scope="session", autouse=True)
def extract_all_test_outputs():
    """
    Automatically extract all generated LBX files after tests run.
    This allows for easier inspection of the XML content.
    """
    # Run tests first
    yield

    # After all tests complete, extract all LBX files
    output_dir = Path("test_output/lbx_change")
    if not output_dir.exists():
        return

    extract_dir = output_dir / "extracted"
    extract_dir.mkdir(parents=True, exist_ok=True)

    # Find all LBX files
    lbx_files = list(output_dir.glob("*.lbx"))
    if not lbx_files:
        print("No LBX files found in test_output/lbx_change/")
        return

    print(f"\nExtracting {len(lbx_files)} test output LBX files to {extract_dir}...")

    for lbx_file in lbx_files:
        try:
            # Extract the LBX (zip) file
            base_name = lbx_file.stem
            test_extract_dir = extract_dir / base_name
            test_extract_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(lbx_file, 'r') as zip_ref:
                zip_ref.extractall(test_extract_dir)

            # Also copy the XML to the extract directory with the same name for easier viewing
            xml_path = test_extract_dir / "label.xml"
            if xml_path.exists():
                # Format the XML for better readability
                try:
                    tree = ET.parse(xml_path)
                    xml_content = ET.tostring(tree, encoding='UTF-8', xml_declaration=True, pretty_print=True)

                    # Write the formatted XML
                    with open(extract_dir / f"{base_name}.xml", 'wb') as f:
                        f.write(xml_content)
                except Exception as e:
                    print(f"  Error formatting XML for {base_name}: {e}")
                    # Fall back to simple copy
                    shutil.copy(xml_path, extract_dir / f"{base_name}.xml")

            print(f"  Extracted: {base_name}")
        except Exception as e:
            print(f"  Error extracting {lbx_file}: {e}")

    print(f"\nAll test output files can be found in:")
    print(f"  LBX files: {output_dir}")
    print(f"  Extracted content: {extract_dir}")
    print(f"  XML files: {extract_dir}/*.xml\n")


# Helper functions
def get_font_size(tree, xpath=".//text:fontExt"):
    """Get font size from the XML tree."""
    font_ext = tree.find(xpath, namespaces=NAMESPACES)
    if font_ext is not None:
        size = font_ext.get('size', '0pt')
        return float(size.replace('pt', ''))
    return None


def get_label_width(tree):
    """Get label width from the XML tree."""
    paper = tree.find(".//style:paper", namespaces=NAMESPACES)
    if paper is not None:
        width = paper.get('width', '0pt')
        return float(width.replace('pt', ''))
    return None


def get_image_dimensions(tree):
    """Get image dimensions from the XML tree."""
    img = tree.find(".//pt:objectStyle", namespaces=NAMESPACES)
    if img is not None:
        width = float(img.get('width', '0pt').replace('pt', ''))
        height = float(img.get('height', '0pt').replace('pt', ''))
        return (width, height)
    return None


def get_text_content(tree):
    """Get text content from the XML tree."""
    data = tree.find(".//pt:data", namespaces=NAMESPACES)
    if data is not None:
        return data.text
    return ""  # Return empty string instead of None to simplify assertions


# Tests for each major feature
def test_font_size_change(test_lbx, output_lbx, extract_lbx):
    """Test changing font size."""
    # Original font size
    original_tree = extract_lbx(test_lbx)
    original_size = get_font_size(original_tree)

    # Modify the file
    new_font_size = 14
    modify_lbx(str(test_lbx), str(output_lbx), {
        'font_size': new_font_size,
        'verbose': True
    })

    # Check the modified file
    modified_tree = extract_lbx(output_lbx)
    modified_size = get_font_size(modified_tree)

    assert modified_size == new_font_size
    assert original_size != modified_size


def test_bold_font_size_change(test_lbx, output_lbx, extract_lbx):
    """Test changing bold font size separately."""
    # Modify the file
    regular_size = 10
    bold_size = 12
    modify_lbx(str(test_lbx), str(output_lbx), {
        'font_size': regular_size,
        'bold_font_size': bold_size,
        'verbose': True
    })

    # This test may not be useful without bold text in the sample
    # But we can at least check that the modification runs without errors
    assert output_lbx.exists()


def test_label_size_change(test_lbx, output_lbx, extract_lbx):
    """Test changing label tape size."""
    # Original label size
    original_tree = extract_lbx(test_lbx)
    original_size_mm = get_current_label_size(original_tree.getroot())
    original_width_pt = get_label_width(original_tree)

    # Pick a different size than the original
    new_size_mm = 18 if original_size_mm != 18 else 24

    # Modify the file
    modify_lbx(str(test_lbx), str(output_lbx), {
        'label_size': new_size_mm,
        'verbose': True
    })

    # Check the modified file
    modified_tree = extract_lbx(output_lbx)
    modified_size_mm = get_current_label_size(modified_tree.getroot())
    modified_width_pt = get_label_width(modified_tree)

    assert modified_size_mm == new_size_mm
    assert original_size_mm != modified_size_mm
    assert original_width_pt != modified_width_pt


def test_vertical_centering(test_lbx, output_lbx, extract_lbx):
    """Test centering elements vertically."""
    # Modify the file
    modify_lbx(str(test_lbx), str(output_lbx), {
        'center_vertically': True,
        'verbose': True
    })

    # Simply check that the modification runs without errors
    # A more thorough test would require checking Y positions
    assert output_lbx.exists()


def test_image_scaling(test_lbx, output_lbx, extract_lbx):
    """Test image scaling functionality."""
    # This test requires an LBX with images
    # Since our test LBX doesn't have images, we'll just verify it runs without errors

    # Modify the file
    scale_factor = 1.5
    modify_lbx(str(test_lbx), str(output_lbx), {
        'image_scale': scale_factor,
        'verbose': True
    })

    assert output_lbx.exists()


def test_text_margin(test_lbx, output_lbx, extract_lbx):
    """Test text margin adjustment."""
    # Modify the file
    text_margin = 2.0  # mm
    modify_lbx(str(test_lbx), str(output_lbx), {
        'text_margin': text_margin,
        'verbose': True
    })

    assert output_lbx.exists()


def test_text_tweaks_dimension_notation(test_lbx, output_lbx, extract_lbx):
    """Test text tweaks for dimension notation."""
    # Original text from template label
    original_tree = extract_lbx(test_lbx)
    original_text = get_text_content(original_tree)

    # Check if we already have dimension notation (2×4) or if we need to convert it (2 x 4)
    # If the original contains "×", we'll test replacing it with "x" and then converting back
    if "×" in original_text:
        # Create a temporary file with "x" instead of "×"
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the LBX
            with zipfile.ZipFile(test_lbx, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Modify the XML to use "x" instead of "×"
            xml_path = os.path.join(temp_dir, 'label.xml')
            modified_xml = ""
            with open(xml_path, 'r', encoding='utf-8') as f:
                modified_xml = f.read().replace("×", " x ")

            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(modified_xml)

            # Create a modified LBX with the "x" notation
            temp_lbx = str(test_lbx) + ".temp"
            with zipfile.ZipFile(temp_lbx, 'w') as zipf:
                zipf.write(xml_path, arcname="label.xml")

            # Now use this modified file for the test
            options = {
                'text_tweaks': True,
                'convert_dimension_notation': True,
                'font_size': 10,
                'verbose': True
            }

            # Modify the file
            modify_lbx(temp_lbx, str(output_lbx), options)

            # Check that "2 x 4" becomes "2×4" again
            modified_tree = extract_lbx(output_lbx)
            modified_text = get_text_content(modified_tree)

            # Clean up the temporary file
            os.remove(temp_lbx)

            # Verify the result
            assert "×" in modified_text, f"Expected '×' in modified text, but got: '{modified_text}'"
            assert " x " not in modified_text, f"Unexpected ' x ' still found in modified text: '{modified_text}'"
    else:
        # If there's no dimension notation yet, we'll test the regular conversion
        # Find a number pattern like "2 x 4" to convert
        number_pattern = re.search(r'(\d+)\s*x\s*(\d+)', original_text, re.IGNORECASE)
        if number_pattern:
            # Process the file to convert the notation
            options = {
                'text_tweaks': True,
                'convert_dimension_notation': True,
                'font_size': 10,
                'verbose': True
            }

            # Modify the file
            modify_lbx(str(test_lbx), str(output_lbx), options)

            # Check the result
            modified_tree = extract_lbx(output_lbx)
            modified_text = get_text_content(modified_tree)

            # The pattern should now use the multiplication symbol
            original_pattern = number_pattern.group(0)
            expected_pattern = original_pattern.replace(" x ", "×").replace("x", "×")

            assert expected_pattern in modified_text, f"Expected '{expected_pattern}' in modified text, but got: '{modified_text}'"
            assert original_pattern not in modified_text, f"Unexpected '{original_pattern}' still found in modified text: '{modified_text}'"
        else:
            # If the file doesn't have any notation to convert, we'll skip this test
            pytest.skip("No dimension notation found in the template file to test conversion")


def test_find_replace(test_lbx, output_lbx, extract_lbx):
    """Test find and replace functionality."""
    # Get original text
    original_tree = extract_lbx(test_lbx)
    original_text = get_text_content(original_tree)

    # Based on the template file content which we know has "3001" in it
    find_text = "3001"
    replace_text = "TEST-REPLACED"

    # Make sure the text to find exists in the original
    if find_text not in original_text:
        pytest.skip(f"Text '{find_text}' not found in the template file to test replacement")

    modify_lbx(str(test_lbx), str(output_lbx), {
        'text_tweaks': True,
        'custom_replacements': [(find_text, replace_text)],
        'font_size': 10,  # Add font size change to bypass early exit condition
        'verbose': True
    })

    # Check the replacement
    modified_tree = extract_lbx(output_lbx)
    modified_text = get_text_content(modified_tree)

    assert replace_text in modified_text, f"Expected '{replace_text}' in modified text, but got: '{modified_text}'"
    assert find_text not in modified_text, f"Unexpected '{find_text}' still found in modified text: '{modified_text}'"


def test_regex_replacement(test_lbx, output_lbx, extract_lbx):
    """Test regex replacement functionality."""
    # Get original text to find something to replace
    original_tree = extract_lbx(test_lbx)
    original_text = get_text_content(original_tree)

    # Look for a number pattern to replace
    number_pattern = re.search(r'(\d+)', original_text)
    if not number_pattern:
        pytest.skip("No numbers found in the template file to test regex replacement")

    # Use the found number for the replacement
    pattern = fr"(\d+)"
    replacement = r"NUM-\1"

    modify_lbx(str(test_lbx), str(output_lbx), {
        'text_tweaks': True,
        'regex_replacements': [(pattern, replacement)],
        'font_size': 10,  # Add font size change to bypass early exit condition
        'verbose': True
    })

    # Check the replacement
    modified_tree = extract_lbx(output_lbx)
    modified_text = get_text_content(modified_tree)

    # The pattern should match at least one number and replace it
    assert "NUM-" in modified_text, f"Expected 'NUM-' in modified text, but got: '{modified_text}'"


def test_case_insensitive_search(test_lbx, output_lbx, extract_lbx):
    """Test case-insensitive text search and replace."""
    # Get original text
    original_tree = extract_lbx(test_lbx)
    original_text = get_text_content(original_tree)

    # Find a text that might be in the file - look for letters
    text_match = re.search(r'([a-zA-Z]+)', original_text)
    if not text_match:
        pytest.skip("No text found in the template file to test case-insensitive search")

    # Use the found text with different case for replacement
    find_text = text_match.group(0).lower()  # Force lowercase for testing
    if find_text.islower() == find_text.isupper():  # If it's only digits or symbols
        pytest.skip("Found text has no case variation to test")

    replace_text = "REPLACED-TEXT"

    modify_lbx(str(test_lbx), str(output_lbx), {
        'text_tweaks': True,
        'custom_replacements': [(find_text, replace_text)],
        'ignore_case': True,
        'font_size': 10,  # Add font size change to bypass early exit condition
        'verbose': True
    })

    # Check the replacement worked despite case difference
    modified_tree = extract_lbx(output_lbx)
    modified_text = get_text_content(modified_tree)

    assert replace_text in modified_text, f"Expected '{replace_text}' in modified text, but got: '{modified_text}'"
    # Check that the original text is gone (regardless of case)
    assert find_text.lower() not in modified_text.lower(), f"Original text still found in modified text: '{modified_text}'"


def test_compacting_multiline_text(test_lbx, output_lbx, extract_lbx):
    """Test compacting multiline text (not applicable with our simple test file)."""
    # This would need a test file with multiple lines of text
    # Just verify it runs without errors

    modify_lbx(str(test_lbx), str(output_lbx), {
        'text_tweaks': True,
        'compact_multiline': True,
        'font_size': 10,  # Add font size change to bypass early exit condition
        'verbose': True
    })

    assert output_lbx.exists()


def test_combination_of_features(test_lbx, output_lbx, extract_lbx):
    """Test combination of multiple features together."""
    # Get original properties
    original_tree = extract_lbx(test_lbx)
    original_size_mm = get_current_label_size(original_tree.getroot())
    original_font_size = get_font_size(original_tree)
    original_text = get_text_content(original_tree)

    # Choose parameters different from original
    new_size_mm = 24 if original_size_mm != 24 else 18
    new_font_size = 14 if original_font_size != 14 else 12

    # Use text that's in the template
    find_text = "3001"
    replace_text = "COMBO-TEST"

    # Skip the replacement test if the text isn't in the original
    has_text_to_replace = find_text in original_text

    # Apply multiple changes at once
    modify_lbx(str(test_lbx), str(output_lbx), {
        'label_size': new_size_mm,
        'font_size': new_font_size,
        'center_vertically': True,
        'image_scale': 1.5,
        'text_margin': 2.0,
        'text_tweaks': True,
        'custom_replacements': [(find_text, replace_text)],
        'verbose': True
    })

    # Check the results
    modified_tree = extract_lbx(output_lbx)
    modified_size_mm = get_current_label_size(modified_tree.getroot())
    modified_font_size = get_font_size(modified_tree)
    modified_text = get_text_content(modified_tree)

    assert modified_size_mm == new_size_mm
    assert modified_font_size == new_font_size

    # Check the text replacement if applicable
    if has_text_to_replace:
        assert replace_text in modified_text, f"Expected '{replace_text}' in modified text, but got: '{modified_text}'"
        assert find_text not in modified_text, f"Unexpected '{find_text}' still found in modified text: '{modified_text}'"


def test_compatibility_tweaks(test_lbx, output_lbx, extract_lbx):
    """Test compatibility tweaks are applied."""
    # Original printer info
    original_tree = extract_lbx(test_lbx)
    paper_elem = original_tree.find(".//style:paper", namespaces=NAMESPACES)
    original_printer_id = paper_elem.get('printerID')

    # Modify to large format which should trigger printer compatibility update
    modify_lbx(str(test_lbx), str(output_lbx), {
        'label_size': 24,  # 24mm should trigger compatibility tweaks
        'verbose': True
    })

    # Check the modified file
    modified_tree = extract_lbx(output_lbx)
    paper_elem = modified_tree.find(".//style:paper", namespaces=NAMESPACES)
    modified_printer_id = paper_elem.get('printerID')

    # Should be updated to the large format printer ID
    assert modified_printer_id == "30256"


def test_text_content_retrieval(test_lbx, output_lbx, extract_lbx):
    """Test text content retrieval functionality."""
    # Use the template file copied by the test_lbx fixture
    input_file = test_lbx
    output_file = output_lbx

    # Extract original content to know what text to expect
    original_tree = extract_lbx(input_file)
    original_text = get_text_content(original_tree)

    # Choose a replacement string
    find_text = "3001"  # Text likely to be in the template
    replace_text = "TESTING"

    # Setup options with a specific text replacement
    options = {
        "font_size": 10,
        "label_size": 12,
        "text_tweaks": True,
        "custom_replacements": [(find_text, replace_text)]
    }

    # Run the modification
    modify_lbx(str(input_file), str(output_file), options)

    # Extract text content from the modified file
    modified_tree = extract_lbx(output_file)
    modified_text = get_text_content(modified_tree)

    # Verify the content contains our replacement
    assert modified_text, "Text content should not be empty"

    # If the original text contains the find_text, assert it's been replaced
    if find_text in original_text:
        assert replace_text in modified_text, f"Expected '{replace_text}' in text content: '{modified_text}'"
        assert find_text not in modified_text, f"'{find_text}' should be replaced: '{modified_text}'"
    else:
        # If the text wasn't found, just make sure we have content and the file was processed
        print(f"Note: '{find_text}' not found in original text. Replacement not tested.")
        assert output_file.exists(), "Output file should exist"


# Parametrized tests for different label sizes
@pytest.mark.parametrize("label_size", [9, 12, 18, 24])
def test_all_label_sizes(test_lbx, output_lbx, extract_lbx, label_size):
    """Test compatibility with all supported label sizes."""
    # Modify the file
    modify_lbx(str(test_lbx), str(output_lbx), {
        'label_size': label_size,
        'verbose': True
    })

    # Check the modified file
    modified_tree = extract_lbx(output_lbx)
    modified_size = get_current_label_size(modified_tree.getroot())

    assert modified_size == label_size


# Parametrized tests for different font sizes
@pytest.mark.parametrize("font_size", [6, 8, 10, 12, 14, 16])
def test_all_font_sizes(test_lbx, output_lbx, extract_lbx, font_size):
    """Test compatibility with various font sizes."""
    # Modify the file
    modify_lbx(str(test_lbx), str(output_lbx), {
        'font_size': font_size,
        'verbose': True
    })

    # Check the modified file
    modified_tree = extract_lbx(output_lbx)
    modified_size = get_font_size(modified_tree)

    assert modified_size == font_size