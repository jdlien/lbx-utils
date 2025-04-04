#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base class for text dimension calculation techniques.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict, Any


class BaseCalculationTechnique(ABC):
    """Abstract base class for text dimension calculation techniques."""

    def __init__(self, debug: bool = False, font_dir: Optional[str] = None):
        """
        Initialize the calculation technique.

        Args:
            debug: Enable debug logging
            font_dir: Optional directory to look for fonts
        """
        self.debug = debug
        self.font_dir = font_dir
        self._font_cache: Dict[str, str] = {}

    @abstractmethod
    def calculate_dimensions(
        self,
        text: str,
        font_name: str,
        size: float,
        weight: str = "normal",
        italic: bool = False
    ) -> Tuple[float, float]:
        """
        Calculate the dimensions of a text string.

        Args:
            text: The text string to measure
            font_name: Name of the font
            size: Font size in points
            weight: Font weight (normal, bold)
            italic: Whether the text is italic

        Returns:
            Tuple of (width, height) in points
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the name of this calculation technique."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this calculation technique is available on the system."""
        pass