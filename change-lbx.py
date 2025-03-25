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
from typing import Optional, List, Dict, Any, Union, Tuple

# Function to check dependencies before importing them
def check_dependencies():
    missing_deps = []

    # Check each required dependency
    try:
        import typer
    except ImportError:
        missing_deps.append("typer")

    try:
        import rich
    except ImportError:
        missing_deps.append("rich")

    try:
        import colorama
    except ImportError:
        missing_deps.append("colorama")

    try:
        import lxml
    except ImportError:
        missing_deps.append("lxml")

    # If any dependencies are missing, print helpful message and exit
    if missing_deps:
        print("\n" + "="*60)
        print("ERROR: Missing required dependencies")
        print("="*60)
        print("\nThe following required packages are not installed:")
        for dep in missing_deps:
            print(f"  - {dep}")

        print("\nTo install all required dependencies, run:")
        print("  pip install " + " ".join(missing_deps))

        print("\nOr install from requirements.txt:")
        print("  pip install -r requirements.txt")

        print("\nSee project documentation for more information.")
        print("="*60 + "\n")
        sys.exit(1)

# Check dependencies before proceeding
check_dependencies()

# Import required dependencies
import typer
from rich.console import Console
from rich import print as rich_print
from colorama import init, Fore, Style
from lxml import etree as ET

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Initialize Typer app and Rich console
app = typer.Typer(help="Brother P-touch LBX Label File Modifier")
console = Console()


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


def update_label_size(root: ET.Element, label_config: Dict[str, Any], label_size: int) -> None:
    """
    Update the label dimensions in the XML.

    Args:
        root: Root element of the XML tree
        label_config: Label configuration dictionary
        label_size: Original label size in mm for reference in messages
    """
    paper_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}paper')
    if paper_elem is not None:
        # Get original margin before updating it
        original_margin = float(paper_elem.get('marginLeft').replace('pt', ''))
        new_margin = label_config['marginLeft']

        # Update paper element attributes
        paper_elem.set('width', f"{label_config['width']}pt")
        paper_elem.set('height', f"{label_config['height']}pt")
        paper_elem.set('marginLeft', f"{label_config['marginLeft']}pt")
        paper_elem.set('marginRight', f"{label_config['marginRight']}pt")

        console.print(f"Updated label width to [bold blue]{label_config['width']}pt[/] ({label_size}mm)")
        console.print(f"Updated margins to [bold blue]{label_config['marginLeft']}pt[/] on both sides")

        # Update format attribute for different label sizes
        paper_elem.set('format', label_config['format'])
        console.print(f"Updated format to [bold blue]{label_config['format']}[/] for {label_size}mm tape")

        # Update Y positions of all objects to account for margin change
        update_object_y_positions(root, original_margin, new_margin)


def update_object_y_positions(root: ET.Element, original_margin: float, new_margin: float) -> None:
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

    console.print(f"Adjusting object Y positions by [bold blue]{offset}pt[/] to match new margins")

    # Update background element Y position
    bg_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}backGround')
    if bg_elem is not None:
        old_y = float(bg_elem.get('y').replace('pt', ''))
        new_y = old_y + offset
        bg_elem.set('y', f"{new_y}pt")
        console.print(f"Updated background Y position from [bold blue]{old_y}pt[/] to [bold blue]{new_y}pt[/]")

    # Get all object elements
    object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

    for obj in object_styles:
        # Get parent element to determine if it's text or image
        parent = obj.getparent()
        is_image = parent is not None and parent.tag.endswith('}image')
        is_text = parent is not None and parent.tag.endswith('}text')

        # Update Y position
        if 'y' in obj.attrib:
            old_y = float(obj.get('y').replace('pt', ''))

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
            console.print(f"Updated {obj_type} Y position from [bold blue]{old_y}pt[/] to [bold blue]{new_y}pt[/]")

            # For images, also update the orgPos Y position
            if is_image:
                org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')
                if org_pos is not None:
                    old_org_y = float(org_pos.get('y').replace('pt', ''))
                    new_org_y = old_org_y + offset
                    org_pos.set('y', f"{new_org_y}pt")
                    console.print(f"Updated image orgPos Y from [bold blue]{old_org_y}pt[/] to [bold blue]{new_org_y}pt[/]")


