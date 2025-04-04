#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Label model for lbxyml2lbx
"""

from dataclasses import dataclass, field
from typing import List, Any
from rich.console import Console

# Create console for rich output
console = Console()

# Default orientation
DEFAULT_ORIENTATION = "landscape"

@dataclass
class LabelConfig:
    """Configuration for a label parsed from YAML."""
    size: str = "12mm"  # Tape size (9mm, 12mm, 18mm, 24mm)
    width: str = "auto"  # Fixed width (or "auto" for automatic sizing)
    orientation: str = DEFAULT_ORIENTATION
    margin: int = 5  # Additional margin beyond the minimum
    background: str = "#FFFFFF"  # Background color
    color: str = "#000000"  # Label text color
    objects: List[Any] = field(default_factory=list)  # All visual elements (text, image, etc.)

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