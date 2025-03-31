#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
change-lbx.py - Brother P-touch LBX Label File Modifier

A utility for customizing Brother P-touch label (.lbx) files by modifying font size,
label width, vertical alignment, image scaling, text positioning, and text content.

Author: JD Lien
Created: 2025
License: MIT

Example usage to convert a BrickArchitect label:
- From 12mm to 24mm
- Using 14pt font
- Centering elements vertically
- Scaling images to 150% of original size
- Setting text margin to 0.5mm from images

python3 change-lbx.py label.lbx label-24mm.lbx -f 14 -l 24 -c -s 1.5 -m 0.5

Text editing examples:
- Convert dimension notation (2x2 to 2×2): --text-tweaks
- Find and replace: --find "old text" --replace "new text"
- Regex replacement: --find r"(\\d+)x(\\d+)" --replace r"\\1×\\2" --regex
- Case-insensitive search: --find "Text" --replace "NEW TEXT" --ignore-case
- Compact multi-line text: automatically combines first two lines with a space when text has more than two lines (enabled by default with --text-tweaks)

Requirements:
- typer: Modern CLI interface
- rich: Enhanced terminal output
- colorama: Cross-platform colored terminal output
- lxml: XML handling with parent node support
- lbx_text_edit.py: Required module for text editing (must be in same directory)

Install dependencies with:
pip install typer rich colorama lxml

To do:
- Allow generating custom labels from a template
  - Support changing text
  - Change images



