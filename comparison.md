# Text Dimension Calculation Techniques Comparison

This report compares various text dimension calculation techniques against P-touch Editor reference values.

## Summary Statistics

### Overall Performance

| Technique | Avg Width Diff (%) | Avg Height Diff (%) | Median Width Diff (%) | Median Height Diff (%) | Std Width Diff (%) | Std Height Diff (%) |
| --- | --- | --- | --- | --- | --- | --- |
| Skia | +19.2% | -5.0% | +5.5% | -6.8% | 29.6% | 7.7% |
| Core_text | +8.8% | -7.2% | -2.8% | -7.0% | 23.5% | 6.9% |
| Pango | +58.1% | +24.4% | +41.1% | +35.0% | 37.3% | 16.1% |
| Harfbuzz | +14.4% | -16.1% | +5.3% | -14.0% | 22.9% | 4.4% |
| Freetype | +5.0% | +15.7% | +3.9% | +14.3% | 17.2% | 34.8% |
| PIL | +4.6% | -33.4% | +1.2% | -50.0% | 17.3% | 29.9% |
| Approximation | -7.4% | +0.2% | -3.8% | +2.2% | 16.1% | 2.4% |

### Suggested Adjustment Factors

| Technique | Width Factor | Height Factor |
| --- | --- | --- |
| Skia | 0.8387 | 1.0524 |
| Core_text | 0.9192 | 1.0772 |
| Pango | 0.6325 | 0.8037 |
| Harfbuzz | 0.8743 | 1.1922 |
| Freetype | 0.9522 | 0.8646 |
| PIL | 0.9559 | 1.5021 |
| Approximation | 1.0798 | 0.9977 |

## Font-Specific Statistics

### Arial Font

| Technique | Avg Width Diff (%) | Avg Height Diff (%) | Width Factor | Height Factor |
| --- | --- | --- | --- | --- |
| Skia | +17.1% | +7.4% | 0.8540 | 0.9307 |
| Core_text | +11.4% | +0.1% | 0.8979 | 0.9986 |
| Pango | +55.0% | +39.3% | 0.6451 | 0.7180 |
| Harfbuzz | +14.5% | -11.4% | 0.8731 | 1.1286 |
| Freetype | +3.6% | +20.8% | 0.9652 | 0.8279 |
| PIL | +1.1% | -47.1% | 0.9892 | 1.8913 |
| Approximation | -13.2% | -3.3% | 1.1525 | 1.0341 |

### Comic Sans MS Font

| Technique | Avg Width Diff (%) | Avg Height Diff (%) | Width Factor | Height Factor |
| --- | --- | --- | --- | --- |
| Skia | +10.1% | -13.7% | 0.9086 | 1.1590 |
| Core_text | +3.0% | -8.5% | 0.9713 | 1.0932 |
| Pango | +40.5% | +41.2% | 0.7118 | 0.7084 |
| Harfbuzz | +10.1% | -13.7% | 0.9086 | 1.1590 |
| Freetype | +10.1% | -13.7% | 0.9086 | 1.1590 |
| PIL | +10.1% | -13.7% | 0.9086 | 1.1590 |
| Approximation | -1.4% | -0.8% | 1.0143 | 1.0078 |

### Helsinki Font

| Technique | Avg Width Diff (%) | Avg Height Diff (%) | Width Factor | Height Factor |
| --- | --- | --- | --- | --- |
| Skia | +28.5% | -6.8% | 0.7781 | 1.0733 |
| Core_text | +14.2% | -9.0% | 0.8760 | 1.0985 |
| Pango | +54.2% | +8.6% | 0.6487 | 0.9205 |
| Harfbuzz | +22.3% | -19.7% | 0.8180 | 1.2451 |
| Freetype | +10.2% | +29.7% | 0.9073 | 0.7707 |
| PIL | +13.0% | -36.7% | 0.8846 | 1.5800 |
| Approximation | -2.0% | +2.5% | 1.0205 | 0.9757 |

### Helsinki Narrow Font

| Technique | Avg Width Diff (%) | Avg Height Diff (%) | Width Factor | Height Factor |
| --- | --- | --- | --- | --- |
| Skia | +21.2% | -6.8% | 0.8248 | 1.0733 |
| Core_text | +6.7% | -11.3% | 0.9372 | 1.1274 |
| Pango | +82.7% | +8.6% | 0.5473 | 0.9205 |
| Harfbuzz | +10.7% | -19.7% | 0.9034 | 1.2451 |
| Freetype | -3.8% | +25.8% | 1.0392 | 0.7949 |
| PIL | -5.7% | -36.1% | 1.0609 | 1.5660 |
| Approximation | -12.9% | +2.5% | 1.1483 | 0.9757 |

## Individual String Comparisons

### Arial Font

#### 8.0pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 37.80 | 8.90 | - | - |
| Skia | 34.70 | 9.60 | -8.2% | +7.9% |
| Core_text | 34.70 | 9.60 | -8.2% | +7.9% |
| Pango | 53.00 | 12.74 | +40.2% | +43.1% |
| Harfbuzz | 36.43 | 7.70 | -3.6% | -13.5% |
| Freetype | 38.72 | 15.32 | +2.4% | +72.1% |
| PIL | 40.43 | 4.80 | +6.9% | -46.1% |
| Approximation | 38.02 | 8.64 | +0.6% | -2.9% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.70 | 8.90 | - | - |
| Skia | 8.90 | 9.60 | -8.3% | +7.9% |
| Core_text | 8.90 | 9.60 | -8.3% | +7.9% |
| Pango | 13.00 | 12.74 | +34.0% | +43.1% |
| Harfbuzz | 9.34 | 7.70 | -3.7% | -13.5% |
| Freetype | 9.68 | 15.32 | -0.2% | +72.1% |
| PIL | 10.40 | 3.60 | +7.2% | -59.6% |
| Approximation | 8.45 | 8.64 | -12.9% | -2.9% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.40 | 8.90 | - | - |
| Skia | 4.45 | 9.60 | +30.9% | +7.9% |
| Core_text | 4.45 | 9.60 | +30.9% | +7.9% |
| Pango | 5.70 | 12.74 | +67.6% | +43.1% |
| Harfbuzz | 4.20 | 7.70 | +23.7% | -13.5% |
| Freetype | 2.42 | 15.32 | -28.8% | +72.1% |
| PIL | 2.31 | 3.60 | -32.1% | -59.6% |
| Approximation | 2.11 | 8.64 | -37.9% | -2.9% |

#### 8.0pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.00 | 8.90 | - | - |
| Skia | 4.45 | 9.60 | +48.3% | +7.9% |
| Core_text | 3.80 | 8.28 | +26.8% | -7.0% |
| Pango | 5.70 | 12.74 | +90.0% | +43.1% |
| Harfbuzz | 4.00 | 7.70 | +33.5% | -13.5% |
| Freetype | 2.20 | 15.32 | -26.7% | +72.1% |
| PIL | 2.20 | 3.60 | -26.7% | -59.6% |
| Approximation | 1.92 | 8.64 | -36.0% | -2.9% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.20 | 8.90 | - | - |
| Skia | 8.90 | 9.60 | -3.3% | +7.9% |
| Core_text | 8.45 | 8.28 | -8.1% | -7.0% |
| Pango | 12.00 | 12.74 | +30.4% | +43.1% |
| Harfbuzz | 8.90 | 7.70 | -3.3% | -13.5% |
| Freetype | 8.80 | 15.32 | -4.3% | +72.1% |
| PIL | 9.90 | 3.60 | +7.6% | -59.6% |
| Approximation | 7.68 | 8.64 | -16.5% | -2.9% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 34.90 | 8.90 | - | - |
| Skia | 34.70 | 9.60 | -0.6% | +7.9% |
| Core_text | 32.96 | 8.28 | -5.6% | -7.0% |
| Pango | 46.00 | 12.74 | +31.8% | +43.1% |
| Harfbuzz | 34.70 | 7.70 | -0.6% | -13.5% |
| Freetype | 35.20 | 15.32 | +0.9% | +72.1% |
| PIL | 38.50 | 4.80 | +10.3% | -46.1% |
| Approximation | 34.56 | 8.64 | -1.0% | -2.9% |

