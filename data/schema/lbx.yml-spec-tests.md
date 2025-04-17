# LBX YAML Format Implementation Checklist

This document provides a comprehensive checklist of all features specified in the LBX YAML format (`lbx.yml-spec.md`). Use this to track implementation status and test coverage across the codebase.

## Status Key

- [ ] Not implemented
- [~] Partially implemented
- [x] Fully implemented
- [T] Tested

## 1. File Format

### 1.1 File Extensions

- [ ] `.lbx.yml` - Standard uncompressed format with external image references
- [ ] `.lbx.yml.zip` - Compressed archive with YAML file and referenced images

### 1.2 Basic Structure

- [ ] Root level label properties
  - [T] `size` (tape width - 3.5mm, 6mm, 9mm, 12mm, 18mm, 24mm)
  - [T] `orientation` (landscape, portrait)
  - [T] `width` (label width in mm or "auto")
  - [T] `margin` (additional margin for ends of tape, left and right in landscape, top and bottom in portrait)
  - [ ] `background` (label background color)
  - [ ] `color` (label text color)
- [ ] `objects` array containing all visual elements
- [ ] Canonical structure validation

## 2. Units

### 2.1 Unit Handling

- [T] Points (pt) as default unit
- [T] Millimeters (mm) conversion support
- [ ] Inches (in) conversion support
- [T] Automatic unit conversion
- [T] Support for numeric values without units (defaulting to pt)

### 2.2 Positioning System

- [T] (0,0) positioned at top-left corner
- [T] Positive X moves right
- [T] Positive Y moves down
- [ ] Positioning is relative to area inside margins instead of the whole label

## 3. Label Properties

### 3.1 Required Properties

- [T] `size` (tape width - 3.5mm, 6mm, 9mm, 12mm, 18mm, 24mm)

### 3.2 Optional Properties

- [T] `width` (label width in mm or "auto")
- [T] `orientation` (label orientation - defaults to "landscape")
- [T] `margin` (additional margin)
- [x] `background` (label background color)
- [x] `color` (label text color)

### 3.3 Root Level Layout Properties

- [ ] `direction` (row, column, row-reverse, column-reverse)
- [ ] `justify` (start, end, center, between, around, evenly)
- [T] `align` (start, end, center, stretch)
- [ ] `gap` (spacing between items)
- [ ] `padding` (internal padding)
- [ ] `wrap` (whether items wrap to next line)

## 4. Objects

### 4.1 Common Object Properties

- [ ] `type` - Required object type
- [ ] `id` - Optional unique identifier
- [ ] `name` - Optional object name (maps to objectName in XML)
- [ ] `x` - X-coordinate positioning
- [ ] `y` - Y-coordinate positioning

### 4.2 Text Objects

#### 4.2.1 Basic Text Properties

- [ ] `content` - Text content
- [ ] `font` - Font family
- [ ] `size` - Font size
- [ ] `bold` - Bold formatting
- [ ] `italic` - Italic formatting
- [ ] `underline` - Underline formatting
- [ ] `align` - Text alignment (left, center, right)
- [ ] `vertical` - Vertical text orientation
- [ ] `color` - Text color
- [ ] `wrap` - Text wrapping behavior
- [ ] `shrink` - Reduce font size to fit

#### 4.2.2 Multiline Text Content

- [ ] Literal block scalar format (`|`)
- [ ] Folded block scalar format (`>`)
- [ ] Quoted strings with escape characters
- [ ] Block scalars with indentation indicators
- [ ] Block scalars with chomping indicators

#### 4.2.3 Rich Text Formatting

- [ ] Text fragments array with mixed formatting
- [ ] Markdown-inspired syntax
  - [ ] Bold formatting (`**text**` or `__text__`)
  - [ ] Italic formatting (`*text*` or `_text_`)
  - [ ] Underline formatting (`++text++`)
  - [ ] Strikethrough formatting (`~~text~~`)
  - [ ] Combined formatting styles

### 4.3 Image Objects

- [ ] `source` - Path to image file
- [ ] `width` - Image width
- [ ] `height` - Image height
- [ ] `monochrome` - Convert to monochrome
- [ ] `transparency` - Enable transparency
- [ ] `transparency_color` - Color to treat as transparent

### 4.4 Barcode Objects

