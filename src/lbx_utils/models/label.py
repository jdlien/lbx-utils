#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Label model for lbxyml2lbx
"""

from dataclasses import dataclass, field
from typing import List, Any, Optional, Union, Dict
from rich.console import Console

# Create console for rich output
console = Console()

# Default orientation
DEFAULT_ORIENTATION = "landscape"
DEFAULT_MARGIN = 0.0

@dataclass
class LabelConfig:
    """Configuration for a label parsed from YAML."""
    size: str = "12mm"  # Tape size (9mm, 12mm, 18mm, 24mm)
    width: str = "auto"  # Fixed width (or "auto" for automatic sizing)
    orientation: str = DEFAULT_ORIENTATION
    margin: float = DEFAULT_MARGIN
    background: str = "#FFFFFF"  # Background color
    color: str = "#000000"  # Label text color
    objects: List[Any] = field(default_factory=list)  # All visual elements (text, image, etc.)

    # Root-level layout properties
    direction: Optional[str] = None  # row, column, row-reverse, column-reverse
    align: Optional[str] = None  # start, end, center, stretch
    justify: Optional[str] = None  # start, end, center, between, around, evenly
    gap: Optional[int] = None  # spacing between items
    padding: Optional[Union[int, Dict[str, int]]] = None  # internal padding
    wrap: Optional[bool] = None  # whether items wrap to next line

    # Flags for root layout handling
    has_root_layout: bool = False  # Whether root-level layout properties are present
    apply_root_layout: bool = False  # Whether to apply root-level layout calculations

    @property
    def size_mm(self) -> float:
        """Extract numerical size in mm from size string."""
        size_value = str(self.size).replace('mm', '')
        try:
            # Use float instead of int to handle sizes like 3.5mm
            return float(size_value)
        except ValueError:
            # Default to 24mm if conversion fails
            console.print(f"[red]Warning: Invalid size value '{self.size}', defaulting to 24mm[/red]")
            return 24.0