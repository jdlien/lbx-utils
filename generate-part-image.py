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
#
#
# TODO:
# - Ensure that specifying width or height automatically overrides distance
# - I'm unsure if line-thickness actually does anything useful. More testing is required



import typer
import subprocess
import os
import sys
import math
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import re  # Add regex for validating filenames
from dataclasses import dataclass, field

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

@dataclass
class Config:
    """Configuration settings for the application."""
    # Default paths
    LDRAW_PARTS_PATH: Path = Path("~/Library/ldraw/parts").expanduser()
    LDVIEW_APP_PATH: Path = Path("/Applications/LDView.app")

    # Default camera angles
    DEFAULT_LONGITUDE_ANGLES: List[int] = field(default_factory=lambda: [-120, -60, -30, 0, 30, 60, 120])
    DEFAULT_LONGITUDE: float = -30.0
    DEFAULT_LATITUDE: float = 35.0
    DEFAULT_CAMERA_DISTANCE: float = 250.0  # 0 means let LDView determine distance automatically

    # Default image settings
    DEFAULT_WIDTH: int = 250
    DEFAULT_HEIGHT: int = 250
    DEFAULT_EDGE_THICKNESS: float = 4.0
    DEFAULT_LINE_THICKNESS: float = 4.0
    DEFAULT_SIZE_SCALE_FACTOR: float = 0.5

    # Reference values for consistent line appearance
    BASE_EDGE_THICKNESS: float = 1.0
    BASE_LINE_THICKNESS: float = 1.0
    BASE_WIDTH: int = 320
    BASE_HEIGHT: int = 180

    # LDraw unit conversion constants
    LDU_PER_STUD: float = 20.0
    LDU_PER_BRICK_HEIGHT: float = 24.0

    # Application behavior settings
    VERBOSE: bool = False  # Controls the amount of output displayed

# Create global config instance
config = Config()

app = typer.Typer(
    help="🖼️ Generate consistent PNG images of LEGO parts using LDView.",
    add_completion=False,
    rich_markup_mode="markdown",
)


def find_ldview_executable(ldview_app_path: Path) -> Optional[Path]:
    """
    Finds the LDView executable within the .app bundle on macOS.
    Currently only supports macOS.
    """
    if sys.platform != "darwin":
        console.print("[bold red]Error:[/bold red] This functionality is only supported on macOS at this time.")
        return None

    if ldview_app_path.suffix == ".app":
        # Standard macOS .app bundle structure
        potential_path = ldview_app_path / "Contents" / "MacOS" / "LDView"
        if potential_path.is_file() and os.access(potential_path, os.X_OK):
            if config.VERBOSE:
                console.print(f"[dim]Found macOS LDView executable: {potential_path}[/dim]")
            return potential_path
        else:
            console.print(f"[yellow]Warning:[/yellow] Could not find executable at standard macOS path: {potential_path}")
            return None
    else:
        console.print(f"[yellow]Warning:[/yellow] Expected a .app path for macOS, got: {ldview_app_path}")
        # Check if the provided path is directly executable
        if ldview_app_path.is_file() and os.access(ldview_app_path, os.X_OK):
            if config.VERBOSE:
                console.print(f"[dim]Using provided path directly: {ldview_app_path}[/dim]")
            return ldview_app_path
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
            if config.VERBOSE: console.print(f"Found part file: '{part_path}'")
            return part_path

    # If not found, log checked paths
    checked_paths = [str(d / part_file_name) for d in search_dirs]
    console.print(f"[bold red]Error:[/bold red] Part file '{part_file_name}' not found in LDraw directory '{ldraw_dir}'.")
    console.print(f"[dim]Checked paths:\n- " + "\n- ".join(checked_paths) + "[/dim]")
    return None


def is_valid_filename(filename: str) -> bool:
    """Check if a filename contains invalid characters."""
    # Common invalid characters in filenames across platforms
    invalid_chars = r'[<>:"/\\|?*]'
    return not bool(re.search(invalid_chars, str(filename)))


