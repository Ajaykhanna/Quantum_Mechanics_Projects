###########################################################
#                 Nuclear Enemble Spectra                 #
#               <------------------------->               #
# A Python Program To Generate Nuclear Ensemble Sepctra   #
# From DFT and TDDFT Vertical Excitation/De-excitation    #
# Calculations                                            #
#                                                         #
#                                                         #
# Developer: Ajay Khanna                                  #
# Place: UC Merced | Isborn Lab                           #
# Project: Fluorescence Resonance Energy Transfer         #
# Date: Aug.15.2019                                       #
###########################################################

import logging
import argparse
import numpy as np
from scipy import integrate

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Constant and Conversion Factors
INVCM_TO_EV = float(0.00012398)


# -------------------
# Required Functions
# -------------------
def load_exception_energies_transition_dipole_moments(filename: str) -> np.array:
    """
    This function loads excitation energies and
    transition dipole moments from a file.

    :param filename: The filename parameter is a string that represents the name of the file from which
    the data will be loaded
    :type filename: str
    :return: two arrays: the excitation energies and the transition dipole moments.
    """
    try:
        data = np.loadtxt(filename, delimiter=",")
        return data[:, 0], data[:, 1:]
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
        exit()
    except Exception as e:
        print(f"An error occurred: {e}")
        exit()


def calculate_ensemble_spectra(
    omega: int,
    excitation_energies: np.array,
    transition_dipole_moments: np.array,
    energy_grid: np.array,
    gaussian_width: float,
) -> np.array:
    """
    Calculates the ensemble spectra for a given set of excitation energies and transition dipole moments.

    Parameters:
    omega (int): Energy scaling factor, where 1 indicates absorption and 3 indicates emission.
    excitation_energies (np.array): Array of excitation or de-excitation energies.
    transition_dipole_moments (np.array): Array of transition dipole moments.
    energy_grid (np.array): Energy grid or window over which intensities are calculated.
    gaussian_width (float): Width of the Gaussian distribution.

    Returns:
    np.array: Calculated ensemble spectra as a 1D numpy array.
    """
    spectra = np.zeros(len(energy_grid))
    for energy, tdm in zip(excitation_energies, transition_dipole_moments):
        scaled_energy = energy**omega
        gaussian_factor = np.exp(
            -((energy_grid - energy) ** 2.0) / (2.0 * gaussian_width**2.0)
        )
        spectra += scaled_energy * tdm**2 * gaussian_factor

    area_ensemble = integrate.simps(spectra, energy_grid)
    normalized_ens = spectra / area_ensemble

    return normalized_ens


def transform_computed_spectra_to_lineshape(
    spectrum_x: np.array,
    spectrum_y: np.array,
    spectroscopy_type: str = "abs",
    is_gaussian: bool = True,
) -> np.array:
    """
    Transforms a computed spectrum into a lineshape by adjusting the y-values.

    Parameters:
    spectrum_x (np.array): 1D array of x-values (spectrum).
    spectrum_y (np.array): 1D array of y-values (spectrum).
    spectroscopy_type (str): Type of spectroscopy, "abs" (absorption) or "ems" (emission). Default is "abs".
    is_gaussian (bool): If True, apply Gaussian16 transformation. Default is True.

    Returns:
    np.array: Transformed 1D array of y-values (lineshape).
    """
    assert len(spectrum_x) == len(
        spectrum_y
    ), "x and y arrays must be of the same length."

    if spectroscopy_type == "abs":
        transformed_y = spectrum_y / spectrum_x
    elif spectroscopy_type == "ems":
        power = 4 if is_gaussian else 3
        transformed_y = spectrum_y / spectrum_x**power
    else:
        raise ValueError("Invalid spectroscopy type. Choose 'abs' or 'ems'.")

    return transformed_y


def main():
    parser = argparse.ArgumentParser(description="Nuclear Ensemble Spectra Generator")
    parser.add_argument(
        "--exictation_energies",
        type=str,
        help="Path to the excitation energies and transition files(.csv)",
    )
    parser.add_argument(
        "--omega",
        type=int,
        default=1,
        help="Omega value: 1 for absorption, 3 for emission",
    )
    parser.add_argument(
        "--energy_grid",
        type=float,
        required=False,
        nargs="+",
        help="Energy grid for the spectra (eV)",
    )
    parser.add_argument(
        "--fwhm",
        type=float,
        default=600.0,
        required=False,
        help="FWHM value for Gaussian Broadening, default is 600.0 cm-1",
    )
    parser.add_argument(
        "--to_lineshape",
        type=bool,
        default=False,
        required=False,
        help="Transfer to Lineshape?: False (default)",
    )
    args = parser.parse_args()

    # Load excitation energies and transition dipole moments
    omega = args.omega
    gaussian_width = (args.fwhm * INVCM_TO_EV) / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    """
    This line is calculating the standard deviation, often referred
    to as the 'width', of a Gaussian distribution.
    The args.fwhm is the Full Width at Half Maximum (FWHM) of the Gaussian,
    which is a measure of the width of the distribution at half of its maximum value.
    The INVCM_TO_EV is a conversion factor that is used to convert the units of the FWHM
    from inverse centimeters to electron volts (eV).
    The denominator of the equation, 2.0 * np.sqrt(2.0 * np.log(2.0)), is a constant
    derived from the properties of the Gaussian distribution. It is used to convert the
    FWHM to the standard deviation of the Gaussian.
    """
    excitation_energies, transition_dipole_moments = (
        load_exception_energies_transition_dipole_moments(args.exictation_energies)
    )
    energy_grid = (
        np.linspace(args.energy_grid[0], args.energy_grid[1], 26980)
        if args.energy_grid
        else np.linspace(
            excitation_energies.min() - 0.5, excitation_energies.max() + 0.5, 26980
        )  # 0.5eV For Converged Spectra
    )

    # Calculate ensemble spectra
    spectra = calculate_ensemble_spectra(
        omega,
        excitation_energies,
        transition_dipole_moments,
        energy_grid,
        gaussian_width,
    )
    if args.to_lineshape:
        spectroscopy_type = ["abs" if omega == 1 else "ems"]
        spectra_ls = transform_computed_spectra_to_lineshape(
            energy_grid, spectra, spectroscopy_type[0], is_gaussian=False
        )

        np.savetxt(
            "nuclear_ensemble_spectra.csv",
            np.column_stack([energy_grid, spectra, spectra_ls]),
            delimiter=",",
            header="Energy (eV), Intensity, Lineshape",
        )
    else:
        np.savetxt(
            "nuclear_ensemble_spectra.csv",
            np.column_stack([energy_grid, spectra]),
            delimiter=",",
            header="Energy (eV), Intensity",
        )


if __name__ == "__main__":
    main()
