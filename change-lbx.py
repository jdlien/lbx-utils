#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
change-lbx.py - Brother P-touch LBX Label File Modifier

A utility for customizing Brother P-touch label (.lbx) files by modifying font size,
label width, vertical alignment, image scaling, and text positioning.

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

Requirements:
- typer: Modern CLI interface
- rich: Enhanced terminal output
- colorama: Cross-platform colored terminal output
- lxml: XML handling with parent node support

Install dependencies with:
pip install typer rich colorama lxml

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

check_and_import_dependencies()

import lxml.etree as ET
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm, Prompt
from rich.table import Table
from colorama import init, Fore, Style
import typer

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Initialize Typer app and Rich console
app = typer.Typer(help="Brother P-touch LBX Label File Modifier", add_completion=False)
console = Console()

# Constants
TRUE_LEFT_EDGE = 5.6  # The true printable left edge in Brother P-touch labels is 5.6pt

def parse_unit(value: str) -> float:
    """
    Parse a value with unit (like '10pt') into a float.

    Args:
        value: String value with unit

    Returns:
        float: Parsed value without unit
    """
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
    # Define constants that apply to all label sizes
    DEFAULT_HEIGHT = 2834.4
    DEFAULT_BG_X = 5.6
    DEFAULT_BG_Y = None  # Will be set to margin value

    # Define format codes for each size
    FORMAT_CODES = {
        9: '258',
        12: '259',
        18: '260',
        24: '261'
    }

    # Calculate width based on the mm size
    # These multipliers match observed values from actual LBX files
    if label_size == 9:
        width = 25.6
        margin = 2.8
        bg_width = 66.4
    elif label_size == 12:
        width = 33.6
        margin = 2.8
        bg_width = 66.4
    elif label_size == 18:
        width = 51.2
        margin = 3.2
        bg_width = 66.4
    elif label_size == 24:
        width = 68.0
        margin = 8.4
        bg_width = 115.3
    else:
        # Default to 12mm if not found
        width = 33.6
        margin = 2.8
        bg_width = 66.4
        label_size = 12  # Normalize to 12mm for format code

    # Calculate background height (roughly proportional to width minus margins)
    if label_size <= 12:
        bg_height = 20.0
    elif label_size == 18:
        bg_height = 28.0
    else:  # 24mm
        bg_height = 51.2

    # Create the configuration dictionary with calculated values
    config = {
        'width': width,
        'height': DEFAULT_HEIGHT,
        'marginLeft': margin,
        'marginRight': margin,
        'bg_width': bg_width,
        'bg_height': bg_height,
        'bg_x': DEFAULT_BG_X,
        'bg_y': margin if DEFAULT_BG_Y is None else DEFAULT_BG_Y,
        'format': FORMAT_CODES.get(label_size, '259')  # Default to 12mm format if not found
    }

    return config


def update_label_size(root: Element, label_size: int, verbose: bool = False) -> None:
    """
    Update the label dimensions in the XML.

    Args:
        root: Root element of the XML tree
        label_size: Label size in mm
    """
    # Get label configuration
    label_config = get_label_config(label_size)

    paper_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}paper')
    if paper_elem is not None:
        # Get original margin before updating it
        original_margin = float(paper_elem.get('marginLeft', '0pt').replace('pt', ''))
        new_margin = label_config['marginLeft']

        # Update paper element attributes
        paper_elem.set('width', f"{label_config['width']}pt")
        paper_elem.set('height', f"{label_config['height']}pt")
        paper_elem.set('marginLeft', f"{label_config['marginLeft']}pt")
        paper_elem.set('marginRight', f"{label_config['marginRight']}pt")

        log_message(f"Updated label width to [bold blue]{label_config['width']}pt[/] ({label_size}mm)", verbose)
        log_message(f"Updated margins to [bold blue]{label_config['marginLeft']}pt[/] on both sides", verbose)

        # Update format attribute for different label sizes
        paper_elem.set('format', label_config['format'])
        log_message(f"Updated format to [bold blue]{label_config['format']}[/] for {label_size}mm tape", verbose)

        # Update Y positions of all objects to account for margin change
        update_object_y_positions(root, original_margin, new_margin, verbose)


