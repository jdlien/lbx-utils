#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Package containing text dimension calculation techniques.

This package provides various techniques for calculating text dimensions
using different libraries and approaches, with varying levels of accuracy.

The techniques included are:
- FreeType: High-quality using the FreeType library
- PIL: Using Pillow's ImageFont
- HarfBuzz: Advanced layout using fontTools with HarfBuzz
- Approximation: Fallback option when other methods are not available
- Pango: Advanced layout using Pango
- Core Text: High-quality using macOS Core Text (macOS only)

Each technique follows the same interface defined by BaseCalculationTechnique.
"""

# Import the base class
from .base import BaseCalculationTechnique
# Import FontMetrics from the freetype technique
from .freetype_technique import FreetypeTechnique, FontMetrics
from .pil_technique import PILTechnique
from .harfbuzz_technique import HarfbuzzTechnique
from .approximation_technique import ApproximationTechnique
from .pango_technique import PangoTechnique

# Import CoreTextTechnique conditionally based on platform
import platform
if platform.system() == "Darwin":
    try:
        from .core_text_technique import CoreTextTechnique
    except ImportError:
        # PyObjC not available, so don't expose the Core Text technique
        pass

# For convenience, also export at the package level
__all__ = [
    'BaseCalculationTechnique',
    'FontMetrics',
    'FreetypeTechnique',
    'PILTechnique',
    'HarfbuzzTechnique',
    'ApproximationTechnique',
    'PangoTechnique'
]

# Add CoreTextTechnique to __all__ if on macOS
if platform.system() == "Darwin":
    try:
        import Cocoa
        __all__.append('CoreTextTechnique')
    except ImportError:
        pass