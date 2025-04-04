#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Unit conversion utilities for lbxyml2lbx
"""

from rich.console import Console

console = Console()

def convert_to_pt(value) -> str:
    """
    Convert a value to a point value.

    Supports:
    - Numeric values (int/float): Assumed to be in points
    - Strings with 'pt' suffix: Used as-is
    - Strings with 'mm' suffix: Converted from mm to points (1mm ≈ 2.83pt)
    - Other strings: Assumed to be in points

    Returns:
        String representation with 'pt' suffix
    """
    if isinstance(value, (int, float)):
        # Treat numeric values as pt by default
        return f"{value}pt"
    elif isinstance(value, str):
        if value.endswith('pt'):
            # Already in points, use as-is
            return value
        elif value.endswith('mm'):
            # Convert mm to pt (1mm ≈ 2.83pt)
            try:
                mm_value = float(value.replace('mm', ''))
                # Use more precise conversion factor
                pt_value = mm_value * 2.834645669
                return f"{pt_value:.2f}pt"
            except ValueError:
                console.print(f"[yellow]Warning: Invalid mm value '{value}', using as-is[/yellow]")
                return f"{value}pt"
        else:
            # Try to convert string to float and treat as pt
            try:
                pt_value = float(value)
                return f"{pt_value}pt"
            except ValueError:
                # If conversion fails, just append pt
                console.print(f"[yellow]Warning: Unrecognized unit in '{value}', assuming points[/yellow]")
                return f"{value}pt"
    else:
        # For any other type, convert to string and append pt
        console.print(f"[yellow]Warning: Unexpected value type for '{value}', converting to string[/yellow]")
        return f"{value}pt"