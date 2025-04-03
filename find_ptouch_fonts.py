#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
find_ptouch_fonts.py - Find Brother P-Touch Editor fonts on the system

This script searches for Brother P-Touch Editor fonts on the system and
provides information about where they are located and how to use them.
"""

import os
import sys
import platform
import subprocess
import glob
from pathlib import Path

def find_ptouch_app():
    """Find the P-Touch Editor app on the system."""
    possible_paths = []

    system = platform.system()
    if system == "Darwin":  # macOS
        possible_paths = [
            "/Applications/P-touch Editor.app",
            "/Applications/Brother P-touch Editor.app",
            os.path.expanduser("~/Applications/P-touch Editor.app"),
            os.path.expanduser("~/Applications/Brother P-touch Editor.app")
        ]
    elif system == "Windows":
        possible_paths = [
            "C:\\Program Files\\Brother\\P-touch Editor",
            "C:\\Program Files (x86)\\Brother\\P-touch Editor"
        ]

    for path in possible_paths:
        if os.path.exists(path):
            print(f"Found P-Touch Editor at: {path}")
            return path

    print("P-Touch Editor not found in standard locations.")
    return None

def find_fonts_in_app(app_path):
    """Find fonts in the P-Touch Editor app package."""
    fonts = []

    system = platform.system()
    if system == "Darwin":  # macOS
        font_paths = [
            os.path.join(app_path, "Contents/Resources/Fonts"),
            os.path.join(app_path, "Contents/Resources/fonts"),
            # Search for font files recursively in the app bundle
            *glob.glob(os.path.join(app_path, "**/*.ttf"), recursive=True),
            *glob.glob(os.path.join(app_path, "**/*.ttc"), recursive=True),
            *glob.glob(os.path.join(app_path, "**/*.otf"), recursive=True)
        ]

        for path in font_paths:
            if os.path.isdir(path):
                print(f"\nFound font directory: {path}")
                font_files = glob.glob(os.path.join(path, "*.ttf")) + \
                             glob.glob(os.path.join(path, "*.ttc")) + \
                             glob.glob(os.path.join(path, "*.otf"))
                for font in font_files:
                    fonts.append(font)
                    print(f"  - {os.path.basename(font)}")
            elif os.path.isfile(path) and path not in fonts:
                fonts.append(path)

    # If no fonts found in specific directories, try a system-wide search
    if not fonts:
        print("\nSearching for P-Touch fonts in system font directories...")
        font_dirs = []

        if system == "Darwin":  # macOS
            font_dirs = [
                "/Library/Fonts",
                "/System/Library/Fonts",
                os.path.expanduser("~/Library/Fonts")
            ]
        elif system == "Windows":
            windir = os.environ.get("WINDIR", "C:\\Windows")
            font_dirs = [os.path.join(windir, "Fonts")]

        for font_dir in font_dirs:
            if os.path.exists(font_dir):
                # Look for Helsinki and other P-Touch related fonts
                helsinki_fonts = glob.glob(os.path.join(font_dir, "*Helsinki*.ttf")) + \
                                 glob.glob(os.path.join(font_dir, "*PT*.ttf")) + \
                                 glob.glob(os.path.join(font_dir, "*Brother*.ttf"))
                if helsinki_fonts:
                    print(f"Found potential P-Touch fonts in {font_dir}:")
                    for font in helsinki_fonts:
                        fonts.append(font)
                        print(f"  - {os.path.basename(font)}")

    return fonts

def examine_dmg_installers():
    """Look for P-Touch Editor DMG installers in the Downloads folder."""
    download_dir = os.path.expanduser("~/Downloads")
    dmg_files = glob.glob(os.path.join(download_dir, "*P-touch*.dmg")) + \
                glob.glob(os.path.join(download_dir, "*Brother*.dmg"))

    if dmg_files:
        print("\nFound potential P-Touch Editor installers:")
        for dmg in dmg_files:
            print(f"  - {os.path.basename(dmg)}")
        print("\nYou can examine these installers to extract fonts:")
        print("  1. Double-click the DMG to mount it")
        print("  2. Look for font files or the app package")
        print("  3. Copy font files to a location of your choice")

    return dmg_files

def create_font_dir():
    """Create a directory for P-Touch fonts in the user's home directory."""
    font_dir = os.path.expanduser("~/PT-Editor-Fonts")
    os.makedirs(font_dir, exist_ok=True)
    print(f"\nCreated directory for P-Touch fonts: {font_dir}")
    return font_dir

def copy_fonts(fonts, dest_dir):
    """Copy fonts to the destination directory."""
    if not fonts:
        print("No fonts to copy.")
        return

    print(f"\nCopying fonts to {dest_dir}...")
    for font in fonts:
        dest_file = os.path.join(dest_dir, os.path.basename(font))
        try:
            with open(font, 'rb') as src_file:
                with open(dest_file, 'wb') as dst_file:
                    dst_file.write(src_file.read())
            print(f"  ✓ Copied {os.path.basename(font)}")
        except Exception as e:
            print(f"  ✗ Error copying {os.path.basename(font)}: {str(e)}")

def suggest_next_steps(font_dir):
    """Suggest next steps for the user."""
    print("\n--- NEXT STEPS ---")
    print(f"1. Use the fonts directory in your text_dimensions.py code:")
    print(f"   calculator = TextDimensionCalculator(font_dir='{font_dir}')")
    print()
    print(f"2. When running tests, specify the font directory:")
    print(f"   python -m pytest tests/test_text_dimensions.py --font-dir='{font_dir}'")
    print()
    print(f"3. To use the calculator directly for testing:")
    print(f"   python src/lbx_utils/text_dimensions.py --text='Hello World' --font=Helsinki --debug --font-dir='{font_dir}'")

def main():
    """Main function."""
    print("=== Brother P-Touch Editor Font Finder ===\n")

    app_path = find_ptouch_app()
    fonts = []

    if app_path:
        fonts = find_fonts_in_app(app_path)

    # If no fonts found in the app, look for DMG installers
    if not fonts:
        examine_dmg_installers()
        print("\nCouldn't find Helsinki font installed on your system.")
        print("Options:")
        print("1. Copy/install the P-Touch Editor application")
        print("2. Find Helsinki.ttf font file from another source")
        print("3. Use a fallback font like Arial or Helvetica")
    else:
        # Create font directory and copy fonts
        font_dir = create_font_dir()
        copy_fonts(fonts, font_dir)
        suggest_next_steps(font_dir)

if __name__ == "__main__":
    main()