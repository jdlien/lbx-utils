#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Process all example YAML files and generate LBX files.

This script finds all .lbx.yml files in the data/lbx_yml_examples directory and
converts them to LBX format using the lbxyml2lbx module.
"""

import os
import sys
import glob
import subprocess
from pathlib import Path

def main():
    """Process all example YAML files."""
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Set the examples directory
    examples_dir = os.path.join(script_dir, 'data', 'lbx_yml_examples')

    # Set the output directory
    output_dir = os.path.join(script_dir, 'test_output', 'lbxyml2lbx')

    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Find all .lbx.yml files in the examples directory
    yaml_files = glob.glob(os.path.join(examples_dir, '*.lbx.yml'))

    if not yaml_files:
        print(f"No .lbx.yml files found in {examples_dir}")
        return

    print(f"Found {len(yaml_files)} YAML files to process.")

    # Process each YAML file
    for yaml_file in yaml_files:
        # Get the base filename without extension
        basename = os.path.basename(yaml_file).replace('.lbx.yml', '')

        # Set the output LBX file path
        lbx_file = os.path.join(output_dir, f"{basename}.lbx")

        # Set the unzip directory
        unzip_dir = os.path.join(output_dir, basename)

        print(f"\nProcessing {basename}...")

        # Build the command
        cmd = [
            sys.executable,
            '-m', 'src.lbx_utils.lbxyml2lbx',
            '--input', yaml_file,
            '--output', lbx_file,
            '--unzip', unzip_dir
        ]

        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ Successfully processed {basename}")
            # Print selected output lines
            for line in result.stdout.splitlines():
                if 'Label size:' in line or 'Using label size:' in line or 'Created LBX file:' in line:
                    print(f"  {line.strip()}")
        else:
            print(f"❌ Error processing {basename}")
            print(result.stderr)

    print("\nProcessing complete! Output files are in:")
    print(f"  {output_dir}/")

if __name__ == "__main__":
    main()