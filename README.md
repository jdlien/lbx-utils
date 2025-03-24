<!-- @format -->

# LBX Utilities

A set of tools for working with Brother P-Touch Label (.lbx) files.

## What is LBX?

LBX files are label documents created with Brother P-Touch Editor software. They're actually ZIP archives containing label configuration, text, and images in XML format.

## Tools Included

### parse-lbx.py

A utility to extract information from LBX files:

- Extracts text content from LBX files
- Extracts images from LBX files (with optional BMP to PNG conversion)
- Can save text to .txt files
- Supports batch processing of multiple LBX files
- Optional database integration for Lego part information
- Requires Python 3.x

Usage:

```
./parse-lbx.py [options]

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

### change-lbx.py

A utility for customizing Brother P-touch label (.lbx) files:

- Modify font size
- Change label width (12mm, 18mm, 24mm)
- Center elements vertically
- Scale images
- Adjust text positioning and margins

Usage:

```
python3 change-lbx.py label.lbx label-24mm.lbx -f 14 -l 24 -c -s 1.5 -m 0.5

Options:
  -f, --font-size      Font size in pt
  -l, --label-size     Label width in mm (12, 18, or 24)
  -c, --center         Center elements vertically
  -s, --scale          Scale factor for images (e.g., 1.5 for 150%)
  -m, --margin         Margin between image and text in mm
```

## Installation

1. Clone this repository
2. Optional dependencies:
   - Install Pillow for image optimization: `pip install pillow`
   - Install colorama for colored output: `pip install colorama`
   - Install lxml for better XML handling: `pip install lxml`
   - Install ImageMagick for advanced image conversion

## License

MIT
