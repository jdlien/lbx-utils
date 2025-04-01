#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LBX Text Editor - A tool for manipulating text in Brother P-touch LBX label files.
This utility focuses on managing text objects in label.xml files, handling character
length tracking automatically when modifications are made.

Features:
- Extract and parse text objects from label.xml files
- Edit text content while automatically updating charLen attributes
- Delete, split, and merge string items with proper character tracking
- Find and replace text across all text objects
- Regular expression-based find and replace

Usage examples:
- Regular find/replace: lbx_text_edit.py replace input.lbx -f "2x2" -r "2×2"
- Regex find/replace: lbx_text_edit.py replace input.lbx -f "(\d+)x(\d+)" -r "\1×\2" --regex
  This example converts "2x4" to "2×4" by capturing digit groups and using the multiplication symbol
- Regex to add suffix: lbx_text_edit.py replace input.lbx -f "^(.*)$" -r "\1 Brick" --regex
  This adds " Brick" to the end of each text object
- Regex to format part numbers: lbx_text_edit.py replace input.lbx -f "(\d{4})(\d)?" -r "Part #\1-\2" --regex
  This formats numbers like "30182" to "Part #3018-2"

The program can be used as a library in other scripts or as a command-line tool.

CRITICAL NOTES ABOUT THE BROTHER P-TOUCH LBX FORMAT:
1. Each text:text element MUST have one or more text:stringItem elements after pt:data
2. Each stringItem needs charLen attribute that matches the length of its text segment
3. The sum of all charLen values must equal the length of the text in pt:data
4. All stringItems must be preserved with proper font info when editing
5. The order of XML elements matters and must be preserved exactly
"""

import os
import re
import shutil
import zipfile
import tempfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple, Optional, Union, Any
from dataclasses import dataclass, field


# Define the XML namespaces used in label.xml files
NAMESPACES = {
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


# Register all namespaces for proper XML output
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)


@dataclass
class FontInfo:
    """Represents font information for a string item."""
    name: str = "Arial"
    width: int = 0
    italic: bool = False
    weight: int = 400  # 400=normal, 700=bold
    char_set: int = 0
    pitch_and_family: str = "34"
    effect: str = "NOEFFECT"
    underline: int = 0
    strikeout: int = 0
    size: str = "8pt"
    org_size: str = "28.8pt"
    text_color: str = "#000000"
    text_print_color_number: str = "1"


@dataclass
class StringItem:
    """
    Represents a text:stringItem element with its character length and font info.

    CRITICAL: In the Brother P-Touch format, each segment of text must have a
    corresponding stringItem with a charLen attribute matching the length of that segment.
    """
    char_len: int
    font_info: FontInfo
    start_pos: int = 0  # Position in the original string

    @classmethod
    def from_element(cls, element: ET.Element, start_pos: int = 0) -> 'StringItem':
        """
        Create a StringItem from an XML element.

        Args:
            element: The XML element (text:stringItem)
            start_pos: The starting position of this segment in the text

        Returns:
            A StringItem object with parsed font information
        """
        char_len = int(element.get('charLen', '0'))

        # Parse font info
        font_info = FontInfo()
        font_elem = element.find('.//text:logFont', NAMESPACES)
        if font_elem is not None:
            font_info.name = font_elem.get('name', font_info.name)
            font_info.width = int(font_elem.get('width', '0'))
            font_info.italic = font_elem.get('italic', 'false').lower() == 'true'
            font_info.weight = int(font_elem.get('weight', '400'))
            font_info.char_set = int(font_elem.get('charSet', '0'))
            font_info.pitch_and_family = font_elem.get('pitchAndFamily', font_info.pitch_and_family)

        font_ext_elem = element.find('.//text:fontExt', NAMESPACES)
        if font_ext_elem is not None:
            font_info.effect = font_ext_elem.get('effect', font_info.effect)
            font_info.underline = int(font_ext_elem.get('underline', '0'))
            font_info.strikeout = int(font_ext_elem.get('strikeout', '0'))
            font_info.size = font_ext_elem.get('size', font_info.size)
            font_info.org_size = font_ext_elem.get('orgSize', font_info.org_size)
            font_info.text_color = font_ext_elem.get('textColor', font_info.text_color)
            font_info.text_print_color_number = font_ext_elem.get('textPrintColorNumber', font_info.text_print_color_number)

        return cls(char_len=char_len, font_info=font_info, start_pos=start_pos)

    def to_element(self) -> ET.Element:
        """
        Convert the StringItem to an XML element.

        Returns:
            An XML Element representing this string item with proper font info
        """
        string_item = ET.Element(f"{{{NAMESPACES['text']}}}stringItem", {'charLen': str(self.char_len)})

        # Create font info elements
        pt_font_info = ET.SubElement(string_item, f"{{{NAMESPACES['text']}}}ptFontInfo")

        log_font = ET.SubElement(pt_font_info, f"{{{NAMESPACES['text']}}}logFont", {
            'name': self.font_info.name,
            'width': str(self.font_info.width),
            'italic': 'true' if self.font_info.italic else 'false',
            'weight': str(self.font_info.weight),
            'charSet': str(self.font_info.char_set),
            'pitchAndFamily': str(self.font_info.pitch_and_family)
        })

        font_ext = ET.SubElement(pt_font_info, f"{{{NAMESPACES['text']}}}fontExt", {
            'effect': self.font_info.effect,
            'underline': str(self.font_info.underline),
            'strikeout': str(self.font_info.strikeout),
            'size': self.font_info.size,
            'orgSize': self.font_info.org_size,
            'textColor': self.font_info.text_color,
            'textPrintColorNumber': self.font_info.text_print_color_number
        })

        return string_item


@dataclass
class TextObject:
    """
    Represents a text:text element with its contents and string items.

    CRITICAL: The Brother P-Touch format requires that:
    1. Every text object must contain one or more stringItem elements
    2. Each stringItem defines formatting for a segment of text
    3. The sum of all stringItem charLen values must equal the total length of text
    """
    text: str
    string_items: List[StringItem] = field(default_factory=list)
    element: Optional[ET.Element] = None

    @classmethod
    def from_element(cls, element: ET.Element) -> 'TextObject':
        """
        Create a TextObject from an XML element.

        Args:
            element: The XML element (text:text)

        Returns:
            A TextObject with parsed text and string items
        """
        # Extract the text content
        data_elem = element.find('.//pt:data', NAMESPACES)
        text = data_elem.text if data_elem is not None and data_elem.text else ""

        # Create the TextObject
        text_obj = cls(text=text, element=element)

        # Extract string items
        start_pos = 0
        for string_item_elem in element.findall('.//text:stringItem', NAMESPACES):
            string_item = StringItem.from_element(string_item_elem, start_pos)
            text_obj.string_items.append(string_item)
            start_pos += string_item.char_len

        # Validate that string items cover the entire text
        total_len = sum(item.char_len for item in text_obj.string_items)
        if total_len != len(text) and text_obj.string_items:
            print(f"WARNING: String items total length ({total_len}) does not match text length ({len(text)})")

        return text_obj

    def update_element(self) -> ET.Element:
        """
        Update the XML element with current text and string items.

        CRITICAL: This maintains the required structure for Brother P-Touch:
        1. Preserves all required elements in the correct order
        2. Updates the pt:data text content
        3. Replaces string items with updated ones

        Returns:
            The updated XML element
        """
        if self.element is None:
            raise ValueError("This TextObject was not created from an XML element")

        # Update the text content
        data_elem = self.element.find('.//pt:data', NAMESPACES)
        if data_elem is not None:
            data_elem.text = self.text

        # First, locate the parent element that contains string items
        # This is crucial for maintaining the correct structure
        string_items_parent = None
        string_item_elems = []

        # Find all existing string items and their parent
        if self.element is not None:
            string_item_elems = self.element.findall('.//text:stringItem', NAMESPACES)
            if string_item_elems:
                # Find the parent element
                for parent in self.element.iter():
                    for child in list(parent):
                        if child in string_item_elems:
                            string_items_parent = parent
                            break
                    if string_items_parent is not None:
                        break

        # Remove existing string items
        if string_items_parent is not None:
            for old_item in string_item_elems:
                string_items_parent.remove(old_item)

            # Add updated string items to the same parent
            for string_item in self.string_items:
                string_items_parent.append(string_item.to_element())
        else:
            # If we couldn't find the parent, try to add them after pt:data
            # This is a fallback method
            data_elem = self.element.find('.//pt:data', NAMESPACES)
            if data_elem is not None:
                # Find the parent of data_elem using a helper method
                parent = self._find_parent(self.element, data_elem)
                if parent is not None:
                    for string_item in self.string_items:
                        parent.append(string_item.to_element())
                else:
                    print("WARNING: Could not locate proper parent for string items")
            else:
                print("WARNING: Could not locate proper parent for string items")

        return self.element

    def _find_parent(self, root: ET.Element, target: ET.Element) -> Optional[ET.Element]:
        """
        Helper method to find the parent element of a given target element.

        Args:
            root: The root element to start searching from
            target: The element to find the parent of

        Returns:
            The parent element or None if not found
        """
        for parent in root.iter():
            for child in list(parent):
                if child == target:
                    return parent
        return None

    def validate(self) -> bool:
        """
        Validate that the TextObject has proper structure:
        - Has string items
        - String items' total length equals text length

        Returns:
            True if valid, False otherwise
        """
        if not self.string_items:
            print("WARNING: No string items in text object")
            return False

        total_len = sum(item.char_len for item in self.string_items)
        if total_len != len(self.text):
            print(f"WARNING: String items total length ({total_len}) does not match text length ({len(self.text)})")
            return False

        return True

    def edit_text(self, new_text: str) -> None:
        """
        Edit the text content and adjust string items accordingly.
        This maintains the same formatting distribution but adjusts the charLen values.

        CRITICAL: This preserves the stringItem structure required by Brother P-Touch
        by proportionally adjusting the charLen values.

        Args:
            new_text: The new text content
        """
        if not self.string_items:
            # If there are no string items, create a default one for the entire text
            self.text = new_text
            self.string_items = [StringItem(char_len=len(new_text), font_info=FontInfo())]
            return

        old_length = len(self.text)
        new_length = len(new_text)

        # Simple case: empty text
        if old_length == 0:
            self.text = new_text
            if self.string_items:
                self.string_items[0].char_len = new_length
                for item in self.string_items[1:]:
                    item.char_len = 0
            return

        # Calculate scaling factor for each string item
        scale_factor = new_length / old_length

        # Adjust character lengths proportionally
        total_adjusted = 0
        for i, item in enumerate(self.string_items[:-1]):  # Process all but the last item
            new_len = round(item.char_len * scale_factor)
            item.char_len = new_len
            total_adjusted += new_len

        # Assign the remainder to the last item
        if self.string_items:
            self.string_items[-1].char_len = max(0, new_length - total_adjusted)

        # Update the text
        self.text = new_text

        # Validate after editing
        self.validate()

    def find_replace(self, find_text: str, replace_text: str, case_sensitive: bool = True) -> int:
        """
        Find and replace text within the content.
        Returns the number of replacements made.

        Args:
            find_text: Text to find
            replace_text: Text to replace with
            case_sensitive: Whether the search is case-sensitive

        Returns:
            Number of replacements made
        """
        if not case_sensitive:
            pattern = re.compile(re.escape(find_text), re.IGNORECASE)
            new_text, count = pattern.subn(replace_text, self.text)
        else:
            count = self.text.count(find_text)
            new_text = self.text.replace(find_text, replace_text)

        if count > 0:
            self.edit_text(new_text)

        return count

    def regex_find_replace(self, pattern: str, replace_text: str, case_sensitive: bool = True) -> int:
        """
        Find and replace text using regular expressions.

        Args:
            pattern: Regular expression pattern to match
            replace_text: Replacement text (can include group references like \1, \2)
            case_sensitive: Whether the pattern matching should be case-sensitive

        Returns:
            Number of replacements made
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        regex = re.compile(pattern, flags)
        new_text, count = regex.subn(replace_text, self.text)

        if count > 0:
            self.edit_text(new_text)

        return count

    def split_string_item(self, item_index: int, position: int) -> None:
        """
        Split a string item at the specified position within that item.

        Args:
            item_index: Index of the string item to split
            position: Character position within the string item where the split should occur
        """
        if item_index < 0 or item_index >= len(self.string_items):
            raise IndexError(f"String item index {item_index} out of range")

        item = self.string_items[item_index]
        if position <= 0 or position >= item.char_len:
            raise ValueError(f"Position {position} out of range for string item with length {item.char_len}")

        # Create a new string item with the same font info
        new_item = StringItem(
            char_len=item.char_len - position,
            font_info=FontInfo(**vars(item.font_info)),
            start_pos=item.start_pos + position
        )

        # Update the original item's length
        item.char_len = position

        # Insert the new item after the original
        self.string_items.insert(item_index + 1, new_item)

        # Validate after splitting
        self.validate()

    def merge_string_items(self, start_index: int, end_index: int) -> None:
        """
        Merge multiple string items into a single item.

        Args:
            start_index: Index of the first string item to merge
            end_index: Index of the last string item to merge (inclusive)
        """
        if start_index < 0 or end_index >= len(self.string_items) or start_index > end_index:
            raise IndexError(f"Invalid indices: start={start_index}, end={end_index}")

        # Calculate the total character length
        total_len = sum(item.char_len for item in self.string_items[start_index:end_index+1])

        # Keep the font info of the first item
        merged_item = StringItem(
            char_len=total_len,
            font_info=FontInfo(**vars(self.string_items[start_index].font_info)),
            start_pos=self.string_items[start_index].start_pos
        )

        # Replace the range of items with the merged item
        self.string_items[start_index:end_index+1] = [merged_item]

        # Validate after merging
        self.validate()

    def delete_string_item(self, item_index: int) -> None:
        """
        Delete a string item and its corresponding text.

        Args:
            item_index: Index of the string item to delete
        """
        if item_index < 0 or item_index >= len(self.string_items):
            raise IndexError(f"String item index {item_index} out of range")

        item = self.string_items[item_index]
        start_pos = sum(si.char_len for si in self.string_items[:item_index])
        end_pos = start_pos + item.char_len

        # Remove the text
        self.text = self.text[:start_pos] + self.text[end_pos:]

        # Remove the string item
        self.string_items.pop(item_index)

        # Update the start positions of subsequent items
        for i in range(item_index, len(self.string_items)):
            self.string_items[i].start_pos -= item.char_len

        # If we deleted the last string item, create a default one
        if not self.string_items and self.text:
            self.string_items = [StringItem(char_len=len(self.text), font_info=FontInfo())]

        # Validate after deletion
        self.validate()

    def add_string_item(self, text: str, font_name: str = "Arial", font_weight: int = 400,
                       font_size: str = "8pt", position: int = -1) -> StringItem:
        """
        Add a new string item with specified text and font properties.

        Args:
            text: The text content to add
            font_name: Name of the font to use
            font_weight: Font weight (400=normal, 700=bold)
            font_size: Font size (e.g. "8pt")
            position: Position to insert the string item (-1 means append to end)

        Returns:
            The newly created StringItem
        """
        # Create font info
        font_info = FontInfo(
            name=font_name,
            weight=font_weight,
            size=font_size,
            org_size=f"{float(font_size.rstrip('pt')) * 3.6:.1f}pt"  # Convert to orgSize (3.6x font size)
        )

        # Calculate start position
        if position < 0 or position >= len(self.string_items):
            # Append to end
            start_pos = len(self.text)
            # Add the text to the end
            self.text += text
            # Create string item
            string_item = StringItem(char_len=len(text), font_info=font_info, start_pos=start_pos)
            # Add to string items
            self.string_items.append(string_item)
        else:
            # Insert at position
            start_pos = sum(si.char_len for si in self.string_items[:position])
            # Insert the text
            self.text = self.text[:start_pos] + text + self.text[start_pos:]
            # Create string item
            string_item = StringItem(char_len=len(text), font_info=font_info, start_pos=start_pos)
            # Insert into string items
            self.string_items.insert(position, string_item)
            # Update start positions of subsequent items
            for i in range(position + 1, len(self.string_items)):
                self.string_items[i].start_pos += len(text)

        # Validate after adding
        self.validate()

        return string_item


