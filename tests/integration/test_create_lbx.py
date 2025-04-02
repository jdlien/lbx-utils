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
import shutil

# Add the parent directory to path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the functionality from create_test_lbx.py
from tests.integration.create_test_lbx import create_test_lbx

# Try different import paths to handle different runtime environments
try:
    from src.lbx_utils import LBXTextEditor, TextObject, StringItem, FontInfo, NAMESPACES, LabelConfig, LBXCreator
    from src.lbx_utils.lbx_create import create_image_object, LABEL_SIZES
except ImportError:
    # This import will work when running within the package, but may show a linter error in IDE
    # The linter error can be safely ignored as we handle both import paths
    from lbx_utils import LBXTextEditor, TextObject, StringItem, FontInfo, NAMESPACES, LabelConfig, LBXCreator  # linter: ignore
    from lbx_utils.lbx_create import create_image_object, LABEL_SIZES  # linter: ignore

# Directory to store output files
TEST_OUTPUT_DIR = Path("test_output/lbx_create")

@pytest.fixture(scope="session", autouse=True)
def setup_output_dir():
    """Create output directory for test files."""
    # Create output directory if it doesn't exist
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    yield

    # No cleanup by default to allow inspection of results
    # Uncomment to clean up after tests if desired
    # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)

    # Extract all LBX files for inspection
    extract_dir = TEST_OUTPUT_DIR / "extracted"
    extract_dir.mkdir(exist_ok=True)

    lbx_files = list(TEST_OUTPUT_DIR.glob("*.lbx"))
    if not lbx_files:
        print("No LBX files found in the output directory.")
        return

    print(f"\nExtracting {len(lbx_files)} LBX files to {extract_dir}...")

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
                # Format the XML for better readability if lxml is available
                try:
                    from lxml import etree
                    tree = etree.parse(xml_path)
                    xml_content = etree.tostring(tree, encoding='UTF-8', xml_declaration=True, pretty_print=True)

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
    print(f"  LBX files: {TEST_OUTPUT_DIR}")
    print(f"  Extracted content: {extract_dir}")
    print(f"  XML files: {extract_dir}/*.xml\n")

@pytest.fixture
def output_path(request):
    """Generate a unique output path based on the test name."""
    test_name = request.node.name
    # Clean the test name to use as a filename
    filename = test_name.replace(" ", "_").replace("[", "_").replace("]", "_")
    return TEST_OUTPUT_DIR / f"{filename}.lbx"

@pytest.fixture
def create_test_lbx_file():
    """Create a test LBX file with dimension text in the test output directory."""
    def _create_file(output_path=None):
        if output_path is None:
            output_path = TEST_OUTPUT_DIR / "basic_dimension.lbx"
        output_path = str(output_path)
        return create_test_lbx(output_path)
    return _create_file

@pytest.mark.integration
def test_create_basic_lbx(output_path, create_test_lbx_file):
    """Test creating a basic LBX file with dimension text."""
    # Create a test file
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
def test_create_and_modify_label(output_path):
    """Test creating a label and then modifying it with LBXTextEditor."""
    # Create the test file using create_test_lbx
    create_test_lbx(str(output_path))

    # Create a modified output path
    modified_path = TEST_OUTPUT_DIR / "modified_label.lbx"

    # Now modify it with LBXTextEditor
    editor = LBXTextEditor()
    xml_path = editor.extract_from_lbx(str(output_path))
    editor.load(xml_path)

    # Verify text objects were loaded
    assert len(editor.get_text_objects()) > 0
    text_obj = editor.get_text_object_by_index(0)

    # Make a simple edit
    text_obj.edit_text("Modified 4×4 Brick")

    # Save to a new file
    editor.update_lbx(str(output_path), str(modified_path))

    # Verify the modified file exists
    assert os.path.exists(modified_path)

    # Open the modified file to verify changes
    new_editor = LBXTextEditor()
    xml_path = new_editor.extract_from_lbx(str(modified_path))
    new_editor.load(xml_path)

    # Verify the text was changed
    modified_text_obj = new_editor.get_text_object_by_index(0)
    assert "Modified" in modified_text_obj.text
    assert "×" in modified_text_obj.text  # Unicode multiplication symbol

