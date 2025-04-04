#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Core Text-based text dimension calculation technique.

This technique uses macOS Core Text via PyObjC to calculate text dimensions with high accuracy.
It should produce results more similar to P-touch Editor's native text rendering on macOS.
"""

import logging
import platform
import os
from typing import Tuple, Optional, Dict, Any
from .base import BaseCalculationTechnique

# Configure logger
logger = logging.getLogger(__name__)

# Check if we're on macOS first
IS_MACOS = platform.system() == "Darwin"

# Try to import PyObjC modules for Core Text
if IS_MACOS:
    try:
        import Cocoa
        import CoreText
        import objc
        import AppKit
        CORE_TEXT_AVAILABLE = True
    except ImportError as e:
        logger.warning(f"PyObjC Core Text modules not available: {str(e)}")
        CORE_TEXT_AVAILABLE = False
else:
    CORE_TEXT_AVAILABLE = False


class CoreTextTechnique(BaseCalculationTechnique):
    """
    Core Text-based text dimension calculation technique for macOS.

    This technique uses Apple's Core Text framework via PyObjC to calculate
    text dimensions with high accuracy on macOS. It should closely match
    results from apps that use Core Text for text rendering.
    """

    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        return "core_text"

    def is_available(self) -> bool:
        """Check if this calculation technique is available."""
        return IS_MACOS and CORE_TEXT_AVAILABLE

    def _get_font_path(self, font_name: str) -> str:
        """
        Get the path to a font file using Core Text.

        Args:
            font_name: Name of the font to find

        Returns:
            Path to the font file

        Raises:
            FileNotFoundError: If the font cannot be found
        """
        if not self.is_available():
            raise ImportError("Core Text is not available on this system")

        # Check cache first
        if font_name in self._font_cache:
            return self._font_cache[font_name]

        # Try to find the font using Core Text
        try:
            # Create a font descriptor with the font name
            font_descriptor = AppKit.NSFontDescriptor.fontDescriptorWithName_size_(
                font_name, 12.0  # Size doesn't matter for the lookup
            )

            # Get the font from the descriptor
            font = AppKit.NSFont.fontWithDescriptor_size_(font_descriptor, 12.0)

            if font is None:
                raise FileNotFoundError(f"Font '{font_name}' not found")

            # Get the CTFont from the NSFont
            ct_font = CoreText.CTFontCreateWithName(font.fontName(), 12.0, None)

            if ct_font is None:
                raise FileNotFoundError(f"Failed to create CTFont for '{font_name}'")

            # Get the font URL
            url = CoreText.CTFontCopyAttribute(ct_font, CoreText.kCTFontURLAttribute)

            if url is None:
                raise FileNotFoundError(f"Failed to get URL for font '{font_name}'")

            # Convert URL to path
            path = url.path()

            if not path or not os.path.exists(path):
                raise FileNotFoundError(f"Font file for '{font_name}' not found at {path}")

            # Cache the result
            self._font_cache[font_name] = path

            return path

        except Exception as e:
            logger.error(f"Error finding font '{font_name}': {str(e)}")
            raise FileNotFoundError(f"Font '{font_name}' could not be found: {str(e)}")

    def _apply_adjustments(self, width: float, height: float, font_name: str, font_size: float, text: Optional[str] = None) -> Tuple[float, float]:
        """Apply font-specific adjustments to the calculated dimensions."""
        width_factor = 1.0
        height_factor = 1.0

        # Font-specific adjustments based on font name
        if font_name.lower().startswith('arial'):
            width_factor = 0.95
            height_factor = 0.92
        elif font_name.lower().startswith('comic sans ms'):
            width_factor = 0.97
            height_factor = 0.98
        elif font_name.lower().startswith('helsinki'):
            if 'narrow' in font_name.lower():
                width_factor = 0.85
                height_factor = 0.9
            else:
                width_factor = 0.9
                height_factor = 0.95

        # Special handling for single characters
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
        Calculate the dimensions of a text string using Core Text.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        if not self.is_available():
            raise ImportError("Core Text is not available on this system")

        if not text:
            # Empty string has zero width but still has height
            return (0, size * 1.2)  # Approximate line height

        try:
            # Create a font traits dictionary
            traits = {}

            # Add weight trait if bold
            if weight == "bold":
                traits[AppKit.NSFontTraitBold] = True

            # Add italic trait if italic
            if italic:
                traits[AppKit.NSFontTraitItalic] = True

            # Create a font descriptor with the given traits
            descriptor = AppKit.NSFontDescriptor.fontDescriptorWithName_size_(
                font_name, size
            )

            if traits:
                descriptor = descriptor.fontDescriptorWithSymbolicTraits_(
                    sum(traits.keys())
                )

            # Create the font with the descriptor
            font = AppKit.NSFont.fontWithDescriptor_size_(descriptor, size)

            if font is None:
                # Try to find a substitute
                font = AppKit.NSFont.fontWithName_size_(font_name, size)

                if font is None:
                    raise FileNotFoundError(f"Font '{font_name}' not found")

                # Apply traits manually
                if weight == "bold":
                    bold_desc = font.fontDescriptor().fontDescriptorWithSymbolicTraits_(
                        AppKit.NSFontDescriptorTraitBold
                    )
                    bold_font = AppKit.NSFont.fontWithDescriptor_size_(bold_desc, size)
                    if bold_font:
                        font = bold_font

                if italic:
                    italic_desc = font.fontDescriptor().fontDescriptorWithSymbolicTraits_(
                        AppKit.NSFontDescriptorTraitItalic
                    )
                    italic_font = AppKit.NSFont.fontWithDescriptor_size_(italic_desc, size)
                    if italic_font:
                        font = italic_font

            # Process multiline text
            lines = text.split("\n")
            max_width = 0
            total_height = 0

            for line in lines:
                # Skip empty lines but count their height
                if not line:
                    total_height += font.leading() + font.descender() + font.ascender()
                    continue

                # Create an attributed string with the font
                attributes = {
                    AppKit.NSFontAttributeName: font
                }
                attrString = AppKit.NSAttributedString.alloc().initWithString_attributes_(
                    line, attributes
                )

                # Use NSAttributedString's boundingRectWithSize method to calculate dimensions
                # Use a very large size for width constraint to get the full width
                constraint = Cocoa.NSMakeSize(1000000, 1000000)
                rect = attrString.boundingRectWithSize_options_(
                    constraint, AppKit.NSStringDrawingUsesLineFragmentOrigin
                )

                # Update maximum width
                max_width = max(max_width, rect.size.width)

                # Add line height
                total_height += rect.size.height

            # If no height was calculated (e.g., all empty lines), use font metrics
            if total_height == 0:
                total_height = len(lines) * (font.leading() + font.descender() + font.ascender())

            # Apply font-specific adjustments
            width, height = self._apply_adjustments(max_width, total_height, font_name, size, text)

            if self.debug:
                logger.debug(f"Core Text dimensions for '{text}': {width:.2f}pt × {height:.2f}pt")

            return (width, height)

        except Exception as e:
            if self.debug:
                logger.error(f"Error calculating text dimensions with Core Text: {str(e)}")
            raise