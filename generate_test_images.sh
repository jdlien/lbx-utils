#!/bin/bash

# Ensure output directory exists
mkdir -p test-images

PART_NUMBER=3001

# Test different edge thicknesses with default line thickness (matching edge thickness)
echo "Generating edge thickness tests..."
for edge in 0.3 0.5 0.8 1.0 1.5 2.0 3.0; do
  echo "  Edge thickness: $edge"
  python generate-part-image.py $PART_NUMBER -o "./test-images/$PART_NUMBER-edge${edge}.png" --edge-thickness $edge
done

# Test different line thicknesses with a fixed edge thickness
echo "Generating line thickness tests with edge=1.5..."
for line in 0.3 0.5 0.8 1.0 1.5 2.0; do
  echo "  Line thickness: $line"
  python generate-part-image.py $PART_NUMBER -o "./test-images/$PART_NUMBER-edge1.5-line${line}.png" --edge-thickness 1.5 --line-thickness $line
done

# Test a few specific combinations that might be particularly useful
echo "Generating combination tests..."
python generate-part-image.py $PART_NUMBER -o "./test-images/$PART_NUMBER-bold.png" --edge-thickness 2.0 --line-thickness 0.8
python generate-part-image.py $PART_NUMBER -o "./test-images/$PART_NUMBER-subtle.png" --edge-thickness 0.8 --line-thickness 0.3
python generate-part-image.py $PART_NUMBER -o "./test-images/$PART_NUMBER-highlight-edges.png" --edge-thickness 1.5 --line-thickness 0.5

echo "All test images generated in test-images folder!"