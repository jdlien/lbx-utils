# LBX YAML Format Specification

## 1. Introduction

The LBX YAML format (`.lbx.yml`) is a simplified representation for Brother P-touch label designs that can be converted into the complex LBX format. This specification defines the structure, properties, and behaviors of this YAML-based format.

## 2. File Format

### 2.1 File Extensions

- `.lbx.yml` - Standard uncompressed format with external image references
- `.lbx.yml.zip` - Compressed archive containing the YAML file and referenced images

### 2.2 Basic Structure

The format consists of a YAML document with a required canonical structure:

```yaml
# Label properties section
size: 24mm
width: 100mm
orientation: landscape

# Objects section (required)
objects:
  - type: text
    content: "Hello World"
    # ...

  - type: image
    source: "logo.png"
    # ...
```

In this structure, label properties are at the root level, and all objects are within the `objects` array. The `objects` key is required, and all visual elements must be defined within this array.

### 2.3 Object Shortcut Syntax

For improved readability and cleaner YAML, object types can be specified using a shortcut syntax:

#### 2.3.1 Content Objects (text, image, barcode, qr)

For object types that primarily define content, you can use the object type as a key with its value as the content:

```yaml
objects:
  # Long form (traditional)
  - type: text
    content: "Hello World"
    x: 10
    y: 20

  # Shortcut syntax
  - text: "Hello World"
    x: 10
    y: 20

  # Image shortcut
  - image: "logo.png"
    width: 30
    height: 30

  # Barcode shortcut
  - barcode: "12345"
    barcodeType: "code128"

  # QR code shortcut
  - qr: "https://example.com"
    errorCorrection: "H"
```

In these examples:

- `text: "Hello World"` is equivalent to `type: text, content: "Hello World"`
- `image: "logo.png"` is equivalent to `type: image, source: "logo.png"`
- `barcode: "12345"` is equivalent to `type: barcode, data: "12345"`
- `qr: "https://example.com"` is equivalent to `type: barcode, barcodeType: "qr", data: "https://example.com"`

#### 2.3.2 Container Objects (line, rect, container, group)

For organizational object types, you can use the object type as a key with its value as the name:

```yaml
objects:
  # Long form (traditional)
  - type: group
    name: "header_section"
    x: 0
    y: 0
    objects: [...]

  # Shortcut syntax
  - group: "header_section"
    x: 0
    y: 0
    objects: [...]

  # Container shortcut
  - container: "content_area"
    direction: column
    objects: [...]

  # Line and rectangle shortcuts
  - line: "divider"
    x1: 0
    y1: 50
    x2: 100
    y2: 50

  - rect: "background"
    x: 10
    y: 10
    width: 80
    height: 30
```

In these examples:

- `group: "header_section"` is equivalent to `type: group, name: "header_section"`
- `container: "content_area"` is equivalent to `type: container, name: "content_area"`
- `line: "divider"` is equivalent to `type: line, name: "divider"`
- `rect: "background"` is equivalent to `type: rect, name: "background"`

All other attributes are interpreted normally, so you can still specify positioning, styling, and other properties with either syntax.

### 2.4 Units

All measurements can be specified in either points (pt) or millimeters (mm). If no unit is specified, points (pt) are used by default. The unit suffix should be included in the YAML file (e.g., `10pt` or `5mm`).

- **Points (pt)** - The default unit if not specified. Used internally by the LBX format.
- **Millimeters (mm)** - More intuitive for users. Will be automatically converted to points during processing.

For positioning objects, both coordinates and dimensions can use either unit:

```yaml
# Using points (default unit)
objects:
  - type: text
    content: "Points"
    x: 10pt
    y: 15pt
    width: 120pt
    height: 20pt

# Using millimeters
- type: text
  content: "Millimeters"
  x: 3.5mm
  y: 5.3mm
  width: 42.3mm
  height: 7.1mm

# Using numeric values (interpreted as points)
- type: text
  content: "No units (defaults to points)"
  x: 10
  y: 15
  width: 120
  height: 20
```

For tape size, millimeters are always used (`size: 24mm`).

The conversion between millimeters and points uses the formula: 1mm ≈ 2.83pt

#### 2.3.1 Positioning Notes

When specifying coordinates in your YAML file, use the same coordinate system that you would use in P-Touch Editor. The coordinates (0,0) represent the top-left corner of the printable area on the label.

The coordinate system works as follows:

- The point (0,0) represents the top-left corner of the printable area
- Positive X values move right from this corner
- Positive Y values move down from this corner

```
    (0,0)
      +-------------------+
      |                   |
      |  Printable Area   |
      |                   |
      +-------------------+
```

You do not need to add any offsets to account for margins - the system automatically handles the relationship between the coordinates in the YAML file and the physical position on the label.

For best results, specify units explicitly (`pt` or `mm`).

## 3. Label Properties

The label properties define the global characteristics of the label.

```yaml
size: 24mm # Tape size (9mm, 12mm, 18mm, 24mm)
width: 100mm # Fixed width (or "auto" for automatic sizing)
length: auto # Fixed length or "auto" for automatic sizing
orientation: landscape # Label orientation (landscape, portrait)
margin: 5 # Optional: Additional margin beyond the minimum
background: "#FFFFFF" # Background color. This doesn't affect printing, but is shown in preview.
color: "#000000" # Color of the label ink. Only affects preview.
```

### 3.1 Required Properties

| Property | Description | Values                                        |
| -------- | ----------- | --------------------------------------------- |
| `size`   | Tape width  | `3.5mm`, `6mm`, `9mm`, `12mm`, `18mm`, `24mm` |

### 3.2 Optional Properties