#### 10.0pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.00 | 11.20 | - | - |
| Skia | 5.56 | 12.00 | +39.0% | +7.1% |
| Core_text | 5.56 | 12.00 | +39.0% | +7.1% |
| Pango | 6.65 | 15.68 | +66.2% | +40.0% |
| Harfbuzz | 5.26 | 9.63 | +31.4% | -14.0% |
| Freetype | 3.63 | 15.32 | -9.2% | +36.8% |
| PIL | 3.47 | 4.20 | -13.4% | -62.5% |
| Approximation | 2.64 | 10.80 | -34.0% | -3.6% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.80 | 11.20 | - | - |
| Skia | 11.12 | 12.00 | -5.7% | +7.1% |
| Core_text | 11.12 | 12.00 | -5.7% | +7.1% |
| Pango | 15.00 | 15.68 | +27.1% | +40.0% |
| Harfbuzz | 11.68 | 9.63 | -1.0% | -14.0% |
| Freetype | 14.52 | 15.32 | +23.1% | +36.8% |
| PIL | 13.86 | 4.20 | +17.5% | -62.5% |
| Approximation | 10.56 | 10.80 | -10.5% | -3.6% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 47.10 | 11.20 | - | - |
| Skia | 43.37 | 12.00 | -7.9% | +7.1% |
| Core_text | 43.37 | 12.00 | -7.9% | +7.1% |
| Pango | 61.00 | 15.68 | +29.5% | +40.0% |
| Harfbuzz | 45.54 | 9.63 | -3.3% | -14.0% |
| Freetype | 55.66 | 15.32 | +18.2% | +36.8% |
| PIL | 49.66 | 5.40 | +5.4% | -51.8% |
| Approximation | 47.52 | 10.80 | +0.9% | -3.6% |

#### 10.0pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 43.20 | 11.20 | - | - |
| Skia | 43.37 | 12.00 | +0.4% | +7.1% |
| Core_text | 41.20 | 10.12 | -4.6% | -9.6% |
| Pango | 56.00 | 15.68 | +29.6% | +40.0% |
| Harfbuzz | 43.37 | 9.63 | +0.4% | -14.0% |
| Freetype | 50.60 | 15.32 | +17.1% | +36.8% |
| PIL | 47.30 | 5.40 | +9.5% | -51.8% |
| Approximation | 43.20 | 10.80 | +0.0% | -3.6% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.20 | 11.20 | - | - |
| Skia | 11.12 | 12.00 | -0.7% | +7.1% |
| Core_text | 10.57 | 10.12 | -5.7% | -9.6% |
| Pango | 14.00 | 15.68 | +25.0% | +40.0% |
| Harfbuzz | 11.12 | 9.63 | -0.7% | -14.0% |
| Freetype | 13.20 | 15.32 | +17.9% | +36.8% |
| PIL | 13.20 | 4.20 | +17.9% | -62.5% |
| Approximation | 9.60 | 10.80 | -14.3% | -3.6% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.50 | 11.20 | - | - |
| Skia | 5.56 | 12.00 | +58.9% | +7.1% |
| Core_text | 4.76 | 10.12 | +35.9% | -9.6% |
| Pango | 6.65 | 15.68 | +90.0% | +40.0% |
| Harfbuzz | 5.01 | 9.63 | +43.0% | -14.0% |
| Freetype | 3.30 | 15.32 | -5.7% | +36.8% |
| PIL | 3.30 | 4.20 | -5.7% | -62.5% |
| Approximation | 2.40 | 10.80 | -31.4% | -3.6% |

#### 12.0pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.60 | 13.40 | - | - |
| Skia | 6.67 | 14.40 | +45.1% | +7.5% |
| Core_text | 6.67 | 14.40 | +45.1% | +7.5% |
| Pango | 8.55 | 18.62 | +85.9% | +39.0% |
| Harfbuzz | 6.31 | 11.55 | +37.1% | -13.8% |
| Freetype | 4.24 | 15.32 | -7.9% | +14.3% |
| PIL | 4.04 | 5.40 | -12.1% | -59.7% |
| Approximation | 3.17 | 12.96 | -31.1% | -3.3% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 13.90 | 13.40 | - | - |
| Skia | 13.35 | 14.40 | -4.0% | +7.5% |
| Core_text | 13.35 | 14.40 | -4.0% | +7.5% |
| Pango | 19.00 | 18.62 | +36.7% | +39.0% |
| Harfbuzz | 14.02 | 11.55 | +0.8% | -13.8% |
| Freetype | 16.94 | 15.32 | +21.9% | +14.3% |
| PIL | 16.17 | 5.40 | +16.3% | -59.7% |
| Approximation | 12.67 | 12.96 | -8.8% | -3.3% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 56.30 | 13.40 | - | - |
| Skia | 52.04 | 14.40 | -7.6% | +7.5% |
| Core_text | 52.04 | 14.40 | -7.6% | +7.5% |
| Pango | 76.00 | 18.62 | +35.0% | +39.0% |
| Harfbuzz | 54.65 | 11.55 | -2.9% | -13.8% |
| Freetype | 65.34 | 15.32 | +16.1% | +14.3% |
| PIL | 60.06 | 6.60 | +6.7% | -50.7% |
| Approximation | 57.02 | 12.96 | +1.3% | -3.3% |

#### 12.0pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 51.60 | 13.40 | - | - |
| Skia | 52.04 | 14.40 | +0.9% | +7.5% |
| Core_text | 49.44 | 12.88 | -4.2% | -3.9% |
| Pango | 70.00 | 18.62 | +35.7% | +39.0% |
| Harfbuzz | 52.04 | 11.55 | +0.9% | -13.8% |
| Freetype | 59.40 | 15.32 | +15.1% | +14.3% |
| PIL | 57.20 | 6.60 | +10.9% | -50.7% |
| Approximation | 51.84 | 12.96 | +0.5% | -3.3% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 13.20 | 13.40 | - | - |
| Skia | 13.35 | 14.40 | +1.1% | +7.5% |
| Core_text | 12.68 | 12.88 | -3.9% | -3.9% |
| Pango | 18.00 | 18.62 | +36.4% | +39.0% |
| Harfbuzz | 13.35 | 11.55 | +1.1% | -13.8% |
| Freetype | 15.40 | 15.32 | +16.7% | +14.3% |
| PIL | 15.40 | 5.40 | +16.7% | -59.7% |
| Approximation | 11.52 | 12.96 | -12.7% | -3.3% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.00 | 13.40 | - | - |
| Skia | 6.67 | 14.40 | +66.8% | +7.5% |
| Core_text | 5.71 | 12.88 | +42.7% | -3.9% |
| Pango | 8.55 | 18.62 | +113.7% | +39.0% |
| Harfbuzz | 6.01 | 11.55 | +50.2% | -13.8% |
| Freetype | 3.85 | 15.32 | -3.7% | +14.3% |
| PIL | 3.85 | 5.40 | -3.7% | -59.7% |
| Approximation | 2.88 | 12.96 | -28.0% | -3.3% |

