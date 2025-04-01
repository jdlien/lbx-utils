<!-- @format -->

# Brother P-touch LBX Format Label Size Specification

## 1. Introduction

This document outlines the structure and parameters related to label sizing in Brother P-touch LBX format files. The LBX format is a ZIP archive containing XML files that define label layouts, with `label.xml` being the primary configuration file.

## 2. File Structure

```
LBX File (ZIP archive)
├── label.xml (Primary configuration)
├── prop.xml (Metadata and properties)
└── [image files] (Optional)
```

## 3. Property Metadata (prop.xml)

The `prop.xml` file contains metadata about the label file, including creation and modification dates, author information, and general properties.

### 3.1 Key XML Elements

```xml
<meta:properties xmlns:meta="http://schemas.brother.info/ptouch/2007/lbx/meta"
                xmlns:dc="http://purl.org/dc/elements/1.1/"
                xmlns:dcterms="http://purl.org/dc/terms/">
    <meta:appName>P-touch Editor</meta:appName>
    <dc:title></dc:title>
    <dc:subject></dc:subject>
    <dc:creator>user@example.com</dc:creator>
    <meta:keyword></meta:keyword>
    <dc:description></dc:description>
    <meta:template></meta:template>
    <dcterms:created>2016-10-08T09:40:30Z</dcterms:created>
    <dcterms:modified>2024-12-13T03:54:36Z</dcterms:modified>
    <meta:lastPrinted></meta:lastPrinted>
    <meta:modifiedBy>user@example.com</meta:modifiedBy>
    <meta:revision>3</meta:revision>
    <meta:editTime>166</meta:editTime>
    <meta:numPages>1</meta:numPages>
    <meta:numWords>0</meta:numWords>
    <meta:numChars>0</meta:numChars>
    <meta:security>0</meta:security>
</meta:properties>
```

### 3.2 Important Metadata Elements

| Element          | Description                              | Impact on Label                 |
| ---------------- | ---------------------------------------- | ------------------------------- |
| meta:appName     | The application used to create the label | May affect compatibility        |
| dc:creator       | Author email or username                 | For informational purposes      |
| dcterms:created  | Creation timestamp (ISO format)          | For tracking purposes           |
| dcterms:modified | Last modification timestamp (ISO format) | For version tracking            |
| meta:revision    | Version number of the document           | Increments with edits           |
| meta:numPages    | Number of pages/sheets in the label      | Typically 1 for standard labels |

### 3.3 XML Namespaces

The prop.xml file uses three main namespaces:

- `xmlns:meta="http://schemas.brother.info/ptouch/2007/lbx/meta"` - Brother-specific metadata
- `xmlns:dc="http://purl.org/dc/elements/1.1/"` - Dublin Core metadata standard
- `xmlns:dcterms="http://purl.org/dc/terms/"` - Dublin Core terms

## 4. Label Size Parameters

### 4.1 Size Categories

Brother P-touch labels come in several standard widths of TZe tape:

- 9mm / 0.35in (M size)
- 12mm / 0.47in (Standard)
- 18mm / 0.71in (Wide)
- 24mm / 0.94in (Extra Wide)

### 4.2 Coordinate System

Brother labels use a point-based (pt) coordinate system where:

- The origin (0,0) is at the top-left corner of the printable area
- In a typical "landscape" orientation, the X-axis runs along the length of the label and Y-axis is the width/height
- The tape width (9mm, 12mm, etc.) corresponds to the Y-dimension in the coordinate system

### 4.3 Key XML Elements

The `label.xml` file contains the elements for the label's contents, sizing, reference to images, and other metadata.

For purposes of specifying the label size, there are two critical elements:

