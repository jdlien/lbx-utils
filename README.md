<!-- @format -->

# LBX Utilities

This repository contains utilities for working with Brother P-Touch LBX label files.

## What is LBX?

LBX is the file format used by Brother P-Touch Editor software for label designs. It's a ZIP archive containing XML files that define the label layout, text, images, and metadata.

## Utilities

### lbx_create.py

Creates new Brother P-touch label files with text and/or images.

#### Examples

```bash
python lbx_create.py create --output mylabel.lbx --text "Hello World" --size 24
```

```bash
python lbx_create.py create --output mylabel.lbx --text "Line 1" --text "Line 2" --size 24
```

```bash
python lbx_create.py create --output mylabel.lbx --image logo.png --size 24
```

```bash
python lbx_create.py create --output mylabel.lbx --image logo.png --text "Company Name" --size 24
```

```bash
python lbx_create.py create --output mylabel.lbx --text "Bold Text" --bold --font "Helsinki" --size 24
```

#### Help

```bash
python lbx_create.py --help
```

## LBX File Format

The LBX file is a ZIP archive containing:

- `label.xml`: Contains the label layout, text, and image references
- `prop.xml`: Contains metadata about the label
- Image files: Any images used in the label

### Key Compatibility Requirements

For compatibility with Brother P-Touch Editor, follow these guidelines:

1. **XML Structure**: The order of XML elements is critical - changing the order may cause the editor to crash
2. **Text Formatting**: Use these settings for best compatibility:

   - Font: Helsinki
   - Font PitchAndFamily: 2
   - Font Size: 21.7pt
   - Original Size: 28.8pt
   - Text Control: AUTOLEN
   - Auto Line Feed: false
   - Vertical Alignment: TOP

3. **Background Width**: Use 34.4pt for maximum compatibility

For detailed specifications, see the [LBX Specification](schema/lbx-specification.md).

## Schema Documentation

The repository includes XSD schema files that document the structure of LBX XML files:

- `schema/lbx_text_schema.xsd`: Defines the structure for text elements
- `schema/lbx_label_schema.xsd`: Defines the overall label structure
- `schema/lbx_image_schema.xsd`: Defines the structure for image elements

## Requirements

- Python 3.6+
- Required packages: typer, rich, colorama, lxml

## License

MIT

# LBX Utilities

A set of tools for working with Brother P-Touch Label (.lbx) files.

## What is LBX?

LBX files are label documents created with Brother P-Touch Editor software. They're actually ZIP archives containing label configuration, text, and images in XML format.

## Tools Included

### parse_lbx.py

A utility to extract information from LBX files:

- Extracts text content from LBX files
- Extracts images from LBX files (with optional BMP to PNG conversion)
- Can save text to .txt files
- Supports batch processing of multiple LBX files
- Optional database integration for Lego part information
- Requires Python 3.x

Usage:

```
./parse_lbx.py [options]

Options:
  -h, --help           Show this help message and exit
  -d DIR, --dir=DIR    Directory to search for LBX files (default: current directory)
  -r, --recursive      Search recursively in subdirectories (default)
  --no-recursive       Do not search recursively in subdirectories
  -o EXT, --output=EXT Output file extension (default: .txt)
  --verbose            Print detailed processing information
  -i --extract-images  Extract images from LBX files and save them to a folder
  --db                 Use SQLite database for part information and update database
```

### change_lbx.py

A utility for customizing Brother P-touch label (.lbx) files:

- Modify font size
- Change label width (12mm, 18mm, 24mm)
- Center elements vertically
- Scale images
- Adjust text positioning and margins

Usage:

```
python3 change_lbx.py label.lbx label-24mm.lbx -f 14 -l 24 -c -s 1.5 -m 0.5

Options:
  -f, --font-size      Font size in pt
  -l, --label-size     Label width in mm (12, 18, or 24)
  -c, --center         Center elements vertically
  -s, --scale          Scale factor for images (e.g., 1.5 for 150%)
  -m, --margin         Margin between image and text in mm
```

## generate_part_image.py

A utility to generate grayscale label-friendly images of LEGO parts using LDView.
This requires LDView to be installed along with the LDraw library.

## Dependencies

### Required

- **Python 3.6+**: Both utilities require Python 3.6 or newer
- **Standard libraries**: `os`, `re`, `sys`, `zipfile`, `xml`, `argparse`, `shutil`, `io`, `tempfile`, `pathlib`, `datetime`

### Optional

- **Pillow**: Used for image optimization and processing
  - Enables proper BMP to PNG conversion
  - Preserves transparency in extracted images
- **lxml**: Provides enhanced XML parsing capabilities
  - Significantly improves vertical centering functionality in change_lbx.py
  - Offers better XML handling and manipulation
- **colorama**: Adds colored terminal output
  - Makes command output more readable with color-coding
- **ImageMagick**: External program for advanced image conversion
  - Required for best BMP to transparent PNG conversion
  - Handles more complex image formats