#### 45.7pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 211.80 | 51.10 | - | - |
| Skia | 198.20 | 54.84 | -6.4% | +7.3% |
| Core_text | 198.20 | 54.84 | -6.4% | +7.3% |
| Pango | 287.00 | 69.00 | +35.5% | +35.0% |
| Harfbuzz | 208.11 | 48.89 | -1.7% | -4.3% |
| Freetype | 222.20 | 30.64 | +4.9% | -40.0% |
| PIL | 204.75 | 49.20 | -3.3% | -3.7% |
| Approximation | 217.17 | 49.36 | +2.5% | -3.4% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 50.90 | 51.10 | - | - |
| Skia | 50.83 | 54.84 | -0.1% | +7.3% |
| Core_text | 50.83 | 54.84 | -0.1% | +7.3% |
| Pango | 71.00 | 69.00 | +39.5% | +35.0% |
| Harfbuzz | 53.37 | 48.89 | +4.9% | -4.3% |
| Freetype | 57.20 | 30.64 | +12.4% | -40.0% |
| PIL | 52.50 | 38.40 | +3.1% | -24.9% |
| Approximation | 48.26 | 49.36 | -5.2% | -3.4% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 15.20 | 51.10 | - | - |
| Skia | 25.42 | 54.84 | +67.2% | +7.3% |
| Core_text | 25.42 | 54.84 | +67.2% | +7.3% |
| Pango | 32.30 | 69.00 | +112.5% | +35.0% |
| Harfbuzz | 24.02 | 48.89 | +58.0% | -4.3% |
| Freetype | 14.30 | 30.64 | -5.9% | -40.0% |
| PIL | 13.12 | 38.40 | -13.7% | -24.9% |
| Approximation | 12.06 | 49.36 | -20.6% | -3.4% |

#### 45.7pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 12.90 | 51.10 | - | - |
| Skia | 25.42 | 54.84 | +97.0% | +7.3% |
| Core_text | 21.73 | 46.92 | +68.5% | -8.2% |
| Pango | 32.30 | 69.00 | +150.4% | +35.0% |
| Harfbuzz | 22.87 | 48.89 | +77.3% | -4.3% |
| Freetype | 13.00 | 30.64 | +0.8% | -40.0% |
| PIL | 12.50 | 38.40 | -3.1% | -24.9% |
| Approximation | 10.97 | 49.36 | -15.0% | -3.4% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 48.20 | 51.10 | - | - |
| Skia | 50.83 | 54.84 | +5.5% | +7.3% |
| Core_text | 48.29 | 46.92 | +0.2% | -8.2% |
| Pango | 68.00 | 69.00 | +41.1% | +35.0% |
| Harfbuzz | 50.83 | 48.89 | +5.5% | -4.3% |
| Freetype | 52.00 | 30.64 | +7.9% | -40.0% |
| PIL | 50.00 | 38.40 | +3.7% | -24.9% |
| Approximation | 43.87 | 49.36 | -9.0% | -3.4% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 194.30 | 51.10 | - | - |
| Skia | 198.20 | 54.84 | +2.0% | +7.3% |
| Core_text | 188.29 | 46.92 | -3.1% | -8.2% |
| Pango | 265.00 | 69.00 | +36.4% | +35.0% |
| Harfbuzz | 198.20 | 48.89 | +2.0% | -4.3% |
| Freetype | 202.00 | 30.64 | +4.0% | -40.0% |
| PIL | 195.00 | 49.20 | +0.4% | -3.7% |
| Approximation | 197.42 | 49.36 | +1.6% | -3.4% |

### Comic Sans MS Font

#### 8.0pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.70 | 11.10 | - | - |
| Skia | 4.45 | 9.60 | +20.2% | -13.5% |
| Core_text | 4.45 | 9.60 | +20.2% | -13.5% |
| Pango | 6.52 | 16.32 | +76.1% | +47.0% |
| Harfbuzz | 4.45 | 9.60 | +20.2% | -13.5% |
| Freetype | 4.45 | 9.60 | +20.2% | -13.5% |
| PIL | 4.45 | 9.60 | +20.2% | -13.5% |
| Approximation | 2.51 | 11.04 | -32.2% | -0.5% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.50 | 11.10 | - | - |
| Skia | 8.90 | 9.60 | -6.3% | -13.5% |
| Core_text | 8.90 | 9.60 | -6.3% | -13.5% |
| Pango | 11.76 | 16.32 | +23.8% | +47.0% |
| Harfbuzz | 8.90 | 9.60 | -6.3% | -13.5% |
| Freetype | 8.90 | 9.60 | -6.3% | -13.5% |
| PIL | 8.90 | 9.60 | -6.3% | -13.5% |
| Approximation | 10.03 | 11.04 | +5.6% | -0.5% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 38.00 | 11.10 | - | - |
| Skia | 34.70 | 9.60 | -8.7% | -13.5% |
| Core_text | 34.70 | 9.60 | -8.7% | -13.5% |
| Pango | 48.02 | 16.32 | +26.4% | +47.0% |
| Harfbuzz | 34.70 | 9.60 | -8.7% | -13.5% |
| Freetype | 34.70 | 9.60 | -8.7% | -13.5% |
| PIL | 34.70 | 9.60 | -8.7% | -13.5% |
| Approximation | 45.14 | 11.04 | +18.8% | -0.5% |

#### 8.0pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 37.40 | 11.10 | - | - |
| Skia | 34.70 | 9.60 | -7.2% | -13.5% |
| Core_text | 36.09 | 10.78 | -3.5% | -2.9% |
| Pango | 47.04 | 16.32 | +25.8% | +47.0% |
| Harfbuzz | 34.70 | 9.60 | -7.2% | -13.5% |
| Freetype | 34.70 | 9.60 | -7.2% | -13.5% |
| PIL | 34.70 | 9.60 | -7.2% | -13.5% |
| Approximation | 41.04 | 11.04 | +9.7% | -0.5% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.00 | 11.10 | - | - |
| Skia | 8.90 | 9.60 | -1.1% | -13.5% |
| Core_text | 8.57 | 10.78 | -4.7% | -2.9% |
| Pango | 10.78 | 16.32 | +19.8% | +47.0% |
| Harfbuzz | 8.90 | 9.60 | -1.1% | -13.5% |
| Freetype | 8.90 | 9.60 | -1.1% | -13.5% |
| PIL | 8.90 | 9.60 | -1.1% | -13.5% |
| Approximation | 9.12 | 11.04 | +1.3% | -0.5% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.40 | 11.10 | - | - |
| Skia | 4.45 | 9.60 | +30.9% | -13.5% |
| Core_text | 3.14 | 10.78 | -7.5% | -2.9% |
| Pango | 4.65 | 16.32 | +36.9% | +47.0% |
| Harfbuzz | 4.45 | 9.60 | +30.9% | -13.5% |
| Freetype | 4.45 | 9.60 | +30.9% | -13.5% |
| PIL | 4.45 | 9.60 | +30.9% | -13.5% |
| Approximation | 2.28 | 11.04 | -32.9% | -0.5% |