- `style:paper`: Specifies the size of the label's printable area.
  - `width`: The width of the chosen label tape media (9mm, 12mm, 18mm, 24mm). In landscape orientation, this is actually the height of the label.
  - `height`: In landscape orientation, this is actually the width of the label (the length that gets printed).
  - `marginRight`/`marginLeft`: In landscape, this is the vertical margin, which varies by tape size.
  - `marginTop`/`marginBottom`: In landscape, this is the horizontal margin.
  - `format`: The format code for the chosen label tape media. (258=9mm, 259=12mm, 260=18mm, 261=24mm)
- `style:backGround`: Specifies the size of the label's printable area.
  - `y`: The starting y-coordinate of the background. (Starts just inside the margin, typically)
  - `height`: The height of the printable area.

These attributes change between different label sizes:

### style:paper Element Attributes

```xml
<style:paper media="0" width="XXpt" height="YYpt" marginLeft="Xpt" marginRight="Xpt" marginTop="5.6pt" marginBottom="5.6pt" orientation="landscape" autoLength="true" monochromeDisplay="true" printColorDisplay="false" printColorsID="0" paperColor="#FFFFFF" paperInk="#000000" split="1" format="FFF" backgroundTheme="0" printerID="XXXXX" printerName="Brother PT-XXXX"/>
```

| Attribute              | 9mm    | 12mm   | 18mm   | 24mm  |
| ---------------------- | ------ | ------ | ------ | ----- |
| width                  | 25.6pt | 33.6pt | 51.2pt | 68pt  |
| marginLeft/marginRight | 2.8pt  | 2.8pt  | 3.2pt  | 8.4pt |
| format                 | 258    | 259    | 260    | 261   |

### style:backGround Element Attributes

```xml
<style:backGround x="5.6pt" y="Y.Ypt" width="Wpt" height="Hpt" brushStyle="NULL" brushId="0" userPattern="NONE" userPatternId="0" color="#000000" printColorNumber="1" backColor="#FFFFFF" backPrintColorNumber="0"/>
```

| Attribute | 9mm   | 12mm  | 18mm   | 24mm   |
| --------- | ----- | ----- | ------ | ------ |
| y         | 2.8pt | 2.8pt | 3.2pt  | 8.4pt  |
| height    | 20pt  | 28pt  | 44.8pt | 51.2pt |

## 5. Object Positioning

### 5.1 Y-Position Adjustments

Object positioning is critical for proper label recognition and rendering. When changing label sizes, both the background and objects must have their y-coordinates properly updated.

| Label Size | Background Y | Text Object Y | Image Object Y |
| ---------- | ------------ | ------------- | -------------- |
| 9mm        | 2.8pt        | 7.1pt         | 2.8pt          |
| 12mm       | 2.8pt        | 7.1pt         | 2.8pt          |
| 18mm       | 3.2pt        | 7.5pt         | 3.2pt          |
| 24mm       | 8.4pt        | 12.7pt        | 8.4pt          |

When converting label sizes, it's essential to update both:

1. Object position Y-values (in `pt:objectStyle` elements)
2. Image positioning Y-values (in both `pt:objectStyle` and `image:orgPos` elements)

The Y-coordinate patterns show that:

- 9mm and 12mm share the same Y-positions
- 18mm has slightly increased Y-positions (+0.4pt)
- 24mm has significantly increased Y-positions (+5.6pt compared to 9/12mm)

This corresponds directly to the margin values in the `style:paper` element.

## 6. Font Size Adjustments

### 6.1 XML Elements and Attributes

When adjusting font sizes in a label, several XML elements and attributes need to be updated to maintain proper text rendering:

1. Main Font Element (`text:fontExt`):

   ```xml
   <text:fontExt size="14pt" orgSize="50.4pt"/>
   ```

   - `size`: The target font size in points
   - `orgSize`: Should be 3.6 times the font size (e.g., 14pt → 50.4pt)

2. Text Style Element (`text:textStyle`):

   ```xml
   <text:textStyle orgPoint="14pt"/>
   ```

   - `orgPoint`: Should match the target font size

