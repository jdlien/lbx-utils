#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare different text dimension calculation approaches against P-touch Editor reference data.

This script implements multiple methods for calculating text dimensions and compares them
against the reference dimensions from P-touch Editor label files to determine which
approach produces the most consistent and accurate results.
"""

import os
import sys
import xml.etree.ElementTree as ET
import statistics
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from src.lbx_utils.text_dimensions import TextDimensionCalculator
from src.lbx_utils.text_dimensions import CalculationMethod

# Path to the sample P-touch Editor label.xml file
PTOUCH_LABEL_XML = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "data",
        "label_examples",
        "multiple-fonts-original",
        "label.xml"
    )
)

def extract_reference_data_from_xml(xml_path=PTOUCH_LABEL_XML):
    """Extract text dimension reference data from the P-touch Editor label XML file."""
    if not os.path.exists(xml_path):
        print(f"Reference P-touch Editor label file not found: {xml_path}")
        return []

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        namespace = {
            'pt': 'http://schemas.brother.info/ptouch/2007/lbx/main',
            'text': 'http://schemas.brother.info/ptouch/2007/lbx/text'
        }

        reference_data = []

        # Find all text objects
        text_elements = root.findall('.//text:text', namespace)

        for text_element in text_elements:
            # Get object style (dimensions)
            obj_style = text_element.find('.//pt:objectStyle', namespace)
            if obj_style is None:
                continue

            width_attr = obj_style.get('width')
            height_attr = obj_style.get('height')

            if width_attr is None or height_attr is None:
                continue

            width = float(width_attr.rstrip('pt'))
            height = float(height_attr.rstrip('pt'))

            # Get font info
            font_info = text_element.find('.//text:logFont', namespace)
            if font_info is None:
                continue

            font_name = font_info.get('name')
            weight_val = font_info.get('weight')
            weight = "bold" if weight_val and int(weight_val) >= 700 else "normal"
            italic = font_info.get('italic') == "true"

            # Get font size and orgSize
            font_ext = text_element.find('.//text:fontExt', namespace)
            if font_ext is None:
                continue

            size_attr = font_ext.get('size')
            org_size_attr = font_ext.get('orgSize')

            if size_attr is None:
                continue

            size = float(size_attr.rstrip('pt'))
            org_size = float(org_size_attr.rstrip('pt')) if org_size_attr else None

            # Calculate size ratio if both values are present
            size_ratio = org_size / size if org_size else None

            # Get text content
            data_element = text_element.find('.//pt:data', namespace)
            if data_element is None or data_element.text is None:
                continue

            text = data_element.text

            # Get text control settings
            text_control = text_element.find('.//text:textControl', namespace)
            auto_len = text_control.get('control') == "AUTOLEN" if text_control else False
            shrink = text_control.get('shrink') == "true" if text_control else False

            # Get text alignment
            text_align = text_element.find('.//text:textAlign', namespace)
            h_align = text_align.get('horizontalAlignment') if text_align else "LEFT"
            v_align = text_align.get('verticalAlignment') if text_align else "TOP"

            # Get text style
            text_style = text_element.find('.//text:textStyle', namespace)
            line_space = float(text_style.get('lineSpace', '0')) if text_style else 0
            char_space = float(text_style.get('charSpace', '0')) if text_style else 0

            reference_data.append({
                "text": text,
                "font_name": font_name,
                "size": size,
                "org_size": org_size,
                "size_ratio": size_ratio,
                "weight": weight,
                "weight_value": weight_val,
                "italic": italic,
                "width": width,
                "height": height,
                "auto_len": auto_len,
                "shrink": shrink,
                "h_align": h_align,
                "v_align": v_align,
                "line_space": line_space,
                "char_space": char_space
            })

        return reference_data

    except Exception as e:
        print(f"Failed to parse reference P-touch Editor label file: {str(e)}")
        return []

class DimensionCalculationMethod:
    """Base class for different text dimension calculation methods."""

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using this method."""
        raise NotImplementedError("Subclasses must implement calculate()")

