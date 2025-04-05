#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Group model for lbxyml2lbx
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict, Union

@dataclass
class GroupObject:
    """
    Represents a group object that contains multiple child objects with layout properties.

    Groups provide a flexbox-inspired layout system to automatically position and align
    child elements, making it easier to create structured layouts.
    """
    x: str
    y: str
    width: str
    height: str
    objects: List[Any] = field(default_factory=list)

    # Layout properties
    direction: str = "row"  # row, column, row-reverse, column-reverse
    justify: str = "start"  # start, end, center, between, around, evenly
    align: str = "start"    # start, end, center, stretch
    gap: int = 0            # spacing between items
    padding: Union[int, Dict[str, int]] = 0  # internal padding or dict with top/right/bottom/left
    wrap: bool = False      # whether items wrap to next line/column

    # Visual properties
    background_color: str = "#FFFFFF"
    border_style: Optional[str] = None  # NULL for no border, INSIDEFRAME for border

    # Identifier
    id: Optional[str] = None
    name: Optional[str] = None  # Optional name for the object, maps to objectName in XML

    def add_object(self, obj: Any) -> None:
        """Add an object to the group."""
        self.objects.append(obj)

    def get_padding_as_dict(self) -> Dict[str, int]:
        """Convert padding to a dictionary format if it's not already."""
        if isinstance(self.padding, dict):
            return self.padding
        return {
            "top": self.padding,
            "right": self.padding,
            "bottom": self.padding,
            "left": self.padding
        }

    @property
    def is_vertical(self) -> bool:
        """Determine if this is a vertical (column) layout."""
        return self.direction.startswith("column")

    @property
    def is_reversed(self) -> bool:
        """Determine if the direction is reversed."""
        return "reverse" in self.direction