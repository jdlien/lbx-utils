#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Various techniques for calculating text dimensions.

Available techniques:
- FreeType: Basic text measurement using FreeType library
- PIL: Using PIL.ImageFont for estimation
- HarfBuzz: Text shaping with HarfBuzz for accuracy
- Approximation: Simple approximation based on character counts
- Pango: Advanced layout using Pango
- Core Text: High-quality using macOS Core Text (macOS only)
- Skia: High-quality using Skia

Each technique follows the same interface defined by BaseCalculationTechnique.
"""

# Import the base class
from .base import BaseCalculationTechnique
# Import techniques
from .freetype_technique import FreetypeTechnique, FontMetrics
from .pil_technique import PILTechnique
from .harfbuzz_technique import HarfbuzzTechnique
from .approximation_technique import ApproximationTechnique
from .pango_technique import PangoTechnique
from .skia_technique import SkiaTechnique

# Import CoreTextTechnique conditionally based on platform
import platform
if platform.system() == "Darwin":
    try:
        from .core_text_technique import CoreTextTechnique
    except ImportError:
        # PyObjC not available, so don't expose the Core Text technique
        pass

__all__ = [
    'BaseCalculationTechnique',
    'FontMetrics',
    'FreetypeTechnique',
    'PILTechnique',
    'HarfbuzzTechnique',
    'ApproximationTechnique',
    'PangoTechnique',
    'SkiaTechnique'
]

# Add CoreTextTechnique conditionally
if platform.system() == "Darwin":
    try:
        __all__.append('CoreTextTechnique')
    except NameError:
        pass