# LBX Simplified Format Ideas

This document outlines four conceptual approaches for a simplified format that can be converted into the complex Brother P-touch LBX format. Each approach aims to make label creation more accessible while still providing the necessary flexibility for functional labels.

## 1. HTML-Inspired Format with Tailwind-like Classes

This approach leverages familiar HTML syntax with utility classes similar to Tailwind CSS for styling.

### Example:

```html
<lbx-label size="12mm" width="90mm" orientation="landscape">
  <text-object
    x="10pt"
    y="12pt"
    font="Helsinki"
    size="14pt"
    align="center"
    class="bold"
  >
    Hello World
  </text-object>
  <image-object
    src="logo.png"
    x="10pt"
    y="30pt"
    width="20pt"
    height="20pt"
    class="mono"
  />
  <barcode-object
    x="50pt"
    y="12pt"
    type="qr"
    data="https://example.com"
    size="30pt"
  />
</lbx-label>
```

### Benefits:

- Familiar syntax for web developers
- Classes for common style options (bold, italic, mono, etc.)
- Element naming clearly indicates purpose
- Position attributes for precise control
- Easy to add new features through new attributes

### Challenges:

- Requires a more complex parser than some alternatives
- May need to handle escaping of special characters

## 2. YAML-Based Configuration Format

This approach uses YAML's hierarchical structure to define label elements in a clean, readable format.

### Example:

```yaml
label:
  size: 12mm
  width: 90mm
  orientation: landscape

objects:
  - type: text
    content: Hello World
    position:
      x: 10pt
      y: 12pt
    style:
      font: Helsinki
      size: 14pt
      bold: true
      align: center

  - type: image
    source: logo.png
    position:
      x: 10pt
      y: 30pt
    style:
      width: 20pt
      height: 20pt
      monochrome: true

  - type: barcode
    data: https://example.com
    position:
      x: 50pt
      y: 12pt
    style:
      type: qr
      size: 30pt
```

### Benefits:

- Human-readable without special knowledge
- Hierarchical structure matches the conceptual model
- Easy to parse with existing YAML libraries
- Good for complex styles and nested properties
- Whitespace-friendly for readability

### Challenges:

- Less compact than some alternatives
- Strict indentation requirements

## 3. Markdown with Custom Extensions

This approach extends Markdown syntax with custom directives for label properties and elements.

### Example:

```md
---
label: 12mm
width: 90mm
orientation: landscape
---

# Text: Hello World {x=10pt y=12pt font=Helsinki size=14pt bold center}

![Logo](logo.png) {x=10pt y=30pt width=20pt height=20pt mono}

$QR: https://example.com {x=50pt y=12pt size=30pt}
```

### Benefits:

- Extremely readable even when not rendered
- Minimal syntax for common elements
- Intuitive for non-developers
- Works well in text editors
- Can utilize existing Markdown parsers with extensions

### Challenges:

- Less structured for machine parsing than alternatives
- May require special handling for complex attributes
- Could have ambiguity in certain edge cases

## 4. JSON Schema with Simplified Structure

This approach uses JSON's universal compatibility with a simplified schema designed specifically for label creation.

### Example:

```json
{
  "label": {
    "size": "12mm",
    "width": "90mm",
    "orientation": "landscape"
  },
  "elements": [
    {
      "type": "text",
      "content": "Hello World",
      "x": "10pt",
      "y": "12pt",
      "font": "Helsinki",
      "size": "14pt",
      "style": ["bold", "center"]
    },
    {
      "type": "image",
      "source": "logo.png",
      "x": "10pt",
      "y": "30pt",
      "width": "20pt",
      "height": "20pt",
      "style": ["mono"]
    },
    {
      "type": "barcode",
      "barcodeType": "qr",
      "data": "https://example.com",
      "x": "50pt",
      "y": "12pt",
      "size": "30pt"
    }
  ]
}
```

### Benefits:

- Universal compatibility with programming languages
- Structured and predictable format
- Simple to validate with JSON schema
- Easy to generate programmatically
- Strong typing possible

### Challenges:

- Less human-friendly for direct editing
- More verbose than some alternatives
- Requires careful string escaping

## 5. Extended YAML Format with Object Grouping

Building on the YAML approach, this extension adds support for object grouping and relative positioning.

### Example:

```yaml
label:
  size: 24mm
  width: 100mm
  orientation: landscape

objects:
  - type: group
    id: header
    position:
      x: 10
      y: 5
    style:
      align: center
    objects:
      - type: text
        content: PRODUCT LABEL
        position:
          x: 0 # Relative to parent group
          y: 0
        style:
          font: Helsinki
          size: 16
          bold: true

      - type: text
        content: Serial Number
        position:
          x: 0
          y: 18
        style:
          size: 10
          italic: true

  - type: group
    id: product_info
    position:
      # Position relative to another object
      relative_to: header
      position: below
      margin: 10
    objects:
      - type: barcode
        barcodeType: qr
        data: https://example.com/product
        position:
          x: 0
          y: 0
        style:
          size: 30

      - type: text
        content: Scan for details
        position:
          relative_to: last # References previous object
          position: below
          margin: 5
        style:
          size: 8
          align: center

  # Object outside of any group
  - type: image
    source: logo.png
    position:
      x: 70
      y: 10
    style:
      width: 20
      height: 20
      monochrome: true
```

### Benefits:

- Hierarchical grouping of related objects
- Relative positioning between objects and groups
- Inheritance of common styles from parent groups
- Simple keywords for positioning (below, right_of, etc.)
- Cleaner organization of complex labels
- Can move entire sections by changing a single coordinate

### Challenges:

- More complex to implement in the converter
- Requires resolving relative positions in the correct order
- May need multiple passes to calculate final coordinates

## Implementation Considerations

Regardless of the chosen format, the implementation should account for:

1. **Automatic Positioning**: Allow relative positioning using keywords like "below", "right-of", etc.

2. **Default Styles**: Provide sensible defaults for common label types and orientations

3. **Template System**: Support for saving and reusing templates

4. **Validation**: Robust validation to catch errors before conversion

5. **Extensibility**: Ability to add new features without breaking existing labels

6. **Helper Functions**: For common operations like centering, distributing elements evenly, etc.

## Conversion Process

The conversion from the simplified format to LBX would follow these steps:

1. Parse the simplified format
2. Validate all parameters against known constraints
3. Apply default values for missing properties
4. Calculate absolute positions for any relative positioning
5. Generate the complex XML structure required by LBX
6. Package the XML and any images into the ZIP archive format

Each approach has its own strengths and would be suitable for different use cases. The HTML-inspired format might be best for developers, the YAML approach for configuration-heavy environments, the Markdown extension for documentation-oriented users, and the JSON schema for programmatic generation.