def update_object_y_positions(root: Element, original_margin: float, new_margin: float, verbose: bool = False) -> None:
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

    log_message(f"Adjusting object Y positions by [bold blue]{offset}pt[/] to match new margins", verbose)

    # Update background element Y position
    bg_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}backGround')
    if bg_elem is not None:
        old_y = float(bg_elem.get('y', '0pt').replace('pt', ''))
        new_y = old_y + offset
        bg_elem.set('y', f"{new_y}pt")
        log_message(f"Updated background Y position from [bold blue]{old_y}pt[/] to [bold blue]{new_y}pt[/]", verbose)

    # Get all object elements
    object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

    for obj in object_styles:
        # Get parent element to determine if it's text or image
        parent = obj.getparent()
        is_image = parent is not None and str(parent.tag).endswith('}image')
        is_text = parent is not None and str(parent.tag).endswith('}text')

        # Update Y position
        if 'y' in obj.attrib:
            old_y = float(obj.get('y', '0pt').replace('pt', ''))

            # For text elements: maintain the 4.3pt offset from margin
            if is_text:
                # Text Y position is consistently offset from margin by 4.3pt
                text_margin_offset = 4.3
                new_y = new_margin + text_margin_offset
            else:
                # For other elements, apply the offset directly
                new_y = old_y + offset

            obj.set('y', f"{new_y}pt")

            obj_type = "text" if is_text else "image" if is_image else "object"
            log_message(f"Updated {obj_type} Y position from [bold blue]{old_y}pt[/] to [bold blue]{new_y}pt[/]", verbose)

            # For images, also update the orgPos Y position
            if is_image and parent is not None:
                org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')
                if org_pos is not None:
                    old_org_y = float(org_pos.get('y', '0pt').replace('pt', ''))
                    new_org_y = old_org_y + offset
                    org_pos.set('y', f"{new_org_y}pt")
                    log_message(f"Updated image orgPos Y from [bold blue]{old_org_y}pt[/] to [bold blue]{new_org_y}pt[/]", verbose)


def update_background(root: Element, label_config: Dict[str, Any], verbose: bool = False) -> None:
    """
    Update the background element dimensions in the XML.

    Args:
        root: Root element of the XML tree
        label_config: Label configuration dictionary
        verbose: Whether to show verbose output
    """
    bg_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}backGround')
    if bg_elem is not None:
        bg_elem.set('width', f"{label_config['bg_width']}pt")
        bg_elem.set('height', f"{label_config['bg_height']}pt")
        bg_elem.set('x', f"{label_config['bg_x']}pt")
        # Note: Y position is already updated by update_object_y_positions function
        log_message(f"Updated background dimensions: [bold blue]{label_config['bg_width']}pt × {label_config['bg_height']}pt[/]", verbose)
        log_message(f"Updated background position X: [bold blue]{label_config['bg_x']}pt[/]", verbose)


def update_font_size(root: Element, font_size: int, verbose: bool = False) -> None:
    """
    Update font size in text elements of an LBX file.

    Args:
        root: Root element of the XML tree
        font_size: New font size in pt
        verbose: Whether to show verbose output
    """
    # Calculate original size (3.6x the font size)
    org_size = font_size * 3.6

    # Modify font sizes in text elements
    font_ext_elems = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt')
    for font_elem in font_ext_elems:
        font_elem.set('size', f"{font_size}pt")
        font_elem.set('orgSize', f"{org_size}pt")
        log_message(f"Updated font size to [bold blue]{font_size}pt[/] (orgSize: [bold blue]{org_size}pt[/])", verbose)


def classify_elements(root: Element) -> Tuple[List[Element], List[Element]]:
    """
    Classify elements in the XML as either image elements or text elements.

    Args:
        root: Root element of the XML tree

    Returns:
        Tuple of (image_elements, text_elements)
    """
    # Get all objects
    object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

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


