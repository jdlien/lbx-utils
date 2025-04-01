<!-- @format -->

# LBX Utilities

This repository contains utilities for working with Brother P-Touch LBX label files.

## What is LBX?

LBX is the file format used by Brother P-Touch Editor software for label designs. It's a ZIP archive containing XML files that define the label layout, text, images, and metadata.

## Project Organization

The project is now organized as a Python package with the following structure:

```
lbx-utils/
├── lbx_utils/                # Main package
│   ├── core/                 # Core functionality modules
│   │   ├── lbx_text_edit.py  # Text editing in LBX files
│   │   ├── lbx_create.py     # Create new LBX labels
│   │   ├── change_lbx.py     # Modify existing LBX files
│   │   ├── lbx_parser.py     # Parse and extract from LBX files
│   │   └── generate_part_image.py # Generate LEGO part images
│   └── __main__.py           # CLI entry point
├── data/                     # Data files
│   ├── label_templates/      # Template LBX files
│   ├── label_examples/       # Example LBX files
│   └── schema/               # XSD schema files
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
└── scripts/                  # Utility shell scripts
```

## Installation

```bash
# Install in development mode
pip install -e .

# Or install from GitHub
pip install git+https://github.com/jdlien/lbx-utils.git
```

## Command Line Usage

After installing, you can use the command line interface:

```bash
# Using the unified CLI
lbx text-edit --help
lbx create --help
lbx change --help
lbx generate-part-image --help

# Or individual commands
lbx-text-edit --help
lbx-create --help
lbx-change --help
lbx-generate-part-image --help
```

## Utilities

### lbx_create.py

Creates new Brother P-touch label files with text and/or images.

#### Examples

```bash
lbx create --output mylabel.lbx --text "Hello World" --size 24
```

```bash
lbx create --output mylabel.lbx --text "Line 1" --text "Line 2" --size 24
```

```bash
lbx create --output mylabel.lbx --image logo.png --size 24
```

```bash
lbx create --output mylabel.lbx --image logo.png --text "Company Name" --size 24
```

```bash
lbx create --output mylabel.lbx --text "Bold Text" --bold --font "Helsinki" --size 24
```

### lbx_text_edit.py

Edits text within existing LBX files.

```bash
lbx text-edit replace input.lbx -f "2x2" -r "2×2"
```

### change_lbx.py

Modifies existing LBX files (font size, label width, centering, etc).

```bash
lbx change input.lbx output.lbx -f 14 -l 24 -c -s 1.5 -m 0.5
```

### generate_part_image.py

Generates grayscale label-friendly images of LEGO parts using LDView.

```bash
lbx generate-part-image 3001 -o brick.png
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

For detailed specifications, see the [LBX Specification](data/schema/lbx-specification.md).

## Dependencies

- Python 3.7+
- Required packages (installed automatically):
  - pillow>=9.0.0
  - lxml>=5.3.1
  - lxml-stubs>=0.5.0
  - colorama>=0.4.6
  - typer>=0.9.0
  - rich>=13.7.0

## License

MIT

Contributions, bug reports, and feature requests are welcome!
