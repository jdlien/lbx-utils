"""
Test configuration and shared fixtures for pytest.

This file contains common fixtures used across test modules.
"""

import os
import sys
import zipfile
import glob
import pytest
import shutil
from pathlib import Path

# Constants
TEMP_DIR = "test_output"
TEST_DATA_DIR = Path("data/label_examples")
TEST_SAMPLE = TEST_DATA_DIR / "30182.lbx"

@pytest.fixture(scope="session")
def temp_dir():
    """Provide a temporary directory for test output files that persists across the test session."""
    # Create the directory if it doesn't exist
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    yield TEMP_DIR

    # By default, don't clean up after tests to allow inspection
    # Uncomment to enable automatic cleanup
    # if os.path.exists(TEMP_DIR):
    #     shutil.rmtree(TEMP_DIR)

@pytest.fixture(scope="session")
def xml_dir(temp_dir):
    """Provide a directory for extracted XML files."""
    xml_dir_path = os.path.join(temp_dir, "xml")
    if not os.path.exists(xml_dir_path):
        os.makedirs(xml_dir_path)
    return xml_dir_path

@pytest.fixture(scope="session")
def test_sample():
    """Provide the path to the test sample LBX file."""
    if not TEST_SAMPLE.exists():
        pytest.fail(f"Test sample {TEST_SAMPLE} not found")
    return str(TEST_SAMPLE)

@pytest.fixture
def lbx_text_editor():
    """Provide a fresh LBXTextEditor instance for each test."""
    from lbx_utils.lbx_text_edit import LBXTextEditor
    return LBXTextEditor()

@pytest.fixture(scope="session", autouse=True)
def extract_label_xml_files(temp_dir, xml_dir):
    """
    Extract label.xml from each LBX file in the test output directory.

    This fixture runs automatically after all tests to extract XML files for inspection.
    """
    # Run tests first
    yield

    # After tests complete, extract XML files
    print("\nExtracting label.xml files for easier analysis...")

    # Find all LBX files in the output directory
    lbx_files = glob.glob(os.path.join(temp_dir, "*.lbx"))

    if not lbx_files:
        print("No LBX files found in the output directory.")
        return

    # Extract each LBX file's label.xml
    for lbx_path in lbx_files:
        try:
            # Get the base name without extension
            base_name = os.path.basename(lbx_path).rsplit('.', 1)[0]
            xml_path = os.path.join(xml_dir, f"{base_name}.xml")

            # Extract the label.xml
            with zipfile.ZipFile(lbx_path, 'r') as zip_ref:
                # Check if label.xml exists in the archive
                if 'label.xml' in zip_ref.namelist():
                    # Extract label.xml to the xml directory with a new name
                    with zip_ref.open('label.xml') as source:
                        with open(xml_path, 'wb') as target:
                            target.write(source.read())
                    print(f"  Extracted: {xml_path}")
                else:
                    print(f"  Warning: No label.xml found in {lbx_path}")
        except Exception as e:
            print(f"  Error extracting {lbx_path}: {str(e)}")

    print(f"Extracted XML files can be found in: {xml_dir}")
    print(f"Test output files can be found in: {temp_dir}")

@pytest.fixture
def create_test_lbx_file():
    """Create a test LBX file with dimension text."""
    from tests.integration.create_test_lbx import create_test_lbx

    def _create(output_path=None):
        if output_path is None:
            output_path = os.path.join(TEMP_DIR, "test_dimension.lbx")
        return create_test_lbx(output_path)

    return _create