def scale_images(image_elements: List[Element], image_scale: float, label_size: int, verbose: bool = False) -> float:
    """
    Scale and position images based on the scale factor and label size.

    Args:
        image_elements: List of image elements to scale
        image_scale: Scale factor for images (1.0 means no scaling)
        label_size: Label width in mm
        verbose: Whether to show verbose output

    Returns:
        float: The maximum right edge of all images after scaling and positioning
    """
    # If no images, return the left margin
    if not image_elements:
        return TRUE_LEFT_EDGE

    # If no scaling is needed, calculate the maximum right edge without changing positions
    if image_scale == 1.0:
        log_message(f"No image scaling required, preserving original horizontal positions", verbose)
        max_right_edge = TRUE_LEFT_EDGE
        # Find the rightmost edge of all images without modifying their positions
        for element in image_elements:
            current_x = parse_unit(element.get('x', '0pt'))
            width = parse_unit(element.get('width', '0pt'))
            right_edge = current_x + width
            max_right_edge = max(max_right_edge, right_edge)
        return max_right_edge

    # Process each image element
    max_right_edge = TRUE_LEFT_EDGE
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
        new_x = TRUE_LEFT_EDGE
        log_message(f"Positioning image at absolute left printable edge: [bold blue]{TRUE_LEFT_EDGE}pt[/]", verbose)

        # Calculate the right edge of this image
        right_edge = new_x + new_width
        max_right_edge = max(max_right_edge, right_edge)

        # Use the current Y position, which is already adjusted by update_object_y_positions
        new_y = current_y

        # Output the scaling and positioning
        log_message(f"Image scaled from [bold blue]{current_width:.1f}x{current_height:.1f}pt[/] to [bold blue]{new_width:.1f}x{new_height:.1f}pt[/]", verbose)
        log_message(f"Image position adjusted from ([bold blue]{current_x:.1f}[/], [bold blue]{current_y:.1f}[/])pt to ([bold blue]{new_x:.1f}[/], [bold blue]{new_y:.1f}[/])pt", verbose)

        # Update the element attributes
        element.set('x', f"{new_x}pt")
        element.set('y', f"{new_y}pt")
        element.set('width', f"{new_width}pt")
        element.set('height', f"{new_height}pt")

        # Get the parent image element
        parent = element.getparent()
        if parent is not None and str(parent.tag).endswith('}image'):
            # Update orgPos element
            org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')
            if org_pos is not None:
                org_pos.set('x', f"{new_x}pt")
                org_pos.set('y', f"{new_y}pt")
                org_pos.set('width', f"{new_width}pt")
                org_pos.set('height', f"{new_height}pt")
                log_message(f"Updated image orgPos to [bold blue]{new_width}x{new_height}pt[/]", verbose)

            # Update trimming dimensions
            image_style = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}imageStyle')
            if image_style is not None:
                trimming = image_style.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}trimming')
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
                    log_message(f"Updated image trimming dimensions from [bold blue]{trim_width}x{trim_height}pt[/] to [bold blue]{new_trim_width}x{new_trim_height}pt[/]", verbose)

    return max_right_edge


def position_text(text_elements: List[Element], max_image_right_edge: float, label_size: int, text_margin_pt: float, image_scale: float, verbose: bool = False) -> None:
    """
    Position text elements after images.

    Args:
        text_elements: List of text elements to position
        max_image_right_edge: Rightmost edge of all images
        label_size: Label width in mm
        text_margin_pt: Margin between image and text in points
        image_scale: Scale factor used for images (used to determine if repositioning is needed)
        verbose: Whether to show verbose output
    """
    if not text_elements:
        return

    # Only reposition text if image scaling was applied
    if image_scale != 1.0:
        # Calculate text X position based on the right edge of images plus margin
        text_x = max_image_right_edge + text_margin_pt
        mm_margin = text_margin_pt/2.8
        log_message(f"Positioning text at x=[bold blue]{text_x}pt[/] ([bold blue]{mm_margin:.1f}mm[/] after images)", verbose)

        for element in text_elements:
            element.set('x', f"{text_x}pt")
            log_message(f"Moved text element to x=[bold blue]{text_x}pt[/]", verbose)
    else:
        log_message(f"Preserving original horizontal text positions (no image scaling applied)", verbose)


