#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compare all text dimension calculation techniques against P-touch Editor reference data.

This script takes the reference data from test_text_dimensions.py and compares the results
of each calculation technique without adjustments, showing the differences in percentage.
"""

import os
import sys
import pandas as pd
import numpy as np
from tabulate import tabulate
from typing import Dict, List, Tuple, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import platform
import matplotlib
import warnings
from scipy import stats
import matplotlib.patches as mpatches
from collections import defaultdict
import argparse

# Suppress the specific matplotlib deprecation warning about 'labels' parameter
warnings.filterwarnings("ignore", message="The 'labels' parameter of boxplot")

# Add the parent directory to the path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary components
from src.lbx_utils.text_dimensions import (
    TextDimensionCalculator,
    CalculationMethod
)

# Import reference data from the test file
from tests.test_text_dimensions import PTOUCH_REFERENCE_DATA

# Set up constants
TECHNIQUES = [
    CalculationMethod.SKIA,        # Skia first for priority
    CalculationMethod.PANGO,
    CalculationMethod.HARFBUZZ,
    CalculationMethod.FREETYPE,
    CalculationMethod.PIL,
    CalculationMethod.APPROXIMATION
]

# Add Core Text technique if on macOS
if platform.system() == "Darwin" and hasattr(CalculationMethod, "CORE_TEXT"):
    TECHNIQUES.insert(1, CalculationMethod.CORE_TEXT)  # Add as second priority after Skia

# Constants for inter-character spacing analysis
SPACING_MIN = 0.0
SPACING_MAX = 3.0
SPACING_STEP = 0.1
DEFAULT_SPACING = 0.1  # Current default value

def format_technique_name(technique: str) -> str:
    """Format technique name for display in reports and plots."""
    if isinstance(technique, CalculationMethod):
        technique = technique.value

    if technique == "skia":
        return "Skia"
    elif technique == "core_text":
        return "Core_text"
    elif technique == "pango":
        return "Pango"
    elif technique == "harfbuzz":
        return "Harfbuzz"
    elif technique == "freetype":
        return "Freetype"
    elif technique == "pil":
        return "PIL"
    elif technique == "approximation":
        return "Approximation"
    else:
        return technique.capitalize()

def calculate_with_technique(
    calc: TextDimensionCalculator,
    technique: CalculationMethod,
    text: str,
    font_name: str,
    size: float,
    weight: str,
    italic: bool
) -> Optional[Tuple[float, float]]:
    """Calculate dimensions using a specific technique with error handling."""
    try:
        width, height = calc.calculate_text_dimensions(
            text=text,
            font_name=font_name,
            size=size,
            weight=weight,
            italic=italic,
            method=technique
        )
        return width, height
    except Exception as e:
        print(f"Error calculating with {format_technique_name(technique)}: {str(e)}")
        return None

def compare_dimensions(
    reference: Dict[str, Any],
    calculated: Tuple[float, float]
) -> Tuple[float, float, float, float]:
    """
    Compare calculated dimensions with reference data.

    Returns:
        Tuple of (width_diff, height_diff, width_diff_pct, height_diff_pct)
    """
    if calculated is None:
        return float('nan'), float('nan'), float('nan'), float('nan')

    ref_width = reference["width"]
    ref_height = reference["height"]
    calc_width, calc_height = calculated

    width_diff = calc_width - ref_width
    height_diff = calc_height - ref_height

    width_diff_pct = (width_diff / ref_width) * 100 if ref_width != 0 else float('nan')
    height_diff_pct = (height_diff / ref_height) * 100 if ref_height != 0 else float('nan')

    return width_diff, height_diff, width_diff_pct, height_diff_pct

def colorize_diff(diff_pct: float) -> str:
    """Return a colored string based on the difference percentage."""
    if np.isnan(diff_pct):
        return "N/A"

    diff_str = f"{diff_pct:+.1f}%"

    if abs(diff_pct) < 5:
        # Green - very close
        return f"\033[92m{diff_str}\033[0m"
    elif abs(diff_pct) < 10:
        # Yellow - somewhat close
        return f"\033[93m{diff_str}\033[0m"
    else:
        # Red - significant difference
        return f"\033[91m{diff_str}\033[0m"

def generate_markdown_report(
    results_df: pd.DataFrame,
    summary_stats: List[Dict[str, Any]],
    adjustment_factors: List[Dict[str, Any]],
    font_stats: Dict[str, List[Dict[str, Any]]],
    available_techniques: List[CalculationMethod]
) -> str:
    """
    Generate a detailed markdown report.

    Args:
        results_df: DataFrame with all comparison results
        summary_stats: List of dictionaries with summary statistics
        adjustment_factors: List of dictionaries with adjustment factors
        font_stats: Dictionary mapping font names to statistics
        available_techniques: List of available calculation techniques

    Returns:
        Markdown formatted report as a string
    """
    md = []

    # Title and introduction
    md.append("# Text Dimension Calculation Techniques Comparison")
    md.append("\nThis report compares various text dimension calculation techniques against P-touch Editor reference values.")
    md.append("\n## Summary Statistics")

    # Summary statistics table
    md.append("\n### Overall Performance")
    md.append("\n| Technique | Avg Width Diff (%) | Avg Height Diff (%) | Median Width Diff (%) | Median Height Diff (%) | Std Width Diff (%) | Std Height Diff (%) |")
    md.append("| --- | --- | --- | --- | --- | --- | --- |")
    for stat in summary_stats:
        md.append(f"| {stat['Technique']} | {stat['Avg Width Diff (%)']} | {stat['Avg Height Diff (%)']} | " +
                 f"{stat['Median Width Diff (%)']} | {stat['Median Height Diff (%)']} | " +
                 f"{stat['Std Width Diff (%)']} | {stat['Std Height Diff (%)']} |")

    # Adjustment factors table
    md.append("\n### Suggested Adjustment Factors")
    md.append("\n| Technique | Width Factor | Height Factor |")
    md.append("| --- | --- | --- |")
    for factor in adjustment_factors:
        md.append(f"| {factor['Technique']} | {factor['Width Factor']} | {factor['Height Factor']} |")

    # Font-specific statistics
    md.append("\n## Font-Specific Statistics")
    for font_name, stats in font_stats.items():
        md.append(f"\n### {font_name} Font")
        md.append("\n| Technique | Avg Width Diff (%) | Avg Height Diff (%) | Width Factor | Height Factor |")
        md.append("| --- | --- | --- | --- | --- |")
        for stat in stats:
            md.append(f"| {stat['Technique']} | {stat['Avg Width Diff (%)']} | {stat['Avg Height Diff (%)']} | " +
                     f"{stat['Width Factor']} | {stat['Height Factor']} |")

    # Individual string comparisons
    md.append("\n## Individual String Comparisons")

    # Group by font
    for font_name in sorted(results_df['font_name'].unique()):
        md.append(f"\n### {font_name} Font")

        # Filter data for this font
        font_data = results_df[results_df['font_name'] == font_name]

        # Group by size and weight
        for size in sorted(font_data['size'].unique()):
            for weight in sorted(font_data['weight'].unique()):
                subset = font_data[(font_data['size'] == size) & (font_data['weight'] == weight)]

                if len(subset) == 0:
                    continue

                # Add a section for this size/weight combination
                md.append(f"\n#### {size}pt {weight}")

                # Create a table for each text string
                for idx, row in subset.iterrows():
                    text = row['text']
                    ref_width = row['p-touch_width']
                    ref_height = row['p-touch_height']

                    md.append(f"\n**Text: `{text}`**")
                    md.append("\n| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |")
                    md.append("| --- | --- | --- | --- | --- |")
                    md.append(f"| P-touch Reference | {ref_width:.2f} | {ref_height:.2f} | - | - |")

                    # Add rows for each technique in consistent order
                    for technique in TECHNIQUES:
                        if technique not in available_techniques:
                            continue

                        tech_name = format_technique_name(technique)
                        tech_value = technique.value

                        width = row.get(f"{tech_value}_width")
                        height = row.get(f"{tech_value}_height")
                        width_diff_pct = row.get(f"{tech_value}_width_diff_pct")
                        height_diff_pct = row.get(f"{tech_value}_height_diff_pct")

                        if width is not None:
                            md.append(f"| {tech_name} | {width:.2f} | {height:.2f} | {width_diff_pct:+.1f}% | {height_diff_pct:+.1f}% |")
                        else:
                            md.append(f"| {tech_name} | N/A | N/A | N/A | N/A |")

    # Add links to plots
    md.append("\n## Visualizations")
    md.append("\n### Width Difference Distribution")
    md.append("\n![Width Difference Boxplot](plots/width_diff_boxplot.png)")

    md.append("\n### Height Difference Distribution")
    md.append("\n![Height Difference Boxplot](plots/height_diff_boxplot.png)")

    return "\n".join(md)

def calculate_regression_models(df: pd.DataFrame, available_techniques: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate linear regression models between calculated dimensions and P-Touch reference values.

    Returns a dictionary with regression statistics for each technique.
    """
    regression_models = {}

    for technique in available_techniques:
        try:
            # Get the technique value for column names
            technique_value = technique.value if hasattr(technique, 'value') else technique

            # Filter out rows where the technique's values are NaN
            tech_df = df[df[f"{technique_value}_width"].notna() & df[f"{technique_value}_height"].notna()]

            # Skip if we don't have enough data points
            if len(tech_df) < 5:
                print(f"Skipping {technique_value} due to insufficient data points")
                continue

            # Extract reference and calculated values
            ref_widths = tech_df["p-touch_width"].values.astype(float)
            ref_heights = tech_df["p-touch_height"].values.astype(float)
            calc_widths = tech_df[f"{technique_value}_width"].values.astype(float)
            calc_heights = tech_df[f"{technique_value}_height"].values.astype(float)

            # Perform linear regression for width (y = mx + b)
            slope_w, intercept_w, r_value_w, p_value_w, std_err_w = stats.linregress(calc_widths, ref_widths)

            # Perform linear regression for height (y = mx + b)
            slope_h, intercept_h, r_value_h, p_value_h, std_err_h = stats.linregress(calc_heights, ref_heights)

            # Calculate prediction errors using the linear model
            width_predictions = slope_w * calc_widths + intercept_w
            height_predictions = slope_h * calc_heights + intercept_h

            width_mean_error = np.mean(np.abs(width_predictions - ref_widths))
            height_mean_error = np.mean(np.abs(height_predictions - ref_heights))

            # Calculate mean absolute percentage error (MAPE)
            width_mape = np.mean(np.abs((ref_widths - width_predictions) / ref_widths)) * 100
            height_mape = np.mean(np.abs((ref_heights - height_predictions) / ref_heights)) * 100

            # Store the results
            regression_models[technique] = {
                "width_slope": slope_w,
                "width_intercept": intercept_w,
                "width_r_squared": r_value_w**2,
                "width_p_value": p_value_w,
                "width_std_err": std_err_w,
                "width_mean_error": width_mean_error,
                "width_mape": width_mape,

                "height_slope": slope_h,
                "height_intercept": intercept_h,
                "height_r_squared": r_value_h**2,
                "height_p_value": p_value_h,
                "height_std_err": std_err_h,
                "height_mean_error": height_mean_error,
                "height_mape": height_mape,
            }
        except Exception as e:
            print(f"Error analyzing {technique if not hasattr(technique, 'value') else technique.value}: {str(e)}")

    return regression_models

