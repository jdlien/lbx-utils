#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Image models for lbxyml2lbx
"""

from dataclasses import dataclass
from typing import Optional

@dataclass
class ImageObject:
    """Object representing an image to be added to the label."""
    file_path: str
    x: str
    y: str
    width: str
    height: str
    convert_to_bmp: bool = False  # Optionally convert to BMP for maximum compatibility
    monochrome: bool = True  # Convert to monochrome
    transparency: bool = False  # Enable transparency
    transparency_color: str = "#FFFFFF"  # Color to treat as transparent
    dest_filename: str = ""
    needs_conversion: bool = False
    transparent_color: Optional[str] = None  # Transparent color (hex format)
    name: Optional[str] = None  # Optional name for the object, maps to objectName in XML

    @property
    def effect_type(self) -> str:
        """Return the effect type based on file format."""
        # For PNG files without conversion, use NONE effect
        if not self.convert_to_bmp and self.file_path.lower().endswith('.png'):
            return "NONE"
        # For BMP or converted files, use MONO effect
        return "MONO"

    @property
    def operation_kind(self) -> str:
        """Return the operation kind based on file format."""
        # For PNG files without conversion, use BINARY operation
        if not self.convert_to_bmp and self.file_path.lower().endswith('.png'):
            return "BINARY"
        # For BMP or converted files, use ERRORDIFFUSION
        return "ERRORDIFFUSION"