def center_elements_vertically(root: Element, label_width: float, verbose: bool = False) -> None:
    """
    Center elements vertically within the background area of the label.

    Args:
        root: Root element of the XML tree
        label_width: Width of the label in points (not used for centering)
        verbose: Whether to show verbose output
    """
    # Get the background element to determine the printable area
    bg_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}backGround')
    if bg_elem is None:
        log_message("[yellow]Warning: No background element found, skipping vertical centering[/]", verbose)
        return

    # Get the paper element to determine label size
    paper_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}paper')
    if paper_elem is None:
        log_message("[yellow]Warning: No paper element found, skipping vertical centering[/]", verbose)
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
    object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

    if not object_styles:
        log_message("[yellow]Warning: No objects found to center[/]", verbose)
        return

    log_message(f"Paper width: [bold blue]{paper_width}pt[/]", verbose)
    log_message(f"Background area: y=[bold blue]{bg_y}pt[/], height=[bold blue]{bg_height}pt[/]", verbose)
    log_message(f"Center of background: [bold blue]{center_of_background}pt[/]", verbose)

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
        log_message(f"Centered object (height=[bold blue]{obj_height}pt[/]) from y=[bold blue]{orig_y}pt[/] to y=[bold blue]{new_y}pt[/]", verbose)

        # Also update corresponding image orgPos if exists
        parent = obj.getparent()
        if parent is not None and str(parent.tag).endswith('}image'):
            org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')
            if org_pos is not None:
                org_pos.set('y', f"{new_y}pt")
                log_message(f"Updated image orgPos y to [bold blue]{new_y}pt[/]", verbose)

    log_message(f"All objects have been centered within the background area", verbose)


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

    # Parse the XML
    namespaces = {
        'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
        'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
        'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
        'draw': 'http://schemas.brother.info/ptouch/2007/lbx/draw',
        'image': 'http://schemas.brother.info/ptouch/2007/lbx/image',
        'barcode': 'http://schemas.brother.info/ptouch/2007/lbx/barcode',
        'database': 'http://schemas.brother.info/ptouch/2007/lbx/database',
        'table': 'http://schemas.brother.info/ptouch/2007/lbx/table',
        'cable': 'http://schemas.brother.info/ptouch/2007/lbx/cable'
    }

    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.parse(xml_path, parser)

    return (tree, xml_path)


def apply_compatibility_tweaks(root: Element, label_size: int, verbose: bool = False) -> None:
    """
    Apply compatibility tweaks to the label file to ensure it works properly with P-touch Editor.

    Args:
        root: Root element of the XML tree
        label_size: Target label size in mm
        verbose: Whether to show verbose output
    """
    # Update the XML document version and generator
    if str(root.tag).endswith('}document'):
        # Set version to 1.9 which is used by modern P-touch Editor
        root.set('version', '1.9')

        # Update the generator to show it was modified by this tool
        root.set('generator', 'com.jdlien.lbx-utils')
        log_message(f"Updated document version to [bold blue]1.9[/] and generator to [bold blue]com.jdlien.lbx-utils[/]", verbose)

    # Update printer compatibility for wider tape formats
    paper_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}paper')
    if paper_elem is not None:
        # The PT-P710BT supports larger tape sizes up to 24mm
        large_format_printer_id = "30256"  # ID for PT-P710BT
        large_format_printer_name = "Brother PT-P710BT"

        # Only update for 18mm and 24mm labels which need a compatible printer
        if label_size >= 18:
            # Check if already set to a compatible printer
            current_printer_id = paper_elem.get('printerID')
            current_printer_name = paper_elem.get('printerName', '')

            if current_printer_id != large_format_printer_id or not current_printer_name.startswith("Brother PT-P7"):
                paper_elem.set('printerID', large_format_printer_id)
                paper_elem.set('printerName', large_format_printer_name)
                log_message(f"Updated printer to [bold blue]{large_format_printer_name}[/] for compatibility with {label_size}mm tape", verbose)


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
    paper_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}paper')
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
    object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

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
    object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

    for element in object_styles:
        # Check if the parent is an image element
        parent = element.getparent()
        if parent is not None and str(parent.tag).endswith('}image'):
            image_elements.append(element)

    return image_elements


