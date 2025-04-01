#!/bin/bash

# Convert a Brother P-touch label file to 24mm width
# Useful for BrickArchitect labels

# Check if an input file was provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 input.lbx"
    exit 1
fi

# Get the input file
input_file="$1"
# Create output filename by adding -24mm before the extension
output_file="${input_file%.*}-24mm.${input_file##*.}"

python3 change_lbx.py -f 14 -l 24 -c -s 1.5 -m 0.5 "$input_file" "$output_file"