###########################################################
#                Charge Transfer Alchemist                #
#               <------------------------->               #
# A Python Program To Generate Input Files for DFT & TDDFT#
# Calculations Concerning Long Range Charge Transfer      #
# Properties of Molecules                                 #
#                                                         #
# Developer: Ajay Khanna                                  #
# Place: UC Merced                                        #
# Project: Fluorescence Resonance Energy Transfer         #
# Data: Oct.15.2023                                       #
###########################################################

"""
The above Python code defines a script that generates quantum
mechanical input files for a molecular simulation using provided
configuration parameters and atomic coordinates.

The generated files are:
    1. Ground State(Gs) Optimization and Frequency Calculation
    2. Vertical Excitation Energy On Optimized Gs Calculation
    3. Excited State(Ex) Optimization and Frequency Calculation
    4. Vertical Deexcitation Energy On Optimized Ex Calculation
    5. Franck-Condon Absorption Spectra For Optimized Gs and Ex
    6. Franck-Condon Emission Spectra For Optimized Gs and Ex

:param filename: The `filename` parameter is used to specify the
path to the configuration JSON file or the coordinates file.

By default, it is set to "config.json" for the configuration file
and "coordinates.xyz" for the coordinates file. However, you can
provide a different file path if needed, defaults to config.json
    :type filename: str (optional)
    :return: The code does not explicitly return any values.
    However, the `load_configuration()` and
    `load_coordinates()` functions return a dictionary and
    a string respectively, if successful.
"""

import json
import logging
import argparse

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def load_configuration(filename: str = "config.json") -> dict:
    """
    Load configuration parameters from a JSON file.
    
    Parameters:
    - filename (str): The path to the configuration JSON file.
    
    Returns:
    - dict: Configuration parameters.
    """
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading configuration file: {e}")
        return None

def load_coordinates(filename: str = "coordinates.xyz") -> str:
    """
    Load atomic coordinates from a file.
    
    Parameters:
    - filename (str): The path to the coordinates file.
    
    Returns:
    - str: String containing atomic coordinates.
    """
    try:
        with open(filename, 'r') as f:
            next(f)
            next(f)
            coordinates = f.read()
        return coordinates
    except Exception as e:
        logging.error(f"Error loading coordinates file: {e}")
        return None

def write_input_files(omega_values: list, config: dict, coordinates: str):
    """
    Generate input files using provided omega values, configuration, and coordinates.
    
    Parameters:
    - omega_values (list): List of omega values for input file generation.
    - config (dict): Configuration parameters.
    - coordinates (str): Atomic coordinates for the molecule.
    """

    file_contents = {
        config['gs_filename']: config['gs_content'].format(coordinates=coordinates, omega="{omega}", filename=config['gs_filename']),
        config['ex_filename']: config['ex_content'].format(gs_filename=config['gs_filename'], omega="{omega}", filename=config['ex_filename']),
        config['vee_filename']: config['vee_content'].format(gs_filename=config['gs_filename'], omega="{omega}", filename=config['vee_filename']),
        config['vde_filename']: config['vde_content'].format(ex_filename=config['ex_filename'], omega="{omega}", filename=config['vde_filename']),
        config['abs_vibronic_filename']: config['abs_vib_content'],
        config['ems_vibronic_filename']: config['ems_vib_content']
    }

# The code block you provided is a nested loop that generates and writes input files for different
# omega values.
    for omega in omega_values:
        for filename, content in file_contents.items():
            try:
                with open(f'{filename}_w{omega}.com', 'w') as f:
                    f.write(content.format(omega=omega, gs_filename=config['gs_filename'], ex_filename=config['ex_filename']))
                logging.info(f"Written {filename}_w{omega}.com successfully!")
            except KeyError as e:
                logging.error(f"Missing placeholder in the template: {e}")
            except Exception as e:
                logging.error(f"Error writing to {filename}_w{omega}.com: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate Quantum Mechanical Input Files")
    parser.add_argument('--omega_start', type=int, default=100000000, help='Start value for omega')
    parser.add_argument('--omega_end', type=int, default=410000000, help='End value for omega')
    parser.add_argument('--omega_step', type=int, default=10000000, help='Step value for omega')
    args = parser.parse_args()

    omega_values = [f'0{w}' for w in range(args.omega_start, args.omega_end, args.omega_step)]
    
    config = load_configuration()
    if config is None:
        return
    
    coordinates = load_coordinates()
    if coordinates is None:
        return
        
    write_input_files(omega_values, config, coordinates)

if __name__ == '__main__':
    main()
