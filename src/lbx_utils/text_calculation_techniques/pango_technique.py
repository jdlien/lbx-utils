#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pango/Cairo-based text dimension calculation technique.

This technique provides accurate text layout measurements using the Pango library
with Cairo for rendering. It handles complex scripts, bidirectional text,
and various font features.
"""

import os
import logging
from typing import Tuple, Optional, Dict, Any, List, cast

from .base import BaseCalculationTechnique

# Configure logger
logger = logging.getLogger(__name__)

# Define variables at module level to avoid linter errors
Pango = None
PangoCairo = None
cairo = None
PANGO_AVAILABLE = False

# Import Pango and Cairo conditionally
try:
    import gi
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')

    # Capture any error, not just ImportError
    try:
        # Import modules only in try block to prevent linter errors about unknown imports
        from gi.repository import Pango as PangoModule
        from gi.repository import PangoCairo as PangoCairoModule
        import cairo as cairoModule

        # Assign to module level variables
        Pango = PangoModule
        PangoCairo = PangoCairoModule
        cairo = cairoModule
        PANGO_AVAILABLE = True
    except (ImportError, AssertionError, Exception) as e:
        logger.warning(f"Failed to import Pango/Cairo modules: {str(e)}")
        PANGO_AVAILABLE = False

except Exception as e:
    logger.warning(f"Pango technique requires PyGObject, Pango, and Cairo: {str(e)}")
    PANGO_AVAILABLE = False


class PangoTechnique(BaseCalculationTechnique):
    """
    Text dimension calculation technique using Pango with Cairo.

    This technique provides high-quality text layout capabilities, including:
    - Advanced OpenType feature support
    - Bidirectional text handling
    - Complex script support (Arabic, Indic scripts, etc.)
    - Accurate line breaking
    """

    def __init__(self, debug: bool = False, font_dir: Optional[str] = None):
        """
        Initialize the Pango calculation technique.

        Args:
            debug: Enable debug logging
            font_dir: Optional directory to look for fonts
        """
        super().__init__(debug, font_dir)
        self._font_desc_cache: Dict[str, Any] = {}
        self._layout_cache: Dict[str, Any] = {}

    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        return "pango"

    def is_available(self) -> bool:
        """Check if Pango and Cairo are available."""
        return PANGO_AVAILABLE and Pango is not None and cairo is not None

    def _get_font_description(self, font_name: str, size: float, weight: str, italic: bool) -> Any:
        """
        Get a Pango font description for the specified font.

        Args:
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Pango.FontDescription
        """
        if not self.is_available() or Pango is None:
            raise ImportError("Pango is not available")

        cache_key = f"{font_name}:{size}:{weight}:{italic}"
        if cache_key in self._font_desc_cache:
            return self._font_desc_cache[cache_key]

        try:
            # Create font description
            font_desc = Pango.FontDescription()
            font_desc.set_family(font_name)

            # Safely access SCALE attribute
            scale = getattr(Pango, 'SCALE', 1024)  # Default value if attribute doesn't exist
            font_desc.set_size(int(size * scale))

            # Set weight - safely access Weight attributes
            if hasattr(Pango, 'Weight'):
                Weight = Pango.Weight
                if weight == "bold":
                    font_desc.set_weight(getattr(Weight, 'BOLD', 700))
                else:
                    font_desc.set_weight(getattr(Weight, 'NORMAL', 400))
            else:
                # Fallback using numeric values
                if weight == "bold":
                    font_desc.set_weight(700)  # BOLD
                else:
                    font_desc.set_weight(400)  # NORMAL

            # Set style - safely access Style attributes
            if hasattr(Pango, 'Style'):
                Style = Pango.Style
                if italic:
                    font_desc.set_style(getattr(Style, 'ITALIC', 2))
                else:
                    font_desc.set_style(getattr(Style, 'NORMAL', 0))
            else:
                # Fallback using numeric values
                if italic:
                    font_desc.set_style(2)  # ITALIC
                else:
                    font_desc.set_style(0)  # NORMAL

            # Cache the font description
            self._font_desc_cache[cache_key] = font_desc

            return font_desc
        except Exception as e:
            if self.debug:
                logger.error(f"Error creating Pango font description: {str(e)}")
            raise

    def calculate_dimensions(
        self,
        text: str,
        font_name: str,
        size: float,
        weight: str = "normal",
        italic: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate the dimensions of a text string using Pango with Cairo.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        if not self.is_available() or Pango is None or cairo is None or PangoCairo is None:
            raise ImportError("Pango and Cairo libraries are not available")

        if not text:
            # For empty strings, return zero width and default line height
            try:
                if not hasattr(cairo, 'FORMAT_ARGB32'):
                    return 0, size * 1.2  # Fallback if format not available

                # Create a layout to get the line height
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
                context = cairo.Context(surface)
                layout = PangoCairo.create_layout(context)
                font_desc = self._get_font_description(font_name, size, weight, italic)
                layout.set_font_description(font_desc)
                layout.set_text("x", -1)  # Use a character to measure height

                # Get line height
                _, logical_rect = layout.get_pixel_extents()
                return 0, logical_rect.height
            except Exception as e:
                if self.debug:
                    logger.error(f"Error getting line height: {str(e)}")
                return 0, size * 1.2  # Fallback approximation

        try:
            if not hasattr(cairo, 'FORMAT_ARGB32'):
                raise ImportError("Cairo FORMAT_ARGB32 not available")

            # Create a Cairo surface and context
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
            context = cairo.Context(surface)

            # Create a Pango layout
            layout = PangoCairo.create_layout(context)

            # Set the font description
            font_desc = self._get_font_description(font_name, size, weight, italic)
            layout.set_font_description(font_desc)

            # Configure the layout
            layout.set_text(text, -1)

            # Handle multiline text
            if '\n' in text and hasattr(Pango, 'WrapMode'):
                # Let Pango handle line breaks
                WrapMode = Pango.WrapMode
                if hasattr(WrapMode, 'WORD_CHAR'):
                    layout.set_wrap(WrapMode.WORD_CHAR)

            # Measure the text
            width, height = layout.get_pixel_size()

            # Apply font-specific adjustments (if needed)
            width, height = self._apply_adjustments(width, height, font_name, size, text)

            if self.debug:
                logger.debug(f"Pango text '{text}' dimensions: {width:.2f}pt × {height:.2f}pt")

            return width, height

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with Pango: {str(e)}")
            raise

    def _apply_adjustments(self, width: float, height: float, font_name: str, font_size: float, text: Optional[str] = None) -> Tuple[float, float]:
        """Apply font-specific adjustments to the calculated dimensions."""
        # Base factors
        width_factor = 1.0
        height_factor = 1.0

        if font_name.lower().startswith('arial'):
            if font_size <= 12:
                height_factor = 0.98
            width_factor = 1.0
        elif font_name.lower().startswith('comic sans ms'):
            height_factor = 1.02
            width_factor = 0.98
        elif font_name.lower().startswith('helsinki'):
            if font_size <= 12:
                height_factor = 0.96
            if 'narrow' in font_name.lower():
                width_factor = 0.98
            else:
                width_factor = 1.01

        # Handle single characters differently
        if text and len(text.strip()) == 1:
            width_factor *= 0.95

        return width * width_factor, height * height_factor