| Property      | Description            | Default     |
| ------------- | ---------------------- | ----------- |
| `width`       | Label width (in mm)    | "auto"      |
| `orientation` | Label orientation      | "landscape" |
| `margin`      | Additional margin      | 0           |
| `background`  | Label background color | "#FFFFFF"   |
| `color`       | Label text color       | "#000000"   |

Note: `width` is technically the length when `orientation` is `landscape`. When `orientation` is `portrait`, `width` is the height.

### 3.3 Layout Properties at Root Level

The root level can include layout properties that apply to all objects within the `objects` array, effectively making the label itself act as an implicit group container. This eliminates the need for a wrapper group when aligning all objects.

```yaml
# Label properties
size: 24mm
width: 100mm
orientation: landscape

# Layout properties at root level (acts as an implicit group)
direction: column # Applied to all objects in the objects array
align: center # Center align all objects
gap: 10 # 10pt spacing between objects

objects:
  - type: text
    content: "Title"
    # No need to specify x position - handled by layout

  - type: text
    content: "Subtitle"
    # Automatically positioned below the title with 10pt gap
```

When using root-level layout properties, any `x` and `y` values specified on individual objects will act as offsets from their calculated positions. For example:

- In `direction: column` layout, adding `y: 4mm` to an element will move that element (and consequently all elements below it) down by 4mm from their calculated positions.
- In `direction: row` layout, adding `x: 5pt` to an element will move that element (and consequently all elements after it) to the right by 5pt from their calculated positions.

This allows for fine-tuning positioning while still maintaining the benefits of automatic layout.

The root level supports the same container layout properties as groups:

| Property    | Description                     | Values                                                  | Default |
| ----------- | ------------------------------- | ------------------------------------------------------- | ------- |
| `direction` | Main axis direction             | `row`, `column`, `row-reverse`, `column-reverse`        | `row`   |
| `justify`   | Alignment along main axis       | `start`, `end`, `center`, `between`, `around`, `evenly` | `start` |
| `align`     | Alignment along cross axis      | `start`, `end`, `center`, `stretch`                     | `start` |
| `gap`       | Spacing between items           | Number                                                  | 0       |
| `padding`   | Internal padding within label   | Number or object with top/right/bottom/left             | 0       |
| `wrap`      | Whether items wrap to next line | `true`, `false`                                         | `false` |

When these properties are present at the root level, the layout engine creates an implicit group container that wraps all objects, which allows for automatic positioning and alignment without having to create an explicit wrapper group.

Individual objects within the root level can still use item properties (`align`, `grow`, `shrink`, `basis`, `order`) to override the root-level settings, just as they would within an explicit group.

## 4. Objects

The `objects` array contains all visual elements to be rendered on the label. Each object must have a `type` property that defines its behavior.

### 4.1 Common Object Properties

All objects support these common properties:

```yaml
- type: text # Required: Object type
  id: main_title # Optional: Unique identifier for reference, part of old idea for relative positioning
  name: my_text_element # Optional: Name for the object, maps to objectName attribute in pt:expanded tag
  x: 10 # X-coordinate from left edge (defaults to 0 if omitted)
  y: 20 # Y-coordinate from top edge (defaults to 0 if omitted)
  # Style properties vary by object type and are direct members of the object
```

| Property | Description                                                           | Default  |
| -------- | --------------------------------------------------------------------- | -------- |
| `type`   | Required: The type of object (text, image, barcode, group, container) | Required |
| `id`     | Optional: Unique identifier for reference                             | None     |
| `name`   | Optional: Name for the object, maps to objectName attribute in XML    | None     |
| `x`      | X-coordinate from left edge                                           | 0        |
| `y`      | Y-coordinate from top edge                                            | 0        |

### 4.2 Text Objects

Text objects display text content on the label.

```yaml
- type: text
  content: "Hello World" # Required: Text content
  name: header_text # Optional: Name for the object
  x: 10
  y: 20
  font: Helsinki # Font family
  size: 12 # Font size in points
  bold: true # Bold formatting
  italic: false # Italic formatting
  underline: false # Underline formatting
  align: center # Text alignment (left, center, right)
  vertical: false # Vertical text orientation
```

#### 4.2.1 Multiline Text Content

YAML offers several ways to include multiline text:

```yaml
# Using | (literal block scalar) - preserves line breaks
- type: text
  content: |
    First line
    Second line
    Third line
  x: 10
  y: 20
  size: 12

# Using > (folded block scalar) - converts line breaks to spaces
- type: text
  content: >
    This is a long sentence
    that will be folded into
    a single line with spaces.
  x: 30
  y: 20
  size: 12

# Using quoted string with escape characters
- type: text
  content: "First line\nSecond line\nThird line"
  x: 50
  y: 20
  size: 12
```

Block scalars (| and >) can include indentation indicators and chomping indicators:

```yaml
# Keep trailing newline (default)
content: |
  Text with
  multiple lines

# Strip trailing newline
content: |-
  Text with
  multiple lines

# Folded text with preserved paragraph breaks
content: >+
  Paragraph one
  still part of paragraph one

  Paragraph two
  still part of paragraph two
```

#### 4.2.2 Text-Specific Properties

| Property    | Description               | Values                      | Default    |
| ----------- | ------------------------- | --------------------------- | ---------- |
| `font`      | Font family               | `Helsinki`, etc.            | `Helsinki` |
| `size`      | Font size                 | Number                      | 12         |
| `bold`      | Bold formatting           | `true`, `false`             | `false`    |
| `italic`    | Italic formatting         | `true`, `false`             | `false`    |
| `underline` | Underline formatting      | `true`, `false`             | `false`    |
| `align`     | Text alignment            | `left`, `center`, `right`   | `left`     |
| `vertical`  | Vertical text orientation | `true`, `false`             | `false`    |
| `color`     | Text color                | Hex color (e.g., `#000000`) | `#000000`  |
| `wrap`      | Text wrapping behavior    | `true`, `false`, Number     | `true`     |
| `shrink`    | Reduce font size to fit   | `true`, `false`             | `false`    |