class FreetypeMethod(DimensionCalculationMethod):
    """Standard FreeType calculation with adjustment factors."""

    def __init__(self, width_factor=1.0, height_factor=1.0):
        super().__init__(
            f"FreeType(w={width_factor:.2f},h={height_factor:.2f})",
            f"FreeType with width factor {width_factor} and height factor {height_factor}"
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True)
        self.width_factor = width_factor
        self.height_factor = height_factor

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using FreeType with adjustment factors."""
        width, height = self.calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic
        )
        return width * self.width_factor, height * self.height_factor

class PILMethod(DimensionCalculationMethod):
    """PIL-based calculation with adjustment factors."""

    def __init__(self, width_factor=1.0, height_factor=1.0):
        super().__init__(
            f"PIL(w={width_factor:.2f},h={height_factor:.2f})",
            f"PIL with width factor {width_factor} and height factor {height_factor}"
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True)
        self.width_factor = width_factor
        self.height_factor = height_factor

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using PIL with adjustment factors."""
        width, height = self.calculator.calculate_text_dimensions_pil(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic
        )
        return width * self.width_factor, height * self.height_factor

class OrgSizeMethod(DimensionCalculationMethod):
    """Method using size ratio from XML orgSize attribute."""

    def __init__(self, org_size_ratio=3.6, fixed_height_factor=0.38):
        super().__init__(
            f"OrgSize(ratio={org_size_ratio:.2f},h={fixed_height_factor:.2f})",
            f"Size calculation based on orgSize ratio {org_size_ratio}"
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True)
        self.org_size_ratio = org_size_ratio
        self.fixed_height_factor = fixed_height_factor

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using orgSize ratio."""
        # Get the base dimensions
        width, height = self.calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size * self.org_size_ratio,  # Use orgSize for calculation
            weight=weight,
            italic=italic
        )

        # Scale down to match PTouch size expectations
        return width, height * self.fixed_height_factor

class FontSpecificMethod(DimensionCalculationMethod):
    """Method using font-specific adjustment factors."""

    def __init__(self, font_factors=None):
        if font_factors is None:
            # Default factors for common fonts
            font_factors = {
                "Helsinki": (1.20, 0.57),
                "Helsinki Narrow": (1.25, 0.58),
                "Arial": (1.18, 0.55),
                "default": (1.21, 0.56)  # Default for other fonts
            }

        super().__init__(
            "FontSpecific",
            "Font-specific adjustment factors"
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True)
        self.font_factors = font_factors

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using font-specific adjustments."""
        width, height = self.calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic
        )

        # Get font-specific factors or use default
        width_factor, height_factor = self.font_factors.get(
            font_name, self.font_factors["default"]
        )

        return width * width_factor, height * height_factor

class CharacterSpacingMethod(DimensionCalculationMethod):
    """Method that accounts for P-touch Editor's character spacing."""

    def __init__(self, base_width_factor=1.15, base_height_factor=0.56):
        super().__init__(
            f"CharSpacing(w={base_width_factor:.2f},h={base_height_factor:.2f})",
            "Considers character spacing attribute from P-touch"
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True)
        self.base_width_factor = base_width_factor
        self.base_height_factor = base_height_factor

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions accounting for character spacing."""
        width, height = self.calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic
        )

        # Get character spacing from kwargs if available
        char_space = kwargs.get('char_space', 0)

        # Adjust width based on character spacing
        # Each character gets additional char_space units
        if char_space != 0:
            char_count = len(text.replace(" ", ""))  # Count non-space characters
            width += char_count * char_space

        return width * self.base_width_factor, height * self.base_height_factor

class SkiaMethod(DimensionCalculationMethod):
    """Skia-based calculation with adjustment factors."""

    def __init__(self, width_factor=0.8, height_factor=0.95):
        super().__init__(
            f"Skia(w={width_factor:.2f},h={height_factor:.2f})",
            f"Skia with width factor {width_factor} and height factor {height_factor}"
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True, apply_technique_adjustments=True)
        self.width_factor = width_factor
        self.height_factor = height_factor
        self.skia_method = CalculationMethod.SKIA

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using Skia with adjustment factors."""
        width, height = self.calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic,
            method=self.skia_method
        )
        return width * self.width_factor, height * self.height_factor

