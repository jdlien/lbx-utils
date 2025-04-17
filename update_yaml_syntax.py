#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to update LBX YAML files to use shortcut syntax
"""

import os
import re
import yaml
import sys
from collections import defaultdict

def process_object(obj, issues):
    """Process a single object recursively, converting to shortcut syntax"""
    if not isinstance(obj, dict):
        return False

    modified = False

    if 'type' in obj:
        obj_type = obj['type'].lower()

        # Handle content objects
        if obj_type in ['text', 'image', 'barcode', 'qr']:
            content_key = 'content'
            if obj_type == 'image':
                content_key = 'source'

            if content_key in obj:
                content_value = obj[content_key]
                obj[obj_type] = content_value
                del obj[content_key]
                del obj['type']
                modified = True

                # For barcode, convert barcodeType to type
                if obj_type == 'barcode' and 'barcodeType' in obj:
                    obj['type'] = obj['barcodeType']
                    del obj['barcodeType']

        # Handle container objects
        elif obj_type in ['group', 'container', 'line', 'rect']:
            if 'name' in obj:
                name_value = obj['name']
                obj[obj_type] = name_value
                del obj['name']
                del obj['type']
                modified = True

        # Track objects that we can't convert automatically
        elif obj_type in ['richtext']:
            issues['special_objects'].append(f"richtext object found")

    # Process nested objects recursively
    if 'objects' in obj and isinstance(obj['objects'], list):
        for i, child_obj in enumerate(obj['objects']):
            if process_object(child_obj, issues):
                modified = True

    return modified

def convert_to_shortcut(yaml_file):
    """Convert a YAML file to use shortcut syntax"""
    # Read the file
    with open(yaml_file, 'r') as f:
        content = f.read()

    # Try to parse the YAML content
    try:
        data = yaml.safe_load(content)
    except Exception as e:
        print(f'Error parsing {yaml_file}: {e}')
        return False, {'parse_error': str(e)}

    if not data or not isinstance(data, dict) or 'objects' not in data:
        # Skip files that don't have objects
        return False, {'no_objects': True}

    modified = False
    issues = defaultdict(list)

    # Process each object in the root objects list
    for obj in data['objects']:
        if process_object(obj, issues):
            modified = True

    if modified:
        # Write the modified data back to the file
        with open(yaml_file, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        print(f'Updated {yaml_file}')
        return True, issues

    return False, issues

def process_directory(directory):
    """Process all YAML files in a directory"""
    updated_count = 0
    skipped_count = 0
    error_count = 0

    # Get list of YAML files
    yaml_files = []
    exclude_files = ['81_shortcut_syntax.lbx.yml', '82_canonical_syntax.lbx.yml']

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.lbx.yml') and file not in exclude_files:
                yaml_files.append(os.path.join(root, file))

    # Process each file
    for yaml_file in yaml_files:
        try:
            if convert_to_shortcut(yaml_file):
                updated_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f'Error processing {yaml_file}: {e}')
            error_count += 1

    print(f'Summary: {updated_count} files updated, {skipped_count} files skipped, {error_count} errors')

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_directory(sys.argv[1])
    else:
        process_directory('data/lbx_yml_examples')