**Note on Centered/Right Alignment:** When using `align: center` or `align: right`, you might observe a small horizontal positioning offset (typically around 1mm or 2.8pt) if you do not specify an explicit `width` for the text object in your YAML. This occurs because the default width used by the generator might differ slightly from the text's actual rendered width calculated by P-Touch Editor, affecting the centering calculation. For precise positioning with these alignments:

- Use `align: left` if exact left-edge positioning is critical.
- Provide an accurate `width` attribute for the text object in your YAML.
- Apply a small manual compensation to the `x` coordinate (e.g., `x: -2.8pt` might correct centering at the origin).

#### 4.2.3 Rich Text Formatting

For text that requires mixed formatting (like having some words bold or italic within a sentence), there are two supported approaches:

##### 1. Text Fragments Array

The most flexible approach is to use an array of text fragments, each with its own formatting:

```yaml
- type: text
  x: 10
  y: 20
  align: left # Common properties apply to all fragments
  fragments:
    - content: "This is "
    - content: "bold"
      bold: true
    - content: " and this is "
    - content: "italic"
      italic: true
      font: "Helvetica Neue"
    - content: " text."
```

Each fragment can have its own formatting properties that override the common properties defined at the text object level.

##### 2. Markdown-Inspired Syntax

For simpler cases, a lightweight Markdown-inspired syntax can be used:

```yaml
- type: text
  content: "This is **bold** and this is *italic* text and __underlined__ text."
  x: 10
  y: 20
  markdown: true # Enable markdown parsing (default)
```

Supported Markdown syntax:

- `**text**` or `__text__` - Bold text
- `*text*` or `_text_` - Italic text
- `++text++` - Underlined text
- `~~text~~` - Strikethrough text

Multiple styles can be combined: `**_Bold and italic_**`

Note: Since this syntax lives inside YAML strings, care must be taken with escaping when using certain characters. Always use quotes around content that contains Markdown formatting.

### 4.3 Image Objects

Image objects display images on the label.

```yaml
- type: image
  source: "logo.png" # Required: Path to image file
  x: 10
  y: 30
  width: 20 # Width in points
  height: 20 # Height in points
  monochrome: true # Convert to monochrome
  transparency: false # Enable transparency
  transparency_color: "#FFFFFF" # Color to treat as transparent
```

#### 4.3.1 Image-Specific Properties

| Property             | Description                   | Values          | Default   |
| -------------------- | ----------------------------- | --------------- | --------- |
| `width`              | Image width                   | Number          | Required  |
| `height`             | Image height                  | Number          | Required  |
| `monochrome`         | Convert to monochrome         | `true`, `false` | `true`    |
| `transparency`       | Enable transparency           | `true`, `false` | `false`   |
| `transparency_color` | Color to treat as transparent | Hex color       | `#FFFFFF` |

### 4.4 Barcode Objects

Barcode objects render various barcode formats.

```yaml
- type: barcode
  barcodeType: qr # Required: Barcode type
  data: "https://example.com" # Required: Data to encode
  x: 50
  y: 12
  size: 30 # Size in points
  errorCorrection: M # QR error correction level
```

#### 4.4.1 Barcode-Specific Properties

| Property     | Description                     | Values                                           | Default                 |
| ------------ | ------------------------------- | ------------------------------------------------ | ----------------------- |
| `size`       | For QR codes: cell size         | Numbers, strings (see QR Code Size Options)      | `4` (Medium Large, 2pt) |
| `correction` | QR error correction level       | `L`, `M`, `Q`, `H`                               | `M`                     |
| `model`      | QR code model                   | `1`, `2`                                         | `2`                     |
| `margin`     | Include quiet zone/margin       | `true`, `false`                                  | `true`                  |
| `version`    | QR code version (size/capacity) | `auto`, `1`-`40`                                 | `auto`                  |
| `protocol`   | Barcode type                    | `qr`, `code39`, `code128`, `ean13`, `ean8`, etc. | `code128`               |
| `text`       | Show human-readable text        | `true`, `false`                                  | `false`                 |

#### 4.4.2 QR Code Cell Sizes

For QR codes, the `cellSize` parameter controls the size of each cell (module) in the QR code, affecting the overall resolution and scan quality:

| Size Value | Point Size | Description  | Readability                               |
| ---------- | ---------- | ------------ | ----------------------------------------- |
| `1`        | `0.8pt`    | Small        | Higher density, may be harder to scan     |
| `2`        | `1.2pt`    | Medium Small | Good balance of size and data capacity    |
| `3`        | `1.6pt`    | Medium       | Standard size for most applications       |
| `4`        | `2pt`      | Medium Large | Default size, good readability            |
| `5`        | `2.4pt`    | Large        | Best readability but larger physical size |

The `cellSize` can be specified either as a numeric size category (1-5) or as a specific point size with units:

```yaml
# Using size category (1-5)
- type: barcode
  barcodeType: qr
  data: "https://example.com"
  size: 40
  cellSize: 3 # Medium (1.6pt)

# Using specific point size
- type: barcode
  barcodeType: qr
  data: "https://example.com"
  size: 40
  cellSize: "1.6pt" # Same as cellSize: 3
```

When choosing a cell size, consider:

- Smaller sizes allow more data in the same space but may be harder to scan
- Larger sizes are more reliable to scan but take up more space
- The higher the error correction level, the larger the cell size should be

