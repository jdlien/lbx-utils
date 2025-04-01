#!/bin/bash

# Script to clean up test output directories

echo "Cleaning up test output directories..."

# Remove test output files
echo "Removing test_output directory..."
rm -rf test_output

# Remove generated part images
echo "Removing part_images directory..."
rm -rf part_images

# Remove test images
echo "Removing test-images directory..."
rm -rf test-images

# Remove extracted images
echo "Removing extracted-images directory..."
rm -rf extracted-images

# Remove Python cache files
echo "Removing __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

echo "Cleanup complete!"