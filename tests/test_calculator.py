#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for TextDimensionCalculator.

This script allows testing text dimension calculation with various methods and fonts.
It provides a simple command-line interface for manual testing and comparison.
"""

import sys
import os
# Add the parent directory to sys.path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse
from src.lbx_utils.text_dimensions import TextDimensionCalculator, CalculationMethod

def test_text(text, font_name="Helsinki", size=12.0, weight="normal", italic=False, debug=True):
    """Test text dimensions with all available methods."""
    calculator = TextDimensionCalculator(debug=debug)

    # Try AUTO method (best available)
    try:
        width, height = calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic,
            method=CalculationMethod.AUTO
        )
        print(f"Auto: {width:.2f}pt × {height:.2f}pt")
    except Exception as e:
        print(f"Auto calculation error: {str(e)}")

    # Try each specific method
    for method_name in ["harfbuzz", "freetype", "pil", "pango", "approximation"]:
        try:
            method = CalculationMethod(method_name)
            width, height = calculator.calculate_text_dimensions(
                text=text,
                font_name=font_name,
                size=size,
                weight=weight,
                italic=italic,
                method=method
            )
            # Capitalize method name for display
            display_name = method_name.capitalize()
            if method_name == "pil":
                display_name = "PIL"
            print(f"{display_name}: {width:.2f}pt × {height:.2f}pt")
        except Exception as e:
            print(f"{method_name.capitalize()} error: {str(e)}")

def main():
    """Test various text samples with different fonts and styles."""
    # Test regular text with default Helsinki font
    print("\nTesting: 'Hello, World!' with Helsinki 12.0pt normal")
    test_text("Hello, World!")

    # Test longer text
    print("\nTesting: 'This is a longer text with multiple words to test wrapping and sizing.' with Helsinki 12.0pt normal")
    test_text("This is a longer text with multiple words to test wrapping and sizing.")

    # Test uppercase text with larger font
    print("\nTesting: 'UPPERCASE TEXT' with Helsinki 16.0pt normal")
    test_text("UPPERCASE TEXT", size=16.0)

    # Test different weights and styles
    print("\nTesting: 'Bold text' with Helsinki 12.0pt bold")
    test_text("Bold text", weight="bold")

    print("\nTesting: 'Italic text' with Helsinki 12.0pt normal italic")
    test_text("Italic text", italic=True)

    print("\nTesting: 'Bold Italic' with Helsinki 12.0pt bold italic")
    test_text("Bold Italic", weight="bold", italic=True)

    # Test multiline text
    print("\nTesting: 'Multiline\nText\nWith\nFour\nLines' with Helsinki 12.0pt normal")
    test_text("Multiline\nText\nWith\nFour\nLines")

    # Test numeric text
    print("\nTesting: '1234567890' with Helsinki 12.0pt normal")
    test_text("1234567890")

    # Test special characters
    print("\nTesting: 'Special Chars: äöüßéèñ©®™' with Helsinki 12.0pt normal")
    test_text("Special Chars: äöüßéèñ©®™")

    # Test different fonts
    if os.name == 'posix':  # macOS/Linux
        for font in ["Arial", "Times New Roman", "Helvetica", "Courier New"]:
            print(f"\nTesting: 'Test with {font}' with {font} 12.0pt normal")
            test_text(f"Test with {font}", font_name=font)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test text dimension calculator")
    parser.add_argument("--text", help="Text to measure (optional)")
    parser.add_argument("--font", default="Helsinki", help="Font name")
    parser.add_argument("--size", type=float, default=12.0, help="Font size in points")
    parser.add_argument("--weight", default="normal", choices=["normal", "bold"], help="Font weight")
    parser.add_argument("--italic", action="store_true", help="Use italic style")
    args = parser.parse_args()

    if args.text:
        # Test with provided text
        print(f"\nTesting: '{args.text}' with {args.font} {args.size}pt {args.weight}{' italic' if args.italic else ''}")
        test_text(args.text, args.font, args.size, args.weight, args.italic)
    else:
        # Run all tests
        main()