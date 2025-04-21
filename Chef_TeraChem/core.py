# -*- coding: utf-8 -*-
"""
Core logic for Chef-TeraChem script.

Includes functions for:
- Gathering calculation parameters (interactive or default)
- Generating TeraChem input file content
- Generating output filenames
"""

from typing import Dict, Any

# Import configuration constants and utility functions
import config
import io_utils


def get_default_parameters() -> Dict[str, Any]:
    """
    Returns a dictionary with parameters for the default H2O calculation.

    Returns:
        A dictionary containing default calculation parameters.
    """
    print("Using default parameters for H2O ground state energy calculation.")
    return {
        "mol_name": config.DEFAULT_MOL_NAME,
        "calc_type": config.DEFAULT_CALC_TYPE,
        "functional": config.DEFAULT_FUNCTIONAL,
        "basis_set": config.DEFAULT_BASIS_SET,
        "charge": config.DEFAULT_CHARGE,
        "multiplicity": config.DEFAULT_MULTIPLICITY,
        "use_solvent": config.DEFAULT_USE_SOLVENT,
        "solvent_name": None,  # No solvent for default gas phase
        "epsilon": None,
        "is_excited_state": config.DEFAULT_CALC_TYPE in config.EXCITED_STATE_CALCS,
        "cis_target": config.DEFAULT_CISTARGET,
        "cis_numstates": config.DEFAULT_CIS_NUMSTATES,
        "cis_guessvecs": config.DEFAULT_CIS_NUMSTATES
        * config.DEFAULT_CIS_GUESVECS_FACTOR,
        "run_type": config.CALC_TYPE_MAP[config.DEFAULT_CALC_TYPE][1],
    }


def get_calculation_parameters(solvent_data: Dict[str, float]) -> Dict[str, Any]:
    """
    Collects all necessary calculation parameters interactively from the user.

    Args:
        solvent_data: Dictionary of available solvents and their dielectric constants.

    Returns:
        A dictionary containing the user-specified parameters.
    """
    params: Dict[str, Any] = {}

    params["mol_name"] = io_utils.get_validated_input(
        "Enter the name of the Molecule: ", str
    )
    print(
        f"Note: Ensure '{params['mol_name']}.xyz' exists or provide the full path later."
    )

    params["calc_type"] = io_utils.get_validated_input(
        f"Enter calculation type code ({', '.join(map(str, config.CALC_TYPE_MAP.keys()))}): ",
        int,
        lambda x: x in config.CALC_TYPE_MAP,
    )

    params["functional"] = io_utils.get_validated_input(
        "Enter the name of the functional (e.g., b3lyp): ", str
    )
    params["basis_set"] = io_utils.get_validated_input(
        "Enter the basis-set (e.g., 6-31g*): ", str
    )
    params["charge"] = io_utils.get_validated_input("Enter the charge: ", int)
    params["multiplicity"] = io_utils.get_validated_input(
        "Enter the multiplicity: ", int
    )

    # Determine if solvent effects should be included
    cosmo_input = io_utils.get_validated_input(
        "Include Solvent Effects (COSMO)? (y/n): ",
        str,
        lambda x: x.lower() in ["y", "n"],
    )
    params["use_solvent"] = cosmo_input.lower() == "y"
    params["solvent_name"] = None
    params["epsilon"] = None

    if params["use_solvent"]:
        available_solvents = list(solvent_data.keys())
        while params["epsilon"] is None:
            solvent_name_input = io_utils.get_validated_input(
                "Enter the name of the solvent: ", str
            )
            params["solvent_name"] = solvent_name_input.lower()
            params["epsilon"] = solvent_data.get(
                params["solvent_name"]
            )  # Use loaded data
            if params["epsilon"] is None:
                print(f"Error: Solvent '{solvent_name_input}' not found.")
                # Optional: Suggest close matches or list all available
                print(
                    "Available solvents (first few):",
                    ", ".join(available_solvents[:10]) + "...",
                )

    # Set excited state parameters
    params["is_excited_state"] = params["calc_type"] in config.EXCITED_STATE_CALCS
    params["cis_target"] = (
        config.DEFAULT_CISTARGET
    )  # Could potentially ask user for these too
    params["cis_numstates"] = config.DEFAULT_CIS_NUMSTATES
    params["cis_guessvecs"] = (
        config.DEFAULT_CIS_NUMSTATES * config.DEFAULT_CIS_GUESVECS_FACTOR
    )

    # Set run type based on calc_type
    params["run_type"] = config.CALC_TYPE_MAP[params["calc_type"]][1]

    return params