class SkiaAdjustedMethod(DimensionCalculationMethod):
    """Skia-based calculation with built-in technique-specific adjustments."""

    def __init__(self):
        super().__init__(
            "Skia(adjusted)",
            "Skia with built-in technique-specific adjustment factors"
        )
        self.calculator = TextDimensionCalculator(
            debug=False,
            allow_fallbacks=True,
            apply_technique_adjustments=True
        )
        self.skia_method = CalculationMethod.SKIA

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using Skia with built-in adjustments."""
        return self.calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic,
            method=self.skia_method
        )

class SkiaFontSpecificMethod(DimensionCalculationMethod):
    """Skia-based calculation with font-specific adjustment factors."""

    def __init__(self, font_factors=None):
        if font_factors is None:
            # Default Skia-specific factors for common fonts
            font_factors = {
                "Helsinki": (0.8, 0.95),
                "Helsinki Narrow": (0.85, 0.95),
                "Arial": (0.78, 0.93),
                "default": (0.8, 0.95)  # Default for other fonts
            }

        super().__init__(
            "Skia(FontSpecific)",
            "Skia with font-specific adjustment factors"
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True)
        self.font_factors = font_factors
        self.skia_method = CalculationMethod.SKIA

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using Skia with font-specific adjustments."""
        width, height = self.calculator.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic,
            method=self.skia_method
        )

        # Get font-specific factors or use default
        width_factor, height_factor = self.font_factors.get(
            font_name, self.font_factors["default"]
        )

        return width * width_factor, height * height_factor

class SkiaHeightTechniques(DimensionCalculationMethod):
    """Skia-based calculation with various height calculation techniques."""

    def __init__(self, technique="default", padding_factor=0.0):
        name_suffix = technique
        if technique == "ascent_descent_padding" and padding_factor != 0.0:
            name_suffix += f"_{padding_factor:.2f}"

        super().__init__(
            f"Skia(height={name_suffix})",
            f"Skia with {technique} height calculation" +
            (f" and padding factor {padding_factor}" if padding_factor != 0.0 else "")
        )
        self.calculator = TextDimensionCalculator(debug=False, allow_fallbacks=True)
        self.skia_method = CalculationMethod.SKIA
        self.technique = technique
        self.padding_factor = padding_factor

    def calculate(self, text, font_name, size, weight, italic, **kwargs):
        """Calculate text dimensions using Skia with different height calculation techniques."""
        # Get the Skia technique instance directly
        technique = self.calculator._techniques[self.skia_method]
        if not technique.is_available():
            raise ImportError("Skia technique is not available")

        # Calculate width using standard method
        width, height = technique.calculate_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic
        )

        # Get font metrics to calculate height differently
        try:
            # Access _create_font safely through the SkiaTechnique class
            if hasattr(technique, '_create_font'):
                font = technique._create_font(font_name, size, weight, italic)
                metrics = font.getMetrics()

                # Extract metrics
                ascent = abs(metrics.fAscent)  # Ascent is negative in Skia
                descent = metrics.fDescent
                leading = metrics.fLeading

                # Calculate height based on the selected technique
                if self.technique == "ascent_only":
                    calculated_height = ascent
                elif self.technique == "descent_only":
                    calculated_height = descent
                elif self.technique == "ascent_descent":
                    calculated_height = ascent + descent
                elif self.technique == "ascent_descent_leading":
                    calculated_height = ascent + descent + leading
                elif self.technique == "ascent_descent_padding":
                    # Add a percentage of the font size as padding
                    calculated_height = ascent + descent + (size * self.padding_factor)
                else:
                    # Default - use the standard height calculation
                    calculated_height = height

                return width, calculated_height
            else:
                # Fall back to standard calculation if method not available
                return width, height

        except Exception as e:
            # Fall back to standard calculation if metrics extraction fails
            return width, height

