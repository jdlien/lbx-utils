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

        # Run lbx_create to generate the test file
        result = self._run_lbx_create(
            output_file,
            "--text", "First Line",
            "--text", "Second Line",
            "--text", "Third Line",
            "--size", "24"
        )

        # Extract and verify the file contents
        extract_dir = os.path.join(OUTPUT_DIR, "02_multiple_text")
        label_xml_path = os.path.join(extract_dir, "label.xml")

        # Check if label.xml exists
        self.assertTrue(os.path.exists(label_xml_path), "label.xml not found in extracted LBX")

        # Parse the label XML
        import xml.etree.ElementTree as ET

        # Define namespaces to properly parse the XML
        namespaces = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
            'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
        }

        tree = ET.parse(label_xml_path)
        root = tree.getroot()

        # Find all text objects - using the text:text path
        text_objects = root.findall('.//text:text', namespaces)

        # Verify we have exactly 3 text objects
        self.assertEqual(len(text_objects), 3, "Expected exactly 3 text objects")

        # Extract position information from the objectStyle elements within text elements
        positions = []
        for i, obj in enumerate(text_objects):
            # Find the objectStyle element
            obj_style = obj.find('./pt:objectStyle', namespaces)
            if obj_style is not None:
                x = obj_style.get('x')
                y = obj_style.get('y')

                # Check text content to ensure it matches our expected order
                data_elem = obj.find('./pt:data', namespaces)
                if data_elem is not None and data_elem.text:
                    text_content = data_elem.text
                else:
                    text_content = f"Unknown text content in element {i+1}"

                positions.append({
                    'index': i,
                    'x': x,
                    'y': y,
                    'text': text_content
                })

                # Verify that x and y attributes exist and have valid pt values
                self.assertIsNotNone(x, f"Text element {i+1} is missing x position")
                self.assertIsNotNone(y, f"Text element {i+1} is missing y position")
                if x is not None:
                    self.assertTrue(x.endswith('pt'), f"Text element {i+1} has invalid x position format: {x}")
                if y is not None:
                    self.assertTrue(y.endswith('pt'), f"Text element {i+1} has invalid y position format: {y}")

        # Verify text contents to ensure the order matches our input
        expected_texts = ["First Line", "Second Line", "Third Line"]
        for i, pos in enumerate(positions):
            self.assertEqual(pos['text'], expected_texts[i],
                            f"Text element {i+1} has incorrect content: {pos['text']} (expected: {expected_texts[i]})")

        # Sort positions by y coordinate to check vertical alignment
        sorted_positions = sorted(positions, key=lambda p: float(p['y'].rstrip('pt')))

        # Check that the order is maintained after sorting by vertical position
        for i, pos in enumerate(sorted_positions):
            self.assertEqual(pos['index'], i, f"Text element order doesn't match vertical position ordering")

        # Verify that y positions are increasing (each text is below the previous)
        for i in range(1, len(sorted_positions)):
            y_prev = float(sorted_positions[i-1]['y'].rstrip('pt'))
            y_curr = float(sorted_positions[i]['y'].rstrip('pt'))

            self.assertGreater(y_curr, y_prev,
                f"Text element {sorted_positions[i]['index']+1} (y={y_curr}pt) should be positioned below " +
                f"element {sorted_positions[i-1]['index']+1} (y={y_prev}pt)")

            # Optional: Check vertical spacing is consistent
            if i > 1:
                spacing_prev = float(sorted_positions[i-1]['y'].rstrip('pt')) - float(sorted_positions[i-2]['y'].rstrip('pt'))
                spacing_curr = y_curr - y_prev
                self.assertAlmostEqual(spacing_curr, spacing_prev, delta=0.1,
                    msg=f"Vertical spacing between elements {i} and {i+1} ({spacing_curr}pt) differs from " +
                        f"spacing between elements {i-1} and {i} ({spacing_prev}pt)")

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

        # With no conversion, the original image filename should be in the archive
        original_filename = os.path.basename(IMAGE1)
        self.assertIn(original_filename, file_list, f"Original image {original_filename} not found in LBX")

    def test_07_text_and_image(self):
        """Test creating a label with text that's exactly to the right of an image with no gap."""
        output_file = os.path.join(OUTPUT_DIR, "07_text_and_image.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Text Touching Image's Left Edge",
            "--image", IMAGE1,
            "--margin", "0",  # No margin between image and text
            "--side-by-side",  # Position text side-by-side with image
            "--size", "24"
        )
        file_list = self._verify_lbx_file(output_file)

        # With no conversion, the original image filename should be in the archive
        original_filename = os.path.basename(IMAGE1)
        self.assertIn(original_filename, file_list, f"Original image {original_filename} not found in LBX")

        # Verify text is positioned exactly to the right of the image with no gap
        extract_dir = os.path.join(OUTPUT_DIR, os.path.splitext(os.path.basename(output_file))[0])
        label_xml_path = os.path.join(extract_dir, "label.xml")
        self.assertTrue(os.path.exists(label_xml_path), "label.xml not found in extracted LBX")

        # Parse the label XML
        import xml.etree.ElementTree as ET
        namespaces = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
            'image': 'http://schemas.brother.info/ptouch/2007/lbx/image',
        }

        tree = ET.parse(label_xml_path)
        root = tree.getroot()

        # Find the image and text objects
        image_objs = root.findall('.//image:image', namespaces)
        text_objs = root.findall('.//text:text', namespaces)

        self.assertEqual(len(image_objs), 1, "Expected exactly 1 image object")
        self.assertEqual(len(text_objs), 1, "Expected exactly 1 text object")

        # Get positions
        image_style = image_objs[0].find('./pt:objectStyle', namespaces)
        text_style = text_objs[0].find('./pt:objectStyle', namespaces)

        # Make sure the style elements exist
        self.assertIsNotNone(image_style, "Image style element not found")
        self.assertIsNotNone(text_style, "Text style element not found")

        # Only proceed if both styles exist
        if image_style is not None and text_style is not None:
            image_x_attr = image_style.get('x')
            image_width_attr = image_style.get('width')
            image_y_attr = image_style.get('y')
            text_x_attr = text_style.get('x')
            text_y_attr = text_style.get('y')

            # Ensure attributes exist
            self.assertIsNotNone(image_x_attr, "Image x position attribute not found")
            self.assertIsNotNone(image_width_attr, "Image width attribute not found")
            self.assertIsNotNone(image_y_attr, "Image y position attribute not found")
            self.assertIsNotNone(text_x_attr, "Text x position attribute not found")
            self.assertIsNotNone(text_y_attr, "Text y position attribute not found")

            # Only proceed if all attributes exist
            if (image_x_attr is not None and image_width_attr is not None and
                image_y_attr is not None and text_x_attr is not None and
                text_y_attr is not None):

                image_x = float(image_x_attr.replace('pt', ''))
                image_width = float(image_width_attr.replace('pt', ''))
                image_y = float(image_y_attr.replace('pt', ''))
                text_x = float(text_x_attr.replace('pt', ''))
                text_y = float(text_y_attr.replace('pt', ''))

                # Verify horizontal positioning - text is positioned exactly at the right edge of the image
                self.assertEqual(text_x, image_x + image_width,
                                f"Text should be positioned at x={image_x + image_width}pt (image_x + image_width), but is at x={text_x}pt")

                # Verify vertical positioning - text and image have the same y-coordinate
                self.assertEqual(text_y, image_y,
                                f"Text should be aligned vertically with image at y={image_y}pt, but is at y={text_y}pt")

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

        # With no conversion, the original image filenames should be in the archive
        image1_filename = os.path.basename(IMAGE1)
        image2_filename = os.path.basename(IMAGE2)
        self.assertIn(image1_filename, file_list, f"Original image {image1_filename} not found in LBX")
        self.assertIn(image2_filename, file_list, f"Original image {image2_filename} not found in LBX")

        # Now also verify the positioning of the images in the XML
        extract_dir = os.path.join(OUTPUT_DIR, os.path.splitext(os.path.basename(output_file))[0])
        label_xml_path = os.path.join(extract_dir, "label.xml")

        # Check if label.xml exists
        self.assertTrue(os.path.exists(label_xml_path), "label.xml not found in extracted LBX")

        # Parse the label XML
        import xml.etree.ElementTree as ET

        # Define namespaces to properly parse the XML
        namespaces = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
            'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
            'image': 'http://schemas.brother.info/ptouch/2007/lbx/image',
        }

        tree = ET.parse(label_xml_path)
        root = tree.getroot()

        # Find all image objects
        image_objects = root.findall('.//image:image', namespaces)

        # Verify we have exactly 2 image objects
        self.assertEqual(len(image_objects), 2, "Expected exactly 2 image objects")

        # Extract position information from the objectStyle elements
        positions = []
        for i, obj in enumerate(image_objects):
            # Find the objectStyle element
            obj_style = obj.find('./pt:objectStyle', namespaces)
            if obj_style is not None:
                x = obj_style.get('x')
                y = obj_style.get('y')

                # Get image information from imageStyle element
                image_style = obj.find('./image:imageStyle', namespaces)
                image_name = "Unknown"
                if image_style is not None:
                    image_name = image_style.get('originalName', f"Unknown image in element {i+1}")

                positions.append({
                    'index': i,
                    'x': x,
                    'y': y,
                    'image': image_name
                })

                # Verify that x and y attributes exist and have valid pt values
                self.assertIsNotNone(x, f"Image element {i+1} is missing x position")
                self.assertIsNotNone(y, f"Image element {i+1} is missing y position")
                if x is not None:
                    self.assertTrue(x.endswith('pt'), f"Image element {i+1} has invalid x position format: {x}")
                if y is not None:
                    self.assertTrue(y.endswith('pt'), f"Image element {i+1} has invalid y position format: {y}")

        # Sort positions by y coordinate to check vertical alignment
        sorted_positions = sorted(positions, key=lambda p: float(p['y'].rstrip('pt')))

        # Verify that y positions are increasing (each image is below the previous)
        for i in range(1, len(sorted_positions)):
            y_prev = float(sorted_positions[i-1]['y'].rstrip('pt'))
            y_curr = float(sorted_positions[i]['y'].rstrip('pt'))

            self.assertGreater(y_curr, y_prev,
                f"Image element {sorted_positions[i]['index']+1} (y={y_curr}pt) should be positioned below " +
                f"element {sorted_positions[i-1]['index']+1} (y={y_prev}pt)")

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

        # With no conversion, the original image filenames should be in the archive
        image1_filename = os.path.basename(IMAGE1)
        image2_filename = os.path.basename(IMAGE2)
        self.assertIn(image1_filename, file_list, f"Original image {image1_filename} not found in LBX")
        self.assertIn(image2_filename, file_list, f"Original image {image2_filename} not found in LBX")

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

        # With no conversion, the original image filenames should be in the archive
        image1_filename = os.path.basename(IMAGE1)
        image2_filename = os.path.basename(IMAGE2)
        self.assertIn(image1_filename, file_list, f"Original image {image1_filename} not found in LBX")
        self.assertIn(image2_filename, file_list, f"Original image {image2_filename} not found in LBX")

    def test_14_image_conversion(self):
        """Test image conversion to BMP format."""
        output_file = os.path.join(OUTPUT_DIR, "14_image_conversion.lbx")
        self._run_lbx_create(
            output_file,
            "--text", "Converted Image Test",
            "--image", IMAGE1,
            "--image", IMAGE2,
            "--convert-images",  # Explicitly convert to BMP
            "--size", "24"
        )
        file_list = self._verify_lbx_file(output_file)

        # When convert_images is true, images should be converted to BMP
        # and named with Object*.bmp pattern
        bmp_count = 0
        original_image1 = os.path.basename(IMAGE1)
        original_image2 = os.path.basename(IMAGE2)

        # Check for BMP files and make sure original filenames are NOT there
        for fname in file_list:
            if fname.startswith("Object") and fname.endswith(".bmp"):
                bmp_count += 1
            # Original filenames should not be present
            self.assertNotEqual(fname, original_image1, "Original image should not be in LBX when converting")
            self.assertNotEqual(fname, original_image2, "Original image should not be in LBX when converting")

        # Verify we have the right number of converted images
        self.assertEqual(bmp_count, 2, "Expected exactly 2 BMP files in LBX when using --convert-images")

        # Verify the XML structure includes references to the converted filenames
        extract_dir = os.path.join(OUTPUT_DIR, os.path.splitext(os.path.basename(output_file))[0])
        label_xml_path = os.path.join(extract_dir, "label.xml")
        self.assertTrue(os.path.exists(label_xml_path), "label.xml not found in extracted LBX")

        # Parse the label XML
        import xml.etree.ElementTree as ET
        namespaces = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'image': 'http://schemas.brother.info/ptouch/2007/lbx/image',
        }

        tree = ET.parse(label_xml_path)
        root = tree.getroot()

        # Verify that image references in XML have the proper structure
        image_styles = root.findall('.//image:imageStyle', namespaces)
        self.assertEqual(len(image_styles), 2, "Expected 2 image style elements in XML")

        for image_style in image_styles:
            filename = image_style.get('fileName')
            self.assertIsNotNone(filename, "fileName attribute missing in imageStyle")
            if filename is not None:
                self.assertTrue(filename.startswith("Object") and filename.endswith(".bmp"),
                               f"Converted image filename {filename} doesn't match expected pattern")

            # Should still have original filename stored in originalName attribute
            original_name = image_style.get('originalName')
            self.assertIsNotNone(original_name, "originalName attribute missing in imageStyle")
            self.assertIn(original_name, [original_image1, original_image2],
                         f"originalName {original_name} not found in expected values")


if __name__ == "__main__":
    unittest.main()