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

### 2.3 Units

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

| Property      | Description       | Values                                        |
| ------------- | ----------------- | --------------------------------------------- |
| `size`        | Tape width        | `3.5mm`, `6mm`, `9mm`, `12mm`, `18mm`, `24mm` |
| `orientation` | Label orientation | `landscape`, `portrait`                       |

### 3.2 Optional Properties

| Property     | Description            | Default   |
| ------------ | ---------------------- | --------- |
| `width`      | Label width (in mm)    | "auto"    |
| `margin`     | Additional margin      | 0         |
| `background` | Label background color | "#FFFFFF" |
| `color`      | Label text color       | "#000000" |

Note: `width` is technically the length when `orientation` is `landscape`. When `orientation` is `portrait`, `width` is the height.

### 3.3 Layout Properties at Root Level

The root level can include layout properties that apply to all objects within the `objects` array, effectively making the label itself act as an implicit group container. This eliminates the need for a wrapper group when aligning all objects.

```yaml
# Label with root layout properties
size: 24mm
width: 100mm
orientation: landscape
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

| Property    | Description                     | Values                                                  | Default |
| ----------- | ------------------------------- | ------------------------------------------------------- | ------- |
| `direction` | Main axis direction             | `row`, `column`, `row-reverse`, `column-reverse`        | `row`   |
| `justify`   | Alignment along main axis       | `start`, `end`, `center`, `between`, `around`, `evenly` | `start` |
| `align`     | Alignment along cross axis      | `start`, `end`, `center`, `stretch`                     | `start` |
| `gap`       | Spacing between items           | Number                                                  | 0       |
| `padding`   | Internal padding within label   | Number or object with top/right/bottom/left             | 0       |
| `wrap`      | Whether items wrap to next line | `true`, `false`                                         | `false` |

These properties function identically to those available for group objects, except they apply to all objects within the `objects` array.

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

| Property | Description                                                        | Default  |
| -------- | ------------------------------------------------------------------ | -------- |
| `type`   | Required: The type of object (text, image, barcode, group)         | Required |
| `id`     | Optional: Unique identifier for reference                          | None     |
| `name`   | Optional: Name for the object, maps to objectName attribute in XML | None     |
| `x`      | X-coordinate from left edge                                        | 0        |
| `y`      | Y-coordinate from top edge                                         | 0        |

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
- type: richtext
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

| Property          | Description                     | Values                                           | Default |
| ----------------- | ------------------------------- | ------------------------------------------------ | ------- |
| `size`            | Barcode size                    | Number                                           | 30      |
| `errorCorrection` | QR error correction level       | `L`, `M`, `Q`, `H`                               | `M`     |
| `model`           | QR code model                   | `1`, `2`                                         | `2`     |
| `cellSize`        | Size of each QR code cell       | Number                                           | auto    |
| `margin`          | Include quiet zone/margin       | `true`, `false`                                  | `true`  |
| `version`         | QR code version (size/capacity) | `auto`, `1`-`40`                                 | `auto`  |
| `protocol`        | Barcode type                    | `qr`, `code39`, `code128`, `ean13`, `ean8`, etc. | `qr`    |
| `humanReadable`   | Show human-readable text        | `true`, `false`                                  | `false` |

#### 4.4.2 QR Code Error Correction Levels

QR codes support different error correction levels that affect their ability to be read when damaged:

| Level | Name           | Description                                                       |
| ----- | -------------- | ----------------------------------------------------------------- |
| `L`   | Low (7%)       | Recovers approximately 7% of damaged data. Highest data capacity. |
| `M`   | Medium (15%)   | Recovers approximately 15% of damaged data. Default level.        |
| `Q`   | Quartile (25%) | Recovers approximately 25% of damaged data.                       |
| `H`   | High (30%)     | Recovers approximately 30% of damaged data. Most robust.          |

The higher the error correction level, the larger the QR code will be for the same data.

#### 4.4.3 Barcode Types

The LBX format supports various barcode types:

| Type         | Description              | Additional Properties |
| ------------ | ------------------------ | --------------------- |
| `qr`         | QR Code (default)        | `errorCorrection`     |
| `code39`     | Code 39                  | `humanReadable`       |
| `code128`    | Code 128                 | `humanReadable`       |
| `ean13`      | EAN-13                   | n/a                   |
| `ean8`       | EAN-8                    | n/a                   |
| `upc-a`      | UPC-A                    | n/a                   |
| `upc-e`      | UPC-E                    | n/a                   |
| `codabar`    | Codabar                  | `humanReadable`       |
| `itf`        | ITF (Interleaved 2 of 5) | `humanReadable`       |
| `pdf417`     | PDF417 (2D barcode)      | n/a                   |
| `datamatrix` | Data Matrix (2D barcode) | n/a                   |

### 4.5 Group Objects

Group objects contain other objects and establish a flexible layout system for their children.

```yaml
- type: group
  id: header
  name: header_container # Optional: Name for the group, maps to objectName attribute
  x: 10
  y: 5
  direction: row # row, column, row-reverse, column-reverse
  justify: between # start, end, center, between, around, evenly
  align: center # start, end, center, stretch
  gap: 10 # spacing between items
  padding: 5 # internal padding within the group
  wrap: false # whether items wrap to next line/column
  width: auto # auto or fixed width in points
  height: auto # auto or fixed height in points
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