"""

import sys
import os
import zipfile
import shutil
import tempfile
import platform
import subprocess
import re
from typing import Optional, List, Dict, Any, Union, Tuple
from pathlib import Path
from lxml.etree import _Element as Element, _ElementTree as ElementTree

# Function to check dependencies before importing them
def check_and_import_dependencies():
    dependencies = ["lxml", "rich", "colorama", "typer"]
    missing = []

    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Installing missing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

    # Check for lbx_text_edit.py in the same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lbx_text_edit_path = os.path.join(script_dir, 'lbx_text_edit.py')

    if not os.path.exists(lbx_text_edit_path):
        print(f"Error: Required module 'lbx_text_edit.py' not found in {script_dir}")
        print("Please make sure lbx_text_edit.py is in the same directory as this script.")
        sys.exit(1)

check_and_import_dependencies()

import lxml.etree as ET
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table
import colorama
from colorama import Fore, Style
import typer

# Import LBXTextEditor directly
from lbx_text_edit import LBXTextEditor

# Initialize colorama for cross-platform colored output
colorama.init(autoreset=True)

# Initialize Typer app and Rich console
app = typer.Typer(help="Brother P-touch LBX Label File Modifier", add_completion=False)
console = Console()

# Global configuration
class Config:
    """Global configuration for the application."""
    def __init__(self):
        # Runtime settings
        self.verbose: bool = False

        # Unit conversion constants
        self.MM_TO_PT: float = 2.8  # Millimeters to points conversion
        self.BROTHER_UNITS_MULTIPLIER: float = 72/20  # Typography points to Brother units

        # Printer constants
        self.TRUE_LEFT_EDGE: float = 5.6  # True printable left edge in points
        self.DEFAULT_HEIGHT: float = 2834.4  # Default height for all label sizes
        self.TEXT_MARGIN_OFFSET: float = 4.3  # Text Y position offset from margin

        # Printer compatibility settings
        self.LARGE_FORMAT_PRINTER_ID: str = "30256"
        self.LARGE_FORMAT_PRINTER_NAME: str = "Brother PT-P710BT"

        # Label tape format codes (mm size to format code)
        self.FORMAT_CODES: dict = {
            9: '258',
            12: '259',
            18: '260',
            24: '261'
        }

        # Label tape configurations
        self.LABEL_CONFIGS: dict = {
            9: {'width': 25.6, 'margin_y': 2.8},
            12: {'width': 33.6, 'margin_y': 2.8},
            18: {'width': 51.2, 'margin_y': 3.2},
            24: {'width': 68.0, 'margin_y': 8.4}
        }

        # XML namespaces
        self.NS: dict = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
            'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
            'image': 'http://schemas.brother.info/ptouch/2007/lbx/image'
        }

config = Config()

# Message classes for logging
from enum import Enum, auto
class MessageClass(Enum):
    ERROR = auto()      # Always shown, indicates failure
    WARNING = auto()    # Always shown, indicates potential issues
    SUCCESS = auto()    # Always shown, indicates successful operations
    INFO = auto()       # Only shown in verbose mode, general information

def log_message(message: str, msg_class: MessageClass = MessageClass.INFO) -> None:
    """
    Log a message to the console with appropriate styling based on message class.
    Uses Rich's markup syntax to style numbers and units consistently.
    """
    # Define styles for different message classes
    styles = {
        MessageClass.ERROR: "[bold red]",
        MessageClass.WARNING: "[yellow]",
        MessageClass.SUCCESS: "[green]",
        MessageClass.INFO: ""
    }

    # Only show INFO messages in verbose mode
    if msg_class == MessageClass.INFO and not config.verbose:
        return

    # Apply message class style
    style = styles[msg_class]

    # First, style numbers with units (pt, mm)
    styled_message = re.sub(
        r'(\d+\.?\d*)(pt|mm)',
        r'[bold cyan]\1[/][cyan]\2[/]',
        message
    )

    # Then, style standalone decimal numbers
    styled_message = re.sub(
        r'(\d+\.\d+)',
        r'[bold cyan]\1[/]',
        styled_message
    )

    # Print with the combined styles
    console.print(f"{style}{styled_message}[/]" if style else styled_message, highlight=False)

def parse_unit(value: str) -> float:
    """Convert a value with unit (e.g. '10pt') to a float."""
    if not value:
        return 0.0

    # Strip unit suffix (like 'pt')
    return float(re.sub(r'[^\d.]', '', value))


def get_label_config(label_size: int) -> Dict[str, Any]:
    """
    Get the configuration values for a specific label size.

    Args:
        label_size: Label width in mm (9, 12, 18, or 24)

    Returns:
        Dictionary with label configuration parameters
    """
    # Get base config from LABEL_CONFIGS, defaulting to 12mm if size not found
    base_config = config.LABEL_CONFIGS.get(label_size, config.LABEL_CONFIGS[12])

    # Calculate background height as width minus margins
    bg_height = base_config['width'] - (base_config['margin_y'] * 2)

    # Create config with derived/additional fields
    config_dict = {
        'width': base_config['width'],
        'height': config.DEFAULT_HEIGHT,
        'marginLeft': base_config['margin_y'],  # Affects vertical positioning in landscape
        'marginRight': base_config['margin_y'],  # Affects vertical positioning in landscape
        'bg_height': bg_height,
        'bg_y': base_config['margin_y'],  # bg_y is always set to margin value
        'format': config.FORMAT_CODES.get(label_size, config.FORMAT_CODES[12])  # Default to 12mm format if not found
    }

    return config_dict


def update_label_tape_size(root: Element, label_size: int) -> None:
    """
    Update the label size to a different "width" of tape, affecting the height of landscape labels,
    or the width of portrait labels.

    Args:
        root: Root element of the XML tree
        label_size: Label size in mm
    """
    # Get label configuration
    label_config = get_label_config(label_size)

    paper_elem = root.find('.//style:paper', namespaces=config.NS)
    if paper_elem is not None:
        # Get original margin before updating it
        original_margin = float(paper_elem.get('marginLeft', '0pt').replace('pt', ''))
        new_margin = label_config['marginLeft']

        # Update paper element attributes
        paper_elem.set('width', f"{label_config['width']}pt")
        log_message(f"Updated label width to {label_config['width']}pt ({label_size}mm)")

        paper_elem.set('marginLeft', f"{label_config['marginLeft']}pt")
        paper_elem.set('marginRight', f"{label_config['marginRight']}pt")
        log_message(f"Updated margins to {label_config['marginLeft']}pt on both sides")

        # Update format attribute for different label sizes
        paper_elem.set('format', label_config['format'])
        log_message(f"Updated format to {label_config['format']} for {label_size}mm tape")

        # Update Y positions of all objects to account for margin change
        update_object_y_positions(root, original_margin, new_margin)


def update_object_y_positions(root: Element, original_margin: float, new_margin: float) -> None:
    """
    Update Y positions of objects to match the new margin.

    Args:
        root: Root element of the XML tree
        original_margin: Original marginLeft value in points
        new_margin: New marginLeft value in points
    """
    if original_margin == new_margin:
        return  # No change needed

    # Calculate the Y-position offset (difference between new and old margins)
    offset = new_margin - original_margin

    if offset == 0:
        return

    log_message(f"Adjusting object Y positions by {offset}pt to match new margins")

    # Update background element Y position
    bg_elem = root.find('.//style:backGround', namespaces=config.NS)
    if bg_elem is not None:
        old_y = float(bg_elem.get('y', '0pt').replace('pt', ''))
        new_y = old_y + offset
        bg_elem.set('y', f"{new_y}pt")
        log_message(f"Updated background Y position from {old_y}pt to {new_y}pt")

    # Get all object elements
    object_styles = root.findall('.//pt:objectStyle', namespaces=config.NS)

    for obj in object_styles:
        # Get parent element to determine if it's text or image
        parent = obj.getparent()
        is_image = parent is not None and str(parent.tag).endswith('}image')
        is_text = parent is not None and str(parent.tag).endswith('}text')

        # Update Y position
        if 'y' in obj.attrib:
            old_y = float(obj.get('y', '0pt').replace('pt', ''))

            # For text elements: maintain the offset from margin
            if is_text:
                # Text Y position is consistently offset from margin
                new_y = new_margin + config.TEXT_MARGIN_OFFSET
            else:
                # For other elements, apply the offset directly
                new_y = old_y + offset

            obj.set('y', f"{new_y}pt")

            obj_type = "text" if is_text else "image" if is_image else "object"
            log_message(f"Updated {obj_type} Y position from {old_y}pt to {new_y}pt")

            # For images, also update the orgPos Y position
            if is_image and parent is not None:
                org_pos = parent.find('.//image:orgPos', namespaces=config.NS)
                if org_pos is not None:
                    old_org_y = float(org_pos.get('y', '0pt').replace('pt', ''))
                    new_org_y = old_org_y + offset
                    org_pos.set('y', f"{new_org_y}pt")
                    log_message(f"Updated image orgPos Y from {old_org_y}pt to {new_org_y}pt")


def update_background(root: Element, label_config: Dict[str, Any]) -> None:
    """
    Update the background element dimensions in the XML.
    Only updates height and Y position, preserving the original width and X position.

    Args:
        root: Root element of the XML tree
        label_config: Label configuration dictionary
    """
    bg_elem = root.find('.//style:backGround', namespaces=config.NS)
    if bg_elem is not None:
        # Get current background width (preserved)
        current_width = parse_unit(bg_elem.get('width', '56.2pt'))  # Default to 56.2pt if not found

        # Only update height - X position stays at config.TRUE_LEFT_EDGE
        bg_elem.set('height', f"{label_config['bg_height']}pt")
        # Note: Y position is already updated by update_object_y_positions function
        log_message(f"Updated background dimensions: {current_width}pt × {label_config['bg_height']}pt")


def update_font_size(root: Element, font_size: int, min_weight: Optional[int] = None, max_weight: Optional[int] = None) -> None:
    """
    Update font size in text elements of an LBX file.

    Args:
        root: Element of the XML tree
        font_size: New font size in pt
        min_weight: Optional minimum font weight to match (inclusive)
        max_weight: Optional maximum font weight to match (inclusive)
    """
    # Convert standard typographic points to Brother's internal units
    org_size = font_size * config.BROTHER_UNITS_MULTIPLIER

    # Find all ptFontInfo elements that contain both logFont and fontExt
    font_infos = root.findall('.//text:ptFontInfo', namespaces=config.NS)
    for font_info in font_infos:
        # Get the logFont element within this ptFontInfo
        log_font = font_info.find('.//text:logFont', namespaces=config.NS)
        if log_font is not None:
            # Get the weight attribute
            weight = int(log_font.get('weight', '400'))

            # Check if weight is within the specified range
            weight_matches = True
            if min_weight is not None and weight < min_weight:
                weight_matches = False
            if max_weight is not None and weight > max_weight:
                weight_matches = False

            if weight_matches:
                # Update all fontExt elements within this ptFontInfo
                font_exts = font_info.findall('.//text:fontExt', namespaces=config.NS)
                for font_elem in font_exts:
                    font_elem.set('size', f"{font_size}pt")
                    font_elem.set('orgSize', f"{org_size}pt")
                    log_message(f"Updated font size to {font_size}pt (orgSize: {org_size}pt) for weight {weight}")


def classify_elements(root: Element) -> Tuple[List[Element], List[Element]]:
    """
    Classify elements in the XML as either image elements or text elements.

    Args:
        root: Root element of the XML tree

    Returns:
        Tuple of (image_elements, text_elements)
    """
    # Get all objects
    object_styles = root.findall('.//pt:objectStyle', namespaces=config.NS)

    # Collect images and text elements
    image_elements = []
    text_elements = []

    for element in object_styles:
        # Determine if element is an image or text
        parent = element.getparent()
        is_image = parent is not None and str(parent.tag).endswith('}image')
        is_text = parent is not None and str(parent.tag).endswith('}text')

        if is_image:
            image_elements.append(element)
        elif is_text:
            text_elements.append(element)

    return (image_elements, text_elements)


def scale_images(image_elements: List[Element], image_scale: float, label_size: int) -> float:
    """
    Scale and position images based on the scale factor and label size.

    Args:
        image_elements: List of image elements to scale
        image_scale: Scale factor for images (1.0 means no scaling)
        label_size: Label width in mm

    Returns:
        float: The maximum right edge of all images after scaling and positioning
    """
    # If no images, return the left margin
    if not image_elements:
        return config.TRUE_LEFT_EDGE

    # If no scaling is needed, calculate the maximum right edge without changing positions
    if image_scale == 1.0:
        log_message(f"No image scaling required, preserving original horizontal positions")
        max_right_edge = config.TRUE_LEFT_EDGE
        # Find the rightmost edge of all images without modifying their positions
        for element in image_elements:
            current_x = parse_unit(element.get('x', '0pt'))
            width = parse_unit(element.get('width', '0pt'))
            right_edge = current_x + width
            max_right_edge = max(max_right_edge, right_edge)
        return max_right_edge

    # Process each image element
    max_right_edge = config.TRUE_LEFT_EDGE
    for element in image_elements:
        # Get current values
        current_x = parse_unit(element.get('x', '0pt'))
        current_y = parse_unit(element.get('y', '0pt'))
        current_width = parse_unit(element.get('width', '0pt'))
        current_height = parse_unit(element.get('height', '0pt'))

        # Calculate new dimensions (maintaining aspect ratio)
        new_width = current_width * image_scale
        new_height = current_height * image_scale

        # Always position at the absolute left printable edge
        new_x = config.TRUE_LEFT_EDGE
        log_message(f"Positioning image at absolute left printable edge: {config.TRUE_LEFT_EDGE}pt")

        # Calculate the right edge of this image
        right_edge = new_x + new_width
        max_right_edge = max(max_right_edge, right_edge)

        # Use the current Y position, which is already adjusted by update_object_y_positions
        new_y = current_y

        # Output the scaling and positioning
        log_message(f"Image scaled from {current_width:.1f}x{current_height:.1f}pt to {new_width:.1f}x{new_height:.1f}pt")
        log_message(f"Image position adjusted from ({current_x:.1f}, {current_y:.1f})pt to ({new_x:.1f}, {new_y:.1f})pt")

        # Update the element attributes
        element.set('x', f"{new_x}pt")
        element.set('y', f"{new_y}pt")
        element.set('width', f"{new_width}pt")
        element.set('height', f"{new_height}pt")

        # Get the parent image element
        parent = element.getparent()
        if parent is not None and str(parent.tag).endswith('}image'):
            # Update orgPos element
            org_pos = parent.find('.//image:orgPos', namespaces=config.NS)
            if org_pos is not None:
                org_pos.set('x', f"{new_x}pt")
                org_pos.set('y', f"{new_y}pt")
                org_pos.set('width', f"{new_width}pt")
                org_pos.set('height', f"{new_height}pt")
                log_message(f"Updated image orgPos to {new_width}x{new_height}pt")

            # Update trimming dimensions
            image_style = parent.find('.//image:imageStyle', namespaces=config.NS)
            if image_style is not None:
                trimming = image_style.find('.//image:trimming', namespaces=config.NS)
                if trimming is not None:
                    # Get original trimming dimensions
                    trim_width = parse_unit(trimming.get('trimOrgWidth', '0pt'))
                    trim_height = parse_unit(trimming.get('trimOrgHeight', '0pt'))

                    # Scale trimming dimensions
                    new_trim_width = trim_width * image_scale
                    new_trim_height = trim_height * image_scale

                    # Update trimming dimensions
                    trimming.set('trimOrgWidth', f"{new_trim_width}pt")
                    trimming.set('trimOrgHeight', f"{new_trim_height}pt")
                    log_message(f"Updated image trimming dimensions from {trim_width}x{trim_height}pt to {new_trim_width}x{new_trim_height}pt")

    return max_right_edge


def position_text(text_elements: List[Element], max_image_right_edge: float, label_size: int, text_margin_pt: float, image_scale: float) -> None:
    """
    Position text elements after images.

    Args:
        text_elements: List of text elements to position
        max_image_right_edge: Rightmost edge of all images
        label_size: Label width in mm
        text_margin_pt: Margin between image and text in points
        image_scale: Scale factor used for images (used to determine if repositioning is needed)
    """
    if not text_elements:
        return

    # Only reposition text if image scaling was applied
    if image_scale != 1.0:
        # Calculate text X position based on the right edge of images plus margin
        text_x = max_image_right_edge + text_margin_pt
        mm_margin = text_margin_pt/2.8
        log_message(f"Positioning text at x={text_x}pt ({mm_margin:.1f}mm after images)")

        for element in text_elements:
            element.set('x', f"{text_x}pt")
            log_message(f"Moved text element to x={text_x}pt")
    else:
        log_message(f"Preserving original horizontal text positions (no image scaling applied)")


def center_elements_vertically(root: Element, label_width: float) -> None:
    """
    Center elements vertically within the background area of the label.

    Args:
        root: Root element of the XML tree
        label_width: Width of the label in points (not used for centering)
    """
    # Get the background element to determine the printable area
    bg_elem = root.find('.//style:backGround', namespaces=config.NS)
    if bg_elem is None:
        log_message("[yellow]Warning: No background element found, skipping vertical centering")
        return

    # Get the paper element to determine label size
    paper_elem = root.find('.//style:paper', namespaces=config.NS)
    if paper_elem is None:
        log_message("[yellow]Warning: No paper element found, skipping vertical centering")
        return

    # Get the label width to determine size
    paper_width = float(paper_elem.get('width', '0pt').replace('pt', ''))

    # Map paper widths to background heights for centering
    # These heights match what P-Touch Editor uses for vertical centering
    width_to_height = {
        25.6: 20.0,    # 9mm
        33.6: 28.0,    # 12mm
        51.2: 44.8,    # 18mm
        68.0: 51.2     # 24mm
    }

    # Get the background height based on paper width
    bg_height = width_to_height.get(paper_width, 28.0)  # Default to 12mm height if not found
    bg_y = float(bg_elem.get('y', '0pt').replace('pt', ''))
    center_of_background = bg_y + (bg_height / 2)

    # Get all objects that need centering
    object_styles = root.findall('.//pt:objectStyle', namespaces=config.NS)

    if not object_styles:
        log_message("[yellow]Warning: No objects found to center")
        return

    log_message(f"Paper width: {paper_width}pt")
    log_message(f"Background area: y={bg_y}pt, height={bg_height}pt")
    log_message(f"Center of background: {center_of_background}pt")

    # Center each object individually
    for obj in object_styles:
        # Get current object position and dimensions
        orig_y = float(obj.get('y', '0pt').replace('pt', ''))
        obj_height = float(obj.get('height', '0pt').replace('pt', ''))

        # Calculate the center of the current object
        center_of_object = orig_y + (obj_height / 2)

        # Calculate how far the object's center is from the background's center
        offset = center_of_background - center_of_object

        # Calculate new y position that will center the object
        new_y = orig_y + offset

        # Ensure the object stays within the background bounds
        if new_y < bg_y:
            new_y = bg_y
        elif new_y + obj_height > bg_y + bg_height:
            new_y = bg_y + bg_height - obj_height

        # Update the object's position
        obj.set('y', f"{new_y}pt")
        log_message(f"Centered object (height={obj_height}pt) from y={orig_y}pt to y={new_y}pt")

        # Also update corresponding image orgPos if exists
        parent = obj.getparent()
        if parent is not None and str(parent.tag).endswith('}image'):
            org_pos = parent.find('.//image:orgPos', namespaces=config.NS)
            if org_pos is not None:
                org_pos.set('y', f"{new_y}pt")
                log_message(f"Updated image orgPos y to {new_y}pt")

    log_message(f"All objects have been centered within the background area")


def extract_and_parse_lbx(input_file: str, temp_dir: str) -> Tuple[ElementTree, str]:
    """
    Extract LBX file (ZIP) and parse the XML.

    Args:
        input_file: Path to the input LBX file
        temp_dir: Directory to extract the files to

    Returns:
        Tuple of (ET.ElementTree, xml_path)
    """
    # Extract the LBX file (it's a ZIP file)
    with zipfile.ZipFile(input_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)

    # Path to the extracted label.xml file
    xml_path = os.path.join(temp_dir, 'label.xml')

    # Register XML namespaces
    for prefix, uri in config.NS.items():
        ET.register_namespace(prefix, uri)

    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.parse(xml_path, parser)

    return (tree, xml_path)


def apply_compatibility_tweaks(root: Element, label_size: int) -> None:
    """
    Apply compatibility tweaks to the label file to ensure it works properly with P-touch Editor.

    Args:
        root: Root element of the XML tree
        label_size: Target label size in mm
    """
    # Update the XML document version and generator
    if str(root.tag).endswith('}document'):
        # Set version to 1.9 which is used by modern P-touch Editor
        root.set('version', '1.9')

        # Update the generator to show it was modified by this tool
        root.set('generator', 'com.jdlien.lbx-utils')
        log_message(f"Updated document version to 1.9 and generator to com.jdlien.lbx-utils")

    # Update printer compatibility for wider tape formats
    paper_elem = root.find('.//style:paper', namespaces=config.NS)
    if paper_elem is not None:
        # Only update for 18mm and 24mm labels which need a compatible printer
        if label_size >= 18:
            # Always update printer ID and name for large format labels
            paper_elem.set('printerID', config.LARGE_FORMAT_PRINTER_ID)
            paper_elem.set('printerName', config.LARGE_FORMAT_PRINTER_NAME)
            log_message(f"Updated printer to {config.LARGE_FORMAT_PRINTER_NAME} for compatibility with {label_size}mm tape")


def save_lbx(tree: ElementTree, xml_path: str, output_file: str, temp_dir: str) -> None:
    """
    Save modified XML and create a new LBX file.

    Args:
        tree: ElementTree with modifications
        xml_path: Path to the XML file
        output_file: Path for the modified output file
        temp_dir: Directory with extracted files
    """
    # Save the modified XML
    tree.write(xml_path, encoding='UTF-8', xml_declaration=True)

    # Verify that the XML has been properly written before creating the LBX
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
        if config.verbose:
            log_message(f"XML content before creating LBX (first 100 chars): {xml_content[:100]}")

    # Create a new ZIP file with the modified content
    with zipfile.ZipFile(output_file, 'w') as zipf:
        for root_dir, _, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root_dir, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)


def get_current_label_size(root: Element) -> Optional[int]:
    """
    Get the current label size in mm from the XML.

    Args:
        root: Root element of the XML tree

    Returns:
        Label size in mm or None if it couldn't be determined
    """
    paper_elem = root.find('.//style:paper', namespaces=config.NS)
    if paper_elem is None:
        return None

    # Get the format attribute which contains the label size code
    format_code = paper_elem.get('format')

    # Map format codes to mm sizes
    format_to_size = {
        '258': 9,
        '259': 12,
        '260': 18,
        '261': 24
    }

    # Try to determine from format code first
    if format_code in format_to_size:
        return format_to_size[format_code]

    # If format code not found, estimate from width
    width = float(paper_elem.get('width', '0pt').replace('pt', ''))

    # Approximate conversion from points to mm size
    if width <= 25.6:
        return 9
    elif width <= 33.6:
        return 12
    elif width <= 51.2:
        return 18
    else:
        return 24


def get_text_elements(root: Element) -> List[Element]:
    """
    Get all text elements from the XML.

    Args:
        root: Root element of the XML tree

    Returns:
        List of text elements
    """
    text_elements = []

    # Find all object styles
    object_styles = root.findall('.//pt:objectStyle', namespaces=config.NS)

    for element in object_styles:
        # Check if the parent is a text element
        parent = element.getparent()
        if parent is not None and str(parent.tag).endswith('}text'):
            text_elements.append(element)

    return text_elements


def get_image_elements(root: Element) -> List[Element]:
    """
    Get all image elements from the XML.

    Args:
        root: Root element of the XML tree

    Returns:
        List of image elements
    """
    image_elements = []

    # Find all object styles
    object_styles = root.findall('.//pt:objectStyle', namespaces=config.NS)

    for element in object_styles:
        # Check if the parent is an image element
        parent = element.getparent()
        if parent is not None and str(parent.tag).endswith('}image'):
            image_elements.append(element)

    return image_elements


def update_font_sizes(text_elements: List[Element], target_font_size: float) -> None:
    """
    Update font sizes in text elements to a specific point size.

    Args:
        text_elements: List of text elements to update
        target_font_size: Target font size in points
    """
    if not text_elements:
        return

    log_message(f"Setting font size to {target_font_size}pt")

    # Process each text element
    for element in text_elements:
        # Find the text element's parent
        parent = element.getparent()
        if parent is None:
            continue

        # Update main fontExt element
        font_ext = parent.find('.//text:fontExt', namespaces=config.NS)
        if font_ext is not None:
            current_size = parse_unit(font_ext.get('size', '9pt'))
            current_org_size = parse_unit(font_ext.get('orgSize', '32.4pt'))

            # Keep the original orgSize ratio
            org_size_ratio = current_org_size / current_size
            new_org_size = target_font_size * org_size_ratio

            font_ext.set('size', f"{target_font_size}pt")
            font_ext.set('orgSize', f"{new_org_size}pt")

            if current_size != target_font_size:
                log_message(f"Updated main font size from {current_size:.1f}pt to {target_font_size}pt")

        # Update textStyle orgPoint
        text_style = parent.find('.//text:textStyle', namespaces=config.NS)
        if text_style is not None:
            current_org_point = parse_unit(text_style.get('orgPoint', '9pt'))
            text_style.set('orgPoint', f"{target_font_size}pt")
            if current_org_point != target_font_size:
                log_message(f"Updated textStyle orgPoint from {current_org_point:.1f}pt to {target_font_size}pt")

        # Update all stringItem fontExt elements
        for string_item in parent.findall('.//text:stringItem', namespaces=config.NS):
            string_font_ext = string_item.find('.//text:fontExt', namespaces=config.NS)
            if string_font_ext is not None:
                current_size = parse_unit(string_font_ext.get('size', '9pt'))
                current_org_size = parse_unit(string_font_ext.get('orgSize', '32.4pt'))

                # Keep the original orgSize ratio
                org_size_ratio = current_org_size / current_size
                new_org_size = target_font_size * org_size_ratio

                string_font_ext.set('size', f"{target_font_size}pt")
                string_font_ext.set('orgSize', f"{new_org_size}pt")

                if current_size != target_font_size:
                    log_message(f"Updated string item font size from {current_size:.1f}pt to {target_font_size}pt")


def tweak_text(root: Element, xml_path: str, options: Dict[str, Any] = {}) -> ElementTree:
    """
    Apply text tweaks to the content of text elements using LBXTextEditor.

    Supported transformations:
    - Converting dimension notation (e.g., "2x2" -> "2×2")
    - Custom find and replace operations
    - Regular expression replacements
    - Compact multi-line text by replacing first newline with space when text has > 2 lines

    Args:
        root: Root element of the XML tree
        xml_path: Path to the XML file for LBXTextEditor
        options: Dictionary of options for text tweaks, may include:
            - custom_replacements: List of (find, replace) tuples
            - regex_replacements: List of (pattern, replace) tuples for regex operations
            - ignore_case: Boolean to control case sensitivity
            - convert_dimension_notation: Boolean to control automatic dimension notation conversion
            - compact_multiline: Boolean to enable compacting multi-line text by replacing first newline with space

    Returns:
        Updated ElementTree with modifications
    """
    # Use LBXTextEditor for text editing
    log_message("Using LBXTextEditor for text tweaks")
    editor = LBXTextEditor()

    # Load the XML file
    editor.load(xml_path)
    total_replacements = 0

    # Default transformation: Convert dimension notation (2x2 -> 2×2)
    if options.get('convert_dimension_notation', True):
        # More robust pattern that handles various spacing and both lowercase and uppercase x
        replacements = editor.regex_find_replace_all(r'(\d+)\s*[xX]\s*(\d+)', r'\1×\2', case_sensitive=False)
        if replacements > 0:
            log_message(f"Converted {replacements} occurrences of dimension notation (e.g., '4 x 4' -> '4×4')")
            total_replacements += replacements

    # Compact multi-line text: replace first newline with space when text has more than two lines
    if options.get('compact_multiline', True):
        # Find text with at least two newlines (more than two lines)
        # Use a regex that matches a string containing at least two newlines
        # and replace only the first newline with a space
        replacements = editor.regex_find_replace_all(
            r'^([^\n]*)\n([^\n]*\n.+)$',
            r'\1 \2',
            case_sensitive=True
        )
        if replacements > 0:
            log_message(f"Compacted {replacements} multi-line text blocks by replacing first newline with space")
            total_replacements += replacements

    # Apply custom text replacements
    for find_text, replace_text in options.get('custom_replacements', []):
        replacements = editor.find_replace_all(find_text, replace_text, not options.get('ignore_case', False))
        if replacements > 0:
            log_message(f"Replaced {replacements} occurrences of '{find_text}' with '{replace_text}'")
            total_replacements += replacements

    # Apply regex replacements
    for pattern, replace_text in options.get('regex_replacements', []):
        replacements = editor.regex_find_replace_all(pattern, replace_text, not options.get('ignore_case', False))
        if replacements > 0:
            log_message(f"Applied regex replacement pattern '{pattern}' to {replacements} occurrences")
            total_replacements += replacements

    # Save changes if any replacements were made
    if total_replacements > 0:
        log_message(f"Made a total of {total_replacements} text replacements")
        editor.save(xml_path)

        # IMPORTANT: Reload the XML tree from the modified file
        parser = ET.XMLParser(remove_blank_text=True)
        updated_tree = ET.parse(xml_path, parser)
        return updated_tree
    else:
        log_message("No text replacements were needed")
        # Return the original tree if no changes were made
        parser = ET.XMLParser(remove_blank_text=True)
        return ET.parse(xml_path, parser)


def modify_lbx(lbx_file_path: str, output_file_path: str, options: Dict[str, Any]) -> None:
    """
    Modify a Brother P-touch LBX file with the given options.

    Args:
        lbx_file_path: Path to input LBX file
        output_file_path: Path to output LBX file
        options: Dictionary of modification options
    """
    # Set global verbosity from options
    config.verbose = options.get('verbose', False)
    log_message(f"Modifying file: {lbx_file_path}")

    # Create a temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract and parse the LBX file
        tree, xml_path = extract_and_parse_lbx(lbx_file_path, temp_dir)
        root = tree.getroot()

        # Get the current label width
        current_label_size = get_current_label_size(root)
        if current_label_size is None:
            log_message("Could not determine current label size", msg_class=MessageClass.ERROR)
            return

        log_message(f"Current label size: {current_label_size}mm")

        # Extract target label size from options
        label_size = options.get('label_size', current_label_size)
        log_message(f"Target label size: {label_size}mm")

        # Convert text margin from mm to points (1mm ≈ 2.8pt)
        text_margin = options.get('text_margin', 1.0)  # Default to 1.0mm
        text_margin_pt = text_margin * 2.8

        # Skip if the label size is the same and no other changes
        if label_size == current_label_size and not options.get('font_size') and not options.get('bold_font_size') and not options.get('image_scale'):
            log_message("No changes necessary - input and output sizes are the same", msg_class=MessageClass.WARNING)
            if options.get('force'):
                log_message("Force option specified - continuing anyway", msg_class=MessageClass.WARNING)
            else:
                # Apply compatibility tweaks before saving
                apply_compatibility_tweaks(root, label_size)
                save_lbx(tree, xml_path, output_file_path, temp_dir)
                return

        # If target label size is different, update it
        if label_size != current_label_size:
            log_message(f"Changing label size from {current_label_size}mm to {label_size}mm")
            update_label_tape_size(root, label_size)

        # Get text and image elements
        text_elements = get_text_elements(root)
        image_elements = get_image_elements(root)

        # Get the target font sizes and image scale
        target_font_size = options.get('font_size')
        bold_font_size = options.get('bold_font_size')
        image_scale = options.get('image_scale', 1.0)

        # Apply changes if needed
        if target_font_size is not None or bold_font_size is not None or image_scale != 1.0:
            # Update font sizes if specified
            if target_font_size is not None:
                # Update regular text (weights up to 599)
                update_font_size(root, target_font_size, max_weight=599)
                log_message(f"Updated regular text to {target_font_size}pt")

            if bold_font_size is not None:
                # Update bold text (weights 600 and above)
                update_font_size(root, bold_font_size, min_weight=600)
                log_message(f"Updated bold text to {bold_font_size}pt")

            # Scale images if requested
            if image_scale != 1.0:
                log_message(f"Scaling images by factor: {image_scale}")
            # Scale and position images
            max_image_right_edge = scale_images(image_elements, image_scale, label_size)

            # Position text elements after images
            position_text(text_elements, max_image_right_edge, label_size, text_margin_pt, image_scale)

            # Vertically center elements if requested
            if options.get('center_vertically', False):
                center_elements_vertically(root, label_size)
        else:
            log_message("No changes needed - keeping original font sizes and image dimensions", msg_class=MessageClass.SUCCESS)
            # Still need to find max_image_right_edge for text positioning
            max_image_right_edge = scale_images(image_elements, image_scale, label_size)
            # Position text elements after images (will preserve positions due to image_scale=1.0)
            position_text(text_elements, max_image_right_edge, label_size, text_margin_pt, image_scale)

        # Apply compatibility tweaks before any text tweaks
        apply_compatibility_tweaks(root, label_size)

        # Save the current state of the tree
        tree.write(xml_path, encoding='UTF-8', xml_declaration=True)

        # Apply text tweaks if requested
        if options.get('text_tweaks', False):
            log_message("Applying text tweaks...")

            # Prepare text tweak options
            text_options = {
                'convert_dimension_notation': True,  # Default transformation
                'custom_replacements': options.get('custom_replacements', []),
                'regex_replacements': options.get('regex_replacements', []),
                'ignore_case': options.get('ignore_case', False),
                'compact_multiline': options.get('compact_multiline', True)  # Enable compacting multi-line text by default
            }

            # Get the updated tree from tweak_text
            tree = tweak_text(root, xml_path, text_options)
        else:
            log_message("Skipping text tweaks (not requested)")

        # Save the modified file
        save_lbx(tree, xml_path, output_file_path, temp_dir)
        log_message(f"Created LBX file: {output_file_path}", msg_class=MessageClass.SUCCESS)

        # Open the file if requested (macOS only)
        if options.get('open_file', False) and platform.system() == 'Darwin':
            try:
                subprocess.run(['open', '-a', '/Applications/P-touch Editor.app', output_file_path])
                log_message("Opened file in P-touch Editor", msg_class=MessageClass.SUCCESS)
            except Exception as e:
                log_message(f"Warning: Could not open file: {str(e)}", msg_class=MessageClass.WARNING)


@app.command()
def main(
    input_file: str = typer.Argument(..., help="Input .lbx file to modify"),
    output_file: str = typer.Argument(..., help="Path for the modified output file"),
    label_size: int = typer.Option(12, "--label-size", "-l", help="Label tape size in mm (9, 12, 18, or 24)"),
    font_size: int = typer.Option(8, "--font-size", "-f", help="Font size in points for all text"),
    bold_font_size: Optional[int] = typer.Option(None, "--bold-font-size", "-b", help="Font size in points for bold text (weight >= 600)"),
    center_vertically: bool = typer.Option(False, "--center-vertically", "-c", help="Center elements vertically on the label"),
    image_scale: float = typer.Option(1.0, "--image-scale", "-s", help="Scale factor for images, e.g. 1.5 for 150%"),
    text_margin: float = typer.Option(1.0, "--text-margin", "-m", help="Margin between image and text in mm"),
    text_tweaks: bool = typer.Option(False, "--text-tweaks", "-t", help="Apply text tweaks (e.g., convert 'x' to '×' between numbers)"),
    find: Optional[str] = typer.Option(None, "--find", help="Text to find for replacement"),
    replace: Optional[str] = typer.Option(None, "--replace", help="Text to replace with"),
    regex: bool = typer.Option(False, "--regex", help="Use regular expressions for pattern matching"),
    ignore_case: bool = typer.Option(False, "--ignore-case", "-i", help="Ignore case in text replacements"),
    no_compact: bool = typer.Option(False, "--no-compact", help="Disable automatic compacting of multi-line text"),
    open_file: bool = typer.Option(False, "--open", "-o", help="Open the modified file in P-touch Editor after creation (macOS only)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging output")
) -> int:
    """
    Modify a Brother P-touch label (.lbx) file by changing font size, label width,
    vertical alignment, image scaling, and text positioning.
    """
    if not os.path.exists(input_file):
        log_message(f"Input file '{input_file}' not found.", msg_class=MessageClass.ERROR)
        return 1

    # Prepare text replacement options
    custom_replacements = []
    regex_replacements = []

    # If both find and replace are specified, add them to the appropriate list
    if find is not None and replace is not None:
        if regex:
            regex_replacements.append((find, replace))
        else:
            custom_replacements.append((find, replace))

    # Enable text tweaks if any text replacement options are specified
    if find is not None and replace is not None:
        text_tweaks = True
        log_message(f"Enabling text tweaks for {'regex' if regex else 'normal'} replacement", msg_class=MessageClass.INFO)

    try:
        # Pass options as a dictionary to the modify_lbx function
        modify_lbx(input_file, output_file, {
            'font_size': font_size,
            'bold_font_size': bold_font_size,
            'label_size': label_size,
            'center_vertically': center_vertically,
            'image_scale': image_scale,
            'text_margin': text_margin,
            'text_tweaks': text_tweaks,
            'custom_replacements': custom_replacements,
            'regex_replacements': regex_replacements,
            'ignore_case': ignore_case,
            'compact_multiline': not no_compact,  # Enable compact multi-line by default, disable if --no-compact is used
            'open_file': open_file,
            'force': False,  # Default value for force option
            'verbose': verbose  # Add verbose flag to options
        })

        log_message("✓ Successfully modified label file!", msg_class=MessageClass.SUCCESS)
        return 0
    except Exception as e:
        log_message(f"Error: {str(e)}", msg_class=MessageClass.ERROR)
        return 1


if __name__ == "__main__":
    app()
