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
# - Latitude: 30
# - Longitude -30

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
from pathlib import Path
from typing import Optional, List
import re  # Add regex for validating filenames

# Rich and Colorama for styled output
from rich.console import Console
from rich.panel import Panel
import colorama

# Initialize Rich Console and Colorama
colorama.init()
console = Console()

# Default paths (adjust if your setup differs)
# User specified ~/Library/ldraw/parts/
DEFAULT_LDRAW_PARTS_PATH = Path("~/Library/ldraw/parts").expanduser()
# Default for macOS, adjust for other OS if needed
DEFAULT_LDVIEW_APP_PATH = Path("/Applications/LDView.app")


app = typer.Typer(
    help="🖼️ Generate consistent PNG images of LEGO parts using LDView.",
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


def is_valid_filename(filename: str) -> bool:
    """Check if a filename contains invalid characters."""
    # Common invalid characters in filenames across platforms
    invalid_chars = r'[<>:"/\\|?*]'
    return not bool(re.search(invalid_chars, str(filename)))


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
    width: int = typer.Option(
        320,
        "--width", "-w",
        help="Width of the output image in pixels. Height is set automatically by LDView.",
        min=10,
    ),
    edge_thickness: float = typer.Option(
        4.0,
        "--edge-thickness", "-e",
        help="Thickness of part edges in the rendered image. Higher values create more pronounced outlines.",
        min=0.1,
        max=5.0,
    ),
    line_thickness: Optional[float] = typer.Option(
        None,
        "--line-thickness", "-l",
        help="Thickness of conditional lines in the rendered image. If not specified, matches edge thickness.",
        min=0.1,
        max=5.0,
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
):
    """
    Generates a cropped, transparent PNG snapshot of an LDraw part file using LDView.

    Ensures consistent camera, lighting, and quality settings.
    Requires LDView to be installed and configured.
    """
    console.print(f"[bold blue]🚀 Starting image generation for part:[/bold blue] [cyan]{part_number}[/cyan]")

    # Debug: Print all command line arguments
    if verbose:
        console.print(f"[dim]Command line arguments:[/dim]")
        console.print(f"[dim]- part_number: {part_number}[/dim]")
        console.print(f"[dim]- output: {output}[/dim]")
        console.print(f"[dim]- width: {width}[/dim]")
        console.print(f"[dim]- edge_thickness: {edge_thickness}[/dim]")
        console.print(f"[dim]- line_thickness: {line_thickness}[/dim]")
        console.print(f"[dim]- ldview_path: {ldview_path_str}[/dim]")
        console.print(f"[dim]- ldraw_dir: {ldraw_dir_str}[/dim]")

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

    # Make sure output_path is absolute (critical for LDView running in a different directory)
    output_path = output_path.absolute()

    # Validate the output filename doesn't contain invalid characters
    if not is_valid_filename(output_path.name):
        console.print(f"[bold red]Error:[/bold red] Output filename '{output_path.name}' contains invalid characters.")
        console.print("[yellow]Wildcards like * and ? are not valid in filenames and won't be expanded as expected.[/yellow]")
        console.print("[yellow]Please use a valid filename without special characters.[/yellow]")

        # Special note for shell wildcards
        if '*' in output_path.name or '?' in output_path.name:
            console.print("\n[blue]Note about shell wildcards:[/blue]")
            console.print("If you intended to use shell wildcards (like *) for multiple files, this isn't supported directly.")
            console.print("The shell might have tried to expand the wildcard but found no matches, or passed it literally.")
            console.print("To generate images for multiple parts, you could create a shell script or loop:")
            console.print("[dim]  for part in 3001 3002 3003; do[/dim]")
            console.print("[dim]    python generate-part-image.py $part[/dim]")
            console.print("[dim]  done[/dim]")

        raise typer.Exit(code=1)

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
            raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Could not create or validate output directory '{output_path.parent}': {e}")
        raise typer.Exit(code=1)

    # Find and validate LDView executable
    ldview_executable = find_ldview_executable(ldview_app_path)
    if not ldview_executable:
        # Error message printed within find_ldview_executable
        raise typer.Exit(code=1)
    if verbose:
        console.print(f"[dim]Using LDView executable: {ldview_executable}[/dim]")

    # Validate LDraw directory
    if not ldraw_dir.is_dir():
        console.print(f"[bold red]Error:[/bold red] LDraw directory not found: '{ldraw_dir}'")
        raise typer.Exit(code=1)
    if verbose:
        console.print(f"[dim]Using LDraw directory: {ldraw_dir}[/dim]")

    # Find the part file
    part_file_path = find_part_file(ldraw_dir, part_number)
    if not part_file_path:
        # Error message printed within find_part_file
        raise typer.Exit(code=1)

    # --- 2. LDView Command Construction ---
    # Set height equal to width for initial render square, AutoCrop will adjust
    height = width

    # Ensure part_file_path is absolute for reliable loading
    part_file_path = part_file_path.absolute()

    # If line thickness not specified, use the same value as edge thickness
    actual_line_thickness = line_thickness if line_thickness is not None else edge_thickness

    if verbose:
        console.print(f"[dim]Edge thickness: {edge_thickness}[/dim]")
        console.print(f"[dim]Line thickness: {actual_line_thickness}[/dim]")

    # Consistent settings for rendering quality and appearance
    # Ref: http://ldview.sourceforge.net/CommandOptions.html
    # Note: Some options might depend on your LDView version and configuration files.
    ldview_cmd: List[str] = [
        str(ldview_executable),
        str(part_file_path),
        # Output settings
        f"-SaveSnapshot={output_path}",
        f"-SaveWidth={width}",
        f"-SaveHeight={height}", # Render square initially
        "-SaveAlpha=1",             # Crucial for transparency
        "-AutoCrop=1",              # Crop tightly to the part
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
        "-DefaultLat=30",           # Camera latitude (elevation angle)
        "-DefaultLon=45",           # Camera longitude (azimuth angle)
        "-ZoomToFit",               # Zoom to fit the model optimally
        # "-LightVector=1,1,1",     # Example: Custom light direction (optional, default is usually okay)
        # "-Ambient=.3", "-Diffuse=.7" # Example: Adjust lighting intensity (optional)
    ]

    # --- 3. Execution ---
    # Nicely format command for printing
    cmd_str = " ".join(f'"{arg}"' if " " in arg else arg for arg in ldview_cmd)

    if dry_run:
        console.print("\n[bold yellow]-- Dry Run Mode --[/bold yellow]")
        console.print("Command that would be executed:")
        console.print(Panel(cmd_str, title="LDView Command", border_style="blue", expand=False))
        raise typer.Exit(code=0)

    console.print(f"\n[magenta]Generating image:[/magenta] '{output_path}' ({width}x{height}px before crop)...")
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
            raise typer.Exit(code=1)

        # Verify output file existence and size
        if not output_path.is_file():
            console.print(f"\n[bold red]Error:[/bold red] LDView ran successfully, but the output file was not created: '{output_path}'")
            console.print("[yellow]Check LDView configuration and permissions.[/yellow]")
            raise typer.Exit(code=1)
        if output_path.stat().st_size == 0:
            console.print(f"\n[bold red]Error:[/bold red] LDView ran successfully, but the output file is empty: '{output_path}'")
            console.print("[yellow]Check LDView configuration and part file validity.[/yellow]")
            # Optionally remove the empty file
            # output_path.unlink()
            raise typer.Exit(code=1)

        console.print(f"\n[bold green]✅ Success![/bold green] Image generated successfully:")
        console.print(f"   [link=file://{output_path}]{output_path}[/link]")

    except FileNotFoundError:
        console.print(f"[bold red]Fatal Error:[/bold red] LDView command '{ldview_executable}' not found. Cannot execute.")
        console.print("Please ensure the --ldview-path is correct and LDView is installed properly.")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred during execution:[/bold red]")
        console.print(f"{e}")
        import traceback
        if verbose:
            console.print(traceback.format_exc())
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
