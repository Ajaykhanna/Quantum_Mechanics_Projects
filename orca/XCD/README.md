# 🚀 Automate ORCA XCD Input & SLURM Script Generation

Welcome to the **Automate ORCA XCDs** project! This Python script simplifies the creation of **ORCA input files** and **SLURM job submission scripts** for **X-ray Circular Dichroism (XCD)** calculations. 🧪✨

---

## 📜 Features

- 🛠️ **Automated Input File Creation**: Generates ORCA `.inp` files using customizable Jinja2 templates.
- 🖥️ **SLURM Job Script Generation**: Creates `.slurm` scripts for HPC job submissions.
- 📂 **Batch Processing**: Handles multiple filenames from a single input file.
- 🔧 **Customizable Parameters**: Easily configure memory, tasks, nodes, and more.
- 🧑‍💻 **Developer-Friendly**: Modular and clean codebase for easy maintenance.

---

## 📂 Directory Structure
Quantum_Mechanics_Projects

    orca
        └── XCD
            ├── automate_orca_XCDs.py
                ├── templates │
                    ├── orca_input.j2 │
                    └── slurm_script.j2
            ├── xcd_filesnames.txt

---

## 🛠️ Requirements

- Python 3.8+
- Required Python Libraries:
  - `numpy`
  - `jinja2`

Install dependencies using pip:

```bash
pip install numpy jinja2

🚀 How to Use
1. Prepare Input Files:
Create a file named xcd_filesnames.txt containing the list of filenames (one per line).

2. Set Up Templates:
Ensure the orca_input.j2 and slurm_script.j2 templates are in the templates/ directory.

3. Run the Script:
python automate_orca_XCDs.py

4. Output:
ORCA .inp files and SLURM .slurm scripts will be generated in the respective directories.
```

## ⚙️Configuration
```
| Parameter        | Description                  | Default Value        |
|------------------|------------------------------|----------------------|
| `partition_name` | SLURM partition name       | `general`            |
| `time`           | Job time limit               | `00-01:00:00`         |
| `nodes`          | Number of nodes             | `1`                  |
| `ntasks`         | Number of tasks             | `8`                  |
| `mem`            | Memory in GB                 | `40`                 |
| `email`          | Email for job notifications | `akhanna2@ucmerced.edu` |
| `orb`            | Orbital number               | `1`                  |
```

## 📧 Contact
For questions or feedback, feel free to reach out to Ajay Khanna at akhanna2@ucmerced.edu. ✉️

## 🌟 Contributing
Contributions are welcome! Feel free to fork this repository, make improvements, and submit a pull request. Let's make this project even better! 💡

## 📜 License
This project is licensed under the MIT License. 📝

## 🎉 Acknowledgments
Special thanks to the LANL Team for their support and guidance in this project. 🙌

Happy Computing! 🧑‍💻