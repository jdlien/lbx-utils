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

## generate-part-image.py

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
  - Significantly improves vertical centering functionality in change-lbx.py
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
   chmod +x parse-lbx.py
   chmod +x change-lbx.py
   ```

# TODO

- Support editing of text in LBX files
- Completely automated generation of labels, including part images and QR codes linking to http://rbck.ca/part_number

## License

MIT