#### 10.0pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 47.20 | 13.90 | - | - |
| Skia | 43.37 | 12.00 | -8.1% | -13.7% |
| Core_text | 43.37 | 12.00 | -8.1% | -13.7% |
| Pango | 61.74 | 19.38 | +30.8% | +39.4% |
| Harfbuzz | 43.37 | 12.00 | -8.1% | -13.7% |
| Freetype | 43.37 | 12.00 | -8.1% | -13.7% |
| PIL | 43.37 | 12.00 | -8.1% | -13.7% |
| Approximation | 56.43 | 13.80 | +19.6% | -0.7% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.70 | 13.90 | - | - |
| Skia | 11.12 | 12.00 | -4.9% | -13.7% |
| Core_text | 11.12 | 12.00 | -4.9% | -13.7% |
| Pango | 14.70 | 19.38 | +25.6% | +39.4% |
| Harfbuzz | 11.12 | 12.00 | -4.9% | -13.7% |
| Freetype | 11.12 | 12.00 | -4.9% | -13.7% |
| PIL | 11.12 | 12.00 | -4.9% | -13.7% |
| Approximation | 12.54 | 13.80 | +7.2% | -0.7% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.40 | 13.90 | - | - |
| Skia | 5.56 | 12.00 | +26.4% | -13.7% |
| Core_text | 5.56 | 12.00 | +26.4% | -13.7% |
| Pango | 7.45 | 19.38 | +69.3% | +39.4% |
| Harfbuzz | 5.56 | 12.00 | +26.4% | -13.7% |
| Freetype | 5.56 | 12.00 | +26.4% | -13.7% |
| PIL | 5.56 | 12.00 | +26.4% | -13.7% |
| Approximation | 3.14 | 13.80 | -28.7% | -0.7% |

#### 10.0pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.00 | 13.90 | - | - |
| Skia | 5.56 | 12.00 | +39.0% | -13.7% |
| Core_text | 3.93 | 13.72 | -1.7% | -1.3% |
| Pango | 5.59 | 19.38 | +39.6% | +39.4% |
| Harfbuzz | 5.56 | 12.00 | +39.0% | -13.7% |
| Freetype | 5.56 | 12.00 | +39.0% | -13.7% |
| PIL | 5.56 | 12.00 | +39.0% | -13.7% |
| Approximation | 2.85 | 13.80 | -28.8% | -0.7% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.30 | 13.90 | - | - |
| Skia | 11.12 | 12.00 | -1.6% | -13.7% |
| Core_text | 10.72 | 13.72 | -5.1% | -1.3% |
| Pango | 14.70 | 19.38 | +30.1% | +39.4% |
| Harfbuzz | 11.12 | 12.00 | -1.6% | -13.7% |
| Freetype | 11.12 | 12.00 | -1.6% | -13.7% |
| PIL | 11.12 | 12.00 | -1.6% | -13.7% |
| Approximation | 11.40 | 13.80 | +0.9% | -0.7% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 46.60 | 13.90 | - | - |
| Skia | 43.37 | 12.00 | -6.9% | -13.7% |
| Core_text | 45.11 | 13.72 | -3.2% | -1.3% |
| Pango | 61.74 | 19.38 | +32.5% | +39.4% |
| Harfbuzz | 43.37 | 12.00 | -6.9% | -13.7% |
| Freetype | 43.37 | 12.00 | -6.9% | -13.7% |
| PIL | 43.37 | 12.00 | -6.9% | -13.7% |
| Approximation | 51.30 | 13.80 | +10.1% | -0.7% |

#### 12.0pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 56.60 | 16.70 | - | - |
| Skia | 52.04 | 14.40 | -8.1% | -13.8% |
| Core_text | 52.04 | 14.40 | -8.1% | -13.8% |
| Pango | 71.54 | 23.46 | +26.4% | +40.5% |
| Harfbuzz | 52.04 | 14.40 | -8.1% | -13.8% |
| Freetype | 52.04 | 14.40 | -8.1% | -13.8% |
| PIL | 52.04 | 14.40 | -8.1% | -13.8% |
| Approximation | 67.72 | 16.56 | +19.6% | -0.8% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 13.80 | 16.70 | - | - |
| Skia | 13.35 | 14.40 | -3.3% | -13.8% |
| Core_text | 13.35 | 14.40 | -3.3% | -13.8% |
| Pango | 17.64 | 23.46 | +27.8% | +40.5% |
| Harfbuzz | 13.35 | 14.40 | -3.3% | -13.8% |
| Freetype | 13.35 | 14.40 | -3.3% | -13.8% |
| PIL | 13.35 | 14.40 | -3.3% | -13.8% |
| Approximation | 15.05 | 16.56 | +9.0% | -0.8% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 5.10 | 16.70 | - | - |
| Skia | 6.67 | 14.40 | +30.9% | -13.8% |
| Core_text | 6.67 | 14.40 | +30.9% | -13.8% |
| Pango | 9.31 | 23.46 | +82.5% | +40.5% |
| Harfbuzz | 6.67 | 14.40 | +30.9% | -13.8% |
| Freetype | 6.67 | 14.40 | +30.9% | -13.8% |
| PIL | 6.67 | 14.40 | +30.9% | -13.8% |
| Approximation | 3.76 | 16.56 | -26.2% | -0.8% |

#### 12.0pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.60 | 16.70 | - | - |
| Skia | 6.67 | 14.40 | +45.1% | -13.8% |
| Core_text | 4.72 | 15.68 | +2.5% | -6.1% |
| Pango | 6.52 | 23.46 | +41.7% | +40.5% |
| Harfbuzz | 6.67 | 14.40 | +45.1% | -13.8% |
| Freetype | 6.67 | 14.40 | +45.1% | -13.8% |
| PIL | 6.67 | 14.40 | +45.1% | -13.8% |
| Approximation | 3.42 | 16.56 | -25.7% | -0.8% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 13.30 | 16.70 | - | - |
| Skia | 13.35 | 14.40 | +0.4% | -13.8% |
| Core_text | 12.86 | 15.68 | -3.3% | -6.1% |
| Pango | 16.66 | 23.46 | +25.3% | +40.5% |
| Harfbuzz | 13.35 | 14.40 | +0.4% | -13.8% |
| Freetype | 13.35 | 14.40 | +0.4% | -13.8% |
| PIL | 13.35 | 14.40 | +0.4% | -13.8% |
| Approximation | 13.68 | 16.56 | +2.9% | -0.8% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 55.70 | 16.70 | - | - |
| Skia | 52.04 | 14.40 | -6.6% | -13.8% |
| Core_text | 54.14 | 15.68 | -2.8% | -6.1% |
| Pango | 70.56 | 23.46 | +26.7% | +40.5% |
| Harfbuzz | 52.04 | 14.40 | -6.6% | -13.8% |
| Freetype | 52.04 | 14.40 | -6.6% | -13.8% |
| PIL | 52.04 | 14.40 | -6.6% | -13.8% |
| Approximation | 61.56 | 16.56 | +10.5% | -0.8% |

#### 45.7pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 17.00 | 63.70 | - | - |
| Skia | 25.42 | 54.84 | +49.5% | -13.9% |
| Core_text | 25.42 | 54.84 | +49.5% | -13.9% |
| Pango | 34.45 | 87.72 | +102.6% | +37.7% |
| Harfbuzz | 25.42 | 54.84 | +49.5% | -13.9% |
| Freetype | 25.42 | 54.84 | +49.5% | -13.9% |
| PIL | 25.42 | 54.84 | +49.5% | -13.9% |
| Approximation | 14.33 | 63.07 | -15.7% | -1.0% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 50.30 | 63.70 | - | - |
| Skia | 50.83 | 54.84 | +1.1% | -13.9% |
| Core_text | 50.83 | 54.84 | +1.1% | -13.9% |
| Pango | 68.60 | 87.72 | +36.4% | +37.7% |
| Harfbuzz | 50.83 | 54.84 | +1.1% | -13.9% |
| Freetype | 50.83 | 54.84 | +1.1% | -13.9% |
| PIL | 50.83 | 54.84 | +1.1% | -13.9% |
| Approximation | 57.31 | 63.07 | +13.9% | -1.0% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 212.80 | 63.70 | - | - |
| Skia | 198.20 | 54.84 | -6.9% | -13.9% |
| Core_text | 198.20 | 54.84 | -6.9% | -13.9% |
| Pango | 280.28 | 87.72 | +31.7% | +37.7% |
| Harfbuzz | 198.20 | 54.84 | -6.9% | -13.9% |
| Freetype | 198.20 | 54.84 | -6.9% | -13.9% |
| PIL | 198.20 | 54.84 | -6.9% | -13.9% |
| Approximation | 257.89 | 63.07 | +21.2% | -1.0% |

