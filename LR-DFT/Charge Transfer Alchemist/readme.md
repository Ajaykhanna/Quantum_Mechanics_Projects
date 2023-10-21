
# Charge Transfer Alchemist 🧙‍♂️🔮
Easily generate input files for quantum chemistry calculations related to charge transfer.

## Features ✨
- **Automated Input Generation**: Just provide your atomic coordinates and desired omega values, and let the script handle the rest.
- **Configurable**: Adjust file naming conventions, content structures, and more via the `config.json` file.
- **Expandable**: While currently tailored for Gaussian, future versions will support TeraChem and potentially other quantum chemistry software.

## Usage 🚀
1. Configure your desired settings in `config.json`.
2. Provide your atomic coordinates in the `coordinates.xyz` file.
3. Run the script:
   ```
   python charge_transfer_alchemist.py --omega_start START --omega_end END --omega_step STEP
   ```
4. Input files will be generated in the specified directory.

## Configuration Options ⚙️
- `gs_filename`: Ground state filename format.
- `ex_filename`: Excited state filename format.
- `gs_content`: Content template for ground state input files.
- `ex_content`: Content template for excited state input files.
- ... (Additional configuration options for various file types and content templates)

## Future Tasks 🌟
- Extend support for TeraChem input files.
- Implement additional error checks and validation mechanisms.
- Enhance the user interface for even more effortless input generation.

## Author Information 📝
- **Name**: Ajay Khanna
- **Email**: [akhanna2@ucmerced.edu](mailto:akhanna2@ucmerced.edu)
- **LinkedIn**: [Ajay Khanna](https://www.linkedin.com/in/ajay-khanna/)

---

**Note**: This tool is under active development. Feedback, suggestions, and contributions are welcome!