3. String Item Font Elements (`text:stringItem/text:fontExt`):
   ```xml
   <text:stringItem>
     <text:fontExt size="14pt" orgSize="50.4pt"/>
   </text:stringItem>
   ```
   - `size`: Should match the target font size
   - `orgSize`: Should be 3.6 times the font size

### 6.2 Important Considerations

1. **Ratio Preservation**: The `orgSize` attribute should always be 3.6 times the font size. This ratio is consistent across all font elements.

2. **Multiple Font Elements**: Each text element may have multiple font elements that need updating:

   - The main `text:fontExt` element
   - The `text:textStyle` element's `orgPoint`
   - Any `text:stringItem` elements with their own `fontExt` elements

3. **Consistency**: All font size-related attributes should be updated together to maintain proper text rendering and spacing.

4. **Default Values**: If no font size is specified, the default is typically 9pt with an `orgSize` of 32.4pt.

### 6.3 Example

Here's a complete example of a text element with all font-related attributes properly set for 14pt:

```xml
<text:text>
  <text:fontExt size="14pt" orgSize="50.4pt"/>
  <text:textStyle orgPoint="14pt"/>
  <text:stringItem>
    <text:fontExt size="14pt" orgSize="50.4pt"/>
    <text:string>Sample Text</text:string>
  </text:stringItem>
</text:text>
```

## 7. Conversion Requirements

When converting between label sizes:

1. Update `paper` element: width, height, margins, format
2. Update `backGround` element: y, height
3. Update all object Y-positions according to the new label size's margin requirements
4. Scale object dimensions proportionally using the scaling factors
5. Reposition objects based on new dimensions
6. Adjust font sizes based on scaling factors
7. Maintain or update XML version/generator attributes

## 8. Common Issues and Solutions

### 8.1 Size Recognition Problems

- **Issue**: Application shows incorrect size despite `format` code change
- **Solution**: Verify all attributes in the `paper` element match the expected values for the target size
- **Solution**: Ensure all object Y-positions have been updated to match the margin of the target size

### 8.2 Object Visibility

- **Issue**: Elements positioned outside printable area
- **Solution**: Ensure objects stay within the proper margins for each tape size

### 8.3 TZ Tape Compatibility

- **Issue**: The label size may be restricted to the label sizes supported by the model of printer specified in the printerID="30256" and/or printerName="Brother PT-P710BT" attributes. E.g., for 24mm tape, you'll need a larger printer like the Brother PT-P710BT.

- **Solution**: Update the printerName to a larger printer model.

### 8.4 Blank Labels

- **Issue**: Creating blank labels (with no text or images) requires the proper XML structure
- **Solution**: Ensure that the `pt:objects` element is correctly included even when empty
- **Solution**: Maintain proper XML namespaces, attributes, and formatting as provided in templates
- **Solution**: Use the Brother P-Touch Editor's default generator value: `generator="com.brother.PtouchEditor"`
- **Solution**: Set the `meta:appName` value to match the generator: `com.brother.PtouchEditor`

## 9. Implementation Notes

For optimal compatibility:

1. Extract attributes from blank templates for each size
2. Update all related attributes together, not just width and format
3. Consider XML version and generator attributes
4. Test with both older and newer P-touch Editor versions
5. Update metadata in prop.xml when making significant changes
6. Ensure object Y-positions match the expected values for the target tape size

## 10. Critical XML Structure Requirements

The LBX file format has several critical requirements that must be followed to ensure compatibility with Brother P-Touch Editor:

### 10.1 Element Order and Hierarchy

The order of elements in the XML is extremely important and strictly enforced by the P-Touch Editor. Changing the order will cause the application to crash.

For text elements, the correct order is:

1. objectStyle (with pen, brush, expanded child elements)
2. ptFontInfo (with logFont and fontExt child elements)
3. textControl
4. textAlign
5. textStyle
6. data (containing the actual text content)
7. stringItem (one or more elements for text formatting)

