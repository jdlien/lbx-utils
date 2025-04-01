#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
lbx-create.py - Create Brother P-Touch LBX labels with text and images

This script generates Brother P-Touch LBX labels with configurable text and images.
It creates label files that are compatible with Brother P-Touch Editor software.
"""

import os
import sys
import io
import re
import uuid
import datetime
import zipfile
import tempfile
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
import xml.etree.ElementTree as ET
from lxml import etree
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rich_print
import colorama
from colorama import Fore, Style

# Initialize colorama for cross-platform color support
colorama.init()

# Create console for rich output
console = Console()

# Create the typer app
app = typer.Typer(help="Create Brother P-Touch LBX label files")

# XML namespaces used in LBX files
NAMESPACES = {
    'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
    'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
    'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
    'draw': 'http://schemas.brother.info/ptouch/2007/lbx/draw',
    'image': 'http://schemas.brother.info/ptouch/2007/lbx/image',
    'barcode': 'http://schemas.brother.info/ptouch/2007/lbx/barcode',
    'database': 'http://schemas.brother.info/ptouch/2007/lbx/database',
    'table': 'http://schemas.brother.info/ptouch/2007/lbx/table',
    'cable': 'http://schemas.brother.info/ptouch/2007/lbx/cable',
    'meta': 'http://schemas.brother.info/ptouch/2007/lbx/meta',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/'
}

# Register all namespaces for proper XML output
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

# Label size configurations based on tape width
LABEL_SIZES = {
    9: {
        'width': '25.6pt',
        'marginLeft': '2.8pt',
        'marginRight': '2.8pt',
        'format': '258',
        'background_y': '2.8pt',
        'background_height': '20pt',
        'text_object_y': '7.1pt',
        'image_object_y': '2.8pt'
    },
    12: {
        'width': '33.6pt',
        'marginLeft': '2.8pt',
        'marginRight': '2.8pt',
        'format': '259',
        'background_y': '2.8pt',
        'background_height': '28pt',
        'text_object_y': '7.1pt',
        'image_object_y': '2.8pt'
    },
    18: {
        'width': '51.2pt',
        'marginLeft': '3.2pt',
        'marginRight': '3.2pt',
        'format': '260',
        'background_y': '3.2pt',
        'background_height': '44.8pt',
        'text_object_y': '7.5pt',
        'image_object_y': '3.2pt'
    },
    24: {
        'width': '68pt',
        'marginLeft': '8.4pt',
        'marginRight': '8.4pt',
        'format': '261',
        'background_y': '8.4pt',
        'background_height': '51.2pt',
        'text_object_y': '12.7pt',
        'image_object_y': '8.4pt'
    }
}

# Default values
DEFAULT_FONT = "Arial"
DEFAULT_FONT_SIZE = "12pt"
DEFAULT_FONT_WEIGHT = "400"  # Normal weight
DEFAULT_FONT_ITALIC = "false"
DEFAULT_ORIENTATION = "landscape"
DEFAULT_PRINTER_ID = "30256"  # Brother PT-P710BT
DEFAULT_PRINTER_NAME = "Brother PT-P710BT"

@dataclass
class FontInfo:
    """Font information for a text object."""
    name: str = DEFAULT_FONT
    size: str = DEFAULT_FONT_SIZE
    weight: str = DEFAULT_FONT_WEIGHT
    italic: str = DEFAULT_FONT_ITALIC
    color: str = "#000000"
    print_color_number: str = "1"

    @property
    def org_size(self) -> str:
        """Calculate the original size (3.6x the font size)."""
        size_value = float(self.size.replace('pt', ''))
        return f"{size_value * 3.6}pt"

@dataclass
class StringItem:
    """String item within a text object."""
    char_len: int
    font_info: FontInfo
    start_pos: int = 0

@dataclass
class TextObject:
    """Represents a text object on the label."""
    text: str
    x: str
    y: str
    width: str
    height: str
    font_info: FontInfo = field(default_factory=FontInfo)
    string_items: List[StringItem] = field(default_factory=list)

    def __post_init__(self):
        """Initialize string items if not provided."""
        if not self.string_items:
            self.string_items = [StringItem(char_len=len(self.text), font_info=self.font_info)]

@dataclass
class ImageObject:
    """Represents an image object on the label."""
    file_path: str
    x: str
    y: str
    width: str
    height: str

@dataclass
class LabelConfig:
    """Configuration for a label."""
    size_mm: int = 24
    auto_length: bool = True
    orientation: str = DEFAULT_ORIENTATION
    height: str = "2834.4pt"  # Default height for auto-length
    printer_id: str = DEFAULT_PRINTER_ID
    printer_name: str = DEFAULT_PRINTER_NAME
    text_objects: List[TextObject] = field(default_factory=list)
    image_objects: List[ImageObject] = field(default_factory=list)

class LBXCreator:
    """Creates Brother P-Touch LBX label files with text and images."""

    def __init__(self, config: LabelConfig):
        """Initialize the LBX creator with a label configuration."""
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
                             attrib={"version": "1.9", "generator": "lbx-utils"},
                             nsmap=nsmap)

        # Add body element
        body = etree.SubElement(root, "{http://schemas.brother.info/ptouch/2007/lbx/main}body")
        body.set("currentSheet", "Sheet 1")
        body.set("direction", "LTR")

        # Add sheet element
        sheet = etree.SubElement(body, "{http://schemas.brother.info/ptouch/2007/lbx/style}sheet")
        sheet.set("name", "Sheet 1")

        # Add paper element with size-specific attributes
        size_config = LABEL_SIZES[self.config.size_mm]
        paper = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/style}paper")
        paper.set("media", "0")
        paper.set("width", size_config["width"])
        paper.set("height", self.config.height)
        paper.set("marginLeft", size_config["marginLeft"])
        paper.set("marginTop", "5.6pt")
        paper.set("marginRight", size_config["marginRight"])
        paper.set("marginBottom", "5.6pt")
        paper.set("orientation", self.config.orientation)
        paper.set("autoLength", str(self.config.auto_length).lower())
        paper.set("monochromeDisplay", "true")
        paper.set("printColorDisplay", "false")
        paper.set("printColorsID", "0")
        paper.set("paperColor", "#FFFFFF")
        paper.set("paperInk", "#000000")
        paper.set("split", "1")
        paper.set("format", size_config["format"])
        paper.set("backgroundTheme", "0")
        paper.set("printerID", self.config.printer_id)
        paper.set("printerName", self.config.printer_name)

        # Add cut line element
        cut_line = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/style}cutLine")
        cut_line.set("regularCut", "0pt")
        cut_line.set("freeCut", "")

        # Add background element
        background = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/style}backGround")
        background.set("x", "5.6pt")
        background.set("y", size_config["background_y"])
        background.set("width", "66.4pt")  # Fixed value for all sizes
        background.set("height", size_config["background_height"])
        background.set("brushStyle", "NULL")
        background.set("brushId", "0")
        background.set("userPattern", "NONE")
        background.set("userPatternId", "0")
        background.set("color", "#000000")
        background.set("printColorNumber", "1")
        background.set("backColor", "#FFFFFF")
        background.set("backPrintColorNumber", "0")

        # Add objects container
        objects = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/main}objects")

        # Add text objects
        for text_obj in self.config.text_objects:
            self._add_text_object(objects, text_obj)

        # Add image objects
        for image_obj in self.config.image_objects:
            self._add_image_object(objects, image_obj)

        # Create ElementTree
        tree = etree.ElementTree(root)
        return tree

    def _add_text_object(self, parent, text_obj: TextObject):
        """Add a text object to the parent element."""
        # Create text element
        text_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/text}text")

        # Add object style
        obj_style = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")
        obj_style.set("x", text_obj.x)
        obj_style.set("y", text_obj.y)
        obj_style.set("width", text_obj.width)
        obj_style.set("height", text_obj.height)
        obj_style.set("backColor", "#FFFFFF")
        obj_style.set("backPrintColorNumber", "0")
        obj_style.set("ropMode", "COPYPEN")
        obj_style.set("angle", "0")
        obj_style.set("anchor", "TOPLEFT")
        obj_style.set("flip", "NONE")

        # Add pen
        pen = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}pen")
        pen.set("style", "NULL")
        pen.set("widthX", "1pt")
        pen.set("widthY", "1pt")
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
        expanded.set("objectName", f'Text{uuid.uuid4().hex[:6]}')
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
        log_font.set("pitchAndFamily", "34")

        # Add font extension
        font_ext = etree.SubElement(font_info_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt")
        font_ext.set("effect", "NOEFFECT")
        font_ext.set("underline", "0")
        font_ext.set("strikeout", "0")
        font_ext.set("size", text_obj.font_info.size)
        font_ext.set("orgSize", text_obj.font_info.org_size)
        font_ext.set("textColor", text_obj.font_info.color)
        font_ext.set("textPrintColorNumber", text_obj.font_info.print_color_number)

        # Add text control
        text_control = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}textControl")
        text_control.set("control", "FREE")
        text_control.set("clipFrame", "false")
        text_control.set("aspectNormal", "true")
        text_control.set("shrink", "true")
        text_control.set("autoLF", "true")
        text_control.set("avoidImage", "false")

        # Add text alignment
        text_align = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}textAlign")
        text_align.set("horizontalAlignment", "LEFT")
        text_align.set("verticalAlignment", "CENTER")
        text_align.set("inLineAlignment", "BASELINE")

        # Add text style
        text_style = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/text}textStyle")
        text_style.set("vertical", "false")
        text_style.set("nullBlock", "false")
        text_style.set("charSpace", "0")
        text_style.set("lineSpace", "0")
        text_style.set("orgPoint", text_obj.font_info.size)
        text_style.set("combinedChars", "false")

        # Add data (text content)
        data = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}data")
        data.text = text_obj.text

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
            item_log_font.set("pitchAndFamily", "34")

            # Add font extension for string item
            item_font_ext = etree.SubElement(item_font_info, "{http://schemas.brother.info/ptouch/2007/lbx/text}fontExt")
            item_font_ext.set("effect", "NOEFFECT")
            item_font_ext.set("underline", "0")
            item_font_ext.set("strikeout", "0")
            item_font_ext.set("size", item.font_info.size)
            item_font_ext.set("orgSize", item.font_info.org_size)
            item_font_ext.set("textColor", item.font_info.color)
            item_font_ext.set("textPrintColorNumber", item.font_info.print_color_number)

        return text_elem

    def _add_image_object(self, parent, image_obj: ImageObject):
        """Add an image object to the parent element."""
        # Create image element
        image_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/image}image")

        # Add object style
        obj_style = etree.SubElement(image_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")
        obj_style.set("x", image_obj.x)
        obj_style.set("y", image_obj.y)
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
        pen.set("widthX", "1pt")
        pen.set("widthY", "1pt")
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
        expanded.set("objectName", f'Image{uuid.uuid4().hex[:6]}')
        expanded.set("ID", "0")
        expanded.set("lock", "0")
        expanded.set("templateMergeTarget", "LABELLIST")
        expanded.set("templateMergeType", "NONE")
        expanded.set("templateMergeID", "0")
        expanded.set("linkStatus", "NONE")
        expanded.set("linkID", "0")

        # Add image style
        image_style = etree.SubElement(image_elem, "{http://schemas.brother.info/ptouch/2007/lbx/image}imageStyle")
        image_style.set("originalSize", "true")
        image_style.set("dither", "true")
        image_style.set("monochrome", "true")
        image_style.set("rotation", "0")
        image_style.set("brightness", "0")
        image_style.set("contrast", "0")
        image_style.set("threshold", "0")
        image_style.set("transparent", "false")
        image_style.set("transparentColor", "#FFFFFF")

        # Add image data reference
        image_path = os.path.basename(image_obj.file_path)
        image_data = etree.SubElement(image_elem, "{http://schemas.brother.info/ptouch/2007/lbx/image}imageData")
        image_data.set("originalName", image_path)
        image_data.text = image_path

        return image_elem

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
        app_name.text = "lbx-utils"

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

    def create_lbx(self, output_path: str) -> None:
        """Create the LBX file with the configured elements."""
        self.temp_dir = tempfile.mkdtemp()

        # Create and save label.xml
        label_xml_tree = self.create_label_xml()
        self.xml_path = os.path.join(self.temp_dir, "label.xml")
        label_xml_tree.write(self.xml_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

        # Create and save prop.xml
        prop_xml_tree = self.create_prop_xml()
        self.prop_xml_path = os.path.join(self.temp_dir, "prop.xml")
        prop_xml_tree.write(self.prop_xml_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

        # Create ZIP file (LBX)
        with zipfile.ZipFile(output_path, "w") as zipf:
            # Add label.xml
            zipf.write(self.xml_path, "label.xml")

            # Add prop.xml
            zipf.write(self.prop_xml_path, "prop.xml")

            # Add image files
            for image_obj in self.config.image_objects:
                if os.path.exists(image_obj.file_path):
                    zipf.write(image_obj.file_path, os.path.basename(image_obj.file_path))

        console.print(f"[green]Created LBX file: {output_path}[/green]")

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

def create_default_text_object(text: str, font_name: str = DEFAULT_FONT, font_size: str = DEFAULT_FONT_SIZE,
                              font_weight: str = DEFAULT_FONT_WEIGHT, font_italic: str = DEFAULT_FONT_ITALIC,
                              x: str = "10pt", y: str = None, width: str = "120pt", height: str = "20pt") -> TextObject:
    """Create a default text object with the specified parameters."""
    # Create font info
    if not font_size.endswith('pt'):
        font_size = f"{font_size}pt"

    font_info = FontInfo(
        name=font_name,
        size=font_size,
        weight=font_weight,
        italic=font_italic
    )

    # Create text object
    text_obj = TextObject(
        text=text,
        x=x,
        y=y if y else "7.1pt",  # Will be updated later based on label size
        width=width,
        height=height,
        font_info=font_info
    )

    return text_obj

def create_image_object(file_path: str, x: str = "10pt", y: str = None,
                        width: str = "20pt", height: str = "20pt") -> ImageObject:
    """Create an image object with the specified parameters."""
    image_obj = ImageObject(
        file_path=file_path,
        x=x,
        y=y if y else "2.8pt",  # Will be updated later based on label size
        width=width,
        height=height
    )

    return image_obj

def calculate_layout(config: LabelConfig) -> None:
    """Calculate the layout of elements on the label."""
    # Get label size configuration
    size_config = LABEL_SIZES[config.size_mm]

    # Set y-positions for objects based on label size
    for text_obj in config.text_objects:
        text_obj.y = size_config['text_object_y']

    for image_obj in config.image_objects:
        image_obj.y = size_config['image_object_y']

    # If we have both images and text, position text to the right of images
    if config.image_objects and config.text_objects:
        # Find the rightmost edge of all images
        max_image_right = 0
        for image_obj in config.image_objects:
            image_right = float(image_obj.x.replace('pt', '')) + float(image_obj.width.replace('pt', ''))
            max_image_right = max(max_image_right, image_right)

        # Position text objects to the right of images with a margin
        margin = 5  # 5pt margin
        for text_obj in config.text_objects:
            text_obj.x = f"{max_image_right + margin}pt"

    # Center all elements vertically
    if config.text_objects or config.image_objects:
        # Calculate available height
        available_height = float(size_config['background_height'].replace('pt', ''))

        # Calculate total height of all objects
        total_height = 0
        for text_obj in config.text_objects:
            total_height += float(text_obj.height.replace('pt', ''))

        for image_obj in config.image_objects:
            total_height += float(image_obj.height.replace('pt', ''))

        # Calculate vertical spacing
        if len(config.text_objects) + len(config.image_objects) > 1:
            spacing = 5  # 5pt spacing between elements
            total_height += spacing * (len(config.text_objects) + len(config.image_objects) - 1)
        else:
            spacing = 0

        # Calculate starting y-position to center all elements
        start_y = float(size_config['background_y'].replace('pt', '')) + (available_height - total_height) / 2

        # Position elements vertically
        current_y = start_y

        # Position image objects first
        for image_obj in config.image_objects:
            image_obj.y = f"{current_y}pt"
            current_y += float(image_obj.height.replace('pt', '')) + spacing

        # Position text objects next
        for text_obj in config.text_objects:
            text_obj.y = f"{current_y}pt"
            current_y += float(text_obj.height.replace('pt', '')) + spacing

def validate_input(text: Optional[List[str]], images: Optional[List[str]]) -> bool:
    """Validate input parameters and display errors if any."""
    if not text and not images:
        console.print("[bold red]Error: At least one text or image must be specified[/bold red]")
        return False

    if images:
        for image_path in images:
            if not os.path.exists(image_path):
                console.print(f"[bold red]Error: Image file not found: {image_path}[/bold red]")
                return False

    return True

def print_label_info(config: LabelConfig) -> None:
    """Print information about the label."""
    table = Table(title=f"Label ({config.size_mm}mm)")

    table.add_column("Type", style="cyan")
    table.add_column("Content", style="green")
    table.add_column("Position", style="yellow")
    table.add_column("Size", style="magenta")

    for i, text_obj in enumerate(config.text_objects):
        table.add_row(
            f"Text {i+1}",
            text_obj.text[:30] + ("..." if len(text_obj.text) > 30 else ""),
            f"({text_obj.x}, {text_obj.y})",
            f"{text_obj.width} × {text_obj.height}"
        )

    for i, image_obj in enumerate(config.image_objects):
        table.add_row(
            f"Image {i+1}",
            os.path.basename(image_obj.file_path),
            f"({image_obj.x}, {image_obj.y})",
            f"{image_obj.width} × {image_obj.height}"
        )

    console.print(table)

@app.command()
def create(
    output: str = typer.Option(..., "--output", "-o", help="Output LBX file path"),
    size: int = typer.Option(24, "--size", "-s", help="Label size in mm (9, 12, 18, or 24)"),
    text: Optional[List[str]] = typer.Option(None, "--text", "-t", help="Text to add to the label (can be specified multiple times)"),
    font: str = typer.Option(DEFAULT_FONT, "--font", "-f", help="Font name for text"),
    font_size: str = typer.Option(DEFAULT_FONT_SIZE, "--font-size", "-fs", help="Font size (e.g., '12pt')"),
    bold: bool = typer.Option(False, "--bold", "-b", help="Use bold font"),
    italic: bool = typer.Option(False, "--italic", "-i", help="Use italic font"),
    images: Optional[List[str]] = typer.Option(None, "--image", "-img", help="Path to image file (can be specified multiple times)"),
    width: Optional[str] = typer.Option(None, "--width", "-w", help="Width of the label (auto by default)"),
    height: Optional[str] = typer.Option(None, "--height", "-h", help="Height of the label (auto by default)"),
    auto_length: bool = typer.Option(True, "--auto-length", "-a", help="Automatically adjust label length based on content")
) -> None:
    """Create a Brother P-Touch LBX label."""
    # Validate size
    if size not in LABEL_SIZES:
        console.print(f"[bold red]Error: Invalid label size. Must be one of: {list(LABEL_SIZES.keys())}[/bold red]")
        raise typer.Exit(1)

    # Validate input
    if not validate_input(text, images):
        raise typer.Exit(1)

    # Create label configuration
    config = LabelConfig(
        size_mm=size,
        auto_length=auto_length
    )

    # Set custom height if provided
    if height:
        config.height = height if height.endswith('pt') else f"{height}pt"
        config.auto_length = False

    # Add text objects
    if text:
        font_weight = "700" if bold else "400"
        font_italic = "true" if italic else "false"

        for t in text:
            text_obj = create_default_text_object(
                text=t,
                font_name=font,
                font_size=font_size,
                font_weight=font_weight,
                font_italic=font_italic
            )
            config.text_objects.append(text_obj)

    # Add image objects
    if images:
        for img_path in images:
            image_obj = create_image_object(file_path=img_path)
            config.image_objects.append(image_obj)

    # Calculate layout
    calculate_layout(config)

    # Print label information
    print_label_info(config)

    # Create LBX file
    creator = LBXCreator(config)

    try:
        creator.create_lbx(output)
        console.print(f"\n[bold green]LBX file created successfully: {output}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error creating LBX file: {str(e)}[/bold red]")
        raise typer.Exit(1)
    finally:
        creator.cleanup()

def display_help() -> None:
    """Display help information with examples."""
    console.print(Panel(
        "[bold cyan]lbx-create.py[/bold cyan] - Create Brother P-Touch LBX label files\n\n"
        "This tool creates Brother P-Touch LBX label files with text and images that can be"
        "opened directly in Brother P-Touch Editor software.\n\n"
        "[bold yellow]Key Features:[/bold yellow]\n"
        "- Add text with customizable font, size, and style\n"
        "- Add images from specified files\n"
        "- Automatically position text to the right of images\n"
        "- Automatically center all elements vertically\n"
        "- Configure label size (9mm, 12mm, 18mm, 24mm)\n\n"
        "[bold yellow]Examples:[/bold yellow]\n\n"
        "[green]Create a basic text label:[/green]\n"
        "  python lbx-create.py --output mylabel.lbx --text \"Hello World\"\n\n"
        "[green]Create a label with multiple text elements:[/green]\n"
        "  python lbx-create.py --output mylabel.lbx --text \"Line 1\" --text \"Line 2\"\n\n"
        "[green]Create a label with an image:[/green]\n"
        "  python lbx-create.py --output mylabel.lbx --image logo.png\n\n"
        "[green]Create a label with text and image:[/green]\n"
        "  python lbx-create.py --output mylabel.lbx --image logo.png --text \"Company Name\"\n\n"
        "[green]Create a label with custom text formatting:[/green]\n"
        "  python lbx-create.py --output mylabel.lbx --text \"Bold Text\" --bold --font \"Arial\" --font-size 14\n\n"
        "[green]Create a label with a specific size:[/green]\n"
        "  python lbx-create.py --output mylabel.lbx --text \"12mm Label\" --size 12\n",
        title="Help & Examples",
        border_style="blue"
    ))

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Brother P-Touch LBX Label Creator."""
    # Display help if no command is specified
    if ctx.invoked_subcommand is None:
        display_help()

if __name__ == "__main__":
    app()