def update_font_sizes(text_elements: List[Element], target_font_size: float, verbose: bool = False) -> None:
    """
    Update font sizes in text elements to a specific point size.

    Args:
        text_elements: List of text elements to update
        target_font_size: Target font size in points
    """
    if not text_elements:
        return

    log_message(f"Setting font size to [bold blue]{target_font_size}pt[/]", verbose)

    # Process each text element
    for element in text_elements:
        # Find the text element's parent
        parent = element.getparent()
        if parent is None:
            continue

        # Update main fontExt element
        font_ext = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt')
        if font_ext is not None:
            current_size = parse_unit(font_ext.get('size', '9pt'))
            current_org_size = parse_unit(font_ext.get('orgSize', '32.4pt'))

            # Keep the original orgSize ratio
            org_size_ratio = current_org_size / current_size
            new_org_size = target_font_size * org_size_ratio

            font_ext.set('size', f"{target_font_size}pt")
            font_ext.set('orgSize', f"{new_org_size}pt")

            if current_size != target_font_size:
                log_message(f"Updated main font size from [bold blue]{current_size:.1f}pt[/] to [bold blue]{target_font_size}pt[/]", verbose)

        # Update textStyle orgPoint
        text_style = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/text}textStyle')
        if text_style is not None:
            current_org_point = parse_unit(text_style.get('orgPoint', '9pt'))
            text_style.set('orgPoint', f"{target_font_size}pt")
            if current_org_point != target_font_size:
                log_message(f"Updated textStyle orgPoint from [bold blue]{current_org_point:.1f}pt[/] to [bold blue]{target_font_size}pt[/]", verbose)

        # Update all stringItem fontExt elements
        for string_item in parent.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/text}stringItem'):
            string_font_ext = string_item.find('.//{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt')
            if string_font_ext is not None:
                current_size = parse_unit(string_font_ext.get('size', '9pt'))
                current_org_size = parse_unit(string_font_ext.get('orgSize', '32.4pt'))

                # Keep the original orgSize ratio
                org_size_ratio = current_org_size / current_size
                new_org_size = target_font_size * org_size_ratio

                string_font_ext.set('size', f"{target_font_size}pt")
                string_font_ext.set('orgSize', f"{new_org_size}pt")

                if current_size != target_font_size:
                    log_message(f"Updated string item font size from [bold blue]{current_size:.1f}pt[/] to [bold blue]{target_font_size}pt[/]", verbose)


def modify_lbx(lbx_file_path: str, output_file_path: str, options: Dict[str, Any]) -> None:
    """
    Modify a Brother P-touch LBX file with the given options.

    Args:
        lbx_file_path: Path to input LBX file
        output_file_path: Path to output LBX file
        options: Dictionary of modification options
    """
    verbose = options.get('verbose', False)
    log_message(f"Modifying file: [bold blue]{lbx_file_path}[/]", verbose)

    # Create a temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Extract and parse the LBX file
        tree, xml_path = extract_and_parse_lbx(lbx_file_path, temp_dir)
        root = tree.getroot()

        # Get the current label width
        current_label_size = get_current_label_size(root)
        if current_label_size is None:
            log_message("[bold red]Could not determine current label size[/]", verbose)
            return

        log_message(f"Current label size: [bold blue]{current_label_size}mm[/]", verbose)

        # Extract target label size from options
        label_size = options.get('label_size', current_label_size)
        log_message(f"Target label size: [bold blue]{label_size}mm[/]", verbose)

        # Convert text margin from mm to points (1mm ≈ 2.8pt)
        text_margin = options.get('text_margin', 1.0)  # Default to 1.0mm
        text_margin_pt = text_margin * 2.8

        # Skip if the label size is the same and no other changes
        if label_size == current_label_size and not options.get('font_size') and not options.get('image_scale'):
            log_message("[bold yellow]No changes necessary - input and output sizes are the same[/]", verbose)
            if options.get('force'):
                log_message("[bold yellow]Force option specified - continuing anyway[/]", verbose)
            else:
                save_lbx(tree, xml_path, output_file_path, temp_dir)
                return

        # If target label size is different, update it
        if label_size != current_label_size:
            log_message(f"Changing label size from [bold blue]{current_label_size}mm[/] to [bold blue]{label_size}mm[/]", verbose)
            update_label_size(root, label_size, verbose)

        # Get text and image elements
        text_elements = get_text_elements(root)
        image_elements = get_image_elements(root)

        # Get the target font size and image scale
        target_font_size = options.get('font_size')
        image_scale = options.get('image_scale', 1.0)

        # Apply changes if needed
        if target_font_size is not None or image_scale != 1.0:
            # Update font size if specified
            if target_font_size is not None:
                update_font_sizes(text_elements, target_font_size, verbose)

            # Scale images if requested
            if image_scale != 1.0:
                log_message(f"Scaling images by factor: [bold blue]{image_scale}[/]", verbose)

            # Scale and position images
            max_image_right_edge = scale_images(image_elements, image_scale, label_size, verbose)

            # Position text elements after images
            position_text(text_elements, max_image_right_edge, label_size, text_margin_pt, image_scale, verbose)

            # Vertically center elements if requested
            if options.get('center_vertically', False):
                center_elements_vertically(root, label_size, verbose)
        else:
            log_message("[bold green]No changes needed - keeping original font sizes and image dimensions[/]", verbose)
            # Still need to find max_image_right_edge for text positioning
            max_image_right_edge = scale_images(image_elements, image_scale, label_size, verbose)
            # Position text elements after images (will preserve positions due to image_scale=1.0)
            position_text(text_elements, max_image_right_edge, label_size, text_margin_pt, image_scale, verbose)

        # Save the modified file
        save_lbx(tree, xml_path, output_file_path, temp_dir)
        log_message(f"Created modified LBX file: [bold blue]{output_file_path}[/]", True)

        # Open the file if requested (macOS only)
        if options.get('open_file', False) and platform.system() == 'Darwin':
            try:
                subprocess.run(['open', '-a', '/Applications/P-touch Editor.app', output_file_path])
                log_message(f"Opened file in P-touch Editor", verbose)
            except Exception as e:
                log_message(f"[yellow]Warning: Could not open file: {str(e)}[/]", verbose)


