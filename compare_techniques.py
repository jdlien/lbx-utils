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
import platform

# Add the parent directory to the path to import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the necessary components
from src.lbx_utils.text_dimensions import (
    TextDimensionCalculator,
    CalculationMethod
)

# Import reference data from the test file
from tests.test_text_dimensions import PTOUCH_REFERENCE_DATA

# Set up constants
TECHNIQUES = [
    CalculationMethod.PANGO,
    CalculationMethod.HARFBUZZ,
    CalculationMethod.FREETYPE,
    CalculationMethod.PIL,
    CalculationMethod.APPROXIMATION
]

# Add Core Text technique if on macOS
if platform.system() == "Darwin" and hasattr(CalculationMethod, "CORE_TEXT"):
    TECHNIQUES.insert(0, CalculationMethod.CORE_TEXT)  # Add to the front for priority

def format_technique_name(technique: CalculationMethod) -> str:
    """Format technique name for display."""
    name = technique.value
    if name == "pil":
        return "PIL"
    return name.capitalize()

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

                    # Add rows for each technique
                    for technique in available_techniques:
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

def main():
    """Main function to run comparison."""
    # Create calculator without adjustments
    calculator = TextDimensionCalculator(
        debug=False,
        allow_fallbacks=True,
        allow_font_substitution=True,
        allow_approximation=True,
        apply_ptouch_adjustments=False  # No adjustments
    )

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

    for technique in available_techniques:
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
        for technique in available_techniques:
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

        for technique in available_techniques:
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

        for technique in available_techniques:
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

if __name__ == "__main__":
    main()