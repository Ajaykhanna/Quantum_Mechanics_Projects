# -*- coding: utf-8 -*-
"""
Input/Output utilities for Chef-TeraChem script.

Includes functions for:
- Printing headers
- Getting validated user input
- Loading solvent data from JSON
- Writing files (TeraChem input, XYZ)
"""

import sys
import json
import os
from pathlib import Path
from typing import Dict, Optional, Any, Callable

# --- Add project root to sys.path ---
try:
    script_path = Path(__file__).resolve()
    project_root = script_path.parent  # Go up two levels
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"DEBUG: Added project root to sys.path: {project_root}")
except NameError:
    print(
        "Warning: Could not automatically determine project root via __file__.",
        file=sys.stderr,
    )

# Import configuration constants
import config


def print_header() -> None:
    """Prints the script header and developer information."""
    print("*********| Chef-TeraChem | **********")
    print(" A python script to create on-demand TeraChem input files.")
    print(f" Version: {config.__version__} (Refactored)")
    print(f" Based on original script by: {config.__author__.split('(')[0].strip()}")
    print(f" Original Date: {config.__date__.split(',')[0].strip()}")
    print(f" Lab: {config.__lab__}")
    print("-" * 40)
    print("Current Calculation Options:")
    for code, (name, _) in config.CALC_TYPE_MAP.items():
        state = "Ground State" if "gs" in name else "Excited State"
        calc = name.split("_")[1].capitalize()
        print(f"  {code}: {state} {calc}")
    print("-" * 40)


def get_validated_input(
    prompt: str,
    input_type: type = str,
    validation_func: Optional[Callable[[Any], bool]] = None,
) -> Any:
    """
    Prompts the user for input, validates it, and converts to the desired type.

    Args:
        prompt: The message to display to the user.
        input_type: The desired type of the output (e.g., str, int, float).
        validation_func: An optional function to perform custom validation.
                         Should accept the converted input and return True if valid,
                         False otherwise.

    Returns:
        The validated user input, converted to input_type.

    Raises:
        SystemExit: If validation fails repeatedly, input type is invalid,
                    or user interrupts.
    """
    while True:
        try:
            user_input_str = input(prompt).strip()
            if not user_input_str:  # Handle empty input if needed, maybe reprompt
                print("Input cannot be empty. Please try again.")
                continue

            # Perform type conversion
            converted_input = input_type(user_input_str)

            # Perform custom validation if provided
            if validation_func:
                if validation_func(converted_input):
                    return converted_input
                else:
                    print("Invalid input based on validation rules. Please try again.")
            else:
                # No custom validation needed, return converted input
                return converted_input

        except ValueError:
            print(f"Invalid input format. Please enter a valid {input_type.__name__}.")
        except EOFError:
            print("\nInput stream closed unexpectedly. Exiting.")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user. Exiting.")
            sys.exit(1)


def load_solvents(filename: str = config.DEFAULT_SOLVENT_FILE) -> Dict[str, float]:
    """
    Loads solvent dielectric constants from a JSON file located
    relative to this script file.

    Args:
        filename: The name of the JSON file (e.g., "solvents.json").

    Returns:
        A dictionary mapping solvent names (lowercase) to dielectric constants.

    Raises:
        SystemExit: If the file cannot be found or read, or if JSON is invalid.
    """
    # --- Modification Start ---
    # Get the directory where io_utils.py resides
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the full path to the solvent file
    filepath = os.path.join(script_dir, filename)
    # --- Modification End ---

    print(
        f"Attempting to load solvent data from: {filepath}"
    )  # Optional: for debugging

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            solvents = json.load(f)
            # Ensure keys are lowercase for consistent lookup
            return {k.lower(): v for k, v in solvents.items()}
    except FileNotFoundError:
        print(f"Error: Solvent data file not found at '{filepath}'.")
        # The message below might be less relevant now, but keep for context
        # print("Please ensure 'solvents.json' is in the same directory as the script.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from '{filepath}'. Check file format.")
        sys.exit(1)
    except IOError as e:
        print(f"Error: Could not read solvent file '{filepath}'. Reason: {e}")
        sys.exit(1)


def write_output_file(filename: str, content: str) -> None:
    """
    Writes the generated content to the specified file.

    Args:
        filename: The name of the file to write.
        content: The string content to write to the file.

    Raises:
        SystemExit: If the file cannot be written.
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\nSuccessfully generated file: '{filename}'")
    except IOError as e:
        print(f"\nError: Could not write file '{filename}'. Reason: {e}")
        sys.exit(1)


def generate_h2o_xyz(filepath: str = config.DEFAULT_XYZ_FILENAME) -> None:
    """
    Generates a simple h2o.xyz file for default calculations.

    Args:
        filepath: The path where the h2o.xyz file should be created/overwritten.
    """
    print(f"Generating default coordinate file: '{filepath}'...")
    write_output_file(filepath, config.H2O_XYZ_CONTENT)
