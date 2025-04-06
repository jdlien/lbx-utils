# Linear Regression Models for Text Dimension Adjustments

This report shows linear models (y = mx + b) for converting calculated dimensions to P-Touch reference dimensions.

## Width Models

```
| Technique | Model Formula | R² | Mean Abs Error | MAPE (%) |
|-----------|---------------|----:|---------------:|--------:|
| Skia | y = 0.9909x-1.4195 | 0.9879 | 3.3699 | 15.53 |
| Core_text | y = 1.0399x-0.9584 | 0.9924 | 2.7365 | 14.23 |
| Pango | y = 0.7225x-1.0913 | 0.9866 | 3.5352 | 15.66 |
| Harfbuzz | y = 0.9923x-1.0583 | 0.9910 | 2.9198 | 12.85 |
| Freetype | y = 0.9283x+0.2314 | 0.9841 | 3.3842 | 11.82 |
| PIL | y = 0.9548x-0.1119 | 0.9831 | 3.5312 | 13.25 |
| Approximation | y = 0.8956x+2.0682 | 0.9939 | 2.2654 | 9.73 |
```

## Height Models

```
| Technique | Model Formula | R² | Mean Abs Error | MAPE (%) |
|-----------|---------------|----:|---------------:|--------:|
| Skia | y = 1.0596x-0.0070 | 0.9853 | 1.4531 | 6.26 |
| Core_text | y = 1.0757x+0.1283 | 0.9880 | 1.3120 | 5.60 |
| Pango | y = 0.8028x+0.4032 | 0.9592 | 3.0378 | 12.73 |
| Harfbuzz | y = 1.1366x+0.7479 | 0.9935 | 1.0322 | 4.27 |
| Freetype | y = 1.3215x-6.9473 | 0.9175 | 4.0791 | 25.79 |
| PIL | y = 0.7720x+8.2653 | 0.9165 | 3.6529 | 15.44 |
| Approximation | y = 0.9939x+0.0729 | 0.9986 | 0.5402 | 2.24 |
```

## Interpretation

- **Model Formula**: Use `pte_dimension = slope * calculated_dimension + intercept`
- **R²**: Coefficient of determination - how well the model fits the data (higher is better, 1.0 is perfect)
- **Mean Abs Error**: Average absolute error in points
- **MAPE**: Mean Absolute Percentage Error

## Recommended Implementation

Based on these results, to adjust calculated dimensions to match P-Touch Editor:

### Best Width Model: Approximation
```python
adjusted_width = 0.895610 * calculated_width + 2.068184
```

### Best Height Model: Approximation
```python
adjusted_height = 0.993946 * calculated_height + 0.072947
```