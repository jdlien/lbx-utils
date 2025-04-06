#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
text_dimensions.py - Calculate text dimensions for P-Touch Editor labels

This module provides functionality to calculate the dimensions of text objects
for Brother P-Touch Editor labels. It uses font metrics and rendering to estimate
the width and height of text with various fonts, sizes, and styles.

The module supports multiple calculation techniques including:
- Skia (primary and most accurate)
- CoreText (macOS only)
- HarfBuzz
- Pango
- FreeType
- PIL (Pillow)
- Basic approximation (fallback)

Key features:
- Automatic selection of the best available technique
- Fallback mechanisms if a technique fails
- Adjustment factors to improve accuracy
- Linear regression models (y = mx + b) for superior dimension adjustments
- Font-specific considerations
"""

import os
import sys
import glob
import platform
import re
from typing import Dict, Tuple, Optional, List, Union, Any, Type
from enum import Enum
import logging

# Import all available calculation techniques
from .text_calculation_techniques import (
    BaseCalculationTechnique,
    FreetypeTechnique,
    PILTechnique,
    ApproximationTechnique,
    HarfbuzzTechnique,
    PangoTechnique,
    FontMetrics,
    SkiaTechnique
)

# Import CoreTextTechnique conditionally if on macOS
if platform.system() == "Darwin":
    try:
        from .text_calculation_techniques import CoreTextTechnique
    except ImportError:
        # CoreTextTechnique may not be available if PyObjC is not installed
        pass

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CalculationMethod(str, Enum):
    """Enum for text dimension calculation methods."""
    FREETYPE = "freetype"
    PIL = "pil"
    HARFBUZZ = "harfbuzz"
    PANGO = "pango"
    SKIA = "skia"
    APPROXIMATION = "approximation"
    AUTO = "auto"  # Automatically choose the best available method

    # Core Text is only available on macOS
    if platform.system() == "Darwin":
        CORE_TEXT = "core_text"


# Suggested adjustment factors derived from comparison with P-touch Editor
# These are the adjustment factors that should be applied to each technique
# to get dimensions closest to P-touch Editor
TECHNIQUE_ADJUSTMENT_FACTORS = {
    "core_text": (1.0133, 1.0477),  # width factor, height factor
    "freetype": (1.0344, 1.0148),
    "pil": (1.0514, 1.4295),
    "harfbuzz": (0.9519, 1.1503),
    "pango": (0.6325, 0.8037),
    "skia": (0.8387, 1.0524),  # Based on comparing with reference data from P-Touch Editor
    "approximation": (1.0798, 0.9977)
}

# Linear regression models derived from comparison with P-touch Editor
# These models have the form: pte_dimension = slope * calculated_dimension + intercept
# Format: (width_slope, width_intercept, height_slope, height_intercept)
# These provide more accurate results than simple multiplicative factors
# as they account for both proportional scaling and fixed offsets
TECHNIQUE_LINEAR_MODELS = {
    "core_text": (1.0399, -0.9584, 1.0757, 0.1283),
    "freetype": (0.9283, 0.2314, 1.3215, -6.9473),
    "pil": (0.9548, -0.1119, 0.7720, 8.2653),
    "harfbuzz": (0.9923, -1.0583, 1.1366, 0.7479),
    "pango": (0.7225, -1.0913, 0.8028, 0.4032),
    "skia": (0.9909, -1.4195, 1.0596, -0.0070),
    "approximation": (0.8956, 2.0682, 0.9939, 0.0729)
}


class TextDimensionCalculator:
    """
    Calculator for determining text dimensions based on font metrics.
    """

    def __init__(
        self,
        font_dir: Optional[str] = None,
        debug: bool = False,
        allow_fallbacks: bool = True,
        allow_font_substitution: bool = True,
        allow_approximation: bool = True,
        apply_ptouch_adjustments: bool = False,
        apply_technique_adjustments: bool = False,
        default_method: Optional[CalculationMethod] = None,
        use_linear_adjustments: bool = True
    ):
        """
        Initialize the calculator.

        Args:
            font_dir: Optional directory to look for fonts
            debug: Enable debug logging
            allow_fallbacks: Whether to use fallback methods if primary method fails
            allow_font_substitution: Whether to try system font substitution
            allow_approximation: Whether to use rough approximation as last resort
            apply_ptouch_adjustments: Whether to apply P-touch Editor specific adjustments
            apply_technique_adjustments: Whether to apply technique-specific adjustment factors
            default_method: Default calculation method to use (None for auto-selection)
            use_linear_adjustments: Whether to use linear regression models for adjustments
                                   (more accurate than simple multiplicative factors)
        """
        # Look for a fonts/ directory in the repository root if font_dir is not specified
        if font_dir is None:
            # Try to find the repository root by looking for common directories/files
            repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            potential_font_dir = os.path.join(repo_root, "fonts")

            if os.path.isdir(potential_font_dir):
                font_dir = potential_font_dir
                if debug:
                    logger.debug(f"Using repository fonts directory: {font_dir}")

        self.font_dir = font_dir
        self.debug = debug
        self.allow_fallbacks = allow_fallbacks
        self.allow_font_substitution = allow_font_substitution
        self.allow_approximation = allow_approximation
        self.apply_ptouch_adjustments = apply_ptouch_adjustments
        self.apply_technique_adjustments = apply_technique_adjustments
        self.use_linear_adjustments = use_linear_adjustments

        # Set default method - use Skia on all platforms as it's the most accurate
        if default_method is None:
            self.default_method = CalculationMethod.SKIA
        else:
            self.default_method = default_method

        # Legacy font-specific adjustment factors for P-touch Editor
        self.font_specific_factors = {
            'Helsinki': (1.0828, 0.9972),
            'Helsinki Narrow': (0.8155, 0.9196),
            'Arial': (0.7951, 0.8889),
            'default': (0.92, 0.93)  # Default for other fonts
        }

        # Legacy global adjustment factors (kept for backward compatibility)
        self.ptouch_width_factor = 1.09 * 0.9979  # Multiply calculated width by this
        self.ptouch_height_factor = 0.37 * 1.0028  # Multiply calculated height by this

        if debug:
            logger.setLevel(logging.DEBUG)

        # Initialize calculation techniques
        self._techniques = self._initialize_techniques()

        if self.debug:
            available_methods = [name for name, technique in self._techniques.items()
                                if technique.is_available()]
            logger.debug(f"Available calculation methods: {available_methods}")

    def _initialize_techniques(self) -> Dict[str, BaseCalculationTechnique]:
        """Initialize all available calculation techniques."""
        techniques = {}

        # Initialize freetype technique
        techniques[CalculationMethod.FREETYPE] = FreetypeTechnique(
            debug=self.debug,
            font_dir=self.font_dir
        )

        # Initialize PIL technique
        techniques[CalculationMethod.PIL] = PILTechnique(
            debug=self.debug,
            font_dir=self.font_dir
        )

        # Initialize HarfBuzz technique
        techniques[CalculationMethod.HARFBUZZ] = HarfbuzzTechnique(
            debug=self.debug,
            font_dir=self.font_dir
        )

        # Initialize Pango technique
        techniques[CalculationMethod.PANGO] = PangoTechnique(
            debug=self.debug,
            font_dir=self.font_dir
        )

        # Initialize Skia technique
        techniques[CalculationMethod.SKIA] = SkiaTechnique(
            debug=self.debug,
            font_dir=self.font_dir
        )

        # Initialize approximation technique
        techniques[CalculationMethod.APPROXIMATION] = ApproximationTechnique(
            debug=self.debug,
            font_dir=self.font_dir
        )

        # Initialize Core Text technique if available (macOS only)
        if platform.system() == "Darwin" and hasattr(CalculationMethod, "CORE_TEXT"):
            try:
                techniques[CalculationMethod.CORE_TEXT] = CoreTextTechnique(
                    debug=self.debug,
                    font_dir=self.font_dir
                )
            except (ImportError, NameError):
                # CoreTextTechnique may not be available if PyObjC is not installed
                pass

        return techniques

    def _get_best_available_technique(self) -> BaseCalculationTechnique:
        """Get the best available calculation technique based on priority."""
        # Priority order: skia, core_text (if on macOS), harfbuzz, freetype, pango, PIL, approximation
        priorities = [
            CalculationMethod.SKIA,      # Skia is most accurate with P-Touch Editor
        ]

        # Add Core Text as second priority if on macOS
        if platform.system() == "Darwin" and hasattr(CalculationMethod, "CORE_TEXT"):
            priorities.append(CalculationMethod.CORE_TEXT)

        # Add other techniques
        priorities.extend([
            CalculationMethod.HARFBUZZ,  # HarfBuzz for complex text shaping
            CalculationMethod.FREETYPE,  # FreeType for basic font metrics
            CalculationMethod.PANGO,     # Pango for good text layout
            CalculationMethod.PIL,       # PIL as a widely available option
            CalculationMethod.APPROXIMATION
        ])

        for method in priorities:
            technique = self._techniques[method]
            if technique.is_available():
                if self.debug:
                    logger.debug(f"Selected {method} as best available technique")
                return technique

        # If we get here, use approximation as last resort
        if self.debug:
            logger.debug("No suitable technique found, using approximation as fallback")
        return self._techniques[CalculationMethod.APPROXIMATION]

    def _get_technique(self, method: Optional[CalculationMethod] = None) -> BaseCalculationTechnique:
        """
        Get the calculation technique based on the requested method.

        Args:
            method: The calculation method to use, or None to use default

        Returns:
            The appropriate calculation technique
        """
        if method is None:
            method = self.default_method

        if method == CalculationMethod.AUTO:
            return self._get_best_available_technique()

        technique = self._techniques[method]

        # Check if the requested technique is available
        if not technique.is_available():
            if self.allow_fallbacks:
                if self.debug:
                    logger.debug(f"{method} technique not available, falling back to best available")
                return self._get_best_available_technique()
            else:
                raise ImportError(f"{method} calculation technique is not available")

        return technique

    def _apply_ptouch_editor_adjustments(self, width: float, height: float, font_name: str) -> Tuple[float, float]:
        """
        Apply P-touch Editor specific adjustments to dimensions.

        Args:
            width: The calculated width
            height: The calculated height
            font_name: The font name for font-specific adjustments

        Returns:
            Adjusted width and height
        """
        if font_name in self.font_specific_factors:
            width_factor, height_factor = self.font_specific_factors[font_name]
        else:
            width_factor, height_factor = self.font_specific_factors["default"]

        return width * width_factor, height * height_factor

    def _apply_technique_adjustment(self, width: float, height: float, technique_name: str) -> Tuple[float, float]:
        """
        Apply technique-specific adjustment factors to dimensions.

        Two adjustment methods are available:
        1. Simple multiplicative factors (width * factor, height * factor)
        2. Linear regression models (slope * dimension + intercept)

        The linear regression models typically provide more accurate results as they
        account for both proportional scaling and fixed offsets.

        Args:
            width: The calculated width
            height: The calculated height
            technique_name: The name of the calculation technique used

        Returns:
            Adjusted width and height
        """
        if technique_name in TECHNIQUE_ADJUSTMENT_FACTORS and not self.use_linear_adjustments:
            # Use traditional multiplicative adjustment factors
            width_factor, height_factor = TECHNIQUE_ADJUSTMENT_FACTORS[technique_name]
            return width * width_factor, height * height_factor
        elif technique_name in TECHNIQUE_LINEAR_MODELS and self.use_linear_adjustments:
            # Use linear regression models: y = mx + b
            # This typically provides more accurate results as it accounts for
            # both proportional scaling and fixed offsets
            width_slope, width_intercept, height_slope, height_intercept = TECHNIQUE_LINEAR_MODELS[technique_name]
            adjusted_width = width_slope * width + width_intercept
            adjusted_height = height_slope * height + height_intercept
            if self.debug:
                logger.debug(f"Applied linear model for {technique_name}: {width:.2f}pt → {adjusted_width:.2f}pt, {height:.2f}pt → {adjusted_height:.2f}pt")
            return adjusted_width, adjusted_height
        return width, height

    def calculate_text_dimensions(
        self,
        text: str,
        font_name: str = "Helsinki",
        size: float = 12.0,
        weight: str = "normal",
        italic: bool = False,
        method: Optional[CalculationMethod] = None,
        apply_adjustments: Optional[bool] = None,
        use_linear_adjustments: Optional[bool] = None
    ) -> Tuple[float, float]:
        """
        Calculate the dimensions of a text string.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic
            method: Specific calculation method to use (or None for default)
            apply_adjustments: Whether to apply technique adjustments (None to use instance default)
            use_linear_adjustments: Whether to use linear adjustment models (None to use instance default)
                                   When True, uses linear regression models (y = mx + b) which are
                                   more accurate than simple multiplicative factors, especially for
                                   matching P-Touch Editor dimensions

        Returns:
            Tuple of (width, height) in points
        """
        # Use instance default if apply_adjustments is not specified
        if apply_adjustments is None:
            apply_adjustments = self.apply_technique_adjustments

        # Use instance default if use_linear_adjustments is not specified
        if use_linear_adjustments is None:
            use_linear_adjustments = self.use_linear_adjustments

        if not text:
            # Empty string has zero width but still has line height
            try:
                # Use any available technique to get line height
                technique = self._get_technique(method)
                width, height = technique.calculate_dimensions("x", font_name, size, weight, italic)
                return 0, height  # Zero width but preserve line height
            except Exception as e:
                if self.debug:
                    logger.error(f"Error getting line height: {str(e)}")
                return 0, size * 1.2  # Fallback approximation

        # Try the requested or default method first
        try:
            technique = self._get_technique(method)
            technique_name = technique.get_name()
            width, height = technique.calculate_dimensions(
                text=text,
                font_name=font_name,
                size=size,
                weight=weight,
                italic=italic
            )

            if self.debug:
                logger.debug(f"Calculated '{text}' using {technique_name}: {width:.2f}pt × {height:.2f}pt")

            # Apply technique-specific adjustments if requested
            if apply_adjustments:
                original_width, original_height = width, height
                # Store original linear adjustment setting
                orig_linear = self.use_linear_adjustments
                # Use the specified linear adjustment setting
                self.use_linear_adjustments = use_linear_adjustments
                width, height = self._apply_technique_adjustment(width, height, technique_name)
                # Restore original setting
                self.use_linear_adjustments = orig_linear

                if self.debug:
                    logger.debug(f"Applied {technique_name} adjustments: {original_width:.2f}pt × {original_height:.2f}pt -> {width:.2f}pt × {height:.2f}pt")

            # Apply P-touch Editor adjustments if requested
            if self.apply_ptouch_adjustments:
                original_width, original_height = width, height
                width, height = self._apply_ptouch_editor_adjustments(width, height, font_name)
                if self.debug:
                    logger.debug(f"Applied P-touch adjustments: {original_width:.2f}pt × {original_height:.2f}pt -> {width:.2f}pt × {height:.2f}pt")

            return width, height

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with {method}: {str(e)}")

            # If fallbacks are allowed, try other methods
            if self.allow_fallbacks and method != CalculationMethod.AUTO:
                if self.debug:
                    logger.debug("Falling back to AUTO method selection")
                return self.calculate_text_dimensions(
                    text=text,
                    font_name=font_name,
                    size=size,
                    weight=weight,
                    italic=italic,
                    method=CalculationMethod.AUTO,
                    apply_adjustments=apply_adjustments,
                    use_linear_adjustments=use_linear_adjustments
                )

            # If we still can't calculate, use approximation if allowed
            if self.allow_approximation:
                if self.debug:
                    logger.debug("Using approximation as last resort")
                technique = self._techniques[CalculationMethod.APPROXIMATION]
                technique_name = technique.get_name()
                width, height = technique.calculate_dimensions(
                    text=text,
                    font_name=font_name,
                    size=size,
                    weight=weight,
                    italic=italic
                )

                # Apply technique-specific adjustments if requested
                if apply_adjustments:
                    width, height = self._apply_technique_adjustment(width, height, technique_name)

                # Apply P-touch Editor adjustments if requested
                if self.apply_ptouch_adjustments:
                    width, height = self._apply_ptouch_editor_adjustments(width, height, font_name)

                return width, height

            # If we get here, give up and raise the exception
            raise

    # Legacy methods for backward compatibility
    def calculate_text_dimensions_pil(
        self,
        text: str,
        font_name: str = "Helsinki",
        size: float = 12.0,
        weight: str = "normal",
        italic: bool = False,
        apply_adjustments: Optional[bool] = None
    ) -> Tuple[float, float]:
        """
        Calculate text dimensions using PIL as an alternative method.

        This is kept for backward compatibility.
        """
        return self.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic,
            method=CalculationMethod.PIL,
            apply_adjustments=apply_adjustments
        )


# Simple test function for direct use
def main():
    import argparse

    # Create the parser with a more detailed description
    parser = argparse.ArgumentParser(
        description="Calculate text dimensions for P-Touch Editor labels using various techniques",
        epilog="Example: python -m src.lbx_utils.text_dimensions --text 'Hello World' --font 'Helsinki' --size 14 --technique-adjustments --linear-adjustments"
    )

    # Basic text and font options
    parser.add_argument("--text", type=str, required=True, help="Text to measure")
    parser.add_argument("--font", type=str, default="Helsinki", help="Font name")
    parser.add_argument("--size", type=float, default=12.0, help="Font size in points")
    parser.add_argument("--weight", type=str, default="normal", help="Font weight (normal, bold)")
    parser.add_argument("--italic", action="store_true", help="Italic style")

    # Debug and directory options
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--font-dir", type=str, help="Custom font directory")

    # Fallback behavior
    fallback_group = parser.add_argument_group('Fallback Behavior')
    fallback_group.add_argument("--no-fallbacks", action="store_true", help="Disable fallback methods")
    fallback_group.add_argument("--no-substitution", action="store_true", help="Disable font substitution")
    fallback_group.add_argument("--no-approximation", action="store_true", help="Disable approximation fallbacks")

    # Adjustment options
    adjustment_group = parser.add_argument_group('Dimension Adjustments', 'Options for adjusting calculated dimensions')
    adjustment_group.add_argument("--ptouch-adjustments", action="store_true", help="Apply P-touch Editor specific adjustments")
    adjustment_group.add_argument("--technique-adjustments", action="store_true", help="Apply technique-specific adjustment factors")
    adjustment_group.add_argument("--linear-adjustments", action="store_true",
                               help="Use linear regression models (y = mx + b) for adjustments - more accurate")
    adjustment_group.add_argument("--simple-adjustments", action="store_false", dest="linear_adjustments",
                               help="Use simple multiplicative factors for adjustments instead of linear models")

    # Method selection
    method_choices = ["auto", "freetype", "pil", "harfbuzz", "pango", "skia", "approximation"]
    if platform.system() == "Darwin":
        method_choices.append("core_text")

    parser.add_argument("--method", type=str, choices=method_choices,
                        default=None, help="Calculation method to use (default: auto selects Skia if available)")

    args = parser.parse_args()

    # Convert string method to enum if specified
    method_enum = CalculationMethod(args.method) if args.method else None

    calculator = TextDimensionCalculator(
        font_dir=args.font_dir,
        debug=args.debug,
        allow_fallbacks=not args.no_fallbacks,
        allow_font_substitution=not args.no_substitution,
        allow_approximation=not args.no_approximation,
        apply_ptouch_adjustments=args.ptouch_adjustments,
        apply_technique_adjustments=args.technique_adjustments,
        default_method=method_enum,
        use_linear_adjustments=args.linear_adjustments
    )

    try:
        # Calculate dimensions using the specified or default method
        width, height = calculator.calculate_text_dimensions(
            text=args.text,
            font_name=args.font,
            size=args.size,
            weight=args.weight,
            italic=args.italic,
            method=method_enum,
            use_linear_adjustments=args.linear_adjustments
        )

        used_method = args.method if args.method else (
            "skia" if calculator.default_method == CalculationMethod.SKIA else
            "core_text" if calculator.default_method == CalculationMethod.CORE_TEXT else
            "auto"
        )

        # Display results
        print(f"Method: {used_method}")
        if args.technique_adjustments:
            adjustment_type = "linear" if args.linear_adjustments else "simple multiplicative"
            print(f"Adjustment: {adjustment_type}")
        print(f"Dimensions: {width:.2f}pt × {height:.2f}pt")

        # Try each available method for comparison if debug is enabled
        if args.debug:
            available_methods = ["freetype", "pil", "harfbuzz", "pango", "skia", "approximation"]
            if platform.system() == "Darwin":
                available_methods.insert(0, "core_text")

            for method_str in available_methods:
                try:
                    method = CalculationMethod(method_str)
                    technique = calculator._techniques[method]
                    if technique.is_available():
                        # With adjustments
                        m_width, m_height = calculator.calculate_text_dimensions(
                            text=args.text,
                            font_name=args.font,
                            size=args.size,
                            weight=args.weight,
                            italic=args.italic,
                            method=method,
                            apply_adjustments=True,
                            use_linear_adjustments=args.linear_adjustments
                        )

                        # Without adjustments
                        raw_width, raw_height = calculator.calculate_text_dimensions(
                            text=args.text,
                            font_name=args.font,
                            size=args.size,
                            weight=args.weight,
                            italic=args.italic,
                            method=method,
                            apply_adjustments=False
                        )

                        print(f"{method_str.capitalize()} (raw): {raw_width:.2f}pt × {raw_height:.2f}pt")

                        adj_type = "linear" if args.linear_adjustments else "simple"
                        print(f"{method_str.capitalize()} ({adj_type} adjusted): {m_width:.2f}pt × {m_height:.2f}pt")
                except Exception as e:
                    print(f"{method_str.capitalize()}: Error - {str(e)}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()