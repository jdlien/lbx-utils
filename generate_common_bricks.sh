#!/bin/bash

# Ensure output directory exists
mkdir -p test-images

# Using edge thickness 3.0 (our new default)

# List of common LEGO elements
# Format: part_number:description
PARTS=(
  # Basic bricks
  "3005:Brick 1×1"
  "3004:Brick 1×2"
  "3622:Brick 1×3"
  "3010:Brick 1×4"
  "3009:Brick 1×6"
  "3008:Brick 1×8"
  "3003:Brick 2×2"
  "3002:Brick 2×3"
  "3001:Brick 2×4"
  "2456:Brick 2×6"
  "3007:Brick 2×8"
  "3006:Brick 2×10"

  # Plates
  "3024:Plate 1×1"
  "3023:Plate 1×2"
  "3710:Plate 1×4"
  "3666:Plate 1×6"
  "3022:Plate 2×2"
  "3021:Plate 2×3"
  "3020:Plate 2×4"
  "3034:Plate 2×8"
  "3032:Plate 4×6"
  "3035:Plate 4×8"
  "3033:Plate 6×10"
  "3027:Plate 8×16"
  "92438:Plate 8×16"

  # Slopes
  "3040:Slope 45° 1×2"
  "4286:Slope 33° 1×3"
  "3037:Slope 45° 2×4"
  "3038:Slope 45° 2×3"
  "3039:Slope 45° 2×2"
  "3298:Slope 33° 2×3"
  "3300:Slope 33° 2×2"

  # Tiles
  "3070:Tile 1×1"
  "3069:Tile 1×2"
  "6636:Tile 1×6"
  "3068:Tile 2×2"

  # Specialty bricks
  "3001p01:Brick 2×4 with Town Car Grille Pattern"
  "3010p90:Brick 1×4 with Hollow Studs and Blue '4 JUNIORS' Pattern"
  "30136:Brick Special 1×2 Log"
  "3941:Brick Round 2×2 with Axle Hole"
  "3942:Cone 2×2"
  "6143:Brick Round 2×2 with Fluted Top and Bottom"
  "6233:Cone 3×3×2"
  "6564:Wedge 3×3"

  # Technic elements
  "3700:Technic Brick 1×2 with Hole"
  "3701:Technic Brick 1×4 with Holes"
  "3702:Technic Brick 1×8 with Holes"
  "3703:Technic Brick 1×16 with Holes"
  "3705:Technic Axle 4"
  "3713:Technic Bush"
  "3894:Technic Brick 1×6 with Holes"

  # Windows and doors
  "3853:Window 1×4×3"
  "4132:Panel 2×2×2 with Window"
  "3861:Door 1×4×5 with 4 Panes"
)

echo "Generating images for ${#PARTS[@]} common LEGO elements..."

# Generate images for each part
for part_entry in "${PARTS[@]}"; do
  # Split the entry into part number and description
  part_number="${part_entry%%:*}"
  description="${part_entry#*:}"

  # Clean the description for filename use
  clean_desc=$(echo "$description" | tr ' ×' '_x' | tr -d '°')

  echo "Processing $part_number ($description)"

  # Generate the image
  python generate_part_image.py "$part_number" -o "./test-images/$part_number-$clean_desc.png"

  # Add a small delay to prevent overwhelming the system
  sleep 0.2
done

echo "All images generated successfully in test-images folder!"