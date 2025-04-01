#!/usr/bin/env python3
"""
LBX Utils - Command line interface for working with Brother LBX label files

This module provides a command-line interface for the lbx-utils package.
"""

import sys
import typer
from typing import Optional

from lbx_utils.core.lbx_text_edit import main as lbx_text_edit_main
from lbx_utils.core.lbx_create import main as lbx_create_main
from lbx_utils.core.change_lbx import main as change_lbx_main
from lbx_utils.core.generate_part_image import app as generate_part_image_app

app = typer.Typer(help="LBX Utils - Tools for working with Brother LBX labels")

@app.command("text-edit")
def text_edit():
    """Edit text in LBX label files."""
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    lbx_text_edit_main()

@app.command("create")
def create():
    """Create new LBX label files."""
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    lbx_create_main()

@app.command("change")
def change():
    """Modify existing LBX label files."""
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    change_lbx_main()

@app.command("generate-part-image")
def generate_part_image():
    """Generate images of LEGO parts from LDraw data."""
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    generate_part_image_app()

if __name__ == "__main__":
    app()