#### 4.4.3 QR Code Error Correction Levels

QR codes support different error correction levels that affect their ability to be read when damaged:

| Level | Name           | Description                                                       |
| ----- | -------------- | ----------------------------------------------------------------- |
| `L`   | Low (7%)       | Recovers approximately 7% of damaged data. Highest data capacity. |
| `M`   | Medium (15%)   | Recovers approximately 15% of damaged data. Default level.        |
| `Q`   | Quartile (25%) | Recovers approximately 25% of damaged data.                       |
| `H`   | High (30%)     | Recovers approximately 30% of damaged data. Most robust.          |

The higher the error correction level, the larger the QR code will be for the same data.

#### 4.4.3 Barcode Types

The LBX format supports various barcode types (case-insensitive), each with specific attributes:

| Type           | Description              | Notes                                                                |
| -------------- | ------------------------ | -------------------------------------------------------------------- |
| `qr`           | QR Code                  | 2D barcode, can encode large amounts of data                         |
| `code39`       | Code 39                  | Linear barcode, supports uppercase letters, numbers and some symbols |
| `code128`      | Code 128                 | Linear barcode, supports all ASCII characters                        |
| `ean128`       | EAN-128 (GS1-128)        | Application identifier linear barcode used in supply chains          |
| `itf25`        | ITF (Interleaved 2 of 5) | Fixed-length numeric-only barcode                                    |
| `codabar`      | Codabar (NW-7)           | Used in libraries, blood banks, and air parcels                      |
| `upca`         | UPC-A                    | 12-digit numeric barcode used in North America                       |
| `upce`         | UPC-E                    | Compressed 6-digit numeric barcode derived from UPC-A                |
| `ean13`        | EAN-13                   | 13-digit numeric barcode, international version of UPC-A             |
| `ean8`         | EAN-8                    | 8-digit numeric barcode for small packages                           |
| `isbn2`        | ISBN+2 (EAN-13 AddOn2)   | ISBN barcode with 2-digit add-on                                     |
| `isbn5`        | ISBN+5 (EAN-13 AddOn5)   | ISBN barcode with 5-digit add-on                                     |
| `postnet`      | POSTNET                  | Postal barcode used by the US Postal Service                         |
| `imb`          | Intelligent Mail Barcode | Used by the US Postal Service for mail tracking                      |
| `laserbarcode` | Laser Barcode            | Proprietary Brother format                                           |
| `datamatrix`   | Data Matrix              | 2D barcode that can encode large amounts of data in a small space    |
| `pdf417`       | PDF417                   | 2D barcode used for various applications including ID cards          |
| `rss`          | GS1 DataBar (RSS)        | Used for marking small items in retail environments                  |
| `maxicode`     | MaxiCode                 | 2D barcode used by UPS for package tracking                          |

#### 4.4.4 Common Barcode Properties

These properties apply to most barcode types:

| Property                 | Description                             | Values                              | Default                            |
| ------------------------ | --------------------------------------- | ----------------------------------- | ---------------------------------- |
| `data`                   | Content to encode in the barcode        | String                              | Required                           |
| `lengths`                | Number of characters for the barcode    | Number                              | Varies by barcode type             |
| `zeroFill`               | Fill with zeros to complete digit count | `true`, `false`                     | `false`                            |
| `barWidth`               | Width of the narrowest bar              | String with units (e.g., "0.8pt")   | `0.8pt`                            |
| `barRatio`               | Ratio between narrow and wide bars      | `1:2`, `1:3`, `2:1`, `2.5:1`, `3:1` | Varies by barcode type             |
| `humanReadable`          | Show human-readable text below barcode  | `true`, `false`                     | `false` for 2D, `true` for most 1D |
| `humanReadableAlignment` | Alignment of human-readable text        | `left`, `center`, `right`           | `left`                             |
| `checkDigit`             | Include check digit in barcode          | `true`, `false`                     | Varies by barcode type             |
| `autoLengths`            | Automatically determine lengths         | `true`, `false`                     | `true`                             |
| `margin`                 | Include quiet zone/margin               | `true`, `false`                     | `true`                             |
| `sameLengthBar`          | Equalize bar lengths                    | `true`, `false`                     | Varies by barcode type             |
| `bearerBar`              | Include bearer bar                      | `true`, `false`                     | `false`                            |

Example usage:

```yaml
- type: barcode
  barcodeType: code128
  data: "12345ABC"
  barWidth: 0.8pt
  barRatio: 1:3
  humanReadable: true
  margin: true
```

#### 4.4.5 Type-Specific Barcode Properties

##### QR Code Specific Properties

| Property          | Description                     | Values                                    | Default   |
| ----------------- | ------------------------------- | ----------------------------------------- | --------- |
| `cellSize`        | Size of each cell (module)      | `1`-`5` or specific point size            | `4` (2pt) |
| `errorCorrection` | Error correction level          | `L` (7%), `M` (15%), `Q` (25%), `H` (30%) | `M`       |
| `model`           | QR code model                   | `1`, `2`                                  | `2`       |
| `version`         | QR code version (size/capacity) | `auto`, `1`-`40`                          | `auto`    |

##### CODABAR Specific Properties

| Property        | Description          | Values             | Default |
| --------------- | -------------------- | ------------------ | ------- |
| `startstopCode` | Start/stop character | `A`, `B`, `C`, `D` | `A`     |

##### GS1 DataBar (RSS) Specific Properties

| Property    | Description                 | Values                  | Default         |
| ----------- | --------------------------- | ----------------------- | --------------- |
| `model`     | RSS model type              | `RSS14Standard`, others | `RSS14Standard` |
| `column`    | Number of columns           | Number                  | `4`             |
| `autoAdd01` | Automatically add 01 prefix | `true`, `false`         | `true`          |

