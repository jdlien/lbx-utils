#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for font name normalization and variation matching.
"""

from src.lbx_utils.text_dimensions import TextDimensionCalculator

def test_font_variations():
    """Test different variations of font names to see if they match."""
    calc = TextDimensionCalculator(debug=True)

    # Test normalization of font names
    print("TESTING FONT NAME NORMALIZATION:")
    print("--------------------------------")
    test_names = [
        "Helsinki Regular",
        "Helsinki-Regular",
        "Helsinki_Regular",
        "Arial Unicode",
        "Arial-Unicode",
        "Arial_Unicode",
        "Times New Roman MT",
        "TimesNewRoman-MT",
        "Times_New_Roman_MT",
        "Helvetica Neue Light",
        "Helvetica-Neue-Light",
        "Helvetica_Neue_Light"
    ]

    for name in test_names:
        normalized = calc._normalize_font_name(name)
        print(f"{name} → {normalized}")

    # Test finding fonts with different name variations
    print("\nTESTING FONT MATCHING WITH VARIATIONS:")
    print("--------------------------------------")
    variation_tests = [
        "Helsinki-Narrow",
        "Helsinki Narrow Regular",
        "Helsinki_Narrow_Regular",
        "Arial Bold",
        "Arial-Bold-Italic",
        "Helvetica Light"
    ]

    for test in variation_tests:
        print(f"\nTesting with name variation: {test}")
        try:
            width, height = calc.calculate_text_dimensions(text='Hello World', font_name=test, size=12.0)
            print(f"Successfully found font. Dimensions: {width:.2f}pt × {height:.2f}pt")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_font_variations()