def plot_regression_models(df: pd.DataFrame, regression_models: Dict[str, Dict[str, Any]], available_techniques: List[str]):
    """
    Generate scatter plots with regression lines for each technique.
    """
    # Check if we have any valid regression models
    if not regression_models:
        print("No valid regression models to plot")
        return

    # Create a plots directory if it doesn't exist
    os.makedirs("plots", exist_ok=True)

    # Plot width comparisons
    plt.figure(figsize=(14, 12))

    # Create a color map for the techniques
    techniques_to_plot = [t for t in available_techniques if t in regression_models]
    colors = plt.cm.tab10.colors[:len(techniques_to_plot)]

    legend_handles = []

    for i, technique in enumerate(techniques_to_plot):
        try:
            # Get the technique value for column names
            technique_value = technique.value if hasattr(technique, 'value') else technique

            # Filter rows where this technique has values
            tech_df = df[df[f"{technique_value}_width"].notna()]

            # Skip if we don't have enough data points
            if len(tech_df) < 5:
                continue

            # Extract values
            x = tech_df[f"{technique_value}_width"].values.astype(float)
            y = tech_df["p-touch_width"].values.astype(float)

            # Get regression model parameters
            model = regression_models[technique]
            slope = model["width_slope"]
            intercept = model["width_intercept"]
            r_squared = model["width_r_squared"]

            # Plot scatter points
            plt.scatter(x, y, color=colors[i], alpha=0.6, s=30)

            # Plot regression line
            x_line = np.array([float(min(x)), float(max(x))])
            y_line = slope * x_line + intercept
            plt.plot(x_line, y_line, color=colors[i], linewidth=2)

            # Add to legend
            legend_handles.append(mpatches.Patch(
                color=colors[i],
                label=f"{format_technique_name(technique)}: y={slope:.4f}x{'+' if intercept >= 0 else ''}{intercept:.4f}, R²={r_squared:.4f}"
            ))
        except Exception as e:
            print(f"Error plotting width for {technique if not hasattr(technique, 'value') else technique.value}: {str(e)}")

    if legend_handles:
        # Add ideal line (y=x)
        try:
            max_val = float(max(max(df["p-touch_width"].max(), df[df.filter(like="_width").columns].max().max())))
            plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label="y=x")
        except:
            # If there's an error with the max calculation, just use a reasonable default
            plt.plot([0, 200], [0, 200], 'k--', alpha=0.3, label="y=x")

        plt.xlabel("Calculated Width (pts)")
        plt.ylabel("P-Touch Reference Width (pts)")
        plt.title("Linear Regression: Calculated vs. P-Touch Reference Width")
        plt.grid(alpha=0.3)
        plt.axis('equal')
        plt.legend(handles=legend_handles, loc="upper left", fontsize=8)
        plt.tight_layout()
        plt.savefig("plots/width_regression.png")
    else:
        print("No valid data for width regression plot")

    # Plot height comparisons
    plt.figure(figsize=(14, 12))
    legend_handles = []

    for i, technique in enumerate(techniques_to_plot):
        try:
            # Get the technique value for column names
            technique_value = technique.value if hasattr(technique, 'value') else technique

            # Filter rows where this technique has values
            tech_df = df[df[f"{technique_value}_height"].notna()]

            # Skip if we don't have enough data points
            if len(tech_df) < 5:
                continue

            # Extract values
            x = tech_df[f"{technique_value}_height"].values.astype(float)
            y = tech_df["p-touch_height"].values.astype(float)

            # Get regression model parameters
            model = regression_models[technique]
            slope = model["height_slope"]
            intercept = model["height_intercept"]
            r_squared = model["height_r_squared"]

            # Plot scatter points
            plt.scatter(x, y, color=colors[i], alpha=0.6, s=30)

            # Plot regression line
            x_line = np.array([float(min(x)), float(max(x))])
            y_line = slope * x_line + intercept
            plt.plot(x_line, y_line, color=colors[i], linewidth=2)

            # Add to legend
            legend_handles.append(mpatches.Patch(
                color=colors[i],
                label=f"{format_technique_name(technique)}: y={slope:.4f}x{'+' if intercept >= 0 else ''}{intercept:.4f}, R²={r_squared:.4f}"
            ))
        except Exception as e:
            print(f"Error plotting height for {technique if not hasattr(technique, 'value') else technique.value}: {str(e)}")

    if legend_handles:
        # Add ideal line (y=x)
        try:
            max_val = float(max(max(df["p-touch_height"].max(), df[df.filter(like="_height").columns].max().max())))
            plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.3, label="y=x")
        except:
            # If there's an error with the max calculation, just use a reasonable default
            plt.plot([0, 50], [0, 50], 'k--', alpha=0.3, label="y=x")

        plt.xlabel("Calculated Height (pts)")
        plt.ylabel("P-Touch Reference Height (pts)")
        plt.title("Linear Regression: Calculated vs. P-Touch Reference Height")
        plt.grid(alpha=0.3)
        plt.axis('equal')
        plt.legend(handles=legend_handles, loc="upper left", fontsize=8)
        plt.tight_layout()
        plt.savefig("plots/height_regression.png")
    else:
        print("No valid data for height regression plot")

    return

