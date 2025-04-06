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

def main():
    """
    Main function to run the comparison script.
    """
    # Create calculator without adjustments - we want to compare the raw calculations
    # and calculate our own adjustment factors
    calculator = TextDimensionCalculator(
        debug=False,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True,
        apply_ptouch_adjustments=False,  # No adjustments
        apply_technique_adjustments=False,  # No adjustments
        use_linear_adjustments=True
    )

    # Run the comparison with raw calculations
    run_comparison_and_create_reports(calculator)

    # Also run a comparison with linear adjustments to analyze how well they work
    print("\n\n================================================================================")
    print("COMPARISON WITH LINEAR ADJUSTMENTS APPLIED")
    print("================================================================================")

    # Create calculator with linear adjustments
    calculator_with_adjustments = TextDimensionCalculator(
        debug=False,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True,
        apply_ptouch_adjustments=False,
        apply_technique_adjustments=True,  # Apply adjustments
        use_linear_adjustments=True
    )

    # Run a separate comparison with adjustments applied
    run_comparison_with_adjustments(calculator_with_adjustments)

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