#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Layout Engine for lbxyml2lbx

This module provides a flexbox-inspired layout engine for positioning
objects within group containers.
"""

from typing import List, Dict, Any, Optional, Tuple, Union, cast
from .models import GroupObject, ContainerObject, TextObject, ImageObject
from .utils.conversion import convert_to_pt
from rich import console


class FlexLayoutEngine:
    """
    Flexbox-inspired layout engine for positioning objects within groups.

    Implements a simplified version of CSS flexbox layout algorithm to
    automatically position and align child elements within a parent group.
    """

    def __init__(self, debug: bool = False):
        """Initialize the layout engine."""
        self.debug = debug

    def _resolve_padding(self, padding: Union[float, int, str, Dict[str, float], None]) -> Dict[str, float]:
        """
        Convert various padding formats to a standardized dictionary with top, right, bottom, left values.

        Args:
            padding: Can be a number, string with units, or dictionary with directional values.

        Returns:
            Dictionary with 'top', 'right', 'bottom', 'left' keys, all as float values in points.
        """
        # Default padding (all sides zero)
        padding_dict = {'top': 0.0, 'right': 0.0, 'bottom': 0.0, 'left': 0.0}

        if padding is None:
            return padding_dict

        # If padding is already a dictionary
        if isinstance(padding, dict):
            # Update with provided values, keeping defaults for missing keys
            for key in ['top', 'right', 'bottom', 'left']:
                if key in padding:
                    value = padding[key]
                    if isinstance(value, str):
                        if value.endswith('pt'):
                            padding_dict[key] = float(value.replace('pt', ''))
                        elif value.endswith('mm'):
                            padding_dict[key] = float(value.replace('mm', '')) * 2.83464567  # mm to pt conversion
                        else:
                            try:
                                padding_dict[key] = float(value)
                            except ValueError:
                                # Keep default if conversion fails
                                pass
                    else:
                        try:
                            padding_dict[key] = float(value)
                        except (ValueError, TypeError):
                            # Keep default if conversion fails
                            pass
            return padding_dict

        # If padding is a string (with units) or a number
        padding_value = 0.0
        if isinstance(padding, str):
            if padding.endswith('pt'):
                padding_value = float(padding.replace('pt', ''))
            elif padding.endswith('mm'):
                padding_value = float(padding.replace('mm', '')) * 2.83464567  # mm to pt conversion
            else:
                try:
                    padding_value = float(padding)
                except ValueError:
                    padding_value = 0.0
        else:
            # Numeric padding
            try:
                padding_value = float(padding)
            except (ValueError, TypeError):
                padding_value = 0.0

        # Apply the same value to all sides
        return {
            'top': padding_value,
            'right': padding_value,
            'bottom': padding_value,
            'left': padding_value
        }

    def apply_layout(self, group: GroupObject):
        """Apply flex layout to the group's child objects."""
        # Check if group has dimensions
        is_auto_width = group.width == "auto" or not group.width
        is_auto_height = group.height == "auto" or not group.height

        # Check if this is a positioned group
        is_positioned_group = getattr(group, '_positioned', False)

        # Store original coordinates for positioned groups before any calculations
        original_x = group.x
        original_y = group.y

        # Rich console is imported at the top
        if self.debug:
            print(f"Layout engine processing group with position: x={group.x}, y={group.y}, positioned={is_positioned_group}")

        # Get padding as a standardized dictionary
        padding_dict = self._resolve_padding(getattr(group, "padding", 0))

        # Get explicit dimensions if available
        explicit_width = 0
        if not is_auto_width:
            explicit_width = float(convert_to_pt(group.width).rstrip("pt"))

        explicit_height = 0
        if not is_auto_height:
            explicit_height = float(convert_to_pt(group.height).rstrip("pt"))

        # Calculate available content area (within padding)
        content_width = explicit_width - padding_dict['left'] - padding_dict['right'] if not is_auto_width else 0
        content_height = explicit_height - padding_dict['top'] - padding_dict['bottom'] if not is_auto_height else 0

        # Get the list of objects to lay out
        objects = group.objects

        if not objects:
            if self.debug:
                print("Warning: Group has no objects to lay out")
            return

        # Determine flow direction
        direction = group.direction.lower()
        is_row = direction == "row"

        # Store original object positions if we need to restore them
        original_positions = []
        for obj in objects:
            original_positions.append((obj.x, obj.y))

        # Check if we need to wrap items
        should_wrap = group.wrap if hasattr(group, "wrap") and group.wrap is not None else False

        # Initialize container dimensions for auto sizing
        container_width = 0
        container_height = 0

        # Apply layout based on direction
        if is_row:
            self._apply_row_layout(
                group, objects, padding_dict,
                should_wrap=should_wrap,
                container_width=content_width,
                container_height=content_height
            )
        else:  # column
            self._apply_column_layout(
                group, objects, padding_dict,
                should_wrap=should_wrap,
                container_width=content_width,
                container_height=content_height
            )

        # Calculate the final bounding box based on positioned children
        min_x = min(float(obj.x.replace('pt', '')) if isinstance(obj.x, str) else float(obj.x) for obj in objects)
        min_y = min(float(obj.y.replace('pt', '')) if isinstance(obj.y, str) else float(obj.y) for obj in objects)

        # Calculate max x and y (position + dimension)
        max_x = max(
            (float(obj.x.replace('pt', '')) if isinstance(obj.x, str) else float(obj.x)) +
            (float(obj.width.replace('pt', '')) if isinstance(obj.width, str) and obj.width != 'auto' else 100)
            for obj in objects
        )
        max_y = max(
            (float(obj.y.replace('pt', '')) if isinstance(obj.y, str) else float(obj.y)) +
            (float(obj.height.replace('pt', '')) if isinstance(obj.height, str) and obj.height != 'auto' else 20)
            for obj in objects
        )

        # Calculate container dimensions based on children - add padding to all sides
        container_width = max_x - min_x + padding_dict['left'] + padding_dict['right']
        container_height = max_y - min_y + padding_dict['top'] + padding_dict['bottom']

        # Update group width/height if auto
        if is_auto_width:
            group.width = f"{container_width}pt"
        if is_auto_height:
            group.height = f"{container_height}pt"

        # If this is a positioned group, restore the original x,y coordinates
        if is_positioned_group:
            group.x = original_x
            group.y = original_y
            if self.debug:
                print(f"Preserving original position for positioned group: x={original_x}, y={original_y}")

        # Recursively apply layout to nested groups
        for obj in group.objects:
            if isinstance(obj, GroupObject):
                self.apply_layout(obj)
            elif isinstance(obj, ContainerObject):
                self.apply_layout_to_container(obj)

        # Return the final dimensions for use in parent layouts
        return container_width, container_height

    def _apply_row_layout(self, group: GroupObject, objects: List[Any], padding_dict: Dict[str, float],
                          should_wrap: bool, container_width: float, container_height: float) -> None:
        """Apply row layout to position objects horizontally."""
        # Get item dimensions
        items = self._get_item_dimensions(objects)

        # Calculate total content width and determine available space
        total_item_width = sum(item['width'] for item in items)
        total_gaps = (len(items) - 1) * group.gap

        # Available space for flexible items
        available_space = container_width - total_item_width - total_gaps

        # Determine starting position based on justify property
        current_x = padding_dict['left']  # Start after left padding
        if group.justify == 'end':
            current_x += available_space
        elif group.justify == 'center':
            current_x += available_space / 2
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

        # Find maximum height for cross-axis alignment
        max_item_height = max(item['height'] for item in items) if items else 0

        # Position each item
        for i, item in enumerate(items):
            # Adjust for reverse direction
            if group.is_reversed:
                item_idx = len(items) - 1 - i
            else:
                item_idx = i

            item_obj = objects[item_idx]
            item_width = item['width']
            item_height = item['height']

            # Check if this is a group or container with explicitly set positions
            is_positioned_group = False
            if isinstance(item_obj, (GroupObject, ContainerObject)):
                is_positioned_group = getattr(item_obj, '_positioned', False)

            # If it's not a group with explicitly set positions, apply layout positioning
            if not is_positioned_group:
                # Calculate vertical position based on align property
                item_y = padding_dict['top']  # Start after top padding

                if group.align == 'center':
                    # Center the item vertically in the available space
                    item_y += (container_height - item_height) / 2
                elif group.align == 'end':
                    # Align to bottom of container
                    item_y += container_height - item_height
                elif group.align == 'stretch' and isinstance(item_obj, (TextObject, ImageObject)):
                    # Stretch item to fill container height
                    item_height = container_height
                    item_obj.height = f"{item_height}pt"

                # Create position strings with 'pt' suffix
                item_obj.x = f"{current_x:.1f}pt"
                item_obj.y = f"{item_y:.1f}pt"

                # Move to next position
                current_x += item_width + group.gap

                # Add additional spacing for justify modes that need it
                if group.justify in ('around', 'evenly'):
                    current_x += spacing

            # If this is a nested group, apply layout recursively
            if isinstance(item_obj, GroupObject):
                self.apply_layout(item_obj)
            elif isinstance(item_obj, ContainerObject):
                # Apply layout to container too
                self.apply_layout_to_container(item_obj)

    def _apply_column_layout(self, group: GroupObject, objects: List[Any], padding_dict: Dict[str, float],
                            should_wrap: bool, container_width: float, container_height: float) -> None:
        """Apply column layout to position objects vertically."""
        # Get item dimensions
        items = self._get_item_dimensions(objects)

        # Calculate total content height and determine available space
        total_item_height = sum(item['height'] for item in items)

        # Calculate gap space
        gap = group.gap if hasattr(group, "gap") else 0
        # Convert gap to a numeric value if it's a string
        if isinstance(gap, str):
            if gap.endswith('pt'):
                gap = float(gap.replace('pt', ''))
            elif gap.endswith('mm'):
                gap = float(gap.replace('mm', '')) * 2.83464567  # mm to pt conversion
            else:
                try:
                    gap = float(gap)
                except ValueError:
                    gap = 0

        total_gaps = gap * (len(items) - 1) if len(items) > 1 else 0

        # Available space for flexible items
        available_space = container_height - total_item_height - total_gaps

        # Determine starting position based on justify property
        current_y = padding_dict['top']  # Start after top padding
        if group.justify == 'end':
            current_y += available_space
        elif group.justify == 'center':
            current_y += available_space / 2
        elif group.justify in ('between', 'around', 'evenly'):
            # These will be handled differently below
            pass

        # Find maximum width for cross-axis alignment
        max_item_width = max(item['width'] for item in items) if items else 0

        # Position each item
        for i, item in enumerate(items):
            # Get actual object
            item_obj = item['object']
            item_width = item['width']
            item_height = item['height']

            # Special spacing calculations for justify options
            if i > 0:
                if group.justify == 'between' and len(items) > 1:
                    # Space evenly between items, no space at edges
                    gap_size = available_space / (len(items) - 1)
                    current_y += gap_size
                elif group.justify == 'around' and len(items) > 1:
                    # Space evenly around items, half space at edges
                    gap_size = available_space / len(items)
                    current_y += gap_size
                elif group.justify == 'evenly' and len(items) >= 1:
                    # Space evenly, equal space at edges and between
                    gap_size = available_space / (len(items) + 1)
                    current_y += gap_size
                else:
                    # Standard gap
                    current_y += gap

            # Skip positioning for explicitly positioned items
            is_positioned_group = hasattr(item_obj, "_positioned") and getattr(item_obj, "_positioned")

            if not is_positioned_group:
                # Calculate horizontal position based on align property
                item_x = padding_dict['left']  # Start after left padding

                if group.align == 'center':
                    # Center the item horizontally in the available space
                    item_x += (container_width - item_width) / 2
                elif group.align == 'end':
                    # Align to right side of container
                    item_x += container_width - item_width
                elif group.align == 'stretch' and isinstance(item_obj, (TextObject, ImageObject)):
                    # Stretch item to fill container width
                    item_width = container_width
                    item_obj.width = f"{item_width}pt"

                # Create position strings with 'pt' suffix
                item_obj.x = f"{item_x}pt"
                item_obj.y = f"{current_y}pt"

            # Move to next position
            current_y += item_height

            # Apply layout to nested groups
            if isinstance(item_obj, GroupObject):
                self.apply_layout(item_obj)
            elif isinstance(item_obj, ContainerObject):
                self.apply_layout_to_container(item_obj)

    def _get_item_dimensions(self, objects: List[Any]) -> List[Dict[str, Any]]:
        """
        Get dimensions of all items in the group.

        Returns a list of dictionaries with width, height, and object reference for each object.
        """
        items = []

        for idx, obj in enumerate(objects):
            # Handle special case of 'auto' dimensions
            if hasattr(obj, 'width') and isinstance(obj.width, str) and obj.width == 'auto':
                width = 100.0  # Default size for 'auto' width
            else:
                # Convert dimensions to float, removing 'pt' suffix if present
                try:
                    width = float(obj.width.replace('pt', '')) if isinstance(obj.width, str) else float(obj.width)
                except (ValueError, TypeError):
                    width = 100.0  # Default if conversion fails

            if hasattr(obj, 'height') and isinstance(obj.height, str) and obj.height == 'auto':
                height = 20.0  # Default size for 'auto' height
            else:
                try:
                    height = float(obj.height.replace('pt', '')) if isinstance(obj.height, str) else float(obj.height)
                except (ValueError, TypeError):
                    height = 20.0  # Default if conversion fails

            items.append({
                'width': width,
                'height': height,
                'object': obj,
                'index': idx
            })

        return items

    def apply_root_layout(self, config):
        """
        Apply root-level layout to objects directly without a group container.

        This functions like apply_layout but works on the LabelConfig's objects
        using the layout properties defined at the root level.
        """
        if not config.has_root_layout or not config.objects:
            return

        # Get label dimensions
        # If width is auto, use a reasonable default width for calculations
        if config.width == 'auto' or not config.width:
            width = 283.4  # ~100mm in points
        else:
            try:
                width_str = config.width
                if isinstance(width_str, str) and width_str.endswith('pt'):
                    width = float(width_str.replace('pt', ''))
                else:
                    # Convert mm to points if needed
                    from .utils.conversion import convert_to_pt
                    width = float(convert_to_pt(width_str).replace('pt', ''))
            except (ValueError, TypeError):
                # Default if conversion fails
                width = 283.4  # ~100mm in points

        # Calculate height based on tape size with some reasonable defaults
        tape_size_mm = config.size_mm
        height = tape_size_mm * 2.83  # Convert mm to pt

        # Handle padding
        padding = {'top': 0, 'right': 0, 'bottom': 0, 'left': 0}
        if hasattr(config, 'padding') and config.padding:
            if isinstance(config.padding, dict):
                padding.update(config.padding)
            else:
                padding = {
                    'top': config.padding,
                    'right': config.padding,
                    'bottom': config.padding,
                    'left': config.padding
                }

        # Calculate available space for content
        content_width = width - padding['left'] - padding['right']
        content_height = height - padding['top'] - padding['bottom']

        # Starting positions, adjusted for padding
        content_x = padding['left']
        content_y = padding['top']

        # For row layout (default)
        if not config.direction.startswith('column'):
            self._apply_root_row_layout(
                config,
                content_x,
                content_y,
                content_width,
                content_height
            )
        # For column layout
        else:
            self._apply_root_column_layout(
                config,
                content_x,
                content_y,
                content_width,
                content_height
            )

    def _apply_root_row_layout(self, config, x, y, width, height):
        """Apply row layout to position objects horizontally at the root level."""
        # Get item dimensions
        items = self._get_item_dimensions(config.objects)

        # Calculate total content width and determine available space
        total_item_width = sum(item['width'] for item in items)
        total_gaps = (len(items) - 1) * config.gap

        # Available space for flexible items
        available_space = width - total_item_width - total_gaps

        # Determine starting position based on justify property
        current_x = x
        if config.justify == 'end':
            current_x = x + available_space
        elif config.justify == 'center':
            current_x = x + available_space / 2
        elif config.justify in ('between', 'around', 'evenly'):
            # These will be handled differently below
            pass

        # Calculate spacing between items based on justification
        spacing = 0
        if len(items) > 1:
            if config.justify == 'between':
                spacing = available_space / (len(items) - 1)
            elif config.justify == 'around':
                spacing = available_space / len(items)
                current_x += spacing / 2
            elif config.justify == 'evenly':
                spacing = available_space / (len(items) + 1)
                current_x += spacing

        # Check if direction is reversed
        is_reversed = config.direction.endswith('-reverse')

        # Position each item
        for i, item in enumerate(items):
            # Adjust for reverse direction
            if is_reversed:
                item_idx = len(items) - 1 - i
            else:
                item_idx = i

            item_obj = config.objects[item_idx]
            item_width = item['width']
            item_height = item['height']

            # Get original x position to use as offset
            original_x = float(item_obj.x.replace('pt', '')) if isinstance(item_obj.x, str) else float(item_obj.x)

            # Calculate vertical position based on align property
            item_y = y
            if config.align == 'center':
                # Treat the original y value of the object as an offset from the centered position
                original_y = float(item_obj.y.replace('pt', '')) if isinstance(item_obj.y, str) else float(item_obj.y)
                # Calculate centered position
                centered_y = y + (height - item_height) / 2
                # Apply the original y as an offset
                item_y = centered_y + original_y
            elif config.align == 'end':
                item_y = y + height - item_height
                # Add original y as offset
                original_y = float(item_obj.y.replace('pt', '')) if isinstance(item_obj.y, str) else float(item_obj.y)
                item_y += original_y
            else:  # align: start or default
                # Add original y as offset
                original_y = float(item_obj.y.replace('pt', '')) if isinstance(item_obj.y, str) else float(item_obj.y)
                item_y += original_y

            # Create position strings with 'pt' suffix - apply original x as offset to layout-calculated position
            final_x = current_x + original_x
            item_obj.x = f"{final_x:.1f}pt"
            item_obj.y = f"{item_y:.1f}pt"

            # If this is a nested group, apply layout recursively
            if isinstance(item_obj, GroupObject):
                self.apply_layout(item_obj)

            # Move to next position - use the final_x (which includes the offset)
            # instead of current_x to properly account for offsets in subsequent items
            current_x = final_x + item_width + config.gap

            # Add additional spacing for justify modes that need it
            if config.justify in ('around', 'evenly'):
                current_x += spacing

    def _apply_root_column_layout(self, config, x, y, width, height):
        """Apply column layout to position objects vertically at the root level."""
        # Get item dimensions
        items = self._get_item_dimensions(config.objects)

        # Calculate total content height and determine available space
        total_item_height = sum(item['height'] for item in items)
        total_gaps = (len(items) - 1) * config.gap

        # Available space for flexible items
        available_space = height - total_item_height - total_gaps

        # Determine starting position based on justify property
        current_y = y
        if config.justify == 'end':
            current_y = y + available_space
        elif config.justify == 'center':
            current_y = y + available_space / 2
        elif config.justify in ('between', 'around', 'evenly'):
            # These will be handled differently below
            pass

        # Calculate spacing between items based on justification
        spacing = 0
        if len(items) > 1:
            if config.justify == 'between':
                spacing = available_space / (len(items) - 1)
            elif config.justify == 'around':
                spacing = available_space / len(items)
                current_y += spacing / 2
            elif config.justify == 'evenly':
                spacing = available_space / (len(items) + 1)
                current_y += spacing

        # Check if direction is reversed
        is_reversed = config.direction.endswith('-reverse')

        # Position each item
        for i, item in enumerate(items):
            # Adjust for reverse direction
            if is_reversed:
                item_idx = len(items) - 1 - i
            else:
                item_idx = i

            item_obj = config.objects[item_idx]
            item_width = item['width']
            item_height = item['height']

            # Get original y position to use as offset
            original_y = float(item_obj.y.replace('pt', '')) if isinstance(item_obj.y, str) else float(item_obj.y)

            # Calculate horizontal position based on align property
            item_x = x
            if config.align == 'center':
                # Treat the original x value of the object as an offset from the centered position
                original_x = float(item_obj.x.replace('pt', '')) if isinstance(item_obj.x, str) else float(item_obj.x)
                # Calculate centered position
                centered_x = x + (width - item_width) / 2
                # Apply the original x as an offset
                item_x = centered_x + original_x
            elif config.align == 'end':
                item_x = x + width - item_width
                # Add original x as offset
                original_x = float(item_obj.x.replace('pt', '')) if isinstance(item_obj.x, str) else float(item_obj.x)
                item_x += original_x
            elif config.align == 'stretch' and isinstance(item_obj, (TextObject, ImageObject)):
                # Only stretch width if it's not a nested group
                item_width = width
                item_obj.width = f"{width:.1f}pt"
                # Add original x as offset
                original_x = float(item_obj.x.replace('pt', '')) if isinstance(item_obj.x, str) else float(item_obj.x)
                item_x += original_x
            else:  # align: start or default
                # Add original x as offset
                original_x = float(item_obj.x.replace('pt', '')) if isinstance(item_obj.x, str) else float(item_obj.x)
                item_x += original_x

            # Create position strings with 'pt' suffix - apply original y as offset to layout-calculated position
            final_y = current_y + original_y
            item_obj.x = f"{item_x:.1f}pt"
            item_obj.y = f"{final_y:.1f}pt"

            # If this is a nested group, apply layout recursively
            if isinstance(item_obj, GroupObject):
                self.apply_layout(item_obj)

            # Move to next position - use the final_y (which includes the offset)
            # instead of current_y to properly account for offsets in subsequent items
            current_y = final_y + item_height + config.gap

            # Add additional spacing for justify modes that need it
            if config.justify in ('around', 'evenly'):
                current_y += spacing

    def apply_layout_to_container(self, container: ContainerObject) -> None:
        """
        Apply layout to all objects within the container.

        This works similarly to group layout, but containers may not have explicit
        width/height. If not provided, they are automatically calculated based on children.
        """
        if not container.objects:
            return

        # First, if width or height is None/auto, we need to calculate it based on child dimensions
        should_auto_width = container.width is None or (isinstance(container.width, str) and container.width == "auto")
        should_auto_height = container.height is None or (isinstance(container.height, str) and container.height == "auto")

        # Set default dimensions for calculation if needed
        if should_auto_width:
            container.width = "100pt"  # Temporary default
        if should_auto_height:
            container.height = "100pt"  # Temporary default

        if should_auto_width or should_auto_height:
            # Calculate the bounding box of all children
            child_dimensions = []
            for child_obj in container.objects:
                # Skip objects that don't have valid coordinates
                if not hasattr(child_obj, 'x') or not hasattr(child_obj, 'y'):
                    continue

                # Ensure coordinates are not None
                if child_obj.x is None or child_obj.y is None:
                    continue

                # Handle 'auto' values
                if isinstance(child_obj.x, str) and child_obj.x == 'auto':
                    continue
                if isinstance(child_obj.y, str) and child_obj.y == 'auto':
                    continue

                # Convert child x/y to float for calculations
                try:
                    child_x = float(child_obj.x.replace('pt', '')) if isinstance(child_obj.x, str) else float(child_obj.x)
                    child_y = float(child_obj.y.replace('pt', '')) if isinstance(child_obj.y, str) else float(child_obj.y)
                except (ValueError, TypeError):
                    # Skip if conversion fails
                    continue

                # Get width and height if available
                child_width = 20.0  # Default minimum width
                if hasattr(child_obj, 'width') and child_obj.width and child_obj.width != 'auto':
                    try:
                        child_width = float(child_obj.width.replace('pt', '')) if isinstance(child_obj.width, str) else float(child_obj.width)
                    except (ValueError, TypeError):
                        pass  # Keep default

                child_height = 20.0  # Default minimum height
                if hasattr(child_obj, 'height') and child_obj.height and child_obj.height != 'auto':
                    try:
                        child_height = float(child_obj.height.replace('pt', '')) if isinstance(child_obj.height, str) else float(child_obj.height)
                    except (ValueError, TypeError):
                        pass  # Keep default

                # Store the bounding box
                child_dimensions.append({
                    'x1': child_x,
                    'y1': child_y,
                    'x2': child_x + child_width,
                    'y2': child_y + child_height
                })

            if child_dimensions:
                # Find the bounding box
                min_x = min(d['x1'] for d in child_dimensions)
                max_x = max(d['x2'] for d in child_dimensions)
                min_y = min(d['y1'] for d in child_dimensions)
                max_y = max(d['y2'] for d in child_dimensions)

                # Calculate dimensions with padding
                padding = container.get_padding_as_dict()
                padding_h = padding['left'] + padding['right']
                padding_v = padding['top'] + padding['bottom']

                width = max_x - min_x + padding_h
                height = max_y - min_y + padding_v

                # Set the dimensions
                if should_auto_width:
                    container.width = f"{width}pt"
                if should_auto_height:
                    container.height = f"{height}pt"

        # Now proceed with normal layout, similar to groups
        # Get container dimensions from attributes - handle 'auto' values
        container_width = 100.0  # Default width
        if container.width is not None:
            if isinstance(container.width, str):
                if container.width == 'auto':
                    container_width = 100.0  # Default width for 'auto'
                else:
                    try:
                        container_width = float(container.width.replace('pt', ''))
                    except ValueError:
                        pass  # Keep default
            else:
                try:
                    container_width = float(container.width)
                except (ValueError, TypeError):
                    pass  # Keep default

        container_height = 100.0  # Default height
        if container.height is not None:
            if isinstance(container.height, str):
                if container.height == 'auto':
                    container_height = 100.0  # Default height for 'auto'
                else:
                    try:
                        container_height = float(container.height.replace('pt', ''))
                    except ValueError:
                        pass  # Keep default
            else:
                try:
                    container_height = float(container.height)
                except (ValueError, TypeError):
                    pass  # Keep default

        # Get padding as a standardized dictionary
        padding_dict = self._resolve_padding(getattr(container, "padding", container.get_padding_as_dict()))

        # Calculate available space for content
        content_width = container_width - padding_dict['left'] - padding_dict['right']
        content_height = container_height - padding_dict['top'] - padding_dict['bottom']

        # Base positions, adjusted for padding
        base_x = 0.0
        if container.x is not None:
            base_x = float(container.x.replace('pt', '')) if isinstance(container.x, str) else float(container.x)

        base_y = 0.0
        if container.y is not None:
            base_y = float(container.y.replace('pt', '')) if isinstance(container.y, str) else float(container.y)

        # Adjust base positions by padding
        content_x = base_x + padding_dict['left']
        content_y = base_y + padding_dict['top']

        # Determine flow direction
        direction = container.direction.lower() if hasattr(container, "direction") else "row"
        is_row = direction == "row"

        # Check if we need to wrap items
        should_wrap = getattr(container, "wrap", False)

        # Apply layout based on direction
        if is_row:
            self._apply_container_row_layout(
                container, padding_dict,
                should_wrap=should_wrap,
                content_width=content_width,
                content_height=content_height
            )
        else:  # column
            self._apply_container_column_layout(
                container, padding_dict,
                should_wrap=should_wrap,
                content_width=content_width,
                content_height=content_height
            )

        # Recursively apply layout to nested groups or containers
        for obj in container.objects:
            if isinstance(obj, GroupObject):
                self.apply_layout(obj)
            elif isinstance(obj, ContainerObject):
                self.apply_layout_to_container(obj)

    def _apply_container_row_layout(self, container: ContainerObject, padding_dict: Dict[str, float],
                                    should_wrap: bool, content_width: float, content_height: float) -> None:
        """Apply row layout to position objects horizontally within a container."""
        # Get item dimensions
        items = self._get_item_dimensions(container.objects)

        # Calculate total content width and determine available space
        total_item_width = sum(item['width'] for item in items)
        gap = getattr(container, "gap", 0)
        total_gaps = (len(items) - 1) * gap if len(items) > 1 else 0

        # Available space for flexible items
        available_space = content_width - total_item_width - total_gaps

        # Determine starting position based on justify property
        justify = getattr(container, "justify", "start")
        current_x = padding_dict['left']  # Start after left padding
        if justify == 'end':
            current_x += available_space
        elif justify == 'center':
            current_x += available_space / 2
        elif justify in ('between', 'around', 'evenly'):
            # These will be handled differently below
            pass

        # Calculate spacing between items based on justification
        spacing = 0
        if len(items) > 1:
            if justify == 'between':
                spacing = available_space / (len(items) - 1)
            elif justify == 'around':
                spacing = available_space / len(items)
                current_x += spacing / 2
            elif justify == 'evenly':
                spacing = available_space / (len(items) + 1)
                current_x += spacing

        # Check for reverse direction
        direction = getattr(container, "direction", "row")
        is_reversed = getattr(container, "is_reversed", False) or direction.endswith('-reverse')

        # Position each item
        for i, item in enumerate(items):
            # Adjust for reverse direction
            if is_reversed:
                item_idx = len(items) - 1 - i
            else:
                item_idx = i

            item_obj = item['object']
            item_width = item['width']
            item_height = item['height']

            # Skip positioning for explicitly positioned items
            is_positioned = hasattr(item_obj, "_positioned") and getattr(item_obj, "_positioned")

            if not is_positioned:
                # Calculate vertical position based on align property
                align = getattr(container, "align", "start")
                item_y = padding_dict['top']  # Start after top padding

                if align == 'center':
                    # Center the item vertically in the available space
                    item_y += (content_height - item_height) / 2
                elif align == 'end':
                    # Align to bottom of container
                    item_y += content_height - item_height
                elif align == 'stretch' and isinstance(item_obj, (TextObject, ImageObject)):
                    # Stretch item to fill container height
                    item_height = content_height
                    item_obj.height = f"{item_height}pt"

                # Calculate absolute position (container position + relative position)
                abs_x = float(container.x.replace('pt', '')) if isinstance(container.x, str) else float(container.x)
                abs_y = float(container.y.replace('pt', '')) if isinstance(container.y, str) else float(container.y)

                # Create position strings with 'pt' suffix
                final_x = abs_x + current_x
                item_obj.x = f"{final_x:.1f}pt"
                item_obj.y = f"{abs_y + item_y:.1f}pt"

                # Move to next position
                current_x += item_width + gap

                # Add additional spacing for justify modes that need it
                if justify in ('around', 'evenly'):
                    current_x += spacing

    def _apply_container_column_layout(self, container: ContainerObject, padding_dict: Dict[str, float],
                                      should_wrap: bool, content_width: float, content_height: float) -> None:
        """Apply column layout to position objects vertically within a container."""
        # Get item dimensions
        items = self._get_item_dimensions(container.objects)

        # Calculate total content height and determine available space
        total_item_height = sum(item['height'] for item in items)
        gap = getattr(container, "gap", 0)
        total_gaps = gap * (len(items) - 1) if len(items) > 1 else 0

        # Available space for flexible items
        available_space = content_height - total_item_height - total_gaps

        # Determine starting position based on justify property
        justify = getattr(container, "justify", "start")
        current_y = padding_dict['top']  # Start after top padding
        if justify == 'end':
            current_y += available_space
        elif justify == 'center':
            current_y += available_space / 2
        elif justify in ('between', 'around', 'evenly'):
            # These will be handled differently below
            pass

        # Position each item
        for i, item in enumerate(items):
            item_obj = item['object']
            item_width = item['width']
            item_height = item['height']

            # Special spacing calculations for justify options
            if i > 0:
                if justify == 'between' and len(items) > 1:
                    # Space evenly between items, no space at edges
                    gap_size = available_space / (len(items) - 1)
                    current_y += gap_size
                elif justify == 'around' and len(items) > 1:
                    # Space evenly around items, half space at edges
                    gap_size = available_space / len(items)
                    current_y += gap_size
                elif justify == 'evenly' and len(items) >= 1:
                    # Space evenly, equal space at edges and between
                    gap_size = available_space / (len(items) + 1)
                    current_y += gap_size
                else:
                    # Standard gap
                    current_y += gap

            # Skip positioning for explicitly positioned items
            is_positioned = hasattr(item_obj, "_positioned") and getattr(item_obj, "_positioned")

            if not is_positioned:
                # Calculate horizontal position based on align property
                align = getattr(container, "align", "start")
                item_x = padding_dict['left']  # Start after left padding

                if align == 'center':
                    # Center the item horizontally in the available space
                    item_x += (content_width - item_width) / 2
                elif align == 'end':
                    # Align to right side of container
                    item_x += content_width - item_width
                elif align == 'stretch' and isinstance(item_obj, (TextObject, ImageObject)):
                    # Stretch item to fill container width
                    item_width = content_width
                    item_obj.width = f"{item_width}pt"

                # Calculate absolute position (container position + relative position)
                abs_x = float(container.x.replace('pt', '')) if isinstance(container.x, str) else float(container.x)
                abs_y = float(container.y.replace('pt', '')) if isinstance(container.y, str) else float(container.y)

                # Create position strings with 'pt' suffix
                final_y = abs_y + current_y
                item_obj.x = f"{abs_x + item_x:.1f}pt"
                item_obj.y = f"{final_y:.1f}pt"

            # Move to next position
            current_y += item_height