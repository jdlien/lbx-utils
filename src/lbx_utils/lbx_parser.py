#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LBX Parser - Extract and modify Brother P-touch LBX label files

Usage:
./parse_lbx.py [options]

This script provides tools to extract contents from Brother P-touch LBX label files,
modify them, and save changes. It handles text elements, images, and label properties.

LBX files are ZIP archives used by Brother P-Touch Editor that contain XML and image files.

Options:
  -h, --help           Show this help message and exit
  -d DIR, --dir=DIR    Directory to search for LBX files (default: current directory)
  -r, --recursive      Search recursively in subdirectories (default)
  --no-recursive       Do not search recursively in subdirectories
  -o EXT, --output=EXT Output file extension (default: .txt)
  --verbose            Print detailed processing information
  -i --extract-images  Extract images from LBX files and save them to a folder
  --db                 Use SQLite database for part information and update database
"""

import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import argparse
import shutil
import io
import sqlite3
import unicodedata
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("Warning: Pillow library not found. Basic image optimization will be disabled.")
    print("Install with: pip install pillow")

# Check if ImageMagick is available and determine which command to use
def check_imagemagick():
    """Check for ImageMagick availability and return (available, command_name)"""
    # Try the new unified 'magick' command first (ImageMagick 7+)
    try:
        result = subprocess.run(["magick", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return True, "magick"
    except FileNotFoundError:
        pass

    # Fall back to legacy 'convert' command (ImageMagick 6.x and earlier)
    try:
        result = subprocess.run(["convert", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode == 0:
            return True, "convert"
    except FileNotFoundError:
        pass

    return False, None

IMAGEMAGICK_AVAILABLE, IMAGEMAGICK_COMMAND = check_imagemagick()
if not IMAGEMAGICK_AVAILABLE:
    print("Warning: ImageMagick not found. Advanced image conversion will be disabled.")
    print("Install ImageMagick for optimal BMP to transparent PNG conversion.")

# Define the path to the database
DB_PATH = os.path.expanduser("~/bin/lego-data/lego.sqlite")


def connect_to_database():
    """Connect to the SQLite database."""
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None


def get_part_info(part_num):
    """Get part information from the database."""
    conn = connect_to_database()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM parts WHERE part_num = ?", (part_num,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        print(f"Error querying database: {e}")
        return None
    finally:
        conn.close()


def update_part_label_file(part_num, label_file):
    """Update the label_file field for a part in the database."""
    conn = connect_to_database()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE parts SET label_file = ? WHERE part_num = ?", (label_file, part_num))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as e:
        print(f"Error updating database: {e}")
        return False
    finally:
        conn.close()


def sanitize_filename(name, max_length=30):
    """Sanitize a string to be safe for use in filenames."""
    # Replace non-ASCII characters with ASCII equivalents if possible
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')

    # Replace spaces and invalid characters with underscores
    name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')

    # Truncate to max length
    if len(name) > max_length:
        name = name[:max_length]

    return name


def find_lbx_files(directory, recursive=True):
    """Find all LBX files in the specified directory (and optionally its subdirectories)."""
    lbx_files = []

    if recursive:
        # Search recursively using os.walk
        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith('.lbx'):
                    lbx_files.append(os.path.join(root, file))
    else:
        # Search only the specified directory
        for file in os.listdir(directory):
            if file.lower().endswith('.lbx'):
                lbx_files.append(os.path.join(directory, file))

    return lbx_files


def extract_text_from_lbx(lbx_file_path, verbose=False):
    """Extract text content from an LBX file."""
    text_blocks = []

    try:
        with zipfile.ZipFile(lbx_file_path, 'r') as zip_ref:
            # Get list of all files in the archive
            file_list = zip_ref.namelist()

            if verbose:
                print(f"Files in archive: {', '.join(file_list)}")

            # Check if label.xml exists in the archive
            if 'label.xml' in file_list:
                # Extract and read label.xml
                label_xml = zip_ref.read('label.xml').decode('utf-8', errors='ignore')

                # Find all <pt:data> tags and extract their content
                data_tags = re.findall(r'<pt:data>(.*?)</pt:data>', label_xml, re.DOTALL)

                if verbose:
                    print(f"Found {len(data_tags)} text blocks in label.xml")

                for data in data_tags:
                    # Preserve newlines but clean up excessive whitespace
                    lines = [line.strip() for line in data.split('\n')]
                    cleaned_lines = [line for line in lines if line]  # Remove empty lines

                    if cleaned_lines:
                        final_text = '\n'.join(cleaned_lines)
                        text_blocks.append(final_text)

    except Exception as e:
        print(f"Error processing {lbx_file_path}: {e}")

    return text_blocks


def extract_images_from_lbx(lbx_file_path, extract_images=False, verbose=False):
    """Extract images from an LBX file."""
    images_info = []
    file_name_to_original = {}

    if not extract_images:
        return images_info

    try:
        with zipfile.ZipFile(lbx_file_path, 'r') as zip_ref:
            # Get list of all files in the archive
            file_list = zip_ref.namelist()

            # Try to extract original names from label.xml
            if 'label.xml' in file_list:
                label_xml = zip_ref.read('label.xml').decode('utf-8', errors='ignore')

                # Look for image:imageStyle tags with originalName and fileName attributes
                image_tags = re.findall(r'<image:imageStyle\s+originalName="([^"]*?)"\s+[^>]*?fileName="([^"]*?)"[^>]*?>', label_xml, re.DOTALL)

                if verbose and image_tags:
                    print(f"Found {len(image_tags)} image tags with mapping information")

                # Create mapping from fileName to originalName
                for original_name, file_name in image_tags:
                    file_name_to_original[file_name] = original_name
                    if verbose:
                        print(f"Mapping: {file_name} -> {original_name}")

            # Collect all image files (check for common image extensions)
            image_files = [f for f in file_list if f.lower().endswith(('.bmp', '.jpg', '.jpeg', '.png', '.gif'))]

            if verbose:
                print(f"Found {len(image_files)} image files in archive")

            # Add all image files to our result list with original names if available
            for img_file in image_files:
                base_name = os.path.basename(img_file)
                # Look for base name in our mapping
                original_name = file_name_to_original.get(base_name, base_name)

                images_info.append({
                    'filename': img_file,
                    'base_name': base_name,
                    'original_name': original_name
                })

    except Exception as e:
        print(f"Error extracting images from {lbx_file_path}: {e}")

    return images_info


def modify_label_xml(lbx_file_path, bmp_to_png_conversions, verbose=False):
    """Modify the label.xml file to update image references after conversion."""
    if not bmp_to_png_conversions:
        return False

    try:
        # Create a temporary directory for our work
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the archive
            with zipfile.ZipFile(lbx_file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Path to label.xml
            label_xml_path = os.path.join(temp_dir, 'label.xml')

            if not os.path.exists(label_xml_path):
                if verbose:
                    print("label.xml not found in the archive")
                return False

            # Read the XML content
            with open(label_xml_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()

            # Track if we made any changes
            changes_made = False

            # Track which files need to be renamed or converted in the archive
            files_to_convert = []

            # For each BMP to PNG conversion, update references in the XML
            for bmp_info in bmp_to_png_conversions:
                original_name = bmp_info['original_name']
                base_name = bmp_info['base_name']
                original_ext = os.path.splitext(original_name)[1]

                # Only continue if the original file was a BMP
                if original_ext.lower() != '.bmp':
                    continue

                # The original name in the XML may already be .png even if the file was .bmp
                original_basename = os.path.splitext(original_name)[0]

                # Add file to our conversion list
                files_to_convert.append({
                    'original_file': base_name,
                    'new_file': f"{original_basename}.png"
                })

                # Patterns to look for (both .bmp and potentially already .png in the XML)
                patterns = [
                    f'originalName="{original_basename}\\.bmp"',
                    f'originalName="{original_basename}\\.BMP"',
                    f'fileName="{base_name}"',  # Exact match for filename attribute
                ]

                # Replacement patterns
                replacements = [
                    f'originalName="{original_basename}.png"',
                    f'originalName="{original_basename}.png"',
                    f'fileName="{original_basename}.png"',
                ]

                # Perform replacements
                for pattern, replacement in zip(patterns, replacements):
                    new_content = re.sub(pattern, replacement, xml_content)
                    if new_content != xml_content:
                        changes_made = True
                        xml_content = new_content
                        if verbose:
                            print(f"Updated XML reference for {original_name} to PNG")

            # If no changes made, we're done
            if not changes_made:
                if verbose:
                    print("No XML references needed updating")
                return False

            # Write back the modified XML
            with open(label_xml_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)

            # Now convert BMP files to PNG and add them to the archive
            for file_info in files_to_convert:
                orig_file = os.path.join(temp_dir, file_info['original_file'])
                new_file = os.path.join(temp_dir, file_info['new_file'])

                if os.path.exists(orig_file) and IMAGEMAGICK_AVAILABLE:
                    try:
                        # Use ImageMagick to convert BMP to PNG with white as transparent
                        cmd = [
                            IMAGEMAGICK_COMMAND,
                            orig_file,
                            "-transparent", "white",
                            new_file
                        ]

                        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                        if result.returncode == 0:
                            # Remove the original BMP file from temp dir
                            os.remove(orig_file)
                            if verbose:
                                print(f"Converted {file_info['original_file']} to {file_info['new_file']} in archive")
                        else:
                            if verbose:
                                print(f"ImageMagick conversion failed in archive: {result.stderr.decode()}")
                    except Exception as e:
                        if verbose:
                            print(f"Error converting image in archive: {e}")

            # Create a new zip file with updated content
            backup_path = lbx_file_path + '.bak'
            shutil.copy2(lbx_file_path, backup_path)

            # Create the new zip file
            with zipfile.ZipFile(lbx_file_path, 'w') as new_zip:
                # Add all files from the temp directory
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        new_zip.write(file_path, arcname)

            if verbose:
                print(f"Updated LBX file with modified XML references and converted images. Backup saved to {backup_path}")
            else:
                print(f"Updated LBX file with PNG images. Backup saved to {backup_path}")

            return True

    except Exception as e:
        print(f"Error modifying label.xml: {e}")
        return False


def save_text_to_file(lbx_file_path, text_blocks, output_ext='.txt'):
    """Save extracted texts to a file with the same base name but specified extension."""
    if not text_blocks:
        print(f"No text found in {lbx_file_path}")
        return

    # Create output file path with the specified extension
    output_path = os.path.splitext(lbx_file_path)[0] + output_ext

    # Get the folder name and file name for the header
    folder_name = os.path.basename(os.path.dirname(lbx_file_path))
    file_name = os.path.basename(lbx_file_path)

    with open(output_path, 'w', encoding='utf-8') as f:
        # Write a simple markdown H1 header with folder/filename
        f.write(f"# {folder_name}/{file_name}\n\n")

        # Write text blocks without any prefixes
        for text in text_blocks:
            f.write(f"{text}\n\n")

    print(f"Text extracted and saved to {output_path}")


def save_images_to_folder(lbx_file_path, images_info, use_db=False, verbose=False):
    """Save extracted images to a folder named after the LBX file."""
    if not images_info:
        print(f"No images found in {lbx_file_path}")
        return

    # Create folder name based on LBX file base name
    base_name = os.path.splitext(os.path.basename(lbx_file_path))[0]
    output_folder = os.path.join(os.path.dirname(lbx_file_path), base_name + "_images")

    # Create folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    extracted_count = 0
    compressed_count = 0
    converted_count = 0
    db_updated_count = 0

    # Track BMP to PNG conversions for XML updating
    bmp_to_png_conversions = []
    has_bmp_files = False

    try:
        with zipfile.ZipFile(lbx_file_path, 'r') as zip_ref:
            for img_info in images_info:
                img_file = img_info['filename']
                base_name = img_info['base_name']
                original_ext = os.path.splitext(base_name)[1]

                # Check if any BMP files exist in the archive
                if original_ext.lower() == '.bmp':
                    has_bmp_files = True
                    bmp_to_png_conversions.append(img_info)

                # Get the original name and part number (without extension)
                original_name = img_info['original_name']
                original_name_no_ext = os.path.splitext(original_name)[0]
                part_num = original_name_no_ext  # Assume part_num is the same as original name without extension

                # Read image data
                img_data = zip_ref.read(img_file)

                # If using database, check for part information and update database
                part_name = None
                if use_db:
                    # Try to update the database with the LBX file information
                    relative_path = os.path.relpath(lbx_file_path, os.getcwd())
                    parent_folder = os.path.basename(os.path.dirname(lbx_file_path))
                    label_file = f"{parent_folder}/{os.path.basename(lbx_file_path)}"

                    if update_part_label_file(part_num, label_file):
                        db_updated_count += 1
                        if verbose:
                            print(f"Updated database for part {part_num}")

                    # Get part name from database
                    part_name = get_part_info(part_num)
                    if part_name and verbose:
                        print(f"Found part name for {part_num}: {part_name}")

                # Create enhanced filename if part name is available
                if part_name:
                    sanitized_name = sanitize_filename(part_name)
                    enhanced_name = f"{part_num}-{sanitized_name}"
                else:
                    enhanced_name = original_name_no_ext

                # Define output path with original format first (as fallback)
                original_ext = os.path.splitext(base_name)[1]
                original_output_path = os.path.join(output_folder, f"{enhanced_name}{original_ext}")

                # Check if we're dealing with a BMP file and can use ImageMagick
                if original_ext.lower() == '.bmp' and IMAGEMAGICK_AVAILABLE:
                    try:
                        # Save the original BMP temporarily to convert it
                        temp_bmp_path = os.path.join(output_folder, f"temp_{enhanced_name}.bmp")
                        with open(temp_bmp_path, 'wb') as f:
                            f.write(img_data)

                        # Define output path for PNG
                        output_path = os.path.join(output_folder, f"{enhanced_name}.png")

                        # Use ImageMagick to convert BMP to PNG with white as transparent
                        cmd = [
                            IMAGEMAGICK_COMMAND,
                            temp_bmp_path,
                            "-transparent", "white",
                            output_path
                        ]

                        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                        # Remove temporary BMP file
                        os.remove(temp_bmp_path)

                        if result.returncode == 0:
                            converted_count += 1
                            extracted_count += 1
                            if verbose:
                                print(f"Converted BMP to transparent PNG: {enhanced_name}")
                            continue  # Skip the rest of the processing
                        else:
                            if verbose:
                                print(f"ImageMagick conversion failed: {result.stderr.decode()}")
                            # Fall back to other methods
                    except Exception as e:
                        if verbose:
                            print(f"Error using ImageMagick to convert {enhanced_name}: {e}")
                        # Fall back to other methods

                # Try to compress and optimize image if Pillow is available
                if PILLOW_AVAILABLE:
                    try:
                        # Load image from binary data
                        img = Image.open(io.BytesIO(img_data))

                        # Check if image is already grayscale, if not convert it
                        if img.mode not in ['L', 'LA', '1']:
                            if verbose:
                                print(f"Converting {enhanced_name} to grayscale")
                            img = img.convert('L')

                        # Create optimized PNG output path
                        output_path = os.path.join(output_folder, f"{enhanced_name}.png")

                        # Save as optimized PNG
                        img.save(output_path, 'PNG', optimize=True, compress_level=9)

                        if os.path.getsize(output_path) < len(img_data) or original_ext.lower() != '.png':
                            compressed_count += 1
                            if verbose:
                                print(f"Compressed {enhanced_name} successfully")

                        extracted_count += 1
                        continue  # Skip the normal file writing

                    except Exception as e:
                        if verbose:
                            print(f"Error compressing {enhanced_name}: {e}")
                        # Fall back to normal extraction without compression

                # If we reach here, either Pillow is not available or compression failed
                # Save the original uncompressed image
                with open(original_output_path, 'wb') as f:
                    f.write(img_data)

                extracted_count += 1

        # If we found any BMP files, update the archive with PNG replacements
        if has_bmp_files and IMAGEMAGICK_AVAILABLE:
            if modify_label_xml(lbx_file_path, bmp_to_png_conversions, verbose):
                if verbose:
                    print(f"Updated XML references and converted images in {lbx_file_path}")

        if verbose:
            print(f"Extracted {extracted_count} images to {output_folder}")
            if converted_count > 0:
                print(f"Converted {converted_count} BMP images to transparent PNG format")
            if PILLOW_AVAILABLE:
                print(f"Compressed {compressed_count} images to optimized PNG format")
            if use_db:
                print(f"Updated database for {db_updated_count} parts")
        else:
            print(f"Images extracted and saved to {output_folder}")
            if converted_count > 0:
                print(f"Converted {converted_count} BMP images to transparent PNG format")
            if use_db and db_updated_count > 0:
                print(f"Updated database for {db_updated_count} parts")

    except Exception as e:
        print(f"Error saving images from {lbx_file_path}: {e}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Extract text from Brother P-Touch Editor LBX files.')
    parser.add_argument('-d', '--dir', dest='directory', default=os.getcwd(),
                       help='Directory to search for LBX files (default: current directory)')
    parser.add_argument('-r', '--recursive', dest='recursive', action='store_true', default=True,
                       help='Search recursively in subdirectories (default)')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false',
                       help='Do not search recursively in subdirectories')
    parser.add_argument('-o', '--output', dest='output_ext', default='.txt',
                       help='Output file extension (default: .txt)')
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False,
                       help='Print detailed processing information')
    parser.add_argument('-i','--extract-images', dest='extract_images', action='store_true', default=False,
                       help='Extract images from LBX files and save them to a folder')
    parser.add_argument('--db', dest='use_db', action='store_true', default=False,
                       help='Use SQLite database for part information and update database')

    return parser.parse_args()


def main():
    """Main function to find and process LBX files."""
    args = parse_arguments()

    # Validate directory
    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a valid directory.")
        return 1

    # Check if database exists when use_db is enabled
    if args.use_db and not os.path.exists(DB_PATH):
        print(f"Error: Database file '{DB_PATH}' not found.")
        return 1

    print(f"Searching for LBX files in {args.directory}" +
          (" and subdirectories..." if args.recursive else "..."))

    lbx_files = find_lbx_files(args.directory, args.recursive)

    if not lbx_files:
        print("No LBX files found.")
        return 0

    print(f"Found {len(lbx_files)} LBX file(s).")

    # Process BMP to PNG conversions for LBX files
    def process_lbx_with_png_conversion(lbx_file):
        """Process a single LBX file with BMP to PNG conversion."""
        print(f"\nProcessing {lbx_file}...")

        # First check if the file contains BMP images that need conversion
        bmp_found = False

        # Extract to a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the archive
            with zipfile.ZipFile(lbx_file, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
                # Check for BMP files
                bmp_files = [f for f in zip_ref.namelist() if f.lower().endswith('.bmp')]
                if bmp_files:
                    bmp_found = True

            # If we found BMP files and ImageMagick is available, convert them
            if bmp_found and IMAGEMAGICK_AVAILABLE:
                print(f"Found BMP files in {lbx_file}, converting to PNG...")

                # Path to label.xml
                label_xml_path = os.path.join(temp_dir, 'label.xml')

                if os.path.exists(label_xml_path):
                    # Read the XML to find image mappings
                    with open(label_xml_path, 'r', encoding='utf-8') as f:
                        xml_content = f.read()

                    # Look for image tags with originalName and fileName attributes
                    image_tags = re.findall(r'<image:imageStyle\s+originalName="([^"]*?)"\s+[^>]*?fileName="([^"]*?)"[^>]*?>', xml_content)
                    file_name_to_original = {}

                    # Create mapping from fileName to originalName
                    for original_name, file_name in image_tags:
                        file_name_to_original[file_name] = original_name

                    # Process each BMP file
                    changes_made = False
                    for bmp_file in bmp_files:
                        bmp_path = os.path.join(temp_dir, bmp_file)
                        file_base = os.path.basename(bmp_file)

                        # Get the original name (usually has .png extension in XML)
                        original_name = file_name_to_original.get(file_base, file_base)
                        original_basename = os.path.splitext(original_name)[0]

                        # Output PNG path
                        png_file = f"{original_basename}.png"
                        png_path = os.path.join(temp_dir, png_file)

                        # Convert BMP to PNG with transparent white
                        if args.verbose:
                            print(f"Converting {bmp_file} to {png_file}...")

                        try:
                            # Use ImageMagick to convert BMP to PNG with white as transparent
                            cmd = [
                                IMAGEMAGICK_COMMAND,
                                bmp_path,
                                "-transparent", "white",
                                png_path
                            ]

                            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                            if result.returncode == 0:
                                # Remove the original BMP file
                                os.remove(bmp_path)

                                # Update XML references
                                patterns = [
                                    f'fileName="{file_base}"',
                                ]
                                replacements = [
                                    f'fileName="{png_file}"',
                                ]

                                for pattern, replacement in zip(patterns, replacements):
                                    new_content = re.sub(pattern, replacement, xml_content)
                                    if new_content != xml_content:
                                        changes_made = True
                                        xml_content = new_content

                                if args.verbose:
                                    print(f"Successfully converted {bmp_file} to transparent PNG")
                            else:
                                if args.verbose:
                                    print(f"ImageMagick conversion failed: {result.stderr.decode()}")
                        except Exception as e:
                            if args.verbose:
                                print(f"Error converting {bmp_file}: {e}")

                    # If changes made to XML, write it back
                    if changes_made:
                        with open(label_xml_path, 'w', encoding='utf-8') as f:
                            f.write(xml_content)

                # Create a backup of the original file
                backup_path = lbx_file + '.bak'
                shutil.copy2(lbx_file, backup_path)

                # Create a new archive with the modified files
                with zipfile.ZipFile(lbx_file, 'w') as new_zip:
                    # Add all files from the temp directory
                    for root, _, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            new_zip.write(file_path, arcname)

                print(f"Updated {lbx_file} with PNG images. Backup saved to {backup_path}")

        # Now proceed with normal processing
        text_blocks = extract_text_from_lbx(
            lbx_file,
            verbose=args.verbose
        )
        save_text_to_file(
            lbx_file,
            text_blocks,
            output_ext=args.output_ext
        )

        if args.extract_images:
            images_info = extract_images_from_lbx(
                lbx_file,
                extract_images=True,
                verbose=args.verbose
            )
            save_images_to_folder(
                lbx_file,
                images_info,
                use_db=args.use_db,
                verbose=args.verbose
            )

    # Process each LBX file
    for lbx_file in lbx_files:
        process_lbx_with_png_conversion(lbx_file)

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())