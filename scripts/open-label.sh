#!/bin/bash
# Script to open LBX files with Brother P-touch Editor

if [ $# -eq 0 ]; then
    echo "Usage: $0 path/to/label.lbx"
    exit 1
fi

open -a "/Applications/P-touch Editor.app" "$1"