#### 45.7pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 209.30 | 63.70 | - | - |
| Skia | 198.20 | 54.84 | -5.3% | -13.9% |
| Core_text | 206.17 | 61.74 | -1.5% | -3.1% |
| Pango | 276.36 | 87.72 | +32.0% | +37.7% |
| Harfbuzz | 198.20 | 54.84 | -5.3% | -13.9% |
| Freetype | 198.20 | 54.84 | -5.3% | -13.9% |
| PIL | 198.20 | 54.84 | -5.3% | -13.9% |
| Approximation | 234.44 | 63.07 | +12.0% | -1.0% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 48.10 | 63.70 | - | - |
| Skia | 50.83 | 54.84 | +5.7% | -13.9% |
| Core_text | 48.98 | 61.74 | +1.8% | -3.1% |
| Pango | 65.66 | 87.72 | +36.5% | +37.7% |
| Harfbuzz | 50.83 | 54.84 | +5.7% | -13.9% |
| Freetype | 50.83 | 54.84 | +5.7% | -13.9% |
| PIL | 50.83 | 54.84 | +5.7% | -13.9% |
| Approximation | 52.10 | 63.07 | +8.3% | -1.0% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 15.20 | 63.70 | - | - |
| Skia | 25.42 | 54.84 | +67.2% | -13.9% |
| Core_text | 17.96 | 61.74 | +18.2% | -3.1% |
| Pango | 25.14 | 87.72 | +65.4% | +37.7% |
| Harfbuzz | 25.42 | 54.84 | +67.2% | -13.9% |
| Freetype | 25.42 | 54.84 | +67.2% | -13.9% |
| PIL | 25.42 | 54.84 | +67.2% | -13.9% |
| Approximation | 13.02 | 63.07 | -14.3% | -1.0% |

### Helsinki Font

#### 8.0pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.40 | 10.30 | - | - |
| Skia | 4.67 | 9.60 | +37.4% | -6.8% |
| Core_text | 4.67 | 9.60 | +37.4% | -6.8% |
| Pango | 5.76 | 11.52 | +69.3% | +11.8% |
| Harfbuzz | 4.29 | 8.17 | +26.1% | -20.7% |
| Freetype | 2.42 | 18.02 | -28.8% | +75.0% |
| PIL | 2.89 | 4.20 | -15.1% | -59.2% |
| Approximation | 2.38 | 10.56 | -30.1% | +2.5% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.60 | 10.30 | - | - |
| Skia | 9.80 | 9.60 | +2.1% | -6.8% |
| Core_text | 9.80 | 9.60 | +2.1% | -6.8% |
| Pango | 12.12 | 11.52 | +26.3% | +11.8% |
| Harfbuzz | 10.00 | 8.17 | +4.2% | -20.7% |
| Freetype | 10.89 | 18.02 | +13.4% | +75.0% |
| PIL | 11.55 | 4.20 | +20.3% | -59.2% |
| Approximation | 9.50 | 10.56 | -1.0% | +2.5% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 37.90 | 10.30 | - | - |
| Skia | 39.67 | 9.60 | +4.7% | -6.8% |
| Core_text | 39.67 | 9.60 | +4.7% | -6.8% |
| Pango | 46.46 | 11.52 | +22.6% | +11.8% |
| Harfbuzz | 40.46 | 8.17 | +6.8% | -20.7% |
| Freetype | 44.77 | 18.02 | +18.1% | +75.0% |
| PIL | 45.05 | 4.90 | +18.9% | -52.4% |
| Approximation | 42.77 | 10.56 | +12.8% | +2.5% |

#### 8.0pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 34.70 | 10.30 | - | - |
| Skia | 39.67 | 9.60 | +14.3% | -6.8% |
| Core_text | 31.23 | 9.50 | -10.0% | -7.8% |
| Pango | 46.46 | 11.52 | +33.9% | +11.8% |
| Harfbuzz | 38.54 | 8.17 | +11.1% | -20.7% |
| Freetype | 40.70 | 18.02 | +17.3% | +75.0% |
| PIL | 42.90 | 4.90 | +23.6% | -52.4% |
| Approximation | 38.88 | 10.56 | +12.0% | +2.5% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.20 | 10.30 | - | - |
| Skia | 9.80 | 9.60 | +6.6% | -6.8% |
| Core_text | 8.01 | 9.50 | -13.0% | -7.8% |
| Pango | 12.12 | 11.52 | +31.7% | +11.8% |
| Harfbuzz | 9.52 | 8.17 | +3.5% | -20.7% |
| Freetype | 9.90 | 18.02 | +7.6% | +75.0% |
| PIL | 11.00 | 4.20 | +19.6% | -59.2% |
| Approximation | 8.64 | 10.56 | -6.1% | +2.5% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 2.90 | 10.30 | - | - |
| Skia | 4.67 | 9.60 | +61.1% | -6.8% |
| Core_text | 3.60 | 9.50 | +24.3% | -7.8% |
| Pango | 5.76 | 11.52 | +98.5% | +11.8% |
| Harfbuzz | 4.08 | 8.17 | +40.8% | -20.7% |
| Freetype | 2.20 | 18.02 | -24.1% | +75.0% |
| PIL | 2.75 | 4.20 | -5.2% | -59.2% |
| Approximation | 2.16 | 10.56 | -25.5% | +2.5% |

#### 10.0pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 47.10 | 12.90 | - | - |
| Skia | 49.59 | 12.00 | +5.3% | -7.0% |
| Core_text | 49.59 | 12.00 | +5.3% | -7.0% |
| Pango | 56.56 | 14.40 | +20.1% | +11.6% |
| Harfbuzz | 50.58 | 10.21 | +7.4% | -20.9% |
| Freetype | 58.08 | 18.02 | +23.3% | +39.7% |
| PIL | 55.44 | 6.30 | +17.7% | -51.2% |
| Approximation | 53.46 | 13.20 | +13.5% | +2.3% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.80 | 12.90 | - | - |
| Skia | 12.25 | 12.00 | +3.8% | -7.0% |
| Core_text | 12.25 | 12.00 | +3.8% | -7.0% |
| Pango | 14.14 | 14.40 | +19.8% | +11.6% |
| Harfbuzz | 12.50 | 10.21 | +5.9% | -20.9% |
| Freetype | 14.52 | 18.02 | +23.1% | +39.7% |
| PIL | 15.02 | 4.90 | +27.2% | -62.0% |
| Approximation | 11.88 | 13.20 | +0.7% | +2.3% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.00 | 12.90 | - | - |
| Skia | 5.84 | 12.00 | +46.0% | -7.0% |
| Core_text | 5.84 | 12.00 | +46.0% | -7.0% |
| Pango | 6.72 | 14.40 | +67.9% | +11.6% |
| Harfbuzz | 5.36 | 10.21 | +34.0% | -20.9% |
| Freetype | 3.63 | 18.02 | -9.2% | +39.7% |
| PIL | 3.47 | 4.90 | -13.4% | -62.0% |
| Approximation | 2.97 | 13.20 | -25.7% | +2.3% |