def update_background(root: ET.Element, label_config: Dict[str, Any]) -> None:
    """
    Update the background element dimensions in the XML.

    Args:
        root: Root element of the XML tree
        label_config: Label configuration dictionary
    """
    bg_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}backGround')
    if bg_elem is not None:
        bg_elem.set('width', f"{label_config['bg_width']}pt")
        bg_elem.set('height', f"{label_config['bg_height']}pt")
        bg_elem.set('x', f"{label_config['bg_x']}pt")
        # Note: Y position is already updated by update_object_y_positions function
        console.print(f"Updated background dimensions: [bold blue]{label_config['bg_width']}pt × {label_config['bg_height']}pt[/]")
        console.print(f"Updated background position X: [bold blue]{label_config['bg_x']}pt[/]")


def update_font_size(root: ET.Element, font_size: int) -> None:
    """
    Update font size in text elements of an LBX file.

    Args:
        root: Root element of the XML tree
        font_size: New font size in pt
    """
    # Calculate original size (3.6x the font size)
    org_size = font_size * 3.6

    # Modify font sizes in text elements
    font_ext_elems = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt')
    for font_elem in font_ext_elems:
        font_elem.set('size', f"{font_size}pt")
        font_elem.set('orgSize', f"{org_size}pt")
        console.print(f"Updated font size to [bold blue]{font_size}pt[/] (orgSize: [bold blue]{org_size}pt[/])")


def classify_elements(root: ET.Element) -> Tuple[List[ET.Element], List[ET.Element]]:
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
        is_image = parent is not None and parent.tag.endswith('}image')
        is_text = parent is not None and parent.tag.endswith('}text')

        if is_image:
            image_elements.append(element)
        elif is_text:
            text_elements.append(element)

    return (image_elements, text_elements)


def scale_images(
    image_elements: List[ET.Element],
    image_scale: float,
    label_size: int,
    margin_left: float
) -> float:
    """
    Scale and position images in the label.

    Args:
        image_elements: List of image elements to scale
        image_scale: Scale factor for images
        label_size: Label width in mm
        margin_left: Left margin in points

    Returns:
        Maximum right edge of all processed images
    """
    if not image_elements:
        return margin_left

    # If no scaling is needed, just find the rightmost edge without modifying positions
    if image_scale == 1.0:
        max_image_right_edge = margin_left
        for element in image_elements:
            width = float(element.get('width').replace('pt', ''))
            x = float(element.get('x').replace('pt', ''))
            right_edge = x + width
            max_image_right_edge = max(max_image_right_edge, right_edge)
        return max_image_right_edge

    console.print(f"Label margin: [bold blue]{margin_left}pt[/]")

    # The true printable left edge in Brother P-touch labels is 5.6pt
    # This constant has been determined by examining actual LBX files
    TRUE_LEFT_EDGE = 5.6
    max_image_right_edge = margin_left  # Default to left margin

    for element in image_elements:
        # Get current dimensions
        width = float(element.get('width').replace('pt', ''))
        height = float(element.get('height').replace('pt', ''))
        x = float(element.get('x').replace('pt', ''))
        y = float(element.get('y').replace('pt', ''))

        # Calculate new dimensions maintaining aspect ratio
        new_width = width * image_scale
        new_height = height * image_scale

        # Use the current Y position - it's already adjusted by update_object_y_positions
        new_y = y

        # Always position at the absolute left printable edge
        new_x = TRUE_LEFT_EDGE
        console.print(f"Positioning image at absolute left printable edge: [bold blue]{TRUE_LEFT_EDGE}pt[/]")

        # Update element attributes
        element.set('width', f"{new_width}pt")
        element.set('height', f"{new_height}pt")
        element.set('x', f"{new_x}pt")
        element.set('y', f"{new_y}pt")

        # Calculate the rightmost edge of this image
        right_edge = new_x + new_width
        max_image_right_edge = max(max_image_right_edge, right_edge)

        # Update orgPos element if it exists
        parent = element.getparent()
        org_pos = None

        if parent is not None:
            org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')

        if org_pos is not None:
            org_pos.set('width', f"{new_width}pt")
            org_pos.set('height', f"{new_height}pt")
            org_pos.set('x', f"{new_x}pt")
            org_pos.set('y', f"{new_y}pt")

        console.print(f"Scaled image from [bold blue]{width}x{height}pt[/] to [bold blue]{new_width}x{new_height}pt[/] and placed at left margin")

    return max_image_right_edge


