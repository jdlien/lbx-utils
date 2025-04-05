#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Skia-based text dimension calculation technique.
"""

import os
import logging
from typing import Dict, Tuple, Optional, List, Any

from .base import BaseCalculationTechnique
from .freetype_technique import FreetypeTechnique

# Configure logger
logger = logging.getLogger(__name__)

# Import skia conditionally
try:
    import skia
except ImportError:
    logger.warning("skia-python module not found. Please install with: pip install skia-python")
    skia = None


class SkiaTechnique(BaseCalculationTechnique):
    """
    Text dimension calculation technique using the Skia Graphics Library.

    This technique leverages Skia, the same rendering engine used by Chrome,
    Android, Flutter, and potentially by P-Touch Editor for better text
    dimension measurements.
    """

    def __init__(self, debug: bool = False, font_dir: Optional[str] = None):
        """
        Initialize the Skia calculation technique.

        Args:
            debug: Enable debug logging
            font_dir: Optional directory to look for fonts
        """
        super().__init__(debug, font_dir)
        # Use FreetypeTechnique for font path discovery
        self._freetype_technique = FreetypeTechnique(debug, font_dir)
        self._font_cache: Dict[str, Any] = {}
        self._typeface_cache: Dict[str, Any] = {}

    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        return "skia"

    def is_available(self) -> bool:
        """Check if Skia is available."""
        return skia is not None

    def _get_typeface(self, font_name: str) -> Any:
        """
        Get Skia typeface for the specified font.

        Args:
            font_name: Name of the font

        Returns:
            Skia typeface
        """
        if not skia:
            raise ImportError("skia module is not available")

        if font_name in self._typeface_cache:
            return self._typeface_cache[font_name]

        try:
            # Use FreetypeTechnique to find the font path
            font_path = self._freetype_technique._get_font_path(font_name)

            # Create a Skia typeface from the font file
            typeface = skia.Typeface.MakeFromFile(font_path)

            if typeface is None:
                if self.debug:
                    logger.warning(f"Skia could not create typeface from {font_path}, using default")
                # Fall back to default typeface
                typeface = skia.Typeface()

            self._typeface_cache[font_name] = typeface

            if self.debug:
                logger.debug(f"Created Skia typeface for '{font_name}' from {font_path}")

            return typeface
        except Exception as e:
            if self.debug:
                logger.error(f"Error creating Skia typeface: {str(e)}")
            # Fall back to default typeface
            default_typeface = skia.Typeface()
            self._typeface_cache[font_name] = default_typeface
            return default_typeface

    def calculate_dimensions(
        self,
        text: str,
        font_name: str,
        size: float,
        weight: str = "normal",
        italic: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate the dimensions of a text string using Skia.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        if not skia:
            raise ImportError("skia-python module is not available")

        if not text:
            # Return zero width but some height for empty text
            return 0, size * 1.2

        try:
            # Get typeface
            typeface = self._get_typeface(font_name)

            # Map weight string to Skia weight value
            weight_value = 400
            if weight.lower() == "bold":
                weight_value = 700

            # Create paint with appropriate settings
            paint = skia.Paint()
            paint.setAntiAlias(True)

            # Create font and set it on the paint
            font = skia.Font(typeface, size)

            # Measure lines
            lines = text.split("\n")
            max_width = 0
            total_height = 0

            # Approximate line height as 120% of font size if we can't get it directly
            line_height = size * 1.2

            # Create a paint for measuring
            for line in lines:
                if not line:  # Handle empty lines
                    total_height += line_height
                    continue

                # Get width using the simple measureText method
                width = font.measureText(line)
                max_width = max(max_width, width)
                total_height += line_height

            # Add spacing between lines if multiline
            if len(lines) > 1:
                total_height += (len(lines) - 1) * (size * 0.1)  # Add spacing

            # Apply font-specific adjustments
            max_width, total_height = self._apply_adjustments(
                max_width, total_height, font_name, size, text
            )

            if self.debug:
                logger.debug(f"Text '{text}' dimensions with Skia: {max_width:.2f}pt × {total_height:.2f}pt")

            return max_width, total_height

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with Skia: {str(e)}")

            # Fall back to approximation
            char_width = size * 0.6
            if 'narrow' in font_name.lower():
                char_width = size * 0.5

            lines = text.split("\n")
            max_width = max(len(line) for line in lines) * char_width
            line_height = size * 1.2
            total_height = len(lines) * line_height

            # Apply weight adjustments
            if weight.lower() == "bold":
                max_width *= 1.1

            # Apply italic adjustments
            if italic:
                max_width *= 1.05

            return max_width, total_height

    def _apply_adjustments(self, width: float, height: float, font_name: str, size: float, text: str) -> Tuple[float, float]:
        """
        Apply font-specific adjustments to the calculated dimensions.

        Args:
            width: Calculated width
            height: Calculated height
            font_name: Font name
            size: Font size
            text: Text content

        Returns:
            Adjusted (width, height)
        """
        # Adjustments based on font name
        if 'helsinki' in font_name.lower():
            # Helsinki fonts need slight width adjustment
            width *= 1.05
        elif 'narrow' in font_name.lower():
            # Narrow fonts often need width adjustment
            width *= 0.95

        # No specific height adjustments for now

        return width, height