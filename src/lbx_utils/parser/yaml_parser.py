#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YAML parser for lbxyml2lbx
"""

import os
import yaml
import platform
from typing import Dict, List, Any
from rich.console import Console

from ..text_dimensions import TextDimensionCalculator, CalculationMethod
from ..models import LabelConfig, TextObject, ImageObject, FontInfo, StringItem, GroupObject
from ..utils import convert_to_pt

# Create console for rich output
console = Console()

class YamlParser:
    """Parser for LBX YAML files."""

    def __init__(self, yaml_file: str):
        """Initialize with the path to a YAML file."""
        self.yaml_file = yaml_file
        self.yaml_data = None
        self.label_config = None

        # Use the most accurate method based on platform
        # CoreText is the best method on macOS
        default_method = None
        if platform.system() == "Darwin":
            default_method = CalculationMethod.CORE_TEXT

        # Initialize the TextDimensionCalculator with recommended settings
        self.text_calculator = TextDimensionCalculator(
            debug=False,
            allow_fallbacks=True,
            apply_technique_adjustments=True,  # Apply technique-specific adjustments
            default_method=default_method
        )

    def parse(self) -> LabelConfig:
        """Parse the YAML file and return a LabelConfig."""
        if not os.path.exists(self.yaml_file):
            raise FileNotFoundError(f"YAML file not found: {self.yaml_file}")

        with open(self.yaml_file, 'r') as f:
            self.yaml_data = yaml.safe_load(f)

        # Create a default label config
        config = LabelConfig()

        # Parse label properties
        if self.yaml_data:
            # Ensure the YAML data has the required structure
            if not isinstance(self.yaml_data, dict):
                raise ValueError(f"Invalid YAML structure in {self.yaml_file}. The file must use the canonical structure with label properties at the root level.")

            # Check for the required 'objects' key
            if 'objects' not in self.yaml_data:
                raise ValueError(f"Missing required 'objects' key in {self.yaml_file}. All visual elements must be defined within the 'objects' array.")

            # Handle label properties at root level
            for key, value in self.yaml_data.items():
                if key == 'size' and value:
                    # Ensure size has "mm" suffix if it's just a number
                    if isinstance(value, (int, float)) or (isinstance(value, str) and value.isdigit()):
                        config.size = f"{value}mm"
                    else:
                        config.size = value
                elif key == 'width':
                    config.width = value
                elif key == 'orientation':
                    config.orientation = value
                elif key == 'margin':
                    # Handle margin values with units
                    if isinstance(value, (int, float)):
                        # If it's already a number, use it directly (assumed to be in mm)
                        config.margin = float(value)
                    elif isinstance(value, str):
                        if value.endswith('mm'):
                            # Value is already in mm, just extract the number
                            try:
                                config.margin = float(value.replace('mm', ''))
                            except ValueError:
                                console.print(f"[yellow]Warning: Invalid margin value '{value}', using default[/yellow]")
                                config.margin = 5.0  # Default margin value
                        elif value.endswith('pt'):
                            # If it's in points, convert to mm (1pt ≈ 0.35mm)
                            try:
                                pt_value = float(value.replace('pt', ''))
                                # Convert to mm (1pt ≈ 0.35mm)
                                config.margin = pt_value / 2.83
                            except ValueError:
                                console.print(f"[yellow]Warning: Invalid margin value '{value}', using default[/yellow]")
                                config.margin = 5.0  # Default margin value
                        else:
                            # Try to parse as a simple number (assumed to be in mm)
                            try:
                                config.margin = float(value)
                            except ValueError:
                                console.print(f"[yellow]Warning: Invalid margin value '{value}', using default[/yellow]")
                                config.margin = 5.0  # Default margin value
                    else:
                        console.print(f"[yellow]Warning: Unexpected margin type '{type(value)}', using default[/yellow]")
                        config.margin = 5.0  # Default margin value
                elif key == 'background':
                    config.background = value
                elif key == 'color':
                    config.color = value
                elif key == 'objects':
                    config.objects = self._parse_objects(value)

            # No need to handle "flat structure" anymore as we're enforcing canonical structure

        # Apply flex layouts to all groups after parsing
        from ..layout_engine import FlexLayoutEngine
        layout_engine = FlexLayoutEngine()

        # Function to recursively apply layouts to all groups
        def apply_layouts_recursive(objects):
            for obj in objects:
                if isinstance(obj, GroupObject):
                    # Apply layouts to nested groups first (bottom-up)
                    apply_layouts_recursive(obj.objects)
                    # Then apply layout to this group
                    layout_engine.apply_layout(obj)

        # Apply layouts to all groups in the config
        apply_layouts_recursive(config.objects)

        self.label_config = config
        return config

    def _parse_objects(self, objects_list: List[Dict]) -> List[Any]:
        """Parse the objects from the YAML data."""
        parsed_objects = []

        for obj in objects_list:
            obj_type = obj.get('type', '').lower()

            if obj_type == 'text':
                parsed_objects.append(self._parse_text_object(obj))
            elif obj_type == 'image':
                parsed_objects.append(self._parse_image_object(obj))
            elif obj_type == 'group':
                parsed_objects.append(self._parse_group_object(obj))
            # Add more object types as needed

        return parsed_objects

    def _parse_text_object(self, obj: Dict) -> TextObject:
        """Parse a text object from the YAML data."""
        # Extract text properties
        content = obj.get('content', '')

        # Get x and y coordinates - note that a horizontal margin (5.6pt/~2mm) will be
        # added to the x value during XML generation to account for the marginTop in
        # landscape mode. The user-specified x is relative to the printable area start.
        x = convert_to_pt(obj.get('x', 0)) # Default x to 0
        y = convert_to_pt(obj.get('y', 0)) # Default y to 0

        # Process bold, italic, and underline flags
        bold = obj.get('bold', False)
        italic = obj.get('italic', False)
        underline = obj.get('underline', False)

        # Get font information
        font_name = obj.get('font', 'Helsinki')
        font_size = obj.get('size', 12)
        # Extract numeric value if it's a string with unit
        if isinstance(font_size, str) and font_size.endswith(('pt', 'mm')):
            if font_size.endswith('mm'):
                # Convert mm to pt (1mm ≈ 2.83pt)
                font_size = float(font_size.replace('mm', '')) * 2.834645669
            else:
                font_size = float(font_size.replace('pt', ''))

        # Calculate text dimensions using TextDimensionCalculator
        try:
            calculated_width, calculated_height = self.text_calculator.calculate_text_dimensions(
                text=content,
                font_name=font_name,
                size=float(font_size),
                weight="bold" if bold else "normal",
                italic=italic
            )

            # Use calculated dimensions if width/height not specified
            width = convert_to_pt(obj.get('width', calculated_width))
            height = convert_to_pt(obj.get('height', calculated_height))

            # Log dimension calculation
            console.print(f"[blue]Text dimensions for '{content}': calculated={calculated_width:.2f}pt x {calculated_height:.2f}pt, final={width} x {height}[/blue]")
        except Exception as e:
            # If calculation fails, fall back to default dimensions
            console.print(f"[yellow]Warning: Failed to calculate text dimensions for '{content}': {str(e)}. Using defaults.[/yellow]")

            # Use default dimensions or user-specified values
            width = convert_to_pt(obj.get('width', 120))
            height = convert_to_pt(obj.get('height', 20))

            console.print(f"[blue]Using dimensions: {width} x {height}[/blue]")

        align = obj.get('align', 'left')
        vertical = obj.get('vertical', False)
        name = obj.get('name', None)  # Get the name property if provided

        # Create font info - ensure these values are correctly set
        font_info = FontInfo(
            name=font_name,
            size=convert_to_pt(font_size),
            weight="700" if bold else "400",  # 700 for bold, 400 for normal
            italic="true" if italic else "false",
            underline="1" if underline else "0",
            color=obj.get('color', "#000000")
        )

        # Log formatting for debugging
        if bold or italic or underline:
            console.print(f"[blue]Formatting applied: bold={bold}, italic={italic}, underline={underline}[/blue]")

        # Create text object
        text_obj = TextObject(
            text=content,
            x=x,
            y=y,
            width=width,
            height=height,
            font_info=font_info,
            align=align,
            vertical=vertical,
            name=name  # Include the name property
        )

        return text_obj

    def _parse_image_object(self, obj: Dict) -> ImageObject:
        """Parse an image object from the YAML data."""
        # Extract image properties
        source = obj.get('source', '')
        x = convert_to_pt(obj.get('x', 10))
        y = convert_to_pt(obj.get('y', 10))
        width = convert_to_pt(obj.get('width', 20))
        height = convert_to_pt(obj.get('height', 20))
        monochrome = obj.get('monochrome', True)
        transparency = obj.get('transparency', False)
        transparency_color = obj.get('transparency_color', "#FFFFFF")
        name = obj.get('name', None)  # Get the name property if provided

        # Create image object
        image_obj = ImageObject(
            file_path=source,
            x=x,
            y=y,
            width=width,
            height=height,
            monochrome=monochrome,
            transparency=transparency,
            transparency_color=transparency_color,
            name=name  # Include the name property
        )

        return image_obj

    def _parse_group_object(self, obj: Dict) -> GroupObject:
        """Parse a group object and its child objects from the YAML data."""
        # Extract group properties
        x = convert_to_pt(obj.get('x', 0))  # Default x to 0
        y = convert_to_pt(obj.get('y', 0))  # Default y to 0
        width = convert_to_pt(obj.get('width', 'auto'))
        height = convert_to_pt(obj.get('height', 'auto'))

        # Get layout properties
        direction = obj.get('direction', 'row')
        justify = obj.get('justify', 'start')
        align = obj.get('align', 'start')
        gap = obj.get('gap', 0)
        padding = obj.get('padding', 0)
        wrap = obj.get('wrap', False)

        # Visual properties
        background_color = obj.get('background_color', '#FFFFFF')
        border_style = obj.get('border_style', None)

        # Identifier
        group_id = obj.get('id', None)
        name = obj.get('name', None)  # Get the name property if provided

        # Create group object with extracted properties
        group_obj = GroupObject(
            x=x,
            y=y,
            width=width,
            height=height,
            direction=direction,
            justify=justify,
            align=align,
            gap=gap,
            padding=padding,
            wrap=wrap,
            background_color=background_color,
            border_style=border_style,
            id=group_id,
            name=name  # Include the name property
        )

        # Parse child objects if any
        if 'objects' in obj and isinstance(obj['objects'], list):
            child_objects = self._parse_objects(obj['objects'])
            group_obj.objects = child_objects

        return group_obj