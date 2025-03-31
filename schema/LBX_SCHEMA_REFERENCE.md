<!-- @format -->

# Brother P-Touch LBX Schema Reference

This document provides a detailed reference for the Brother P-Touch LBX label format, based on analysis of multiple LBX templates including `8mm-vertical.lbx` and `4-up-smoking.lbx`.

## Overview

LBX files are ZIP archives containing at least two XML files:

- `label.xml`: Contains the actual label design and content
- `prop.xml`: Contains metadata about the label (creator, software, timestamps)

The `label.xml` file uses multiple XML namespaces to organize different aspects of the label design.

## Namespaces

The LBX format uses the following namespaces:

| Prefix  | Namespace                                           | Description                                  |
| ------- | --------------------------------------------------- | -------------------------------------------- |
| `pt`    | `http://schemas.brother.info/ptouch/2007/lbx/main`  | Main label elements                          |
| `text`  | `http://schemas.brother.info/ptouch/2007/lbx/text`  | Text objects and formatting                  |
| `draw`  | `http://schemas.brother.info/ptouch/2007/lbx/draw`  | Drawing elements (frames, symbols, polygons) |
| `image` | `http://schemas.brother.info/ptouch/2007/lbx/image` | Image elements (clipart, photos)             |

## Key Findings from Template Analysis

### Text Handling

1. **Vertical Text**:

   - Implemented using `text:textStyle vertical="true"`
   - Works best with `textControl control="LONGTEXTFIXED"` and `orientation="portrait"`
   - Found in `8mm-vertical.lbx` for narrow tape labels
   - Reverses meaning of horizontal/vertical alignment attributes

2. **Mixed Font Sizes**:

   - Multiple `stringItem` elements can have different font sizes within the same text block
   - Used in `4-up-smoking.lbx` to create visual hierarchy
   - Each `stringItem` needs its own `ptFontInfo` with correct settings

3. **Text Control Modes**:

   - `FREE`: Standard text flow with automatic wrapping
   - `LONGTEXTFIXED`: Used for vertical text, creates vertical flow
   - `FIXEDFRAME`: Constrains text to a fixed frame

4. **Line and Character Spacing**:
   - Line spacing can be adjusted: `lineSpace="-25"` for tighter spacing
   - Character spacing can also be adjusted for visual effect

### Label Layouts

1. **Multiple Copies**:

   - Split attribute: `paper split="4"` creates a 2×2 grid of identical labels
   - Used in `4-up-smoking.lbx`

2. **Orientation**:

   - `portrait` vs. `landscape` affects text flow and available space
   - `8mm-vertical.lbx` uses portrait orientation for narrow tape

3. **Positioning**:
   - Negative coordinates (e.g., `x="-1.3pt"`) allow elements to extend beyond margins
   - Useful for creating elements that bleed to the edge

### Graphical Elements

1. **Frames**:

   - `draw:frame` with `draw:frameStyle` creates decorative borders
   - Different styles available via category and style attributes

2. **Symbols**:

   - `draw:symbol` adds predefined symbols from Brother's library
   - Uses a font-based approach with font name and character code

3. **Polygons/Shapes**:

   - `draw:poly` creates custom shapes using coordinate points
   - Can specify arrow styles at beginning/end
   - Closed (polygon) or open (polyline) shapes

4. **Clipart**:
   - `image:clipart` adds built-in vector graphics
   - Organized by category and ID
   - Used in `4-up-smoking.lbx` for no-smoking symbols

## Critical Requirements for Text Editing

1. The `stringItem` elements MUST be present after the `pt:data` element
2. The sum of `charLen` values across all `stringItem` elements must equal the length of text in `pt:data`
3. Each `stringItem` must have its own `ptFontInfo` with `logFont` and `fontExt`
4. If a `stringItem` is removed, the corresponding text must be removed from `pt:data`
5. The order of elements is strictly important and must be preserved

## Element Details

### Text Elements

#### `text:text`

The main text object with the following structure:

```xml
<text:text>
  <pt:objectStyle/>
  <text:ptFontInfo>
    <text:logFont/>
    <text:fontExt/>
  </text:ptFontInfo>
  <text:textControl/>
  <text:textAlign/>
  <text:textStyle/>
  <pt:data>Actual text content</pt:data>
  <text:stringItem charLen="...">
    <text:ptFontInfo>...</text:ptFontInfo>
  </text:stringItem>
  <!-- More stringItem elements if needed -->
</text:text>
```

#### `text:textControl`

Controls text flow behavior:

- `control`: `FREE`, `LONGTEXTFIXED`, or `FIXEDFRAME`
- `clipFrame`: Whether to clip text that doesn't fit
- `shrink`: Whether to automatically reduce font size to fit
- `autoLF`: Whether to add automatic line breaks

#### `text:textStyle`

Controls text appearance:

- `vertical`: `true` for vertical text (top-to-bottom)
- `lineSpace`: Controls spacing between lines
- `charSpace`: Controls spacing between characters

### Drawing Elements

#### `draw:frame`

Creates a decorative frame:

```xml
<draw:frame>
  <pt:objectStyle/>
  <draw:frameStyle category="SIMPLE" style="2" stretchCenter="true"/>
</draw:frame>
```

#### `draw:symbol`

Inserts predefined symbols:

```xml
<draw:symbol>
  <pt:objectStyle/>
  <draw:symbolStyle fontName="PT Dingbats 1" code="33"/>
</draw:symbol>
```

#### `draw:poly`

Creates custom shapes:

```xml
<draw:poly>
  <pt:objectStyle/>
  <draw:polyStyle shape="POLYGON" arrowBegin="SQUARE" arrowEnd="SQUARE">
    <draw:polyOrgPos x="..." y="..." width="..." height="..."/>
    <draw:polyLinePoints points="2pt,59.3pt 6.8pt,56.5pt 7pt,62.5pt 4.3pt,62.5pt"/>
  </draw:polyStyle>
</draw:poly>
```

### Image Elements

#### `image:clipart`

Inserts built-in clipart:

```xml
<image:clipart>
  <pt:objectStyle/>
  <image:clipartStyle category="Sign" id="SignImage002" fillColor="#000000" drawMode="FILLRECT"/>
</image:clipart>
```

## Template Examples

### 8mm-vertical.lbx

Features:

- Vertical text for narrow tape
- Portrait orientation
- Decorative frame around text
- Warning symbol
- Custom arrow shape

### 4-up-smoking.lbx

Features:

- 4-up layout (2×2 grid of labels)
- "No Smoking" clipart symbols
- Mixed font sizes within text blocks
- Tight line spacing
- Pattern brush fills

## Best Practices

1. **Text Editing**:

   - Always maintain the total character count in `charLen` attributes
   - When replacing text, ensure the exact same number of characters or update `charLen` values
   - Keep the order of elements consistent

2. **Layout**:

   - Use appropriate orientation based on tape width
   - For narrow tapes, consider vertical text

3. **Complex Designs**:

   - Use multiple text objects instead of a single complex one
   - Leverage built-in symbols and clipart when possible

4. **Testing**:
   - Always test labels in the Brother P-Touch Editor software after editing
   - Verify text displays correctly and all elements maintain their positions
