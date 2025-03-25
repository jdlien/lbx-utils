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

## 6. Conversion Requirements

When converting between label sizes:

1. Update `paper` element: width, height, margins, format
2. Update `backGround` element: y, height
3. Update all object Y-positions according to the new label size's margin requirements
4. Scale object dimensions proportionally using the scaling factors
5. Reposition objects based on new dimensions
6. Adjust font sizes based on scaling factors
7. Maintain or update XML version/generator attributes

## 7. Common Issues and Solutions

### 7.1 Size Recognition Problems

- **Issue**: Application shows incorrect size despite `format` code change
- **Solution**: Verify all attributes in the `paper` element match the expected values for the target size
- **Solution**: Ensure all object Y-positions have been updated to match the margin of the target size

### 7.2 Object Visibility

- **Issue**: Elements positioned outside printable area
- **Solution**: Ensure objects stay within the proper margins for each tape size

### 7.3 TZ Tape Compatibility

- **Issue**: The label size may be restricted to the label sizes supported by the model of printer specified in the printerID="30256" and/or printerName="Brother PT-P710BT" attributes. E.g., for 24mm tape, you'll need a larger printer like the Brother PT-P710BT.

- **Solution**: Update the printerName to a larger printer model.

## 8. Implementation Notes

For optimal compatibility:

1. Extract attributes from blank templates for each size
2. Update all related attributes together, not just width and format
3. Consider XML version and generator attributes
4. Test with both older and newer P-touch Editor versions
5. Update metadata in prop.xml when making significant changes
6. Ensure object Y-positions match the expected values for the target tape size

---

This specification is based on analysis of LBX files across different tape widths and should be updated as additional insights are discovered.
