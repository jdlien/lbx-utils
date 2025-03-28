#!/usr/bin/env python3

# This script generates a cropped, transparent PNG snapshot of an LDraw part file using LDView.
# It ensures consistent camera, lighting, and quality settings.
# Requires LDView to be installed and configured with an appropriate view and the LDraw library to be accessible.
#
# Notes:
# To make images closer to Tom Alphin BrickArchitect Label style, use the following settings in LDView:
#
# View (under menu):
# ------------------
# - Latitude: 35
# - Longitude -30 (Some parts look better with -60)

# Preferences
# -----------
# General:
# - Antialiased Lines
# - Field of View: 0.1
# - Background: White
# - Default: White (or transparent for trans parts)

# Geometry:
# - Edge Lines
# - Conditional Lines
# - High QUality
# - Always Black
# - Maximum Thickness

# Effects:
# - Lighting:
# 	- High quality
# 	- Subdued (or turn off subdued for increased contrast and darker faces)
# 	- Light Direction: Top Right

# Primitives:
# - Primitive Substitution
# 	- Curve Quality: Maximum


import typer
import subprocess
import os
import sys
import math
from pathlib import Path
from typing import Optional, List, Dict, Any
import re  # Add regex for validating filenames

# Rich and Colorama for styled output
from rich.console import Console
from rich.panel import Panel
import colorama

# For image processing (cropping transparencies)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Initialize Rich Console and Colorama
colorama.init()
console = Console()

# Default angles for the --all-angles option
DEFAULT_LONGITUDE_ANGLES = [-120, -60, -30, 0, 30, 60, 120]

# Default paths (adjust if your setup differs)
# User specified ~/Library/ldraw/parts/
DEFAULT_LDRAW_PARTS_PATH = Path("~/Library/ldraw/parts").expanduser()
# Default for macOS, adjust for other OS if needed
DEFAULT_LDVIEW_APP_PATH = Path("/Applications/LDView.app")


app = typer.Typer(
    help="🖼️ Generate consistent PNG images of LEGO parts using LDView.",
    add_completion=False,
    rich_markup_mode="markdown",
)


def find_ldview_executable(ldview_app_path: Path) -> Optional[Path]:
    """
    Finds the LDView executable within the .app bundle on macOS
    or checks if the provided path is an executable on other systems.
    """
    if sys.platform == "darwin" and ldview_app_path.suffix == ".app":
        # Standard macOS .app bundle structure
        potential_path = ldview_app_path / "Contents" / "MacOS" / "LDView"
        if potential_path.is_file() and os.access(potential_path, os.X_OK):
            console.print(f"[dim]Found macOS LDView executable: {potential_path}[/dim]")
            return potential_path
        else:
             console.print(f"[yellow]Warning:[/yellow] Could not find executable at standard macOS path: {potential_path}")
             # Fallback: Check if the .app path itself is somehow executable (unlikely but possible)
             if ldview_app_path.is_file() and os.access(ldview_app_path, os.X_OK):
                 console.print(f"[dim]Using provided path directly (unusual for .app): {ldview_app_path}[/dim]")
                 return ldview_app_path
    elif ldview_app_path.is_file() and os.access(ldview_app_path, os.X_OK):
        # Assume the path is directly to the executable (Linux, Windows, or non-standard macOS)
        console.print(f"[dim]Found LDView executable: {ldview_app_path}[/dim]")
        return ldview_app_path
    elif ldview_app_path.is_dir():
         # Check for common executable names within the directory if it's not a .app
         for name in ["ldview", "LDView", "ldview.exe", "LDView.exe"]:
              potential_path = ldview_app_path / name
              if potential_path.is_file() and os.access(potential_path, os.X_OK):
                   console.print(f"[dim]Found LDView executable in directory: {potential_path}[/dim]")
                   return potential_path

    console.print(f"[bold red]Error:[/bold red] LDView executable not found or not executable at '{ldview_app_path}'.")
    return None


def find_part_file(ldraw_dir: Path, part_number: str) -> Optional[Path]:
    """
    Searches for the part .dat file in the LDraw directory, including common subdirs.
    """
    part_file_name = f"{part_number}.dat"
    search_dirs = [
        ldraw_dir,
        ldraw_dir / "parts",
        ldraw_dir / "p",
        ldraw_dir / "parts" / "s", # Subparts directory
    ]

    for directory in search_dirs:
        part_path = directory / part_file_name
        if part_path.is_file():
            console.print(f"Found part file: '{part_path}'")
            return part_path

    # If not found, log checked paths
    checked_paths = [str(d / part_file_name) for d in search_dirs]
    console.print(f"[bold red]Error:[/bold red] Part file '{part_file_name}' not found in LDraw directory '{ldraw_dir}'.")
    console.print(f"[dim]Checked paths:\n- " + "\n- ".join(checked_paths) + "[/dim]")
    return None


