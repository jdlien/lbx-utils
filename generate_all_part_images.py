#!/usr/bin/env python3

"""
Script to generate PNG images for all LDraw .dat files in the ldraw/parts directory.
This uses the generate-part-image.py script to create consistent images.
"""

import os
import sys
import argparse
import multiprocessing
from pathlib import Path
import subprocess
from typing import List, Optional, Tuple
import glob
from concurrent.futures import ProcessPoolExecutor, as_completed

# Rich for colored output
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
import colorama

# Initialize console
colorama.init()
console = Console()

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate PNG images for all LDraw parts")
    parser.add_argument(
        "--ldraw-dir",
        type=str,
        default=os.path.expanduser("~/Library/ldraw"),
        help="Path to LDraw directory (default: ~/Library/ldraw)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="part-images",
        help="Directory to save the generated images (default: part-images)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing images"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--jobs", "-j",
        type=int,
        default=multiprocessing.cpu_count(),
        help=f"Number of parallel jobs (default: {multiprocessing.cpu_count()} - all CPU cores)"
    )
    return parser.parse_args()

def get_part_files(ldraw_dir: str) -> List[Path]:
    """Get list of all .dat files in the ldraw/parts directory."""
    parts_dir = Path(ldraw_dir) / "parts"
    if not parts_dir.exists():
        console.print(f"[bold red]Error:[/bold red] Parts directory not found: {parts_dir}")
        sys.exit(1)

    # Find all .dat files in the parts directory
    return list(parts_dir.glob("*.dat"))

def generate_part_image(
    part_file: Path,
    output_dir: Path,
    force: bool = False,
    verbose: bool = False
) -> Tuple[str, bool, bool]:
    """
    Generate an image for a single part file.

    Returns:
        Tuple of (part_number, success, skipped)
    """
    # Get the part number (filename without extension)
    part_number = part_file.stem
    output_file = output_dir / f"{part_number}.png"

    # Skip if output file already exists and not forcing overwrite
    if output_file.exists() and not force:
        return part_number, True, True  # Success but skipped

    # Use generate-part-image.py script to create the image
    cmd = [
        sys.executable,
        "generate-part-image.py",
        part_number,
        "--output", str(output_file)
    ]

    if verbose:
        cmd.append("--verbose")

    try:
        # Redirect stdout/stderr to devnull if not verbose to avoid cluttering the output
        stdout = None if verbose else subprocess.DEVNULL
        stderr = None if verbose else subprocess.DEVNULL

        result = subprocess.run(
            cmd,
            stdout=stdout,
            stderr=stderr,
            check=True
        )
        return part_number, True, False  # Success and not skipped
    except subprocess.CalledProcessError as e:
        error_msg = f"[bold red]Error generating image for {part_number}[/bold red]"
        if verbose:
            if e.stdout:
                error_msg += f"\n[dim]{e.stdout.decode('utf-8')}[/dim]"
            if e.stderr:
                error_msg += f"\n[dim]{e.stderr.decode('utf-8')}[/dim]"
        print(error_msg)  # Print directly to avoid race conditions with rich console
        return part_number, False, False  # Failed and not skipped

def process_batch(batch: List[Tuple[Path, Path, bool, bool]]) -> List[Tuple[str, bool, bool]]:
    """Process a batch of part files in parallel within a worker process."""
    results = []
    for part_file, output_dir, force, verbose in batch:
        result = generate_part_image(part_file, output_dir, force, verbose)
        results.append(result)
    return results

def main():
    """Main function to generate all part images."""
    args = parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # Get all part files
    console.print(f"Finding part files in {args.ldraw_dir}/parts...")
    part_files = get_part_files(args.ldraw_dir)
    console.print(f"Found [bold green]{len(part_files)}[/bold green] part files")

    if len(part_files) == 0:
        console.print("[yellow]No part files found. Exiting.[/yellow]")
        return

    # Prepare tasks for parallel processing
    tasks = [(part_file, output_dir, args.force, args.verbose) for part_file in part_files]

    # Calculate number of parts to process per job
    num_jobs = min(args.jobs, len(tasks))
    console.print(f"Using [bold blue]{num_jobs}[/bold blue] parallel processes")

    # Initialize counters
    success_count = 0
    error_count = 0
    skip_count = 0
    completed_count = 0

    # Use ProcessPoolExecutor for parallel processing
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task_id = progress.add_task("Generating part images", total=len(part_files))

        with ProcessPoolExecutor(max_workers=num_jobs) as executor:
            # Submit individual jobs
            futures = {executor.submit(generate_part_image, *task): task[0].stem for task in tasks}

            # Process results as they complete
            for future in as_completed(futures):
                part_number, success, skipped = future.result()
                completed_count += 1

                if skipped:
                    skip_count += 1
                elif success:
                    success_count += 1
                else:
                    error_count += 1

                # Update progress bar
                progress.update(task_id, advance=1, description=f"Processed {completed_count}/{len(part_files)}")

    # Print summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"Total parts: {len(part_files)}")
    console.print(f"Successfully generated: [bold green]{success_count}[/bold green]")
    console.print(f"Skipped (already exist): [bold blue]{skip_count}[/bold blue]")
    console.print(f"Errors: [bold red]{error_count}[/bold red]")
    console.print(f"\nImages saved to: [bold]{output_dir.absolute()}[/bold]")

if __name__ == "__main__":
    # This is important for multiprocessing on macOS
    multiprocessing.set_start_method('spawn', force=True)
    main()