# -*- coding: utf-8 -*-
"""
Configuration constants for Chef-TeraChem script.
"""

from typing import Dict, Tuple

# --- Script Metadata ---
__version__ = "1.2.0"  # Further refactored version
__author__ = "Ajay Khanna (Original), Refactored by AI"
__date__ = "Oct.10.2020 (Original), April 21, 2025 (Refactored)"
__lab__ = "Dr. Isborb's Lab | UC-Merced"

# --- Calculation Type Mapping ---
# Maps integer codes to (filename_suffix, terachem_run_keyword)
CALC_TYPE_MAP: Dict[int, Tuple[str, str]] = {
    0: ("gs_energy", "energy"),
    1: ("gs_opt", "minimize"),
    2: ("gs_freq", "frequencies"),
    3: ("ex_energy", "energy"),
    4: ("ex_opt", "minimize"),
    5: ("ex_freq", "frequencies"),
}

# Calculation types requiring excited state ('cis') options
EXCITED_STATE_CALCS: Tuple[int, ...] = (3, 4, 5)

# --- Default Calculation Parameters ---
DEFAULT_MOL_NAME: str = "h2o"
DEFAULT_CALC_TYPE: int = 0  # Ground State Energy
DEFAULT_FUNCTIONAL: str = "b3lyp"
DEFAULT_BASIS_SET: str = "6-31g*"
DEFAULT_CHARGE: int = 0
DEFAULT_MULTIPLICITY: int = 1
DEFAULT_USE_SOLVENT: bool = False
DEFAULT_SOLVENT_NAME: str = "water" # Default if solvent needed but not specified

# --- Default TeraChem Settings ---
DEFAULT_GPUS: int = 4
DEFAULT_CIS_NUMSTATES: int = 6
DEFAULT_CIS_GUESVECS_FACTOR: int = 2 # cisguessvecs = factor * cisnumstates
DEFAULT_CISTARGET: int = 1

# --- File Paths ---
DEFAULT_SOLVENT_FILE: str = "solvents.json"
DEFAULT_XYZ_FILENAME: str = f"{DEFAULT_MOL_NAME}.xyz"

# --- Default H2O Coordinates (XYZ format string) ---
H2O_XYZ_CONTENT: str = """\
3
Water molecule for default calculation
O    0.00000000    0.00000000    0.11730000
H    0.00000000    0.75720000   -0.46920000
H    0.00000000   -0.75720000   -0.46920000
"""
