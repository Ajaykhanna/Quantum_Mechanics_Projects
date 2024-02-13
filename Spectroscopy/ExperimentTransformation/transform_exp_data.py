""" Contact Information
@email: akhanna2@ucmerced.edu || quantphobia@gmail.com 
@lab: Dr. Isborn
@place: UC Merced
@date: Mar.30.2022
@author: Ajay Khanna |Git: Ajaykhanna|Twitter: @samdig| LinkedIn: ajay-khanna

The above Python code is a program that transforms experimental spectra from the wavelength domain
to the frequency domain or performs a lineshape transformation based on the spectroscopy type
(absorption or emission) and saves the transformed data to CSV files.

:param filename: The `filename` parameter is the name of the file to save the data to. It should be
a string
"""

import numpy as np

# Conversion factor from nm to eV
nm_to_ev = 4.135667696e-15 * 2.99792458e08 * 1.0e09

def save_file(filename, *data_arrays):
    """
    Save data to a CSV file.
    - filename: Name of the file to save.
    - data_arrays: Data arrays to save.
    """
    header = "Energy(eV), Intensity(arb units)"
    data = np.column_stack(data_arrays)
    np.savetxt(filename, data, fmt=["%1.6f", "%1.6f"], header=header, delimiter=",")

def intensity_lambda_to_frequency(x, y, spec_type="abs"):
    """
    Transform intensity data from wavelength to frequency domain.
    - x: Wavelength or wavenumber values.
    - y: Intensity values.
    - spec_type: Type of spectrum ('abs' for absorption, others for emission).
    """
    if spec_type == "abs":
        return y
    else:
        energy_squared_reciprocal = 1.0 / x**2
        return energy_squared_reciprocal * y

def lineshape_transform(x, y, spec_type="abs"):
    """
    Transform lineshape based on spectroscopy type.
    - x: Wavelength or wavenumber values.
    - y: Intensity values.
    - spec_type: Type of spectroscopy ('abs' or 'ems').
    """
    if spec_type == "abs":
        return (1.0 / x) * y
    elif spec_type == "ems":
        return (1.0 / x**5) * y
    else:
        raise ValueError("Invalid spectroscopy type")

# Program Banner
print("Spectroscopy Data Transformation Program")
print("Converts experimental spectra from wavelength to frequency domain.")

# Main Program
try:
    input_filename = input("Input filename: ")
    spec_type = input("Spec Type ('abs' or 'ems'): ")
    output_filename = input("Output filename: ")

    exp_data = np.loadtxt(input_filename, delimiter=",")
    exp_x = nm_to_ev / exp_data[:, 0]
    exp_y = exp_data[:, 1]

    print("Performing Transformation...")
    frequency_domain_y = intensity_lambda_to_frequency(exp_x, exp_y, spec_type)
    lineshape_y = lineshape_transform(exp_x, exp_y, spec_type)

    print("Saving Data...")
    save_file(f'exp_{output_filename}_freq_domain.csv', exp_x, frequency_domain_y)
    save_file(f'exp_{output_filename}_lineshape.csv', exp_x, lineshape_y)
    print("Done!")

except Exception as e:
    print(f"An error occurred: {e}")