- [ ] `barcodeType` - Type of barcode
- [ ] `data` - Data to encode
- [ ] `size` - Barcode size
- [ ] `errorCorrection` - QR error correction level
- [ ] `model` - QR code model
- [ ] `cellSize` - Size of each QR code cell
- [ ] `margin` - Include quiet zone/margin
- [ ] `version` - QR code version
- [ ] `protocol` - Barcode type
- [ ] `humanReadable` - Show human-readable text

#### 4.4.1 Barcode Types Support

- [ ] `qr` - QR Code
- [ ] `code39` - Code 39
- [ ] `code128` - Code 128
- [ ] `ean13` - EAN-13
- [ ] `ean8` - EAN-8
- [ ] `upc-a` - UPC-A
- [ ] `upc-e` - UPC-E
- [ ] `codabar` - Codabar
- [ ] `itf` - ITF (Interleaved 2 of 5)
- [ ] `pdf417` - PDF417 (2D barcode)
- [ ] `datamatrix` - Data Matrix (2D barcode)

### 4.5 Group Objects

- [ ] Container with other objects
- [ ] Width and height properties (fixed or auto)
- [ ] Layout properties (direction, justify, align, etc.)
- [ ] Nested groups
- [ ] Background and border support

#### 4.5.1 Container Layout Properties

- [ ] `direction` - Main axis direction
- [ ] `justify` - Alignment along main axis
- [ ] `align` - Default alignment for cross axis
- [ ] `gap` - Spacing between items
- [ ] `padding` - Internal padding
- [ ] `wrap` - Whether items wrap to next line

#### 4.5.2 Item Layout Properties

- [ ] `align` - Override cross-axis alignment
- [ ] `grow` - How much item can grow
- [ ] `shrink` - How much item can shrink
- [ ] `basis` - Base size before growing/shrinking
- [ ] `order` - Ordering within flex container

### 4.6 Container Objects

- [ ] Virtual organization without XML representation
- [ ] Layout functionality without creating a visual box
- [ ] Same layout properties as groups
- [ ] Positioning children

## 5. Positioning System

### 5.1 Absolute Positioning

- [ ] Objects positioned with absolute coordinates
- [ ] Default to 0 for omitted x/y values

### 5.2 Flexbox Layout

- [x] Row Layout (Horizontal)
- [x] Column Layout (Vertical)
- [x] Rich positioning options (justify, align, etc.)
- [x] Proper handling of nested layouts
- [x] Using x/y values as offsets when root-level layout is applied

### 5.3 Auto-Sizing and Content Adaptation

- [ ] Auto-adjusting label dimensions
- [ ] Text wrapping and fitting
- [ ] Auto-sizing groups based on content

## 6. Style Inheritance

- [ ] Child objects inherit style from parent groups
- [ ] Override inheritance with explicit properties

## 7. File Handling

- [ ] Uncompressed format (`.lbx.yml`)
- [ ] Compressed format (`.lbx.yml.zip`)
- [ ] Image path resolution (relative to YAML file)

## 8. Layout Engine Implementation

### 8.1 Basic Layout Algorithm

- [x] Flexbox-inspired layout engine
- [x] Proper handling of padding
- [~] Proper calculation of item dimensions
  - [ ] Item dimensions are calculated but text is still fairly inaccurate
- [T] Row layout implementation
- [T] Column layout implementation

### 8.2 Alignment Implementation

- [x] Cross-axis alignment (start, end, center, stretch)
- [T] Main-axis justification (start, end, center, between, around, evenly)
- [x] Reverse direction support
- [x] Gap support between items

### 8.3 Nested Layout Support

- [x] Parent-child coordinate system
- [x] Recursive layout application
- [T] Proper positioning of nested groups

### 8.4 Auto-Sizing

- [x] Auto-width and auto-height calculations
- [x] Content-based dimension calculations
- [ ] Text wrapping and fitting calculations

## Implementation Priorities

1. **High Priority**

   - Basic structure and validation
   - Text objects with basic properties
   - Image objects
   - Group objects with layout
   - Unit conversion (pt/mm)
   - Absolute positioning
   - Flexbox layout basics

2. **Medium Priority**

   - Barcode objects
   - Rich text formatting
   - Container objects
   - Auto-sizing
   - Style inheritance

3. **Low Priority**
   - Compressed format
   - Advanced QR code options
   - Advanced barcode types
   - Markdown syntax
