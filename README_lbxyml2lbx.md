# LBX YAML to LBX Converter

This tool converts Brother P-Touch label designs from a simplified YAML format (`.lbx.yml`) to the Brother P-Touch LBX format (`.lbx`) compatible with Brother P-Touch Editor software.

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/lbx-utils.git
cd lbx-utils

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python -m src.lbx_utils.lbxyml2lbx --input my_label.lbx.yml --output my_label.lbx
```

Optional parameters:

- `--unzip PATH`: Extract the resulting LBX file to the specified directory for inspection

Example with organized output directory:

```bash
# Create output directory
mkdir -p test_output/lbxyml2lbx

# Convert YAML to LBX and unzip for inspection
python -m src.lbx_utils.lbxyml2lbx \
  --input data/lbx_yml_examples/01_basic_text.lbx.yml \
  --output test_output/lbxyml2lbx/01_basic_text.lbx \
  --unzip test_output/lbxyml2lbx/01_basic_text
```

This will create the LBX file at `test_output/lbxyml2lbx/01_basic_text.lbx` and extract its contents to `test_output/lbxyml2lbx/01_basic_text/` for inspection.

### Processing All Examples

You can automatically process all example YAML files in the `data/lbx_yml_examples` directory using the provided script:

```bash
python process_examples.py
```

This script will:

1. Find all `.lbx.yml` files in the examples directory
2. Convert each file to LBX format
3. Save the output to `test_output/lbxyml2lbx/`
4. Extract the contents of each LBX file for inspection

This is a convenient way to process multiple examples at once and see how different YAML configurations are converted to LBX format.

### Python API

```python
from lbx_utils.lbxyml2lbx import YamlParser, LbxGenerator

# Parse the YAML file
parser = YamlParser("my_label.lbx.yml")
config = parser.parse()

# Generate the LBX file
generator = LbxGenerator(config)
generator.generate_lbx("my_label.lbx")
```

## LBX YAML Format

The LBX YAML format is a simplified representation for Brother P-touch label designs. See the [specification](data/schema/lbx.yml-spec.md) for complete details.

### Supported Features

- Different label sizes (9mm, 12mm, 18mm, 24mm)
- Fixed width or auto-sizing
- Portrait or landscape orientation
- Text objects with formatting (bold, italic, underlined)
- Text alignment (left, center, right)
- Images with monochrome conversion and transparency

### Size Specification

The label size can be specified in two equivalent formats:

- With units: `size: 12mm`
- Without units: `size: 12`

Both formats will be correctly interpreted. Available sizes are 9mm, 12mm, 18mm, and 24mm.

### Basic Example

```yaml
# Basic label with text
size: 24mm
width: auto
orientation: landscape

objects:
  - type: text
    content: "Hello World"
    x: 10
    y: 12
    font: Helsinki
    size: 14
    bold: true
    align: center
```

### Fixed Width Example

```yaml
# Label with fixed width
size: 12mm
width: 90mm
orientation: landscape

objects:
  - type: text
    content: "Fixed Width Text"
    x: 10
    y: 12
    font: Helsinki
    size: 14
    bold: true
    align: center
```

### Formatted Text Example

```yaml
# Label with formatted text
size: 24mm
width: auto
orientation: landscape

objects:
  - type: text
    content: "Bold Text"
    x: 10
    y: 12
    font: Helsinki
    size: 14
    bold: true
    align: left

  - type: text
    content: "Italic Text"
    x: 10
    y: 30
    font: Helsinki
    size: 14
    italic: true
    align: center

  - type: text
    content: "Underlined Text"
    x: 10
    y: 48
    font: Helsinki
    size: 14
    underline: true
    align: right
```

### Image Example

```yaml
# Label with an image
size: 24mm
width: auto
orientation: landscape

objects:
  - type: image
    source: "path/to/image.png"
    x: 20
    y: 12
    width: 50
    height: 40
    monochrome: true
```

## Testing

Run the tests to verify functionality:

```bash
python -m tests.test_lbxyml2lbx
```

The tests will generate output files in the `test_output/lbxyml2lbx` directory. The directory structure is organized as follows:

```
test_output/
  └── lbxyml2lbx/
      ├── basic_text/           # Unzipped basic text label
      ├── basic_text.lbx        # LBX file for basic text label
      ├── blank_label/          # Unzipped blank label
      ├── blank_label.lbx       # LBX file for blank label
      ├── fixed_width/          # Unzipped fixed width label
      ├── fixed_width.lbx       # LBX file for fixed width label
      ├── formatted_text/       # Unzipped formatted text label
      ├── formatted_text.lbx    # LBX file for formatted text label
      ├── image_label/          # Unzipped image label
      └── image_label.lbx       # LBX file for image label
```

You can examine these files to see the structure of LBX files and understand how different YAML elements are translated to the Brother P-Touch format.

## Known Issues and Limitations

- Rich text with mixed formatting in a single text object is not yet fully supported
- Barcode objects are not yet implemented
- Group objects and flex layouts are not yet implemented

## License

[MIT License](LICENSE)
