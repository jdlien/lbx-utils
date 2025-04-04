#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple script to test the text dimension calculator with the new modular approach.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.lbx_utils.text_dimensions import TextDimensionCalculator, CalculationMethod

def test_text(text, font="Helsinki", size=12.0, weight="normal", italic=False):
    print(f"\nTesting: '{text}' with {font} {size}pt {weight}{' italic' if italic else ''}")

    # Create calculator with all techniques
    calculator = TextDimensionCalculator(debug=True, apply_ptouch_adjustments=False)

    # Test with all methods and compare
    for method in [CalculationMethod.AUTO, CalculationMethod.FREETYPE, CalculationMethod.PIL, CalculationMethod.APPROXIMATION]:
        try:
            width, height = calculator.calculate_text_dimensions(
                text=text,
                font_name=font,
                size=size,
                weight=weight,
                italic=italic,
                method=method
            )
            print(f"{method.value.capitalize()}: {width:.2f}pt × {height:.2f}pt")
        except Exception as e:
            print(f"{method.value.capitalize()}: Failed - {str(e)}")

def main():
    # Test with different fonts, text, and styles
    test_text("Hello, World!")
    test_text("This is a longer text with multiple words to test wrapping and sizing.")
    test_text("UPPERCASE TEXT", size=16.0)
    test_text("Bold text", weight="bold")
    test_text("Italic text", italic=True)
    test_text("Bold Italic", weight="bold", italic=True)
    test_text("Multiline\nText\nWith\nFour\nLines")
    test_text("1234567890")
    test_text("Special Chars: äöüßéèñ©®™")

    # Test with different fonts
    for font in ["Arial", "Times New Roman", "Helvetica", "Courier New"]:
        test_text(f"Test with {font}", font=font)

if __name__ == "__main__":
    main()