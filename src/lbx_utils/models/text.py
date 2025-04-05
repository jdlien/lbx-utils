#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text models for lbxyml2lbx
"""

from dataclasses import dataclass, field
from typing import List, Optional

# Default values
DEFAULT_FONT = "Helsinki"
DEFAULT_FONT_SIZE = "12pt"
DEFAULT_FONT_WEIGHT = "400"  # Normal weight
DEFAULT_FONT_ITALIC = "false"

@dataclass
class FontInfo:
    """Font information for a text object."""
    name: str = DEFAULT_FONT
    size: str = DEFAULT_FONT_SIZE
    weight: str = DEFAULT_FONT_WEIGHT
    italic: str = DEFAULT_FONT_ITALIC
    underline: str = "0"  # Adding underline support
    color: str = "#000000"
    print_color_number: str = "1"

    @property
    def org_size(self) -> str:
        """Calculate the original size (3.6x the font size)."""
        size_value = float(self.size.replace('pt', ''))
        return f"{size_value * 3.6}pt"

@dataclass
class StringItem:
    """String item within a text object."""
    char_len: int
    font_info: FontInfo
    start_pos: int = 0

@dataclass
class TextObject:
    """Represents a text object on the label."""
    text: str
    x: str
    y: str
    width: str
    height: str
    font_info: FontInfo = field(default_factory=FontInfo)
    string_items: List[StringItem] = field(default_factory=list)
    align: str = "left"  # Text alignment (left, center, right)
    vertical: bool = False  # Vertical text orientation
    name: Optional[str] = None  # Optional name for the object, maps to objectName in XML

    def __post_init__(self):
        """Initialize string items if not provided."""
        if not self.string_items:
            self.string_items = [StringItem(char_len=len(self.text), font_info=self.font_info)]