##### PDF417 Specific Properties

| Property   | Description            | Values                          | Default    |
| ---------- | ---------------------- | ------------------------------- | ---------- |
| `model`    | PDF417 model type      | `standard`, `truncate`, `micro` | `standard` |
| `width`    | Width of each module   | String with units               | `0.8pt`    |
| `aspect`   | Width to height ratio  | Number                          | `3`        |
| `row`      | Number of rows         | `auto` or Number                | `auto`     |
| `column`   | Number of columns      | `auto` or Number                | `auto`     |
| `eccLevel` | Error correction level | `auto`, `0`-`8`                 | `auto`     |
| `joint`    | Joint characters       | Number                          | `1`        |

##### DataMatrix Specific Properties

| Property   | Description       | Values                | Default  |
| ---------- | ----------------- | --------------------- | -------- |
| `model`    | DataMatrix model  | `square`, `rectangle` | `square` |
| `cellSize` | Size of each cell | String with units     | `1.6pt`  |
| `macro`    | Macro type        | `none`, `05`, `06`    | `none`   |
| `fnc01`    | Include FNC1      | `true`, `false`       | `false`  |
| `joint`    | Joint characters  | Number                | `1`      |

##### MaxiCode Specific Properties

| Property | Description      | Values             | Default |
| -------- | ---------------- | ------------------ | ------- |
| `model`  | MaxiCode model   | `2`, `3`, `4`, `5` | `4`     |
| `joint`  | Joint characters | Number             | `1`     |

Example of a QR code with specific properties:

```yaml
- type: barcode
  barcodeType: qr
  data: "https://example.com"
  cellSize: 3 # Medium (1.6pt)
  errorCorrection: H
  model: 2
  version: auto
```

Example of a CODE128 barcode:

```yaml
- type: barcode
  barcodeType: code128
  data: "ABC12345"
  barWidth: 0.8pt
  humanReadable: true
  checkDigit: true
```

Example of a DataMatrix barcode:

```yaml
- type: barcode
  barcodeType: datamatrix
  data: "Product ID: 12345"
  cellSize: 1.6pt
  model: square
```

### 4.5 Group Objects

Group objects contain other objects and establish a flexible layout system for their children.

```yaml
- type: group
  id: header
  name: header_container # Optional: Name for the group, maps to objectName attribute
  x: 10
  y: 5
  width: auto # Optional: auto (default) or fixed width in points
  height: auto # Optional: auto (default) or fixed height in points

  # Container layout properties (only applicable to groups)
  direction: row # row, column, row-reverse, column-reverse
  justify: between # start, end, center, between, around, evenly
  align: center # start, end, center, stretch
  gap: 10 # spacing between items
  padding: 5 # internal padding within the group
  wrap: false # whether items wrap to next line/column

  objects: # Children of this group
    - type: text
      content: "Title"
      name: title_text # Named text element within the group
      # No x/y needed - automatically placed by layout
      font: Helsinki
      size: 14
    - type: image
      source: "logo.png"
      name: logo_image # Named image element within the group
      width: 20
      height: 20
```

#### 4.5.1 Container Layout Properties

These properties apply only to groups and define how their child elements are arranged:

| Property    | Description                      | Values                                                  | Default | Applies to  |
| ----------- | -------------------------------- | ------------------------------------------------------- | ------- | ----------- |
| `direction` | Main axis direction              | `row`, `column`, `row-reverse`, `column-reverse`        | `row`   | Groups only |
| `justify`   | Alignment along main axis        | `start`, `end`, `center`, `between`, `around`, `evenly` | `start` | Groups only |
| `align`     | Default alignment for cross axis | `start`, `end`, `center`, `stretch`                     | `start` | Groups only |
| `gap`       | Spacing between items            | Number                                                  | 0       | Groups only |
| `padding`   | Internal padding within group    | Number or object with top/right/bottom/left             | 0       | Groups only |
| `wrap`      | Whether items wrap to next line  | `true`, `false`                                         | `false` | Groups only |

These properties establish the layout container's behavior, similar to CSS flexbox's container properties.

#### 4.5.2 Item Layout Properties

These properties can be applied to any object (text, image, barcode, or group) to control how it behaves within its parent group's layout:

```yaml
- type: text
  content: "Override parent's alignment"
  # Item layout properties - can be used on any object
  align: end # Override parent's cross-axis alignment for just this item
  grow: 1 # Take up available space (like flex-grow)
  shrink: 1 # Shrink if needed (like flex-shrink)
  basis: auto # Base size before growing/shrinking
  order: 2 # Ordering within the flex container
```

| Property | Description                        | Values                              | Default        | Applies to |
| -------- | ---------------------------------- | ----------------------------------- | -------------- | ---------- |
| `align`  | Override cross-axis alignment      | `start`, `end`, `center`, `stretch` | parent's align | Any object |
| `grow`   | How much item can grow             | Number                              | 0              | Any object |
| `shrink` | How much item can shrink           | Number                              | 1              | Any object |
| `basis`  | Base size before growing/shrinking | Number or `auto`                    | `auto`         | Any object |
| `order`  | Ordering within flex container     | Number                              | 0              | Any object |

These properties allow individual items to override or adjust how they participate in their parent container's layout, similar to CSS flexbox's item properties.

#### 4.5.3 How Container and Item Properties Work Together

The flex layout system works on two levels:

1. **Container Level** (groups): Define the overall layout direction and rules

   - `direction` determines if items are arranged horizontally or vertically
   - `align` sets the default cross-axis alignment for all children
   - `justify` determines spacing along the main axis
   - `gap` controls spacing between items