def crop_transparent_edges(image_path: Path, maintain_height: bool = True) -> bool:
    """
    Crops transparent edges from a PNG image while optionally maintaining the original height.

    Args:
        image_path: Path to the PNG image
        maintain_height: If True, only crop horizontal transparent areas, preserving height

    Returns:
        True if cropping was successful, False otherwise
    """
    if not PIL_AVAILABLE:
        if config.VERBOSE:
            console.print("[yellow]Warning:[/yellow] PIL/Pillow not available, skipping transparent cropping.")
        return False

    try:
        # Open the image
        img = Image.open(image_path)

        # Get the alpha channel
        if img.mode != 'RGBA':
            if config.VERBOSE:
                console.print(f"[yellow]Warning:[/yellow] Image is not RGBA, skipping transparent cropping.")
            return False

        # Get the size
        width, height = img.size
        if config.VERBOSE:
            console.print(f"[dim]Original image size: {width}x{height}[/dim]")

        # Get the alpha data
        alpha = img.split()[3]

        # Get bounding box of non-transparent pixels
        bbox = alpha.getbbox()
        if not bbox:
            if config.VERBOSE:
                console.print(f"[yellow]Warning:[/yellow] Image is entirely transparent.")
            return False

        left, upper, right, lower = bbox

        if maintain_height:
            # Only crop horizontally, keep full height
            bbox = (left, 0, right, height)
            if config.VERBOSE:
                console.print(f"[dim]Maintaining height, cropping horizontally to: {left}, 0, {right}, {height}[/dim]")
        elif config.VERBOSE:
            console.print(f"[dim]Cropping to: {left}, {upper}, {right}, {lower}[/dim]")

        # Crop the image
        cropped = img.crop(bbox)

        # Save the cropped image, overwriting the original
        cropped.save(image_path)

        new_width, new_height = cropped.size
        if config.VERBOSE:
            console.print(f"[dim]New image size: {new_width}x{new_height}[/dim]")

        return True
    except Exception as e:
        if config.VERBOSE:
            console.print(f"[red]Error during transparent cropping:[/red] {e}")
        return False


def optimize_image(image_path: Path) -> bool:
    """
    Optimize the PNG image to reduce file size.
    Focuses on converting RGBA to LA mode (grayscale+alpha) which is much more efficient
    for LDraw part images that are primarily grayscale with transparency.

    Args:
        image_path: Path to the PNG image to optimize

    Returns:
        True if optimization was successful, False otherwise
    """
    if not PIL_AVAILABLE:
        if config.VERBOSE:
            console.print("[yellow]Warning:[/yellow] PIL/Pillow not available, skipping image optimization.")
        return False

    try:
        # Get original file size for comparison
        original_size = image_path.stat().st_size

        # Open the image
        img = Image.open(image_path)

        # Only try LA mode for grayscale+alpha which is typically the most effective
        # for LDraw part images
        if img.mode == 'RGBA':
            # Use PIL's built-in conversion to LA mode which is much faster and more reliable
            la_img = img.convert('LA')

            # Save with optimization
            la_img.save(image_path, optimize=True)

            # Check size improvement
            new_size = image_path.stat().st_size

            if config.VERBOSE and new_size < original_size:
                reduction = (original_size - new_size) / original_size * 100
                console.print(f"[dim]Image optimized: {original_size:,} → {new_size:,} bytes ({reduction:.1f}% reduction)[/dim]")

            return True
        else:
            # For non-RGBA images, just optimize the existing format
            img.save(image_path, optimize=True)

            if config.VERBOSE:
                new_size = image_path.stat().st_size
                if new_size < original_size:
                    reduction = (original_size - new_size) / original_size * 100
                    console.print(f"[dim]Image optimized: {original_size:,} → {new_size:,} bytes ({reduction:.1f}% reduction)[/dim]")
                else:
                    console.print("[dim]No significant size improvement from optimization[/dim]")

            return True

    except Exception as e:
        if config.VERBOSE:
            console.print(f"[yellow]Warning:[/yellow] Image optimization failed: {e}")
        return False


