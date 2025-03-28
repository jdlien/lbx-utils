#!/bin/bash

# Ensure output directory exists
mkdir -p test-images/constraint-comparison

# Parts of different shapes to test
# Format: part_number:description
PARTS=(
  "3001:Brick 2×4"      # Regular brick
  "3006:Brick 2×10"     # Long brick
  "3633:Brick 1×6×2"    # Tall brick
  "3032:Plate 4×6"      # Wide plate
  "4282:Plate 2×16"     # Very wide plate
  "3039:Slope 45° 2×2"  # Small part
  "3037:Slope 45° 2×4"  # Small-medium part
)

# Common settings
BASE_WIDTH=320
BASE_HEIGHT=140  # This will be the FIXED height for all height-constrained images
EDGE_THICKNESS=1.5
LINE_THICKNESS=1.0
SCALE_FACTOR=1.0  # No additional scaling

echo "=== GENERATING COMPARISON IMAGES ==="
echo "Height-constrained images will have EXACTLY ${BASE_HEIGHT}px height"
echo "Width-constrained images will have APPROXIMATELY ${BASE_WIDTH}px width (auto-cropped)"
echo ""

# Create a directory for view angle tests
mkdir -p test-images/view-angles

# Generate view angle comparison for one part
ANGLE_TEST_PART="3001"  # Use 2x4 brick for view comparison
echo "Generating view angle comparisons for part ${ANGLE_TEST_PART}..."

for longitude in -45 -30 -15 0 15 30 45; do
  echo "  - Generating image with longitude ${longitude}°"
  python generate-part-image.py $ANGLE_TEST_PART \
    -o "./test-images/view-angles/${ANGLE_TEST_PART}-long${longitude}.png" \
    --height $BASE_HEIGHT \
    --edge-thickness $EDGE_THICKNESS \
    --line-thickness $LINE_THICKNESS \
    --lon $longitude
done

echo "View angle comparisons generated in test-images/view-angles folder!"
echo ""

# Loop through parts
for part_info in "${PARTS[@]}"; do
  part_number=$(echo $part_info | cut -d: -f1)
  description=$(echo $part_info | cut -d: -f2)

  echo "Processing part $part_number ($description)..."

  # Generate image with height constraint and cropped transparent parts (default)
  echo "  - Generating height-constrained image with transparent cropping (default)..."
  python generate-part-image.py $part_number \
    -o "./test-images/constraint-comparison/${part_number}-height-cropped.png" \
    --height $BASE_HEIGHT \
    --edge-thickness $EDGE_THICKNESS \
    --line-thickness $LINE_THICKNESS \
    --crop-transparency

  # Generate image with height constraint but without cropping transparent parts
  echo "  - Generating height-constrained image WITHOUT transparent cropping..."
  python generate-part-image.py $part_number \
    -o "./test-images/constraint-comparison/${part_number}-height-uncropped.png" \
    --height $BASE_HEIGHT \
    --edge-thickness $EDGE_THICKNESS \
    --line-thickness $LINE_THICKNESS \
    --no-crop-transparency

  # Generate image with width constraint (using the new flag)
  echo "  - Generating width-constrained image (auto-cropped by LDView)..."
  python generate-part-image.py $part_number \
    -o "./test-images/constraint-comparison/${part_number}-width.png" \
    --width $BASE_WIDTH \
    --edge-thickness $EDGE_THICKNESS \
    --line-thickness $LINE_THICKNESS \
    --constrain-width

  echo ""
done

echo "All test images generated in test-images/constraint-comparison folder!"
echo "Check that height-constrained images all have EXACTLY the same height (${BASE_HEIGHT}px)"
echo "The cropped versions should have transparent areas on the sides removed."