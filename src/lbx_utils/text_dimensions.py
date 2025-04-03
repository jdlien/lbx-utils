#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
text_dimensions.py - Calculate text dimensions for P-Touch Editor labels

This module provides functionality to calculate the dimensions of text objects
for Brother P-Touch Editor labels. It uses font metrics and rendering to estimate
the width and height of text with various fonts, sizes, and styles.
"""

import os
import sys
import glob
import platform
import re
from typing import Dict, Tuple, Optional, List, Union, Any
from dataclasses import dataclass
import logging

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle imports with better error messages
try:
    import freetype
except ImportError:
    logger.error("freetype module not found. Please install with: pip install freetype-py")
    freetype = None

try:
    from fontTools.ttLib import TTFont
except ImportError:
    logger.error("fontTools module not found. Please install with: pip install fontTools")
    TTFont = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    logger.error("PIL module not found. Please install with: pip install Pillow")
    Image = ImageDraw = ImageFont = None

import math

@dataclass
class FontMetrics:
    """Font metrics for a specific font and size."""
    ascent: float
    descent: float
    line_height: float
    average_width: float
    max_width: float
    x_height: float
    cap_height: float

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
        apply_ptouch_adjustments: bool = False
    ):
        """
        Initialize the calculator.

        Args:
            font_dir: Optional directory to look for fonts
            debug: Enable debug logging
            allow_fallbacks: Whether to use fallback methods (PIL) if FreeType fails
            allow_font_substitution: Whether to try system font substitution
            allow_approximation: Whether to use rough approximation as last resort
            apply_ptouch_adjustments: Whether to apply P-touch Editor specific adjustments
        """
        self.font_dir = font_dir
        self.debug = debug
        self.allow_fallbacks = allow_fallbacks
        self.allow_font_substitution = allow_font_substitution
        self.allow_approximation = allow_approximation
        self.apply_ptouch_adjustments = apply_ptouch_adjustments

        # P-touch Editor specific adjustment factors
        # These factors correct for systematic differences between our text dimension
        # calculations and the actual dimensions used by Brother P-touch Editor.
        # The values were derived through empirical testing by comparing our calculations
        # with dimensions extracted from P-touch Editor XML files.
        #
        # Font-specific adjustment factors provide better accuracy than global factors
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

        # Caches for performance
        self._font_cache: Dict[str, str] = {}
        self._font_face_cache: Dict[str, Any] = {}
        self._metrics_cache: Dict[str, FontMetrics] = {}

        # Check if required libraries are available
        if freetype is None or TTFont is None or ImageFont is None:
            logger.error("Missing required libraries. Please install them using:")
            logger.error("pip install -r requirements-text-dims.txt")

        # Set up font search paths
        self._system_font_paths = self._get_system_font_paths()

        if self.debug:
            logger.debug(f"System font paths: {self._system_font_paths}")
            if self.font_dir:
                logger.debug(f"Custom font directory: {self.font_dir}")

    def _get_system_font_paths(self) -> List[str]:
        """Get system font paths based on the operating system."""
        paths = []
        system = platform.system()

        if system == "Darwin":  # macOS
            paths = [
                "/Library/Fonts",
                "/System/Library/Fonts",
                os.path.expanduser("~/Library/Fonts"),
                # Brother P-Touch Editor fonts might be installed here
                "/Applications/P-touch Editor.app/Contents/Resources/Fonts",
                "/Applications/Brother P-touch Editor.app/Contents/Resources/Fonts"
            ]
        elif system == "Windows":
            windir = os.environ.get("WINDIR", "C:\\Windows")
            paths = [
                os.path.join(windir, "Fonts"),
                # Brother P-Touch Editor fonts might be installed here
                "C:\\Program Files\\Brother\\P-touch Editor\\Fonts",
                "C:\\Program Files (x86)\\Brother\\P-touch Editor\\Fonts"
            ]
        elif system == "Linux":
            paths = [
                "/usr/share/fonts",
                "/usr/local/share/fonts",
                os.path.expanduser("~/.fonts"),
                os.path.expanduser("~/.local/share/fonts")
            ]

        # Filter out non-existent paths
        paths = [p for p in paths if os.path.exists(p)]
        return paths

    def _normalize_font_name(self, font_name: str) -> str:
        """
        Normalize a font name by removing common suffixes and standardizing format.

        This helps with font matching by removing variations like "Regular", "Unicode",
        "MT", "MS", etc. that don't affect the core font identity.

        Args:
            font_name: The font name to normalize

        Returns:
            Normalized font name
        """
        # Convert to lowercase for case-insensitive comparison
        normalized = font_name.lower()

        # Remove common font suffixes/variations
        common_suffixes = [
            " regular", "regular", " unicode", "unicode",
            " mt", "mt", " ms", "ms", " ht", "ht",
            " condensed", " narrow", " bold", " italic",
            " oblique", " light", " medium", " black",
            " thin", " heavy", " pro", " standard"
        ]

        for suffix in common_suffixes:
            normalized = re.sub(f"{suffix}$", "", normalized)
            normalized = re.sub(f"{suffix}[\\s-]", " ", normalized)

        # Remove spaces, dashes and underscores
        normalized = re.sub(r'[\s_-]+', "", normalized)

        # Remove any non-alphanumeric characters
        normalized = re.sub(r'[^a-z0-9]', "", normalized)

        if self.debug:
            if normalized != font_name.lower().replace(" ", ""):
                logger.debug(f"Normalized font name: '{font_name}' → '{normalized}'")

        return normalized

    def _get_font_path(self, font_name: str, tried_fonts: Optional[set] = None) -> str:
        """
        Get the path to a font file from its name.

        Args:
            font_name: The name of the font to find
            tried_fonts: Set of font names already tried (to prevent recursion)

        Returns:
            str: Path to the font file

        Raises:
            FileNotFoundError: If the font cannot be found
        """
        # Initialize the set of tried fonts if not provided
        if tried_fonts is None:
            tried_fonts = set()

        # Add the current font to the tried set
        tried_fonts.add(font_name)

        # Font name aliases for common fonts
        font_aliases = {
            # Standard fonts
            "Arial": ["Arial Unicode", "Arial MT", "ArialMT"],
            "Arial Unicode": ["Arial", "Arial MT", "ArialMT"],
            "Times New Roman": ["Times", "TimesNewRoman"],
            "Helvetica": ["Arial", "Helvetica Neue"],
            "Courier New": ["Courier", "CourierNew", "Courier Prime"],

            # Brother P-touch specific fonts
            "Helsinki": ["Helsinki Narrow", "Helsinki Narrow Regular"],
            "Helsinki Narrow": ["Helsinki", "Helsinki Narrow Regular"],
            "Brussels": ["Arial", "Helvetica"]  # Brussels is similar to Arial in appearance
        }

        # First check if it's already a path
        if os.path.exists(font_name):
            return font_name

        # Check if we have cached this font
        if font_name in self._font_cache:
            return self._font_cache[font_name]

        # Standard font extensions
        extensions = ['.ttf', '.ttc', '.otf']

        # First check custom font dir if provided
        if self.font_dir:
            for ext in extensions:
                font_path = os.path.join(self.font_dir, f"{font_name}{ext}")
                if os.path.exists(font_path):
                    self._font_cache[font_name] = font_path
                    if self.debug:
                        logger.debug(f"Found font at {font_path}")
                    return font_path

        # System font directories
        if platform.system() == 'Darwin':  # macOS
            font_dirs = [
                '/Library/Fonts',
                '/System/Library/Fonts',
                os.path.expanduser('~/Library/Fonts')
            ]
        elif platform.system() == 'Windows':
            font_dirs = [
                os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
            ]
        else:  # Linux and others
            font_dirs = [
                '/usr/share/fonts',
                '/usr/local/share/fonts',
                os.path.expanduser('~/.fonts')
            ]

        # Try exact match first
        for font_dir in font_dirs:
            for ext in extensions:
                font_path = os.path.join(font_dir, f"{font_name}{ext}")
                if os.path.exists(font_path):
                    self._font_cache[font_name] = font_path
                    if self.debug:
                        logger.debug(f"Found font at {font_path}")
                    return font_path

        # Try aliases if original name was not found
        if font_name in font_aliases and self.allow_font_substitution:
            for alias in font_aliases[font_name]:
                # Skip aliases we've already tried to prevent recursion
                if alias in tried_fonts:
                    if self.debug:
                        logger.debug(f"Skipping already tried alias: {alias}")
                    continue

                try:
                    # Try to find the alias font
                    alias_path = self._get_font_path(alias, tried_fonts)
                    # Cache the result for the original font name
                    self._font_cache[font_name] = alias_path
                    if self.debug:
                        logger.debug(f"Using font alias: '{font_name}' → '{alias}' at {alias_path}")
                    return alias_path
                except FileNotFoundError:
                    # Continue to the next alias if this one wasn't found
                    continue

        # Try case-insensitive or partial match if allowed
        if self.allow_font_substitution:
            # Normalize the requested font name
            normalized_font_name = self._normalize_font_name(font_name)

            for font_dir in font_dirs:
                if not os.path.exists(font_dir):
                    continue

                for filename in os.listdir(font_dir):
                    file_base, file_ext = os.path.splitext(filename)
                    if file_ext.lower() in ['.ttf', '.ttc', '.otf']:
                        # Normalize the filename for comparison
                        normalized_file_base = self._normalize_font_name(file_base)

                        # Check for similarity by normalized name
                        if (normalized_file_base == normalized_font_name or
                            normalized_font_name in normalized_file_base or
                            normalized_file_base in normalized_font_name):

                            font_path = os.path.join(font_dir, filename)
                            self._font_cache[font_name] = font_path
                            if self.debug:
                                logger.debug(f"Found similar font through normalization: '{font_name}' → '{file_base}' at {font_path}")
                            return font_path

                        # If still not found, check for similarity with original method
                        if (file_base.lower() == font_name.lower() or
                            font_name.lower() in file_base.lower() or
                            file_base.lower() in font_name.lower()):

                            font_path = os.path.join(font_dir, filename)
                            self._font_cache[font_name] = font_path
                            if self.debug:
                                logger.debug(f"Found similar font at {font_path}")
                            return font_path

        # If we get here, we didn't find the font
        error_msg = f"Font '{font_name}' not found. Searched in:\n"
        for font_dir in font_dirs:
            for ext in extensions:
                error_msg += f"  - {os.path.join(font_dir, f'{font_name}{ext}')}\n"

        if self.debug:
            logger.error(error_msg)

        raise FileNotFoundError(error_msg)

    def _load_font(self, font_name: str) -> Any:
        """
        Load a font with freetype.

        Args:
            font_name: The name of the font to load

        Returns:
            freetype.Face object

        Raises:
            FileNotFoundError: If the font cannot be found
            ImportError: If freetype is not available
        """
        # Check if freetype is available
        if freetype is None:
            raise ImportError("freetype module is not available")

        if font_name not in self._font_face_cache:
            font_path = self._get_font_path(font_name)

            try:
                face = freetype.Face(font_path)
                self._font_face_cache[font_name] = face

                if self.debug:
                    logger.debug(f"Loaded font '{font_name}' from {font_path}")

                return face
            except Exception as e:
                if self.debug:
                    logger.error(f"Error loading font '{font_name}': {str(e)}")
                raise

        return self._font_face_cache[font_name]

    def _get_font_metrics(self, font_name: str, size: float) -> FontMetrics:
        """Get font metrics for a specific font and size."""
        cache_key = f"{font_name}_{size}"
        if cache_key not in self._metrics_cache:
            face = self._load_font(font_name)

            # Set the font size (freetype uses 26.6 fixed point format)
            face.set_char_size(int(size * 64))

            # Get basic metrics (with safe attribute access using getattr with defaults)
            metrics = FontMetrics(
                ascent=face.ascender / 64.0,
                descent=abs(face.descender / 64.0),
                line_height=face.height / 64.0,
                average_width=getattr(face.size, 'avg_width', size * 0.6) / 64.0,
                max_width=getattr(face.size, 'max_width', size * 1.2) / 64.0,
                x_height=getattr(face.size, 'x_height', size * 0.5) / 64.0,
                cap_height=getattr(face.size, 'cap_height', size * 0.7) / 64.0
            )

            self._metrics_cache[cache_key] = metrics

            if self.debug:
                logger.debug(f"Font metrics for {font_name} at {size}pt: {metrics}")

        return self._metrics_cache[cache_key]

    def calculate_text_dimensions(
        self,
        text: str,
        font_name: str = "Helsinki",
        size: float = 12.0,
        weight: str = "normal",
        italic: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate the dimensions of a text string.

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
            try:
                metrics = self._get_font_metrics(font_name, size)
                return (0, metrics.line_height)
            except Exception:
                if self.allow_approximation:
                    return (0, size * 1.2)  # Fallback height approximation
                else:
                    raise

        try:
            face = self._load_font(font_name)
            metrics = self._get_font_metrics(font_name, size)

            # Set font size
            face.set_char_size(int(size * 64))

            # Calculate width by summing advance widths and kerning
            width = 0
            prev_glyph = None
            lines = text.split("\n")
            max_width = 0

            for line in lines:
                line_width = 0
                prev_glyph = None

                for char in line:
                    glyph_index = face.get_char_index(ord(char))
                    if glyph_index:
                        face.load_glyph(glyph_index)
                        # Get advance width
                        line_width += face.glyph.advance.x >> 6

                        # Add kerning if applicable
                        if prev_glyph:
                            kerning = face.get_kerning(prev_glyph, glyph_index)
                            line_width += kerning.x >> 6

                        prev_glyph = glyph_index

                max_width = max(max_width, line_width)

            width = max_width

            # Calculate height based on number of lines
            height = (metrics.ascent - metrics.descent) * len(lines)  # Use ascent-descent for height

            # Adjust for weight and italic
            if weight == "bold":
                width *= 1.1  # Approximate bold width increase
            if italic:
                width *= 1.05  # Approximate italic width increase

            # Get the final dimensions with font-specific adjustments
            width, height = self._apply_adjustments(width, height, font_name, size, text)

            if self.debug:
                logger.debug(f"Text '{text}' dimensions: {width}pt × {height}pt")

            return (width, height)

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions: {str(e)}")

            # Try PIL as fallback only if allowed
            if self.allow_fallbacks:
                return self.calculate_text_dimensions_pil(text, font_name, size, weight, italic)
            else:
                raise

    def _apply_adjustments(self, width: float, height: float, font_name: str, font_size: float, text: Optional[str] = None) -> tuple[float, float]:
        """Apply font-specific adjustments to the calculated dimensions."""
        # Get font-specific factors
        width_factor = 1.0
        height_factor = 1.0

        # Base height factor on font size and font
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

    def calculate_text_dimensions_pil(
        self,
        text: str,
        font_name: str = "Helsinki",
        size: float = 12.0,
        weight: str = "normal",
        italic: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate text dimensions using PIL as an alternative method.

        This can be used as a fallback if freetype fails.
        """
        if ImageFont is None:
            if self.debug:
                logger.error("PIL ImageFont is not available")

            if self.allow_approximation:
                return (len(text) * size * 0.6, size * 1.2)  # Very rough approximation
            else:
                raise ImportError("PIL ImageFont is not available")

        try:
            # Try to load the font
            font_path = self._get_font_path(font_name)
            font = ImageFont.truetype(font_path, int(size))

            # Handle multiline text
            lines = text.split("\n")
            max_width = 0
            total_height = 0

            for line in lines:
                # Get text dimensions
                bbox = font.getbbox(line)
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                max_width = max(max_width, width)
                total_height += height

            # Add a small margin between lines
            if len(lines) > 1:
                total_height += (len(lines) - 1) * (size * 0.1)

            # Apply adjustments if needed, including font-specific ones
            max_width, total_height = self._apply_adjustments(max_width, total_height, font_name, size, text)

            if self.debug:
                logger.debug(f"PIL text '{text}' dimensions: {max_width}pt × {total_height}pt")

            return (max_width, total_height)

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with PIL: {str(e)}")

            # Last resort: very rough approximation, only if allowed
            if self.allow_approximation:
                lines = text.split("\n")
                max_chars = max(len(line) for line in lines)
                return (max_chars * size * 0.6, len(lines) * size * 1.2)
            else:
                raise

