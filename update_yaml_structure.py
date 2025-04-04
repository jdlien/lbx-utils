#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to update LBX YAML files to use the canonical structure with objects array
"""

import os
import re
import glob
import yaml

# Function to update a YAML file to the new structure
def update_yaml_file(filepath):
    print(f"Processing {filepath}...")

    with open(filepath, 'r') as f:
        content = f.read()

    # Check if the file already has the 'objects:' key at the root level
    if re.search(r'^objects:', content, re.MULTILINE):
        print(f"  Already using the new structure. Skipping.")
        return

    # Extract the header section (before the first list item '- type:')
    match = re.search(r'^(.*?)(?=^- type:)', content, re.DOTALL | re.MULTILINE)
    if not match:
        print(f"  Could not find the header section. Skipping.")
        return

    header = match.group(1).rstrip()
    objects_content = content[len(header):].strip()

    # Indent the objects by 2 spaces
    indented_objects = "\n".join(["  " + line for line in objects_content.split("\n")])

    # Create the new content
    new_content = f"{header}\n\nobjects:\n{indented_objects}"

    # Write back to the file
    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"  Updated to new structure.")

# Main script
if __name__ == '__main__':
    # Find all YAML files in the project
    yaml_files = glob.glob('data/lbx_yml_examples/*.lbx.yml')
    yaml_files += glob.glob('data/**/*.lbx.yml', recursive=True)
    yaml_files += glob.glob('tests/**/*.lbx.yml', recursive=True)

    # Remove duplicates
    yaml_files = list(set(yaml_files))

    print(f"Found {len(yaml_files)} YAML files to process")

    # Process each file
    for yaml_file in yaml_files:
        update_yaml_file(yaml_file)

    print("Done!")