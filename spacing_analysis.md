# Inter-Character Spacing Analysis - Skia

This report analyzes the optimal inter-character spacing values to match P-touch Editor reference dimensions.

## Overall Best Spacing

- **Optimal spacing**: 0.1 points
- **Average error**: 1.97%
- **Mean absolute error**: 5.56%
- **Current default**: 0.1 points

## Font-Specific Optimal Spacing

| Font | Optimal Spacing | Error (%) | Abs Error (%) |
| --- | --- | --- | --- |
| Arial | 0.3 | 0.59% | 3.52% |
| Comic Sans MS | 0.4 | 0.02% | 2.27% |
| Helsinki | 0.0 | 9.12% | 9.12% |
| Helsinki Narrow | 0.0 | 1.12% | 4.13% |

## Size-Specific Optimal Spacing

| Font Size | Optimal Spacing | Error (%) | Abs Error (%) |
| --- | --- | --- | --- |
| 8.0 | 0.1 | 0.35% | 5.15% |
| 10.0 | 0.1 | 1.17% | 5.10% |
| 12.0 | 0.0 | 0.83% | 5.13% |
| 45.7 | 0.0 | 4.05% | 6.63% |

## Relationship with Font Size

- **Correlation coefficient**: -0.6394
- **Interpretation**: Moderate correlation between font size and optimal spacing

## Recommendations

The current default spacing of 0.1 points is very close to the optimal value of 0.1 points.

No change is recommended at this time.

## Visualizations

![Spacing Analysis](plots/spacing_analysis_skia.png)

![Font-Specific Spacing](plots/font_spacing_skia.png)

![Size-Specific Spacing](plots/size_spacing_skia.png)