#### 10.0pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.40 | 12.90 | - | - |
| Skia | 5.84 | 12.00 | +71.8% | -7.0% |
| Core_text | 4.50 | 11.40 | +32.5% | -11.6% |
| Pango | 6.72 | 14.40 | +97.5% | +11.6% |
| Harfbuzz | 5.11 | 10.21 | +50.2% | -20.9% |
| Freetype | 3.30 | 18.02 | -2.9% | +39.7% |
| PIL | 3.30 | 4.90 | -2.9% | -62.0% |
| Approximation | 2.70 | 13.20 | -20.6% | +2.3% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.30 | 12.90 | - | - |
| Skia | 12.25 | 12.00 | +8.4% | -7.0% |
| Core_text | 10.01 | 11.40 | -11.4% | -11.6% |
| Pango | 14.14 | 14.40 | +25.1% | +11.6% |
| Harfbuzz | 11.90 | 10.21 | +5.3% | -20.9% |
| Freetype | 13.20 | 18.02 | +16.8% | +39.7% |
| PIL | 14.30 | 4.90 | +26.5% | -62.0% |
| Approximation | 10.80 | 13.20 | -4.4% | +2.3% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 43.20 | 12.90 | - | - |
| Skia | 49.59 | 12.00 | +14.8% | -7.0% |
| Core_text | 39.03 | 11.40 | -9.6% | -11.6% |
| Pango | 56.56 | 14.40 | +30.9% | +11.6% |
| Harfbuzz | 48.17 | 10.21 | +11.5% | -20.9% |
| Freetype | 52.80 | 18.02 | +22.2% | +39.7% |
| PIL | 52.80 | 6.30 | +22.2% | -51.2% |
| Approximation | 48.60 | 13.20 | +12.5% | +2.3% |

#### 12.0pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 56.30 | 15.40 | - | - |
| Skia | 59.51 | 14.40 | +5.7% | -6.5% |
| Core_text | 59.51 | 14.40 | +5.7% | -6.5% |
| Pango | 70.70 | 16.32 | +25.6% | +6.0% |
| Harfbuzz | 60.70 | 12.25 | +7.8% | -20.4% |
| Freetype | 67.76 | 18.02 | +20.4% | +17.0% |
| PIL | 66.99 | 7.70 | +19.0% | -50.0% |
| Approximation | 64.15 | 15.84 | +13.9% | +2.9% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 13.90 | 15.40 | - | - |
| Skia | 14.70 | 14.40 | +5.8% | -6.5% |
| Core_text | 14.70 | 14.40 | +5.8% | -6.5% |
| Pango | 18.18 | 16.32 | +30.8% | +6.0% |
| Harfbuzz | 15.00 | 12.25 | +7.9% | -20.4% |
| Freetype | 16.94 | 18.02 | +21.9% | +17.0% |
| PIL | 17.33 | 6.30 | +24.6% | -59.1% |
| Approximation | 14.26 | 15.84 | +2.6% | +2.9% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 4.60 | 15.40 | - | - |
| Skia | 7.01 | 14.40 | +52.3% | -6.5% |
| Core_text | 7.01 | 14.40 | +52.3% | -6.5% |
| Pango | 8.64 | 16.32 | +87.7% | +6.0% |
| Harfbuzz | 6.43 | 12.25 | +39.8% | -20.4% |
| Freetype | 4.24 | 18.02 | -7.9% | +17.0% |
| PIL | 4.04 | 6.30 | -12.1% | -59.1% |
| Approximation | 3.56 | 15.84 | -22.5% | +2.9% |

#### 12.0pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.90 | 15.50 | - | - |
| Skia | 7.01 | 14.40 | +79.7% | -7.1% |
| Core_text | 5.41 | 13.30 | +38.6% | -14.2% |
| Pango | 8.64 | 16.32 | +121.4% | +5.3% |
| Harfbuzz | 6.13 | 12.25 | +57.1% | -21.0% |
| Freetype | 3.85 | 18.02 | -1.3% | +16.3% |
| PIL | 3.85 | 6.30 | -1.3% | -59.4% |
| Approximation | 3.24 | 15.84 | -16.9% | +2.2% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 13.40 | 15.50 | - | - |
| Skia | 14.70 | 14.40 | +9.7% | -7.1% |
| Core_text | 12.01 | 13.30 | -10.4% | -14.2% |
| Pango | 18.18 | 16.32 | +35.7% | +5.3% |
| Harfbuzz | 14.28 | 12.25 | +6.6% | -21.0% |
| Freetype | 15.40 | 18.02 | +14.9% | +16.3% |
| PIL | 16.50 | 6.30 | +23.1% | -59.4% |
| Approximation | 12.96 | 15.84 | -3.3% | +2.2% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 51.70 | 15.50 | - | - |
| Skia | 59.51 | 14.40 | +15.1% | -7.1% |
| Core_text | 46.84 | 13.30 | -9.4% | -14.2% |
| Pango | 70.70 | 16.32 | +36.8% | +5.3% |
| Harfbuzz | 57.81 | 12.25 | +11.8% | -21.0% |
| Freetype | 61.60 | 18.02 | +19.1% | +16.3% |
| PIL | 63.80 | 7.70 | +23.4% | -50.3% |
| Approximation | 58.32 | 15.84 | +12.8% | +2.2% |

#### 45.7pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 15.10 | 58.70 | - | - |
| Skia | 26.69 | 54.84 | +76.7% | -6.6% |
| Core_text | 26.69 | 54.84 | +76.7% | -6.6% |
| Pango | 32.62 | 62.00 | +116.0% | +5.6% |
| Harfbuzz | 24.50 | 49.11 | +62.2% | -16.3% |
| Freetype | 15.13 | 51.50 | +0.2% | -12.3% |
| PIL | 14.44 | 66.00 | -4.4% | +12.4% |
| Approximation | 13.57 | 60.32 | -10.1% | +2.8% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 50.80 | 58.70 | - | - |
| Skia | 56.00 | 54.84 | +10.2% | -6.6% |
| Core_text | 56.00 | 54.84 | +10.2% | -6.6% |
| Pango | 68.68 | 62.00 | +35.2% | +5.6% |
| Harfbuzz | 57.12 | 49.11 | +12.4% | -16.3% |
| Freetype | 64.13 | 51.50 | +26.2% | -12.3% |
| PIL | 63.53 | 68.00 | +25.0% | +15.8% |
| Approximation | 54.29 | 60.32 | +6.9% | +2.8% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 211.90 | 58.70 | - | - |
| Skia | 226.62 | 54.84 | +6.9% | -6.6% |
| Core_text | 226.62 | 54.84 | +6.9% | -6.6% |
| Pango | 267.65 | 62.00 | +26.3% | +5.6% |
| Harfbuzz | 231.15 | 49.11 | +9.1% | -16.3% |
| Freetype | 260.15 | 51.50 | +22.8% | -12.3% |
| PIL | 250.64 | 86.00 | +18.3% | +46.5% |
| Approximation | 244.31 | 60.32 | +15.3% | +2.8% |

#### 45.7pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 194.20 | 58.90 | - | - |
| Skia | 226.62 | 54.84 | +16.7% | -6.9% |
| Core_text | 178.38 | 52.25 | -8.1% | -11.3% |
| Pango | 267.65 | 62.00 | +37.8% | +5.3% |
| Harfbuzz | 220.14 | 49.11 | +13.4% | -16.6% |
| Freetype | 236.50 | 51.50 | +21.8% | -12.6% |
| PIL | 238.70 | 86.00 | +22.9% | +46.0% |
| Approximation | 222.10 | 60.32 | +14.4% | +2.4% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 48.40 | 58.90 | - | - |
| Skia | 56.00 | 54.84 | +15.7% | -6.9% |
| Core_text | 45.75 | 52.25 | -5.5% | -11.3% |
| Pango | 68.68 | 62.00 | +41.9% | +5.3% |
| Harfbuzz | 54.40 | 49.11 | +12.4% | -16.6% |
| Freetype | 58.30 | 51.50 | +20.5% | -12.6% |
| PIL | 60.50 | 68.00 | +25.0% | +15.4% |
| Approximation | 49.36 | 60.32 | +2.0% | +2.4% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 12.50 | 58.90 | - | - |
| Skia | 26.69 | 54.84 | +113.5% | -6.9% |
| Core_text | 20.59 | 52.25 | +64.7% | -11.3% |
| Pango | 32.62 | 62.00 | +161.0% | +5.3% |
| Harfbuzz | 23.33 | 49.11 | +86.7% | -16.6% |
| Freetype | 13.75 | 51.50 | +10.0% | -12.6% |
| PIL | 13.75 | 66.00 | +10.0% | +12.1% |
| Approximation | 12.34 | 60.32 | -1.3% | +2.4% |