def generate_terachem_input(params: Dict[str, Any]) -> str:
    """
    Generates the TeraChem input file content as a string based on parameters.

    Args:
        params: A dictionary containing the calculation parameters.

    Returns:
        A string containing the formatted TeraChem input file content.
    """
    mol_name = params["mol_name"]
    calc_name, _ = config.CALC_TYPE_MAP[params["calc_type"]]
    solvent_desc = (
        f"in {params['solvent_name']} (COSMO)"
        if params["use_solvent"]
        else "in gas phase"
    )
    state_desc = "Excited state" if params["is_excited_state"] else "Ground state"
    job_desc = (
        f"{mol_name} {state_desc} {calc_name.split('_')[1]} calculation {solvent_desc}"
    )

    # --- Template Sections ---
    header_tmpl = f"""\
# Job info: {job_desc}
# Generated by Chef-TeraChem (Refactored v{config.__version__})
#
"""

    coordinates_tmpl = f"""\
# Coordinate file (ensure '{mol_name}.xyz' is accessible)
coordinates        {mol_name.lower()}.xyz
"""

    charge_mult_tmpl = f"""\
# Charge & Multiplicity
charge             {params['charge']}
spinmult           {params['multiplicity']}
"""

    method_basis_run_tmpl = f"""\
# Basis Set, Method (Functional), and Run Type
basis              {params['basis_set']}
method             {params['functional'].lower()}
run                {params['run_type']}
"""

    # Specific options for optimization runs
    minimizer_tmpl = (
        """\
# Optimization specific options
new_minimizer      yes
"""
        if params["run_type"] == "minimize"
        else ""
    )

    # Specific options for frequency runs
    frequency_tmpl = (
        """\
# Frequency specific options
mincheck           false
"""
        if params["run_type"] == "frequencies"
        else ""
    )

    solvent_tmpl = (
        f"""\
# Solvent model (COSMO) and dielectric constant
pcm                cosmo
epsilon            {params['epsilon']:.4f}
"""
        if params["use_solvent"] and params["epsilon"] is not None
        else ""
    )

    excited_state_tmpl = (
        f"""\
# Excited state options (TD-DFT/CIS)
cis                yes
cistarget          {params['cis_target']}
cisnumstates       {params['cis_numstates']}
cisguessvecs       {params['cis_guessvecs']}
"""
        if params["is_excited_state"]
        else ""
    )

    hardware_tmpl = f"""\
# Hardware Information (Adjust as needed in config.py)
gpus               {config.DEFAULT_GPUS}
safemode           no
"""

    expert_opts_tmpl = """\
# Expert options (Uncomment and modify with caution, refer to TeraChem manual)
#precision         double
#threall           1.0e-15
#convthre          3.0e-07
#dftgrid           5
"""

    pcm_expert_opts_tmpl = (
        """\
# PCM Expert options (Uncomment and modify with caution)
#pcm_scale         1
#pcm_grid          lebedev
#pcmgrid_h         7
#pcmgrid_heavy     7
"""
        if params["use_solvent"]
        else ""
    )

    footer_tmpl = "end\n"

    # --- Assemble the input file content ---
    # Use filter(None, [...]) to easily skip empty template sections
    content_parts = [
        header_tmpl,
        coordinates_tmpl,
        charge_mult_tmpl,
        method_basis_run_tmpl,
        minimizer_tmpl,
        frequency_tmpl,
        solvent_tmpl,
        excited_state_tmpl,
        hardware_tmpl,
        expert_opts_tmpl,
        pcm_expert_opts_tmpl,
        footer_tmpl,
    ]
    content = "".join(filter(None, content_parts))

    return content


def generate_filename(params: Dict[str, Any]) -> str:
    """
    Generates a descriptive filename for the input file.

    Args:
        params: Dictionary of calculation parameters.

    Returns:
        A string representing the suggested filename.
    """
    base_name = params["mol_name"]
    # Get suffix from CALC_TYPE_MAP based on calc_type in params
    calc_suffix, _ = config.CALC_TYPE_MAP.get(
        params["calc_type"], ("unknown_calc", "unknown")
    )
    solvent_suffix = "_cosmo" if params.get("use_solvent", False) else ""
    return f"{base_name}_{calc_suffix}{solvent_suffix}.in"