For image elements, the correct order is:

1. objectStyle (with pen, brush, expanded child elements)
2. imageStyle
3. imageData (containing the image path)

### 10.2 Text Content Requirements

1. **Text Content Handling**: When creating text elements, the text content must be properly enclosed within the `<pt:data>` element as its content, not as an attribute:

   ```xml
   <!-- CORRECT -->
   <pt:data>Your text here</pt:data>

   <!-- INCORRECT -->
   <pt:data text="Your text here" />
   ```

2. **String Item Length**: Each `stringItem` element must have a `charLen` attribute that precisely matches the length of the corresponding text segment. The sum of all `charLen` values must exactly equal the total length of the text in the `data` element.

3. **Data Before StringItem**: The `data` element must always come before any `stringItem` elements in the XML structure.

### 10.3 Image Content Requirements

1. **Image Path**: The image path should be stored as the content of the `imageData` element:

   ```xml
   <!-- CORRECT -->
   <image:imageData originalName="image.png">image.png</image:imageData>

   <!-- INCORRECT -->
   <image:imageData originalName="image.png" path="image.png" />
   ```

2. **Image References**: All images referenced in the XML must also be included in the LBX file (ZIP archive).

### 10.4 Text Formatting and Positioning Requirements

1. **Text Control Mode**: For text elements to open properly in P-Touch Editor, several critical settings must be correct:

   - Text control mode should be `AUTOLEN` instead of `FREE`
   - Auto Line Feed should be `false` to match the P-Touch Editor's default behavior
   - Vertical alignment should be `TOP` rather than `CENTER`

