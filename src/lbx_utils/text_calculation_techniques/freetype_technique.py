#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
FreeType-based text dimension calculation technique.
"""

import os
import platform
import logging
import re
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List, Any

from .base import BaseCalculationTechnique

# Configure logger
logger = logging.getLogger(__name__)

# Import freetype conditionally
try:
    import freetype
except ImportError:
    logger.warning("freetype module not found. Please install with: pip install freetype-py")
    freetype = None

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


class FreetypeTechnique(BaseCalculationTechnique):
    """
    Text dimension calculation technique using the FreeType library.
    """

    def __init__(self, debug: bool = False, font_dir: Optional[str] = None):
        """
        Initialize the FreeType calculation technique.

        Args:
            debug: Enable debug logging
            font_dir: Optional directory to look for fonts
        """
        super().__init__(debug, font_dir)
        self._font_face_cache: Dict[str, Any] = {}
        self._metrics_cache: Dict[str, FontMetrics] = {}
        self._system_font_paths = self._get_system_font_paths()

        # Initialize font_dir mapping if font_dir is provided
        self._font_dir_mapping: Dict[str, str] = {}
        if self.font_dir and os.path.exists(self.font_dir):
            if self.debug:
                logger.debug(f"Scanning custom font directory: {self.font_dir}")
            self._font_dir_mapping = self._scan_font_directory(self.font_dir)
            if self.debug:
                logger.debug(f"Found {len(self._font_dir_mapping)} fonts in {self.font_dir}")

        if self.debug:
            logger.debug(f"System font paths: {self._system_font_paths}")
            if self.font_dir:
                logger.debug(f"Custom font directory: {self.font_dir}")

    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        return "freetype"

    def is_available(self) -> bool:
        """Check if the FreeType library is available."""
        return freetype is not None

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

    def _get_real_font_name_from_file(self, font_path: str) -> Optional[str]:
        """
        Extract the real font name from a font file using FreeType.

        Args:
            font_path: Path to the font file

        Returns:
            The font family name or None if it can't be extracted
        """
        if freetype is None:
            return None

        try:
            face = freetype.Face(font_path)
            family_name = face.family_name

            # Convert from bytes to string if necessary
            if isinstance(family_name, bytes):
                family_name = family_name.decode('utf-8', errors='replace')

            return family_name
        except Exception as e:
            if self.debug:
                logger.debug(f"Error extracting font name from {font_path}: {str(e)}")
            return None

    def _scan_font_directory(self, directory: str) -> Dict[str, str]:
        """
        Scan a font directory and build a mapping of font names to file paths.

        Args:
            directory: Directory to scan for font files

        Returns:
            Dictionary mapping font names to file paths
        """
        result = {}

        if not os.path.exists(directory):
            return result

        for filename in os.listdir(directory):
            _, ext = os.path.splitext(filename)
            if ext.lower() in ['.ttf', '.ttc', '.otf']:
                font_path = os.path.join(directory, filename)

                # Try to get the real font name
                font_name = self._get_real_font_name_from_file(font_path)

                if font_name:
                    # Store with both the actual font name and the normalized version
                    result[font_name] = font_path
                    normalized_name = self._normalize_font_name(font_name)
                    if normalized_name != font_name:
                        result[normalized_name] = font_path

                    if self.debug:
                        logger.debug(f"Found font: {font_name} at {font_path}")

        return result

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

        # Normalize the requested font name
        normalized_font_name = self._normalize_font_name(font_name)

        # First check custom font dir if provided - build a comprehensive font name mapping
        if self.font_dir and os.path.exists(self.font_dir):
            # Try direct match with font name
            if font_name in self._font_dir_mapping:
                font_path = self._font_dir_mapping[font_name]
                self._font_cache[font_name] = font_path
                if self.debug:
                    logger.debug(f"Found font '{font_name}' in custom directory at {font_path}")
                return font_path

            # Try with normalized name
            if normalized_font_name in self._font_dir_mapping:
                font_path = self._font_dir_mapping[normalized_font_name]
                self._font_cache[font_name] = font_path
                if self.debug:
                    logger.debug(f"Found font '{font_name}' (as '{normalized_font_name}') in custom directory at {font_path}")
                return font_path

            # Try partial match with any font in the mapping
            for mapped_name, font_path in self._font_dir_mapping.items():
                normalized_mapped = self._normalize_font_name(mapped_name)
                if (normalized_font_name in normalized_mapped or
                    normalized_mapped in normalized_font_name):
                    self._font_cache[font_name] = font_path
                    if self.debug:
                        logger.debug(f"Found similar font for '{font_name}' as '{mapped_name}' in custom directory at {font_path}")
                    return font_path

            # Try standard filename-based approach as fallback for custom directory
            for ext in extensions:
                font_path = os.path.join(self.font_dir, f"{font_name}{ext}")
                if os.path.exists(font_path):
                    self._font_cache[font_name] = font_path
                    if self.debug:
                        logger.debug(f"Found font at {font_path}")
                    return font_path

        # Try exact match first across system font paths
        for font_dir in self._system_font_paths:
            for ext in extensions:
                font_path = os.path.join(font_dir, f"{font_name}{ext}")
                if os.path.exists(font_path):
                    self._font_cache[font_name] = font_path
                    if self.debug:
                        logger.debug(f"Found font at {font_path}")
                    return font_path

        # Try aliases if original name was not found
        if font_name in font_aliases:
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

        # Try case-insensitive or partial match through system font paths
        for font_dir in self._system_font_paths:
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
        error_msg = f"Font '{font_name}' not found. Searched in:"
        if self.font_dir:
            error_msg += f"\n  - Custom font directory: {self.font_dir}"
        for font_dir in self._system_font_paths:
            error_msg += f"\n  - System font directory: {font_dir}"

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
        Calculate the dimensions of a text string using FreeType.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        if not freetype:
            raise ImportError("FreeType library is not available")

        if not text:
            # Empty string has zero width but still has line height
            try:
                metrics = self._get_font_metrics(font_name, size)
                return (0, metrics.line_height)
            except Exception:
                return (0, size * 1.2)  # Fallback height approximation

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

            # Apply font-specific adjustments
            width, height = self._apply_adjustments(width, height, font_name, size, text)

            if self.debug:
                logger.debug(f"Text '{text}' dimensions: {width}pt × {height}pt")

            return (width, height)

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with FreeType: {str(e)}")
            raise