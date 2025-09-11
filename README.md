# Quantum_Mechanics_Projects

A comprehensive repository of Python tools, scripts, and utilities for quantum chemistry and quantum mechanics calculations. This collection supports workflows for TeraChem, Gaussian, ORCA, Psi4, and more. Each subdirectory contains specialized programs, utilities, or tutorials for tasks ranging from input file generation to spectral analysis and data transformation.

---

## Repository Structure & Contents

### 1. **GaussGlow ✨**

**Purpose:**  
Generate and visualize Gaussian vibronic spectra from quantum chemistry outputs.  
**Features:**  

- Parses Gaussian output files for vibrational and electronic transitions.
- Produces high-quality spectra plots.
- Customizable visualization options for quantum mechanical analysis.

### 2. **Charge Transfer Alchemist 🧙‍♂️🔮**

**Purpose:**  
Automate the generation of input files for charge transfer calculations in quantum chemistry.  
**Features:**  

- Supports multiple quantum chemistry packages (Gaussian, TeraChem, ORCA, Psi4).
- Streamlines setup for charge transfer studies.
- Includes templates and parameter customization.

### 3. **Spectroscopy 🌈🔬**

**Purpose:**  
Transform and analyze experimental and theoretical spectra.  
**Key Scripts:**  

- `transform_exp_data.py`:  
  - Converts experimental spectra from wavelength to frequency domain.
  - Performs lineshape transformations (absorption/emission).
  - Outputs processed data to CSV files.
- Additional scripts for spectral fitting and visualization.

### 4. **Nuclear Ensemble Approach**

**Purpose:**  
Generate nuclear ensemble spectra from DFT and TDDFT vertical excitation/de-excitation calculations.  
**Features:**  

- Parses output files from quantum chemistry calculations.
- Simulates ensemble spectra for comparison with experiment.

### 5. **TeraChem Utilities**

**Purpose:**  
Tools for managing TeraChem calculations and outputs.  
**Features:**  

- Input file generators.
- Output parsers and data extractors.
- Batch job management scripts.

### 6. **Gaussian Utilities**

**Purpose:**  
Scripts for automating Gaussian calculations and post-processing.  
**Features:**  

- Input file generators for various calculation types.
- Output parsers for extracting energies, spectra, and molecular properties.
- Batch job submission helpers.

### 7. **ORCA & Psi4 Utilities**

**Purpose:**  
Support for ORCA and Psi4 workflows.  
**Features:**  

- Input file templates and generators.
- Output parsing for key quantum chemical results.

### 8. **General Quantum Chemistry Tools**

**Purpose:**  
Miscellaneous utilities for quantum mechanics and chemistry.  
**Features:**  

- Data transformation scripts.
- Visualization tools.
- Tutorials and example notebooks.

---

## Getting Started

1. **Installation:**  
   - Most scripts require Python 3.x and standard scientific libraries (`numpy`, `pandas`, `matplotlib`, etc.).
   - Some tools require package-specific dependencies (e.g., `cclib` for output parsing).
   - See individual subdirectory README files for details.

2. **Usage:**  
   - Navigate to the relevant subdirectory for your task.
   - Read the local README or script docstrings for instructions.
   - Example command:

     ```
     python transform_exp_data.py --input spectrum.csv --output transformed.csv --mode absorption
     ```

3. **Contributions:**  
   - Pull requests and issues are welcome!
   - Please add documentation and example usage for new scripts.

---

## Contact

- **Author:** Ajay Khanna  
- **Email:** [akhanna2@ucmerced.edu](mailto:akhanna2@ucmerced.edu) / [quantphobia@gmail.com](mailto:quantphobia@gmail.com)  
- **GitHub:** [Ajaykhanna](https://github.com/Ajaykhanna)  
- **Twitter:** [@samdig](https://twitter.com/samdig)  
- **LinkedIn:** [ajay-khanna](https://www.linkedin.com/in/ajay-khanna)

---

*Explore, automate, and visualize your quantum chemistry projects with this evolving toolkit!*