2. **Item Level** (any object): Controls how an individual item behaves
   - `align` can override the parent's default cross-axis alignment
   - `grow`/`shrink`/`basis` control how an item sizes relative to siblings
   - `order` changes where an item appears visually regardless of code order

For example, if a group has `align: center`, all its children will be centered vertically (in row direction). But any child can override this with its own `align` property.

### 4.6 Container Objects

Container objects are a special type of organization element that behave similarly to groups but with one key distinction: they don't create a group element in the output XML.

```yaml
- type: container
  id: header_section
  # Container layout properties (same as groups)
  direction: row
  justify: between
  align: center
  gap: 10

  objects: # Children of this container
    - type: text
      content: "Title"
      font: Helsinki
      size: 14
    - type: image
      source: "logo.png"
      width: 20
      height: 20
```

#### 4.6.1 Container vs. Group

The key differences between containers and groups:

| Feature                   | Container | Group |
| ------------------------- | --------- | ----- |
| Creates XML element       | No        | Yes   |
| Adds visual box in output | No        | Yes   |
| Adds border options       | No        | Yes   |
| Can have background color | No        | Yes   |
| Layout functionality      | Yes       | Yes   |
| Positioning children      | Yes       | Yes   |

Containers are "virtual" elements that exist only in the YAML file, not in the final LBX output. They serve as organizational tools to:

1. Group related elements for easier YAML organization
2. Apply layout properties (direction, justify, align) to a set of elements
3. Avoid creating unnecessary group elements in the output XML

#### 4.6.2 When to Use Containers vs. Groups

Use a **container** when:

- You want to organize and lay out elements in your YAML
- You don't need a visible box or background in the final label
- You want to minimize the XML output size and complexity

Use a **group** when:

- You need a visible containing box with borders in the final label
- You want to set a background color for a set of elements
- You need to treat multiple elements as a single entity in the final label

#### 4.6.3 Container Properties

Containers support the same layout properties as groups:

| Property    | Description                      | Values                                                  | Default |
| ----------- | -------------------------------- | ------------------------------------------------------- | ------- |
| `direction` | Main axis direction              | `row`, `column`, `row-reverse`, `column-reverse`        | `row`   |
| `justify`   | Alignment along main axis        | `start`, `end`, `center`, `between`, `around`, `evenly` | `start` |
| `align`     | Default alignment for cross axis | `start`, `end`, `center`, `stretch`                     | `start` |
| `gap`       | Spacing between items            | Number                                                  | 0       |
| `padding`   | Layout padding (not visual)      | Number or object with top/right/bottom/left             | 0       |
| `wrap`      | Whether items wrap to next line  | `true`, `false`                                         | `false` |

The padding in containers is used only for layout calculations and doesn't create visual padding in the output.

## 5. Positioning System

### 5.1 Absolute Positioning

Objects can be positioned using absolute coordinates from the label origin (top-left corner):

```yaml
- type: text
  content: "Positioned Text"
  x: 10 # X-coordinate from left edge
  y: 20 # Y-coordinate from top edge
```

Both x and y coordinates are optional. If omitted, they default to 0. When objects are inside a group with layout settings, the x and y coordinates are overridden by the layout engine.

### 5.2 Flexbox Layout

Groups can use a flexbox-inspired layout system to automatically position and align their child elements:

#### 5.2.1 Row Layout (Horizontal)

```yaml
- type: group
  name: row_container
  x: 10
  y: 5
  direction: row
  justify: between # Spaces items evenly with space between them
  align: center # Centers items vertically
  gap: 5 # 5pt gap between items
  objects:
    - type: text
      name: left_text
      content: "Left"
    - type: text
      name: center_text
      content: "Center"
      grow: 1 # This item will grow to take up available space
      align: start # Override: aligns to top instead of center
    - type: text
      name: right_text
      content: "Right"
```

In this example:

