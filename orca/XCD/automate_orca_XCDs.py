############################################
# Developer: Ajay Khanna
# Date: Dec.12.2024
# Place: LANL
# Project: Xray Circular Dichroism (XCD)
############################################

# Import Required Libraries
import os
import shutil
import numpy as np
from jinja2 import Environment, FileSystemLoader


def print_banner():
    """Prints a banner with the ORCA input file creation message and developer name."""
    print("=" * 70)  # Top border
    print("Creating ORCA X-ray Circular Dichoroism Input Files")
    print("Developer: Ajay Khanna")
    print("=" * 70)  # Bottom border


def render_template(template_name, **kwargs):
    """Renders a Jinja2 template with the provided context."""
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template(template_name)
    return template.render(**kwargs)


def write_file(filepath, content):
    """Writes content to a file and handles potential errors."""
    try:
        with open(filepath, "w") as outfile:
            outfile.write(content)
        print(f"Created file: {filepath}")
        return True
    except Exception as e:
        print(f"Error writing to {filepath}: {e}")
        return False


def create_orca_input(ntasks, orb, path_to_xyz_file, folder_name, base_name):
    """Creates the ORCA input file."""
    orca_input_content = render_template(
        "orca_input.j2", ntasks=ntasks, orb=orb, path_to_xyz_file=path_to_xyz_file
    )
    inp_file_path = os.path.join(folder_name, f"{base_name}_optd_gs_orb_{orb}_XCD.inp")
    return write_file(inp_file_path, orca_input_content)


def create_slurm_script(
    base_name, partition_name, folder_name, time, nodes, ntasks, mem, orb=1, email=None
):
    """Creates the SLURM script file."""
    slurm_script_content = render_template(
        "slurm_script.j2",
        base_name=base_name,
        partition_name=partition_name,
        time=time,
        nodes=nodes,
        ntasks=ntasks,
        mem=mem,
        orb=orb,
        email=email,
    )
    slurm_file_path = os.path.join(
        folder_name, f"{base_name}_optd_gs_orb_{orb}_XCD_job.slurm"
    )
    return write_file(slurm_file_path, slurm_script_content)


def process_filenames(filename_file):
    """Reads a file containing filenames and returns a list of filenames."""
    try:
        filenames = np.genfromtxt(filename_file, dtype=str)
        return list(filenames)  # Ensure it's always a list
    except Exception as e:
        print(f"Error reading filenames from {filename_file}: {e}")
        return None


def create_inp_and_slurm_files(
    filenames, partition_name, time, nodes, ntasks, mem, orb=1, email=None
):
    """Creates ORCA input (.inp) files and SLURM job submission scripts."""
    for name in filenames:
        base_name = os.path.splitext(name)[0]
        folder_name = os.path.join(base_name, "2s")
        os.makedirs(folder_name, exist_ok=True)
        xyz_file_path = os.path.join(os.getcwd(), base_name, name + "_opt_gs.xyz")

        if not os.path.exists(xyz_file_path):
            print(f"XYZ file not found: {xyz_file_path}")
            continue

        if not create_orca_input(ntasks, orb, xyz_file_path, folder_name, base_name):
            continue

        create_slurm_script(
            base_name,
            partition_name,
            folder_name,
            time,
            nodes,
            ntasks,
            mem,
            orb,
            email,
        )


def main():
    print_banner()

    filenames_file = "xcd_filesnames.txt"

    partition_name = "general"
    time = "00-01:00:00"
    nodes = 1
    ntasks = 8
    mem = 40
    email = "akhanna2@ucmerced.edu"
    orb = 1

    filenames = process_filenames(filenames_file)
    if filenames:
        create_inp_and_slurm_files(
            filenames, partition_name, time, nodes, ntasks, mem, orb, email
        )
        print("Successfully created input and slurm files.")
    else:
        print("Failed to process filenames.")


if __name__ == "__main__":
    main()
