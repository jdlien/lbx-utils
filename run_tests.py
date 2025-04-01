#!/usr/bin/env python3
"""
Test Runner Script

This script provides a simple way to run the test suite for lbx_text_edit.py.
It handles setting up the test environment and running the tests.

Usage:
    python run_tests.py
"""

import os
import sys
import unittest
import zipfile
import glob
from test_lbx_text_edit import LBXTextEditor, LBXTextEditTests, TEMP_DIR

def extract_label_xml_files():
    """Extract label.xml from each LBX file in the test output directory."""
    print("\nExtracting label.xml files for easier analysis...")

    # Find all LBX files in the output directory
    lbx_files = glob.glob(os.path.join(TEMP_DIR, "*.lbx"))

    if not lbx_files:
        print("No LBX files found in the output directory.")
        return

    # Create a directory for XML files if it doesn't exist
    xml_dir = os.path.join(TEMP_DIR, "xml")
    if not os.path.exists(xml_dir):
        os.makedirs(xml_dir)

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

def main():
    """Run all the tests."""
    # Create output directory if it doesn't exist
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    # Run tests
    print("Running LBX Text Editor tests...")

    # Load the test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(LBXTextEditTests)

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print results
    print("\nTest Results:")
    print(f"- Ran {result.testsRun} tests")
    print(f"- Failures: {len(result.failures)}")
    print(f"- Errors: {len(result.errors)}")
    print(f"- Skipped: {len(result.skipped)}")

    if result.wasSuccessful():
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed. See above for details.")

    # Extract label.xml files from test output
    extract_label_xml_files()

    # Show where output files are located
    print(f"\nTest output files can be found in the '{TEMP_DIR}' directory.")
    print(f"Extracted XML files can be found in the '{TEMP_DIR}/xml' directory.")

if __name__ == "__main__":
    main()