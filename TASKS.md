# LBX-Utils Project Tasks

This document outlines the tasks required to complete the `lbxyml2lbx.py` conversion tool in order to fully comply with the `lbx.yml-spec.md` specification.

## Current Functionality

- [x] Basic CLI structure setup (imports from .cli module)
- [x] Command entry point (`app()` function call in main block)
- [x] CLI options for input/output files
- [x] CLI options for verbosity and debugging
- [x] Text dimension calculation methods

## Core Functionality

- [x] YAML Parser

  - [x] Parse .lbx.yml files
  - [x] Validate against specification
  - [x] Error handling for invalid YAML
  - [x] Support for file paths with spaces

- [x] LBX Generator
  - [x] Generate label.xml structure
  - [x] Generate prop.xml structure
  - [x] Create proper LBX directory structure
  - [x] Package as .lbx zip file

## Label Properties

- [x] Basic Label Properties

  - [x] Size (tape width)
  - [x] Width/length
  - [x] Orientation
  - [x] Margin
  - [x] Background/color

- [x] Root-Level Layout Properties
  - [x] Direction (row, column)
  - [x] Justify (start, end, center, between, around, evenly)
  - [x] Align (start, end, center, stretch)
  - [x] Gap
  - [x] Padding
  - [x] Wrap

## Object Handling

- [x] Text Objects

  - [x] Basic text rendering
  - [x] Font properties (font, size, bold, italic, underline)
  - [x] Text alignment
  - [x] Vertical text orientation
  - [x] Text wrapping
  - [x] Rich text formatting (fragments array)
  - [x] Markdown-inspired syntax

- [x] Image Objects

  - [x] Image embedding
  - [x] Width/height handling
  - [x] Monochrome conversion
  - [x] Transparency handling

- [x] Barcode Objects

  - [x] QR code generation
    - [x] Error correction levels
    - [ ] Cell size options
    - [x] Margin/version handling
  - [x] Other barcode types (code39, code128, ean13, etc.)
  - [x] Human-readable text options

- [x] Group Objects

  - [x] Nested object structure
  - [x] Width/height calculation
  - [x] Style inheritance

- [x] Container Objects
  - [x] Virtual grouping (no XML element creation)
  - [x] Layout functionality without visual representation

## Layout System

- [x] Absolute Positioning

  - [x] X/Y coordinate system
  - [x] Default positioning

- [x] Flexbox Layout

  - [x] Row layout (horizontal)
  - [x] Column layout (vertical)
  - [x] Container layout properties
    - [x] Direction
    - [x] Justify
    - [x] Align
    - [x] Gap
    - [x] Padding
    - [x] Wrap
  - [x] Item layout properties
    - [x] Individual align
    - [x] Grow/shrink/basis
    - [x] Order

- [x] Auto-Sizing
  - [x] Auto-adjusting label dimensions
  - [x] Text wrapping and fitting
  - [x] Auto-sizing groups

## File Handling

- [x] Uncompressed Format (.lbx.yml)

  - [x] Read YAML with external image references
  - [x] Relative path resolution

- [ ] Compressed Format (.lbx.yml.zip)
  - [ ] Extract YAML and images from zip
  - [ ] Handle internal directory structure

## Testing and Documentation

- [x] Unit Tests

  - [x] YAML parsing tests
  - [x] XML generation tests
  - [x] Layout system tests
  - [x] End-to-end conversion tests

- [x] Example Files

  - [x] Create example .lbx.yml files for all features
  - [x] Compare with actual Brother LBX outputs

- [ ] Documentation
  - [ ] CLI usage documentation
  - [ ] API documentation
  - [x] Example usage in README
  - [ ] Error message explanations

## Command Line Interface

- [x] Basic Options

  - [x] Input file path
  - [x] Output file path
  - [x] Verbose/quiet modes

- [x] Advanced Options
  - [ ] Validation only mode
  - [ ] Force overwrite option
  - [x] Image conversion options
  - [x] Debug output

## Integration and Convenience Features

- [ ] Additional Utilities

  - [ ] Preview generation (image of resulting label)
  - [ ] Web interface for conversion
  - [ ] Watch mode for development

- [x] Error Handling and Reporting

  - [x] Descriptive error messages
  - [x] Line number references for YAML errors
  - [ ] Suggestions for fixing common issues

- [ ] Performance Optimizations
  - [ ] Caching for repeated conversions
  - [ ] Parallel processing for multiple files
