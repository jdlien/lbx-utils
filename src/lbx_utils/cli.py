#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Command-line interface for lbxyml2lbx
"""

import os
import zipfile
import traceback
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
import colorama

from .parser import YamlParser
from .generator import LbxGenerator
from .text_dimensions import TextDimensionCalculator, CalculationMethod

# Initialize colorama for cross-platform color support
colorama.init()

# Create console for rich output
console = Console()

# Create the typer app
app = typer.Typer(help="Convert LBX YAML files to Brother P-Touch LBX format")

@app.command()
def convert(
    input_file: Optional[str] = typer.Argument(None, help="Input LBX YAML file path"),
    output_file: Optional[str] = typer.Argument(None, help="Output LBX file path"),
    input_flag: Optional[str] = typer.Option(None, "--input", "-i", help="Input LBX YAML file path (alternative to positional argument)"),
    output_flag: Optional[str] = typer.Option(None, "--output", "-o", help="Output LBX file path (alternative to positional argument)"),
    unzip_dir: Optional[str] = typer.Option(None, "--unzip", "-u", help="Directory to unzip the output LBX file for inspection"),
    text_method: Optional[str] = typer.Option(None, "--text-method", "-t", help="Text dimension calculation method (auto, core_text, freetype, pil, harfbuzz, pango, approximation)"),
    adjust_text: bool = typer.Option(True, "--adjust-text/--no-adjust-text", help="Apply technique-specific text dimension adjustments"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output including text dimension calculations"),
    show_text_methods: bool = typer.Option(False, "--show-text-methods", help="Show available text dimension calculation methods with recommendations")
) -> None:
    """
    Convert an LBX YAML file to a Brother P-Touch LBX file.

    You can specify input/output files as positional arguments:
      python -m src.lbx_utils.lbxyml2lbx input.lbx.yml output.lbx

    Or use traditional flags:
      python -m src.lbx_utils.lbxyml2lbx --input input.lbx.yml --output output.lbx
    """
    # Show available text methods if requested
    if show_text_methods:
        console.print(Panel.fit(
            "[bold green]Available Text Dimension Calculation Methods[/bold green]\n\n"
            "[blue]core_text[/blue]: Best method on macOS - very accurate (requires PyObjC)\n"
            "[blue]freetype[/blue]: Good method on all platforms - reliable and accurate\n"
            "[blue]harfbuzz[/blue]: Decent method with good international text support\n"
            "[blue]pango[/blue]: Provides good typography support\n"
            "[blue]pil[/blue]: Simple method using Pillow (less accurate)\n"
            "[blue]approximation[/blue]: Fallback method with rough estimates\n"
            "[blue]auto[/blue]: Automatically selects best available method (default)\n\n"
            "[bold yellow]Recommendation:[/bold yellow]\n"
            f"On macOS: use [green]core_text[/green]\n"
            f"On other platforms: use [green]freetype[/green]",
            title="Text Dimension Methods",
            border_style="blue"
        ))
        raise typer.Exit(code=0)

    # Handle both positional and flag-based arguments
    input_path = input_flag if input_flag is not None else input_file
    output_path = output_flag if output_flag is not None else output_file

    # Validate we have both input and output
    if input_path is None:
        console.print("[bold red]Error: Input file not specified[/bold red]")
        console.print("Please provide an input file as a positional argument or with --input")
        raise typer.Exit(code=1)

    if output_path is None:
        console.print("[bold red]Error: Output file not specified[/bold red]")
        console.print("Please provide an output file as a positional argument or with --output")
        raise typer.Exit(code=1)

    try:
        console.print(f"[blue]Converting {input_path} to {output_path}...[/blue]")

        # Handle text calculation method if specified
        calculation_method = None
        if text_method:
            # Validate the method
            valid_methods = ["auto", "core_text", "freetype", "pil", "harfbuzz", "pango", "approximation"]
            if text_method.lower() not in valid_methods:
                console.print(f"[yellow]Warning: Invalid text calculation method '{text_method}'. Using auto selection.[/yellow]")
            else:
                # Convert string to CalculationMethod enum
                try:
                    calculation_method = CalculationMethod(text_method.lower())
                    console.print(f"[blue]Using {calculation_method.value} for text dimension calculations[/blue]")
                except (ValueError, AttributeError):
                    console.print(f"[yellow]Warning: Could not set calculation method to '{text_method}'. Using auto selection.[/yellow]")

        # Override calculator debug setting if verbose is enabled
        debug_mode = verbose

        # Parse the YAML file with custom text calculation settings
        parser = YamlParser(input_path)

        # Override text calculator settings if specified
        if calculation_method or not adjust_text or debug_mode:
            parser.text_calculator = TextDimensionCalculator(
                debug=debug_mode,
                allow_fallbacks=True,
                apply_technique_adjustments=adjust_text,
                default_method=calculation_method
            )

            if verbose:
                method_name = calculation_method.value if calculation_method else "auto"
                console.print(f"[blue]Text dimension calculator: method={method_name}, adjustments={adjust_text}[/blue]")

        config = parser.parse()

        # Print summary of what was parsed
        object_counts = {}
        for obj in config.objects:
            obj_type = obj.__class__.__name__
            if obj_type not in object_counts:
                object_counts[obj_type] = 0
            object_counts[obj_type] += 1

        console.print(f"[blue]Parsed YAML file with the following elements:[/blue]")
        console.print(f"  Label size: {config.size}")
        console.print(f"  Width: {config.width}")
        console.print(f"  Orientation: {config.orientation}")

        for obj_type, count in object_counts.items():
            console.print(f"  {obj_type}s: {count}")

        # Generate the LBX file
        generator = LbxGenerator(config)
        generator.generate_lbx(output_path)

        console.print(f"[green]Successfully converted {input_path} to {output_path}[/green]")

        # Optionally unzip the output for inspection
        if unzip_dir:
            # Create the unzip directory
            os.makedirs(unzip_dir, exist_ok=True)

            # Unzip the file
            with zipfile.ZipFile(output_path, 'r') as zip_ref:
                zip_ref.extractall(unzip_dir)

            console.print(f"[green]Unzipped LBX file to {unzip_dir}[/green]")
            console.print(f"  Files extracted:")
            for file in os.listdir(unzip_dir):
                file_path = os.path.join(unzip_dir, file)
                file_size = os.path.getsize(file_path)
                console.print(f"    {file} ({file_size} bytes)")

    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()