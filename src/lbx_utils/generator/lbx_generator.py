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

from ..models import LabelConfig, TextObject, ImageObject, GroupObject
from ..utils import LABEL_SIZES, DEFAULT_PRINTER_ID, DEFAULT_PRINTER_NAME

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
            # Convert width to points if it's in mm
            width_value = self.config.width
            if isinstance(width_value, str) and width_value.endswith('mm'):
                width_pt = float(width_value.replace('mm', '')) * 2.83
                paper_height = f"{width_pt}pt"
            elif isinstance(width_value, (int, float)) or (isinstance(width_value, str) and width_value.isdigit()):
                # If numeric, assume it's already in points
                paper_height = f"{width_value}pt"

        paper.set("height", paper_height)
        paper.set("marginLeft", size_config["marginLeft"])
        paper.set("marginTop", "5.6pt")
        paper.set("marginRight", size_config["marginRight"])
        paper.set("marginBottom", "5.6pt")
        paper.set("orientation", self.config.orientation)
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
        # console.print(f"[blue]Calculated background width: {background_width}[/blue]")

        # Add background element
        background = etree.SubElement(sheet, "{http://schemas.brother.info/ptouch/2007/lbx/style}backGround")
        background.set("x", "5.6pt") # Reverting x to hardcoded value based on reference
        background.set("y", size_config["background_y"])
        background.set("width", background_width)
        background.set("height", size_config["background_height"])
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

        # Create ElementTree
        tree = etree.ElementTree(root)
        return tree

    def _add_text_object(self, parent, text_obj: TextObject):
        """Add a text object to the parent element."""
        # Create text element
        text_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/text}text")

        # Get label size configuration
        size_config = LABEL_SIZES[self.config.size_mm]

        # Debug info - print original coordinates without any adjustment
        console.print(f"[blue]Text object positioning: x={text_obj.x}, y={text_obj.y}[/blue]")
        console.print(f"[blue]Text object dimensions: width={text_obj.width}, height={text_obj.height}[/blue]")

        # Add object style with exact coordinates as specified by the user
        # P-Touch Editor handles margin offsets internally
        obj_style = etree.SubElement(text_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")
        obj_style.set("x", text_obj.x)
        obj_style.set("y", text_obj.y)

        # Always set width and height attributes. Use defaults if not specified.
        # Omitting them caused unpredictable positioning shifts.
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
        expanded.set("objectName", f"Text{uuid.uuid4().hex[:4]}")
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

    def _add_image_object(self, parent, image_obj: ImageObject):
        """Add an image object to the parent element."""
        image_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/image}image")

        # Get label size configuration
        size_config = LABEL_SIZES[self.config.size_mm]

        # Debug info - print original coordinates without any adjustment
        console.print(f"[blue]Image object positioning: x={image_obj.x}, y={image_obj.y}[/blue]")

        # Create object style with exact coordinates as specified by the user
        # P-Touch Editor handles margin offsets internally
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

        # Create pen
        pen = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}pen")
        pen.set("style", "NULL")
        pen.set("widthX", "0.5pt")
        pen.set("widthY", "0.5pt")
        pen.set("color", "#000000")
        pen.set("printColorNumber", "1")

        # Create brush
        brush = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}brush")
        brush.set("style", "NULL")
        brush.set("color", "#000000")
        brush.set("printColorNumber", "1")
        brush.set("id", "0")

        # Create expanded info
        expanded = etree.SubElement(obj_style, "{http://schemas.brother.info/ptouch/2007/lbx/main}expanded")
        expanded.set("objectName", f"Bitmap{uuid.uuid4().hex[:4]}")
        expanded.set("ID", "0")
        expanded.set("lock", "2")
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

        # Create image style
        image_style = etree.SubElement(image_elem, "{http://schemas.brother.info/ptouch/2007/lbx/image}imageStyle")
        image_style.set("originalName", original_image_path)
        image_style.set("alignInText", "NONE")
        image_style.set("firstMerge", "true")
        image_style.set("IpName", "")
        image_style.set("fileName", dest_filename)

        # Add transparent element
        transparent = etree.SubElement(image_style, "{http://schemas.brother.info/ptouch/2007/lbx/image}transparent")
        transparent.set("flag", "true" if image_obj.transparency else "false")
        transparent.set("color", image_obj.transparency_color)

        # Add trimming element
        trimming = etree.SubElement(image_style, "{http://schemas.brother.info/ptouch/2007/lbx/image}trimming")
        trimming.set("flag", "false")
        trimming.set("shape", "RECTANGLE")
        trimming.set("trimOrgX", "0pt")
        trimming.set("trimOrgY", "0pt")
        trimming.set("trimOrgWidth", "0pt")
        trimming.set("trimOrgHeight", "0pt")

        # Add original position element
        org_pos = etree.SubElement(image_style, "{http://schemas.brother.info/ptouch/2007/lbx/image}orgPos")
        org_pos.set("x", image_obj.x)
        org_pos.set("y", image_obj.y)
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

    def _add_group_object(self, parent, group_obj: GroupObject):
        """Add a group object to the parent element."""
        # Create group element
        group_elem = etree.SubElement(parent, "{http://schemas.brother.info/ptouch/2007/lbx/main}group")

        # Add object style
        obj_style = etree.SubElement(group_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objectStyle")
        obj_style.set("x", group_obj.x)
        obj_style.set("y", group_obj.y)
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
        if group_obj.id:
            obj_name = f"Group_{group_obj.id}"
        expanded.set("objectName", obj_name)
        expanded.set("ID", "0")
        expanded.set("lock", "2")  # 2 seems to be used for groups
        expanded.set("templateMergeTarget", "LABELLIST")
        expanded.set("templateMergeType", "NONE")
        expanded.set("templateMergeID", "0")
        expanded.set("linkStatus", "NONE")
        expanded.set("linkID", "0")

        # Add objects container for child objects
        objects_elem = etree.SubElement(group_elem, "{http://schemas.brother.info/ptouch/2007/lbx/main}objects")

        # Process each child object
        for child_obj in group_obj.objects:
            if isinstance(child_obj, TextObject):
                self._add_text_object(objects_elem, child_obj)
            elif isinstance(child_obj, ImageObject):
                self._add_image_object(objects_elem, child_obj)
            elif isinstance(child_obj, GroupObject):
                # Support nested groups
                self._add_group_object(objects_elem, child_obj)

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