### Helsinki Narrow Font

#### 8.0pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 31.20 | 10.30 | - | - |
| Skia | 29.88 | 9.60 | -4.2% | -6.8% |
| Core_text | 29.88 | 9.60 | -4.2% | -6.8% |
| Pango | 51.94 | 11.52 | +66.5% | +11.8% |
| Harfbuzz | 29.28 | 8.17 | -6.2% | -20.7% |
| Freetype | 33.00 | 17.48 | +5.8% | +69.7% |
| PIL | 30.45 | 5.60 | -2.4% | -45.6% |
| Approximation | 31.68 | 10.56 | +1.5% | +2.5% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 8.10 | 10.30 | - | - |
| Skia | 7.66 | 9.60 | -5.4% | -6.8% |
| Core_text | 7.66 | 9.60 | -5.4% | -6.8% |
| Pango | 12.74 | 11.52 | +57.3% | +11.8% |
| Harfbuzz | 7.51 | 8.17 | -7.3% | -20.7% |
| Freetype | 8.80 | 17.48 | +8.6% | +69.7% |
| PIL | 8.40 | 4.20 | +3.7% | -59.2% |
| Approximation | 7.04 | 10.56 | -13.1% | +2.5% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 2.90 | 10.30 | - | - |
| Skia | 3.83 | 9.60 | +32.1% | -6.8% |
| Core_text | 3.83 | 9.60 | +32.1% | -6.8% |
| Pango | 5.59 | 11.52 | +92.6% | +11.8% |
| Harfbuzz | 3.38 | 8.17 | +16.5% | -20.7% |
| Freetype | 2.20 | 17.48 | -24.1% | +69.7% |
| PIL | 2.10 | 4.20 | -27.6% | -59.2% |
| Approximation | 1.76 | 10.56 | -39.3% | +2.5% |

#### 8.0pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 2.50 | 10.30 | - | - |
| Skia | 3.83 | 9.60 | +53.2% | -6.8% |
| Core_text | 2.79 | 9.00 | +11.6% | -12.6% |
| Pango | 5.59 | 11.52 | +123.4% | +11.8% |
| Harfbuzz | 3.22 | 8.17 | +28.7% | -20.7% |
| Freetype | 2.00 | 17.48 | -20.0% | +69.7% |
| PIL | 2.00 | 4.20 | -20.0% | -59.2% |
| Approximation | 1.60 | 10.56 | -36.0% | +2.5% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 7.70 | 10.30 | - | - |
| Skia | 7.66 | 9.60 | -0.5% | -6.8% |
| Core_text | 6.20 | 9.00 | -19.5% | -12.6% |
| Pango | 11.76 | 11.52 | +52.7% | +11.8% |
| Harfbuzz | 7.15 | 8.17 | -7.1% | -20.7% |
| Freetype | 8.00 | 17.48 | +3.9% | +69.7% |
| PIL | 8.00 | 4.20 | +3.9% | -59.2% |
| Approximation | 6.40 | 10.56 | -16.9% | +2.5% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 28.60 | 10.30 | - | - |
| Skia | 29.88 | 9.60 | +4.5% | -6.8% |
| Core_text | 24.19 | 9.00 | -15.4% | -12.6% |
| Pango | 45.08 | 11.52 | +57.6% | +11.8% |
| Harfbuzz | 27.88 | 8.17 | -2.5% | -20.7% |
| Freetype | 30.00 | 17.48 | +4.9% | +69.7% |
| PIL | 29.00 | 5.60 | +1.4% | -45.6% |
| Approximation | 28.80 | 10.56 | +0.7% | +2.5% |

#### 10.0pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.40 | 12.90 | - | - |
| Skia | 4.79 | 12.00 | +40.8% | -7.0% |
| Core_text | 4.79 | 12.00 | +40.8% | -7.0% |
| Pango | 6.52 | 14.40 | +91.7% | +11.6% |
| Harfbuzz | 4.22 | 10.21 | +24.2% | -20.9% |
| Freetype | 2.75 | 17.48 | -19.1% | +35.5% |
| PIL | 2.62 | 4.90 | -22.8% | -62.0% |
| Approximation | 2.20 | 13.20 | -35.3% | +2.3% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.90 | 12.90 | - | - |
| Skia | 9.58 | 12.00 | -3.3% | -7.0% |
| Core_text | 9.58 | 12.00 | -3.3% | -7.0% |
| Pango | 14.70 | 14.40 | +48.5% | +11.6% |
| Harfbuzz | 9.39 | 10.21 | -5.2% | -20.9% |
| Freetype | 11.00 | 17.48 | +11.1% | +35.5% |
| PIL | 10.50 | 4.90 | +6.1% | -62.0% |
| Approximation | 8.80 | 13.20 | -11.1% | +2.3% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 38.80 | 12.90 | - | - |
| Skia | 37.34 | 12.00 | -3.8% | -7.0% |
| Core_text | 37.34 | 12.00 | -3.8% | -7.0% |
| Pango | 59.78 | 14.40 | +54.1% | +11.6% |
| Harfbuzz | 36.60 | 10.21 | -5.7% | -20.9% |
| Freetype | 41.80 | 17.48 | +7.7% | +35.5% |
| PIL | 37.80 | 6.30 | -2.6% | -51.2% |
| Approximation | 39.60 | 13.20 | +2.1% | +2.3% |

#### 10.0pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 35.60 | 12.90 | - | - |
| Skia | 37.34 | 12.00 | +4.9% | -7.0% |
| Core_text | 30.23 | 10.80 | -15.1% | -16.3% |
| Pango | 54.88 | 14.40 | +54.2% | +11.6% |
| Harfbuzz | 34.86 | 10.21 | -2.1% | -20.9% |
| Freetype | 38.00 | 17.48 | +6.7% | +35.5% |
| PIL | 36.00 | 6.30 | +1.1% | -51.2% |
| Approximation | 36.00 | 13.20 | +1.1% | +2.3% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 9.40 | 12.90 | - | - |
| Skia | 9.58 | 12.00 | +1.9% | -7.0% |
| Core_text | 7.75 | 10.80 | -17.5% | -16.3% |
| Pango | 13.72 | 14.40 | +46.0% | +11.6% |
| Harfbuzz | 8.94 | 10.21 | -4.9% | -20.9% |
| Freetype | 10.00 | 17.48 | +6.4% | +35.5% |
| PIL | 10.00 | 4.90 | +6.4% | -62.0% |
| Approximation | 8.00 | 13.20 | -14.9% | +2.3% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 2.90 | 12.90 | - | - |
| Skia | 4.79 | 12.00 | +65.1% | -7.0% |
| Core_text | 3.49 | 10.80 | +20.3% | -16.3% |
| Pango | 6.52 | 14.40 | +124.7% | +11.6% |
| Harfbuzz | 4.02 | 10.21 | +38.7% | -20.9% |
| Freetype | 2.50 | 17.48 | -13.8% | +35.5% |
| PIL | 2.50 | 4.90 | -13.8% | -62.0% |
| Approximation | 2.00 | 13.20 | -31.0% | +2.3% |

