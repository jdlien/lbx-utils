#!/bin/bash

# This script should be able to get the fonts from P-touch Editor for Mac and save them to a directory that is easily accessed.
# extract_fonts.sh - Extract fonts from macOS application bundles
# Usage: ./extract_fonts.sh /path/to/app.app

set -e

# Default path for Brother P-touch Editor on macOS
DEFAULT_APP_PATH="/Applications/P-touch Editor.app"

# Check if an argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 /path/to/app.app"
    echo "Extracts all font files from the specified application bundle"
    echo ""
    echo "Example:"
    echo "  $0 \"$DEFAULT_APP_PATH\""

    # Check if the default app exists and suggest using it
    if [ -d "$DEFAULT_APP_PATH" ]; then
        echo ""
        echo "Default Brother P-touch Editor application found at:"
        echo "  $DEFAULT_APP_PATH"
        echo "You can run the script with this path."
    fi

    exit 1
fi

APP_PATH="$1"

# Check if the app path exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: Application bundle not found at $APP_PATH"
    exit 1
fi

echo "Extracting fonts from: $APP_PATH"

# Create fonts directory if it doesn't exist
EXTRACT_DIR="fonts"
mkdir -p "$EXTRACT_DIR"

# This function copies fonts from a directory to the destination
extract_fonts() {
    local src_dir="$1"

    if [ -d "$src_dir" ]; then
        echo "Searching for fonts in: $src_dir"

        # Find and copy all font files
        find "$src_dir" -type f \( -name "*.ttf" -o -name "*.TTF" -o -name "*.otf" -o -name "*.OTF" \) -exec cp {} "$EXTRACT_DIR/" \;
    fi
}

# Look in common locations for font files
# 1. Check Info.plist for ATSApplicationFontsPath
FONTS_PATH=""
if [ -f "$APP_PATH/Contents/Info.plist" ]; then
    # Use plutil to extract the ATSApplicationFontsPath if it exists
    FONTS_PATH=$(plutil -extract ATSApplicationFontsPath raw -o - "$APP_PATH/Contents/Info.plist" 2>/dev/null || echo "")

    if [ ! -z "$FONTS_PATH" ]; then
        # Convert relative path to absolute
        if [[ "$FONTS_PATH" == /* ]]; then
            FONT_DIR="$APP_PATH$FONTS_PATH"
        else
            FONT_DIR="$APP_PATH/Contents/$FONTS_PATH"
        fi

        echo "Found font path in Info.plist: $FONTS_PATH"
        extract_fonts "$FONT_DIR"
    fi
fi

# 2. Check common locations for fonts
# Resources directory
extract_fonts "$APP_PATH/Contents/Resources"

# Frameworks directory (search recursively for font files)
if [ -d "$APP_PATH/Contents/Frameworks" ]; then
    echo "Searching for fonts in Frameworks directory..."

    # Look for *.bundle/fonts* directories in Frameworks
    find "$APP_PATH/Contents/Frameworks" -type d -name "*.bundle" | while read bundle; do
        extract_fonts "$bundle"

        # Check for fonts.bundle or similarly named directories
        find "$bundle" -type d -name "*font*" | while read font_dir; do
            extract_fonts "$font_dir"
        done
    done

    # Also check for Frameworks/*/Resources/fonts* directories
    find "$APP_PATH/Contents/Frameworks" -path "*/Resources/*font*" -type d | while read font_dir; do
        extract_fonts "$font_dir"
    done
fi

# Count the number of fonts extracted
FONT_COUNT=$(ls -1 "$EXTRACT_DIR"/* 2>/dev/null | wc -l)
if [ "$FONT_COUNT" -gt 0 ]; then
    echo "Successfully extracted $FONT_COUNT font files to $EXTRACT_DIR directory"

    # List the largest fonts
    echo "Largest font files:"
    ls -lSh "$EXTRACT_DIR" | head -10
else
    echo "No font files were found in the application bundle"
fi

echo "Font extraction complete!"