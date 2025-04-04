#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Constants for lbxyml2lbx
"""

import xml.etree.ElementTree as ET

# XML namespaces used in LBX files
NAMESPACES = {
    'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
    'style': 'http://schemas.brother.info/ptouch/2007/lbx/style',
    'text': 'http://schemas.brother.info/ptouch/2007/lbx/text',
    'draw': 'http://schemas.brother.info/ptouch/2007/lbx/draw',
    'image': 'http://schemas.brother.info/ptouch/2007/lbx/image',
    'barcode': 'http://schemas.brother.info/ptouch/2007/lbx/barcode',
    'database': 'http://schemas.brother.info/ptouch/2007/lbx/database',
    'table': 'http://schemas.brother.info/ptouch/2007/lbx/table',
    'cable': 'http://schemas.brother.info/ptouch/2007/lbx/cable',
    'meta': 'http://schemas.brother.info/ptouch/2007/lbx/meta',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/'
}

# Register all namespaces for proper XML output
for prefix, uri in NAMESPACES.items():
    ET.register_namespace(prefix, uri)

# Label size configurations based on tape width
LABEL_SIZES = {
    3.5: {
        'width': '9.6pt',
        'marginLeft': '0pt',
        'marginRight': '0pt',
        'format': '263',
        'background_y': '0pt',
        'background_height': '9.6pt',
        'text_object_y': '3.0pt',
        'image_object_y': '0pt'
    },
    6: {
        'width': '16.8pt',
        'marginLeft': '2pt',
        'marginRight': '2pt',
        'format': '257',
        'background_y': '2pt',
        'background_height': '12.8pt',
        'text_object_y': '5.0pt',
        'image_object_y': '2pt'
    },
    9: {
        'width': '25.6pt',
        'marginLeft': '2.8pt',
        'marginRight': '2.8pt',
        'format': '258',
        'background_y': '2.8pt',
        'background_height': '20pt',
        'text_object_y': '7.1pt',
        'image_object_y': '2.8pt'
    },
    12: {
        'width': '33.6pt',
        'marginLeft': '2.8pt',
        'marginRight': '2.8pt',
        'format': '259',
        'background_y': '2.8pt',
        'background_height': '28pt',
        'text_object_y': '7.1pt',
        'image_object_y': '2.8pt'
    },
    18: {
        'width': '51.2pt',
        'marginLeft': '3.2pt',
        'marginRight': '3.2pt',
        'format': '260',
        'background_y': '3.2pt',
        'background_height': '44.8pt',
        'text_object_y': '7.5pt',
        'image_object_y': '3.2pt'
    },
    24: {
        'width': '68pt',
        'marginLeft': '8.4pt',
        'marginRight': '8.4pt',
        'format': '261',
        'background_y': '8.4pt',
        'background_height': '51.2pt',
        'text_object_y': '12.7pt',
        'image_object_y': '8.4pt'
    }
}

# Default values
DEFAULT_PRINTER_ID = "30256"  # Brother PT-P710BT
DEFAULT_PRINTER_NAME = "Brother PT-P710BT"