## Installation

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/lbx-utils.git
   cd lbx-utils
   ```

2. Install required Python dependencies:

   ```
   # Install all dependencies (recommended)
   pip install -r requirements.txt

   # OR install individually
   # Basic installation with minimal features
   pip install pillow

   # Full installation with all features
   pip install pillow lxml colorama
   ```

3. Install ImageMagick (optional):

   - **macOS**: `brew install imagemagick`
   - **Ubuntu/Debian**: `sudo apt-get install imagemagick`
   - **Windows**: Download and install from [ImageMagick website](https://imagemagick.org/script/download.php)

4. Make scripts executable (on Unix-based systems):
   ```
   chmod +x parse_lbx.py
   chmod +x change_lbx.py
   ```

# TODO

- Tinker with increasing default resolution of images, Tom's are still a little higher
- Support editing of text in LBX files
- Completely automated generation of labels, including part images and QR codes linking to http://rbck.ca/part_number
- Note: QR Codes are only effective when sized at 7mm or greater, unless we can print at higher than 180dpi.

# LBX Text Editor

A Python utility for manipulating text in Brother P-Touch LBX label files. This tool allows you to edit, find, and replace text content in label files while preserving the required formatting structure for proper display in Brother P-Touch Editor.

## Features

- Extract and parse text objects from label.xml files in LBX containers
- Edit text content while automatically updating character length tracking
- Find and replace text across all text objects
- Support for regular expression-based find and replace operations
- Automated handling of string item character length attributes

## Installation

Clone this repository and ensure you have Python 3.6+ installed.

```bash
git clone https://github.com/yourusername/lbx-utils.git
cd lbx-utils
```

No additional dependencies are required beyond the Python standard library.

## Usage

### Command Line Usage

```bash
# List all text objects in an LBX file
python lbx_text_edit.py list input.lbx

# Edit a specific text object
python lbx_text_edit.py edit input.lbx -i 0 -t "New text" -o output.lbx

# Find and replace text
python lbx_text_edit.py replace input.lbx -f "Old text" -r "New text" -o output.lbx

# Case-insensitive find and replace
python lbx_text_edit.py replace input.lbx -f "text" -r "TEXT" -i -o output.lbx

# Regular expression find and replace
python lbx_text_edit.py replace input.lbx -f "(\d+)x(\d+)" -r "\1×\2" --regex -o output.lbx
```

### As a Library

```python
from lbx_text_edit import LBXTextEditor

# Open an LBX file
editor = LBXTextEditor()
label_xml_path = editor.extract_from_lbx("input.lbx")
editor.load(label_xml_path)

# Get and edit text objects
text_obj = editor.get_text_object_by_index(0)
text_obj.edit_text("New text content")

# Save changes back to a new LBX file
editor.update_lbx("input.lbx", "output.lbx")
```

## Critical Format Requirements

The Brother P-Touch label format has several requirements that must be maintained for labels to display correctly:

1. Each `text:text` element MUST have one or more `text:stringItem` elements after `pt:data`
2. Each `stringItem` needs a `charLen` attribute that matches the length of its text segment
3. The sum of all `charLen` values must equal the length of the text in `pt:data`
4. All `stringItems` must include their own `text:ptFontInfo` with font information
5. The order of XML elements matters and must be preserved exactly
6. If a text segment is removed, its corresponding `stringItem` must be removed or adjusted
7. Special XML tags must be formatted exactly as expected by the Brother software

This tool automatically handles these requirements when editing text, ensuring that your modified labels continue to work correctly in the Brother P-Touch Editor.

## Examples

### Convert dimension notation from "2x2" to "2×2"

```bash
python lbx_text_edit.py replace label.lbx -f "(\d+)x(\d+)" -r "\1×\2" --regex
```

### Add a suffix to all text objects

```bash
python lbx_text_edit.py replace label.lbx -f "^(.*)$" -r "\1 Brick" --regex
```

### Format part numbers

```bash
python lbx_text_edit.py replace label.lbx -f "(\d{4})(\d)?" -r "Part #\1-\2" --regex
```

# LBX Schema Documentation

The `schema` directory contains XML Schema Definition (XSD) files and documentation for the Brother P-Touch LBX format based on reverse engineering. These files document the structure, elements, and requirements of the LBX format.

## Schema Files

- **lbx_label_schema.xsd**: Main schema for the label.xml structure
- **lbx_text_schema.xsd**: Schema for text elements and formatting
- **lbx_draw_schema.xsd**: Schema for drawing elements (frames, symbols, polygons)
- **lbx_image_schema.xsd**: Schema for image elements (clipart, photos)
- **lbx_unified_schema.xsd**: Master schema that imports all namespace-specific schemas

## Features Documented

- Vertical text support
- Multiple text control modes (FREE, LONGTEXTFIXED, FIXEDFRAME)
- Multiple copies of labels (4-up printing)
- Portrait and landscape orientation
- Mixed font sizes within text blocks
- Decorative frames and custom shapes
- Built-in clipart and symbols

## Reference Documentation

The `schema/LBX_SCHEMA_REFERENCE.md` file provides a comprehensive reference guide explaining:

- The overall LBX file structure
- Namespaces used in the format
- Critical requirements for text editing
- Examples of XML structures for various elements
- Best practices for working with LBX files

This documentation is especially useful for developers working on tools to manipulate Brother P-Touch label files programmatically.

## License

MIT License

## Troubleshooting

If modified labels aren't displaying correctly in Brother P-Touch Editor:

1. Ensure you're using the latest version of this tool which properly preserves string items
2. Check that string items' character lengths match the text content length
3. Verify that the XML structure maintains the same element order as the original
4. Use the `list` command to inspect the text objects and their string items

## Contributing

Contributions, bug reports, and feature requests are welcome!