def get_part_dimensions_from_dat(part_file_path: Path, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    Parses an LDraw DAT file to calculate the dimensions of a part.

    Args:
        part_file_path: Path to the LDraw DAT file
        verbose: Whether to print detailed information

    Returns:
        Dictionary containing dimensions (width, height, depth) in LDraw Units,
        and derived measurements like stud dimensions and approximate stud count,
        or None if parsing failed
    """
    if not part_file_path.exists():
        console.print(f"[bold red]Error:[/bold red] Part file not found: {part_file_path}")
        return None

    try:
        # Initialize min/max values for bounding box calculation
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
        vertices_found = 0

        if verbose:
            console.print(f"[dim]Parsing DAT file: {part_file_path}[/dim]")

        with open(part_file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line_num, line in enumerate(f, 1):
                parts = line.strip().split()
                if not parts:
                    continue

                # Line type 1 (triangles) and 3 (quadrilaterals) contain vertex coordinates
                if parts[0] in ('1', '3'):
                    # Number of vertices based on line type
                    num_vertices = 3 if parts[0] == '1' else 4

                    # Extract coordinates for each vertex
                    # Format: 1 color x1 y1 z1 x2 y2 z2 x3 y3 z3
                    # or:     3 color x1 y1 z1 x2 y2 z2 x3 y3 z3 x4 y4 z4
                    for i in range(num_vertices):
                        try:
                            # Get coordinates from appropriate positions
                            x_idx = 2 + i*3  # x coordinate index
                            y_idx = 3 + i*3  # y coordinate index
                            z_idx = 4 + i*3  # z coordinate index

                            if x_idx < len(parts) and y_idx < len(parts) and z_idx < len(parts):
                                x = float(parts[x_idx])
                                y = float(parts[y_idx])
                                z = float(parts[z_idx])

                                # Update min/max values
                                min_x = min(min_x, x)
                                min_y = min(min_y, y)
                                min_z = min(min_z, z)
                                max_x = max(max_x, x)
                                max_y = max(max_y, y)
                                max_z = max(max_z, z)

                                vertices_found += 1
                        except (IndexError, ValueError) as e:
                            if verbose:
                                console.print(f"[yellow]Warning:[/yellow] Error parsing line {line_num}: {e}")
                                console.print(f"[dim]Line content: {line.strip()}[/dim]")

        # Check if we found any vertices
        if vertices_found == 0:
            console.print(f"[yellow]Warning:[/yellow] No vertices found in {part_file_path}")
            return None

        # Calculate dimensions from bounding box
        width = max_x - min_x
        height = max_y - min_y
        depth = max_z - min_z

        # Calculate LDU to stud conversion (1 stud = 20 LDU)
        stud_width = width / 20.0
        stud_height = height / 20.0
        stud_depth = depth / 20.0

        # Approximate footprint in studs (based on width/depth)
        stud_count = stud_width * stud_depth

        # Calculate volume
        volume = width * height * depth
        volume_studs = stud_width * stud_height * stud_depth

        if verbose:
            console.print(f"[dim]Found {vertices_found} vertices[/dim]")
            console.print(f"[dim]Bounding box: ({min_x}, {min_y}, {min_z}) to ({max_x}, {max_y}, {max_z})[/dim]")
            console.print(f"[dim]Dimensions (LDU): {width:.2f} × {height:.2f} × {depth:.2f}[/dim]")
            console.print(f"[dim]Dimensions (studs): {stud_width:.2f} × {stud_height:.2f} × {stud_depth:.2f}[/dim]")
            console.print(f"[dim]Approximate stud count (footprint): {stud_count:.2f}[/dim]")

        return {
            # Raw dimensions in LDraw Units (LDU)
            "width_ldu": width,
            "height_ldu": height,
            "depth_ldu": depth,

            # Bounding box coordinates
            "min_x": min_x,
            "min_y": min_y,
            "min_z": min_z,
            "max_x": max_x,
            "max_y": max_y,
            "max_z": max_z,

            # Dimensions in studs (1 stud = 20 LDU)
            "width_studs": stud_width,
            "height_studs": stud_height,
            "depth_studs": stud_depth,

            # Derived measurements
            "stud_count": stud_count,  # Approximate footprint in studs
            "volume_ldu": volume,      # Volume in cubic LDU
            "volume_studs": volume_studs  # Volume in cubic studs
        }

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to parse part file: {e}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        return None


def is_valid_filename(filename: str) -> bool:
    """Check if a filename contains invalid characters."""
    # Common invalid characters in filenames across platforms
    invalid_chars = r'[<>:"/\\|?*]'
    return not bool(re.search(invalid_chars, str(filename)))


def crop_transparent_edges(image_path: Path, maintain_height: bool = True, verbose: bool = False) -> bool:
    """
    Crops transparent edges from a PNG image while optionally maintaining the original height.

    Args:
        image_path: Path to the PNG image
        maintain_height: If True, only crop horizontal transparent areas, preserving height
        verbose: Whether to print detailed information

    Returns:
        True if cropping was successful, False otherwise
    """
    if not PIL_AVAILABLE:
        if verbose:
            console.print("[yellow]Warning:[/yellow] PIL/Pillow not available, skipping transparent cropping.")
        return False

    try:
        # Open the image
        img = Image.open(image_path)

        # Get the alpha channel
        if img.mode != 'RGBA':
            if verbose:
                console.print(f"[yellow]Warning:[/yellow] Image is not RGBA, skipping transparent cropping.")
            return False

        # Get the size
        width, height = img.size
        if verbose:
            console.print(f"[dim]Original image size: {width}x{height}[/dim]")

        # Get the alpha data
        alpha = img.split()[3]

        # Get bounding box of non-transparent pixels
        bbox = alpha.getbbox()
        if not bbox:
            if verbose:
                console.print(f"[yellow]Warning:[/yellow] Image is entirely transparent.")
            return False

        left, upper, right, lower = bbox

        if maintain_height:
            # Only crop horizontally, keep full height
            bbox = (left, 0, right, height)
            if verbose:
                console.print(f"[dim]Maintaining height, cropping horizontally to: {left}, 0, {right}, {height}[/dim]")
        elif verbose:
            console.print(f"[dim]Cropping to: {left}, {upper}, {right}, {lower}[/dim]")

        # Crop the image
        cropped = img.crop(bbox)

        # Save the cropped image, overwriting the original
        cropped.save(image_path)

        new_width, new_height = cropped.size
        if verbose:
            console.print(f"[dim]New image size: {new_width}x{new_height}[/dim]")

        return True
    except Exception as e:
        if verbose:
            console.print(f"[red]Error during transparent cropping:[/red] {e}")
        return False


def _generate_single_image(
    part_number: str,
    output_path: Path,
    width: int,
    height: int,
    constrain_width: bool,
    edge_thickness: float,
    line_thickness: Optional[float],
    scale_size_not_lines: bool,
    size_scale_factor: float,
    crop_transparency: bool,
    view_latitude: float,
    view_longitude: float,
    ldview_app_path: Path,
    ldraw_dir: Path,
    dry_run: bool,
    verbose: bool,
) -> bool:
    """Helper function that generates a single image with the given parameters."""
    # Make sure output_path is absolute (critical for LDView running in a different directory)
    output_path = output_path.absolute()

    # Validate the output filename doesn't contain invalid characters
    if not is_valid_filename(output_path.name):
        console.print(f"[bold red]Error:[/bold red] Output filename '{output_path.name}' contains invalid characters.")
        console.print("[yellow]Wildcards like * and ? are not valid in filenames and won't be expanded as expected.[/yellow]")
        console.print("[yellow]Please use a valid filename without special characters.[/yellow]")
        return False

    # Ensure output directory exists
    try:
        output_dir = output_path.parent
        # If verbose or non-trivial directory (not just . or current dir)
        if verbose or str(output_dir) != ".":
            console.print(f"[dim]Creating output directory if needed: {output_dir}[/dim]")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Verify we can actually write to the directory
        try:
            test_file = output_dir / f"_test_write_{os.getpid()}.tmp"
            with open(test_file, 'w') as f:
                f.write('test')
            # Clean up the test file
            test_file.unlink()
            console.print(f"[dim]Verified write access to output directory: {output_dir}[/dim]")
        except (PermissionError, IOError) as e:
            console.print(f"[bold red]Error:[/bold red] Cannot write to output directory '{output_dir}': {e}")
            return False

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not create or validate output directory '{output_path.parent}': {e}")
        return False

    # Find and validate LDView executable
    ldview_executable = find_ldview_executable(ldview_app_path)
    if not ldview_executable:
        # Error message printed within find_ldview_executable
        return False
    if verbose:
        console.print(f"[dim]Using LDView executable: {ldview_executable}[/dim]")

    # Validate LDraw directory
    if not ldraw_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] LDraw directory not found: '{ldraw_dir}'")
        return False
    if verbose:
        console.print(f"[dim]Using LDraw directory: {ldraw_dir}[/dim]")

    # Find the part file
    part_file_path = find_part_file(ldraw_dir, part_number)
    if not part_file_path:
        # Error message printed within find_part_file
        return False

    # --- 2. LDView Command Construction ---
    # Set render dimensions based on constraints
    if constrain_width:
        # Use the specified width and set height to maintain a square initially
        # (LDView will autocrop later)
        render_width = width
        render_height = width  # Start with a square that will be cropped
    else:
        # Height-constrained approach (default)
        # We need to ensure the height stays consistent after autocrop
        # To do this, we'll disable autocrop and set a very large width to ensure
        # the entire part is visible, then we'll manage cropping ourselves
        render_height = height
        render_width = height * 6  # Use a wide aspect ratio to ensure part fits

    # Ensure part_file_path is absolute for reliable loading
    part_file_path = part_file_path.absolute()

    # Reference values for consistent line appearance
    BASE_EDGE_THICKNESS = 1.0
    BASE_LINE_THICKNESS = 1.0
    BASE_WIDTH = 320
    BASE_HEIGHT = 180

    # If line thickness not specified, use the same value as edge thickness
    actual_line_thickness = line_thickness if line_thickness is not None else edge_thickness

    # If we're scaling size instead of lines, adjust dimensions based on line thickness ratio
    if scale_size_not_lines:
        # Calculate scaling ratio from edge thickness (how much thicker than base)
        thickness_ratio = edge_thickness / BASE_EDGE_THICKNESS

        if constrain_width:
            # Scale width by the ratio to maintain visual consistency
            adjusted_width = int(render_width * thickness_ratio * size_scale_factor)
            adjusted_height = adjusted_width  # Start with square (will be autocropped)
        else:
            # Scale height by the ratio to maintain visual consistency
            adjusted_height = int(render_height * thickness_ratio * size_scale_factor)
            adjusted_width = adjusted_height  # Start with square (will be autocropped)

        # Adjust edge and line thickness to fixed base values
        adjusted_edge_thickness = BASE_EDGE_THICKNESS
        adjusted_line_thickness = BASE_LINE_THICKNESS if line_thickness is None else (line_thickness / edge_thickness) * BASE_LINE_THICKNESS

        if verbose:
            console.print(f"[dim]Scaling image size instead of lines:[/dim]")
            if constrain_width:
                console.print(f"[dim]- Original width: {render_width}, Edge thickness: {edge_thickness}[/dim]")
                console.print(f"[dim]- Adjusted width: {adjusted_width}, Edge thickness: {adjusted_edge_thickness}[/dim]")
            else:
                console.print(f"[dim]- Original height: {render_height}, Edge thickness: {edge_thickness}[/dim]")
                console.print(f"[dim]- Adjusted height: {adjusted_height}, Edge thickness: {adjusted_edge_thickness}[/dim]")
            console.print(f"[dim]- Scale factor: {size_scale_factor}[/dim]")
            console.print(f"[dim]- Line thickness: {adjusted_line_thickness}[/dim]")

        # Update values for command construction
        render_width = adjusted_width
        render_height = adjusted_height
        edge_thickness = adjusted_edge_thickness
        actual_line_thickness = adjusted_line_thickness

    if verbose:
        console.print(f"[dim]Edge thickness: {edge_thickness}[/dim]")
        console.print(f"[dim]Line thickness: {actual_line_thickness}[/dim]")
        console.print(f"[dim]Image dimensions: {render_width}x{render_height}px (before crop)[/dim]")
        console.print(f"[dim]Constraint: {'Width' if constrain_width else 'Height'}[/dim]")

    # Consistent settings for rendering quality and appearance
    # Ref: http://ldview.sourceforge.net/CommandOptions.html
    # Note: Some options might depend on your LDView version and configuration files.
    ldview_cmd: List[str] = [
        str(ldview_executable),
        str(part_file_path),
        # Output settings
        f"-SaveSnapshot={output_path}",
        f"-SaveWidth={render_width}",
        f"-SaveHeight={render_height}", # Initial dimensions before autocrop
        "-SaveAlpha=1",             # Crucial for transparency
    ]

    # Add autocrop option conditionally - only for width-constrained images
    if constrain_width:
        ldview_cmd.append("-AutoCrop=1")  # Crop tightly to the part for width-constrained
    else:
        # For height-constrained images, we want a fixed height with variable width
        # Disable autocrop to maintain the exact height we specified
        ldview_cmd.append("-AutoCrop=0")  # Don't autocrop for height-constrained

    # Continue with other visual settings
    ldview_cmd.extend([
        # Visual settings
        "-ShowAxes=0",              # Hide coordinate axes
        "-ShowEdges=1",             # Ensure edges are visible
        f"-EdgeThickness={edge_thickness}",  # Fine-tune edge appearance
        f"-LineThickness={actual_line_thickness}",  # Fine-tune conditional line appearance
        "-HiResPrimitives=1",       # Use high-resolution primitives (if available in your library)
        "-SmoothShading=1",         # Enable smooth shading for curved surfaces
        "-TextureMaps=1",           # Enable textures (if part uses them)
        "-Quality=4",               # Set rendering quality (0=low, 4=high)
        "-DefaultColor=0.8,0.8,0.8,1.0", # Set a default part color if none specified (RGBA, light gray) - Optional
        "-BackgroundColor=0,0,0,0", # Ensure background is transparent (RGBA)
        # Camera and Lighting (adjust for desired standard view)
        # Using combined latitude/longitude parameter as documented
        f"-DefaultLatLong={view_latitude},{view_longitude}",  # Combined latitude/longitude parameter (variable latitude and longitude)
        "-ZoomToFit",               # Zoom to fit the model optimally
        # "-LightVector=1,1,1",     # Example: Custom light direction (optional, default is usually okay)
        # "-Ambient=.3", "-Diffuse=.7" # Example: Adjust lighting intensity (optional)
    ])

    # --- 3. Execution ---
    # Nicely format command for printing
    cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in ldview_cmd)

    if dry_run:
        console.print("\n[bold yellow]-- Dry Run Mode --[/bold yellow]")
        console.print("Command that would be executed:")
        console.print(Panel(cmd_str, title="LDView Command", border_style="blue", expand=False))
        return True  # Consider dry run successful

    if scale_size_not_lines:
        if constrain_width:
            console.print(f"\n[magenta]Generating image with scaled size and constrained width:[/magenta]")
            console.print(f"(Auto-cropped to fit part while maintaining specified width)")
        else:
            console.print(f"\n[magenta]Generating image with scaled size and constrained height:[/magenta]")
            console.print(f"(Fixed height of {render_height}px with variable width)")
    else:
        if constrain_width:
            console.print(f"\n[magenta]Generating image with constrained width:[/magenta]")
            console.print(f"(Auto-cropped to fit part while maintaining specified width)")
        else:
            console.print(f"\n[magenta]Generating image with constrained height:[/magenta]")
            console.print(f"(Fixed height of {render_height}px with variable width)")

    console.print(f"'{output_path}' ({render_width}x{render_height}px before post-processing)")
    console.print(f"[dim]Absolute output path: {output_path.absolute()}[/dim]")

    if verbose:
        console.print(f"[dim]Executing: {cmd_str}[/dim]")

    try:
        # Determine appropriate CWD for LDView
        # On macOS, it often needs to be the dir containing the executable for resources
        cwd = ldview_executable.parent if ldview_executable else None
        if verbose:
            console.print(f"[dim]Using working directory: {cwd}[/dim]")

        process = subprocess.run(
            ldview_cmd,
            capture_output=True,
            text=True,
            check=False, # We check the return code manually
            cwd=cwd,
            encoding='utf-8', # Be explicit about encoding
            errors='replace' # Handle potential encoding errors in output
        )

        if verbose:
            console.print("\n[bold cyan]LDView stdout:[/bold cyan]")
            console.print(f"[cyan]{process.stdout.strip()}[/cyan]" if process.stdout.strip() else "[dim]No stdout[/dim]")
            console.print("\n[bold magenta]LDView stderr:[/bold magenta]")
            console.print(f"[magenta]{process.stderr.strip()}[/magenta]" if process.stderr.strip() else "[dim]No stderr[/dim]")

        # Check results
        if process.returncode != 0:
            console.print(f"\n[bold red]Error:[/bold red] LDView execution failed with code {process.returncode}.")
            if not verbose and process.stderr: # Print stderr if not already shown by verbose
                 console.print("[magenta]LDView stderr:[/magenta]")
                 console.print(f"[magenta]{process.stderr.strip()}[/magenta]")
            return False

        # Verify output file existence and size
        if not output_path.is_file():
            console.print(f"\n[bold red]Error:[/bold red] LDView ran successfully, but the output file was not created: '{output_path}'")
            console.print("[yellow]Check LDView configuration and permissions.[/yellow]")
            return False
        if output_path.stat().st_size == 0:
            console.print(f"\n[bold red]Error:[/bold red] LDView ran successfully, but the output file is empty: '{output_path}'")
            console.print("[yellow]Check LDView configuration and part file validity.[/yellow]")
            # Optionally remove the empty file
            # output_path.unlink()
            return False

        # Post-processing: Always crop transparent edges for height-constrained images
        if not constrain_width:
            if not PIL_AVAILABLE:
                console.print("[yellow]Warning:[/yellow] PIL/Pillow not available, skipping transparent cropping.")
                console.print("[yellow]Install with: pip install pillow[/yellow]")
            else:
                console.print("\n[magenta]Post-processing:[/magenta] Cropping transparent edges...")
                cropped = crop_transparent_edges(output_path, maintain_height=True, verbose=verbose)
                if cropped:
                    console.print("[dim]Transparent areas successfully cropped.[/dim]")
                else:
                    console.print("[yellow]Warning:[/yellow] Transparent cropping was skipped or failed.")

        # Success message
        console.print(f"\n[bold green]✅ Success![/bold green] Image generated successfully:")
        if scale_size_not_lines:
            constraint_type = "width" if constrain_width else "height"
            console.print(f"   [link=file://{output_path}]{output_path}[/link] (constrained {constraint_type}, scaled size: {render_width}x{render_height}px, scale factor: {size_scale_factor})")
        else:
            constraint_type = "width" if constrain_width else "height"
            console.print(f"   [link=file://{output_path}]{output_path}[/link] (constrained {constraint_type})")

        return True

    except FileNotFoundError:
        console.print(f"[bold red]Fatal Error:[/bold red] LDView command '{ldview_executable}' not found. Cannot execute.")
        console.print("Please ensure the --ldview-path is correct and LDView is installed properly.")
        return False
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during execution:[/bold red]")
        console.print(f"{e}")
        import traceback
        if verbose:
            console.print(traceback.format_exc())
        return False


@app.command()
def generate(
    part_number: str = typer.Argument(
        ...,
        help="The LDraw part number (e.g., '3001'). The '.dat' extension is added automatically."
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output", "-o",
        help="Path to save the output PNG file. Defaults to '<part_number>.png' in current directory if not specified.",
        writable=True, # Basic check if parent dir is writable
        resolve_path=True, # Resolve to absolute path
    ),
    width: Optional[int] = typer.Option(
        None,
        "--width", "-w",
        help="Width of the output image in pixels. Used when constraining by width. Specifying this disables proportional sizing.",
        min=10,
    ),
    height: Optional[int] = typer.Option(
        None,
        "--height", "-h",
        help="Height of the output image in pixels. Used when constraining by height. Specifying this disables proportional sizing.",
        min=10,
    ),
    constrain_width: bool = typer.Option(
        False,
        "--constrain-width", "-cw",
        help="Constrain the width of the image instead of the height (height is constrained by default).",
        is_flag=True,
    ),
    edge_thickness: float = typer.Option(
        4.0,
        "--edge-thickness", "-e",
        help="Thickness of part edges in the rendered image. Higher values create more pronounced outlines.",
        min=0.1,
        max=5.0,
    ),
    line_thickness: Optional[float] = typer.Option(
        4.0,
        "--line-thickness", "-l",
        help="Thickness of conditional lines in the rendered image. If not specified, matches edge thickness.",
        min=0.1,
        max=5.0,
    ),
    scale_size_not_lines: bool = typer.Option(
        False,
        "--scale-size-not-lines", "-s",
        help="Scale the image size proportionally to part size rather than line thickness. This keeps lines visually consistent across parts of different sizes.",
        is_flag=True,
    ),
    size_scale_factor: float = typer.Option(
        0.5,
        "--size-scale-factor", "-f",
        help="Scale factor for the final image size when using --scale-size-not-lines. Lower values produce smaller images (e.g., 0.5 for half size).",
        min=0.1,
        max=2.0,
    ),
    proportional_size: bool = typer.Option(
        True,
        "--proportional-size/--no-proportional-size", "-p/--no-p",
        help="Scale image size proportionally to part's physical dimensions (stud count). Larger parts get larger images, smaller parts get smaller images. This is the default unless width or height is specified.",
    ),
    base_pixels_per_stud: int = typer.Option(
        80,
        "--base-pixels-per-stud", "-ps",
        help="Base number of pixels per stud when using proportional sizing. A 1x1 part will be approximately this many pixels wide.",
        min=10,
        max=200,
    ),
    # Crop transparency is now always enabled for height-constrained images
    # crop_transparency: bool = typer.Option(
    #     False,
    #     "--crop-transparency/--no-crop-transparency",
    #     help="Crop transparent areas from the sides of the image while maintaining height. Requires PIL/Pillow. Disabled by default.",
    #     is_flag=True,
    # ),
    view_longitude: float = typer.Option(
        -30.0,
        "--lon", "--view-longitude", "--longitude",
        help="Camera longitude (horizontal rotation in degrees). -30 gives a slightly angled view, 0 for front view, 90 for side view.",
        min=-360.0,
        max=360.0,
    ),
    view_latitude: float = typer.Option(
        35.0,
        "--lat", "--view-latitude", "--latitude",
        help="Camera latitude (vertical rotation in degrees). 30 gives a slightly elevated view, 0 for level view, 90 for top-down view.",
        min=-90.0,
        max=90.0,
    ),
    ldview_path_str: str = typer.Option(
        str(DEFAULT_LDVIEW_APP_PATH),
        "--ldview-path",
        help="Path to the LDView application (e.g., /Applications/LDView.app) or executable.",
        envvar="LDVIEW_PATH", # Allow setting via environment variable
    ),
    ldraw_dir_str: str = typer.Option(
        str(DEFAULT_LDRAW_PARTS_PATH),
        "--ldraw-dir",
        help="Path to the root LDraw library directory (containing 'parts', 'p', etc.).",
        envvar="LDRAW_DIR", # Allow setting via environment variable
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the LDView command instead of executing it.",
        is_flag=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose output, including LDView's stdout/stderr.",
        is_flag=True,
    ),
    all_angles: bool = typer.Option(
        False,
        "--all-angles", "-a",
        help=f"Generate images at multiple preset longitude angles {DEFAULT_LONGITUDE_ANGLES}. Adds _lon## suffix to filenames.",
        is_flag=True,
    ),
):
    """
    Generates a cropped, transparent PNG snapshot of an LDraw part file using LDView.

    Ensures consistent camera, lighting, and quality settings.
    Requires LDView to be installed and configured.
    """
    console.print(f"[bold blue]🚀 Starting image generation for part:[/bold blue] [cyan]{part_number}[/cyan]")

    # Default width and height if not specified
    DEFAULT_WIDTH = 250
    DEFAULT_HEIGHT = 250

    # Handle auto-disable of proportional sizing when width or height is specified
    if (width is not None or height is not None) and proportional_size:
        console.print(f"[yellow]Note:[/yellow] Width or height specified, disabling proportional sizing.")
        proportional_size = False

    # Set default values if not provided
    if width is None:
        width = DEFAULT_WIDTH
    if height is None:
        height = DEFAULT_HEIGHT

    # Debug: Print all command line arguments
    if verbose:
        console.print(f"[dim]Command line arguments:[/dim]")
        console.print(f"[dim]- part_number: {part_number}[/dim]")
        console.print(f"[dim]- output: {output}[/dim]")
        console.print(f"[dim]- width: {width}[/dim]")
        console.print(f"[dim]- height: {height}[/dim]")
        console.print(f"[dim]- constrain_width: {constrain_width}[/dim]")
        console.print(f"[dim]- edge_thickness: {edge_thickness}[/dim]")
        console.print(f"[dim]- line_thickness: {line_thickness}[/dim]")
        console.print(f"[dim]- scale_size_not_lines: {scale_size_not_lines}[/dim]")
        console.print(f"[dim]- size_scale_factor: {size_scale_factor}[/dim]")
        console.print(f"[dim]- proportional_size: {proportional_size}[/dim]")
        console.print(f"[dim]- base_pixels_per_stud: {base_pixels_per_stud}[/dim]")
        # console.print(f"[dim]- crop_transparency: {crop_transparency}[/dim]")
        console.print(f"[dim]- view_longitude: {view_longitude}[/dim]")
        console.print(f"[dim]- view_latitude: {view_latitude}[/dim]")
        console.print(f"[dim]- ldview_path: {ldview_path_str}[/dim]")
        console.print(f"[dim]- ldraw_dir: {ldraw_dir_str}[/dim]")
        console.print(f"[dim]- all_angles: {all_angles}[/dim]")

    # --- 1. Path Setup & Validation ---
    ldview_app_path = Path(ldview_path_str).expanduser()
    ldraw_dir = Path(ldraw_dir_str).expanduser()

    # Set default output path if not provided
    if output is None:
        output_path = Path(f"{part_number}.png")
        console.print(f"[dim]No output path specified, using default: {output_path}[/dim]")
    else:
        output_path = output.expanduser() # Typer's resolve_path already does this, but belt-and-suspenders
        console.print(f"[dim]Output path specified: {output_path} (raw input: {output})[/dim]")

    # Find the part file path (for proportional sizing or all_angles)
    part_file_path = find_part_file(ldraw_dir, part_number)
    if not part_file_path:
        # Error message printed within find_part_file
        raise typer.Exit(code=1)

    # --- Handle proportional sizing if requested ---
    if proportional_size:
        # We need to get the part dimensions
        console.print(f"[bold magenta]Calculating proportional size based on part dimensions...[/bold magenta]")

        dimensions = get_part_dimensions_from_dat(part_file_path, verbose=verbose)

        if not dimensions:
            console.print(f"[yellow]Warning:[/yellow] Could not determine part dimensions. Using default sizing.")
            proportional_size = False
        else:
            # Calculate appropriate size based on stud count
            stud_count = dimensions["stud_count"]
            console.print(f"[dim]Part dimensions: {dimensions['width_studs']:.2f} × {dimensions['depth_studs']:.2f} studs (approx. {stud_count:.2f} studs footprint)[/dim]")

            # If part is very small (less than 1 stud footprint), use minimum size
            stud_count = max(1.0, stud_count)

            # Apply square root scaling to convert area (stud count) to linear dimension
            # This makes the scaling feel more natural - a 2x2 part will be sqrt(4) = 2x larger than a 1x1
            scaling_factor = math.sqrt(stud_count)

            # Apply the scaling to base_pixels_per_stud
            if constrain_width:
                width = int(base_pixels_per_stud * scaling_factor)
                console.print(f"[dim]Calculated proportional width: {width}px (base: {base_pixels_per_stud}, scaling: {scaling_factor:.2f}x)[/dim]")
            else:
                height = int(base_pixels_per_stud * scaling_factor)
                console.print(f"[dim]Calculated proportional height: {height}px (base: {base_pixels_per_stud}, scaling: {scaling_factor:.2f}x)[/dim]")

            # Disable other scaling options that might conflict
            if scale_size_not_lines:
                console.print(f"[yellow]Note:[/yellow] --proportional-size overrides --scale-size-not-lines")
                scale_size_not_lines = False

    # --- Check if we're generating multiple angles ---
    if all_angles:
        # We'll handle multiple angles in a loop
        if view_longitude != -30.0 and verbose:
            console.print(f"[yellow]Note:[/yellow] --lon value will be ignored when using --all-angles")

        console.print(f"[bold magenta]Generating images at multiple angles:[/bold magenta] {DEFAULT_LONGITUDE_ANGLES}")

        # Keep original output path for reference in messages
        original_output_path = output_path

        # For each angle in our predefined list
        for angle in DEFAULT_LONGITUDE_ANGLES:
            # Create a new filename with _lon## suffix
            # First, split the path into stem and suffix
            stem = output_path.stem
            suffix = output_path.suffix

            # Create new filename with angle suffix
            angle_output = output_path.with_name(f"{stem}_lon{angle}{suffix}")

            console.print(f"\n[bold cyan]Rendering angle: {angle}°[/bold cyan] -> {angle_output.name}")

            # Call the rendering function with the current angle
            _generate_single_image(
                part_number, angle_output, width, height, constrain_width,
                edge_thickness, line_thickness, scale_size_not_lines,
                size_scale_factor, False, view_latitude, angle,
                ldview_app_path, ldraw_dir, dry_run, verbose
            )

        # We've completed all angles
        console.print(f"\n[bold green]✅ All angles completed![/bold green] Images saved with _lon## suffixes.")
        raise typer.Exit(code=0)  # Exit after processing all angles

    # --- Standard single-angle rendering logic continues here ---
    # Just call our helper function with all the parameters
    success = _generate_single_image(
        part_number, output_path, width, height, constrain_width,
        edge_thickness, line_thickness, scale_size_not_lines,
        size_scale_factor, False, view_latitude, view_longitude,
        ldview_app_path, ldraw_dir, dry_run, verbose
    )

    # Return appropriate exit code
    if not success:
        raise typer.Exit(code=1)
    else:
        raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
