#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for lbx_create.py

This script tests all functionality of lbx_create.py by generating various label configurations
and writing output files to lbx-create-test-output directory.
"""

import os
import sys
import subprocess
import zipfile
import tempfile
import shutil
import unittest
from pathlib import Path

# Test configuration
OUTPUT_DIR = "test_output"
TEST_IMAGES_DIR = "test_images"
IMAGE1 = os.path.join(TEST_IMAGES_DIR, "3004.png")
IMAGE2 = os.path.join(TEST_IMAGES_DIR, "3005.png")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ensure test images directory exists
os.makedirs(os.path.dirname(IMAGE1), exist_ok=True)

class LBXCreateTestCase(unittest.TestCase):
    """Test case for lbx_create.py functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Ensure test image 1 exists
        if not os.path.exists(IMAGE1):
            # Create a simple 20x20 pixel image
            try:
                from PIL import Image
                img = Image.new('RGB', (20, 20), color='red')
                img.save(IMAGE1)
            except ImportError:
                print("Warning: PIL not installed. Test image not created.")

        # Ensure test image 2 exists
        if not os.path.exists(IMAGE2):
            # Create a simple 20x20 pixel image
            try:
                from PIL import Image
                img = Image.new('RGB', (20, 20), color='blue')
                img.save(IMAGE2)
            except ImportError:
                print("Warning: PIL not installed. Test image not created.")

    @classmethod
    def _create_dummy_image(cls, filepath, width=100, height=100, color="black"):
        """Create a dummy image for testing."""
        try:
            from PIL import Image
            img = Image.new('RGB', (width, height), color=color)
            img.save(filepath)
            print(f"Created test image: {filepath}")
        except ImportError:
            print("PIL not available. Creating an empty file instead.")
            with open(filepath, 'wb') as f:
                f.write(b'\x89PNG\r\n\x1a\n')

    def _run_lbx_create(self, output_file, *args):
        """Run lbx_create.py with the given arguments."""
        cmd = ["python", "-m", "lbx_utils.lbx_create", "create", "--output", output_file] + list(args)
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Print output for debugging
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")

        self.assertEqual(result.returncode, 0, f"Command failed with error: {result.stderr}")
        self.assertTrue(os.path.exists(output_file), f"Output file not created: {output_file}")

        # Unzip the LBX file for inspection
        self._unzip_lbx_for_inspection(output_file)

        return result

    def _verify_lbx_file(self, filepath):
        """Verify that the LBX file contains the expected files."""
        self.assertTrue(os.path.exists(filepath), f"File does not exist: {filepath}")
        with zipfile.ZipFile(filepath, 'r') as zipf:
            file_list = zipf.namelist()
            self.assertIn("label.xml", file_list, "label.xml not found in LBX file")
            self.assertIn("prop.xml", file_list, "prop.xml not found in LBX file")
            return file_list

    def _unzip_lbx_for_inspection(self, lbx_filepath):
        """
        Unzip the LBX file into a directory with the same name for easy inspection.

        Args:
            lbx_filepath (str): Path to the LBX file to unzip
        """
        # Create extraction directory based on the LBX filename
        base_name = os.path.basename(lbx_filepath)
        extract_dir = os.path.join(OUTPUT_DIR, os.path.splitext(base_name)[0])

        # Create or clear the directory
        os.makedirs(extract_dir, exist_ok=True)

        # Extract the LBX (ZIP) file
        with zipfile.ZipFile(lbx_filepath, 'r') as zipf:
            zipf.extractall(extract_dir)

        print(f"Extracted LBX file to: {extract_dir}")

    def test_00_blank_label(self):
        """Test creating a blank label with no content."""
        output_file = os.path.join(OUTPUT_DIR, "00_blank_label.lbx")
        self._run_lbx_create(output_file, "--size", "12")
        file_list = self._verify_lbx_file(output_file)
        self.assertEqual(len(file_list), 2, "Expected only label.xml and prop.xml")

    def test_01_basic_text_label(self):
        """Test creating a basic text label."""
        output_file = os.path.join(OUTPUT_DIR, "01_basic_text.lbx")
        self._run_lbx_create(output_file, "--text", "Basic Text Label", "--size", "24")
        file_list = self._verify_lbx_file(output_file)
        self.assertEqual(len(file_list), 2, "Expected only label.xml and prop.xml")

    def test_02_multiple_text_elements(self):
        """Test creating a label with multiple text elements."""
        output_file = os.path.join(OUTPUT_DIR, "02_multiple_text.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "First Line",
            "--text", "Second Line",
            "--text", "Third Line",
            "--size", "24"
        )
        self._verify_lbx_file(output_file)

    def test_03_formatted_text(self):
        """Test creating a label with formatted text."""
        output_file = os.path.join(OUTPUT_DIR, "03_formatted_text.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Bold Text",
            "--bold",
            "--font", "Arial",
            "--font-size", "14",
            "--size", "24"
        )
        self._verify_lbx_file(output_file)

    def test_04_italic_text(self):
        """Test creating a label with italic text."""
        output_file = os.path.join(OUTPUT_DIR, "04_italic_text.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Italic Text",
            "--italic",
            "--font", "Arial",
            "--font-size", "12",
            "--size", "24"
        )
        self._verify_lbx_file(output_file)

    def test_05_bold_italic_text(self):
        """Test creating a label with both bold and italic text."""
        output_file = os.path.join(OUTPUT_DIR, "05_bold_italic_text.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Bold Italic Text",
            "--bold",
            "--italic",
            "--font", "Arial",
            "--font-size", "14",
            "--size", "24"
        )
        self._verify_lbx_file(output_file)

    def test_06_single_image(self):
        """Test creating a label with a single image."""
        output_file = os.path.join(OUTPUT_DIR, "06_single_image.lbx")
        self._run_lbx_create(
            output_file,
            "--image", IMAGE1,
            "--size", "24"
        )
        file_list = self._verify_lbx_file(output_file)
        self.assertIn(os.path.basename(IMAGE1), file_list, "Image file not found in LBX")

    def test_07_text_and_image(self):
        """Test creating a label with text and an image."""
        output_file = os.path.join(OUTPUT_DIR, "07_text_and_image.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Image with Text",
            "--image", IMAGE1,
            "--size", "24"
        )
        file_list = self._verify_lbx_file(output_file)
        self.assertIn(os.path.basename(IMAGE1), file_list, "Image file not found in LBX")

    def test_08_multiple_images(self):
        """Test creating a label with multiple images."""
        output_file = os.path.join(OUTPUT_DIR, "08_multiple_images.lbx")
        self._run_lbx_create(
            output_file,
            "--image", IMAGE1,
            "--image", IMAGE2,
            "--size", "24"
        )
        file_list = self._verify_lbx_file(output_file)
        self.assertIn(os.path.basename(IMAGE1), file_list, "First image not found in LBX")
        self.assertIn(os.path.basename(IMAGE2), file_list, "Second image not found in LBX")

    def test_09_multiple_images_and_text(self):
        """Test creating a label with multiple images and text."""
        output_file = os.path.join(OUTPUT_DIR, "09_multiple_images_and_text.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Multiple Images",
            "--text", "With Multiple Text",
            "--image", IMAGE1,
            "--image", IMAGE2,
            "--size", "24"
        )
        file_list = self._verify_lbx_file(output_file)
        self.assertIn(os.path.basename(IMAGE1), file_list, "First image not found in LBX")
        self.assertIn(os.path.basename(IMAGE2), file_list, "Second image not found in LBX")

    def test_10_different_sizes(self):
        """Test creating labels with different sizes."""
        sizes = [9, 12, 18, 24]
        for size in sizes:
            output_file = os.path.join(OUTPUT_DIR, f"10_size_{size}mm.lbx")
            self._run_lbx_create(
                output_file,
                "--text", f"{size}mm Label",
                "--size", str(size)
            )
            self._verify_lbx_file(output_file)

    def test_11_fixed_height(self):
        """Test creating a label with fixed height (non-auto length)."""
        output_file = os.path.join(OUTPUT_DIR, "11_fixed_height.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Fixed Height Label",
            "--height", "100pt",
            "--size", "24"
        )
        self._verify_lbx_file(output_file)

    def test_12_custom_width(self):
        """Test creating a label with custom width for text."""
        output_file = os.path.join(OUTPUT_DIR, "12_custom_width.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "This is a very long text that should wrap to multiple lines due to the narrower width setting",
            "--width", "80pt",
            "--size", "24"
        )
        self._verify_lbx_file(output_file)

    def test_13_complex_label(self):
        """Test creating a complex label with all features."""
        output_file = os.path.join(OUTPUT_DIR, "13_complex_label.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Main Title",
            "--text", "Subtitle Text",
            "--text", "Details and information",
            "--bold",
            "--font", "Arial",
            "--font-size", "14",
            "--image", IMAGE1,
            "--image", IMAGE2,
            "--size", "24"
        )
        file_list = self._verify_lbx_file(output_file)
        self.assertIn(os.path.basename(IMAGE1), file_list, "First image not found in LBX")
        self.assertIn(os.path.basename(IMAGE2), file_list, "Second image not found in LBX")


if __name__ == "__main__":
    unittest.main()