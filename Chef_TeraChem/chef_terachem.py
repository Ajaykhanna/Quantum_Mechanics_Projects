#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Chef-TeraChem: Main script to generate TeraChem input files.

This script orchestrates the process of gathering parameters
(either interactively or using defaults) and generating the
corresponding TeraChem input file.

Usage:
  python chef_terachem.py [--default]

Options:
  --default   Generate a default input file for H2O ground state energy
              (h2o_gs_energy.in) and create h2o.xyz. Skips interactive prompts.
"""

import sys
import argparse
from pathlib import Path

# --- Add project root to sys.path ---
try:
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent  # Go up two levels
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"DEBUG: Added project root to sys.path: {project_root}")
except NameError:
    print(
        "Warning: Could not automatically determine project root via __file__.",
        file=sys.stderr,
    )

# Import modules from the package/directory
import config
import io_utils
import core


def main() -> None:
    """Main function to run the script."""

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Generate TeraChem input files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # Preserve formatting in description
        epilog="Example: python chef_terachem.py --default",  # Add example usage
    )
    parser.add_argument(
        "--default",
        action="store_true",  # Makes it a flag, True if present
        help="Generate default H2O ground state energy input and h2o.xyz.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {config.__version__}",  # Show version from config
    )
    args = parser.parse_args()

    # --- Load Shared Data ---
    # Load solvent data early, needed for both default (potentially) and interactive modes
    # Wrap in try-except in case the file is missing right at the start
    try:
        solvent_data = io_utils.load_solvents(config.DEFAULT_SOLVENT_FILE)
    except SystemExit:
        # Error message already printed by load_solvents
        sys.exit(1)  # Ensure exit if loading fails

    # --- Parameter Acquisition ---
    parameters: dict  # Declare type hint

    if args.default:
        # Generate the default h2o.xyz file
        io_utils.generate_h2o_xyz(config.DEFAULT_XYZ_FILENAME)
        # Get the predefined default parameters
        parameters = core.get_default_parameters()
    else:
        # Interactive mode
        io_utils.print_header()
        parameters = core.get_calculation_parameters(
            solvent_data
        )  # Pass loaded solvent data

    # --- Input File Generation ---
    try:
        input_content = core.generate_terachem_input(parameters)
        output_filename = core.generate_filename(parameters)
        io_utils.write_output_file(output_filename, input_content)

        print("\nTask Completed Successfully.")
        if not args.default:  # Only show this in interactive mode
            print("Consider buying the original developer a beer!")

    except Exception as e:
        # Catch any other unexpected errors during generation/writing
        print(f"\nAn unexpected error occurred during file generation: {e}")
        # Consider adding more specific error handling if needed
        sys.exit(1)


if __name__ == "__main__":
    # Ensure Python 3.6+ for f-strings and type hints
    if sys.version_info < (3, 6):
        print("Error: This script requires Python 3.6 or later.")
        sys.exit(1)
    main()
