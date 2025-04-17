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
from ..models import (
    LabelConfig, TextObject, ImageObject, GroupObject, ContainerObject,
    FontInfo, StringItem, DEFAULT_ORIENTATION, BarcodeObject
)
from ..utils import convert_to_pt
from ..utils.conversion import MM_TO_PT, PT_TO_MM

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
                                config.margin = pt_value * PT_TO_MM
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
                # Capture any root-level layout properties
                elif key in ('direction', 'align', 'justify', 'gap', 'padding', 'wrap'):
                    setattr(config, key, value)

            # Check if we have any root-level layout properties
            root_layout_props = {
                prop: getattr(config, prop, None)
                for prop in ('direction', 'align', 'justify', 'gap', 'padding', 'wrap')
                if hasattr(config, prop)
            }

            # If we found any layout properties at the root level, store them on the config
            # but don't create an actual group element
            if root_layout_props:
                # We'll keep the layout properties on the config object
                # and handle the layout calculation separately
                config.has_root_layout = True

                # Make sure we have proper defaults for all properties
                if not hasattr(config, 'direction') or not config.direction:
                    config.direction = 'row'
                if not hasattr(config, 'align') or not config.align:
                    config.align = 'start'
                if not hasattr(config, 'justify') or not config.justify:
                    config.justify = 'start'
                if not hasattr(config, 'gap') or config.gap is None:
                    config.gap = 0
                if not hasattr(config, 'padding') or config.padding is None:
                    config.padding = 0
                if not hasattr(config, 'wrap') or config.wrap is None:
                    config.wrap = False

                # Set flag so generator knows to apply root-level layout
                config.apply_root_layout = True

                # Convert gap value to a numeric value if it has units
                if hasattr(config, 'gap') and config.gap is not None:
                    from ..utils.conversion import convert_unit
                    if isinstance(config.gap, str):
                        config.gap = int(convert_unit(config.gap))
                    elif isinstance(config.gap, float):
                        config.gap = int(config.gap)

            # No need to handle "flat structure" anymore as we're enforcing canonical structure

        # Apply flex layouts to all groups after parsing
        from ..layout_engine import FlexLayoutEngine
        layout_engine = FlexLayoutEngine()

        # Apply root layout first if needed
        if hasattr(config, 'apply_root_layout') and config.apply_root_layout:
            layout_engine.apply_root_layout(config)

        # Function to recursively apply layouts to all groups and containers
        def apply_layouts_recursive(objects):
            for obj in objects:
                if isinstance(obj, GroupObject):
                    # Apply layouts to nested groups first (bottom-up)
                    apply_layouts_recursive(obj.objects)
                    # Then apply layout to this group
                    layout_engine.apply_layout(obj)
                elif isinstance(obj, ContainerObject):
                    # Apply layouts to nested container objects first (bottom-up)
                    apply_layouts_recursive(obj.objects)
                    # Then apply layout to this container
                    layout_engine.apply_layout_to_container(obj)

        # Apply layouts to all groups in the config
        apply_layouts_recursive(config.objects)

        self.label_config = config
        return config

    def _parse_objects(self, objects_list: List[Dict]) -> List[Any]:
        """Parse the objects from the YAML data."""
        parsed_objects = []

        for obj in objects_list:
            # First check for shortcut syntax
            shortcut_found = False

            # Check for text/image/barcode/qr shortcut (object_type: content)
            for type_name in ['text', 'image', 'barcode', 'qr']:
                if type_name in obj:
                    # Create a copy of the object dictionary
                    new_obj = obj.copy()

                    # Set the content/data/source based on type
                    if type_name == 'text':
                        new_obj['content'] = new_obj.pop(type_name)
                    elif type_name == 'image':
                        new_obj['source'] = new_obj.pop(type_name)
                    elif type_name in ['barcode', 'qr']:
                        new_obj['data'] = new_obj.pop(type_name)
                        if type_name == 'qr':
                            new_obj['barcodeType'] = 'qr'
                        # If a type is specified for a barcode, use it as barcodeType
                        elif 'type' in new_obj:
                            new_obj['barcodeType'] = new_obj['type']
                            # Don't remove 'type' since it will be processed later
                        else:
                            new_obj['barcodeType'] = 'code128'  # Default type
                        type_name = 'barcode'

                    # Set the type
                    new_obj['type'] = type_name
                    obj = new_obj
                    shortcut_found = True
                    break

            # Check for line/rect/container/group shortcut (object_type: name)
            if not shortcut_found:
                for type_name in ['line', 'rect', 'container', 'group']:
                    if type_name in obj:
                        # Create a copy of the object dictionary
                        new_obj = obj.copy()

                        # Set the name
                        new_obj['name'] = new_obj.pop(type_name)

                        # Set the type
                        new_obj['type'] = type_name
                        obj = new_obj
                        break

            # Now process the object based on its type
            obj_type = obj.get('type', '').lower()

            if obj_type == 'text':
                parsed_objects.append(self._parse_text_object(obj))
            elif obj_type == 'image':
                parsed_objects.append(self._parse_image_object(obj))
            elif obj_type == 'group':
                parsed_objects.append(self._parse_group_object(obj))
            elif obj_type == 'container':
                parsed_objects.append(self._parse_container_object(obj))
            elif obj_type == 'barcode':
                parsed_objects.append(self._parse_barcode_object(obj))
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
                font_size = float(font_size.replace('mm', '')) * MM_TO_PT
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
        x = obj.get('x', 0)
        y = obj.get('y', 0)

        # Debug raw position values
        console.print(f"[green]Parsing group with raw position: x={x}, y={y}[/green]")

        # Check if x and y are explicitly provided in the YAML
        has_explicit_position = 'x' in obj or 'y' in obj

        # Check if position values have units before conversion
        if isinstance(x, str) and 'mm' in x:
            console.print(f"[yellow]Found mm value for x in YAML: {x}[/yellow]")
        if isinstance(y, str) and 'mm' in y:
            console.print(f"[yellow]Found mm value for y in YAML: {y}[/yellow]")

        # Store the original values before conversion
        x_original = x
        y_original = y

        # Convert to points after checking for existence
        x_pt = convert_to_pt(x)
        y_pt = convert_to_pt(y)

        # Debug converted values
        console.print(f"[blue]Converted position values: x={x_pt}, y={y_pt}[/blue]")

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
            x=x_pt,
            y=y_pt,
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

        # Mark if it has explicit positioning and store the original coordinates
        if has_explicit_position:
            group_obj._positioned = True
            group_obj._original_x = x_original
            group_obj._original_y = y_original
            console.print(f"[yellow]Storing original position values: x={x_original}, y={y_original}[/yellow]")

        # Parse child objects if any
        if 'objects' in obj and isinstance(obj['objects'], list):
            child_objects = self._parse_objects(obj['objects'])
            group_obj.objects = child_objects

        return group_obj

    def _parse_container_object(self, obj: Dict) -> ContainerObject:
        """Parse a container object and its child objects from the YAML data."""
        # Extract container properties
        x = obj.get('x', 0)
        y = obj.get('y', 0)

        # Debug raw position values
        console.print(f"[green]Parsing container with raw position: x={x}, y={y}[/green]")

        # Check if x and y are explicitly provided in the YAML
        has_explicit_position = 'x' in obj or 'y' in obj

        # Store the original values before conversion
        x_original = x
        y_original = y

        # Check if position values have units before conversion
        if isinstance(x, str) and 'mm' in x:
            console.print(f"[yellow]Found mm value for x in YAML: {x}[/yellow]")
        if isinstance(y, str) and 'mm' in y:
            console.print(f"[yellow]Found mm value for y in YAML: {y}[/yellow]")

        # Convert to points after checking for existence
        x_pt = convert_to_pt(x)
        y_pt = convert_to_pt(y)

        # Debug converted values
        console.print(f"[blue]Converted position values: x={x_pt}, y={y_pt}[/blue]")

        # Width and height are optional for containers and only used for layout calculations
        width = convert_to_pt(obj.get('width', None)) if 'width' in obj else None
        height = convert_to_pt(obj.get('height', None)) if 'height' in obj else None

        # Get layout properties
        direction = obj.get('direction', 'row')
        justify = obj.get('justify', 'start')
        align = obj.get('align', 'start')
        gap = obj.get('gap', 0)
        padding = obj.get('padding', 0)
        wrap = obj.get('wrap', False)

        # Identifier
        container_id = obj.get('id', None)
        name = obj.get('name', None)  # Get the name property if provided

        # Create container object with extracted properties
        container_obj = ContainerObject(
            x=x_pt,
            y=y_pt,
            width=width,
            height=height,
            direction=direction,
            justify=justify,
            align=align,
            gap=gap,
            padding=padding,
            wrap=wrap,
            id=container_id,
            name=name
        )

        # Mark if it has explicit positioning and store original coordinates
        if has_explicit_position:
            container_obj._positioned = True
            container_obj._original_x = x_original
            container_obj._original_y = y_original
            console.print(f"[yellow]Storing original container position: x={x_original}, y={y_original}[/yellow]")

        # Parse child objects if any
        if 'objects' in obj and isinstance(obj['objects'], list):
            child_objects = self._parse_objects(obj['objects'])
            container_obj.objects = child_objects

        return container_obj

    def _parse_barcode_object(self, obj: Dict) -> Any:
        """Parse a barcode object from the YAML data."""
        # Get required fields - handle case-insensitive barcodeType
        barcode_type = obj.get('barcodeType', obj.get('type', 'qr')).lower()
        data = obj.get('data', '')

        # Get positioning
        x = convert_to_pt(obj.get('x', 0))
        y = convert_to_pt(obj.get('y', 0))

        # Size and other properties - default to size 4 (Medium Large) for QR codes
        size = obj.get('size', 4 if barcode_type == 'qr' else 30)

        # For QR codes, convert any size format to a standardized numeric value (1-5)
        if barcode_type == 'qr':
            # Standardize on numeric values 1-5 for size
            standardized_size = self._standardize_qr_size(size)
            size = standardized_size

            # If a cellSize is directly specified, convert it to standardized size too
            if 'cellSize' in obj:
                cellSize = obj['cellSize']
                standardized_cellSize = self._standardize_qr_size(cellSize)
                obj['cellSize'] = standardized_cellSize
        else:
            # For other barcode types, convert to points
            size = convert_to_pt(size)

        # Handle the renamed parameter: correction vs errorCorrection (case-insensitive)
        error_correction = None
        for key in ['correction', 'errorCorrection', 'error_correction', 'ecc']:
            if key in obj:
                error_correction = obj[key]
                break
        if error_correction is None:
            error_correction = 'M'  # Default to Medium error correction

        # Create barcode object with specified type
        barcode = BarcodeObject(
            type=barcode_type,
            data=data,
            x=x,
            y=y,
            size=size,
            correction=error_correction.upper()  # Ensure uppercase for consistency
        )

        # For QR codes, we'll leave the width/height at their defaults
        # The generator will calculate appropriate values based on the size (1-5)
        # For non-QR codes, use the provided width/height or size
        if barcode_type != 'qr':
            # Only override width/height for non-QR codes
            width_value = obj.get('width', size)
            height_value = obj.get('height', size)

            # Convert to points if needed
            if isinstance(width_value, str) and not width_value.endswith('pt'):
                width_value = convert_to_pt(width_value)
            if isinstance(height_value, str) and not height_value.endswith('pt'):
                height_value = convert_to_pt(height_value)

            # Assign to the object properties
            try:
                # Parse numeric values if possible
                if isinstance(width_value, str) and width_value.endswith('pt'):
                    barcode.width = int(float(width_value.rstrip('pt')))
                else:
                    barcode.width = int(float(width_value))

                if isinstance(height_value, str) and height_value.endswith('pt'):
                    barcode.height = int(float(height_value.rstrip('pt')))
                else:
                    barcode.height = int(float(height_value))
            except (ValueError, TypeError):
                # If conversion fails, leave at defaults
                console.print(f"[yellow]Warning: Invalid width/height for barcode, using defaults[/yellow]")

        # Define comprehensive property mappings with case-insensitive keys
        property_mappings = {
            # Common barcode properties
            'model': ['model', 'qr_model', 'Model'],
            'cellSize': ['cellSize', 'cell_size', 'cellsize', 'CellSize'],
            'margin': ['margin', 'Margin'],
            'version': ['version', 'qr_version', 'Version'],
            'humanReadable': ['humanReadable', 'human_readable', 'text', 'showText', 'HumanReadable'],
            'humanReadableAlignment': ['humanReadableAlignment', 'human_readable_alignment', 'textAlignment', 'HumanReadableAlignment'],
            'barWidth': ['barWidth', 'bar_width', 'barwidth', 'BarWidth'],
            'barRatio': ['barRatio', 'bar_ratio', 'barratio', 'BarRatio'],
            'checkDigit': ['checkDigit', 'check_digit', 'checkdigit', 'CheckDigit'],
            'autoLengths': ['autoLengths', 'auto_lengths', 'autolengths', 'AutoLengths'],
            'sameLengthBar': ['sameLengthBar', 'same_length_bar', 'samelengthbar', 'SameLengthBar'],
            'bearerBar': ['bearerBar', 'bearer_bar', 'bearerbar', 'BearerBar'],
            'zeroFill': ['zeroFill', 'zero_fill', 'zerofill', 'ZeroFill'],
            'lengths': ['lengths', 'Lengths', 'length', 'Length'],
            'removeParentheses': ['removeParentheses', 'remove_parentheses', 'removeparentheses', 'RemoveParentheses'],
            'startstopCode': ['startstopCode', 'startstop_code', 'startstopcode', 'startStopCode', 'StartStopCode'],

            # RSS (GS1 DataBar) specific attributes
            'rssModel': ['rssModel', 'rss_model', 'rssmodel', 'RssModel'],
            'column': ['column', 'Column'],
            'autoAdd01': ['autoAdd01', 'auto_add_01', 'autoadd01', 'AutoAdd01'],

            # PDF417 specific attributes
            'pdf417Model': ['pdf417Model', 'pdf417_model', 'pdf417model', 'Pdf417Model'],
            'aspect': ['aspect', 'Aspect'],
            'row': ['row', 'Row'],
            'eccLevel': ['eccLevel', 'ecc_level', 'ecclevel', 'EccLevel'],
            'joint': ['joint', 'Joint'],

            # DataMatrix specific attributes
            'dataMatrixModel': ['dataMatrixModel', 'data_matrix_model', 'datamatrixmodel', 'DataMatrixModel'],
            'macro': ['macro', 'Macro'],
            'fnc01': ['fnc01', 'Fnc01'],

            # MaxiCode specific attributes
            'maxiCodeModel': ['maxiCodeModel', 'maxi_code_model', 'maxicodemodel', 'MaxiCodeModel']
        }

        # Process each property with its possible key variations
        for prop_name, key_variations in property_mappings.items():
            for key in key_variations:
                if key in obj:
                    value = obj[key]
                    # Convert boolean strings to actual booleans
                    if isinstance(value, str) and value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    setattr(barcode, prop_name, value)
                    break

        # Special handling for protocol (used in XML output)
        # Map from lowercase type to proper protocol value
        protocol_mapping = {
            'qr': 'QRCODE',
            'code39': 'CODE39',
            'code128': 'CODE128',
            'ean128': 'EAN128',
            'itf25': 'ITF25',
            'codabar': 'CODABAR',
            'upca': 'UPCA',
            'upce': 'UPCE',
            'ean13': 'EAN13',
            'ean8': 'EAN8',
            'isbn2': 'ISBN2',
            'isbn5': 'ISBN5',
            'postnet': 'POSTNET',
            'imb': 'IMB',
            'laserbarcode': 'LASERBARCODE',
            'rss': 'RSS',
            'pdf417': 'PDF417',
            'datamatrix': 'DATAMATRIX',
            'maxicode': 'MAXICODE'
        }
        barcode.protocol = protocol_mapping.get(barcode_type.lower(), barcode_type.upper())

        return barcode

    def _standardize_qr_size(self, size_value) -> int:
        """
        Convert any QR code size format to a standardized numeric value (1-5).

        Args:
            size_value: Input size which could be a string like "small", a number like 2,
                        or a point size like "1.2pt"

        Returns:
            An integer from 1-5 representing the standardized size
        """
        # QR size mapping - this is a subset of what's in BarcodeObject
        qr_size_mapping = {
            # Point sizes
            "0.8pt": 1,
            "1.2pt": 2,
            "1.6pt": 3,
            "2pt": 4,
            "2.4pt": 5,

            # String aliases (case insensitive)
            "small": 1,
            "sm": 1,
            "small medium": 2,
            "small-medium": 2,
            "smallmedium": 2,
            "medium small": 2,
            "medium-small": 2,
            "mediumsmall": 2,
            "mdsm": 2,
            "smmd": 2,
            "medium": 3,
            "md": 3,
            "medium large": 4,
            "medium-large": 4,
            "mediumlarge": 4,
            "largemedium": 4,
            "large medium": 4,
            "large-medium": 4,
            "large": 5,
            "mdlg": 4,
            "lgmd": 4,
            "large": 5,
            "lg": 5
        }

        # Handle string values
        if isinstance(size_value, str):
            # If it's already a number string like "1", "2", etc.
            if size_value.isdigit() and 1 <= int(size_value) <= 5:
                return int(size_value)

            # If it's a point size like "0.8pt"
            if size_value.endswith("pt"):
                return qr_size_mapping.get(size_value, 4)  # Default to 4 if not found

            # If it's a string alias like "small", "medium", etc.
            return qr_size_mapping.get(size_value.lower(), 4)  # Default to 4 if not found

        # Handle numeric values directly
        if isinstance(size_value, (int, float)):
            size_int = int(size_value)
            # If it's already in the 1-5 range, use it directly
            if 1 <= size_int <= 5:
                return size_int

        # Default to size 4 (Medium Large)
        return 4