#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Layout Engine for lbxyml2lbx

This module provides a flexbox-inspired layout engine for positioning
objects within group containers.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from .models import GroupObject, TextObject, ImageObject


class FlexLayoutEngine:
    """
    Flexbox-inspired layout engine for positioning objects within groups.

    Implements a simplified version of CSS flexbox layout algorithm to
    automatically position and align child elements within a parent group.
    """

    def __init__(self, debug: bool = False):
        """Initialize the layout engine."""
        self.debug = debug

    def apply_layout(self, group: GroupObject) -> None:
        """
        Apply layout to all objects within the group.

        This calculates positions for all child objects based on the group's
        layout properties (direction, justify, align, gap, etc.).
        """
        if not group.objects:
            return

        # Get group dimensions from attributes
        # Remove 'pt' suffix if present
        width = float(group.width.replace('pt', '')) if isinstance(group.width, str) else float(group.width)
        height = float(group.height.replace('pt', '')) if isinstance(group.height, str) else float(group.height)

        # Get padding
        padding = group.get_padding_as_dict()

        # Calculate available space for content
        content_width = width - padding['left'] - padding['right']
        content_height = height - padding['top'] - padding['bottom']

        # Base positions, adjusted for padding
        base_x = float(group.x.replace('pt', '')) if isinstance(group.x, str) else float(group.x)
        base_y = float(group.y.replace('pt', '')) if isinstance(group.y, str) else float(group.y)

        # Adjust base positions by padding
        content_x = base_x + padding['left']
        content_y = base_y + padding['top']

        # For row layout
        if not group.is_vertical:
            self._apply_row_layout(
                group,
                content_x,
                content_y,
                content_width,
                content_height
            )
        # For column layout
        else:
            self._apply_column_layout(
                group,
                content_x,
                content_y,
                content_width,
                content_height
            )

    def _apply_row_layout(self, group: GroupObject, x: float, y: float, width: float, height: float) -> None:
        """Apply row layout to position objects horizontally."""
        # Get item dimensions
        items = self._get_item_dimensions(group.objects)

        # Calculate total content width and determine available space
        total_item_width = sum(item['width'] for item in items)
        total_gaps = (len(items) - 1) * group.gap

        # Available space for flexible items
        available_space = width - total_item_width - total_gaps

        # Determine starting position based on justify property
        current_x = x
        if group.justify == 'end':
            current_x = x + available_space
        elif group.justify == 'center':
            current_x = x + available_space / 2
        elif group.justify in ('between', 'around', 'evenly'):
            # These will be handled differently below
            pass

        # Calculate spacing between items based on justification
        spacing = 0
        if len(items) > 1:
            if group.justify == 'between':
                spacing = available_space / (len(items) - 1)
            elif group.justify == 'around':
                spacing = available_space / len(items)
                current_x += spacing / 2
            elif group.justify == 'evenly':
                spacing = available_space / (len(items) + 1)
                current_x += spacing

        # Position each item
        for i, item in enumerate(items):
            # Adjust for reverse direction
            if group.is_reversed:
                item_idx = len(items) - 1 - i
            else:
                item_idx = i

            item_obj = group.objects[item_idx]
            item_width = item['width']
            item_height = item['height']

            # Calculate vertical position based on align property
            item_y = y
            if group.align == 'center':
                item_y = y + (height - item_height) / 2
            elif group.align == 'end':
                item_y = y + height - item_height

            # Create position strings with 'pt' suffix
            item_obj.x = f"{current_x:.1f}pt"
            item_obj.y = f"{item_y:.1f}pt"

            # If this is a nested group, apply layout recursively
            if isinstance(item_obj, GroupObject):
                self.apply_layout(item_obj)

            # Move to next position
            current_x += item_width + group.gap

            # Add additional spacing for justify modes that need it
            if group.justify in ('around', 'evenly'):
                current_x += spacing

    def _apply_column_layout(self, group: GroupObject, x: float, y: float, width: float, height: float) -> None:
        """Apply column layout to position objects vertically."""
        # Get item dimensions
        items = self._get_item_dimensions(group.objects)

        # Calculate total content height and determine available space
        total_item_height = sum(item['height'] for item in items)
        total_gaps = (len(items) - 1) * group.gap

        # Available space for flexible items
        available_space = height - total_item_height - total_gaps

        # Determine starting position based on justify property
        current_y = y
        if group.justify == 'end':
            current_y = y + available_space
        elif group.justify == 'center':
            current_y = y + available_space / 2
        elif group.justify in ('between', 'around', 'evenly'):
            # These will be handled differently below
            pass

        # Calculate spacing between items based on justification
        spacing = 0
        if len(items) > 1:
            if group.justify == 'between':
                spacing = available_space / (len(items) - 1)
            elif group.justify == 'around':
                spacing = available_space / len(items)
                current_y += spacing / 2
            elif group.justify == 'evenly':
                spacing = available_space / (len(items) + 1)
                current_y += spacing

        # Position each item
        for i, item in enumerate(items):
            # Adjust for reverse direction
            if group.is_reversed:
                item_idx = len(items) - 1 - i
            else:
                item_idx = i

            item_obj = group.objects[item_idx]
            item_width = item['width']
            item_height = item['height']

            # Calculate horizontal position based on align property
            item_x = x
            if group.align == 'center':
                item_x = x + (width - item_width) / 2
            elif group.align == 'end':
                item_x = x + width - item_width
            elif group.align == 'stretch' and isinstance(item_obj, (TextObject, ImageObject)):
                # Only stretch width if it's not a nested group
                item_width = width
                item_obj.width = f"{width:.1f}pt"

            # Create position strings with 'pt' suffix
            item_obj.x = f"{item_x:.1f}pt"
            item_obj.y = f"{current_y:.1f}pt"

            # If this is a nested group, apply layout recursively
            if isinstance(item_obj, GroupObject):
                self.apply_layout(item_obj)

            # Move to next position
            current_y += item_height + group.gap

            # Add additional spacing for justify modes that need it
            if group.justify in ('around', 'evenly'):
                current_y += spacing

    def _get_item_dimensions(self, objects: List[Any]) -> List[Dict[str, float]]:
        """
        Get dimensions of all items in the group.

        Returns a list of dictionaries with width and height for each object.
        """
        items = []

        for obj in objects:
            # Convert dimensions to float, removing 'pt' suffix if present
            width = float(obj.width.replace('pt', '')) if isinstance(obj.width, str) else float(obj.width)
            height = float(obj.height.replace('pt', '')) if isinstance(obj.height, str) else float(obj.height)

            items.append({
                'width': width,
                'height': height,
                'object': obj
            })

        return items