#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
import os
import tempfile
from src.lbx_utils.parser.yaml_parser import YamlParser
from src.lbx_utils.models import TextObject, ImageObject, BarcodeObject, GroupObject

class TestYamlParserShortcuts(unittest.TestCase):
    """Test the YAML parser's support for shortcut syntax."""

    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = self.temp_dir.name

    def tearDown(self):
        """Clean up temporary files."""
        self.temp_dir.cleanup()

    def _create_test_yaml(self, yaml_content):
        """Create a temporary YAML file with the given content."""
        yaml_path = os.path.join(self.test_dir, "test.lbx.yml")
        with open(yaml_path, "w") as f:
            f.write(yaml_content)
        return yaml_path

    def test_text_shortcut(self):
        """Test the text shortcut syntax."""
        yaml_content = """
size: 24mm
width: 90mm
orientation: landscape

objects:
  - text: "Hello World"
    x: 10
    y: 10
    size: 12
    bold: true
"""
        yaml_path = self._create_test_yaml(yaml_content)
        parser = YamlParser(yaml_path)
        config = parser.parse()

        # Verify that a text object was created
        self.assertEqual(len(config.objects), 1)
        self.assertIsInstance(config.objects[0], TextObject)
        self.assertEqual(config.objects[0].text, "Hello World")

    def test_image_shortcut(self):
        """Test the image shortcut syntax."""
        yaml_content = """
size: 24mm
width: 90mm
orientation: landscape

objects:
  - image: "logo.png"
    x: 10
    y: 10
    width: 50
    height: 30
"""
        yaml_path = self._create_test_yaml(yaml_content)
        parser = YamlParser(yaml_path)
        config = parser.parse()

        # Verify that an image object was created
        self.assertEqual(len(config.objects), 1)
        self.assertIsInstance(config.objects[0], ImageObject)
        self.assertEqual(config.objects[0].file_path, "logo.png")

    def test_qr_shortcut(self):
        """Test the QR code shortcut syntax."""
        yaml_content = """
size: 24mm
width: 90mm
orientation: landscape

objects:
  - qr: "https://example.com"
    x: 10
    y: 10
    size: 30
    errorCorrection: H
"""
        yaml_path = self._create_test_yaml(yaml_content)
        parser = YamlParser(yaml_path)
        config = parser.parse()

        # Verify that a barcode object was created with QR type
        self.assertEqual(len(config.objects), 1)
        self.assertIsInstance(config.objects[0], BarcodeObject)
        self.assertEqual(config.objects[0].type, "qr")
        self.assertEqual(config.objects[0].data, "https://example.com")

    def test_barcode_shortcut(self):
        """Test the barcode shortcut syntax."""
        yaml_content = """
size: 24mm
width: 90mm
orientation: landscape

objects:
  - barcode: "123456789012"
    x: 10
    y: 10
    width: 70
    height: 20
    barcodeType: "code128"
    humanReadable: true
"""
        yaml_path = self._create_test_yaml(yaml_content)
        parser = YamlParser(yaml_path)
        config = parser.parse()

        # Verify that a barcode object was created
        self.assertEqual(len(config.objects), 1)
        self.assertIsInstance(config.objects[0], BarcodeObject)
        self.assertEqual(config.objects[0].data, "123456789012")
        self.assertEqual(config.objects[0].type, "code128")

    def test_group_shortcut(self):
        """Test the group shortcut syntax."""
        yaml_content = """
size: 24mm
width: 90mm
orientation: landscape

objects:
  - group: "header"
    x: 10
    y: 10
    direction: row
    align: center
    objects:
      - text: "Header Text"
        size: 12
"""
        yaml_path = self._create_test_yaml(yaml_content)
        parser = YamlParser(yaml_path)
        config = parser.parse()

        # Verify that a group object was created
        self.assertEqual(len(config.objects), 1)
        self.assertIsInstance(config.objects[0], GroupObject)
        self.assertEqual(config.objects[0].name, "header")

        # Verify the nested object
        self.assertEqual(len(config.objects[0].objects), 1)
        self.assertIsInstance(config.objects[0].objects[0], TextObject)
        self.assertEqual(config.objects[0].objects[0].text, "Header Text")

    def test_mixed_objects(self):
        """Test a mix of shortcut and standard syntax."""
        yaml_content = """
size: 24mm
width: 90mm
orientation: landscape

objects:
  - text: "Shortcut Syntax"
    x: 10
    y: 10
    size: 12

  - type: text
    content: "Standard Syntax"
    x: 10
    y: 30
    size: 12
"""
        yaml_path = self._create_test_yaml(yaml_content)
        parser = YamlParser(yaml_path)
        config = parser.parse()

        # Verify both objects were created
        self.assertEqual(len(config.objects), 2)
        self.assertIsInstance(config.objects[0], TextObject)
        self.assertIsInstance(config.objects[1], TextObject)
        self.assertEqual(config.objects[0].text, "Shortcut Syntax")
        self.assertEqual(config.objects[1].text, "Standard Syntax")


if __name__ == "__main__":
    unittest.main()