class LBXTextEditor:
    """Main class for working with LBX label.xml files."""

    def __init__(self, file_path: Optional[str] = None):
        """Initialize the editor, optionally with a file path."""
        self.file_path = file_path
        self.tree = None
        self.root = None
        self.text_objects = []

        if file_path:
            self.load(file_path)

    def load(self, file_path: str) -> None:
        """Load and parse a label.xml file."""
        self.file_path = file_path
        self.tree = ET.parse(file_path)
        self.root = self.tree.getroot()
        self._parse_text_objects()

    def _parse_text_objects(self) -> None:
        """Parse all text objects from the XML."""
        self.text_objects = []

        # Safety check for root
        if self.root is None:
            print("ERROR: No XML root found")
            return

        # Find all text:text elements
        for text_elem in self.root.findall('.//text:text', NAMESPACES):
            text_obj = TextObject.from_element(text_elem)
            # Validate the text object
            text_obj.validate()
            self.text_objects.append(text_obj)

    def save(self, output_path: Optional[str] = None) -> None:
        """
        Save changes back to the XML file.

        CRITICAL: This ensures proper XML formatting for Brother P-Touch by:
        1. Updating all text objects with their current text and string items
        2. Writing XML with proper encoding and declaration

        Args:
            output_path: Path to save the XML file (uses original path if None)
        """
        if not self.tree or not self.root:
            raise ValueError("No XML data loaded")

        # Update all text objects in the XML
        for text_obj in self.text_objects:
            # Validate before saving
            if text_obj.validate():
                text_obj.update_element()
            else:
                print(f"WARNING: Invalid text object: {text_obj.text}")

        # Save the modified XML
        if output_path is None:
            output_path = self.file_path
        if output_path is None:
            raise ValueError("No output path specified and no file path set during initialization")

        # Add declaration and proper formatting
        self.tree.write(output_path, encoding='UTF-8', xml_declaration=True)

    def get_text_objects(self) -> List[TextObject]:
        """Get all text objects from the label."""
        return self.text_objects

    def get_text_object_by_index(self, index: int) -> TextObject:
        """Get a text object by its index."""
        if index < 0 or index >= len(self.text_objects):
            raise IndexError(f"Text object index {index} out of range")
        return self.text_objects[index]

    def find_replace_all(self, find_text: str, replace_text: str, case_sensitive: bool = True) -> int:
        """Find and replace text in all text objects. Returns the number of replacements."""
        total_replacements = 0
        for text_obj in self.text_objects:
            total_replacements += text_obj.find_replace(find_text, replace_text, case_sensitive)
        return total_replacements

    def regex_find_replace_all(self, pattern: str, replace_text: str, case_sensitive: bool = True) -> int:
        """
        Find and replace text using regular expressions in all text objects.

        Args:
            pattern: Regular expression pattern to match
            replace_text: Replacement text (can include group references)
            case_sensitive: Whether the pattern matching should be case-sensitive

        Returns:
            Total number of replacements made across all text objects
        """
        total_replacements = 0
        for text_obj in self.text_objects:
            total_replacements += text_obj.regex_find_replace(pattern, replace_text, case_sensitive)
        return total_replacements

    def extract_from_lbx(self, lbx_path: str, output_dir: Optional[str] = None) -> str:
        """
        Extract label.xml from an LBX file.

        Args:
            lbx_path: Path to the LBX file
            output_dir: Directory to extract to (temporary directory if None)

        Returns:
            Path to the extracted label.xml file
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()

        with zipfile.ZipFile(lbx_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        label_xml_path = os.path.join(output_dir, 'label.xml')
        if not os.path.exists(label_xml_path):
            raise FileNotFoundError(f"label.xml not found in {lbx_path}")

        return label_xml_path

    def update_lbx(self, lbx_path: str, output_path: Optional[str] = None) -> str:
        """
        Update label.xml in an LBX file.

        Args:
            lbx_path: Path to the LBX file
            output_path: Path to save the updated LBX file (defaults to overwriting the input)

        Returns:
            Path to the updated LBX file
        """
        if output_path is None:
            output_path = lbx_path

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()

        try:
            # Extract the LBX
            with zipfile.ZipFile(lbx_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Save the updated XML
            label_xml_path = os.path.join(temp_dir, 'label.xml')
            self.save(label_xml_path)

            # Create a new LBX file
            with zipfile.ZipFile(output_path, 'w', compression=zipfile.ZIP_DEFLATED) as zip_out:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zip_out.write(file_path, arcname)

            return output_path

        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)


def main():
    """Command line interface for the LBX Text Editor."""
    import argparse

    parser = argparse.ArgumentParser(description='LBX Text Editor - Manipulate text in Brother P-touch LBX label files')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract label.xml from an LBX file')
    extract_parser.add_argument('input', help='Input LBX file')
    extract_parser.add_argument('-o', '--output', help='Output directory')

    # List text objects command
    list_parser = subparsers.add_parser('list', help='List text objects in a label.xml file')
    list_parser.add_argument('input', help='Input label.xml file or LBX file')

    # Edit text command
    edit_parser = subparsers.add_parser('edit', help='Edit text in a label.xml file')
    edit_parser.add_argument('input', help='Input label.xml file or LBX file')
    edit_parser.add_argument('-i', '--index', type=int, required=True, help='Index of text object to edit')
    edit_parser.add_argument('-t', '--text', required=True, help='New text content')
    edit_parser.add_argument('-o', '--output', help='Output file')

    # Find and replace command
    replace_parser = subparsers.add_parser('replace', help='Find and replace text')
    replace_parser.add_argument('input', help='Input label.xml file or LBX file')
    replace_parser.add_argument('-f', '--find', required=True, help='Text to find')
    replace_parser.add_argument('-r', '--replace', required=True, help='Text to replace with')
    replace_parser.add_argument('-i', '--ignore-case', action='store_true', help='Ignore case when finding')
    replace_parser.add_argument('-o', '--output', help='Output file')
    replace_parser.add_argument('--regex', action='store_true', help='Use regular expressions for pattern matching')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Handle extract command
    if args.command == 'extract':
        editor = LBXTextEditor()
        output_path = editor.extract_from_lbx(args.input, args.output)
        print(f"Extracted label.xml to: {output_path}")
        return

    # Load the input file
    editor = LBXTextEditor()
    input_file = args.input
    is_lbx = input_file.lower().endswith('.lbx')

    if is_lbx:
        input_file = editor.extract_from_lbx(args.input)

    editor.load(input_file)

    # Handle list command
    if args.command == 'list':
        for i, text_obj in enumerate(editor.get_text_objects()):
            print(f"Text Object {i}:")
            print(f"  Content: {repr(text_obj.text)}")
            print(f"  String Items: {len(text_obj.string_items)}")
            for j, item in enumerate(text_obj.string_items):
                print(f"    Item {j}: charLen={item.char_len}, "
                      f"font={item.font_info.name}, "
                      f"weight={item.font_info.weight}, "
                      f"size={item.font_info.size}")

    # Handle edit command
    elif args.command == 'edit':
        try:
            text_obj = editor.get_text_object_by_index(args.index)
            text_obj.edit_text(args.text)

            output = args.output or input_file
            if is_lbx and args.output:
                editor.update_lbx(args.input, args.output)
            else:
                editor.save(output)

            print(f"Text updated and saved to: {output}")
        except IndexError:
            print(f"Error: Text object index {args.index} not found")

    # Handle replace command
    elif args.command == 'replace':
        if args.regex:
            count = editor.regex_find_replace_all(args.find, args.replace, not args.ignore_case)
        else:
            count = editor.find_replace_all(args.find, args.replace, not args.ignore_case)

        output = args.output or input_file
        if is_lbx and args.output:
            editor.update_lbx(args.input, args.output)
        else:
            editor.save(output)

        print(f"Replaced {count} occurrences. Updated file saved to: {output}")


if __name__ == "__main__":
    main()