def position_text(text_elements: List[ET.Element], max_image_right_edge: float, label_size: int, text_margin_pt: float) -> None:
    """
    Position text elements after images.

    Args:
        text_elements: List of text elements to position
        max_image_right_edge: Rightmost edge of all images
        label_size: Label width in mm
        text_margin_pt: Margin between image and text in points
    """
    if not text_elements:
        return

    # Calculate text X position based on the right edge of images plus margin
    text_x = max_image_right_edge + text_margin_pt
    mm_margin = text_margin_pt/2.8
    console.print(f"Positioning text at x=[bold blue]{text_x}pt[/] ([bold blue]{mm_margin:.1f}mm[/] after images)")

    for element in text_elements:
        element.set('x', f"{text_x}pt")
        console.print(f"Moved text element to x=[bold blue]{text_x}pt[/]")


def center_elements_vertically(root: ET.Element, label_width: float) -> None:
    """
    Center elements vertically on the label.

    Args:
        root: Root element of the XML tree
        label_width: Width of the label in points
    """
    # Get all objects that need centering
    object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

    if object_styles:
        # Calculate the available vertical space on the label
        paper_height = float(label_width)

        # Find the original vertical position range of objects
        min_y = float('inf')
        max_y = float('-inf')
        orig_positions = {}

        # First pass: find the top and bottom positions
        for obj in object_styles:
            obj_y = float(obj.get('y').replace('pt', ''))
            obj_height = float(obj.get('height').replace('pt', ''))
            obj_bottom = obj_y + obj_height

            min_y = min(min_y, obj_y)
            max_y = max(max_y, obj_bottom)

            # Store original positions for later use
            orig_positions[obj] = {
                'y': obj_y,
                'height': obj_height,
                'bottom': obj_bottom
            }

        # Calculate the group height and center position
        group_height = max_y - min_y
        center_of_paper = paper_height / 2
        center_of_group = min_y + (group_height / 2)

        # Calculate the offset needed to center the group
        offset = center_of_paper - center_of_group

        console.print(f"Group height: [bold blue]{group_height}pt[/]")
        console.print(f"Center of label: [bold blue]{center_of_paper}pt[/]")
        console.print(f"Applying offset of [bold blue]{offset}pt[/] to center elements")

        # Second pass: adjust each object's position
        for obj in object_styles:
            orig_y = orig_positions[obj]['y']
            new_y = orig_y + offset
            obj.set('y', f"{new_y}pt")
            console.print(f"Centered object from y=[bold blue]{orig_y}pt[/] to y=[bold blue]{new_y}pt[/]")

            # Also update corresponding image orgPos if exists
            parent = obj.getparent()
            if parent is not None and parent.tag.endswith('}image'):
                org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')
                if org_pos is not None:
                    org_pos.set('y', f"{new_y}pt")
                    console.print(f"Updated image position y to [bold blue]{new_y}pt[/]")

        console.print(f"All objects have been centered as a group")


def extract_and_parse_lbx(input_file: str, temp_dir: str) -> Tuple[ET.ElementTree, str]:
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


def apply_compatibility_tweaks(root: ET.Element, label_size: int) -> None:
    """
    Apply compatibility tweaks to the label file to ensure it works properly with P-touch Editor.

    Args:
        root: Root element of the XML tree
        label_size: Target label size in mm
    """
    # Update the XML document version and generator
    if root.tag.endswith('}document'):
        # Set version to 1.9 which is used by modern P-touch Editor
        root.set('version', '1.9')

        # Update the generator to show it was modified by this tool
        root.set('generator', 'com.jdlien.lbx-utils')
        console.print(f"Updated document version to [bold blue]1.9[/] and generator to [bold blue]com.jdlien.lbx-utils[/]")

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
            current_printer_name = paper_elem.get('printerName')

            if current_printer_id != large_format_printer_id or not current_printer_name.startswith("Brother PT-P7"):
                paper_elem.set('printerID', large_format_printer_id)
                paper_elem.set('printerName', large_format_printer_name)
                console.print(f"Updated printer to [bold blue]{large_format_printer_name}[/] for compatibility with {label_size}mm tape")