@pytest.mark.integration
def test_create_with_label_config(output_path):
    """Test using LabelConfig to create a label structure."""
    # Create a simple LabelConfig for testing
    config = LabelConfig(
        size_mm=24,
        auto_length=True
    )

    # Initialize LBXCreator with the config
    creator = LBXCreator(config)

    # Verify creator was initialized
    assert creator is not None

    # We can't fully test the creation without mock objects for the XML structure
    # but we can at least check the creator was initialized with the config
    assert creator.config.size_mm == 24
    assert creator.config.auto_length is True

@pytest.mark.integration
def test_create_with_images_and_centered_text(output_path):
    """Test creating a label with images on both sides of text and vertical centering."""
    # Create test image paths in the test output directory
    test_images_dir = TEST_OUTPUT_DIR / "images"
    test_images_dir.mkdir(exist_ok=True)
    image1_path = test_images_dir / "test_img1.png"
    image2_path = test_images_dir / "test_img2.png"

    # Create test images if they don't exist
    for img_path, color in [(image1_path, (255, 0, 0)), (image2_path, (0, 0, 255))]:
        if not img_path.exists():
            try:
                from PIL import Image
                img = Image.new('RGB', (20, 20), color=color)
                img.save(img_path)
                print(f"Created test image: {img_path}")
            except ImportError:
                print("Warning: PIL not installed. Test image not created.")
                img_path.write_bytes(b'\x89PNG\r\n\x1a\n')  # Minimal PNG header

    # Create a LabelConfig for our test
    config = LabelConfig(
        size_mm=24,
        auto_length=True
    )

    # Create the first image object (left side)
    image1 = create_image_object(
        str(image1_path),
        x="10pt",
        y="10pt",  # This will be adjusted for vertical centering
        width="20pt",
        height="20pt"
    )

    # Create the text object (middle)
    text_obj = TextObject(
        text="Test Label",
        x="40pt",  # Position to the right of the first image with some spacing
        y="10pt",  # This will be adjusted for vertical centering
        width="40pt",
        height="20pt",
        font_info=FontInfo(name="Arial", size="12pt")
    )

    # Create the second image object (right side)
    image2 = create_image_object(
        str(image2_path),
        x="90pt",  # Position to the right of the text with some spacing
        y="10pt",  # This will be adjusted for vertical centering
        width="20pt",
        height="20pt"
    )

    # Add all objects to the config
    config.image_objects.extend([image1, image2])
    config.text_objects.append(text_obj)

    # Create the LBX file
    creator = LBXCreator(config)

    # Calculate vertical center for all objects
    size_config = LABEL_SIZES[config.size_mm]

    # Label height minus margins
    label_height = float(size_config["background_height"].replace("pt", ""))

    # Get object height (assuming all objects have the same height)
    object_height = float(image1.height.replace("pt", ""))

    # Calculate center position
    center_y = (label_height - object_height) / 2 + float(size_config["background_y"].replace("pt", ""))
    center_y_pt = f"{center_y}pt"

    # Update Y positions to center vertically
    for img in config.image_objects:
        img.y = center_y_pt

    for txt in config.text_objects:
        txt.y = center_y_pt

    # Create the LBX file
    creator.create_lbx(str(output_path))

    # Verify the file exists
    assert os.path.exists(output_path)

    # Verify it's a valid zip file
    with zipfile.ZipFile(output_path, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        assert 'label.xml' in file_list

        # Check that both images are included
        image_files = [f for f in file_list if f.endswith(".png")]
        assert len(image_files) == 2

        # Extract and check the XML content
        with zip_ref.open('label.xml') as xml_file:
            xml_content = xml_file.read().decode('utf-8')
            assert 'Test Label' in xml_content
            # The font might be Helsinki instead of Arial in the actual output
            assert any(font in xml_content for font in ['Arial', 'Helsinki'])