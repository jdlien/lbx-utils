#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Barcode model for lbxyml2lbx
"""

from typing import Union, Optional, Any

class BarcodeObject:
    """
    Barcode object model for various barcode types including QR codes.

    For QR codes, the 'size' parameter controls the cell size (module size) and can be specified in several ways:
    1. As a specific point size: "0.8pt", "1.2pt", "1.6pt", "2pt", "2.4pt"
    2. As a numeric index (1-5):
       - 1: Small (0.8pt)
       - 2: Medium Small (1.2pt)
       - 3: Medium (1.6pt)
       - 4: Medium Large (2pt)
       - 5: Large (2.4pt)
    3. As descriptive strings (case insensitive):
       - "small", "sm": Small (0.8pt)
       - "medium small", "medium-small", "mediumsmall", "mdsm", "smmd": Medium Small (1.2pt)
       - "medium", "md": Medium (1.6pt)
       - "medium large", "medium-large", "mediumlarge", "mdlg", "lgmd": Medium Large (2pt)
       - "large", "lg": Large (2.4pt)

    If not specified, the default is Medium Large (2pt).
    """

    # Standard QR code cell sizes
    QR_SIZE_SMALL = "0.8pt"         # Size 1: Small (sm)
    QR_SIZE_MEDIUM_SMALL = "1.2pt"  # Size 2: Medium Small (mdsm, smmd)
    QR_SIZE_MEDIUM = "1.6pt"        # Size 3: Medium (md)
    QR_SIZE_MEDIUM_LARGE = "2pt"    # Size 4: Medium Large (mdlg, lgmd)
    QR_SIZE_LARGE = "2.4pt"         # Size 5: Large (lg)

    # Mapping of size names and aliases to point sizes
    QR_SIZE_MAPPING = {
        # Index values
        1: QR_SIZE_SMALL,
        2: QR_SIZE_MEDIUM_SMALL,
        3: QR_SIZE_MEDIUM,
        4: QR_SIZE_MEDIUM_LARGE,
        5: QR_SIZE_LARGE,

        # String descriptors
        "small": QR_SIZE_SMALL,
        "sm": QR_SIZE_SMALL,

        "medium small": QR_SIZE_MEDIUM_SMALL,
        "medium-small": QR_SIZE_MEDIUM_SMALL,
        "mediumsmall": QR_SIZE_MEDIUM_SMALL,
        "mdsm": QR_SIZE_MEDIUM_SMALL,
        "smmd": QR_SIZE_MEDIUM_SMALL,

        "medium": QR_SIZE_MEDIUM,
        "md": QR_SIZE_MEDIUM,

        "medium large": QR_SIZE_MEDIUM_LARGE,
        "medium-large": QR_SIZE_MEDIUM_LARGE,
        "mediumlarge": QR_SIZE_MEDIUM_LARGE,
        "mdlg": QR_SIZE_MEDIUM_LARGE,
        "lgmd": QR_SIZE_MEDIUM_LARGE,

        "large": QR_SIZE_LARGE,
        "lg": QR_SIZE_LARGE,
    }

    def __init__(self, type: str = "qr", data: str = "", x: Union[int, float, str] = 0,
                 y: Union[int, float, str] = 0, size: Union[int, float, str] = 4,
                 correction: str = "M", errorCorrection: Optional[str] = None):
        """Initialize a barcode object.

        Parameters:
            type: Barcode type (qr, code39, code128, etc.)
            data: Data to encode in the barcode
            x: X-coordinate position
            y: Y-coordinate position
            size: For QR codes, specifies the cell size (see class docstring for accepted values).
                  For other barcodes, this is the overall size.
            correction: QR error correction level (L, M, Q, H)
            errorCorrection: (Deprecated) Use correction instead
        """
        self.type = type
        self.data = data
        self.x = x
        self.y = y

        # Store the original size parameter
        self._raw_size = size

        # For QR codes, size is interpreted as cell size
        # For other barcodes, it's the overall size
        self.size = size

        # For backward compatibility, errorCorrection takes precedence if provided
        self.correction = errorCorrection if errorCorrection is not None else correction

        # Set reasonable default width/height for all barcodes
        # For QR codes, these will be adjusted based on cell size and content
        self.width = 30
        self.height = 30

        # Optional properties with defaults
        self.model: str = "2"  # QR code model (1 or 2)
        self.margin: Union[bool, int, float] = True  # Include quiet zone/margin
        self.version: str = "auto"  # QR code version (auto, 1-40)
        self.humanReadable: bool = False  # Show human-readable text (for linear barcodes)
        self.protocol: str = "qr"  # Alias for type, used in XML output

        # Common barcode style attributes (from BarcodeStyleAttributes in XSD)
        self.lengths: str = "0"  # Required data length
        self.zeroFill: bool = False
        self.barWidth: str = "0.8pt"
        self.barRatio: str = "1:3"
        self.humanReadableAlignment: str = "LEFT"
        self.checkDigit: bool = False
        self.autoLengths: bool = True
        self.sameLengthBar: bool = False
        self.bearerBar: bool = False
        self.removeParentheses: bool = False
        self.startstopCode: Optional[str] = None  # For CODABAR

        # RSS (GS1 DataBar) specific attributes
        self.rssModel: str = "RSS14Standard"
        self.column: str = "4"
        self.autoAdd01: bool = True

        # PDF417 specific attributes
        self.pdf417Model: str = "standard"
        self.aspect: str = "3"
        self.row: str = "auto"
        self.eccLevel: str = "auto"
        self.joint: str = "1"

        # DataMatrix specific attributes
        self.dataMatrixModel: str = "square"
        self.cellSize: str = "1.6pt"
        self.macro: str = "none"
        self.fnc01: bool = False

        # MaxiCode specific attributes
        self.maxiCodeModel: str = "4"

    @property
    def cell_size(self) -> str:
        """
        Get the QR code cell size in points, converting from various formats.

        For internal use by the generator to get the proper XML value.

        Returns:
            String in format like "2pt" for the cell size.
        """
        # If the barcode is not a QR code, return empty string
        if self.type.lower() != "qr":
            return ""

        # Handle different size formats
        size_value = self._raw_size

        # Handle point size strings
        if isinstance(size_value, str) and size_value.endswith("pt"):
            return size_value

        # Handle string descriptors (case-insensitive)
        if isinstance(size_value, str):
            lower_size = size_value.lower()
            if lower_size in self.QR_SIZE_MAPPING:
                return self.QR_SIZE_MAPPING[lower_size]

        # Handle numeric indices (1-5)
        if isinstance(size_value, (int, float)):
            int_size = int(size_value)
            if int_size in self.QR_SIZE_MAPPING:
                return self.QR_SIZE_MAPPING[int_size]
            # Small numbers (1-5) are treated as indices
            if 1 <= int_size <= 5:
                return self.QR_SIZE_MAPPING[int_size]

        # Default to Medium Large if no valid format is found
        return self.QR_SIZE_MEDIUM_LARGE