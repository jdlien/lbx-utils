#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Container model for lbxyml2lbx
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict, Union

@dataclass
class ContainerObject:
    """
    Represents a virtual container object that organizes child objects with layout properties
    but doesn't create an actual group element in the output XML.

    Containers provide the same layout functionality as groups but without creating an
    additional visual element in the final label.
    """
    x: str
    y: str
    objects: List[Any] = field(default_factory=list)

    # Layout properties (same as groups)
    direction: str = "row"  # row, column, row-reverse, column-reverse
    justify: str = "start"  # start, end, center, between, around, evenly
    align: str = "start"    # start, end, center, stretch
    gap: int = 0            # spacing between items
    padding: Union[int, Dict[str, int]] = 0  # internal padding (for layout calculations only)
    wrap: bool = False      # whether items wrap to next line/column

    # Identifier
    id: Optional[str] = None
    name: Optional[str] = None  # Optional name for identification

    # Width and height are optional and used only for layout calculations
    width: Optional[str] = None
    height: Optional[str] = None

    # Whether the object has an explicitly set position
    _positioned: bool = False

    # Store original coordinates
    _original_x: str = ""
    _original_y: str = ""

    def add_object(self, obj: Any) -> None:
        """Add an object to the container."""
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