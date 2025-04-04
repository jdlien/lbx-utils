#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HarfBuzz-based text dimension calculation technique using fontTools.

This technique provides accurate text layout measurements using the HarfBuzz shaping engine
through the fontTools library. It handles complex scripts and advanced typography features.
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any, List

from .base import BaseCalculationTechnique
from .freetype_technique import FreetypeTechnique  # For font path discovery

# Configure logger
logger = logging.getLogger(__name__)

# Import fontTools and uharfbuzz conditionally
try:
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    import uharfbuzz as hb
except ImportError:
    logger.warning("HarfBuzz technique requires fontTools and uharfbuzz. "
                   "Please install with: pip install fonttools uharfbuzz")
    TTFont = None
    BoundsPen = None
    hb = None


class HarfbuzzTechnique(BaseCalculationTechnique):
    """
    Text dimension calculation technique using HarfBuzz with fontTools.

    This technique provides high-quality text layout capabilities, including:
    - Advanced glyph positioning and kerning
    - Support for complex scripts (Arabic, Devanagari, etc.)
    - OpenType feature support (ligatures, contextual alternates, etc.)
    - Accurate text dimension calculations
    """

    def __init__(self, debug: bool = False, font_dir: Optional[str] = None):
        """
        Initialize the HarfBuzz calculation technique.

        Args:
            debug: Enable debug logging
            font_dir: Optional directory to look for fonts
        """
        super().__init__(debug, font_dir)
        # Use FreetypeTechnique for font path discovery
        self._freetype_technique = FreetypeTechnique(debug, font_dir)
        self._font_cache: Dict[str, Any] = {}
        self._ttfont_cache: Dict[str, Any] = {}

    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        return "harfbuzz"

    def is_available(self) -> bool:
        """Check if HarfBuzz and fontTools are available."""
        return TTFont is not None and hb is not None

    def _get_font(self, font_name: str) -> Any:
        """
        Get HarfBuzz font for the specified font.

        Args:
            font_name: Name of the font

        Returns:
            HarfBuzz font
        """
        if font_name in self._font_cache:
            return self._font_cache[font_name]

        try:
            # Use FreetypeTechnique to find the font path
            font_path = self._freetype_technique._get_font_path(font_name)

            # For uharfbuzz 0.48.0, we need to:
            # 1. Read the font data
            with open(font_path, 'rb') as font_file:
                font_data = font_file.read()

            # 2. Create a blob directly
            blob = hb.Blob(font_data)

            # 3. Create a face from the blob
            face = hb.Face(blob, 0)  # Use first font in collection (index 0)

            # 4. Create a font from the face
            font = hb.Font(face)

            # Configure the font with defaults
            upem = face.upem
            font.scale = (upem, upem)

            # Store in cache
            self._font_cache[font_name] = font

            if self.debug:
                logger.debug(f"Created HarfBuzz font for '{font_name}' from {font_path}")

            return font
        except Exception as e:
            if self.debug:
                logger.error(f"Error creating HarfBuzz font: {str(e)}")
            raise

    def _get_ttfont(self, font_name: str) -> Any:
        """
        Get TTFont object for the specified font.

        Args:
            font_name: Name of the font

        Returns:
            TTFont object
        """
        if font_name in self._ttfont_cache:
            return self._ttfont_cache[font_name]

        try:
            # Use FreetypeTechnique to find the font path
            font_path = self._freetype_technique._get_font_path(font_name)

            # Check if this is a TTC (TrueType Collection) file
            is_ttc = font_path.lower().endswith('.ttc')

            # For TTC files, specify the font index
            if is_ttc:
                ttfont = TTFont(font_path, fontNumber=0)  # Use first font in collection
            else:
                ttfont = TTFont(font_path)

            self._ttfont_cache[font_name] = ttfont

            if self.debug:
                logger.debug(f"Loaded TTFont for '{font_name}' from {font_path}")

            return ttfont
        except Exception as e:
            if self.debug:
                logger.error(f"Error loading TTFont: {str(e)}")
            raise

    def _get_font_metrics(self, font_name: str, size: float) -> Tuple[float, float, float]:
        """
        Get basic font metrics (ascent, descent, line height).

        Args:
            font_name: Name of the font
            size: Font size in points

        Returns:
            Tuple of (ascent, descent, line_height) scaled to the requested size
        """
        try:
            ttfont = self._get_ttfont(font_name)

            if 'OS/2' in ttfont:
                os2 = ttfont['OS/2']
                units_per_em = ttfont['head'].unitsPerEm

                # Get metrics from OS/2 table
                ascent = os2.sTypoAscender / units_per_em * size
                descent = abs(os2.sTypoDescender) / units_per_em * size
                line_gap = os2.sTypoLineGap / units_per_em * size
                line_height = ascent + descent + line_gap

                if self.debug:
                    logger.debug(f"Font metrics for {font_name} at {size}pt: "
                                 f"ascent={ascent:.2f}, descent={descent:.2f}, lineHeight={line_height:.2f}")

                return ascent, descent, line_height
            else:
                # Fallback if OS/2 table is not available
                return size * 0.8, size * 0.2, size * 1.2
        except Exception as e:
            if self.debug:
                logger.error(f"Error getting font metrics: {str(e)}")
            # Fallback
            return size * 0.8, size * 0.2, size * 1.2

    def _apply_adjustments(self, width: float, height: float, font_name: str, font_size: float, text: Optional[str] = None) -> Tuple[float, float]:
        """Apply font-specific adjustments to the calculated dimensions."""
        # Base factors
        width_factor = 1.0
        height_factor = 1.0

        if font_name.lower().startswith('arial'):
            if font_size <= 12:
                height_factor = 0.9
            width_factor = 1.0
        elif font_name.lower().startswith('comic sans ms'):
            height_factor = 1.05
            width_factor = 0.95
        elif font_name.lower().startswith('helsinki'):
            if font_size <= 12:
                height_factor = 0.95
            if 'narrow' in font_name.lower():
                width_factor = 0.98
            else:
                width_factor = 1.02

        # Handle single characters differently
        if text and len(text.strip()) == 1:
            width_factor *= 0.9

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
        Calculate the dimensions of a text string using HarfBuzz with fontTools.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        if not hb or not TTFont:
            raise ImportError("HarfBuzz and fontTools libraries are not available")

        if not text:
            # Empty string has zero width but still has line height
            try:
                ascent, descent, line_height = self._get_font_metrics(font_name, size)
                return 0, line_height
            except Exception as e:
                if self.debug:
                    logger.error(f"Error getting font metrics: {str(e)}")
                return 0, size * 1.2  # Fallback approximation

        try:
            # Get font metrics for height calculation
            ascent, descent, line_height = self._get_font_metrics(font_name, size)

            # Split text into lines
            lines = text.split("\n")
            max_width = 0

            # Get scale factor to convert from font units to points
            ttfont = self._get_ttfont(font_name)
            units_per_em = ttfont['head'].unitsPerEm
            scale_factor = size / units_per_em

            # Get HarfBuzz font
            hb_font = self._get_font(font_name)

            # Process each line
            for line in lines:
                if not line:  # Skip empty lines (but count them for height)
                    continue

                # Create buffer
                buf = hb.Buffer()
                buf.add_str(line)

                # Set script, language and direction
                buf.guess_segment_properties()

                # Shape the text
                hb.shape(hb_font, buf)

                # Calculate width based on glyph positions
                try:
                    # Get positions and calculate width
                    line_width = 0
                    positions = buf.glyph_positions
                    for pos in positions:
                        line_width += pos.x_advance

                    # Convert to points
                    line_width *= scale_factor
                    max_width = max(max_width, line_width)
                except Exception as e:
                    if self.debug:
                        logger.error(f"Error calculating line width: {str(e)}")
                    # Fall back to approximation based on character count
                    char_width = size * 0.6
                    if font_name.lower().startswith('arial'):
                        char_width = size * 0.5
                    elif 'narrow' in font_name.lower():
                        char_width = size * 0.45
                    elif 'mono' in font_name.lower() or 'courier' in font_name.lower():
                        char_width = size * 0.6

                    line_width = len(line) * char_width
                    max_width = max(max_width, line_width)

            # Calculate total height based on line count
            total_height = line_height * len(lines)

            # Adjust for weight and italic
            if weight == "bold":
                max_width *= 1.05  # Small adjustment for bold
            if italic:
                max_width *= 1.03  # Small adjustment for italic

            # Apply font-specific adjustments
            max_width, total_height = self._apply_adjustments(
                max_width, total_height, font_name, size, text
            )

            if self.debug:
                logger.debug(f"HarfBuzz text '{text}' dimensions: {max_width:.2f}pt × {total_height:.2f}pt")

            return max_width, total_height

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with HarfBuzz: {str(e)}")
            raise