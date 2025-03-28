#!/bin/bash

# Ensure output directory exists
mkdir -p test-images/scaled

# Parts of different sizes to test
# Format: part_number:description
PARTS=(
  "3001:Brick 2×4"      # Medium size
  "3005:Brick 1×1"      # Small size
  "3006:Brick 2×10"     # Long brick
  "3032:Plate 4×6"      # Wide plate
  "30136:Brick Special 1×2 Log" # Small special part
  "3941:Brick Round 2×2 with Axle Hole" # Small technic part
  "3020:Plate 2×4"      # Small plate
)

# Common settings
BASE_WIDTH=320
EDGE_THICKNESS=2.0
LINE_THICKNESS=1.0
SCALE_FACTOR=0.5  # Makes scaled images approximately half the size

echo "Generating comparison images (fixed size vs. scaled size)..."

# Loop through parts
for part_info in "${PARTS[@]}"; do
  part_number=$(echo $part_info | cut -d: -f1)
  description=$(echo $part_info | cut -d: -f2)

  echo "Processing part $part_number ($description)..."

  # Generate image with fixed size (variable line thickness)
  echo "  - Generating fixed size image..."
  python generate-part-image.py $part_number \
    -o "./test-images/scaled/${part_number}-fixed.png" \
    --width $BASE_WIDTH \
    --edge-thickness $EDGE_THICKNESS \
    --line-thickness $LINE_THICKNESS

  # Generate image with scaled size (fixed line thickness)
  echo "  - Generating scaled size image..."
  python generate-part-image.py $part_number \
    -o "./test-images/scaled/${part_number}-scaled.png" \
    --width $BASE_WIDTH \
    --edge-thickness $EDGE_THICKNESS \
    --line-thickness $LINE_THICKNESS \
    --scale-size-not-lines \
    --size-scale-factor $SCALE_FACTOR
done

echo "All test images generated in test-images/scaled folder!"