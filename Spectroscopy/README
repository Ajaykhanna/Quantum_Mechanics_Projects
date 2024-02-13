# Spectroscopy Data Transformation :microscope: :chart_with_upwards_trend:

This Python code efficiently transforms experimental spectra measured in the wavelength domain into:
- :zap: **Frequency Domain**
- :rainbow: **Lineshape in Frequency Domain**

These transformations are crucial for an accurate comparison between experimental and computed absorption and emission/fluorescence spectra. For more insights, please refer to the following literature:
1. :books: [Insights for an Accurate Comparison of Computational Data to Experimental Absorption and Emission Spectra: Beyond the Vertical Transition Approximation](dx.doi.org/10.1021/ct301107m) | J. Chem. Theory Comput. 2013, 9, 2072−2082.
2. :bulb: Valeur, B. _Molecular Fluorescence: Principles and Applications_; Wiley-VCH: Weinheim, 2001; pp 51.
3. :microscope: Karunakaran, V. et al. J. Phys. Chem. A 2007, 111, 10944−10952.

## How to Run? :computer:

Provide the `input_filename`, `spectroscopy_type` ('abs' or 'ems'), and `output_filename`:

```python
python3 transform_exp_data.py
Input filename ?: original_exp_abs_du_nbd_dmso.csv
Spec Type: 'abs' or 'ems' ?: abs
Output filename ?: abs_test
```
Spectra Normalization :straight_ruler:
Normalization of the spectra can be achieved in two ways: by area or maximum intensity. Use the following Python snippet for normalization:

```python
import numpy as np
from scipy import integrate

def normalization(x, y, kind="max"):
    """
    Normalizes a dataset using either the maximum value or the area under the curve.
    :param x: X-values of the data points (1-dimensional array or list).
    :param y: Y-values for normalization (1-dimensional numerical array).
    :param kind: Type of normalization ('max' for maximum value, any other value for area under the curve).
    :return: Normalized values of 'y'.
    """
    if kind == "max":
        max_y = np.max(y)
        return y / max_y
    else:
        area_y = integrate.simps(y, x)
        return y / area_y
```
