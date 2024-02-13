import numpy as np
import matplotlib.pyplot as plt

# Read the CSV file
data = np.loadtxt("nuclear_ensemble_spectra.csv", delimiter=",", dtype=float, usecols=(0, 2))

# Extract the x and y values from the data
x = data[:,0]
y = data[:,1]

# Plot the data
plt.plot(x, y)
plt.xlabel("Energy(eV)")
plt.ylabel("Intensity[arb. units]")
plt.title("Nuclear Ensemble Spectra")
plt.tight_layout()
plt.savefig("nuclear_ensemble_spectra.png", dpi=600, bbox_inches="tight")
plt.show()
