#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to explore the uharfbuzz API in version 0.48.0
"""

import sys
import os
import inspect

try:
    import uharfbuzz as hb
    print(f"uharfbuzz version: {hb.__version__}")
except ImportError:
    print("uharfbuzz is not installed")
    sys.exit(1)

# Print all functions and classes in the uharfbuzz module
print("\nAvailable attributes in uharfbuzz module:")
for name in dir(hb):
    if not name.startswith('_'):  # Skip private attributes
        attr = getattr(hb, name)
        if inspect.isclass(attr):
            print(f"Class: {name}")
            # Print methods of the class
            for method_name in dir(attr):
                if not method_name.startswith('_'):
                    try:
                        method = getattr(attr, method_name)
                        if inspect.isfunction(method) or inspect.ismethod(method):
                            print(f"  Method: {method_name}")
                        else:
                            print(f"  Attribute: {method_name}")
                    except Exception as e:
                        print(f"  Error accessing {method_name}: {e}")
        elif inspect.isfunction(attr):
            print(f"Function: {name}")
        else:
            print(f"Other: {name} (type: {type(attr).__name__})")

print("\nTesting Face creation:")
# Test different ways to create a Face
font_path = None

# Try to find a font file
possible_font_paths = [
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Times.ttc",
    "/System/Library/Fonts/Courier.ttc",
]

for path in possible_font_paths:
    if os.path.exists(path):
        font_path = path
        print(f"Found font: {font_path}")
        break

if not font_path:
    print("No font found, exiting")
    sys.exit(1)

# Test creating a blob
print("\nTesting Blob creation:")
blob = None

# Method 1: Direct instantiation
try:
    with open(font_path, 'rb') as f:
        font_data = f.read()
    print("Creating blob with direct instantiation: hb.Blob(font_data)")
    blob = hb.Blob(font_data)
    print(f"Success! Blob created: {blob}")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Using create method
try:
    with open(font_path, 'rb') as f:
        font_data = f.read()
    print("Creating blob with create method: hb.Blob.create(font_data)")
    if hasattr(hb.Blob, 'create'):
        blob = hb.Blob.create(font_data)
        print(f"Success! Blob created: {blob}")
    else:
        print("hb.Blob.create method does not exist")
except Exception as e:
    print(f"Error: {e}")

# Method 3: Using from_file_path
try:
    print("Creating blob with from_file_path method: hb.Blob.from_file_path(font_path)")
    if hasattr(hb.Blob, 'from_file_path'):
        blob = hb.Blob.from_file_path(font_path)
        print(f"Success! Blob created: {blob}")
    else:
        print("hb.Blob.from_file_path method does not exist")
except Exception as e:
    print(f"Error: {e}")

# Test Face creation
print("\nTesting Face creation:")
face = None

# Method 1: Direct instantiation
try:
    if blob:
        print("Creating face with direct instantiation: hb.Face(blob, 0)")
        face = hb.Face(blob, 0)
        print(f"Success! Face created: {face}")
    else:
        print("Cannot create face without blob")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Using create method
try:
    if blob:
        print("Creating face with create method: hb.Face.create(blob, 0)")
        if hasattr(hb.Face, 'create'):
            face = hb.Face.create(blob, 0)
            print(f"Success! Face created: {face}")
        else:
            print("hb.Face.create method does not exist")
    else:
        print("Cannot create face without blob")
except Exception as e:
    print(f"Error: {e}")

# Method 3: Using from_file_path
try:
    print("Creating face with from_file_path method: hb.Face.from_file_path(font_path, 0)")
    if hasattr(hb.Face, 'from_file_path'):
        face = hb.Face.from_file_path(font_path, 0)
        print(f"Success! Face created: {face}")
    else:
        print("hb.Face.from_file_path method does not exist")
except Exception as e:
    print(f"Error: {e}")

# Test Font creation
print("\nTesting Font creation:")
font = None

# Method 1: Direct instantiation
try:
    if face:
        print("Creating font with direct instantiation: hb.Font(face)")
        font = hb.Font(face)
        print(f"Success! Font created: {font}")
    else:
        print("Cannot create font without face")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Using create method
try:
    if face:
        print("Creating font with create method: hb.Font.create(face)")
        if hasattr(hb.Font, 'create'):
            font = hb.Font.create(face)
            print(f"Success! Font created: {font}")
        else:
            print("hb.Font.create method does not exist")
    else:
        print("Cannot create font without face")
except Exception as e:
    print(f"Error: {e}")

# Test Buffer creation
print("\nTesting Buffer creation:")
buf = None

# Method 1: Direct instantiation
try:
    print("Creating buffer with direct instantiation: hb.Buffer()")
    buf = hb.Buffer()
    print(f"Success! Buffer created: {buf}")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Using create method
try:
    print("Creating buffer with create method: hb.Buffer.create()")
    if hasattr(hb.Buffer, 'create'):
        buf = hb.Buffer.create()
        print(f"Success! Buffer created: {buf}")
    else:
        print("hb.Buffer.create method does not exist")
except Exception as e:
    print(f"Error: {e}")

# Test buffer methods
if buf:
    try:
        print("\nTesting buffer methods:")
        buf.add_str("Hello World")
        buf.guess_segment_properties()

        if font:
            print("Shaping text...")
            hb.shape(font, buf)

            # Try different ways to get glyph info
            print("\nTesting glyph position access:")
            try:
                print("Using buf.glyph_positions:")
                if hasattr(buf, 'glyph_positions'):
                    positions = buf.glyph_positions
                    print(f"Success! Found {len(positions)} positions")
                else:
                    print("buf.glyph_positions attribute does not exist")
            except Exception as e:
                print(f"Error: {e}")

            try:
                print("Using buf.get_glyph_positions():")
                if hasattr(buf, 'get_glyph_positions'):
                    positions = buf.get_glyph_positions()
                    print(f"Success! Found {len(positions)} positions")
                else:
                    print("buf.get_glyph_positions() method does not exist")
            except Exception as e:
                print(f"Error: {e}")

            try:
                print("Testing buffer length access:")
                length_via_len = len(buf)
                print(f"len(buf) = {length_via_len}")

                if hasattr(buf, 'length'):
                    length_attr = buf.length
                    print(f"buf.length = {length_attr}")
                else:
                    print("buf.length attribute does not exist")
            except Exception as e:
                print(f"Error: {e}")
    except Exception as e:
        print(f"Error testing buffer: {e}")
else:
    print("Cannot test buffer methods without a buffer")

print("\nTest completed")