#### 12.0pt bold

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.90 | 15.40 | - | - |
| Skia | 5.75 | 14.40 | +47.3% | -6.5% |
| Core_text | 5.75 | 14.40 | +47.3% | -6.5% |
| Pango | 8.38 | 16.32 | +114.8% | +6.0% |
| Harfbuzz | 5.07 | 12.25 | +30.0% | -20.4% |
| Freetype | 2.75 | 17.48 | -29.5% | +13.5% |
| PIL | 2.62 | 6.30 | -32.7% | -59.1% |
| Approximation | 2.64 | 15.84 | -32.3% | +2.9% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.70 | 15.40 | - | - |
| Skia | 11.49 | 14.40 | -1.8% | -6.5% |
| Core_text | 11.49 | 14.40 | -1.8% | -6.5% |
| Pango | 18.62 | 16.32 | +59.1% | +6.0% |
| Harfbuzz | 11.26 | 12.25 | -3.7% | -20.4% |
| Freetype | 11.00 | 17.48 | -6.0% | +13.5% |
| PIL | 11.55 | 6.30 | -1.3% | -59.1% |
| Approximation | 10.56 | 15.84 | -9.7% | +2.9% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 46.30 | 15.40 | - | - |
| Skia | 44.81 | 14.40 | -3.2% | -6.5% |
| Core_text | 44.81 | 14.40 | -3.2% | -6.5% |
| Pango | 74.48 | 16.32 | +60.9% | +6.0% |
| Harfbuzz | 43.92 | 12.25 | -5.1% | -20.4% |
| Freetype | 44.00 | 17.48 | -5.0% | +13.5% |
| PIL | 45.15 | 7.70 | -2.5% | -50.0% |
| Approximation | 47.52 | 15.84 | +2.6% | +2.9% |

#### 12.0pt normal

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 42.50 | 15.50 | - | - |
| Skia | 44.81 | 14.40 | +5.4% | -7.1% |
| Core_text | 36.28 | 12.60 | -14.6% | -18.7% |
| Pango | 68.60 | 16.32 | +61.4% | +5.3% |
| Harfbuzz | 41.83 | 12.25 | -1.6% | -21.0% |
| Freetype | 40.00 | 17.48 | -5.9% | +12.8% |
| PIL | 43.00 | 7.70 | +1.2% | -50.3% |
| Approximation | 43.20 | 15.84 | +1.6% | +2.2% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 11.10 | 15.50 | - | - |
| Skia | 11.49 | 14.40 | +3.5% | -7.1% |
| Core_text | 9.30 | 12.60 | -16.2% | -18.7% |
| Pango | 17.64 | 16.32 | +58.9% | +5.3% |
| Harfbuzz | 10.73 | 12.25 | -3.4% | -21.0% |
| Freetype | 10.00 | 17.48 | -9.9% | +12.8% |
| PIL | 11.00 | 6.30 | -0.9% | -59.4% |
| Approximation | 9.60 | 15.84 | -13.5% | +2.2% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 3.40 | 15.50 | - | - |
| Skia | 5.75 | 14.40 | +69.0% | -7.1% |
| Core_text | 4.19 | 12.60 | +23.1% | -18.7% |
| Pango | 8.38 | 16.32 | +146.4% | +5.3% |
| Harfbuzz | 4.83 | 12.25 | +42.0% | -21.0% |
| Freetype | 2.50 | 17.48 | -26.5% | +12.8% |
| PIL | 2.50 | 6.30 | -26.5% | -59.4% |
| Approximation | 2.40 | 15.84 | -29.4% | +2.2% |

#### 45.7pt bold

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 174.00 | 58.70 | - | - |
| Skia | 170.67 | 54.84 | -1.9% | -6.6% |
| Core_text | 170.67 | 54.84 | -1.9% | -6.6% |
| Pango | 281.26 | 62.00 | +61.6% | +5.6% |
| Harfbuzz | 167.25 | 49.11 | -3.9% | -16.3% |
| Freetype | 179.30 | 49.94 | +3.0% | -14.9% |
| PIL | 168.00 | 86.00 | -3.4% | +46.5% |
| Approximation | 180.97 | 60.32 | +4.0% | +2.8% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 41.80 | 58.70 | - | - |
| Skia | 43.77 | 54.84 | +4.7% | -6.6% |
| Core_text | 43.77 | 54.84 | +4.7% | -6.6% |
| Pango | 69.58 | 62.00 | +66.5% | +5.6% |
| Harfbuzz | 42.89 | 49.11 | +2.6% | -16.3% |
| Freetype | 46.20 | 49.94 | +10.5% | -14.9% |
| PIL | 43.05 | 68.00 | +3.0% | +15.8% |
| Approximation | 40.22 | 60.32 | -3.8% | +2.8% |

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 12.60 | 58.70 | - | - |
| Skia | 21.88 | 54.84 | +73.7% | -6.6% |
| Core_text | 21.88 | 54.84 | +73.7% | -6.6% |
| Pango | 31.65 | 62.00 | +151.2% | +5.6% |
| Harfbuzz | 19.30 | 49.11 | +53.2% | -16.3% |
| Freetype | 11.55 | 49.94 | -8.3% | -14.9% |
| PIL | 11.03 | 66.00 | -12.5% | +12.4% |
| Approximation | 10.05 | 60.32 | -20.2% | +2.8% |

#### 45.7pt normal

**Text: `1`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 10.40 | 58.90 | - | - |
| Skia | 21.88 | 54.84 | +110.4% | -6.9% |
| Core_text | 15.94 | 49.50 | +53.3% | -16.0% |
| Pango | 31.65 | 62.00 | +204.4% | +5.3% |
| Harfbuzz | 18.38 | 49.11 | +76.8% | -16.6% |
| Freetype | 10.50 | 49.94 | +1.0% | -15.2% |
| PIL | 10.50 | 66.00 | +1.0% | +12.1% |
| Approximation | 9.14 | 60.32 | -12.1% | +2.4% |

**Text: `ab`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 39.80 | 58.90 | - | - |
| Skia | 43.77 | 54.84 | +10.0% | -6.9% |
| Core_text | 35.43 | 49.50 | -11.0% | -16.0% |
| Pango | 66.64 | 62.00 | +67.4% | +5.3% |
| Harfbuzz | 40.85 | 49.11 | +2.6% | -16.6% |
| Freetype | 42.00 | 49.94 | +5.5% | -15.2% |
| PIL | 41.00 | 68.00 | +3.0% | +15.4% |
| Approximation | 36.56 | 60.32 | -8.1% | +2.4% |

**Text: `abcdefghi`**

| Technique | Width (pt) | Height (pt) | Width Diff (%) | Height Diff (%) |
| --- | --- | --- | --- | --- |
| P-touch Reference | 159.40 | 58.90 | - | - |
| Skia | 170.67 | 54.84 | +7.1% | -6.9% |
| Core_text | 138.16 | 49.50 | -13.3% | -16.0% |
| Pango | 259.70 | 62.00 | +62.9% | +5.3% |
| Harfbuzz | 159.29 | 49.11 | -0.1% | -16.6% |
| Freetype | 163.00 | 49.94 | +2.3% | -15.2% |
| PIL | 160.00 | 86.00 | +0.4% | +46.0% |
| Approximation | 164.52 | 60.32 | +3.2% | +2.4% |

## Visualizations

### Width Difference Distribution

![Width Difference Boxplot](plots/width_diff_boxplot.png)

### Height Difference Distribution

![Height Difference Boxplot](plots/height_diff_boxplot.png)