def generate_regression_report(regression_models: Dict[str, Dict[str, Any]], available_techniques: List[str]) -> str:
    """
    Generate a markdown report of the regression analysis results.
    """
    md = []
    md.append("# Linear Regression Models for Text Dimension Adjustments")
    md.append("\nThis report shows linear models (y = mx + b) for converting calculated dimensions to P-Touch reference dimensions.")
    md.append("\n## Width Models")
    md.append("\n```")
    md.append("| Technique | Model Formula | R² | Mean Abs Error | MAPE (%) |")
    md.append("|-----------|---------------|----:|---------------:|--------:|")

    # Ensure we display techniques in the order defined in TECHNIQUES
    for technique in TECHNIQUES:
        if technique not in available_techniques or technique not in regression_models:
            continue

        model = regression_models[technique]
        tech_name = format_technique_name(technique)
        slope = model["width_slope"]
        intercept = model["width_intercept"]
        r_squared = model["width_r_squared"]
        mean_error = model["width_mean_error"]
        mape = model["width_mape"]

        sign = "+" if intercept >= 0 else ""
        md.append(f"| {tech_name} | y = {slope:.4f}x{sign}{intercept:.4f} | {r_squared:.4f} | {mean_error:.4f} | {mape:.2f} |")

    md.append("```")

    md.append("\n## Height Models")
    md.append("\n```")
    md.append("| Technique | Model Formula | R² | Mean Abs Error | MAPE (%) |")
    md.append("|-----------|---------------|----:|---------------:|--------:|")

    # Ensure we display techniques in the order defined in TECHNIQUES
    for technique in TECHNIQUES:
        if technique not in available_techniques or technique not in regression_models:
            continue

        model = regression_models[technique]
        tech_name = format_technique_name(technique)
        slope = model["height_slope"]
        intercept = model["height_intercept"]
        r_squared = model["height_r_squared"]
        mean_error = model["height_mean_error"]
        mape = model["height_mape"]

        sign = "+" if intercept >= 0 else ""
        md.append(f"| {tech_name} | y = {slope:.4f}x{sign}{intercept:.4f} | {r_squared:.4f} | {mean_error:.4f} | {mape:.2f} |")

    md.append("```")

    md.append("\n## Interpretation")
    md.append("\n- **Model Formula**: Use `pte_dimension = slope * calculated_dimension + intercept`")
    md.append("- **R²**: Coefficient of determination - how well the model fits the data (higher is better, 1.0 is perfect)")
    md.append("- **Mean Abs Error**: Average absolute error in points")
    md.append("- **MAPE**: Mean Absolute Percentage Error")

    md.append("\n## Recommended Implementation")
    md.append("\nBased on these results, to adjust calculated dimensions to match P-Touch Editor:")

    # Find the best model for width and height based on R²
    best_width_technique = max(
        [t for t in available_techniques if t in regression_models],
        key=lambda t: regression_models[t]["width_r_squared"]
    )
    best_height_technique = max(
        [t for t in available_techniques if t in regression_models],
        key=lambda t: regression_models[t]["height_r_squared"]
    )

    best_width_model = regression_models[best_width_technique]
    best_height_model = regression_models[best_height_technique]

    md.append(f"\n### Best Width Model: {format_technique_name(best_width_technique)}")
    md.append(f"```python")
    md.append(f"adjusted_width = {best_width_model['width_slope']:.6f} * calculated_width + {best_width_model['width_intercept']:.6f}")
    md.append(f"```")

    md.append(f"\n### Best Height Model: {format_technique_name(best_height_technique)}")
    md.append(f"```python")
    md.append(f"adjusted_height = {best_height_model['height_slope']:.6f} * calculated_height + {best_height_model['height_intercept']:.6f}")
    md.append(f"```")

    return "\n".join(md)

def analyze_character_spacing(calculator, technique, reference_data=None):
    """
    Analyze different inter-character spacing values to find the optimal value.

    Args:
        calculator: TextDimensionCalculator instance
        technique: The calculation method to use
        reference_data: Optional list of reference data points (uses PTOUCH_REFERENCE_DATA if None)

    Returns:
        Dictionary with statistics about optimal spacing values
    """
    if reference_data is None:
        reference_data = PTOUCH_REFERENCE_DATA

    # Create spacing values to test
    spacing_values = [round(SPACING_MIN + i * SPACING_STEP, 1) for i in range(int((SPACING_MAX - SPACING_MIN) / SPACING_STEP) + 1)]

    # Data structures to store results
    spacing_errors = {spacing: {'widths': [], 'width_error': 0, 'abs_width_error': 0} for spacing in spacing_values}

    # Test each reference data point with each spacing value
    for ref_data in reference_data:
        text = ref_data["text"]
        font_name = ref_data["font_name"]
        size = ref_data["size"]
        weight = ref_data["weight"]
        italic = ref_data["italic"]
        ref_width = ref_data["width"]

        # Only process text with more than one character (inter-character spacing doesn't affect single chars)
        if len(text) <= 1:
            continue

        for spacing in spacing_values:
            try:
                # Calculate with specified spacing value but without other adjustments
                # This lets us isolate the effect of just the inter-character spacing
                calc_width, _ = calculator.calculate_text_dimensions(
                    text=text,
                    font_name=font_name,
                    size=size,
                    weight=weight,
                    italic=italic,
                    method=technique,
                    apply_adjustments=False,
                    inter_character_spacing=spacing
                )

                # Calculate percentage error
                diff_pct = ((calc_width - ref_width) / ref_width) * 100

                # Store the results
                spacing_errors[spacing]['widths'].append(diff_pct)

            except Exception as e:
                # Skip if calculation fails
                continue

    # Calculate average error for each spacing value
    for spacing, data in spacing_errors.items():
        if data['widths']:
            data['width_error'] = sum(data['widths']) / len(data['widths'])
            data['abs_width_error'] = sum(abs(d) for d in data['widths']) / len(data['widths'])

    # Find the spacing value with the lowest absolute error
    best_spacing = min(spacing_values, key=lambda s: spacing_errors[s]['abs_width_error']
                       if spacing_errors[s]['widths'] else float('inf'))

    # Group by font and find best spacing for each font
    font_specific = {}
    for ref_data in reference_data:
        if len(ref_data["text"]) <= 1:
            continue

        font_name = ref_data["font_name"]
        if font_name not in font_specific:
            font_specific[font_name] = {spacing: {'widths': [], 'width_error': 0, 'abs_width_error': 0}
                                       for spacing in spacing_values}

    for ref_data in reference_data:
        if len(ref_data["text"]) <= 1:
            continue

        text = ref_data["text"]
        font_name = ref_data["font_name"]
        size = ref_data["size"]
        weight = ref_data["weight"]
        italic = ref_data["italic"]
        ref_width = ref_data["width"]

        for spacing in spacing_values:
            try:
                calc_width, _ = calculator.calculate_text_dimensions(
                    text=text,
                    font_name=font_name,
                    size=size,
                    weight=weight,
                    italic=italic,
                    method=technique,
                    apply_adjustments=False,
                    inter_character_spacing=spacing
                )

                diff_pct = ((calc_width - ref_width) / ref_width) * 100
                font_specific[font_name][spacing]['widths'].append(diff_pct)

            except Exception:
                continue

    # Calculate average errors for each font
    font_best_spacing = {}
    for font_name, spacing_data in font_specific.items():
        for spacing, data in spacing_data.items():
            if data['widths']:
                data['width_error'] = sum(data['widths']) / len(data['widths'])
                data['abs_width_error'] = sum(abs(d) for d in data['widths']) / len(data['widths'])

        # Find best spacing for this font
        best_font_spacing = min(spacing_values, key=lambda s: font_specific[font_name][s]['abs_width_error']
                               if font_specific[font_name][s]['widths'] else float('inf'))

        font_best_spacing[font_name] = {
            'best_spacing': best_font_spacing,
            'error': font_specific[font_name][best_font_spacing]['width_error'],
            'abs_error': font_specific[font_name][best_font_spacing]['abs_width_error']
        }

    # Check if spacing should scale with font size
    # Group by font size and find best spacing for each size
    size_specific = {}
    for ref_data in reference_data:
        if len(ref_data["text"]) <= 1:
            continue

        size = ref_data["size"]
        if size not in size_specific:
            size_specific[size] = {spacing: {'widths': [], 'width_error': 0, 'abs_width_error': 0}
                                  for spacing in spacing_values}

    for ref_data in reference_data:
        if len(ref_data["text"]) <= 1:
            continue

        text = ref_data["text"]
        font_name = ref_data["font_name"]
        size = ref_data["size"]
        weight = ref_data["weight"]
        italic = ref_data["italic"]
        ref_width = ref_data["width"]

        for spacing in spacing_values:
            try:
                calc_width, _ = calculator.calculate_text_dimensions(
                    text=text,
                    font_name=font_name,
                    size=size,
                    weight=weight,
                    italic=italic,
                    method=technique,
                    apply_adjustments=False,
                    inter_character_spacing=spacing
                )

                diff_pct = ((calc_width - ref_width) / ref_width) * 100
                size_specific[size][spacing]['widths'].append(diff_pct)

            except Exception:
                continue

    # Calculate average errors for each size
    size_best_spacing = {}
    for size, spacing_data in size_specific.items():
        for spacing, data in spacing_data.items():
            if data['widths']:
                data['width_error'] = sum(data['widths']) / len(data['widths'])
                data['abs_width_error'] = sum(abs(d) for d in data['widths']) / len(data['widths'])

        # Find best spacing for this size
        best_size_spacing = min(spacing_values, key=lambda s: size_specific[size][s]['abs_width_error']
                               if size_specific[size][s]['widths'] else float('inf'))

        size_best_spacing[size] = {
            'best_spacing': best_size_spacing,
            'error': size_specific[size][best_size_spacing]['width_error'],
            'abs_error': size_specific[size][best_size_spacing]['abs_width_error']
        }

    # Analyze if spacing scales with font size
    sizes = sorted(size_best_spacing.keys())
    spacings = [size_best_spacing[size]['best_spacing'] for size in sizes]

    # Check if there's a correlation between size and spacing
    # If spacings increase with size, it might indicate scaling is needed
    correlation = None
    slope = None
    if len(sizes) > 1:
        try:
            from scipy import stats
            correlation, p_value = stats.pearsonr(sizes, spacings)
            # Calculate linear regression to find the scaling formula
            slope, intercept, r_value, p_value, std_err = stats.linregress(sizes, spacings)
        except Exception:
            # If scipy isn't available, don't calculate correlation
            pass

    return {
        'best_spacing': best_spacing,
        'error': spacing_errors[best_spacing]['width_error'],
        'abs_error': spacing_errors[best_spacing]['abs_width_error'],
        'font_specific': font_best_spacing,
        'size_specific': size_best_spacing,
        'size_correlation': correlation,
        'size_slope': slope,
        'spacing_values': spacing_values,
        'spacing_errors': spacing_errors
    }