def log_message(message: str, verbose: bool = False) -> None:
    """
    Log a message to the console, respecting the verbose flag.

    Args:
        message: Message to log
        verbose: Whether to show verbose output

    Message types:
    - Errors (red): Always shown
    - Warnings (yellow): Always shown
    - Basic success: Always shown
    - All other messages: Only shown with verbose flag
    """
    # Always show errors and warnings
    if message.startswith("[bold red]") or message.startswith("[red]") or \
       message.startswith("[yellow]") or message.startswith("[bold yellow]"):
        console.print(message)
        return

    # Show all other messages only in verbose mode
    if verbose:
        console.print(message)


@app.command()
def main(
    input_file: str = typer.Argument(..., help="Input .lbx file to modify"),
    output_file: str = typer.Argument(..., help="Path for the modified output file"),
    font_size: int = typer.Option(8, "--font-size", "-f", help="Font size in points"),
    label_size: int = typer.Option(12, "--label-size", "-l", help="Label tape size in mm (9, 12, 18, or 24)"),
    center_vertically: bool = typer.Option(False, "--center-vertically", "-c", help="Center elements vertically on the label"),
    image_scale: float = typer.Option(1.0, "--image-scale", "-s", help="Scale factor for images, e.g. 1.5 for 150%"),
    text_margin: float = typer.Option(1.0, "--text-margin", "-m", help="Margin between image and text in mm"),
    open_file: bool = typer.Option(False, "--open", "-o", help="Open the modified file in P-touch Editor after creation (macOS only)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed logging output")
) -> int:
    """
    Modify a Brother P-touch label (.lbx) file by changing font size, label width,
    vertical alignment, image scaling, and text positioning.
    """
    if not os.path.exists(input_file):
        console.print(f"[red]Input file '{input_file}' not found.[/red]")
        return 1

    try:
        # Pass options as a dictionary to the new modify_lbx function
        modify_lbx(input_file, output_file, {
            'font_size': font_size,
            'label_size': label_size,
            'center_vertically': center_vertically,
            'image_scale': image_scale,
            'text_margin': text_margin,
            'open_file': open_file,
            'force': False,  # Default value for force option
            'verbose': verbose  # Add verbose flag to options
        })

        log_message(f"[green]✓ Successfully modified label file![/green]", verbose)
        return 0
    except Exception as e:
        log_message(f"[red]Error: {str(e)}[/red]", verbose)
        return 1


if __name__ == "__main__":
    app()
