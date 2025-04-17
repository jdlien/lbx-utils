#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LBX Generator for lbxyml2lbx
"""

import os
import re
import uuid
import datetime
import zipfile
import tempfile
import shutil
from lxml import etree
from rich.console import Console

from ..models import LabelConfig, TextObject, ImageObject, GroupObject, ContainerObject, BarcodeObject
from ..utils import LABEL_SIZES, DEFAULT_PRINTER_ID, DEFAULT_PRINTER_NAME, convert_to_pt
from ..utils.conversion import MM_TO_PT

# Create console for rich output
console = Console()

class LbxGenerator:
    """Generates LBX files from a LabelConfig."""

    def __init__(self, config: LabelConfig):
        """Initialize with a label configuration."""
        self.config = config
        self.temp_dir = None
        self.xml_path = None
        self.prop_xml_path = None

    def create_label_xml(self):
        """Create the label.xml file with the configured elements."""
        # Create the document with proper namespaces using lxml
        nsmap = {
            "pt": "http://schemas.brother.info/ptouch/2007/lbx/main",
            "style": "http://schemas.brother.info/ptouch/2007/lbx/style",
            "text": "http://schemas.brother.info/ptouch/2007/lbx/text",
            "draw": "http://schemas.brother.info/ptouch/2007/lbx/draw",
            "image": "http://schemas.brother.info/ptouch/2007/lbx/image",
            "barcode": "http://schemas.brother.info/ptouch/2007/lbx/barcode",
            "database": "http://schemas.brother.info/ptouch/2007/lbx/database",
            "table": "http://schemas.brother.info/ptouch/2007/lbx/table",
            "cable": "http://schemas.brother.info/ptouch/2007/lbx/cable"
        }

        # Create root element with namespaces
        root = etree.Element("{http://schemas.brother.info/ptouch/2007/lbx/main}document",
                            attrib={"version": "1.9", "generator": "com.brother.PtouchEditor"},
                            nsmap=nsmap)

        # Add body element
        body = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/main}body")
        body.set("currentSheet", "Sheet 1")
        body.set("direction", "LTR")

        # Add sheet element
        sheet = etree.SubElement(body, "{http://schemas.brother.info/ptouch/2007/lbx/style}sheet")
        sheet.set("name", "Sheet 1")

        # Add paper element with size-specific attributes
        size_mm = self.config.size_mm
        console.print(f"[blue]Using label size: {size_mm}mm (format code: {LABEL_SIZES[size_mm]['format']})[/blue]")

        size_config = LABEL_SIZES[size_mm]
        paper = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/style}paper")
        paper.set("media", "0")
        paper.set("width", size_config["width"])

        # Calculate height based on specified width - adjust if width is specified
        # Default is auto-length (2834.4pt)
        paper_height = "2834.4pt"
        is_auto_length = self.config.width == "auto"

        if not is_auto_length:
            # Convert width to points using the convert_to_pt function
            paper_height = convert_to_pt(self.config.width)

        paper.set("height", paper_height)

        # Calculate margins based on user settings (1mm ≈ 2.83pt)
        # Minimum margin is 2mm (5.6pt), treat it as a default/minimum
        min_margin_pt = 5.6

        # Use user margin directly if specified, otherwise use minimum
        if hasattr(self.config, 'margin'):
            user_margin_pt = self.config.margin * MM_TO_PT
            # Ensure margin isn't less than minimum
            margin_pt = max(user_margin_pt, min_margin_pt)
        else:
            margin_pt = min_margin_pt

        console.print(f"[blue]Using margin: {margin_pt}pt[/blue]")

        # Get orientation to determine margin placement
        orientation = self.config.orientation.lower()

        # For portrait orientation, we swap the margin application
        if orientation == "portrait":
            # In portrait, the tape feeds top-to-bottom, so margins are on left/right
            paper.set("marginLeft", size_config["marginLeft"])
            paper.set("marginRight", size_config["marginRight"])
            paper.set("marginTop", f"{margin_pt}pt")
            paper.set("marginBottom", f"{margin_pt}pt")
            console.print(f"[blue]Portrait margins: vertical margins={margin_pt}pt[/blue]")
        else:
            # In landscape, the tape feeds left-to-right, so margins are on top/bottom
            paper.set("marginLeft", size_config["marginLeft"])
            paper.set("marginRight", size_config["marginRight"])
            paper.set("marginTop", f"{margin_pt}pt")
            paper.set("marginBottom", f"{margin_pt}pt")
            console.print(f"[blue]Landscape margins: horizontal margins={margin_pt}pt[/blue]")

        # Ensure orientation is correctly set
        console.print(f"[blue]Setting orientation to: {orientation}[/blue]")
        paper.set("orientation", orientation)

        paper.set("autoLength", "true" if is_auto_length else "false")
        paper.set("monochromeDisplay", "true")
        paper.set("printColorDisplay", "false")
        paper.set("printColorsID", "0")
        paper.set("paperColor", self.config.background)
        paper.set("paperInk", self.config.color)
        paper.set("split", "1")
        paper.set("format", size_config["format"])
        paper.set("backgroundTheme", "0")
        paper.set("printerID", DEFAULT_PRINTER_ID)
        paper.set("printerName", DEFAULT_PRINTER_NAME)

        # Add cut line element
        cut_line = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/style}cutLine")
        cut_line.set("regularCut", "0pt")
        cut_line.set("freeCut", "")

        # Calculate background width based on paper height
        # For non-auto layouts, we need to set the width based on the specified width
        # Reverting to the previous default calculation for now
        background_width = "34.4pt"  # Default for auto-length
        if not is_auto_length:
            # Use the same width we calculated for paper height
            background_width = paper_height

        # Set up the background element based on orientation
        background = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/style}backGround")

        # Default values (for landscape)
        bg_x = "5.6pt"
        bg_y = size_config["background_y"]
        bg_width = background_width
        bg_height = size_config["background_height"]

        # In portrait mode, swap x/y and width/height
        if orientation == "portrait":
            # In portrait mode, x should be left margin and y should be 5.6pt (from top)
            bg_x = size_config["marginLeft"]
            bg_y = "5.6pt"

            # Swap width and height for portrait
            bg_width = size_config["background_height"]  # Height becomes width
            bg_height = background_width  # Width becomes height

            console.print(f"[blue]Using portrait background: x={bg_x}, y={bg_y}, width={bg_width}, height={bg_height}[/blue]")

        background.set("x", bg_x)
        background.set("y", bg_y)
        background.set("width", bg_width)
        background.set("height", bg_height)
        background.set("brushStyle", "NULL")
        background.set("brushId", "0")
        background.set("userPattern", "NONE")
        background.set("userPatternId", "0")
        background.set("color", self.config.color)
        background.set("printColorNumber", "1")
        background.set("backColor", self.config.background)
        background.set("backPrintColorNumber", "0")

        # Add objects container
        objects = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/main}objects")

        # Process each object from the config
        for obj in self.config.objects:
            if isinstance(obj, TextObject):
                self._add_text_object(objects, obj)
            elif isinstance(obj, ImageObject):
                self._add_image_object(objects, obj)
            elif isinstance(obj, GroupObject):
                self._add_group_object(objects, obj)
            elif isinstance(obj, ContainerObject):
                self._process_container_object(objects, obj)
            elif isinstance(obj, BarcodeObject):
                self._add_barcode_object(objects, obj)

        # Create ElementTree
        tree = etree.ElementTree(root)
        return tree

    def _add_text_object(self, parent, text_obj: TextObject, parent_coords=None):
        """
        Add a text object to the parent element.

        Args:
            parent: The parent XML element
            text_obj: The text object to add
            parent_coords: Optional (x,y) tuple of parent coordinates for nested elements
        """
        # Create text element
        text_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/text}text")

        # Get label size configuration
        size_config = LABEL_SIZES[self.config.size_mm]

        # Debug info - print original coordinates
        console.print(f"[blue]Text object positioning: x={text_obj.x}, y={text_obj.y}[/blue]")
        console.print(f"[blue]Text object dimensions: width={text_obj.width}, height={text_obj.height}[/blue]")

        # Add object style
        obj_style = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")

        # Use convert_to_pt to ensure all values are in points
        x_value_str = convert_to_pt(text_obj.x)
        y_value_str = convert_to_pt(text_obj.y)

        obj_style.set("x", x_value_str)
        obj_style.set("y", y_value_str)
        obj_style.set("width", text_obj.width)
        obj_style.set("height", text_obj.height)
        obj_style.set("backColor", "#FFFFFF")
        obj_style.set("backPrintColorNumber", "0")
        obj_style.set("ropMode", "COPYPEN")
        obj_style.set("angle", "0" if not text_obj.vertical else "90")
        obj_style.set("anchor", "TOPLEFT")
        obj_style.set("flip", "NONE")

        # Add pen (border)
        pen = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}pen")
        pen.set("style", "NULL")
        pen.set("widthX", "0.5pt")
        pen.set("widthY", "0.5pt")
        pen.set("color", "#000000")
        pen.set("printColorNumber", "1")

        # Add brush
        brush = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}brush")
        brush.set("style", "NULL")
        brush.set("color", "#000000")
        brush.set("printColorNumber", "1")
        brush.set("id", "0")

        # Add expanded properties
        expanded = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}expanded")
        obj_name = f"Text{uuid.uuid4().hex[:4]}"
        if text_obj.name:
            obj_name = text_obj.name
        expanded.set("objectName", obj_name)
        expanded.set("ID", "0")
        expanded.set("lock", "0")
        expanded.set("templateMergeTarget", "LABELLIST")
        expanded.set("templateMergeType", "NONE")
        expanded.set("templateMergeID", "0")
        expanded.set("linkStatus", "NONE")
        expanded.set("linkID", "0")

        # Add font info
        font_info_elem = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}ptFontInfo")

        # Add log font
        log_font = etree.SubElement(font_info_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}logFont")
        log_font.set("name", text_obj.font_info.name)
        log_font.set("width", "0")
        log_font.set("italic", text_obj.font_info.italic)
        log_font.set("weight", text_obj.font_info.weight)
        log_font.set("charSet", "0")
        log_font.set("pitchAndFamily", "2")

        # Add font extension
        font_ext = etree.SubElement(font_info_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt")
        font_ext.set("effect", "NOEFFECT")
        font_ext.set("underline", text_obj.font_info.underline)
        font_ext.set("strikeout", "0")
        font_ext.set("size", text_obj.font_info.size)
        font_ext.set("orgSize", text_obj.font_info.org_size)
        font_ext.set("textColor", text_obj.font_info.color)
        font_ext.set("textPrintColorNumber", text_obj.font_info.print_color_number)

        # Add text control
        text_control = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}textControl")
        text_control.set("control", "AUTOLEN")
        text_control.set("clipFrame", "false")
        text_control.set("aspectNormal", "true")
        text_control.set("shrink", "true")
        text_control.set("autoLF", "false")
        text_control.set("avoidImage", "false")

        # Add text alignment
        align_value = text_obj.align.upper()
        text_align = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}textAlign")
        text_align.set("horizontalAlignment", align_value)
        text_align.set("verticalAlignment", "TOP")
        text_align.set("inLineAlignment", "BASELINE")

        # Add text style
        text_style = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}textStyle")
        text_style.set("vertical", "true" if text_obj.vertical else "false")
        text_style.set("nullBlock", "false")
        text_style.set("charSpace", "0")
        text_style.set("lineSpace", "0")
        text_style.set("orgPoint", text_obj.font_info.size)
        text_style.set("combinedChars", "false")

        # Add data - we'll set the text content here
        data = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}data")
        # Store for later
        data.attrib["_text_content"] = text_obj.text

        # Add string items
        for item in text_obj.string_items:
            string_item = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}stringItem")
            string_item.set("charLen", str(item.char_len))

            # Add font info for string item
            item_font_info = etree.SubElement(string_item, "{http://schemas.brother.info/ptouch/2007/lbx/text}ptFontInfo")

            # Add log font for string item
            item_log_font = etree.SubElement(item_font_info, "{http://schemas.brother.info/ptouch/2007/lbx/text}logFont")
            item_log_font.set("name", item.font_info.name)
            item_log_font.set("width", "0")
            item_log_font.set("italic", item.font_info.italic)
            item_log_font.set("weight", item.font_info.weight)
            item_log_font.set("charSet", "0")
            item_log_font.set("pitchAndFamily", "2")

            # Add font extension for string item
            item_font_ext = etree.SubElement(item_font_info, "{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt")
            item_font_ext.set("effect", "NOEFFECT")
            item_font_ext.set("underline", item.font_info.underline)
            item_font_ext.set("strikeout", "0")
            item_font_ext.set("size", item.font_info.size)
            item_font_ext.set("orgSize", item.font_info.org_size)
            item_font_ext.set("textColor", item.font_info.color)
            item_font_ext.set("textPrintColorNumber", item.font_info.print_color_number)

        return text_elem

    def _add_image_object(self, parent, image_obj: ImageObject, parent_coords=None):
        """
        Add an image object to the parent element.

        Args:
            parent: The parent XML element
            image_obj: The image object to add
            parent_coords: Optional (x,y) tuple of parent coordinates for nested elements
        """
        # Create image element
        image_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/image}image")

        # Debug info - print original coordinates
        console.print(f"[blue]Image object positioning: x={image_obj.x}, y={image_obj.y}[/blue]")
        console.print(f"[blue]Image object dimensions: width={image_obj.width}, height={image_obj.height}[/blue]")

        # Add object style
        obj_style = etree.SubElement(image_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")

        # Use convert_to_pt to ensure all values are in points
        x_value_str = convert_to_pt(image_obj.x)
        y_value_str = convert_to_pt(image_obj.y)

        obj_style.set("x", x_value_str)
        obj_style.set("y", y_value_str)
        obj_style.set("width", image_obj.width)
        obj_style.set("height", image_obj.height)
        obj_style.set("backColor", "#FFFFFF")
        obj_style.set("backPrintColorNumber", "0")
        obj_style.set("ropMode", "COPYPEN")
        obj_style.set("angle", "0")
        obj_style.set("anchor", "TOPLEFT")
        obj_style.set("flip", "NONE")

        # Add pen
        pen = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}pen")
        pen.set("style", "NULL")
        pen.set("widthX", "0.5pt")
        pen.set("widthY", "0.5pt")
        pen.set("color", "#000000")
        pen.set("printColorNumber", "1")

        # Add brush
        brush = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}brush")
        brush.set("style", "NULL")
        brush.set("color", "#000000")
        brush.set("printColorNumber", "1")
        brush.set("id", "0")

        # Add expanded properties
        expanded = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}expanded")
        obj_name = f"Image{uuid.uuid4().hex[:4]}"
        if image_obj.name:
            obj_name = image_obj.name
        expanded.set("objectName", obj_name)
        expanded.set("ID", "0")
        expanded.set("lock", "0")
        expanded.set("templateMergeTarget", "LABELLIST")
        expanded.set("templateMergeType", "NONE")
        expanded.set("templateMergeID", "0")
        expanded.set("linkStatus", "NONE")
        expanded.set("linkID", "0")

        # Get image file name
        original_image_path = os.path.basename(image_obj.file_path)
        image_extension = os.path.splitext(original_image_path)[1].lower()

        # Determine if we need to convert this image to BMP
        if image_obj.monochrome or image_extension not in ['.png', '.bmp']:
            # Create a unique name for the BMP in the LBX file
            dest_filename = f"Object{uuid.uuid4().hex[:4]}.bmp"
            image_obj.needs_conversion = True
        else:
            # Use the original filename when not converting
            dest_filename = original_image_path
            image_obj.needs_conversion = False

        # Store the destination filename
        image_obj.dest_filename = dest_filename

        # Add image elements based on the image type (binary or path)
        image_format = etree.SubElement(image_elem, "{http://schemas.brother.info/ptouch/2007/lbx/image}format")
        image_format.set("type", "1")
        image_format.set("bpp", "24")
        image_format.set("orgSize", "74340")

        # Add image style
        image_style = etree.SubElement(image_elem, "{http://schemas.brother.info/ptouch/2007/lbx/image}style")

        # Add trimming element
        trimming = etree.SubElement(image_style, "{http://schemas.brother.info/ptouch/2007/lbx/image}trimming")
        trimming.set("left", "0pt")
        trimming.set("top", "0pt")
        trimming.set("right", "0pt")
        trimming.set("bottom", "0pt")
        trimming.set("trimWidth", "0pt")
        trimming.set("trimHeight", "0pt")
        trimming.set("trimOrgWidth", "0pt")
        trimming.set("trimOrgHeight", "0pt")

        # Add original position element (use the same x value without adjustment)
        org_pos = etree.SubElement(image_style, "{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos")
        org_pos.set("x", x_value_str)
        org_pos.set("y", y_value_str)
        org_pos.set("width", image_obj.width)
        org_pos.set("height", image_obj.height)

        # Add effect element
        effect = etree.SubElement(image_style, "{http://schemas.brother.info/ptouch/2007/lbx/image}effect")
        effect.set("effect", image_obj.effect_type)
        effect.set("brightness", "50")
        effect.set("contrast", "50")
        effect.set("photoIndex", "4")

        # Add mono element
        mono = etree.SubElement(image_style, "{http://schemas.brother.info/ptouch/2007/lbx/image}mono")
        mono.set("operationKind", image_obj.operation_kind)
        mono.set("reverse", "0")
        mono.set("ditherKind", "MESH")
        mono.set("threshold", "128")
        mono.set("gamma", "100")
        mono.set("ditherEdge", "0")
        mono.set("rgbconvProportionRed", "30")
        mono.set("rgbconvProportionGreen", "59")
        mono.set("rgbconvProportionBlue", "11")
        mono.set("rgbconvProportionReversed", "0")

        return image_elem

    def _add_group_object(self, parent, group_obj: GroupObject, parent_coords=None):
        """
        Add a group object to the parent element.

        Args:
            parent: The parent XML element
            group_obj: The group object to add
            parent_coords: Optional (x,y) tuple of parent coordinates for nested elements
        """
        # Create group element
        group_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/main}group")

        # Debug info - print original coordinates
        console.print(f"[green]Group object '{group_obj.name}' raw positioning: x={group_obj.x}, y={group_obj.y}[/green]")
        console.print(f"[blue]Group object dimensions: width={group_obj.width}, height={group_obj.height}[/blue]")

        # Add debug info about positioning flag
        is_positioned = getattr(group_obj, '_positioned', False)
        console.print(f"[blue]Group has explicit positioning: {is_positioned}[/blue]")

        # Add object style
        obj_style = etree.SubElement(group_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")

        # For explicitly positioned groups, use the original coordinates
        if is_positioned:
            # Check if we have original coordinates stored (these were the values before conversion)
            original_x = getattr(group_obj, '_original_x', None)
            original_y = getattr(group_obj, '_original_y', None)

            if original_x is not None and original_y is not None:
                # Use the original values that were directly from YAML
                console.print(f"[yellow]Using original YAML coordinates: x={original_x}, y={original_y}[/yellow]")
                x_value_str = convert_to_pt(original_x)
                y_value_str = convert_to_pt(original_y)
            else:
                # Fallback to the current x,y (which might have been modified by layout engine)
                x_value_str = convert_to_pt(group_obj.x)
                y_value_str = convert_to_pt(group_obj.y)

            console.print(f"[yellow]Using explicitly positioned coordinates: x={x_value_str}, y={y_value_str}[/yellow]")
        else:
            # For non-positioned groups, use the coordinates as calculated by the layout engine
            x_value_str = convert_to_pt(group_obj.x)
            y_value_str = convert_to_pt(group_obj.y)

        # If this group has a parent with coordinates, adjust this group's coordinates to be absolute
        if parent_coords:
            parent_x, parent_y = parent_coords
            group_local_x = float(x_value_str.rstrip('pt'))
            group_local_y = float(y_value_str.rstrip('pt'))

            # Calculate absolute coordinates
            group_abs_x = parent_x + group_local_x
            group_abs_y = parent_y + group_local_y

            # Update to absolute coordinates
            x_value_str = f"{group_abs_x}pt"
            y_value_str = f"{group_abs_y}pt"

            console.print(f"[blue]Adjusted nested group coordinates: local ({group_local_x}pt, {group_local_y}pt) -> absolute ({group_abs_x}pt, {group_abs_y}pt)[/blue]")

        # Debug the conversion
        console.print(f"[blue]Final group coordinates: x={x_value_str}, y={y_value_str}[/blue]")

        # Set coordinates in XML - ensure these are properly converted to points
        obj_style.set("x", x_value_str)
        obj_style.set("y", y_value_str)

        # Store the group's absolute position for child element positioning
        group_x = float(x_value_str.rstrip('pt'))
        group_y = float(y_value_str.rstrip('pt'))

        # Add objects container for child objects first (before calculating dimensions)
        objects_elem = etree.SubElement(group_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objects")

        # Process each child object and collect their data for auto-sizing calculation
        child_dimensions = []
        for child_obj in group_obj.objects:
            child_data = {'obj': child_obj}

            # Convert child x/y to points for consistent calculations
            child_x = float(convert_to_pt(child_obj.x).rstrip('pt'))
            child_y = float(convert_to_pt(child_obj.y).rstrip('pt'))

            # Get width and height (both should be available)
            if hasattr(child_obj, 'width') and child_obj.width and child_obj.width != 'auto':
                child_width = float(convert_to_pt(child_obj.width).rstrip('pt'))
            else:
                # If no width, use a default minimum width
                child_width = 20.0  # Default minimum width

            if hasattr(child_obj, 'height') and child_obj.height and child_obj.height != 'auto':
                child_height = float(convert_to_pt(child_obj.height).rstrip('pt'))
            else:
                # If no height, use a default minimum height
                child_height = 20.0  # Default minimum height

            # Store the bounding box of this child using its local coordinates (for auto-sizing)
            child_data['x1'] = child_x
            child_data['y1'] = child_y
            child_data['x2'] = child_x + child_width
            child_data['y2'] = child_y + child_height

            child_dimensions.append(child_data)

            # Store the original local position before we adjust it
            child_original_x = child_obj.x
            child_original_y = child_obj.y

            # Calculate absolute position by adding the group's position
            abs_x = child_x + group_x
            abs_y = child_y + group_y

            # Log the calculation
            console.print(f"[blue]Adjusting child position in group: local ({child_x}pt, {child_y}pt) -> absolute ({abs_x}pt, {abs_y}pt)[/blue]")

            # Temporarily adjust the child's position to be absolute
            child_obj.x = f"{abs_x}pt"
            child_obj.y = f"{abs_y}pt"

            # Add the child to the group with the adjusted absolute position
            if isinstance(child_obj, TextObject):
                self._add_text_object(objects_elem, child_obj)
            elif isinstance(child_obj, ImageObject):
                self._add_image_object(objects_elem, child_obj)
            elif isinstance(child_obj, GroupObject):
                # Support nested groups - pass the parent coordinates for further adjustment
                self._add_group_object(objects_elem, child_obj, (group_x, group_y))
            elif isinstance(child_obj, BarcodeObject):
                self._add_barcode_object(objects_elem, child_obj, (group_x, group_y))

            # Restore original local position
            child_obj.x = child_original_x
            child_obj.y = child_original_y

        # Calculate automatic dimensions if needed
        should_auto_width = group_obj.width == "auto" or not group_obj.width
        should_auto_height = group_obj.height == "auto" or not group_obj.height

        if should_auto_width or should_auto_height:
            # Find the bounding box of all children
            if child_dimensions:
                # Initialize with first child's dimensions
                min_x = min(d['x1'] for d in child_dimensions)
                max_x = max(d['x2'] for d in child_dimensions)
                min_y = min(d['y1'] for d in child_dimensions)
                max_y = max(d['y2'] for d in child_dimensions)

                # Calculate dimensions with padding
                padding = 5.0  # Add some padding in points
                width = max_x - min_x + (2 * padding)
                height = max_y - min_y + (2 * padding)

                console.print(f"[blue]Auto-calculated group dimensions: width={width}pt, height={height}pt[/blue]")

                # Set the auto-calculated dimensions only for those that should be auto
                if should_auto_width:
                    group_obj.width = f"{width}pt"
                if should_auto_height:
                    group_obj.height = f"{height}pt"
            else:
                # If no children, use minimal default dimensions
                if should_auto_width:
                    group_obj.width = "30pt"
                if should_auto_height:
                    group_obj.height = "30pt"

                console.print(f"[yellow]Warning: Group has no children, using default dimensions[/yellow]")

        # Set the final dimensions
        obj_style.set("width", group_obj.width)
        obj_style.set("height", group_obj.height)

        obj_style.set("backColor", group_obj.background_color)
        obj_style.set("backPrintColorNumber", "0")
        obj_style.set("ropMode", "COPYPEN")
        obj_style.set("angle", "0")
        obj_style.set("anchor", "TOPLEFT")
        obj_style.set("flip", "NONE")

        # Add pen (border)
        pen = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}pen")
        # Use INSIDEFRAME for visible borders, NULL for no border
        pen_style = group_obj.border_style if group_obj.border_style else "NULL"
        pen.set("style", pen_style)
        pen.set("widthX", "0.5pt")
        pen.set("widthY", "0.5pt")
        pen.set("color", "#000000")
        pen.set("printColorNumber", "1")

        # Add brush
        brush = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}brush")
        brush.set("style", "NULL")
        brush.set("color", "#000000")
        brush.set("printColorNumber", "1")
        brush.set("id", "0")

        # Add expanded properties
        expanded = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}expanded")
        obj_name = f"Group{uuid.uuid4().hex[:4]}"
        if group_obj.name:
            obj_name = group_obj.name
        elif group_obj.id:
            obj_name = f"Group_{group_obj.id}"
        expanded.set("objectName", obj_name)
        expanded.set("ID", "0")
        expanded.set("lock", "2")  # 2 seems to be used for groups
        expanded.set("templateMergeTarget", "LABELLIST")
        expanded.set("templateMergeType", "NONE")
        expanded.set("templateMergeID", "0")
        expanded.set("linkStatus", "NONE")
        expanded.set("linkID", "0")

    def _process_container_object(self, parent, container_obj: ContainerObject, parent_coords=None):
        """
        Process a container object's children without creating a group element.

        Unlike group objects, containers don't create their own XML element.
        Their children are added directly to the parent.

        Args:
            parent: The parent XML element
            container_obj: The container object to process
            parent_coords: Optional (x,y) tuple of parent coordinates for nested containers
        """
        # Debug info
        console.print(f"[green]Processing container '{container_obj.name}' at position: x={container_obj.x}, y={container_obj.y}[/green]")
        console.print(f"[blue]Container has explicit positioning: {getattr(container_obj, '_positioned', False)}[/blue]")

        # Get container position
        is_positioned = getattr(container_obj, '_positioned', False)

        # For explicitly positioned containers, use the original coordinates
        if is_positioned:
            # Check if we have original coordinates stored
            original_x = getattr(container_obj, '_original_x', None)
            original_y = getattr(container_obj, '_original_y', None)

            if original_x is not None and original_y is not None:
                # Use the original values that were directly from YAML
                console.print(f"[yellow]Using original YAML coordinates: x={original_x}, y={original_y}[/yellow]")
                x_value_str = convert_to_pt(original_x)
                y_value_str = convert_to_pt(original_y)
            else:
                # Fallback to the current x,y
                x_value_str = convert_to_pt(container_obj.x)
                y_value_str = convert_to_pt(container_obj.y)
        else:
            # For non-positioned containers, use the coordinates as calculated by the layout engine
            x_value_str = convert_to_pt(container_obj.x)
            y_value_str = convert_to_pt(container_obj.y)

        # Get container position as float values
        container_x = float(x_value_str.rstrip('pt'))
        container_y = float(y_value_str.rstrip('pt'))

        # If this container has a parent with coordinates, adjust this container's coordinates
        if parent_coords:
            parent_x, parent_y = parent_coords

            # Calculate absolute coordinates
            container_abs_x = parent_x + container_x
            container_abs_y = parent_y + container_y

            # Update to absolute coordinates
            container_x = container_abs_x
            container_y = container_abs_y

            console.print(f"[blue]Adjusted nested container coordinates: local ({container_x}pt, {container_y}pt) -> absolute ({container_abs_x}pt, {container_abs_y}pt)[/blue]")

        console.print(f"[blue]Container position in points: x={container_x}pt, y={container_y}pt[/blue]")

        # Calculate automatic dimensions if needed before processing children
        # (Auto-dimension calculation code remains unchanged)

        # Process each child object and add it directly to the parent
        # Since containers don't create their own XML element, we need to adjust
        # each child's position to be relative to the container's position
        for child_obj in container_obj.objects:
            # Store original position
            child_original_x = child_obj.x
            child_original_y = child_obj.y

            # Convert child coordinates to points for consistent calculations
            child_x = float(convert_to_pt(child_obj.x).rstrip('pt'))
            child_y = float(convert_to_pt(child_obj.y).rstrip('pt'))

            # Since containers don't create a parent group element in the XML,
            # we need to adjust the position of children to be absolute
            abs_x = child_x + container_x
            abs_y = child_y + container_y
            console.print(f"[blue]Adjusting child position: from ({child_x}pt, {child_y}pt) to ({abs_x}pt, {abs_y}pt)[/blue]")

            # Temporarily adjust the child's position to be absolute
            child_obj.x = f"{abs_x}pt"
            child_obj.y = f"{abs_y}pt"

            # Add the child to the parent with absolute coordinates
            if isinstance(child_obj, TextObject):
                self._add_text_object(parent, child_obj)
            elif isinstance(child_obj, ImageObject):
                self._add_image_object(parent, child_obj)
            elif isinstance(child_obj, GroupObject):
                self._add_group_object(parent, child_obj)
            elif isinstance(child_obj, ContainerObject):
                # Support nested containers - pass the container's coordinates
                self._process_container_object(parent, child_obj, (container_x, container_y))
            elif isinstance(child_obj, BarcodeObject):
                self._add_barcode_object(parent, child_obj, (container_x, container_y))

            # Restore original position
            child_obj.x = child_original_x
            child_obj.y = child_original_y

    def _add_barcode_object(self, parent, barcode_obj: BarcodeObject, parent_coords=None):
        """
        Add a barcode object to the parent element.

        Args:
            parent: The parent XML element
            barcode_obj: The barcode object to add
            parent_coords: Optional (x,y) tuple of parent coordinates for nested elements
        """
        # Create barcode element in the barcode namespace
        barcode_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/barcode}barcode")

        # Debug info - print original coordinates
        console.print(f"[blue]Barcode object positioning: x={barcode_obj.x}, y={barcode_obj.y}[/blue]")

        # Get the base width and height values
        width_value = convert_to_pt(barcode_obj.width)
        height_value = convert_to_pt(barcode_obj.height)

        # For QR codes, determine the size based on the standardized size value (1-5)
        if barcode_obj.type.lower() == "qr":
            # Get the size value (should be an integer 1-5)
            qr_size = barcode_obj.size

            # Check if size is a numeric value from 1-5
            if isinstance(qr_size, (int, float)):
                qr_size_int = int(qr_size)
                if 1 <= qr_size_int <= 5:
                    # Map the numeric size to a cell size in pt
                    cell_size_mapping = {
                        1: "0.8pt",  # Small
                        2: "1.2pt",  # Medium Small
                        3: "1.6pt",  # Medium
                        4: "2pt",    # Medium Large
                        5: "2.4pt"   # Large
                    }
                    cell_size = cell_size_mapping[qr_size_int]

                    # Map to the corresponding width/height based on cell size
                    # Using the observed factor of 29
                    size_factor = 29
                    cell_size_pt = float(cell_size.rstrip('pt'))
                    calculated_size = f"{cell_size_pt * size_factor}pt"

                    width_value = calculated_size
                    height_value = calculated_size

                    # Store the cell size for later use in the XML
                    standardized_cell_size = cell_size

                    console.print(f"[blue]Using standardized size {qr_size_int} => cell size: {cell_size}, dimensions: {calculated_size}[/blue]")
                else:
                    # Use default for invalid size
                    console.print(f"[yellow]Invalid QR size {qr_size_int}, using default size 4[/yellow]")
                    standardized_cell_size = "2pt"  # Default Medium Large
                    size_factor = 29
                    width_value = f"{2 * size_factor}pt"
                    height_value = f"{2 * size_factor}pt"
            else:
                # Handle string values by using the cell_size property
                cell_size = barcode_obj.cell_size

                # Parse the point value from the cell size
                if isinstance(cell_size, str) and cell_size.endswith('pt'):
                    try:
                        cell_size_pt = float(cell_size.rstrip('pt'))
                        # Use the size factor of 29
                        size_factor = 29
                        calculated_size = f"{cell_size_pt * size_factor}pt"
                        width_value = calculated_size
                        height_value = calculated_size
                        standardized_cell_size = cell_size
                        console.print(f"[blue]Using cell size: {cell_size}, dimensions: {calculated_size}[/blue]")
                    except ValueError:
                        # Default to medium-large if parsing fails
                        standardized_cell_size = "2pt"
                        width_value = "58pt"  # 2pt * 29
                        height_value = "58pt"
                        console.print(f"[yellow]Invalid cell size format, using default: 2pt[/yellow]")
                else:
                    # Default values for invalid cell size
                    standardized_cell_size = "2pt"
                    width_value = "58pt"  # 2pt * 29
                    height_value = "58pt"
                    console.print(f"[yellow]Invalid or missing cell size, using default: 2pt[/yellow]")

        console.print(f"[blue]Barcode dimensions: width={width_value}, height={height_value}[/blue]")

        # Add object style
        obj_style = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")

        # Use convert_to_pt to ensure all values are in points
        x_value_str = convert_to_pt(barcode_obj.x)
        y_value_str = convert_to_pt(barcode_obj.y)

        obj_style.set("x", x_value_str)
        obj_style.set("y", y_value_str)
        obj_style.set("width", width_value)
        obj_style.set("height", height_value)
        obj_style.set("backColor", "#FFFFFF")
        obj_style.set("backPrintColorNumber", "0")
        obj_style.set("ropMode", "COPYPEN")
        obj_style.set("angle", "0")  # Barcodes don't support rotation currently
        obj_style.set("anchor", "TOPLEFT")
        obj_style.set("flip", "NONE")

        # Add pen (border)
        pen = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}pen")
        pen.set("style", "INSIDEFRAME")
        pen.set("widthX", "0.5pt")
        pen.set("widthY", "0.5pt")
        pen.set("color", "#000000")
        pen.set("printColorNumber", "1")

        # Add brush
        brush = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}brush")
        brush.set("style", "NULL")
        brush.set("color", "#000000")
        brush.set("printColorNumber", "1")
        brush.set("id", "0")

        # Add expanded properties
        expanded = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}expanded")
        obj_name = f"Barcode{uuid.uuid4().hex[:4]}"
        expanded.set("objectName", obj_name)
        expanded.set("ID", "0")
        expanded.set("lock", "0")
        expanded.set("templateMergeTarget", "LABELLIST")
        expanded.set("templateMergeType", "NONE")
        expanded.set("templateMergeID", "0")
        expanded.set("linkStatus", "NONE")
        expanded.set("linkID", "0")

        # Add barcode style element (common to all barcode types)
        barcode_style = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/barcode}barcodeStyle")

        # Set protocol from barcode.protocol
        barcode_style.set("protocol", barcode_obj.protocol)

        # Set common barcode attributes
        barcode_style.set("lengths", str(barcode_obj.lengths))
        barcode_style.set("zeroFill", "true" if barcode_obj.zeroFill else "false")
        barcode_style.set("barWidth", str(barcode_obj.barWidth))
        barcode_style.set("barRatio", str(barcode_obj.barRatio))
        barcode_style.set("humanReadable", "true" if barcode_obj.humanReadable else "false")
        barcode_style.set("humanReadableAlignment", str(barcode_obj.humanReadableAlignment))
        barcode_style.set("checkDigit", "true" if barcode_obj.checkDigit else "false")
        barcode_style.set("autoLengths", "true" if barcode_obj.autoLengths else "false")
        barcode_style.set("margin", "true" if barcode_obj.margin else "false")
        barcode_style.set("sameLengthBar", "true" if barcode_obj.sameLengthBar else "false")
        barcode_style.set("bearerBar", "true" if barcode_obj.bearerBar else "false")

        # Add optional attributes if they have values
        if hasattr(barcode_obj, 'removeParentheses') and barcode_obj.removeParentheses:
            barcode_style.set("removeParentheses", "true")

        if hasattr(barcode_obj, 'startstopCode') and barcode_obj.startstopCode:
            barcode_style.set("startstopCode", str(barcode_obj.startstopCode))

        barcode_type = barcode_obj.type.lower()

        # For QR codes, add QR code-specific style
        if barcode_type == "qr":
            qrcode_style = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/barcode}qrcodeStyle")
            qrcode_style.set("model", str(barcode_obj.model))

            # Convert L, M, Q, H error correction to percentage values
            ec_mapping = {
                "L": "7%",
                "M": "15%",
                "Q": "25%",
                "H": "30%"
            }
            ecc_level = ec_mapping.get(barcode_obj.correction.upper(), "15%")  # Default to M (15%)
            qrcode_style.set("eccLevel", ecc_level)

            # Set the cell size based on our standardized value
            if 'standardized_cell_size' in locals():
                qrcode_style.set("cellSize", standardized_cell_size)
            else:
                # Use the cell_size property as fallback
                qrcode_style.set("cellSize", barcode_obj.cell_size)

            qrcode_style.set("mbcs", "auto")
            qrcode_style.set("joint", "1")

            # Handle version (auto or specific number)
            qrcode_style.set("version", str(barcode_obj.version))
            if barcode_obj.version != "auto":
                qrcode_style.set("changeVersionDrag", "true")

        # For RSS/GS1 DataBar barcodes
        elif barcode_type == "rss":
            rss_style = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/barcode}rssStyle")
            rss_style.set("model", str(barcode_obj.rssModel))
            rss_style.set("margin", "true" if barcode_obj.margin else "false")
            rss_style.set("autoLengths", "true" if barcode_obj.autoLengths else "false")
            rss_style.set("lengths", str(barcode_obj.lengths))
            rss_style.set("barWidth", str(barcode_obj.barWidth))
            rss_style.set("column", str(barcode_obj.column))
            rss_style.set("humanReadable", "true" if barcode_obj.humanReadable else "false")
            rss_style.set("humanReadableAlignment", str(barcode_obj.humanReadableAlignment))
            rss_style.set("autoAdd01", "true" if barcode_obj.autoAdd01 else "false")

        # For PDF417 barcodes
        elif barcode_type == "pdf417":
            pdf417_style = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/barcode}pdf417Style")
            pdf417_style.set("model", str(barcode_obj.pdf417Model))
            pdf417_style.set("width", str(barcode_obj.barWidth))
            pdf417_style.set("aspect", str(barcode_obj.aspect))
            pdf417_style.set("row", str(barcode_obj.row))
            pdf417_style.set("column", str(barcode_obj.column))
            pdf417_style.set("eccLevel", str(barcode_obj.eccLevel))
            pdf417_style.set("joint", str(barcode_obj.joint))

        # For DataMatrix barcodes
        elif barcode_type == "datamatrix":
            datamatrix_style = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/barcode}datamatrixStyle")
            datamatrix_style.set("model", str(barcode_obj.dataMatrixModel))
            datamatrix_style.set("cellSize", str(barcode_obj.cellSize))
            datamatrix_style.set("macro", str(barcode_obj.macro))
            datamatrix_style.set("fnc01", "true" if barcode_obj.fnc01 else "false")
            datamatrix_style.set("joint", str(barcode_obj.joint))

        # For MaxiCode barcodes
        elif barcode_type == "maxicode":
            maxicode_style = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/barcode}maxicodeStyle")
            maxicode_style.set("model", str(barcode_obj.maxiCodeModel))
            maxicode_style.set("joint", str(barcode_obj.joint))

        # Add data element
        data = etree.SubElement(barcode_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}data")
        # Use attrib["_text_content"] instead of .text to avoid linter error
        data.attrib["_text_content"] = str(barcode_obj.data)

        return barcode_elem

    def create_prop_xml(self):
        """Create the prop.xml file with metadata."""
        # Create namespaces
        nsmap = {
            "meta": "http://schemas.brother.info/ptouch/2007/lbx/meta",
            "dc": "http://purl.org/dc/elements/1.1/",
            "dcterms": "http://purl.org/dc/terms/"
        }

        # Create root element
        root = etree.Element("{http://schemas.brother.info/ptouch/2007/lbx/meta}properties", nsmap=nsmap)

        # Add metadata elements
        app_name = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}appName")
        app_name.text = "com.brother.PtouchEditor"

        title = etree.SubElement(root, "{http://purl.org/dc/elements/1.1/}title")
        title.text = ""

        subject = etree.SubElement(root, "{http://purl.org/dc/elements/1.1/}subject")
        subject.text = ""

        creator = etree.SubElement(root, "{http://purl.org/dc/elements/1.1/}creator")
        creator.text = ""

        keyword = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}keyword")
        keyword.text = ""

        description = etree.SubElement(root, "{http://purl.org/dc/elements/1.1/}description")
        description.text = ""

        template = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}template")
        template.text = ""

        created = etree.SubElement(root, "{http://purl.org/dc/terms/}created")
        created.text = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        modified = etree.SubElement(root, "{http://purl.org/dc/terms/}modified")
        modified.text = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        last_printed = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}lastPrinted")
        last_printed.text = ""

        modified_by = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}modifiedBy")
        modified_by.text = ""

        revision = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}revision")
        revision.text = "1"

        edit_time = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}editTime")
        edit_time.text = "0"

        num_pages = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}numPages")
        num_pages.text = "1"

        num_words = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}numWords")
        num_words.text = "0"

        num_chars = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}numChars")
        num_chars.text = "0"

        security = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}security")
        security.text = "0"

        transfer_script = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/meta}transferScript")
        transfer_script.text = ""

        # Create ElementTree
        tree = etree.ElementTree(root)
        return tree

    def generate_lbx(self, output_path: str) -> None:
        """Generate the LBX file with all configured elements."""
        self.temp_dir = tempfile.mkdtemp()

        # Create and save label.xml
        label_xml_tree = self.create_label_xml()
        self.xml_path = os.path.join(self.temp_dir, "label.xml")

        # Convert to string
        xml_str = etree.tostring(label_xml_tree, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")

        # Handle text content for data elements
        xml_str = re.sub(r'<pt:data _text_content="([^"]*?)"/>', r'<pt:data>\1</pt:data>', xml_str)

        # Minify the XML while preserving the XML declaration
        xml_lines = xml_str.splitlines()
        xml_declaration = xml_lines[0] if xml_lines and xml_lines[0].startswith('<?xml') else '<?xml version="1.0" encoding="UTF-8"?>'

        # Join the rest of the XML and remove extra whitespace
        xml_body = "".join(xml_lines[1:])

        # Extract all pt:data and other content tags to preserve their whitespace
        content_tags = {}
        tag_counter = 0

        # Store content in pt:data tags
        for match in re.finditer(r'<pt:data>(.*?)</pt:data>', xml_body):
            placeholder = f"__CONTENT_PLACEHOLDER_{tag_counter}__"
            content_tags[placeholder] = match.group(1)
            xml_body = xml_body.replace(match.group(0), f'<pt:data>{placeholder}</pt:data>')
            tag_counter += 1

        # Minify the XML body
        xml_body = re.sub(r'>\s+<', '><', xml_body)
        xml_body = re.sub(r'\s+', ' ', xml_body)
        xml_body = re.sub(r'> <', '><', xml_body)

        # Restore the content of the data tags
        for placeholder, content in content_tags.items():
            xml_body = xml_body.replace(placeholder, content)

        # Combine XML declaration with minified body
        minified_xml = xml_declaration + '\n' + xml_body

        # Write the XML to file
        with open(self.xml_path, 'w', encoding='utf-8') as f:
            f.write(minified_xml)

        # Create and save prop.xml
        prop_xml_tree = self.create_prop_xml()
        self.prop_xml_path = os.path.join(self.temp_dir, "prop.xml")

        # Convert prop.xml to string and minify
        prop_xml_str = etree.tostring(prop_xml_tree, encoding="utf-8", xml_declaration=True, pretty_print=True).decode("utf-8")
        prop_xml_lines = prop_xml_str.splitlines()
        prop_xml_declaration = prop_xml_lines[0] if prop_xml_lines and prop_xml_lines[0].startswith('<?xml') else '<?xml version="1.0" encoding="UTF-8"?>'
        prop_xml_body = "".join(prop_xml_lines[1:])

        # Minify the prop.xml body
        prop_xml_body = re.sub(r'>\s+<', '><', prop_xml_body)
        prop_xml_body = re.sub(r'\s+', ' ', prop_xml_body)
        prop_xml_body = re.sub(r'> <', '><', prop_xml_body)

        # Combine XML declaration with minified body
        minified_prop_xml = prop_xml_declaration + '\n' + prop_xml_body

        # Write the prop.xml to file
        with open(self.prop_xml_path, 'w', encoding='utf-8') as f:
            f.write(minified_prop_xml)

        # Process images
        image_files = []
        for obj in self.config.objects:
            if isinstance(obj, ImageObject):
                image_obj = obj
                if os.path.exists(image_obj.file_path):
                    if image_obj.needs_conversion:
                        try:
                            # Use PIL to convert the image
                            from PIL import Image

                            # Create the destination file path in the temp directory
                            dest_path = os.path.join(self.temp_dir, image_obj.dest_filename)

                            # Open and convert the image
                            img = Image.open(image_obj.file_path)

                            # Convert to RGB mode if needed
                            if img.mode in ('RGBA', 'LA'):
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                background.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else img.split()[1])
                                img = background
                            elif img.mode != 'RGB':
                                img = img.convert('RGB')

                            # Convert to monochrome if needed
                            if image_obj.monochrome:
                                img = img.convert('L').convert('1')

                            # Save as BMP
                            img.save(dest_path, "BMP")

                            # Add to the list of image files to include in the ZIP
                            image_files.append((dest_path, image_obj.dest_filename))
                            console.print(f"Converted {image_obj.file_path} to BMP format: {image_obj.dest_filename}")
                        except Exception as e:
                            console.print(f"[bold red]Error converting image {image_obj.file_path}: {str(e)}[/bold red]")
                    else:
                        # No conversion needed, just copy the file
                        dest_path = os.path.join(self.temp_dir, image_obj.dest_filename)
                        shutil.copy2(image_obj.file_path, dest_path)
                        image_files.append((dest_path, image_obj.dest_filename))
                        console.print(f"Using original image format for {image_obj.file_path}")
                else:
                    console.print(f"[bold yellow]Warning: Image file not found: {image_obj.file_path}[/bold yellow]")

        # Create ZIP file (LBX)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with zipfile.ZipFile(output_path, "w") as zipf:
            # Add label.xml
            zipf.write(self.xml_path, "label.xml")

            # Add prop.xml
            zipf.write(self.prop_xml_path, "prop.xml")

            # Add image files
            for file_path, file_name in image_files:
                zipf.write(file_path, file_name)

        console.print(f"[green]Created LBX file: {output_path}[/green]")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None