def compare_methods(reference_data):
    """Compare different calculation methods against reference data."""
    methods = [
        # Current adjustment factors used in the code
        FreetypeMethod(width_factor=1.087, height_factor=0.371),

        # Suggested adjustments from test results
        FreetypeMethod(width_factor=1.21, height_factor=0.57),

        # PIL method with adjustments
        PILMethod(width_factor=1.2, height_factor=1.4),

        # Skia methods
        SkiaMethod(width_factor=0.8, height_factor=0.95),
        SkiaMethod(width_factor=1.0, height_factor=0.38),
        SkiaAdjustedMethod(),
        SkiaFontSpecificMethod(),

        # New height calculation techniques
        SkiaHeightTechniques(technique="ascent_only"),
        SkiaHeightTechniques(technique="descent_only"),
        SkiaHeightTechniques(technique="ascent_descent"),
        SkiaHeightTechniques(technique="ascent_descent_leading"),
        SkiaHeightTechniques(technique="ascent_descent_padding", padding_factor=0.05),
        SkiaHeightTechniques(technique="ascent_descent_padding", padding_factor=0.10),
        SkiaHeightTechniques(technique="ascent_descent_padding", padding_factor=0.15),
        SkiaHeightTechniques(technique="ascent_descent_padding", padding_factor=0.20),

        # orgSize method
        OrgSizeMethod(org_size_ratio=3.6, fixed_height_factor=0.38),

        # Font-specific method
        FontSpecificMethod(),

        # Character spacing method
        CharacterSpacingMethod()
    ]

    results = []

    for item in reference_data:
        expected_width = item["width"]
        expected_height = item["height"]

        for method in methods:
            try:
                width, height = method.calculate(
                    text=item["text"],
                    font_name=item["font_name"],
                    size=item["size"],
                    weight=item["weight"],
                    italic=item["italic"],
                    char_space=item["char_space"],
                    line_space=item["line_space"]
                )

                # Calculate differences
                width_diff = width - expected_width
                height_diff = height - expected_height
                width_diff_pct = (width_diff / expected_width) * 100
                height_diff_pct = (height_diff / expected_height) * 100

                # Calculate mean absolute percentage error
                mape = (abs(width_diff_pct) + abs(height_diff_pct)) / 2

                results.append({
                    "method": method.name,
                    "font": item["font_name"],
                    "size": item["size"],
                    "text_length": len(item["text"]),
                    "expected_width": expected_width,
                    "expected_height": expected_height,
                    "calc_width": width,
                    "calc_height": height,
                    "width_diff": width_diff,
                    "height_diff": height_diff,
                    "width_diff_pct": width_diff_pct,
                    "height_diff_pct": height_diff_pct,
                    "mape": mape,
                    "width_ratio": width / expected_width,
                    "height_ratio": height / expected_height
                })

            except Exception as e:
                print(f"Error with method {method.name} for {item['font_name']}: {str(e)}")
                continue

    return results

def analyze_results(results):
    """Analyze the comparison results and provide summary metrics."""
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(results)

    # Group by method and calculate summary statistics
    summary = df.groupby('method').agg({
        'width_diff_pct': ['mean', 'std', 'min', 'max'],
        'height_diff_pct': ['mean', 'std', 'min', 'max'],
        'mape': ['mean', 'std', 'min', 'max'],
        'width_ratio': ['mean', 'std'],
        'height_ratio': ['mean', 'std']
    })

    # Calculate overall height score (lower is better)
    summary['height_score'] = abs(summary[('height_diff_pct', 'mean')]) + summary[('height_diff_pct', 'std')]

    # Calculate consistency score (lower is better)
    summary['consistency_score'] = summary[('mape', 'std')] + summary[('mape', 'mean')]

    # Sort by height score first
    height_summary = summary.sort_values('height_score')

    # Sort by consistency score
    consistency_summary = summary.sort_values('consistency_score')

    return df, height_summary, consistency_summary