#### 4.5.1 Group Layout Properties

| Property    | Description                     | Values                                                  | Default |
| ----------- | ------------------------------- | ------------------------------------------------------- | ------- |
| `direction` | Main axis direction             | `row`, `column`, `row-reverse`, `column-reverse`        | `row`   |
| `justify`   | Alignment along main axis       | `start`, `end`, `center`, `between`, `around`, `evenly` | `start` |
| `align`     | Alignment along cross axis      | `start`, `end`, `center`, `stretch`                     | `start` |
| `gap`       | Spacing between items           | Number                                                  | 0       |
| `padding`   | Internal padding within group   | Number or object with top/right/bottom/left             | 0       |
| `wrap`      | Whether items wrap to next line | `true`, `false`                                         | `false` |
| `width`     | Group width                     | Number or "auto"                                        | "auto"  |
| `height`    | Group height                    | Number or "auto"                                        | "auto"  |

#### 4.5.2 Item-Specific Flex Properties

Individual items in a group can override layout properties:

```yaml
- type: text
  content: "Override group alignment"
  flex:
    align: end # Override alignment just for this item
    grow: 1 # Take up available space (like flex-grow)
    shrink: 1 # Shrink if needed (like flex-shrink)
    basis: auto # Base size before growing/shrinking
    order: 2 # Ordering within the flex container
```

| Property | Description                        | Values                              | Default        |
| -------- | ---------------------------------- | ----------------------------------- | -------------- |
| `align`  | Override cross-axis alignment      | `start`, `end`, `center`, `stretch` | parent's align |
| `grow`   | How much item can grow             | Number                              | 0              |
| `shrink` | How much item can shrink           | Number                              | 1              |
| `basis`  | Base size before growing/shrinking | Number or `auto`                    | `auto`         |
| `order`  | Ordering within flex container     | Number                              | 0              |

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
    - type: text
      name: right_text
      content: "Right"
```

This creates a row with three evenly spaced text elements, centered vertically.

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
    - type: text
      content: "Bottom"
```

This creates a column with items centered horizontally, with 8pt spacing between them.

#### 5.2.3 Individual Item Overrides

```yaml
- type: group
  direction: row
  align: center
  justify: start
  objects:
    - type: text
      content: "Regular"
    - type: text
      content: "Grows to fill space"
      flex:
        grow: 1
        align: start # Aligns to top
    - type: text
      content: "Last but shown first"
      flex:
        order: -1 # Changes display order
```

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
  height: auto # Automatically size height to content
  width: 120 # Keep fixed width
  objects:
    - type: text
      content: "First line"
    - type: text
      content: "Second line"
    # Group height will adjust to fit all content
```

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
# Label properties at root level
size: 24mm
width: 100mm
orientation: landscape

# Main container group that uses flex layout
- type: group
  x: 5
  y: 5
  direction: column
  justify: between
  gap: 10
  padding: 5
  objects:
    # Header section
    - type: group
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

    # Middle section with logo and barcode side by side
    - type: group
      direction: row
      justify: center
      gap: 15
      align: center
      objects:
        - type: image
          source: "logo.png"
          width: 25
          height: 25
          monochrome: true

        - type: barcode
          barcodeType: qr
          data: "https://example.com/product"
          size: 30

    # Footer with additional info
    - type: text
      content: "Scan for details"
      size: 8
      align: center
```

### 7.4 Label with Mixed Positioning Systems

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
    direction: row
    justify: between
    align: center
    objects:
      - type: text
        content: "Left"
      - type: text
        content: "Center"
        flex:
          grow: 1
          align: center
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

```yaml
# Basic QR code with default settings
- type: barcode
  barcodeType: qr
  data: "https://example.com"
  x: 10
  y: 10
  size: 40

# QR code with high error correction
- type: barcode
  barcodeType: qr
  data: "https://example.com"
  x: 60
  y: 10
  size: 50
  errorCorrection: H

# QR code with specific cell size
- type: barcode
  barcodeType: qr
  data: "https://example.com"
  x: 120
  y: 10
  size: 60
  errorCorrection: M
  cellSize: 2

# QR code with fixed version
- type: barcode
  barcodeType: qr
  data: "https://example.com"
  x: 190
  y: 10
  size: 80
  errorCorrection: Q
  version: 5
```

### 7.7 Label with Root-Level Layout Properties

```yaml
# Label properties
size: 12mm
width: 90mm
orientation: landscape

# Layout properties at root level (acts as an implicit group)
direction: column
align: center
justify: center
gap: 10

# Objects directly at root level, arranged by the layout
- type: text
  content: "Centered Title"
  size: 16
  bold: true

- type: text
  content: "Subtitle"
  size: 12
  italic: true

- type: barcode
  barcodeType: qr
  data: "https://example.com"
  size: 40

- type: text
  content: "Scan for more info"
  size: 10
```

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
      transparency: true
      transparency_color: "#FFFFFF"

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
      flex:
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
