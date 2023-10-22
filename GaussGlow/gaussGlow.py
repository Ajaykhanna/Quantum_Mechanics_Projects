
import re
import csv
import pandas as pd
import matplotlib.pyplot as plt

def display_banner():
    """Display the banner for the Gaussian Vibronic Spectra Generator."""
    banner = "Gaussian Vibronic Spectra Generator"
    print("=" * len(banner))
    print(banner)
    print("=" * len(banner))

def extract_data_from_log(filename):
    """Extract relevant data from the Gaussian log file."""
    with open(filename, "r") as file:
        content = file.read()
    transition_match = re.search(r"Energy of the 0-0 transition:\s+(\d+\.\d+)", content)
    transition_value = float(transition_match.group(1)) if transition_match else None
    hwhm_match = re.search(r"Half-Widths at Half-Maximum of\s+(\d+\.\d+)", content)
    hwhm_value = float(hwhm_match.group(1)) if hwhm_match else None
    spectrum_content = re.search(r'Legend:(.*?)Electric dipole moment \(input orientation\):', content, re.DOTALL).group(1)
    spectrum_content = spectrum_content.replace("D", "E")
    spectrum_lines = spectrum_content.strip().split("\n")[6:-6]
    spectrum_list = []
    for line in spectrum_lines:
        values = line.split()
        energy = float(values[0])
        intensity_0K = float(values[1])
        intensity_300K = float(values[2])
        spectrum_list.append([energy, intensity_0K, intensity_300K])
    return transition_value, hwhm_value, spectrum_list

def write_data_to_csv(filename, transition_value, hwhm_value, spectrum_list):
    """Write the extracted data to a CSV file."""
    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["# 0-0 transition value: " + str(transition_value) + " cm^-1"])
        csvwriter.writerow(["# Half-width half maxima value: " + str(hwhm_value) + " cm^-1"])
        csvwriter.writerow(["# Energy(cm^-1)", "Intensity_0K", "Intensity_300K"])
        for row in spectrum_list:
            csvwriter.writerow(row)

def read_and_normalize_data(filename):
    """Read the data from the CSV file and normalize the intensities."""
    df = pd.read_csv(filename, comment='#', skiprows=3, names=["Energy", "Intensity_0K", "Intensity_300K"])
    df["Intensity_0K"] /= df["Intensity_0K"].max()
    df["Intensity_300K"] /= df["Intensity_300K"].max()
    return df

def plot_spectra(abs_df, ems_df, output_filename):
    """Plot both the absorption and emission spectra on a single plot."""
    plt.figure(figsize=(12, 8))
    plt.plot(abs_df["Energy"], abs_df["Intensity_0K"], color='blue', label='Absorption at 0K', alpha=0.7)
    plt.plot(abs_df["Energy"], abs_df["Intensity_300K"], color='orange', label='Absorption at 300K', alpha=0.7)
    plt.plot(ems_df["Energy"], ems_df["Intensity_0K"], color='blue', linestyle='--', label='Emission at 0K', alpha=0.7)
    plt.plot(ems_df["Energy"], ems_df["Intensity_300K"], color='orange', linestyle='--', label='Emission at 300K', alpha=0.7)
    plt.xlabel('Energy (cm^-1)')
    plt.ylabel('Normalized Intensity')
    plt.legend()
    plt.title('Absorption and Emission Spectra')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_filename, dpi=600)
    plt.show()

# Main execution block
if __name__ == "__main__":
    display_banner()
    abs_transition_value, abs_hwhm_value, abs_spectrum_list = extract_data_from_log("./vib_abs.log")
    write_data_to_csv("absorption_spectrum_data.csv", abs_transition_value, abs_hwhm_value, abs_spectrum_list)
    ems_transition_value, ems_hwhm_value, ems_spectrum_list = extract_data_from_log("./vib_ems.log")
    write_data_to_csv("emission_spectrum_data.csv", ems_transition_value, ems_hwhm_value, ems_spectrum_list)
    abs_df = read_and_normalize_data("./absorption_spectrum_data.csv")
    ems_df = read_and_normalize_data("./emission_spectrum_data.csv")
    plot_spectra(abs_df, ems_df, "./abs_ems_spectrum_plot.png")