def save_lbx(tree: ET.ElementTree, xml_path: str, output_file: str, temp_dir: str) -> None:
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

    console.print(f"Created modified LBX file: {output_file}")


def modify_lbx(
    input_file: str,
    output_file: str,
    font_size: int = 8,
    label_size: int = 12,
    center_vertically: bool = False,
    image_scale: float = 1.0,
    text_margin: float = 1.0,
    open_file: bool = False
) -> None:
    """
    Modify a Brother LBX file by changing font size and label width.

    Parameters:
    - input_file: Path to the input LBX file
    - output_file: Path for the modified output LBX file
    - font_size: New font size in pt
    - label_size: Label width in mm (12, 18, or 24)
    - center_vertically: Whether to center elements vertically
    - image_scale: Scale factor for images
    - text_margin: Margin between image and text in mm
    - open_file: Whether to open the file after creating it (macOS only)
    """
    # Get label configuration
    label_config = get_label_config(label_size)

    # Convert text margin from mm to points (1mm ≈ 2.8pt)
    text_margin_pt = text_margin * 2.8

    # Create a temp directory for extracting and modifying files
    temp_dir = tempfile.mkdtemp()

    try:
        # Extract LBX and parse XML
        tree, xml_path = extract_and_parse_lbx(input_file, temp_dir)
        root = tree.getroot()

        # Apply compatibility tweaks before any other modifications
        apply_compatibility_tweaks(root, label_size)

        # Update label dimensions
        update_label_size(root, label_config, label_size)

        # Update background element if it exists
        update_background(root, label_config)

        # Update font size
        update_font_size(root, font_size)

        # Classify elements as images or text
        image_elements, text_elements = classify_elements(root)

        # Scale and position images
        paper_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}paper')
        margin_left = float(paper_elem.get('marginLeft').replace('pt', '')) if paper_elem is not None else 2.8
        max_image_right_edge = scale_images(image_elements, image_scale, label_size, margin_left)

        # Position text elements after images
        position_text(text_elements, max_image_right_edge, label_size, text_margin_pt)

        # Vertically center elements if requested
        if center_vertically:
            center_elements_vertically(root, label_config['width'])

        # Save modified XML and create new LBX file
        save_lbx(tree, xml_path, output_file, temp_dir)

        # Open the file if requested (macOS only)
        if open_file and platform.system() == 'Darwin':  # Check if on macOS
            try:
                subprocess.run(['open', '-a', '/Applications/P-touch Editor.app', output_file])
                console.print(f"Opened file in P-touch Editor")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not open file: {str(e)}")

    finally:
        # Clean up the temp directory
        shutil.rmtree(temp_dir)


@app.command()
def main(
    input_file: str = typer.Argument(..., help="Input .lbx file to modify"),
    output_file: str = typer.Argument(..., help="Path for the modified output file"),
    font_size: int = typer.Option(8, "--font-size", "-f", help="Font size in points"),
    label_size: int = typer.Option(12, "--label-size", "-l", help="Label tape size in mm (9, 12, 18, or 24)"),
    center_vertically: bool = typer.Option(False, "--center-vertically", "-c", help="Center elements vertically on the label"),
    image_scale: float = typer.Option(1.0, "--image-scale", "-s", help="Scale factor for images, e.g. 1.5 for 150%"),
    text_margin: float = typer.Option(1.0, "--text-margin", "-m", help="Margin between image and text in mm"),
    open_file: bool = typer.Option(False, "--open", "-o", help="Open the modified file in P-touch Editor after creation (macOS only)")
) -> int:
    """
    Modify a Brother P-touch label (.lbx) file by changing font size, label width,
    vertical alignment, image scaling, and text positioning.
    """
    if not os.path.exists(input_file):
        console.print(f"[red]Input file '{input_file}' not found.[/red]")
        return 1

    try:
        modify_lbx(input_file, output_file, font_size, label_size,
                  center_vertically, image_scale, text_margin, open_file)

        console.print(f"[green]✓ Successfully modified label file![/green]")
        return 0
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1


if __name__ == "__main__":
    app()