# Simple test function for direct use
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Calculate text dimensions")
    parser.add_argument("--text", type=str, required=True, help="Text to measure")
    parser.add_argument("--font", type=str, default="Helsinki", help="Font name")
    parser.add_argument("--size", type=float, default=12.0, help="Font size in points")
    parser.add_argument("--weight", type=str, default="normal", help="Font weight (normal, bold)")
    parser.add_argument("--italic", action="store_true", help="Italic style")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--font-dir", type=str, help="Custom font directory")
    parser.add_argument("--no-fallbacks", action="store_true", help="Disable fallback methods")
    parser.add_argument("--no-substitution", action="store_true", help="Disable font substitution")
    parser.add_argument("--no-approximation", action="store_true", help="Disable approximation fallbacks")
    parser.add_argument("--ptouch-adjustments", action="store_true", help="Apply P-touch Editor specific adjustments")
    args = parser.parse_args()

    calculator = TextDimensionCalculator(
        font_dir=args.font_dir,
        debug=args.debug,
        allow_fallbacks=not args.no_fallbacks,
        allow_font_substitution=not args.no_substitution,
        allow_approximation=not args.no_approximation,
        apply_ptouch_adjustments=args.ptouch_adjustments
    )

    try:
        # Try freetype method first
        width, height = calculator.calculate_text_dimensions(
            text=args.text,
            font_name=args.font,
            size=args.size,
            weight=args.weight,
            italic=args.italic
        )
        print(f"Freetype: {width:.2f}pt × {height:.2f}pt")

        # Then try PIL method if fallbacks are allowed
        if not args.no_fallbacks:
            pil_width, pil_height = calculator.calculate_text_dimensions_pil(
                text=args.text,
                font_name=args.font,
                size=args.size,
                weight=args.weight,
                italic=args.italic
            )
            print(f"PIL: {pil_width:.2f}pt × {pil_height:.2f}pt")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()