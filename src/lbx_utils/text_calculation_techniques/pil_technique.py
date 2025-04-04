#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PIL-based text dimension calculation technique.
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any

from .base import BaseCalculationTechnique
from .freetype_technique import FreetypeTechnique

# Configure logger
logger = logging.getLogger(__name__)

# Import PIL conditionally
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    logger.warning("PIL module not found. Please install with: pip install Pillow")
    Image = ImageDraw = ImageFont = None


class PILTechnique(BaseCalculationTechnique):
    """
    Text dimension calculation technique using PIL (Pillow).
    """

    def __init__(self, debug: bool = False, font_dir: Optional[str] = None):
        """
        Initialize the PIL calculation technique.

        Args:
            debug: Enable debug logging
            font_dir: Optional directory to look for fonts
        """
        super().__init__(debug, font_dir)
        # We'll use the FreeType technique for font path discovery
        self._freetype_technique = FreetypeTechnique(debug, font_dir)

    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        return "pil"

    def is_available(self) -> bool:
        """Check if PIL library is available."""
        return ImageFont is not None

    def _apply_adjustments(self, width: float, height: float, font_name: str, font_size: float, text: Optional[str] = None) -> tuple[float, float]:
        """Apply font-specific adjustments to the calculated dimensions."""
        # Base height factor on font size and font
        width_factor = 1.0
        height_factor = 1.0

        if font_name.lower().startswith('arial'):
            if font_size <= 12:
                height_factor = 0.6  # Reduce height more for small sizes
            elif font_size <= 24:
                height_factor = 0.7  # Medium reduction for medium sizes
            else:
                height_factor = 1.2  # Increase height for large sizes
            width_factor = 1.1 if font_size <= 12 else 1.0
        elif font_name.lower().startswith('comic sans ms'):
            height_factor = 1.15  # Consistent height adjustment
            width_factor = 0.6  # Reduce width more aggressively
        elif font_name.lower().startswith('helsinki'):
            if font_size <= 12:
                height_factor = 0.7  # Reduce height for small sizes
            elif font_size <= 24:
                height_factor = 0.9  # Small reduction for medium sizes
            else:
                height_factor = 2.0  # Large increase for large sizes
            if 'narrow' in font_name.lower():
                width_factor = 1.0
            else:
                width_factor = 1.1

        # Special handling for single characters
        if text and len(text.strip()) == 1:
            width_factor *= 0.5

        return width * width_factor, height * height_factor

    def calculate_dimensions(
        self,
        text: str,
        font_name: str,
        size: float,
        weight: str = "normal",
        italic: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate the dimensions of a text string using PIL.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        if not ImageFont:
            raise ImportError("PIL ImageFont is not available")

        if not text:
            # Empty string has zero width but still has line height
            return (0, size * 1.2)  # Approximation for empty string height

        try:
            # Try to load the font, using FreeType technique to find font path
            font_path = self._freetype_technique._get_font_path(font_name)
            font = ImageFont.truetype(font_path, int(size))

            # Handle multiline text
            lines = text.split("\n")
            max_width = 0
            total_height = 0

            for line in lines:
                # PIL's text size measurement has different methods in different versions
                # Try the newer getbbox method first, then fall back to older methods
                if hasattr(font, 'getbbox'):
                    bbox = font.getbbox(line)
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                elif hasattr(font, 'getsize'):
                    # For older Pillow versions
                    # Note: getsize is deprecated in newer versions
                    width, height = font.getsize(line)  # type: ignore
                else:
                    # If neither method is available, fall back to approximation
                    char_width_factor = 0.6
                    if 'narrow' in font_name.lower():
                        char_width_factor = 0.5
                    width = len(line) * size * char_width_factor
                    height = size * 1.2

                max_width = max(max_width, width)
                total_height += height

            # Add a small margin between lines
            if len(lines) > 1:
                total_height += (len(lines) - 1) * (size * 0.1)

            # Adjust for weight and italic if needed
            if weight == "bold":
                max_width *= 1.05  # Slight width increase for bold
            if italic:
                max_width *= 1.02  # Slight width increase for italic

            # Apply font-specific adjustments
            max_width, total_height = self._apply_adjustments(
                max_width, total_height, font_name, size, text
            )

            if self.debug:
                logger.debug(f"PIL text '{text}' dimensions: {max_width}pt × {total_height}pt")

            return (max_width, total_height)

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with PIL: {str(e)}")
            raise