def plot_spacing_analysis(spacing_analysis, technique_name):
    """
    Create plots for inter-character spacing analysis.

    Args:
        spacing_analysis: Results from analyze_character_spacing()
        technique_name: Name of the technique used
    """
    import matplotlib.pyplot as plt

    # Create a plots directory if it doesn't exist
    os.makedirs("plots", exist_ok=True)

    # Plot spacing vs error
    plt.figure(figsize=(12, 8))

    spacing_values = spacing_analysis['spacing_values']
    errors = [spacing_analysis['spacing_errors'][s]['width_error'] for s in spacing_values]
    abs_errors = [spacing_analysis['spacing_errors'][s]['abs_width_error'] for s in spacing_values]

    plt.plot(spacing_values, errors, 'b-', label='Average Error (%)')
    plt.plot(spacing_values, abs_errors, 'r-', label='Mean Absolute Error (%)')

    # Mark the best spacing
    best_spacing = spacing_analysis['best_spacing']
    plt.axvline(x=best_spacing, color='g', linestyle='--', label=f'Best Value: {best_spacing}')

    # Mark the current default spacing
    plt.axvline(x=DEFAULT_SPACING, color='m', linestyle='--', label=f'Current Default: {DEFAULT_SPACING}')

    plt.xlabel('Inter-Character Spacing (points)')
    plt.ylabel('Width Error (%)')
    plt.title(f'Inter-Character Spacing Analysis - {technique_name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(f"plots/spacing_analysis_{technique_name.lower().replace(' ', '_')}.png")

    # Plot spacing by font
    plt.figure(figsize=(12, 8))

    fonts = list(spacing_analysis['font_specific'].keys())
    font_spacings = [spacing_analysis['font_specific'][f]['best_spacing'] for f in fonts]

    plt.bar(range(len(fonts)), font_spacings)
    plt.xticks(range(len(fonts)), fonts, rotation=45, ha='right')
    plt.axhline(y=best_spacing, color='g', linestyle='--', label=f'Overall Best: {best_spacing}')
    plt.axhline(y=DEFAULT_SPACING, color='m', linestyle='--', label=f'Current Default: {DEFAULT_SPACING}')

    plt.xlabel('Font')
    plt.ylabel('Optimal Spacing (points)')
    plt.title(f'Optimal Spacing by Font - {technique_name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"plots/font_spacing_{technique_name.lower().replace(' ', '_')}.png")

    # Plot spacing by font size if we have size-specific data
    if spacing_analysis['size_specific']:
        plt.figure(figsize=(12, 8))

        sizes = sorted(spacing_analysis['size_specific'].keys())
        size_spacings = [spacing_analysis['size_specific'][s]['best_spacing'] for s in sizes]

        plt.plot(sizes, size_spacings, 'bo-')

        # Add regression line if correlation was calculated
        if spacing_analysis['size_slope'] is not None:
            slope = spacing_analysis['size_slope']
            intercept = size_spacings[0] - slope * sizes[0]  # Calculate intercept

            # Plot regression line
            x_line = [min(sizes), max(sizes)]
            y_line = [slope * x + intercept for x in x_line]
            plt.plot(x_line, y_line, 'r-', label=f'y = {slope:.4f}x + {intercept:.4f}')

            # Add correlation info
            corr = spacing_analysis['size_correlation']
            if corr is not None:
                plt.text(0.05, 0.95, f'Correlation: {corr:.4f}', transform=plt.gca().transAxes,
                         bbox=dict(facecolor='white', alpha=0.7))

        plt.axhline(y=best_spacing, color='g', linestyle='--', label=f'Overall Best: {best_spacing}')
        plt.axhline(y=DEFAULT_SPACING, color='m', linestyle='--', label=f'Current Default: {DEFAULT_SPACING}')

        plt.xlabel('Font Size (points)')
        plt.ylabel('Optimal Spacing (points)')
        plt.title(f'Optimal Spacing by Font Size - {technique_name}')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.savefig(f"plots/size_spacing_{technique_name.lower().replace(' ', '_')}.png")

def generate_spacing_report(spacing_analysis, technique_name):
    """
    Generate a markdown report for inter-character spacing analysis.

    Args:
        spacing_analysis: Results from analyze_character_spacing()
        technique_name: Name of the technique used

    Returns:
        Markdown formatted report as a string
    """
    md = []

    # Title and introduction
    md.append(f"# Inter-Character Spacing Analysis - {technique_name}")
    md.append("\nThis report analyzes the optimal inter-character spacing values to match P-touch Editor reference dimensions.")

    # Overall best spacing
    best_spacing = spacing_analysis['best_spacing']
    error = spacing_analysis['error']
    abs_error = spacing_analysis['abs_error']

    md.append("\n## Overall Best Spacing")
    md.append(f"\n- **Optimal spacing**: {best_spacing:.1f} points")
    md.append(f"- **Average error**: {error:.2f}%")
    md.append(f"- **Mean absolute error**: {abs_error:.2f}%")
    md.append(f"- **Current default**: {DEFAULT_SPACING} points")

    # Font-specific spacing values
    md.append("\n## Font-Specific Optimal Spacing")
    md.append("\n| Font | Optimal Spacing | Error (%) | Abs Error (%) |")
    md.append("| --- | --- | --- | --- |")

    for font, data in sorted(spacing_analysis['font_specific'].items()):
        md.append(f"| {font} | {data['best_spacing']:.1f} | {data['error']:.2f}% | {data['abs_error']:.2f}% |")

    # Size-specific spacing values
    md.append("\n## Size-Specific Optimal Spacing")
    md.append("\n| Font Size | Optimal Spacing | Error (%) | Abs Error (%) |")
    md.append("| --- | --- | --- | --- |")

    for size, data in sorted(spacing_analysis['size_specific'].items()):
        md.append(f"| {size:.1f} | {data['best_spacing']:.1f} | {data['error']:.2f}% | {data['abs_error']:.2f}% |")

    # Correlation with font size
    md.append("\n## Relationship with Font Size")

    if spacing_analysis['size_correlation'] is not None:
        correlation = spacing_analysis['size_correlation']
        slope = spacing_analysis['size_slope']

        md.append(f"\n- **Correlation coefficient**: {correlation:.4f}")

        if abs(correlation) > 0.7:
            md.append("- **Interpretation**: Strong correlation between font size and optimal spacing")
            md.append("\n### Scaling Formula")

            if slope is not None:
                # Calculate intercept
                sizes = sorted(spacing_analysis['size_specific'].keys())
                size_spacings = [spacing_analysis['size_specific'][s]['best_spacing'] for s in sizes]
                intercept = size_spacings[0] - slope * sizes[0]

                md.append(f"\n```python")
                md.append(f"inter_character_spacing = {slope:.6f} * font_size + {intercept:.6f}")
                md.append(f"```")

                md.append("\nThis formula can be used to automatically adjust inter-character spacing based on font size.")
        elif abs(correlation) > 0.3:
            md.append("- **Interpretation**: Moderate correlation between font size and optimal spacing")
        else:
            md.append("- **Interpretation**: Weak or no correlation between font size and optimal spacing")
            md.append("\nA fixed spacing value is likely sufficient for all font sizes.")
    else:
        md.append("\nCorrelation analysis not available.")

    # Recommendations
    md.append("\n## Recommendations")

    if abs(spacing_analysis.get('size_correlation', 0) or 0) > 0.7:
        md.append("\nBased on the analysis, we recommend implementing a dynamic inter-character spacing that scales with font size:")

        sizes = sorted(spacing_analysis['size_specific'].keys())
        size_spacings = [spacing_analysis['size_specific'][s]['best_spacing'] for s in sizes]
        slope = spacing_analysis['size_slope']
        intercept = size_spacings[0] - slope * sizes[0]

        md.append(f"\n```python")
        md.append(f"inter_character_spacing = {slope:.6f} * font_size + {intercept:.6f}")
        md.append(f"```")
    else:
        if abs(best_spacing - DEFAULT_SPACING) < 0.2:
            md.append(f"\nThe current default spacing of {DEFAULT_SPACING} points is very close to the optimal value of {best_spacing:.1f} points.")
            md.append("\nNo change is recommended at this time.")
        else:
            md.append(f"\nBased on the analysis, we recommend changing the default inter-character spacing from {DEFAULT_SPACING} to {best_spacing:.1f} points.")
            md.append("\nThis should improve text width accuracy by reducing the average error.")

    # Add references to plots
    md.append("\n## Visualizations")
    md.append(f"\n![Spacing Analysis](plots/spacing_analysis_{technique_name.lower().replace(' ', '_')}.png)")
    md.append(f"\n![Font-Specific Spacing](plots/font_spacing_{technique_name.lower().replace(' ', '_')}.png)")

    if spacing_analysis['size_specific']:
        md.append(f"\n![Size-Specific Spacing](plots/size_spacing_{technique_name.lower().replace(' ', '_')}.png)")

    return "\n".join(md)

def run_comparison_with_adjustments(calculator):
    """
    Run a simplified comparison with adjustments applied to see how well they work.
    """
    # Check which techniques are available
    available_techniques = []
    for technique in TECHNIQUES:
        try:
            if calculator._techniques[technique].is_available():
                available_techniques.append(technique)
        except KeyError:
            pass

    if not available_techniques:
        print("No calculation techniques available. Exiting.")
        return

    print(f"\nComparing {len(PTOUCH_REFERENCE_DATA)} reference data points with adjustments applied...")

    # Create data structures to store results
    technique_stats = {t: {"width_diffs": [], "height_diffs": []} for t in available_techniques}

    # Test each reference data point with each available technique
    for i, ref_data in enumerate(PTOUCH_REFERENCE_DATA):
        text = ref_data["text"]
        font_name = ref_data["font_name"]
        size = ref_data["size"]
        weight = ref_data["weight"]
        italic = ref_data["italic"]

        ref_width = ref_data["width"]
        ref_height = ref_data["height"]

        # Calculate dimensions using each technique with adjustments
        for technique in available_techniques:
            try:
                # Calculate with adjustments applied
                calc_width, calc_height = calculator.calculate_text_dimensions(
                    text=text,
                    font_name=font_name,
                    size=size,
                    weight=weight,
                    italic=italic,
                    method=technique,
                    apply_adjustments=True
                )

                # Calculate differences
                width_diff = calc_width - ref_width
                height_diff = calc_height - ref_height

                width_diff_pct = (width_diff / ref_width) * 100 if ref_width != 0 else float('nan')
                height_diff_pct = (height_diff / ref_height) * 100 if ref_height != 0 else float('nan')

                # Store for statistics
                technique_stats[technique]["width_diffs"].append(width_diff_pct)
                technique_stats[technique]["height_diffs"].append(height_diff_pct)
            except Exception as e:
                # Skip if calculation fails
                pass

        # Print progress
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(PTOUCH_REFERENCE_DATA)} samples...")

    # Calculate summary statistics for each technique
    summary_stats = []

    for technique in TECHNIQUES:
        if technique not in available_techniques:
            continue

        tech_name = format_technique_name(technique)
        width_diffs = technique_stats[technique]["width_diffs"]
        height_diffs = technique_stats[technique]["height_diffs"]

        # Filter out NaN values
        width_diffs = [d for d in width_diffs if not np.isnan(d)]
        height_diffs = [d for d in height_diffs if not np.isnan(d)]

        if width_diffs and height_diffs:
            avg_width_diff = sum(width_diffs) / len(width_diffs)
            avg_height_diff = sum(height_diffs) / len(height_diffs)

            median_width_diff = sorted(width_diffs)[len(width_diffs) // 2]
            median_height_diff = sorted(height_diffs)[len(height_diffs) // 2]

            std_width_diff = (sum((d - avg_width_diff) ** 2 for d in width_diffs) / len(width_diffs)) ** 0.5
            std_height_diff = (sum((d - avg_height_diff) ** 2 for d in height_diffs) / len(height_diffs)) ** 0.5

            # Mean absolute percentage error
            abs_width_diff = sum(abs(d) for d in width_diffs) / len(width_diffs)
            abs_height_diff = sum(abs(d) for d in height_diffs) / len(height_diffs)

            summary_stats.append({
                "Technique": tech_name,
                "Avg Width Diff (%)": f"{avg_width_diff:+.1f}%",
                "Avg Height Diff (%)": f"{avg_height_diff:+.1f}%",
                "Median Width Diff (%)": f"{median_width_diff:+.1f}%",
                "Median Height Diff (%)": f"{median_height_diff:+.1f}%",
                "MAPE Width (%)": f"{abs_width_diff:.1f}%",
                "MAPE Height (%)": f"{abs_height_diff:.1f}%",
                "Std Width Diff (%)": f"{std_width_diff:.1f}%",
                "Std Height Diff (%)": f"{std_height_diff:.1f}%",
            })

    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS WITH LINEAR ADJUSTMENTS APPLIED")
    print("=" * 80)
    print(tabulate(summary_stats, headers="keys", tablefmt="grid"))

    return summary_stats

def compare_spacing_values_directly(technique=CalculationMethod.SKIA):
    """
    Directly compare different inter-character spacing values against reference data.
    """
    print("\n================================================================================")
    print("DIRECT COMPARISON OF INTER-CHARACTER SPACING VALUES")
    print("================================================================================")

    # Spacing values to test
    spacing_values = [0.0, 0.5, 1.0, 1.3, 1.5, 2.0, 2.5, 3.0]

    # Create calculators with different spacing values
    calculators = {
        spacing: TextDimensionCalculator(
            debug=False,
            allow_fallbacks=True,
            allow_font_substitution=True,
            allow_approximation=True,
            apply_ptouch_adjustments=False,
            apply_technique_adjustments=False,
            inter_character_spacing=spacing
        ) for spacing in spacing_values
    }

    # Data structure to store results
    results = []

    # Process each reference data point
    for ref_data in PTOUCH_REFERENCE_DATA:
        text = ref_data["text"]
        font_name = ref_data["font_name"]
        size = ref_data["size"]
        weight = ref_data["weight"]
        italic = ref_data["italic"]
        ref_width = ref_data["width"]
        ref_height = ref_data["height"]

        # Skip single characters as spacing doesn't affect them
        if len(text) <= 1:
            continue

        row_data = {
            "text": text,
            "font_name": font_name,
            "size": size,
            "weight": weight,
            "p-touch_width": ref_width,
        }

        # Calculate with each spacing value
        for spacing in spacing_values:
            try:
                calc_width, _ = calculators[spacing].calculate_text_dimensions(
                    text=text,
                    font_name=font_name,
                    size=size,
                    weight=weight,
                    italic=italic,
                    method=technique
                )

                # Calculate difference
                width_diff = calc_width - ref_width
                width_diff_pct = (width_diff / ref_width) * 100

                # Store results
                row_data[f"spacing_{spacing}_width"] = calc_width
                row_data[f"spacing_{spacing}_diff"] = width_diff
                row_data[f"spacing_{spacing}_diff_pct"] = width_diff_pct

            except Exception as e:
                row_data[f"spacing_{spacing}_width"] = None
                row_data[f"spacing_{spacing}_diff"] = None
                row_data[f"spacing_{spacing}_diff_pct"] = None

        results.append(row_data)

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Print summary statistics for each spacing value
    summary_stats = []
    for spacing in spacing_values:
        diff_col = f"spacing_{spacing}_diff_pct"
        if diff_col in df.columns:
            diff_values = df[diff_col].dropna().values

            if len(diff_values) > 0:
                avg_diff = float(np.mean(diff_values))
                median_diff = float(np.median(diff_values))
                abs_diff = float(np.mean(np.abs(diff_values)))
                std_diff = float(np.std(diff_values))

                summary_stats.append({
                    "Spacing": f"{spacing:.1f}pt",
                    "Avg Width Diff (%)": f"{avg_diff:+.1f}%",
                    "Median Width Diff (%)": f"{median_diff:+.1f}%",
                    "MAPE Width (%)": f"{abs_diff:.1f}%",
                    "Std Width Diff (%)": f"{std_diff:.1f}%",
                })

    print("\n" + "=" * 80)
    print("COMPARISON OF INTER-CHARACTER SPACING VALUES")
    print("=" * 80)
    print(tabulate(summary_stats, headers="keys", tablefmt="grid"))

    # Generate visualization
    try:
        import matplotlib.pyplot as plt

        # Create a directory for plots if it doesn't exist
        os.makedirs("plots", exist_ok=True)

        # Extract data for plotting
        plot_data = {
            spacing: df[f"spacing_{spacing}_diff_pct"].dropna().values
            for spacing in spacing_values
            if f"spacing_{spacing}_diff_pct" in df.columns and len(df[f"spacing_{spacing}_diff_pct"].dropna()) > 0
        }

        # Create boxplot
        plt.figure(figsize=(12, 6))
        plt.boxplot(list(plot_data.values()), labels=[f"{s:.1f}pt" for s in plot_data.keys()])

        plt.axhline(y=0, color='k', linestyle='--', alpha=0.3)
        plt.title("Width Difference by Inter-Character Spacing")
        plt.xlabel("Inter-Character Spacing")
        plt.ylabel("Width Difference (%)")
        plt.grid(axis="y", alpha=0.3)
        plt.savefig("plots/spacing_comparison_boxplot.png")

        # Create scatter plot of actual vs calculated widths for each spacing
        plt.figure(figsize=(14, 10))

        for i, spacing in enumerate(spacing_values):
            width_col = f"spacing_{spacing}_width"
            if width_col in df.columns:
                valid_data = df[~df[width_col].isna()]
                if len(valid_data) > 0:
                    plt.subplot(2, 4, i+1)
                    plt.scatter(valid_data["p-touch_width"], valid_data[width_col], alpha=0.7)

                    # Add diagonal reference line
                    max_val = max(valid_data["p-touch_width"].max(), valid_data[width_col].max())
                    plt.plot([0, max_val], [0, max_val], 'k--', alpha=0.3)

                    plt.title(f"Spacing: {spacing:.1f}pt")
                    plt.xlabel("P-touch Width (pt)")
                    plt.ylabel("Calculated Width (pt)")
                    plt.grid(alpha=0.3)

        plt.tight_layout()
        plt.savefig("plots/spacing_scatter_comparison.png")

        print("Created spacing comparison visualizations.")
    except Exception as e:
        print(f"Error creating plots: {str(e)}")

    # Save detailed results
    csv_path = "spacing_comparison_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"Detailed results saved to: {csv_path}")

    return df, summary_stats

def compare_dynamic_vs_fixed_spacing(technique=CalculationMethod.SKIA):
    """
    Compare the accuracy of dynamic spacing vs fixed spacing against reference data.
    """
    print("\n================================================================================")
    print("COMPARISON OF DYNAMIC VS FIXED SPACING")
    print("================================================================================")

    # Create calculator
    calculator = TextDimensionCalculator(
        debug=False,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True,
        apply_ptouch_adjustments=False,
        apply_technique_adjustments=False,
        inter_character_spacing=0.1  # default spacing
    )

    # Initialize data structures
    fixed_errors = []
    dynamic_errors = []
    size_groups = defaultdict(lambda: {'fixed': [], 'dynamic': []})
    font_groups = defaultdict(lambda: {'fixed': [], 'dynamic': []})

    # Process each reference data point
    for ref_data in PTOUCH_REFERENCE_DATA:
        text = ref_data["text"]
        font_name = ref_data["font_name"]
        size = ref_data["size"]
        weight = ref_data["weight"]
        italic = ref_data["italic"]
        ref_width = ref_data["width"]

        # Skip single characters
        if len(text) <= 1:
            continue

        try:
            # Calculate with fixed spacing
            fixed_width, _ = calculator.calculate_text_dimensions(
                text=text,
                font_name=font_name,
                size=size,
                weight=weight,
                italic=italic,
                method=technique,
                apply_adjustments=False,
                inter_character_spacing=DEFAULT_SPACING,
                use_dynamic_spacing=False
            )

            # Calculate with dynamic spacing
            dynamic_width, _ = calculator.calculate_text_dimensions(
                text=text,
                font_name=font_name,
                size=size,
                weight=weight,
                italic=italic,
                method=technique,
                apply_adjustments=False,
                use_dynamic_spacing=True
            )

            # Calculate percentage errors
            fixed_error = ((fixed_width - ref_width) / ref_width) * 100
            dynamic_error = ((dynamic_width - ref_width) / ref_width) * 100

            # Store results
            fixed_errors.append(fixed_error)
            dynamic_errors.append(dynamic_error)

            # Group by font size
            size_groups[size]['fixed'].append(fixed_error)
            size_groups[size]['dynamic'].append(dynamic_error)

            # Group by font
            font_groups[font_name]['fixed'].append(fixed_error)
            font_groups[font_name]['dynamic'].append(dynamic_error)

        except Exception as e:
            if DEBUG:
                print(f"Error calculating dimensions: {str(e)}")
            continue

    # Calculate overall statistics
    fixed_abs_errors = [abs(e) for e in fixed_errors]
    dynamic_abs_errors = [abs(e) for e in dynamic_errors]

    fixed_mean = sum(fixed_errors) / len(fixed_errors) if fixed_errors else 0
    dynamic_mean = sum(dynamic_errors) / len(dynamic_errors) if dynamic_errors else 0

    fixed_mape = sum(fixed_abs_errors) / len(fixed_abs_errors) if fixed_abs_errors else 0
    dynamic_mape = sum(dynamic_abs_errors) / len(dynamic_abs_errors) if dynamic_abs_errors else 0

    fixed_median = sorted(fixed_errors)[len(fixed_errors)//2] if fixed_errors else 0
    dynamic_median = sorted(dynamic_errors)[len(dynamic_errors)//2] if dynamic_errors else 0

    fixed_std = (sum((e - fixed_mean)**2 for e in fixed_errors) / len(fixed_errors))**0.5 if fixed_errors else 0
    dynamic_std = (sum((e - dynamic_mean)**2 for e in dynamic_errors) / len(dynamic_errors))**0.5 if dynamic_errors else 0

    # Print overall results
    print("\nOVERALL RESULTS:")
    print(f"{'Metric':<24} {'Fixed Spacing':<16} {'Dynamic Spacing':<16} {'Improvement':<16}")
    print(f"{'-'*24} {'-'*16} {'-'*16} {'-'*16}")
    print(f"{'Average Error':<24} {fixed_mean:+.2f}% {dynamic_mean:+.2f}% {abs(fixed_mean) - abs(dynamic_mean):+.2f}%")
    print(f"{'Median Error':<24} {fixed_median:+.2f}% {dynamic_median:+.2f}% {abs(fixed_median) - abs(dynamic_median):+.2f}%")
    print(f"{'Mean Absolute Error':<24} {fixed_mape:.2f}% {dynamic_mape:.2f}% {fixed_mape - dynamic_mape:+.2f}%")
    print(f"{'Standard Deviation':<24} {fixed_std:.2f}% {dynamic_std:.2f}% {fixed_std - dynamic_std:+.2f}%")

    # Print results by font size
    print("\nRESULTS BY FONT SIZE:")
    print(f"{'Font Size':<12} {'Fixed MAPE':<16} {'Dynamic MAPE':<16} {'Improvement':<16}")
    print(f"{'-'*12} {'-'*16} {'-'*16} {'-'*16}")

    for size in sorted(size_groups.keys()):
        fixed_size_mape = sum(abs(e) for e in size_groups[size]['fixed']) / len(size_groups[size]['fixed']) if size_groups[size]['fixed'] else 0
        dynamic_size_mape = sum(abs(e) for e in size_groups[size]['dynamic']) / len(size_groups[size]['dynamic']) if size_groups[size]['dynamic'] else 0
        improvement = fixed_size_mape - dynamic_size_mape

        print(f"{size:<12.1f} {fixed_size_mape:<16.2f}% {dynamic_size_mape:<16.2f}% {improvement:+16.2f}%")

    # Print results by font
    print("\nRESULTS BY FONT:")
    print(f"{'Font':<16} {'Fixed MAPE':<16} {'Dynamic MAPE':<16} {'Improvement':<16}")
    print(f"{'-'*16} {'-'*16} {'-'*16} {'-'*16}")

    for font in sorted(font_groups.keys()):
        fixed_font_mape = sum(abs(e) for e in font_groups[font]['fixed']) / len(font_groups[font]['fixed']) if font_groups[font]['fixed'] else 0
        dynamic_font_mape = sum(abs(e) for e in font_groups[font]['dynamic']) / len(font_groups[font]['dynamic']) if font_groups[font]['dynamic'] else 0
        improvement = fixed_font_mape - dynamic_font_mape

        print(f"{font:<16} {fixed_font_mape:<16.2f}% {dynamic_font_mape:<16.2f}% {improvement:+16.2f}%")

    # Create visualization
    try:
        plt.figure(figsize=(12, 8))

        # Create grouped bar chart
        sizes = sorted(size_groups.keys())
        x = np.arange(len(sizes))
        width = 0.35

        fixed_means = [sum(abs(e) for e in size_groups[size]['fixed']) / len(size_groups[size]['fixed']) if size_groups[size]['fixed'] else 0 for size in sizes]
        dynamic_means = [sum(abs(e) for e in size_groups[size]['dynamic']) / len(size_groups[size]['dynamic']) if size_groups[size]['dynamic'] else 0 for size in sizes]

        plt.bar(x - width/2, fixed_means, width, label='Fixed Spacing', color='blue', alpha=0.7)
        plt.bar(x + width/2, dynamic_means, width, label='Dynamic Spacing', color='green', alpha=0.7)

        plt.xlabel('Font Size (points)')
        plt.ylabel('Mean Absolute Error (%)')
        plt.title('Fixed vs Dynamic Spacing by Font Size')
        plt.xticks(x, [f"{size:.1f}pt" for size in sizes])
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig("plots/dynamic_vs_fixed_spacing.png")

        # Show overall comparison
        plt.figure(figsize=(10, 6))
        labels = ['Average Error', 'Median Error', 'Mean Absolute Error', 'Standard Deviation']
        fixed_values = [abs(fixed_mean), abs(fixed_median), fixed_mape, fixed_std]
        dynamic_values = [abs(dynamic_mean), abs(dynamic_median), dynamic_mape, dynamic_std]

        x = np.arange(len(labels))
        width = 0.35

        plt.bar(x - width/2, fixed_values, width, label='Fixed Spacing', color='blue', alpha=0.7)
        plt.bar(x + width/2, dynamic_values, width, label='Dynamic Spacing', color='green', alpha=0.7)

        plt.xlabel('Metric')
        plt.ylabel('Error (%)')
        plt.title('Fixed vs Dynamic Spacing - Overall Comparison')
        plt.xticks(x, labels)
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig("plots/dynamic_vs_fixed_overall.png")

        print("\nVisualizations saved to plots directory.")

    except Exception as e:
        print(f"Error creating visualization: {str(e)}")

    # Return overall comparison
    return {
        'fixed': {
            'mean': fixed_mean,
            'median': fixed_median,
            'mape': fixed_mape,
            'std': fixed_std
        },
        'dynamic': {
            'mean': dynamic_mean,
            'median': dynamic_median,
            'mape': dynamic_mape,
            'std': dynamic_std
        },
        'improvement': {
            'mean': abs(fixed_mean) - abs(dynamic_mean),
            'median': abs(fixed_median) - abs(dynamic_median),
            'mape': fixed_mape - dynamic_mape,
            'std': fixed_std - dynamic_std
        }
    }

def main():
    """
    Main function to run the comparison script.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Compare text dimension calculation techniques')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    parser.add_argument('--no-spacing-analysis', action='store_true', help='Skip spacing analysis')
    parser.add_argument('--no-report', action='store_true', help='Skip report generation')
    parser.add_argument('--no-plots', action='store_true', help='Skip plot generation')
    parser.add_argument('--dynamic-spacing', action='store_true', help='Compare dynamic vs fixed spacing')

    args = parser.parse_args()

    # Enable DEBUG output
    global DEBUG
    DEBUG = args.debug

    # Create calculator without adjustments - we want to compare the raw calculations
    # and calculate our own adjustment factors
    calculator = TextDimensionCalculator(
        debug=DEBUG,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True,
        apply_ptouch_adjustments=False,  # No adjustments
        apply_technique_adjustments=False,  # No adjustments
        use_linear_adjustments=True,
        inter_character_spacing=0.0  # Start with no spacing to analyze the effect
    )

    # If dynamic spacing comparison requested, run that first
    if args.dynamic_spacing:
        print("\nComparing dynamic vs fixed spacing...")
        compare_dynamic_vs_fixed_spacing(CalculationMethod.SKIA)

    # Run the comparison with raw calculations
    if not args.no_report:
        run_comparison_and_create_reports(calculator)

    # Analyze optimal inter-character spacing
    if not args.no_spacing_analysis:
        print("\n\n================================================================================")
        print("ANALYZING OPTIMAL INTER-CHARACTER SPACING")
        print("================================================================================")

        # Use the best technique available for this analysis (Skia if available)
        technique = CalculationMethod.SKIA

        # Check if Skia is available, otherwise try other techniques
        if not calculator._techniques[technique].is_available():
            for alt_technique in TECHNIQUES:
                if calculator._techniques[alt_technique].is_available():
                    technique = alt_technique
                    break

        technique_name = format_technique_name(technique)
        print(f"Using {technique_name} for inter-character spacing analysis...")

        # Run the spacing analysis
        spacing_analysis = analyze_character_spacing(calculator, technique)

        # Create visualization
        if not args.no_plots:
            try:
                plot_spacing_analysis(spacing_analysis, technique_name)
                print("Created spacing analysis visualizations.")
            except Exception as e:
                print(f"Error creating plots: {str(e)}")

        # Generate report
        if not args.no_report:
            spacing_report = generate_spacing_report(spacing_analysis, technique_name)

            # Save report
            spacing_report_path = "spacing_analysis.md"
            with open(spacing_report_path, "w") as f:
                f.write(spacing_report)

            print(f"Spacing analysis report saved to: {spacing_report_path}")

        # Run direct comparison of spacing values
        print("\n\n================================================================================")
        print("DIRECT COMPARISON OF INTER-CHARACTER SPACING VALUES")
        print("================================================================================")

        # Compare different spacing values
        compare_spacing_values_directly(technique)

        # Print summary of findings
        best_spacing = spacing_analysis['best_spacing']
        abs_error = spacing_analysis['abs_error']

        print(f"\nBest inter-character spacing: {best_spacing:.1f} points")
        print(f"Mean absolute error with this spacing: {abs_error:.2f}%")
        print(f"Current default is: {DEFAULT_SPACING} points")

        # Also run a comparison with linear adjustments to analyze how well they work
        print("\n\n================================================================================")
        print("COMPARISON WITH LINEAR ADJUSTMENTS APPLIED")
        print("================================================================================")

        # Create calculator with linear adjustments
        calculator_with_adjustments = TextDimensionCalculator(
            debug=DEBUG,
            allow_fallbacks=True,
            allow_font_substitution=True,
            allow_approximation=True,
            apply_ptouch_adjustments=False,
            apply_technique_adjustments=True,  # Apply adjustments
            use_linear_adjustments=True,
            inter_character_spacing=best_spacing  # Use the optimal spacing value we found
        )

        # Run a separate comparison with adjustments applied
        run_comparison_with_adjustments(calculator_with_adjustments)

        # Finally, test with both the optimal spacing and technique adjustments
        print("\n\n================================================================================")
        print(f"COMPARISON WITH OPTIMAL SPACING ({best_spacing:.1f}pt) AND LINEAR ADJUSTMENTS")
        print("================================================================================")

        # Create calculator with both optimal spacing and linear adjustments
        calculator_optimal = TextDimensionCalculator(
            debug=DEBUG,
            allow_fallbacks=True,
            allow_font_substitution=True,
            allow_approximation=True,
            apply_ptouch_adjustments=False,
            apply_technique_adjustments=True,  # Apply adjustments
            use_linear_adjustments=True,
            inter_character_spacing=best_spacing  # Use the optimal spacing value
        )

        # Run comparison
        run_comparison_with_adjustments(calculator_optimal)

        print(f"\nAnalysis complete. Use {best_spacing:.1f}pt for optimal inter-character spacing.")

def run_comparison_and_create_reports(calculator):
    """
    Run the original comparison and create reports.
    """
    # Check which techniques are available
    available_techniques = []
    for technique in TECHNIQUES:
        try:
            if calculator._techniques[technique].is_available():
                available_techniques.append(technique)
                print(f"✓ {format_technique_name(technique)}: Available")
            else:
                print(f"✗ {format_technique_name(technique)}: Not available")
        except KeyError:
            print(f"? {technique}: Unknown technique")

    if not available_techniques:
        print("No calculation techniques available. Exiting.")
        return

    print(f"\nComparing {len(PTOUCH_REFERENCE_DATA)} reference data points...")

    # Create data structures to store results
    results = []
    technique_stats = {t: {"width_diffs": [], "height_diffs": []} for t in available_techniques}

    # Test each reference data point with each available technique
    for i, ref_data in enumerate(PTOUCH_REFERENCE_DATA):
        text = ref_data["text"]
        font_name = ref_data["font_name"]
        size = ref_data["size"]
        weight = ref_data["weight"]
        italic = ref_data["italic"]

        ref_width = ref_data["width"]
        ref_height = ref_data["height"]

        row_data = {
            "text": text,
            "font_name": font_name,
            "size": size,
            "weight": weight,
            "italic": "Yes" if italic else "No",
            "p-touch_width": ref_width,
            "p-touch_height": ref_height
        }

        # Calculate dimensions using each technique
        for technique in available_techniques:
            calculated = calculate_with_technique(
                calculator, technique, text, font_name, size, weight, italic
            )

            if calculated:
                calc_width, calc_height = calculated
                width_diff, height_diff, width_diff_pct, height_diff_pct = compare_dimensions(
                    ref_data, calculated
                )

                # Store raw data
                row_data[f"{technique.value}_width"] = calc_width
                row_data[f"{technique.value}_height"] = calc_height
                row_data[f"{technique.value}_width_diff_pct"] = width_diff_pct
                row_data[f"{technique.value}_height_diff_pct"] = height_diff_pct

                # Store for statistics
                technique_stats[technique]["width_diffs"].append(width_diff_pct)
                technique_stats[technique]["height_diffs"].append(height_diff_pct)
            else:
                row_data[f"{technique.value}_width"] = None
                row_data[f"{technique.value}_height"] = None
                row_data[f"{technique.value}_width_diff_pct"] = None
                row_data[f"{technique.value}_height_diff_pct"] = None

        results.append(row_data)

        # Print progress
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(PTOUCH_REFERENCE_DATA)} samples...")

    # Convert to pandas DataFrame for easier analysis
    df = pd.DataFrame(results)

    # Calculate summary statistics for each technique
    summary_stats = []
    adjustment_factors = []

    for technique in TECHNIQUES:
        if technique not in available_techniques:
            continue

        tech_name = format_technique_name(technique)
        width_diffs = technique_stats[technique]["width_diffs"]
        height_diffs = technique_stats[technique]["height_diffs"]

        # Filter out NaN values
        width_diffs = [d for d in width_diffs if not np.isnan(d)]
        height_diffs = [d for d in height_diffs if not np.isnan(d)]

        if width_diffs and height_diffs:
            avg_width_diff = sum(width_diffs) / len(width_diffs)
            avg_height_diff = sum(height_diffs) / len(height_diffs)

            median_width_diff = sorted(width_diffs)[len(width_diffs) // 2]
            median_height_diff = sorted(height_diffs)[len(height_diffs) // 2]

            std_width_diff = (sum((d - avg_width_diff) ** 2 for d in width_diffs) / len(width_diffs)) ** 0.5
            std_height_diff = (sum((d - avg_height_diff) ** 2 for d in height_diffs) / len(height_diffs)) ** 0.5

            # Calculate suggested adjustment factors
            width_factor = 100 / (100 + avg_width_diff)
            height_factor = 100 / (100 + avg_height_diff)

            summary_stats.append({
                "Technique": tech_name,
                "Avg Width Diff (%)": f"{avg_width_diff:+.1f}%",
                "Avg Height Diff (%)": f"{avg_height_diff:+.1f}%",
                "Median Width Diff (%)": f"{median_width_diff:+.1f}%",
                "Median Height Diff (%)": f"{median_height_diff:+.1f}%",
                "Std Width Diff (%)": f"{std_width_diff:.1f}%",
                "Std Height Diff (%)": f"{std_height_diff:.1f}%",
            })

            adjustment_factors.append({
                "Technique": tech_name,
                "Width Factor": f"{width_factor:.4f}",
                "Height Factor": f"{height_factor:.4f}",
            })

    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print(tabulate(summary_stats, headers="keys", tablefmt="grid"))

    print("\n" + "=" * 80)
    print("SUGGESTED ADJUSTMENT FACTORS")
    print("=" * 80)
    print(tabulate(adjustment_factors, headers="keys", tablefmt="grid"))

    # Save detailed results to CSV
    csv_path = "technique_comparison_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nDetailed results saved to: {csv_path}")

    # Generate report for each font family separately
    font_families = sorted(set(item["font_name"] for item in PTOUCH_REFERENCE_DATA))

    print("\n" + "=" * 80)
    print("FONT-SPECIFIC STATISTICS")
    print("=" * 80)

    # Create a dictionary to store font-specific stats for markdown
    font_specific_stats = {}

    for font in font_families:
        print(f"\n--- {font} Font ---")
        font_data = df[df["font_name"] == font]

        font_stats = []
        for technique in TECHNIQUES:
            if technique not in available_techniques:
                continue

            tech_name = format_technique_name(technique)

            # Filter only data for this font and technique
            width_diffs = font_data[f"{technique.value}_width_diff_pct"].dropna().tolist()
            height_diffs = font_data[f"{technique.value}_height_diff_pct"].dropna().tolist()

            if width_diffs and height_diffs:
                avg_width_diff = sum(width_diffs) / len(width_diffs)
                avg_height_diff = sum(height_diffs) / len(height_diffs)

                # Calculate suggested adjustment factors for this font
                width_factor = 100 / (100 + avg_width_diff)
                height_factor = 100 / (100 + avg_height_diff)

                font_stats.append({
                    "Technique": tech_name,
                    "Avg Width Diff (%)": f"{avg_width_diff:+.1f}%",
                    "Avg Height Diff (%)": f"{avg_height_diff:+.1f}%",
                    "Width Factor": f"{width_factor:.4f}",
                    "Height Factor": f"{height_factor:.4f}",
                })

        # Store for markdown report
        font_specific_stats[font] = font_stats

        if font_stats:
            print(tabulate(font_stats, headers="keys", tablefmt="simple"))
        else:
            print("No data available for this font.")

    # Optional: Create visualizations
    try:
        # Create a directory for plots
        os.makedirs("plots", exist_ok=True)

        # Create box plots for width differences
        plt.figure(figsize=(12, 6))
        data = []
        labels = []

        # Ensure we display techniques in the order defined in TECHNIQUES
        for technique in TECHNIQUES:
            if technique not in available_techniques:
                continue

            tech_name = format_technique_name(technique)
            width_diffs = technique_stats[technique]["width_diffs"]
            width_diffs = [d for d in width_diffs if not np.isnan(d)]

            if width_diffs:
                data.append(width_diffs)
                labels.append(tech_name)

        if data:
            plt.boxplot(data, labels=labels)
            plt.title("Width Difference Percentages by Technique")
            plt.xlabel("Technique")
            plt.ylabel("Width Difference (%)")
            plt.grid(axis="y", alpha=0.3)
            plt.savefig("plots/width_diff_boxplot.png")

        # Create box plots for height differences
        plt.figure(figsize=(12, 6))
        data = []
        labels = []

        # Ensure we display techniques in the order defined in TECHNIQUES
        for technique in TECHNIQUES:
            if technique not in available_techniques:
                continue

            tech_name = format_technique_name(technique)
            height_diffs = technique_stats[technique]["height_diffs"]
            height_diffs = [d for d in height_diffs if not np.isnan(d)]

            if height_diffs:
                data.append(height_diffs)
                labels.append(tech_name)

        if data:
            plt.boxplot(data, labels=labels)
            plt.title("Height Difference Percentages by Technique")
            plt.xlabel("Technique")
            plt.ylabel("Height Difference (%)")
            plt.grid(axis="y", alpha=0.3)
            plt.savefig("plots/height_diff_boxplot.png")

        print("\nPlots generated in 'plots' directory.")
    except Exception as e:
        print(f"Error generating plots: {str(e)}")

    # Perform regression analysis
    try:
        print("\nPerforming regression analysis...")
        regression_models = calculate_regression_models(df, available_techniques)
        plot_regression_models(df, regression_models, available_techniques)

        # Generate regression report
        regression_report = generate_regression_report(regression_models, available_techniques)

        # Save regression report
        regression_md_path = "regression_models.md"
        with open(regression_md_path, "w") as f:
            f.write(regression_report)

        print(f"Regression analysis saved to: {regression_md_path}")
    except Exception as e:
        print(f"Error performing regression analysis: {str(e)}")

    # Generate markdown report
    markdown_report = generate_markdown_report(
        results_df=df,
        summary_stats=summary_stats,
        adjustment_factors=adjustment_factors,
        font_stats=font_specific_stats,
        available_techniques=available_techniques
    )

    # Save markdown report
    md_path = "comparison.md"
    with open(md_path, "w") as f:
        f.write(markdown_report)

    print(f"\nDetailed markdown report saved to: {md_path}")

    return df, available_techniques

if __name__ == "__main__":
    main()