def visualize_results(df, height_summary, consistency_summary):
    """Create visualization of the results."""
    # Create a figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Text Dimension Calculation Method Comparison', fontsize=16)

    # Plot 1: Height error by method (top methods only)
    top_height_methods = height_summary.index[:10]  # Top 10 methods by height accuracy
    height_means = height_summary.loc[top_height_methods, ('height_diff_pct', 'mean')].values
    height_stds = height_summary.loc[top_height_methods, ('height_diff_pct', 'std')].values

    axes[0, 0].barh(top_height_methods, height_means, xerr=height_stds, alpha=0.7)
    axes[0, 0].axvline(x=0, color='r', linestyle='--', alpha=0.5)
    axes[0, 0].set_title('Height Error % by Method (Lower is Better)')
    axes[0, 0].set_xlabel('Height Error %')
    axes[0, 0].grid(axis='x', linestyle='--', alpha=0.7)

    # Plot 2: Height ratio distributions
    top_methods = list(consistency_summary.index[:8])
    for method in top_methods:
        method_df = df[df['method'] == method]
        axes[0, 1].scatter(method_df['expected_height'], method_df['calc_height'],
                          label=method, alpha=0.7)

    # Plot ideal 1:1 line
    max_height = max(df['expected_height'].max(), df['calc_height'].max())
    axes[0, 1].plot([0, max_height], [0, max_height], 'k--', alpha=0.5)

    axes[0, 1].set_title('Calculated vs Expected Height')
    axes[0, 1].set_xlabel('Expected Height (pt)')
    axes[0, 1].set_ylabel('Calculated Height (pt)')
    axes[0, 1].grid(True, linestyle='--', alpha=0.7)
    axes[0, 1].legend(loc='upper left', bbox_to_anchor=(1, 1))

    # Plot 3: Height error by font size for top methods
    sizes = sorted(df['size'].unique())
    for method in top_methods[:4]:  # Top 4 methods for clarity
        method_df = df[df['method'] == method]
        size_errors = []
        for size in sizes:
            size_df = method_df[method_df['size'] == size]
            if not size_df.empty:
                size_errors.append(size_df['height_diff_pct'].mean())
            else:
                size_errors.append(float('nan'))

        axes[1, 0].plot(sizes, size_errors, marker='o', label=method)

    axes[1, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[1, 0].set_title('Height Error % by Font Size')
    axes[1, 0].set_xlabel('Font Size (pt)')
    axes[1, 0].set_ylabel('Height Error %')
    axes[1, 0].grid(True, linestyle='--', alpha=0.7)
    axes[1, 0].legend()

    # Plot 4: Height error by font for top methods
    fonts = sorted(df['font'].unique())
    font_indices = range(len(fonts))

    for method in top_methods[:4]:  # Top 4 methods for clarity
        method_df = df[df['method'] == method]
        font_errors = []
        for font in fonts:
            font_df = method_df[method_df['font'] == font]
            if not font_df.empty:
                font_errors.append(font_df['height_diff_pct'].mean())
            else:
                font_errors.append(float('nan'))

        axes[1, 1].plot(font_indices, font_errors, marker='o', label=method)

    axes[1, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[1, 1].set_title('Height Error % by Font')
    axes[1, 1].set_xlabel('Font')
    axes[1, 1].set_xticks(font_indices)
    axes[1, 1].set_xticklabels(fonts, rotation=45, ha='right')
    axes[1, 1].set_ylabel('Height Error %')
    axes[1, 1].grid(True, linestyle='--', alpha=0.7)
    axes[1, 1].legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('text_height_comparison.png', dpi=300, bbox_inches='tight')
    print(f"Height comparison visualization saved as 'text_height_comparison.png'")

def print_detailed_report(df, height_summary, consistency_summary):
    """Print a detailed report of the results."""
    # Print overall summary
    print("\n" + "="*80)
    print("TEXT DIMENSION CALCULATION METHOD COMPARISON")
    print("="*80)

    # Print height-focused summary
    print("\nMETHODS SORTED BY HEIGHT ACCURACY (LOWER SCORE IS BETTER):")
    print("-"*80)
    for method in height_summary.index[:8]:  # Show top 8 methods
        height_mean = height_summary.loc[method, ('height_diff_pct', 'mean')]
        height_std = height_summary.loc[method, ('height_diff_pct', 'std')]
        height_ratio = height_summary.loc[method, ('height_ratio', 'mean')]
        height_score = float(height_summary.loc[method, 'height_score'])

        print(f"Method: {method}")
        print(f"  Mean Height Error: {height_mean:.2f}% ± {height_std:.2f}%")
        print(f"  Avg Height Ratio (calc/expected): {height_ratio:.4f}")
        print(f"  Height Score: {height_score:.4f}")
        print("-"*80)

    # Print consistency-focused summary
    print("\nMETHODS SORTED BY OVERALL CONSISTENCY (LOWER SCORE IS BETTER):")
    print("-"*80)
    for method in consistency_summary.index[:8]:  # Show top 8 methods
        mape_mean = consistency_summary.loc[method, ('mape', 'mean')]
        mape_std = consistency_summary.loc[method, ('mape', 'std')]
        width_ratio = consistency_summary.loc[method, ('width_ratio', 'mean')]
        height_ratio = consistency_summary.loc[method, ('height_ratio', 'mean')]
        score = float(consistency_summary.loc[method, 'consistency_score'])

        print(f"Method: {method}")
        print(f"  Mean Error: {mape_mean:.2f}% ± {mape_std:.2f}%")
        print(f"  Avg Width Ratio (calc/expected): {width_ratio:.4f}")
        print(f"  Avg Height Ratio (calc/expected): {height_ratio:.4f}")
        print(f"  Consistency Score: {score:.4f}")
        print("-"*80)

    # Print detailed method performance by font
    print("\nDETAILED HEIGHT PERFORMANCE BY FONT:")
    print("-"*80)

    fonts = df['font'].unique()
    for font in fonts:
        print(f"\nFont: {font}")
        font_df = df[df['font'] == font]

        # Get top 5 methods by height for this font
        methods_by_height = font_df.groupby('method')['height_diff_pct'].apply(
            lambda x: (abs(x.mean()), x.std())).sort_values().head(5).index

        for method in methods_by_height:
            method_df = font_df[font_df['method'] == method]
            if not method_df.empty:
                height_mean = method_df['height_diff_pct'].mean()
                height_std = method_df['height_diff_pct'].std()
                height_ratio = method_df['height_ratio'].mean()

                print(f"  {method}:")
                print(f"    Mean Height Error: {height_mean:.2f}% ± {height_std:.2f}%")
                print(f"    Height Ratio: {height_ratio:.4f}")

    # Print the best method for height calculation
    best_height_method = height_summary.index[0]
    print("\n" + "="*80)
    print(f"RECOMMENDATION FOR HEIGHT CALCULATION: {best_height_method}")
    print("="*80)

    # Provide code snippet for implementation
    print("\n" + "="*80)
    print("IMPLEMENTATION RECOMMENDATIONS FOR HEIGHT CALCULATION:")
    print("="*80)

    # Extract information from the method name
    method_name = str(best_height_method)
    if "ascent_only" in method_name:
        print("# Use ascent only for height calculation")
        print("height = abs(metrics.fAscent)")
    elif "descent_only" in method_name:
        print("# Use descent only for height calculation")
        print("height = metrics.fDescent")
    elif "ascent_descent_leading" in method_name:
        print("# Use ascent + descent + leading for height calculation")
        print("height = abs(metrics.fAscent) + metrics.fDescent + metrics.fLeading")
    elif "ascent_descent_padding" in method_name:
        padding = float(method_name.split("_")[-1]) if "_" in method_name.split("padding")[1] else 0.0
        print(f"# Use ascent + descent + padding ({padding:.2f} of font size) for height calculation")
        print(f"height = abs(metrics.fAscent) + metrics.fDescent + (font_size * {padding:.2f})")
    elif "ascent_descent" in method_name:
        print("# Use ascent + descent for height calculation")
        print("height = abs(metrics.fAscent) + metrics.fDescent")
    else:
        # If it's a standard method with a height factor
        if "height=" in method_name:
            factor = method_name.split("height=")[1].split(")")[0]
            print(f"# Apply height factor of {factor}")
            print(f"height = original_height * {factor}")

def main():
    """Main function to run the comparison."""
    print("Extracting reference data from P-touch Editor label file...")
    reference_data = extract_reference_data_from_xml()

    if not reference_data:
        print("No reference data found. Exiting.")
        return

    print(f"Found {len(reference_data)} text objects with dimension data.")

    # Print reference data summary
    print("\nREFERENCE DATA SUMMARY:")
    for i, item in enumerate(reference_data):
        print(f"{i+1}. Font: {item['font_name']} {item['size']}pt, " +
              f"Weight: {item['weight']}, Italic: {item['italic']}")
        print(f"   Text: '{item['text'][:40]}{'...' if len(item['text']) > 40 else ''}'")
        print(f"   Dimensions: {item['width']:.2f}pt × {item['height']:.2f}pt")
        if item['size_ratio']:
            print(f"   Size ratio (orgSize/size): {item['size_ratio']:.2f}")
        print(f"   Character spacing: {item['char_space']}")
        print(f"   Line spacing: {item['line_space']}")
        print()

    print("Comparing calculation methods...")
    results = compare_methods(reference_data)

    print("Analyzing results...")
    df, height_summary, consistency_summary = analyze_results(results)

    print_detailed_report(df, height_summary, consistency_summary)

    print("Generating visualization...")
    try:
        visualize_results(df, height_summary, consistency_summary)
    except Exception as e:
        print(f"Error generating visualization: {str(e)}")

    print("\nAnalysis complete!")

if __name__ == "__main__":
    main()