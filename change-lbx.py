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

"""

import sys
import os
import zipfile
import xml.etree.ElementTree as ET
import shutil
import tempfile
import argparse
from argparse import RawDescriptionHelpFormatter

try:
    # Try to import colorama for colored terminal output
    from colorama import init, Fore, Style
    init(autoreset=True)  # Initialize colorama with autoreset
    USING_COLOR = True
except ImportError:
    # Create dummy color objects if colorama is not available
    USING_COLOR = False
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = Style = DummyColor()
    print("Tip: Install colorama for colored output: pip install colorama")

try:
    # Try to import lxml which supports getparent()
    from lxml import etree as ET
    USING_LXML = True
except ImportError:
    # Fall back to standard ElementTree
    import xml.etree.ElementTree as ET
    USING_LXML = False
    print(f"{Fore.YELLOW}Warning: lxml not found. Vertical centering will be limited.")
    print("Install lxml for better results: pip install lxml")

def modify_lbx(input_file, output_file, font_size=8, label_size=12, center_vertically=False, image_scale=1.0, text_margin=1.0):
    """
    Modify a Brother LBX file by changing font size and label width.

    Parameters:
    - input_file: Path to the input LBX file
    - output_file: Path for the modified output LBX file
    - font_size: New font size in pt (default: 8)
    - label_size: Label width in mm (12, 18, or 24, default: 12)
    - center_vertically: Whether to center elements vertically (default: False)
    - image_scale: Scale factor for images (default: 1.0)
    - text_margin: Margin between image and text in mm (default: 2.0)
    """
    # Configuration for different label sizes based on actual examples
    label_configs = {
        # width, marginLeft, marginRight, background width, background height, background x, background y
        12: {
            'width': 33.6,
            'marginLeft': 8.4,
            'marginRight': 8.4,
            'bg_width': 33.8,  # slightly larger than paper width
            'bg_height': 16.8,
            'bg_x': 5.6,
            'bg_y': 8.4
        },
        18: {
            'width': 51.2,
            'marginLeft': 3.2,
            'marginRight': 3.2,
            'bg_width': 51.4,
            'bg_height': 44.8,
            'bg_x': 5.6,
            'bg_y': 3.2
        },
        24: {
            'width': 68.0,
            'marginLeft': 8.4,
            'marginRight': 8.4,
            'bg_width': 68.2,
            'bg_height': 51.2,
            'bg_x': 5.6,
            'bg_y': 8.4
        }
    }.get(label_size, {
        'width': 33.6,  # default to 12mm if not found
        'marginLeft': 8.4,
        'marginRight': 8.4,
        'bg_width': 33.8,
        'bg_height': 16.8,
        'bg_x': 5.6,
        'bg_y': 8.4
    })

    # Convert text margin from mm to points (1mm ≈ 2.8pt)
    text_margin_pt = text_margin * 2.8

    # Calculate original size (3.6x the font size)
    org_size = font_size * 3.6

    # Create a temp directory for extracting and modifying files
    temp_dir = tempfile.mkdtemp()

    try:
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

        if USING_LXML:
            parser = ET.XMLParser(remove_blank_text=True)
            tree = ET.parse(xml_path, parser)
        else:
            tree = ET.parse(xml_path)

        root = tree.getroot()

        # Modify label width (tape size) and margins
        paper_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}paper')
        if paper_elem is not None:
            paper_elem.set('width', f"{label_configs['width']}pt")
            paper_elem.set('marginLeft', f"{label_configs['marginLeft']}pt")
            paper_elem.set('marginRight', f"{label_configs['marginRight']}pt")

            print(f"Updated label width to {label_configs['width']}pt ({label_size}mm)")
            print(f"Updated margins to Left: {label_configs['marginLeft']}pt, Right: {label_configs['marginRight']}pt")

            # Update format attribute for different label sizes
            format_value = "261" if label_size == 24 else "260" if label_size == 18 else "259"
            paper_elem.set('format', format_value)
            print(f"Updated format to {format_value}")

        # Also update background element if it exists
        bg_elem = root.find('.//{http://schemas.brother.info/ptouch/2007/lbx/style}backGround')
        if bg_elem is not None:
            bg_elem.set('width', f"{label_configs['bg_width']}pt")
            bg_elem.set('height', f"{label_configs['bg_height']}pt")
            bg_elem.set('x', f"{label_configs['bg_x']}pt")
            bg_elem.set('y', f"{label_configs['bg_y']}pt")
            print(f"Updated background dimensions: width={label_configs['bg_width']}pt, height={label_configs['bg_height']}pt")
            print(f"Updated background position: x={label_configs['bg_x']}pt, y={label_configs['bg_y']}pt")

        # Modify font sizes in text elements
        font_ext_elems = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt')
        for font_elem in font_ext_elems:
            font_elem.set('size', f"{font_size}pt")
            font_elem.set('orgSize', f"{org_size}pt")
            print(f"Updated font size to {font_size}pt (orgSize: {org_size}pt)")

        # Get all objects
        object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

        # Collect images and text elements
        image_elements = []
        text_elements = []

        for element in object_styles:
            # Determine if element is an image or text
            parent = None
            if USING_LXML:
                parent = element.getparent()

            is_image = (parent is not None and parent.tag.endswith('}image')) if USING_LXML else False
            is_text = (parent is not None and parent.tag.endswith('}text')) if USING_LXML else False

            # If not using lxml, try to determine by other means
            if not USING_LXML:
                # Check for image elements
                for image_elem in root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/image}image'):
                    for obj_style in image_elem.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle'):
                        if obj_style is element:
                            is_image = True
                            break

                # Check for text elements
                for text_elem in root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/text}text'):
                    for obj_style in text_elem.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle'):
                        if obj_style is element:
                            is_text = True
                            break

            if is_image:
                image_elements.append(element)
            elif is_text:
                text_elements.append(element)

        # Scale images if requested
        max_image_right_edge = label_configs['marginLeft']  # Default to left margin if no images

        if image_scale != 1.0 and image_elements:
            # First print information about label settings for reference
            margin_left = float(paper_elem.get('marginLeft').replace('pt', ''))
            print(f"Label margin: {margin_left}pt")

            # The true printable left edge in Brother P-touch labels is 5.6pt
            # This constant has been determined by examining actual LBX files
            TRUE_LEFT_EDGE = 5.6

            for element in image_elements:
                # Get current dimensions
                width = float(element.get('width').replace('pt', ''))
                height = float(element.get('height').replace('pt', ''))
                x = float(element.get('x').replace('pt', ''))
                y = float(element.get('y').replace('pt', ''))

                # Calculate new dimensions maintaining aspect ratio
                new_width = width * image_scale
                new_height = height * image_scale

                # Always position at the absolute left printable edge
                new_x = TRUE_LEFT_EDGE
                print(f"Positioning image at absolute left printable edge: {TRUE_LEFT_EDGE}pt")

                # Update element attributes
                element.set('width', f"{new_width}pt")
                element.set('height', f"{new_height}pt")
                element.set('x', f"{new_x}pt")
                element.set('y', f"{y}pt")  # Keep original y position

                # Calculate the rightmost edge of this image
                right_edge = new_x + new_width
                max_image_right_edge = max(max_image_right_edge, right_edge)

                # Update orgPos element if it exists
                parent = None
                if USING_LXML:
                    parent = element.getparent()

                org_pos = None
                if USING_LXML and parent is not None:
                    org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')
                else:
                    # For standard ElementTree, iterate through all orgPos elements
                    for pos in root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos'):
                        pos_x = float(pos.get('x').replace('pt', ''))
                        pos_y = float(pos.get('y').replace('pt', ''))
                        pos_width = float(pos.get('width').replace('pt', ''))
                        pos_height = float(pos.get('height').replace('pt', ''))

                        # If this orgPos has similar dimensions to our original element, it's likely the one
                        if abs(pos_x - x) < 0.1 and abs(pos_y - y) < 0.1 and \
                           abs(pos_width - width) < 0.1 and abs(pos_height - height) < 0.1:
                            org_pos = pos
                            break

                if org_pos is not None:
                    org_pos.set('width', f"{new_width}pt")
                    org_pos.set('height', f"{new_height}pt")
                    org_pos.set('x', f"{new_x}pt")
                    org_pos.set('y', f"{y}pt")

                print(f"Scaled image from {width}x{height}pt to {new_width}x{new_height}pt and placed at left margin")

        # Reposition text elements to be after the images
        if text_elements:
            text_x = max_image_right_edge + text_margin_pt
            print(f"Positioning text at x={text_x}pt ({text_margin}mm after images)")

            for element in text_elements:
                element.set('x', f"{text_x}pt")
                print(f"Moved text element to x={text_x}pt")

        # Vertically center elements if requested
        if center_vertically:
            if not USING_LXML:
                print("Warning: Full vertical centering requires lxml. Install with: pip install lxml")
                print("Proceeding with limited centering...")

            # Get all objects that need centering
            object_styles = root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle')

            if object_styles:
                # Calculate the available vertical space on the label
                paper_height = float(label_configs['width'])

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

                print(f"Group height: {group_height}pt")
                print(f"Center of label: {center_of_paper}pt")
                print(f"Applying offset of {offset}pt to center elements")

                # Second pass: adjust each object's position
                for obj in object_styles:
                    orig_y = orig_positions[obj]['y']
                    new_y = orig_y + offset
                    obj.set('y', f"{new_y}pt")
                    print(f"Centered object from y={orig_y}pt to y={new_y}pt")

                    # Also update corresponding image orgPos if exists
                    if USING_LXML:
                        parent = obj.getparent()
                        if parent is not None and parent.tag.endswith('}image'):
                            org_pos = parent.find('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos')
                            if org_pos is not None:
                                org_pos.set('y', f"{new_y}pt")
                                print(f"Updated image position y to {new_y}pt")
                    else:
                        # Without lxml, find image orgPos elements by matching coordinates
                        for orgPos in root.findall('.//{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos'):
                            if abs(float(orgPos.get('y').replace('pt', '')) - orig_y) < 0.1:
                                orgPos.set('y', f"{new_y}pt")
                                print(f"Updated image position y to {new_y}pt")

                print(f"All objects have been centered as a group")

        # Save the modified XML
        tree.write(xml_path, encoding='UTF-8', xml_declaration=True)

        # Create a new ZIP file with the modified content
        with zipfile.ZipFile(output_file, 'w') as zipf:
            for root_dir, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)

        print(f"Created modified LBX file: {output_file}")

    finally:
        # Clean up the temp directory
        shutil.rmtree(temp_dir)

def main():
    title = f"{Fore.CYAN}{Style.BRIGHT}Brother LBX Label File Modifier{Style.RESET_ALL}"
    description = f"""
    {title}
    {Fore.CYAN}=============================={Style.RESET_ALL}

    This tool allows you to customize Brother P-touch label (.lbx) files by:
      {Fore.GREEN}- Changing the font size{Style.RESET_ALL}
      {Fore.GREEN}- Modifying the label tape width{Style.RESET_ALL}
      {Fore.GREEN}- Vertically centering elements{Style.RESET_ALL}
      {Fore.GREEN}- Scaling images while preserving aspect ratio{Style.RESET_ALL}
      {Fore.GREEN}- Positioning text after images with customizable margin{Style.RESET_ALL}

    {Fore.YELLOW}{Style.BRIGHT}Examples:{Style.RESET_ALL}
      {Fore.BLUE}# Change font size to 10pt on a 12mm label{Style.RESET_ALL}
      change-lbx.py input.lbx output.lbx -f 10

      {Fore.BLUE}# Use 24mm tape with 12pt font size{Style.RESET_ALL}
      change-lbx.py input.lbx output.lbx -f 12 -l 24

      {Fore.BLUE}# Center elements vertically{Style.RESET_ALL}
      change-lbx.py input.lbx output.lbx -c

      {Fore.BLUE}# Scale images to 150%% of original size{Style.RESET_ALL}
      change-lbx.py input.lbx output.lbx -s 1.5

      {Fore.BLUE}# Set text margin to 3mm from images{Style.RESET_ALL}
      change-lbx.py input.lbx output.lbx -m 3
    """

    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=RawDescriptionHelpFormatter,
        prog="change-lbx.py"
    )

    parser.add_argument('input_file',
                        help=f'Input .lbx file to modify')
    parser.add_argument('output_file',
                        help=f'Path for the modified output file')

    font_group = parser.add_argument_group(f'{Fore.CYAN}Font Options{Style.RESET_ALL}')
    font_group.add_argument('-f', '--font-size',
                        type=int,
                        default=8,
                        metavar='SIZE',
                        help=f'Font size in points (default: {Fore.GREEN}8{Style.RESET_ALL})')

    label_group = parser.add_argument_group(f'{Fore.CYAN}Label Options{Style.RESET_ALL}')
    label_group.add_argument('-l', '--label-size',
                        type=int,
                        choices=[12, 18, 24],
                        default=12,
                        metavar='MM',
                        help=f'Label tape size in mm - 12, 18, or 24 (default: {Fore.GREEN}12{Style.RESET_ALL})')

    layout_group = parser.add_argument_group(f'{Fore.CYAN}Layout Options{Style.RESET_ALL}')
    layout_group.add_argument('-c', '--center-vertically',
                        action='store_true',
                        help=f'Center elements vertically on the label')
    layout_group.add_argument('-s', '--image-scale',
                        type=float,
                        default=1.0,
                        metavar='FACTOR',
                        help=f'Scale factor for images, e.g. 1.5 for 150%% (default: {Fore.GREEN}1.0{Style.RESET_ALL})')
    layout_group.add_argument('-m', '--text-margin',
                        type=float,
                        default=1.0,
                        metavar='MM',
                        help=f'Margin between image and text in mm (default: {Fore.GREEN}1.0{Style.RESET_ALL})')

    version_string = f"{Fore.CYAN}change-lbx.py{Style.RESET_ALL} {Fore.GREEN}1.0{Style.RESET_ALL}"
    parser.add_argument('-v', '--version',
                        action='version',
                        version=version_string)

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        parser.error(f"{Fore.RED}Input file '{args.input_file}' not found.{Style.RESET_ALL}")
        return 1

    try:
        modify_lbx(args.input_file, args.output_file, args.font_size, args.label_size,
                  args.center_vertically, args.image_scale, args.text_margin)
        print(f"{Fore.GREEN}✓ Successfully modified label file!{Style.RESET_ALL}")
        return 0
    except Exception as e:
        parser.error(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
