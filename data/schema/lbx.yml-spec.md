# LBX YAML Format Specification

## 1. Introduction

The LBX YAML format (`.lbx.yml`) is a simplified representation for Brother P-touch label designs that can be converted into the complex LBX format. This specification defines the structure, properties, and behaviors of this YAML-based format.

## 2. File Format

### 2.1 File Extensions

- `.lbx.yml` - Standard uncompressed format with external image references
- `.lbx.yml.zip` - Compressed archive containing the YAML file and referenced images

### 2.2 Basic Structure

The format consists of a YAML document with two approaches to structure: canonical (using sections) or flat (direct objects).

#### Canonical Structure

The canonical structure uses distinct sections for label properties and objects:

```yaml
# Label properties section
size: 24mm
width: 100mm
orientation: landscape

# Objects section
objects:
  - type: text
    content: "Hello World"
    # ...

  - type: image
    source: "logo.png"
    # ...
```

In this structure, label properties are at the root level, and all objects are within the `objects` array.

### 2.3 Units

All measurements are in points (pt) unless otherwise specified. The unit suffix is optional in the YAML file and will be automatically added during conversion.

Common units that can be explicitly specified:

- `mm` - Millimeters for tape size (e.g., `12mm`)
- `pt` - Points (default unit if not specified)

### 2.4 Alternative Flat Structure

For simplicity and to reduce indentation levels, objects can also be defined directly at the root level alongside label properties:

```yaml
# Label properties
size: 24mm
width: 100mm
orientation: landscape

# Objects directly at root level
- type: text
  content: 'Hello World'
  position:
    x: 10
    y: 12
  # ...

- type: image
  source: 'logo.png'
  position:
    x: 10
    y: 30
  # ...
```

The parser will identify array elements at the root level as objects, while other properties at the root level are treated as label properties. This flat structure is functionally identical to the canonical structure but requires less indentation.

## 3. Label Properties

The `label` section defines the global properties of the label.

```yaml
label:
  size: 24mm # Tape size (9mm, 12mm, 18mm, 24mm)
  width: 100mm # Fixed width (or "auto" for automatic sizing)
  length: auto # Fixed length or "auto" for automatic sizing
  orientation: landscape # Label orientation (landscape, portrait)
  margin: 5 # Optional: Additional margin beyond the minimum
  background: "#FFFFFF" # Background color. This doesn't affect printing, but is shown in preview.
  color: "#000000" # Color of the label ink. Only affects preview.
```

### 3.1 Required Properties

| Property      | Description       | Values                        |
| ------------- | ----------------- | ----------------------------- |
| `size`        | Tape width        | `9mm`, `12mm`, `18mm`, `24mm` |
| `orientation` | Label orientation | `landscape`, `portrait`       |

### 3.2 Optional Properties

| Property     | Description            | Default   |
| ------------ | ---------------------- | --------- |
| `width`      | Label width (in mm)    | "auto"    |
| `margin`     | Additional margin      | 0         |
| `background` | Label background color | "#FFFFFF" |
| `color`      | Label text color       | "#000000" |

Note: `width` is technically the length when `orientation` is `landscape`. When `orientation` is `portrait`, `width` is the height.

## 4. Objects

The `objects` array contains all visual elements to be rendered on the label. Each object must have a `type` property that defines its behavior.

### 4.1 Common Object Properties

All objects support these common properties:

```yaml
- type: text # Required: Object type
  id: main_title # Optional: Unique identifier for reference, part of old idea for relative positioning
  x: 10 # X-coordinate from left edge (defaults to 0 if omitted)
  y: 20 # Y-coordinate from top edge (defaults to 0 if omitted)
  # Style properties vary by object type and are direct members of the object
```

### 4.2 Text Objects

Text objects display text content on the label.

```yaml
- type: text
  content: "Hello World" # Required: Text content
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

#### 4.2.1 Text-Specific Properties

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

| Property          | Description               | Values             | Default |
| ----------------- | ------------------------- | ------------------ | ------- |
| `size`            | Barcode size              | Number             | 30      |
| `errorCorrection` | QR error correction level | `L`, `M`, `Q`, `H` | `M`     |

### 4.5 Group Objects

Group objects contain other objects and establish a flexible layout system for their children.

```yaml
- type: group
  id: header
  x: 10
  y: 5
  layout:
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
      # No x/y needed - automatically placed by layout
      font: Helsinki
      size: 14
    - type: image
      source: "logo.png"
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
  x: 10
  y: 5
  layout:
    direction: row
    justify: between # Spaces items evenly with space between them
    align: center # Centers items vertically
    gap: 5 # 5pt gap between items
  objects:
    - type: text
      content: "Left"
    - type: text
      content: "Center"
    - type: text
      content: "Right"
```

This creates a row with three evenly spaced text elements, centered vertically.

#### 5.2.2 Column Layout (Vertical)

```yaml
- type: group
  x: 10
  y: 5
  layout:
    direction: column
    justify: start # Items start at the top
    align: center # Centers items horizontally
    gap: 8 # 8pt gap between items
  objects:
    - type: text
      content: "Top"
    - type: image
      source: "middle.png"
      style:
        width: 20
        height: 20
    - type: text
      content: "Bottom"
```

This creates a column with items centered horizontally, with 8pt spacing between them.

#### 5.2.3 Individual Item Overrides

```yaml
- type: group
  layout:
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
  layout:
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
    layout:
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
    layout:
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
  layout:
    direction: column
    justify: between
    gap: 10
    padding: 5
  objects:
    # Header section
    - type: group
      layout:
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
      layout:
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
    layout:
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
    layout:
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