2. **Font Settings**: The following font settings are required for compatibility:

   - Font name should be `Helsinki` (P-Touch Editor's default font)
   - pitchAndFamily value should be `2` rather than the more common `34`
   - Font size should be `21.7pt` with corresponding `orgSize` of `28.8pt`

3. **Object Positioning**: For text objects, positioning must precisely match the background element:

   - The `x` coordinate should be exactly `5.6pt` (matching background's x)
   - The `y` coordinate should exactly match the background y-coordinate
   - The width should be `34.4pt` to match the background width
   - The height should match the background height

4. **Pen Width**: Use `0.5pt` for both widthX and widthY values in pen elements

5. **Object Name**: For text objects, use a consistent naming scheme with `Text1` rather than random identifiers

### 10.5 XML Generation Issues

When programmatically generating LBX files, be aware of these common issues:

1. **XML Library Compatibility**: Some XML libraries may handle text content for elements differently. When using libraries like lxml, you may need to implement workarounds to ensure text content is properly set.

2. **Namespace Handling**: All elements must include proper namespace prefixes (pt:, style:, text:, image:, etc.). Missing or incorrect namespaces will cause the editor to crash.

3. **Empty Elements**: Self-closing tags for elements that should contain text content can cause issues. Use explicit opening and closing tags for elements like `data` and `imageData`.

4. **Special Characters**: Ensure proper XML escaping for special characters in text content.

Following these strict requirements will help ensure that LBX files can be successfully opened in the Brother P-Touch Editor software without crashing.

---

This specification is based on analysis of LBX files across different tape widths and should be updated as additional insights are discovered.

## 10. XML Formatting Requirements

### 10.1 Single-Line XML Content

For compatibility with Brother P-Touch Editor, all XML content (except the XML declaration) **MUST** be on a single line with no line breaks or unnecessary whitespace:

- The XML declaration line should be separate: `<?xml version="1.0" encoding="UTF-8"?>`
- All remaining XML content must follow on a single line with no line breaks
- While the XML structure should be minified, text content should be preserved as-is (including whitespace)
- Failure to follow these formatting rules can cause the P-Touch Editor to crash or fail to open files

### 10.2 Example

```xml
<?xml version="1.0" encoding="UTF-8"?>
<pt:document xmlns:pt="http://schemas.brother.info/ptouch/2007/lbx/main" version="1.5" generator="com.brother.PtouchEditor"><pt:body...</pt:body></pt:document>
```

Note how all content after the XML declaration is on a single line.

### 10.3 Implementation

When generating LBX files programmatically:

1. Generate properly formatted XML with appropriate indentation for development
2. Before writing to the LBX file, remove all line breaks and unnecessary whitespace
3. Ensure text content within elements is preserved exactly as intended
4. Keep proper XML escaping for special characters

This formatting requirement applies to both `label.xml` and `prop.xml` files within the LBX archive.

---

This specification is based on analysis of LBX files across different tape widths and should be updated as additional insights are discovered.

## Image Handling

### Image Format Requirements

The Brother P-Touch LBX format has specific considerations for image handling:

1. **Image File Format**:

   - BMP (Bitmap) files are commonly used within LBX archives and provide the most reliable compatibility
   - PNG files should also work well, especially in newer versions of P-Touch Editor
   - Other formats (JPEG, etc.) may work but have less consistent support
   - While BMP format is traditionally used, both BMP and PNG are supported formats for LBX files

2. **Filename Pattern**: Image files typically use unique filenames:

   - BMP files often follow a pattern like `Object[uuid].bmp` (e.g., `Object1234.bmp`)
   - PNG files can retain their original names or use a similar naming pattern

3. **XML Structure for Images**: Images must be structured correctly in the XML for proper display:
   - The `<image:image>` element should include a proper `<image:imageStyle>` element
   - The `fileName` attribute of `imageStyle` should reference the image file in the archive
   - The `originalName` attribute should contain the original filename

### Required Image Elements

The following structure is necessary for proper image rendering:

```xml
<image:image>
  <pt:objectStyle x="10pt" y="12.7pt" width="20pt" height="20pt" backColor="#FFFFFF" backPrintColorNumber="0" ropMode="COPYPEN" angle="0" anchor="TOPLEFT" flip="NONE">
    <pt:pen style="NULL" widthX="0.5pt" widthY="0.5pt" color="#000000" printColorNumber="1"/>
    <pt:brush style="NULL" color="#000000" printColorNumber="1" id="0"/>
    <pt:expanded objectName="Bitmap12ab" ID="0" lock="2" templateMergeTarget="LABELLIST" templateMergeType="NONE" templateMergeID="0" linkStatus="NONE" linkID="0"/>
  </pt:objectStyle>
  <image:imageStyle originalName="original.png" alignInText="NONE" firstMerge="true" IpName="" fileName="image.png">
    <image:transparent flag="false" color="#FFFFFF"/>
    <image:trimming flag="false" shape="RECTANGLE" trimOrgX="0pt" trimOrgY="0pt" trimOrgWidth="0pt" trimOrgHeight="0pt"/>
    <image:orgPos x="10pt" y="12.7pt" width="20pt" height="20pt"/>
    <image:effect effect="MONO" brightness="50" contrast="50" photoIndex="4"/>
    <image:mono operationKind="ERRORDIFFUSION" reverse="0" ditherKind="MESH" threshold="128" gamma="100" ditherEdge="0" rgbconvProportionRed="30" rgbconvProportionGreen="59" rgbconvProportionBlue="11" rgbconvProportionReversed="0"/>
  </image:imageStyle>
</image:image>
```

### Image Conversion Notes

When generating LBX files with images:

1. **Mode Conversion**: For maximum compatibility, images in LA, RGBA, or other non-RGB modes should be converted to RGB before inclusion in the LBX file.

2. **Image Positioning**: The position information must be consistent between:

   - The `objectStyle` element's `x`, `y`, `width`, and `height` attributes
   - The nested `image:orgPos` element within `imageStyle`

3. **Background Handling**: For transparent images, a white background should be applied when using file formats that don't fully support transparency in the P-Touch Editor.
