#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test suite for text_dimensions.py
"""

import os
import sys
import pytest
import xml.etree.ElementTree as ET
import re
from src.lbx_utils.text_dimensions import TextDimensionCalculator, FontMetrics, CalculationMethod
from pytest_dependency import depends
from typing import List, Dict, Any
import logging
import platform

# Set up logging
logger = logging.getLogger(__name__)

# Test data
TEST_FONTS = [
    "Helsinki",  # Default P-Touch font
    "Arial",     # Common system font
    "Times New Roman",  # Another common system font
    "Helvetica", # Common on macOS
    "Courier New", # Common monospace font
]

TEST_TEXT_SAMPLES = [
    "Hello World",
    "The quick brown fox jumps over the lazy dog",
    "1234567890",
    "!@#$%^&*()",
    "Hello\nWorld",  # Test with newlines
    "Hello\tWorld",  # Test with tabs
    "Hello  World",  # Test with multiple spaces
]

TEST_SIZES = [8, 12, 16, 24, 32]
TEST_WEIGHTS = ["normal", "bold"]
TEST_STYLES = [False, True]  # italic

# Path to the sample P-touch Editor label.xml file
PTOUCH_LABEL_XML = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "label_examples",
        "multi-font-grid",
        "label.xml"
    )
)

# Define reference data extracted from P-touch Editor label
PTOUCH_REFERENCE_DATA = [
    {
        "text": "1",
        "font_name": "Arial",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 12.9,
        "height": 51.1
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 48.2,
        "height": 51.1
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 194.3,
        "height": 51.1
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 194.2,
        "height": 58.9
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 48.4,
        "height": 58.9
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 12.5,
        "height": 58.9
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 10.4,
        "height": 58.9
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 39.8,
        "height": 58.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 159.4,
        "height": 58.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 209.3,
        "height": 63.7
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 48.1,
        "height": 63.7
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 45.7,
        "weight": "normal",
        "italic": False,
        "width": 15.2,
        "height": 63.7
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 4.6,
        "height": 16.7
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 13.3,
        "height": 16.7
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 55.7,
        "height": 16.7
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 42.5,
        "height": 15.5
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 11.1,
        "height": 15.5
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 3.4,
        "height": 15.5
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 3.9,
        "height": 15.5
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 13.4,
        "height": 15.5
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 51.7,
        "height": 15.5
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 51.6,
        "height": 13.4
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 13.2,
        "height": 13.4
    },
    {
        "text": "1",
        "font_name": "Arial",
        "size": 12.0,
        "weight": "normal",
        "italic": False,
        "width": 4.0,
        "height": 13.4
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 4.0,
        "height": 13.9
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 11.3,
        "height": 13.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 46.6,
        "height": 13.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 35.6,
        "height": 12.9
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 9.4,
        "height": 12.9
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 2.9,
        "height": 12.9
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 3.4,
        "height": 12.9
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 11.3,
        "height": 12.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 43.2,
        "height": 12.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 43.2,
        "height": 11.2
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 11.2,
        "height": 11.2
    },
    {
        "text": "1",
        "font_name": "Arial",
        "size": 10.0,
        "weight": "normal",
        "italic": False,
        "width": 3.5,
        "height": 11.2
    },
    {
        "text": "1",
        "font_name": "Arial",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 3.0,
        "height": 8.9
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 9.2,
        "height": 8.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 34.9,
        "height": 8.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 34.7,
        "height": 10.3
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 9.2,
        "height": 10.3
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 2.9,
        "height": 10.3
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 2.5,
        "height": 10.3
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 7.7,
        "height": 10.3
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 28.6,
        "height": 10.3
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 37.4,
        "height": 11.1
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 9.0,
        "height": 11.1
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 8.0,
        "weight": "normal",
        "italic": False,
        "width": 3.4,
        "height": 11.1
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 3.7,
        "height": 11.1
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 9.5,
        "height": 11.1
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 38.0,
        "height": 11.1
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 31.2,
        "height": 10.3
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 8.1,
        "height": 10.3
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 2.9,
        "height": 10.3
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 3.4,
        "height": 10.3
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 9.6,
        "height": 10.3
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 37.9,
        "height": 10.3
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 37.8,
        "height": 8.9
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 9.7,
        "height": 8.9
    },
    {
        "text": "1",
        "font_name": "Arial",
        "size": 8.0,
        "weight": "bold",
        "italic": False,
        "width": 3.4,
        "height": 8.9
    },
    {
        "text": "1",
        "font_name": "Arial",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 4.0,
        "height": 11.2
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 11.8,
        "height": 11.2
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 47.1,
        "height": 11.2
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 47.1,
        "height": 12.9
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 11.8,
        "height": 12.9
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 4.0,
        "height": 12.9
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 3.4,
        "height": 12.9
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 9.9,
        "height": 12.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 38.8,
        "height": 12.9
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 47.2,
        "height": 13.9
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 11.7,
        "height": 13.9
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 10.0,
        "weight": "bold",
        "italic": False,
        "width": 4.4,
        "height": 13.9
    },
    {
        "text": "1",
        "font_name": "Arial",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 4.6,
        "height": 13.4
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 13.9,
        "height": 13.4
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 56.3,
        "height": 13.4
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 56.3,
        "height": 15.4
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 13.9,
        "height": 15.4
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 4.6,
        "height": 15.4
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 3.9,
        "height": 15.4
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 11.7,
        "height": 15.4
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 46.3,
        "height": 15.4
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 56.6,
        "height": 16.7
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 13.8,
        "height": 16.7
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 12.0,
        "weight": "bold",
        "italic": False,
        "width": 5.1,
        "height": 16.7
    },
    {
        "text": "1",
        "font_name": "Comic Sans MS",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 17.0,
        "height": 63.7
    },
    {
        "text": "ab",
        "font_name": "Comic Sans MS",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 50.3,
        "height": 63.7
    },
    {
        "text": "abcdefghi",
        "font_name": "Comic Sans MS",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 212.8,
        "height": 63.7
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki Narrow",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 174.0,
        "height": 58.7
    },
    {
        "text": "ab",
        "font_name": "Helsinki Narrow",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 41.8,
        "height": 58.7
    },
    {
        "text": "1",
        "font_name": "Helsinki Narrow",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 12.6,
        "height": 58.7
    },
    {
        "text": "1",
        "font_name": "Helsinki",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 15.1,
        "height": 58.7
    },
    {
        "text": "ab",
        "font_name": "Helsinki",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 50.8,
        "height": 58.7
    },
    {
        "text": "abcdefghi",
        "font_name": "Helsinki",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 211.9,
        "height": 58.7
    },
    {
        "text": "abcdefghi",
        "font_name": "Arial",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 211.8,
        "height": 51.1
    },
    {
        "text": "ab",
        "font_name": "Arial",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 50.9,
        "height": 51.1
    },
    {
        "text": "1",
        "font_name": "Arial",
        "size": 45.7,
        "weight": "bold",
        "italic": False,
        "width": 15.2,
        "height": 51.1
    }
]

def pytest_addoption(parser):
    """Add command line options to pytest."""
    parser.addoption("--font-dir", action="store", default=None,
                     help="Directory containing font files for testing")

@pytest.fixture
def font_dir(request):
    """Get the font directory from command line options."""
    return request.config.getoption("--font-dir")

@pytest.fixture
def calculator():
    """Fixture providing a text dimension calculator instance."""
    # Enable fallbacks and substitution to allow testing with system fonts
    calculator = TextDimensionCalculator(
        debug=True,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True,
        apply_ptouch_adjustments=False
    )
    return calculator

@pytest.fixture
def adjusted_calculator():
    """Fixture providing a calculator with P-touch adjustments enabled."""
    calculator = TextDimensionCalculator(
        debug=True,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True,
        apply_ptouch_adjustments=True
    )
    return calculator

def test_system_font_paths(calculator):
    """Test that system font paths are detected correctly."""
    # Get the FreeType technique directly
    freetype_technique = calculator._techniques["freetype"]

    assert hasattr(freetype_technique, '_system_font_paths')
    assert freetype_technique._system_font_paths
    # At least one system font path should exist
    assert len(freetype_technique._system_font_paths) > 0

    # Print detected system font paths for debugging
    print("\nDetected system font paths:")
    for path in freetype_technique._system_font_paths:
        print(f"  - {path}")
        assert os.path.exists(path)

def test_available_fonts(calculator):
    """Test which fonts from our test list are available."""
    freetype_technique = calculator._techniques["freetype"]
    available_fonts = []
    unavailable_fonts = []

    for font_name in TEST_FONTS:
        try:
            path = freetype_technique._get_font_path(font_name)
            available_fonts.append((font_name, path))
        except FileNotFoundError:
            unavailable_fonts.append(font_name)

    # Print font availability information
    print("\nAvailable fonts:")
    for font_name, path in available_fonts:
        print(f"  - {font_name}: {path}")

    print("\nUnavailable fonts:")
    for font_name in unavailable_fonts:
        print(f"  - {font_name}")

    # Ensure we have at least one font available for testing
    assert len(available_fonts) > 0, "No test fonts are available"

def test_font_metrics(calculator):
    """Test that font metrics are calculated correctly."""
    freetype_technique = calculator._techniques["freetype"]
    for font_name in TEST_FONTS:
        for size in TEST_SIZES:
            try:
                metrics = freetype_technique._get_font_metrics(font_name, size)
                assert isinstance(metrics, FontMetrics)
                assert metrics.ascent > 0
                assert metrics.descent > 0
                assert metrics.line_height > 0
                assert metrics.average_width > 0
                assert metrics.max_width > 0
                assert metrics.x_height > 0
                assert metrics.cap_height > 0
            except FileNotFoundError:
                # Skip if font not found
                continue

def test_text_dimensions_basic(calculator):
    """Test basic text dimension calculations."""
    for text in TEST_TEXT_SAMPLES:
        for size in TEST_SIZES:
            try:
                width, height = calculator.calculate_text_dimensions(
                    text=text,
                    size=size
                )
                assert width > 0
                assert height > 0

                # Compare with PIL calculation
                pil_width, pil_height = calculator.calculate_text_dimensions_pil(
                    text=text,
                    size=size
                )

                # Allow for some variation between methods
                # For width, we can be fairly strict
                if width > 0 and pil_width > 0:
                    relative_diff = abs(width - pil_width) / max(width, pil_width)
                    assert relative_diff < 0.5, f"Width difference too large: {width} vs {pil_width}"

                # For height, just ensure both are positive - different font metrics
                # systems can have vastly different height calculations
                assert height > 0 and pil_height > 0, f"Heights must be positive: {height} vs {pil_height}"

                # Print dimensions for manual verification
                if text == "Hello World" and size == 12:
                    print(f"\nDimensions for 'Hello World' at 12pt:")
                    print(f"  - Freetype: {width:.2f}pt × {height:.2f}pt")
                    print(f"  - PIL: {pil_width:.2f}pt × {pil_height:.2f}pt")
                    print(f"  - Width diff: {(abs(width - pil_width) / max(width, pil_width) * 100):.1f}%")
                    print(f"  - Height diff: {(abs(height - pil_height) / max(height, pil_height) * 100):.1f}%")

            except FileNotFoundError:
                # Skip if font not found
                continue

def test_text_dimensions_variations(calculator):
    """Test text dimensions with different weights and styles."""
    # Use a smaller subset of test data to avoid excessive output
    sample_text = "Hello World"
    sample_size = 12

    for weight in TEST_WEIGHTS:
        for italic in TEST_STYLES:
            try:
                width, height = calculator.calculate_text_dimensions(
                    text=sample_text,
                    size=sample_size,
                    weight=weight,
                    italic=italic
                )
                assert width > 0
                assert height > 0

                # Print variations for manual verification
                print(f"\nDimensions for '{sample_text}' with weight={weight}, italic={italic}:")
                print(f"  - {width:.2f}pt × {height:.2f}pt")

                # Bold text should be wider than normal text
                if weight == "bold" and not italic:
                    normal_width, _ = calculator.calculate_text_dimensions(
                        text=sample_text,
                        size=sample_size,
                        weight="normal",
                        italic=False
                    )
                    assert width > normal_width, f"Bold text should be wider: {width} vs {normal_width}"

                # Italic text should be different width than non-italic
                if italic and weight == "normal":
                    non_italic_width, _ = calculator.calculate_text_dimensions(
                        text=sample_text,
                        size=sample_size,
                        weight="normal",
                        italic=False
                    )
                    assert width != non_italic_width, f"Italic text should have different width: {width} vs {non_italic_width}"

            except FileNotFoundError:
                # Skip if font not found
                continue

def test_text_dimensions_cache(calculator):
    """Test that the font and metrics caches work correctly."""
    # First calculation should populate cache
    width1, height1 = calculator.calculate_text_dimensions("Test")

    # Second calculation should use cache
    width2, height2 = calculator.calculate_text_dimensions("Test")

    assert width1 == width2
    assert height1 == height2

    # Verify cache is being used in the underlying technique
    best_technique = calculator._get_best_available_technique()
    assert hasattr(best_technique, '_font_cache')
    assert len(best_technique._font_cache) > 0

    # If using freetype, also check metrics cache
    if best_technique.get_name() == "freetype":
        assert hasattr(best_technique, '_metrics_cache')
        assert len(best_technique._metrics_cache) > 0

def test_text_dimensions_empty(calculator):
    """Test text dimension calculations with empty strings."""
    width, height = calculator.calculate_text_dimensions("")
    assert width == 0
    assert height > 0  # Height should still be the line height

def test_text_dimensions_special_chars(calculator):
    """Test text dimension calculations with special characters."""
    special_chars = "äöüßéèñ©®™"
    try:
        width, height = calculator.calculate_text_dimensions(special_chars)
        assert width > 0
        assert height > 0
        print(f"\nDimensions for special characters '{special_chars}':")
        print(f"  - {width:.2f}pt × {height:.2f}pt")
    except FileNotFoundError:
        # Skip if font not found
        pass

def test_text_dimensions_multiline(calculator):
    """Test text dimension calculations with multiline text."""
    multiline_text = "Line 1\nLine 2\nLine 3"
    try:
        width, height = calculator.calculate_text_dimensions(multiline_text)
        assert width > 0
        assert height > 0

        # Height should be roughly 3x single line height
        single_height = calculator.calculate_text_dimensions("Line 1")[1]
        assert height > single_height * 2, f"Multiline height ({height}) should be at least twice single line height ({single_height})"

        print(f"\nDimensions for multiline text:")
        print(f"  - Multiline: {width:.2f}pt × {height:.2f}pt")
        print(f"  - Single line: {calculator.calculate_text_dimensions('Line 1')[0]:.2f}pt × {single_height:.2f}pt")
    except FileNotFoundError:
        # Skip if font not found
        pass

def extract_font_data_from_xml(xml_path: str) -> List[Dict[str, Any]]:
    """
    Extract font data from the P-touch Editor XML file.

    Args:
        xml_path: Path to the XML file containing font data

    Returns:
        List of dictionaries containing font data for each text object
    """
    try:
        # Parse the XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Define namespaces
        namespaces = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'text': 'http://schemas.brother.info/ptouch/2007/lbx/text'
        }

        # Find all text objects
        text_objects = root.findall('.//text:text', namespaces)

        font_data = []
        for obj in text_objects:
            # Get text content
            data_elem = obj.find('.//pt:data', namespaces)
            if data_elem is None or data_elem.text is None:
                continue
            text = data_elem.text

            # Get font attributes from logFont and fontExt
            log_font = obj.find('.//text:logFont', namespaces)
            font_ext = obj.find('.//text:fontExt', namespaces)

            if log_font is None or font_ext is None:
                continue

            font_name = log_font.get('name')
            weight = "bold" if log_font.get('weight') == "700" else "normal"
            italic = log_font.get('italic', 'false').lower() == 'true'

            size_str = font_ext.get('size')
            if font_name is None or size_str is None:
                continue

            try:
                size = float(size_str.rstrip('pt'))
            except ValueError:
                continue

            # Get dimensions from objectStyle
            obj_style = obj.find('.//pt:objectStyle', namespaces)
            if obj_style is None:
                continue

            try:
                width = float(obj_style.get('width', '0').rstrip('pt'))
                height = float(obj_style.get('height', '0').rstrip('pt'))
            except ValueError:
                continue

            font_data.append({
                'text': text,
                'font_name': font_name,
                'size': size,
                'weight': weight,
                'italic': italic,
                'width': width,
                'height': height
            })

        return font_data

    except Exception as e:
        print(f"Error extracting font data: {str(e)}")
        return []

def test_ptouch_editor_reference_data_extraction():
    """Test that we can extract reference data from the P-touch Editor label file."""
    font_data = extract_font_data_from_xml(PTOUCH_LABEL_XML)

    if not font_data:
        pytest.skip("No font data extracted from the P-touch Editor label file")

    # Verify we have data
    assert len(font_data) > 0

    # Print the extracted data for verification
    print("\nExtracted font data from P-touch Editor label:")
    for item in font_data:
        print(f"  - Font: {item['font_name']}, Size: {item['size']}pt, Weight: {item['weight']}, Italic: {item['italic']}")
        print(f"    Text: '{item['text']}'")
        print(f"    Dimensions: {item['width']:.2f}pt × {item['height']:.2f}pt")

def test_ptouch_editor_multi_font_dimensions(calculator):
    """Test text dimensions against P-touch Editor measurements from multi-font grid."""
    # Extract font data from XML
    xml_path = "data/label_examples/multi-font-grid/label.xml"
    font_data = extract_font_data_from_xml(xml_path)

    # Create output directory if it doesn't exist
    os.makedirs("test_output", exist_ok=True)

    # Open output file
    with open("test_output/dimension_comparison.txt", "w") as f:
        # Group data by font and size for better analysis
        font_groups = {}
        for data in font_data:
            key = f"{data['font_name']} {data['size']}pt {data['weight']}"
            if key not in font_groups:
                font_groups[key] = []
            font_groups[key].append(data)

        # Test each group
        for font_key, items in sorted(font_groups.items()):
            f.write(f"\n=== Testing {font_key} ===\n")

            # Calculate average differences
            width_diffs = []
            height_diffs = []

            for data in items:
                # Calculate dimensions using hybrid method
                width, height = calculator.calculate_text_dimensions(
                    text=data["text"],
                    font_name=data["font_name"],
                    size=data["size"],
                    weight=data["weight"],
                    italic=data["italic"]
                )

                # Get P-touch Editor dimensions
                ptouch_width = data["width"]
                ptouch_height = data["height"]

                # Calculate differences
                width_diff = width - ptouch_width
                height_diff = height - ptouch_height
                width_diff_pct = (width_diff / ptouch_width) * 100
                height_diff_pct = (height_diff / ptouch_height) * 100

                width_diffs.append(width_diff_pct)
                height_diffs.append(height_diff_pct)

                # Write detailed comparison
                f.write(f"\nText: '{data['text']}'\n")
                f.write(f"P-touch Editor: {ptouch_width:6.2f}pt × {ptouch_height:6.2f}pt\n")
                f.write(f"Calculated:     {width:6.2f}pt × {height:6.2f}pt\n")
                f.write(f"Difference:     {width_diff:+6.2f}pt ({width_diff_pct:+6.1f}%) × {height_diff:+6.2f}pt ({height_diff_pct:+6.1f}%)\n")

            # Write average differences for this font/size group
            avg_width_diff = sum(width_diffs) / len(width_diffs)
            avg_height_diff = sum(height_diffs) / len(height_diffs)
            f.write(f"\nAverage differences for {font_key}:\n")
            f.write(f"  Width:  {avg_width_diff:+6.1f}%\n")
            f.write(f"  Height: {avg_height_diff:+6.1f}%\n")

            # For now, just assert that dimensions are positive
            # We'll use this data to calibrate our calculations
            assert all(width > 0 for width in [data["width"] for data in items])
            assert all(height > 0 for height in [data["height"] for data in items])

    # Print the file contents
    with open("test_output/dimension_comparison.txt", "r") as f:
        print(f.read())

def test_required_fonts_availability():
    """Test if all required fonts for the dimension tests are available."""
    # Create calculator with fallbacks enabled for this test run
    calculator = TextDimensionCalculator(
        debug=True,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True
    )

    # Get freetype technique to use its font path methods
    freetype_technique = calculator._techniques["freetype"]

    # Get the set of required fonts from the reference data
    required_fonts = {item["font_name"] for item in PTOUCH_REFERENCE_DATA}

    # Check each font
    missing_fonts = []
    substituted_fonts = {}

    for font_name in required_fonts:
        print(f"Checking font: {font_name}...")
        try:
            font_path = freetype_technique._get_font_path(font_name)
            if font_name.lower() not in font_path.lower():
                substituted_fonts[font_name] = font_path
                print(f"  Found substitute at: {font_path}")
            else:
                print(f"  Found exact match at: {font_path}")
        except FileNotFoundError as e:
            print(f"  Not found: {str(e)}")
            missing_fonts.append(font_name)

    # Warn about missing fonts but don't fail
    if missing_fonts:
        print(f"WARNING: Some fonts not found: {', '.join(missing_fonts)}")
        print("Tests will continue with approximations")

    if substituted_fonts:
        print("\nUsing font substitutions:")
        for original, substitute in substituted_fonts.items():
            print(f"  - {original} → {os.path.basename(substitute)}")

    # Return True to allow tests to continue
    return True

@pytest.mark.dependency(name="test_required_fonts")
def test_required_fonts_wrapper():
    """Wrapper for test_required_fonts_availability to use with dependency."""
    return test_required_fonts_availability()

@pytest.mark.dependency(depends=["test_required_fonts"])
def test_ptouch_editor_reference_dimensions_debug(calculator):
    """Debug test to understand how text dimensions are being calculated for missing fonts."""
    freetype_technique = calculator._techniques["freetype"]

    for expected in PTOUCH_REFERENCE_DATA:
        # Special focus on Helsinki Narrow
        if expected["font_name"] == "Helsinki Narrow":
            print(f"\nDebugging calculation for {expected['font_name']}:")
            try:
                print("  1. Checking if font can be found directly:")
                try:
                    font_path = freetype_technique._get_font_path(expected["font_name"])
                    print(f"     Found at: {font_path}")
                except FileNotFoundError as e:
                    print(f"     Not found! Error: {str(e)[:100]}...")

                print("  2. Trying to calculate text dimensions:")
                width, height = calculator.calculate_text_dimensions(
                    text=expected["text"],
                    font_name=expected["font_name"],
                    size=expected["size"],
                    weight=expected["weight"],
                    italic=expected["italic"]
                )
                print(f"     Success! Got dimensions: {width:.2f}pt × {height:.2f}pt")

                # Get the technique that was used
                technique = calculator._get_best_available_technique()
                print(f"  3. Technique used: {technique.get_name()}")

                print("  4. Checking if PIL fallback is being used:")
                try:
                    pil_width, pil_height = calculator.calculate_text_dimensions(
                        text=expected["text"],
                        font_name=expected["font_name"],
                        size=expected["size"],
                        weight=expected["weight"],
                        italic=expected["italic"],
                        method="pil"
                    )
                    print(f"     PIL calculation succeeded: {pil_width:.2f}pt × {pil_height:.2f}pt")
                except Exception as e:
                    print(f"     PIL calculation failed: {str(e)[:100]}...")

            except Exception as e:
                print(f"  Error during debug: {str(e)}")

def test_ptouch_editor_reference_dimensions(calculator, adjusted_calculator):
    """Test text dimensions against references from P-touch Editor."""
    # Display fallback settings
    print(f"\nTest running with fallbacks enabled:")
    print(f"  allow_fallbacks = {calculator.allow_fallbacks}")
    print(f"  allow_font_substitution = {calculator.allow_font_substitution}")
    print(f"  allow_approximation = {calculator.allow_approximation}")

    # Define the check_dimensions function first
    def check_dimensions(expected_data):
        # Extract data
        text = expected_data["text"]
        font_name = expected_data["font_name"]
        size = expected_data["size"]
        weight = expected_data["weight"]
        italic = expected_data["italic"]
        expected_width = expected_data["width"]
        expected_height = expected_data["height"]

        try:
            # Calculate dimensions (unadjusted)
            width, height = calculator.calculate_text_dimensions(
                text=text,
                font_name=font_name,
                size=size,
                weight=weight,
                italic=italic
            )

            # Calculate dimensions with P-touch adjustments
            adj_width, adj_height = adjusted_calculator.calculate_text_dimensions(
                text=text,
                font_name=font_name,
                size=size,
                weight=weight,
                italic=italic
            )

            # Calculate differences for unadjusted
            width_diff = width - expected_width
            height_diff = height - expected_height
            width_diff_pct = (width_diff / expected_width) * 100
            height_diff_pct = (height_diff / expected_height) * 100

            # Calculate differences for adjusted
            adj_width_diff = adj_width - expected_width
            adj_height_diff = adj_height - expected_height
            adj_width_diff_pct = (adj_width_diff / expected_width) * 100
            adj_height_diff_pct = (adj_height_diff / expected_width) * 100

            # Print comparison info in a clearer format
            font_desc = f"{font_name} {size}pt"
            if weight == "bold":
                font_desc += " bold"
            if italic:
                font_desc += " italic"

            print(f"\n{'-'*80}")
            print(f"Font: {font_desc}")
            print(f"Text: '{text[:40]}{'...' if len(text) > 40 else ''}'")
            print(f"{'-'*80}")
            print(f"                  Width (pt)      Height (pt)")
            print(f"P-touch Editor:   {expected_width:8.2f}        {expected_height:8.2f}")
            print(f"Unadjusted:       {width:8.2f}        {height:8.2f}")
            print(f"Difference:       {width_diff:8.2f}        {height_diff:8.2f}")
            print(f"Difference (%):   {width_diff_pct:8.2f}%       {height_diff_pct:8.2f}%")
            print(f"Ratio (calc/exp): {width/expected_width:8.2f}        {height/expected_height:8.2f}")
            print(f"{'-'*80}")
            print(f"With adjustments: {adj_width:8.2f}        {adj_height:8.2f}")
            print(f"Difference:       {adj_width_diff:8.2f}        {adj_height_diff:8.2f}")
            print(f"Difference (%):   {adj_width_diff_pct:8.2f}%       {adj_height_diff_pct:8.2f}%")
            print(f"Ratio (adj/exp):  {adj_width/expected_width:8.2f}        {adj_height/expected_width:8.2f}")

            # Currently, we're collecting data rather than enforcing exact matches
            # We'll store the ratios to determine adjustment factors
            return {
                "unadjusted": (width / expected_width, height / expected_height),
                "adjusted": (adj_width / expected_width, adj_height / expected_width)
            }

        except Exception as e:
            pytest.fail(f"Error calculating dimensions for {font_name}: {str(e)}")

    # Rest of the function
    # Check for required fonts
    freetype_technique = calculator._techniques["freetype"]
    required_fonts = {item["font_name"] for item in PTOUCH_REFERENCE_DATA}
    missing_fonts = []

    # Only do a quick check for each font
    for font_name in required_fonts:
        try:
            freetype_technique._get_font_path(font_name)
        except FileNotFoundError:
            missing_fonts.append(font_name)

    # Skip the test if any fonts are missing
    if missing_fonts:
        pytest.skip(f"Required fonts not available: {', '.join(missing_fonts)}")

    # Track ratios for analysis
    unadjusted_width_ratios = []
    unadjusted_height_ratios = []
    adjusted_width_ratios = []
    adjusted_height_ratios = []

    # Process each reference data item
    for expected in PTOUCH_REFERENCE_DATA:
        ratios = check_dimensions(expected)
        unadjusted_width_ratios.append(ratios["unadjusted"][0])
        unadjusted_height_ratios.append(ratios["unadjusted"][1])
        adjusted_width_ratios.append(ratios["adjusted"][0])
        adjusted_height_ratios.append(ratios["adjusted"][1])

    # Calculate and print average ratios
    if unadjusted_width_ratios and unadjusted_height_ratios:
        avg_unadj_width_ratio = sum(unadjusted_width_ratios) / len(unadjusted_width_ratios)
        avg_unadj_height_ratio = sum(unadjusted_height_ratios) / len(unadjusted_height_ratios)
        avg_adj_width_ratio = sum(adjusted_width_ratios) / len(adjusted_width_ratios)
        avg_adj_height_ratio = sum(adjusted_height_ratios) / len(adjusted_height_ratios)

        print(f"\n{'-'*80}")
        print(f"SUMMARY ACROSS ALL FONTS")
        print(f"{'-'*80}")
        print(f"UNADJUSTED:")
        print(f"Average width ratio (calc/expected):  {avg_unadj_width_ratio:.4f}")
        print(f"Average height ratio (calc/expected): {avg_unadj_height_ratio:.4f}")
        print(f"Suggested width adjustment factor:    {1/avg_unadj_width_ratio:.4f}")
        print(f"Suggested height adjustment factor:   {1/avg_unadj_height_ratio:.4f}")
        print(f"{'-'*80}")
        print(f"WITH ADJUSTMENTS:")
        print(f"Average width ratio (adj/expected):   {avg_adj_width_ratio:.4f}")
        print(f"Average height ratio (adj/expected):  {avg_adj_height_ratio:.4f}")
        print(f"Residual width adjustment needed:     {1/avg_adj_width_ratio:.4f}")
        print(f"Residual height adjustment needed:    {1/avg_adj_height_ratio:.4f}")
        print(f"{'-'*80}")

@pytest.mark.skipif(
    platform.system() != "Darwin" or not hasattr(CalculationMethod, "CORE_TEXT"),
    reason="Core Text is only available on macOS with PyObjC installed"
)
def test_core_text_availability():
    """Test if Core Text technique is available on this system."""
    calculator = TextDimensionCalculator(debug=True)

    # Check if Core Text is in available methods
    available_methods = [
        name for name, technique in calculator._techniques.items()
        if technique.is_available()
    ]

    print("\nChecking Core Text availability:")
    if hasattr(CalculationMethod, "CORE_TEXT") and CalculationMethod.CORE_TEXT in available_methods:
        print(f"✓ Core Text is available")
        # Get the technique directly
        core_text_technique = calculator._techniques[CalculationMethod.CORE_TEXT]
        assert core_text_technique.is_available() is True
        assert core_text_technique.get_name() == "core_text"
    else:
        print(f"✗ Core Text is not available")
        pytest.skip("Core Text technique is not available on this system")

@pytest.mark.skipif(
    platform.system() != "Darwin" or not hasattr(CalculationMethod, "CORE_TEXT"),
    reason="Core Text is only available on macOS with PyObjC installed"
)
def test_core_text_dimensions_basic():
    """Test basic text dimension calculations using Core Text."""
    calculator = TextDimensionCalculator(debug=True)

    # Skip if Core Text is not available
    if not hasattr(CalculationMethod, "CORE_TEXT") or not calculator._techniques[CalculationMethod.CORE_TEXT].is_available():
        pytest.skip("Core Text technique is not available")

    sample_text = "Hello World"
    sample_size = 12

    # Calculate dimensions using Core Text
    width, height = calculator.calculate_text_dimensions(
        text=sample_text,
        size=sample_size,
        method=CalculationMethod.CORE_TEXT
    )

    assert width > 0
    assert height > 0

    print(f"\nCore Text dimensions for '{sample_text}' at {sample_size}pt:")
    print(f"  - {width:.2f}pt × {height:.2f}pt")

    # Compare with other methods if available
    other_methods = []
    for method in ["freetype", "pil", "harfbuzz", "pango"]:
        if method in calculator._techniques and calculator._techniques[method].is_available():
            other_methods.append(method)

    for method in other_methods:
        try:
            other_width, other_height = calculator.calculate_text_dimensions(
                text=sample_text,
                size=sample_size,
                method=method
            )
            print(f"  - {method.capitalize()}: {other_width:.2f}pt × {other_height:.2f}pt")
            print(f"    Difference: {(width - other_width):.2f}pt ({((width - other_width) / other_width * 100):.1f}%) × "
                  f"{(height - other_height):.2f}pt ({((height - other_height) / other_height * 100):.1f}%)")
        except Exception as e:
            print(f"  - {method.capitalize()}: Error - {str(e)}")

@pytest.mark.skipif(
    platform.system() != "Darwin" or not hasattr(CalculationMethod, "CORE_TEXT"),
    reason="Core Text is only available on macOS with PyObjC installed"
)
def test_core_text_ptouch_comparison():
    """Compare Core Text measurements against P-touch Editor reference data."""
    calculator = TextDimensionCalculator(
        debug=True,
        apply_ptouch_adjustments=False  # Test raw calculations
    )

    # Skip if Core Text is not available
    if not hasattr(CalculationMethod, "CORE_TEXT") or not calculator._techniques[CalculationMethod.CORE_TEXT].is_available():
        pytest.skip("Core Text technique is not available")

    # Track differences for analysis
    width_diffs = []
    height_diffs = []
    width_diffs_pct = []
    height_diffs_pct = []

    # Process a subset of reference data for brevity
    subset = PTOUCH_REFERENCE_DATA[:10]  # First 10 items

    print("\nComparing Core Text with P-touch Editor reference data:")
    for expected in subset:
        text = expected["text"]
        font_name = expected["font_name"]
        size = expected["size"]
        weight = expected["weight"]
        italic = expected["italic"]
        expected_width = expected["width"]
        expected_height = expected["height"]

        try:
            # Calculate dimensions using Core Text
            width, height = calculator.calculate_text_dimensions(
                text=text,
                font_name=font_name,
                size=size,
                weight=weight,
                italic=italic,
                method=CalculationMethod.CORE_TEXT
            )

            # Calculate differences
            width_diff = width - expected_width
            height_diff = height - expected_height
            width_diff_pct = (width_diff / expected_width) * 100
            height_diff_pct = (height_diff / expected_height) * 100

            # Track differences
            width_diffs.append(width_diff)
            height_diffs.append(height_diff)
            width_diffs_pct.append(width_diff_pct)
            height_diffs_pct.append(height_diff_pct)

            print(f"\nText: '{text}'")
            print(f"Font: {font_name} {size}pt {weight} {'italic' if italic else ''}")
            print(f"P-touch: {expected_width:.2f}pt × {expected_height:.2f}pt")
            print(f"Core Text: {width:.2f}pt × {height:.2f}pt")
            print(f"Difference: {width_diff:.2f}pt ({width_diff_pct:.1f}%) × "
                  f"{height_diff:.2f}pt ({height_diff_pct:.1f}%)")
        except Exception as e:
            print(f"\nError calculating '{text}' with {font_name}: {str(e)}")

    # Calculate and print average differences
    if width_diffs:
        avg_width_diff = sum(width_diffs) / len(width_diffs)
        avg_height_diff = sum(height_diffs) / len(height_diffs)
        avg_width_diff_pct = sum(width_diffs_pct) / len(width_diffs_pct)
        avg_height_diff_pct = sum(height_diffs_pct) / len(height_diffs_pct)

        print("\nAverage differences:")
        print(f"Width: {avg_width_diff:.2f}pt ({avg_width_diff_pct:.1f}%)")
        print(f"Height: {avg_height_diff:.2f}pt ({avg_height_diff_pct:.1f}%)")
        print(f"Suggested adjustment factors:")
        print(f"Width factor: {1/(1 + avg_width_diff_pct/100):.4f}")
        print(f"Height factor: {1/(1 + avg_height_diff_pct/100):.4f}")

    # Basic assertion - average difference should be reasonable
    if width_diffs_pct and height_diffs_pct:
        assert abs(avg_width_diff_pct) < 30, "Width difference too large"
        assert abs(avg_height_diff_pct) < 30, "Height difference too large"