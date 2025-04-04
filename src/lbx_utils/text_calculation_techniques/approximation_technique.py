#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Approximation-based text dimension calculation technique.

This is a fallback method when more accurate techniques are not available.
"""

import logging
from typing import Tuple, Optional, Dict

from .base import BaseCalculationTechnique

# Configure logger
logger = logging.getLogger(__name__)


class ApproximationTechnique(BaseCalculationTechnique):
    """
    Simple approximation-based text dimension calculation technique.
    """

    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        return "approximation"

    def is_available(self) -> bool:
        """Check if this calculation technique is available."""
        # This technique is always available as it requires no external dependencies
        return True

    def _apply_adjustments(self, width: float, height: float, font_name: str, font_size: float, text: Optional[str] = None) -> tuple[float, float]:
        """Apply font-specific adjustments to the calculated dimensions."""
        width_factor = 1.0
        height_factor = 1.0

        # Font-specific adjustments based on font name
        if font_name.lower().startswith('arial'):
            width_factor = 0.8
            height_factor = 0.9
        elif font_name.lower().startswith('comic sans ms'):
            width_factor = 0.95
            height_factor = 1.15
        elif font_name.lower().startswith('helsinki'):
            if 'narrow' in font_name.lower():
                width_factor = 0.8
            else:
                width_factor = 0.9
            height_factor = 1.1

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
        Calculate the dimensions of a text string using approximation.

        This is a very rough approximation based on some general assumptions about
        font metrics. It should only be used as a last resort when more accurate
        methods are not available.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        if not text:
            # Empty string has zero width but still has line height
            return (0, size * 1.2)

        # Split into lines to handle multi-line text
        lines = text.split("\n")

        # Find the max line length
        max_chars = max(len(line) for line in lines)

        # Basic character width approximation based on font size
        # This assumes a monospace-like width distribution for simplicity
        if 'narrow' in font_name.lower() or 'condensed' in font_name.lower():
            char_width_factor = 0.5  # Narrower fonts
        elif 'mono' in font_name.lower() or 'courier' in font_name.lower():
            char_width_factor = 0.7  # Monospace fonts
        else:
            char_width_factor = 0.6  # Regular fonts

        # Calculate base width and height
        width = max_chars * size * char_width_factor
        height = len(lines) * size * 1.2  # Line height is typically ~120% of font size

        # Adjust for weight and style
        if weight == "bold":
            width *= 1.1  # Bold text is wider
        if italic:
            width *= 1.05  # Italic text is slightly wider

        # Apply font-specific adjustments
        width, height = self._apply_adjustments(width, height, font_name, size, text)

        if self.debug:
            logger.debug(f"Approximation for '{text}': {width:.2f}pt × {height:.2f}pt")

        return (width, height)