- The group defines a row direction with items spaced evenly between them
- All items are vertically centered by default (group's `align: center`)
- The middle "Center" text overrides the alignment with its own `align: start`
- The middle text also takes up any extra space with `grow: 1`

#### 5.2.2 Column Layout (Vertical)

```yaml
- type: group
  x: 10
  y: 5
  direction: column
  justify: start # Items start at the top
  align: center # Centers items horizontally
  gap: 8 # 8pt gap between items
  objects:
    - type: text
      content: "Top"
    - type: image
      source: "middle.png"
      width: 20
      height: 20
      align: start # Left align this image, overriding the center alignment
    - type: text
      content: "Bottom"
```

In this example:

- The group defines a column layout with items starting at the top
- All items are horizontally centered by default
- The middle image overrides this with `align: start` to left-align itself

### 5.3 Auto-Sizing and Content Adaptation

The format supports various methods to automatically size and adapt content:

#### 5.3.1 Auto-Adjusting Label Dimensions

The label itself can automatically adjust its dimensions based on content:

```yaml
size: 24mm
width: auto # Automatically determine width based on content
length: auto # Automatically determine length based on content
orientation: landscape
```

This is useful for variable content labels where the dimensions cannot be predetermined.

#### 5.3.2 Text Wrapping and Fitting

Text objects can automatically wrap and adapt to their containers:

```yaml
- type: text
  content: "This is a long text that will automatically wrap to fit within the specified width"
  x: 10
  y: 20
  wrap: 100 # Wrap text at 100 points width
  shrink: true # Reduce font size if needed to fit
```

#### 5.3.3 Auto-Sizing Groups

Groups can dynamically adjust their dimensions based on their content:

```yaml
- type: group
  x: 10
  y: 5
  direction: column
  height: auto # Automatically size height to content (default if omitted)
  width: auto # Automatically size width to content (default if omitted)
  objects:
    - type: text
      content: "First line"
    - type: text
      content: "Second line"
    # Group dimensions will adjust to fit all content
```

When `width` and/or `height` are set to `auto` or omitted, the group will automatically calculate its dimensions based on the positions and sizes of its child elements, ensuring it properly contains all children with appropriate padding.

## 6. Style Inheritance

Child objects can inherit style properties from their parent groups. For example, a text object inside a group with alignment settings will inherit those settings unless explicitly overridden with its own style properties.

## 7. Examples

### 7.1 Basic Label with Text (Canonical Structure)

```yaml
size: 12mm
width: 90mm
orientation: landscape

objects:
  - type: text
    name: title_text
    content: "Hello World"
    x: 10
    y: 12
    font: Helsinki
    size: 14
    bold: true
    align: center
```

### 7.2 Product Label with Flexbox Layout (Canonical Structure)

```yaml
size: 24mm
width: 100mm
orientation: landscape

objects:
  - type: group
    id: header
    x: 10
    y: 5
    direction: column
    align: center
    gap: 5
    objects:
      - type: text
        content: "PRODUCT LABEL"
        font: Helsinki
        size: 16
        bold: true

      - type: text
        content: "Serial Number"
        size: 10
        italic: true

  - type: group
    id: product_info
    x: 10
    y: 40
    direction: column
    align: center
    gap: 5
    objects:
      - type: barcode
        barcodeType: qr
        data: "https://example.com/product"
        size: 30

      - type: text
        content: "Scan for details"
        size: 8
        align: center
```

### 7.3 Product Label with Flat Structure and Flexbox Layout

```yaml
# Label properties
size: 24mm
width: 100mm
orientation: landscape

# Root level layout properties (container properties)
direction: column
align: center
gap: 10

objects:
  # Header with centered content
  - type: text
    content: "PRODUCT LABEL"
    font: Helsinki
    size: 16
    bold: true

  # Middle section with item-specific alignment override
  - type: text
    content: "Serial Number"
    size: 10
    italic: true
    align: end # Item property: overrides the root container's center alignment

  # Bottom QR code that appears first in order
  - type: barcode
    barcodeType: qr
    data: "https://example.com/product"
    size: 30
    order: -1 # Item property: makes this appear before other elements
```

This example demonstrates:

1. Root level container properties for overall layout
2. An individual text element with its own alignment that overrides the container's alignment
3. A barcode that uses the `order` property to change its visual position

### 7.4 Mixed Positioning Systems

```yaml
size: 24mm
width: 100mm
orientation: landscape

objects:
  # Absolutely positioned element
  - type: text
    content: "Fixed Position"
    x: 70
    y: 10
    size: 8

  # Flex layout container
  - type: group
    x: 10
    y: 20
    direction: row # Container property
    justify: between # Container property
    align: center # Container property
    objects:
      - type: text
        content: "Left"
      - type: text
        content: "Center"
        grow: 1 # Item property: grows to fill available space
        align: center # Item property: maintains center alignment
      - type: text
        content: "Right"
```

### 7.5 Auto-Sizing Label with Wrapped Text

```yaml
# Label with auto-sizing and text wrapping
size: 12mm
width: auto
length: auto
orientation: landscape

objects:
  - type: group
    x: 5
    y: 5
    direction: column
    align: center
    gap: 5
    height: auto
    width: auto
    objects:
      - type: text
        content: "This is a long title that will automatically wrap"
        size: 10
        bold: true
        wrap: 80 # Wrap at 80 points width

      - type: text
        content: "Additional information that will also wrap to fit within the constraints of the label width"
        size: 8
        wrap: 80

      - type: barcode
        barcodeType: qr
        data: "https://example.com/auto-sizing-demo"
        size: 25
```

### 7.6 QR Code Examples

#### QR Code Size Options

The `size` parameter for QR codes controls the cell size (or module size) and can be specified in multiple ways:

**Point sizes** (exact sizes):

- `"0.8pt"` - Small
- `"1.2pt"` - Medium Small
- `"1.6pt"` - Medium
- `"2pt"` - Medium Large
- `"2.4pt"` - Large

**Numeric indexes** (1-5):

- `1` - Small (0.8pt)
- `2` - Medium Small (1.2pt)
- `3` - Medium (1.6pt)
- `4` - Medium Large (2pt) - Default
- `5` - Large (2.4pt)

**String aliases** (case insensitive):

- `"small"` or `"sm"` - Small (0.8pt)
- `"medium small"`, `"mediumsmall"`, `"smallmedium"`, `"mdsm"`, or `"smmd"` - Medium Small (1.2pt)
- `"medium"` or `"md"` - Medium (1.6pt)
- `"medium large"`, `"mediumlarge"`, `"largemedium"`, `"mdlg"`, or `"lgmd"` - Medium Large (2pt)
- `"large"` or `"lg"` - Large (2.4pt)

The default is Medium Large (2pt) which provides good readability for most QR codes.

#### QR Code Examples

```yaml
# Basic QR code with default settings (Medium Large cell size - 2pt)
- type: qr
  data: https://example.com
  x: 10
  y: 10
  size: 40 # Overall size of the QR code area

# QR code with small cell size
- type: qr
  data: https://example.com
  x: 10
  y: 10
  size: sm # Small (0.8pt)

# QR code with medium cell size and high error correction
- type: qr
  data: https://example.com
  x: 10
  y: 10
  size: md # Medium (1.6pt)
  correction: H

# QR code with explicit point size
- type: qr
  data: https://example.com
  x: 10
  y: 10
  size: "2.4pt" # Large (same as size: 5)
  correction: M

# QR code with fixed version
- type: qr
  data: https://example.com
  x: 10
  y: 20
  size: 3 # Medium (1.6pt)
  version: 5
```

### 7.7 Label with Root-Level Layout Properties

```yaml
# Label properties
size: 12mm
width: 90mm
orientation: landscape

# Layout properties at root level (container properties)
direction: column # Main axis is vertical
align: center # Center items horizontally
justify: center # Center vertically within available space
gap: 10 # 10pt spacing between items

# Objects directly at root level, arranged by the layout
- type: text
  content: "Centered Title"
  size: 16
  bold: true

- type: text
  content: "Subtitle"
  size: 12
  italic: true
  align: start # Item property: override to left-align this item

- type: barcode
  barcodeType: qr
  data: "https://example.com"
  size: 40
  grow: 1 # Item property: this element will take extra space

- type: text
  content: "Scan for more info"
  size: 10
```

This example shows:

1. Root-level container properties creating an implicit group
2. Automatic vertical arrangement with centered alignment
3. Individual items overriding specific aspects of the layout
4. Mixed content types (text and barcode) sharing the same layout rules

### 7.8 Complex Example with All Features/Properties

```yaml
# Label properties
size: 24mm
width: auto
length: auto
orientation: landscape
margin: 8
background: "#F8F8F8"
color: "#000000"

# Root level layout properties
direction: column
align: center
gap: 12
padding: 10

# Header section
- type: group
  id: header_section
  direction: row
  justify: between
  align: center
  gap: 5
  width: auto
  height: 40
  objects:
    # Logo image with transparency
    - type: image
      source: "company_logo.png"
      width: 35
      height: 35
      monochrome: true
      transparency: true # Uses white by default, but can specify a different color here to enable transparency for a specific color

    # Title with multiple formatting options
    - type: text
      content: "PRODUCT SPECIFICATION"
      font: Helsinki
      size: 18
      bold: true
      align: center
      color: "#1A5276"

# Basic text with no optional properties
- type: text
  content: "Reference ID: 12345"

# Middle content section (nested groups)
- type: group
  id: content_section
  direction: row
  justify: start
  align: start
  gap: 15
  wrap: true
  objects:
    # Left column - Product image and details
    - type: group
      id: product_visual
      direction: column
      align: center
      gap: 8
      width: 150
      objects:
        # Product image
        - type: image
          source: "product.png"
          width: 120
          height: 100
          monochrome: false

        # Nested group with two text elements
        - type: group
          id: product_details
          direction: column
          align: center
          gap: 3
          padding: 5
          objects:
            - type: text
              content: "Model XYZ-42"
              size: 12
              bold: true

            - type: text
              content: "Manufacturing Date: 2023-04-15"
              size: 8
              italic: true

        # QR code with specific settings
        - type: barcode
          barcodeType: qr
          data: "https://example.com/products/xyz-42"
          size: 60
          errorCorrection: H
          model: 2
          cellSize: 2
          margin: true
          version: 5

    # Right column - Specifications
    - type: group
      id: specifications
      direction: column
      align: start
      gap: 5
      width: 200
      objects:
        - type: text
          content: "Technical Specifications"
          size: 14
          bold: true
          underline: true

        # Long wrapped text
        - type: text
          content: |
            This product meets all regulatory requirements and has been tested for durability under extreme conditions. Please refer to the manual for detailed instructions on operation and maintenance.
          size: 10
          wrap: 190

        # Specifications as a nested list
        - type: group
          direction: column
          gap: 2
          objects:
            - type: text
              content: "• Dimensions: 10cm × 15cm × 5cm"
              size: 9

            - type: text
              content: "• Weight: 250g"
              size: 9

            - type: text
              content: "• Power: 5V DC"
              size: 9

            - type: text
              content: "• Battery Life: 24 hours"
              size: 9

# Footer with flexible layout
- type: group
  id: footer
  direction: row
  justify: between
  align: center
  gap: 10
  padding: 5
  objects:
    - type: text
      content: "P/N: 123-456-789"
      size: 10

    - type: text
      content: "Rev. A"
      size: 10
      align: center
      grow: 1

    - type: barcode
      barcodeType: code128
      data: "123456789"
      size: 40
      humanReadable: true

    - type: text
      content: "Page 1/1"
      size: 10
      align: right
      vertical: false
```

This comprehensive example showcases:

1. **Label Properties**: Custom size, auto-sizing, margins, and colors
2. **Root-Level Layout**: Using column direction with centered alignment
3. **Multiple Groups**: With different layout directions (row, column)
4. **Nested Groups**: Including a product details group within a product visual group
5. **Text Formatting**: Various font sizes, styles (bold, italic, underline), and alignments
6. **Multiline Text**: Using the block scalar format with wrapping
7. **Images**: Two different images with different monochrome and transparency settings
8. **Barcodes**: Both QR code with detailed settings and Code 128 with human-readable text
9. **Flex Layouts**: Using justify, align, gap, and wrap properties
10. **Minimal Text**: A basic text element with only required properties
11. **Complex Structure**: Multiple levels of nesting with different layout strategies

## 8. File Handling

### 8.1 Uncompressed Format (`.lbx.yml`)

The uncompressed format consists of a single YAML file with references to external image files. Image paths should be relative to the YAML file.

### 8.2 Compressed Format (`.lbx.yml.zip`)

The compressed format is a ZIP archive containing:

- The YAML file at the root level, named `label.yml`
- All referenced images in an `images/` directory

This format allows for easy distribution of labels with all required resources.

## 9. Conversion Process

The conversion from LBX YAML to Brother LBX format involves:

1. Parsing the YAML file
2. Resolving all relative positions into absolute coordinates
3. Generating the complex XML structure required by LBX
4. Converting and packaging images in the appropriate format
5. Creating the final ZIP archive with the proper structure