def _generate_single_image(
    part_number: str,
    output_path: Path,
    width: int,
    height: int,
    constrain_width: bool,
    edge_thickness: float,
    line_thickness: Optional[float],
    crop_transparency: bool,
    view_latitude: float,
    view_longitude: float,
    camera_distance: float,
    ldview_executable: Path,
    ldraw_dir: Path,
    dry_run: bool,
) -> bool:
    """Helper function that generates a single image with the given parameters."""
    # Make sure output_path is absolute (critical for LDView running in a different directory)
    output_path = output_path.absolute()

    # Validate the output filename doesn't contain invalid characters
    if not is_valid_filename(output_path.name):
        console.print(f"[bold red]Error:[/bold red] Output filename '{output_path.name}' contains invalid characters.")
        return False

    # Ensure output directory exists
    try:
        output_dir = output_path.parent
        # If verbose or non-trivial directory (not just . or current dir)
        if config.VERBOSE or str(output_dir) != ".":
            if config.VERBOSE: console.print(f"[dim]Creating output directory if needed: {output_dir}[/dim]")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Verify we can actually write to the directory
        try:
            test_file = output_dir / f"_test_write_{os.getpid()}.tmp"
            with open(test_file, 'w') as f:
                f.write('test')
            # Clean up the test file
            test_file.unlink()
            # console.print(f"[dim]Verified write access to output directory: {output_dir}[/dim]")
        except (PermissionError, IOError) as e:
            console.print(f"[bold red]Error:[/bold red] Cannot write to output directory '{output_dir}': {e}")
            return False

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not create or validate output directory '{output_path.parent}': {e}")
        return False

    # Verify that ldview_executable exists
    if not ldview_executable or not ldview_executable.exists():
        console.print(f"[bold red]Error:[/bold red] LDView executable not found at path: {ldview_executable}")
        return False
    if config.VERBOSE:
        console.print(f"[dim]Using LDView executable: {ldview_executable}[/dim]")

    # Validate LDraw directory
    if not ldraw_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] LDraw directory not found: '{ldraw_dir}'")
        return False
    if config.VERBOSE:
        console.print(f"[dim]Using LDraw directory: {ldraw_dir}[/dim]")

    # Find the part file
    part_file_path = find_part_file(ldraw_dir, part_number)
    if not part_file_path:
        # Error message printed within find_part_file
        return False

    # --- 2. LDView Command Construction ---
    # Set render dimensions based on constraints
    if camera_distance > 0:
        # When using a custom distance, we need a large height so the part is fully visible
        render_height = 1500
        render_width = 2500
    elif constrain_width:
        # Use the specified width and set height to maintain a square initially
        render_width = width
        render_height = width  # Start with a square that will be cropped
    else:
        # Height-constrained approach (default)
        render_height = height
        render_width = height * 6  # Use a wide aspect ratio to ensure part fits

    # Ensure part_file_path is absolute for reliable loading
    part_file_path = part_file_path.absolute()

    # If line thickness not specified, use the same value as edge thickness
    actual_line_thickness = line_thickness if line_thickness is not None else edge_thickness

    # Initialize the command list
    ldview_cmd: List[str] = [
        str(ldview_executable),
        str(part_file_path),
        # Output settings
        f"-SaveSnapshot={output_path}",
        f"-SaveWidth={render_width}",
        f"-SaveHeight={render_height}", # Initial dimensions before autocrop
        "-SaveAlpha=1",             # Crucial for transparency
    ]

    # We don't autocrop, as we handle that as a separate step after rendering
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
    ])

    # Add camera settings based on whether a custom distance is specified
    if camera_distance > 0:
        # We need a fairly large height to ensure the part is visible at a custom distance
        render_height = 1500
        # When using a custom distance, use the camera globe parameter with distance
        ldview_cmd.append(f"-cg{view_latitude},{view_longitude},{camera_distance*1000}")  # Camera position with specific distance
        ldview_cmd.append("-ZoomToFit=0")  # Don't auto-adjust the camera distance when using cg with distance
        # ldview_cmd.append("-ZoomMax=10000") # Allow high zoom values for flexibility

    else:
        # When no custom distance is specified, use DefaultLatLong (without setting distance)
        ldview_cmd.append(f"-DefaultLatLong={view_latitude},{view_longitude}")  # Standard lat/lon positioning
        ldview_cmd.append("-ZoomToFit=1")  # Let LDView calculate the appropriate distance

    # Add additional camera settings that may be needed
    ldview_cmd.extend([
        "-FOV=0.1",  # Use a small Field of View (like a telephoto lens) to reduce perspective distortion
        # "-LightVector=1,1,1",     # Example: Custom light direction (optional, default is usually okay)
        # "-Ambient=.3", "-Diffuse=.7" # Example: Adjust lighting intensity (optional)
    ])

    # --- 3. Execution ---
    # Nicely format command for printing
    cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in ldview_cmd)

    if dry_run:
        console.print("\n[bold yellow]-- Dry Run Mode --[/bold yellow]")
        console.print("[bold blue]Command that would be executed:[/bold blue]")

        # Format each option on its own line for better readability
        formatted_cmd = f"{ldview_cmd[0]} \\\n"
        formatted_cmd += f"    {ldview_cmd[1]} \\\n"
        for arg in ldview_cmd[2:]:
            formatted_cmd += f"    {arg} \\\n"
        # Remove the trailing backslash and newline
        formatted_cmd = formatted_cmd.rstrip(" \\\n")

        # Print without panel for easier copying
        console.print(formatted_cmd)
        return True  # Consider dry run successful

    if config.VERBOSE:
        if camera_distance > 0:
            console.print(f"[magenta]Generating image at distance: {camera_distance}[/magenta]")
        elif constrain_width:
          console.print(f"[magenta]Generating image with constrained width:[/magenta]")
        else:
          console.print(f"[magenta]Generating image with constrained height:[/magenta]")
          if config.VERBOSE:
              console.print(f"(Fixed height of {render_height}px with variable width)")

        console.print(f"({render_width}x{render_height}px before post-processing)")
        console.print(f"[dim]Absolute output path: {output_path.absolute()}[/dim]")
        console.print(f"[dim]Executing: {cmd_str}[/dim]")

    try:
        # Determine appropriate CWD for LDView
        # On macOS, it often needs to be the dir containing the executable for resources
        cwd = ldview_executable.parent if sys.platform == "darwin" else None
        if config.VERBOSE and cwd:
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

        if config.VERBOSE:
            console.print("\n[bold cyan]LDView stdout:[/bold cyan]")
            console.print(f"[cyan]{process.stdout.strip()}[/cyan]" if process.stdout.strip() else "[dim]No stdout[/dim]")
            console.print("\n[bold magenta]LDView stderr:[/bold magenta]")
            console.print(f"[magenta]{process.stderr.strip()}[/magenta]" if process.stderr.strip() else "[dim]No stderr[/dim]")

        # Check results
        if process.returncode != 0:
            console.print(f"\n[bold red]Error:[/bold red] LDView execution failed with code {process.returncode}.")
            if not config.VERBOSE and process.stderr: # Print stderr if not already shown by verbose
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

        # Post-processing: Always crop transparent edges
        if not PIL_AVAILABLE:
            console.print("[yellow]Warning:[/yellow] PIL/Pillow not available, skipping transparent cropping.")
            console.print("[yellow]Install with: pip install pillow[/yellow]")
        else:
            # Set maintain_height to False if constrain_width is True OR camera_distance > 0
            maintain_height = not (constrain_width or camera_distance > 0)
            cropped = crop_transparent_edges(output_path, maintain_height=maintain_height)
            if not cropped:
                console.print("[yellow]Warning:[/yellow] Transparent cropping was skipped or failed.")
            # Optimize image size (Experimental)
            optimize_image(output_path)
        # Success message
        if config.VERBOSE: console.print(f"\n[bold green]✅ Success![/bold green] Image generated successfully:")

        constraint_type = "width" if constrain_width else "height"
        console.print(f"[link=file://{output_path}]{output_path}[/link]")

        return True

    except FileNotFoundError:
        console.print(f"[bold red]Fatal Error:[/bold red] LDView command '{ldview_executable}' not found. Cannot execute.")
        console.print("Please ensure the --ldview-path is correct and LDView is installed properly.")
        return False
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during execution:[/bold red]")
        console.print(f"{e}")
        import traceback
        if config.VERBOSE:
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
        help="Width of the output image in pixels. Used when constraining by width.",
        min=10,
    ),
    height: Optional[int] = typer.Option(
        None,
        "--height", "-h",
        help="Height of the output image in pixels. Used when constraining by height.",
        min=10,
    ),
    constrain_width: bool = typer.Option(
        False,
        "--constrain-width", "-cw",
        help="Constrain the width of the image instead of the height.",
        is_flag=True,
    ),
    edge_thickness: float = typer.Option(
        config.DEFAULT_EDGE_THICKNESS,
        "--edge-thickness", "-e",
        help="Thickness of part edges in the rendered image. Higher values create more pronounced outlines.",
        min=0.1,
        max=5.0,
    ),
    line_thickness: Optional[float] = typer.Option(
        config.DEFAULT_LINE_THICKNESS,
        "--line-thickness", "-l",
        help="Thickness of conditional lines in the rendered image. If not specified, matches edge thickness.",
        min=0.1,
        max=5.0,
    ),
    view_longitude: float = typer.Option(
        config.DEFAULT_LONGITUDE,
        "--lon", "--view-longitude", "--longitude",
        help="Camera longitude (horizontal rotation in degrees). -30 gives a slightly angled view, 0 for front view, 90 for side view.",
        min=-360.0,
        max=360.0,
    ),
    view_latitude: float = typer.Option(
        config.DEFAULT_LATITUDE,
        "--lat", "--view-latitude", "--latitude",
        help="Camera latitude (vertical rotation in degrees). 30 gives a slightly elevated view, 0 for level view, 90 for top-down view.",
        min=-90.0,
        max=90.0,
    ),
    camera_distance: float = typer.Option(
        config.DEFAULT_CAMERA_DISTANCE,
        "--distance", "-d",
        help="Camera distance from the model (in kLDU). If 0, LDView determines distance automatically based on model size and the part will be zoomed to fit a fixed height by default. "
             "Set to >300 to make large part outlines more pronounced for small labels.",
        min=0.0,
        max=2000.0,
    ),
    ldview_path_str: str = typer.Option(
        str(config.LDVIEW_APP_PATH),
        "--ldview-path",
        help="Path to the LDView application (e.g., /Applications/LDView.app) or executable.",
        envvar="LDVIEW_PATH", # Allow setting via environment variable
    ),
    ldraw_dir_str: str = typer.Option(
        str(config.LDRAW_PARTS_PATH),
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
        help="Enable verbose output, including LDView's stdout/stderr and detailed progress information.",
        is_flag=True,
    ),
    all_angles: bool = typer.Option(
        False,
        "--all-angles", "-a",
        help=f"Generate images at multiple preset longitude angles {config.DEFAULT_LONGITUDE_ANGLES}. Adds _lon## suffix to filenames.",
        is_flag=True,
    ),
):
    """
    Generates a cropped, transparent PNG snapshot of an LDraw part file using LDView.

    Ensures consistent camera, lighting, and quality settings.
    Requires LDView to be installed and configured.
    """
    # Set the global verbosity level based on command-line flag
    config.VERBOSE = verbose

    if config.VERBOSE: console.print(f"[bold blue]🚀 Starting image generation for part:[/bold blue] [cyan]{part_number}[/cyan]")

    # Set default values if not provided
    if width is None:
        width = config.DEFAULT_WIDTH
    if height is None:
        height = config.DEFAULT_HEIGHT

    # Debug: Print all command line arguments
    if config.VERBOSE:
        console.print(f"[dim]Command line arguments:[/dim]")
        console.print(f"[dim]- part_number: {part_number}[/dim]")
        console.print(f"[dim]- output: {output}[/dim]")
        console.print(f"[dim]- width: {width}[/dim]")
        console.print(f"[dim]- height: {height}[/dim]")
        console.print(f"[dim]- constrain_width: {constrain_width}[/dim]")
        console.print(f"[dim]- edge_thickness: {edge_thickness}[/dim]")
        console.print(f"[dim]- line_thickness: {line_thickness}[/dim]")
        console.print(f"[dim]- view_longitude: {view_longitude}[/dim]")
        console.print(f"[dim]- view_latitude: {view_latitude}[/dim]")
        console.print(f"[dim]- camera_distance: {camera_distance}[/dim]")
        console.print(f"[dim]- ldview_path: {ldview_path_str}[/dim]")
        console.print(f"[dim]- ldraw_dir: {ldraw_dir_str}[/dim]")
        console.print(f"[dim]- all_angles: {all_angles}[/dim]")

    # --- 1. Path Setup & Validation ---
    ldview_app_path = Path(ldview_path_str).expanduser()
    ldraw_dir = Path(ldraw_dir_str).expanduser()

    # Find the LDView executable once
    ldview_executable = find_ldview_executable(ldview_app_path)
    if not ldview_executable:
        console.print(f"[bold red]Error:[/bold red] Could not find LDView executable at {ldview_app_path}")
        raise typer.Exit(code=1)

    if config.VERBOSE:
        console.print(f"[dim]Using LDView executable: {ldview_executable}[/dim]")

    # Validate LDraw directory
    if not ldraw_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] LDraw directory not found: '{ldraw_dir}'")
        raise typer.Exit(code=1)
    if config.VERBOSE:
        console.print(f"[dim]Using LDraw directory: {ldraw_dir}[/dim]")

    # Find the part file
    part_file_path = find_part_file(ldraw_dir, part_number)
    if not part_file_path:
        # Error message printed within find_part_file
        raise typer.Exit(code=1)

    # Set default output path if not provided
    if output is None:
        output_path = Path(f"{part_number}.png")
        if config.VERBOSE:
            console.print(f"[dim]No output path specified, using default: {output_path}[/dim]")
    else:
        output_path = output.expanduser() # Typer's resolve_path already does this, but belt-and-suspenders
        if config.VERBOSE:
            console.print(f"[dim]Output path specified: {output_path} (raw input: {output})[/dim]")

    # --- Check if we're generating multiple angles ---
    if all_angles:
        # We'll handle multiple angles in a loop
        if view_longitude != config.DEFAULT_LONGITUDE and config.VERBOSE:
            console.print(f"[yellow]Note:[/yellow] --lon value will be ignored when using --all-angles")

        console.print(f"[bold magenta]Generating images at multiple angles:[/bold magenta] {config.DEFAULT_LONGITUDE_ANGLES}")

        # Keep original output path for reference in messages
        original_output_path = output_path

        # For each angle in our predefined list
        for angle in config.DEFAULT_LONGITUDE_ANGLES:
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
                edge_thickness, line_thickness, False, view_latitude, angle,
                camera_distance, ldview_executable, ldraw_dir, dry_run
            )

        # We've completed all angles
        console.print(f"\n[bold green]✅ All angles completed![/bold green] Images saved with _lon## suffixes.")
        raise typer.Exit(code=0)  # Exit after processing all angles

    # --- Standard single-angle rendering logic continues here ---
    # Just call our helper function with all the parameters, using the executable path we already found
    success = _generate_single_image(
        part_number, output_path, width, height, constrain_width,
        edge_thickness, line_thickness, False, view_latitude, view_longitude,
        camera_distance, ldview_executable, ldraw_dir, dry_run
    )

    # Return appropriate exit code
    if not success:
        raise typer.Exit(code=1)
    else:
        raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
