# 📘 Modeling Excited States in Molecular Organic Aggregates  

**A Student Guide to Optoelectronic Materials Design**  
*Based on Hernández & Crespo-Otero, Annu. Rev. Phys. Chem. 2023*

---

## 🔍 Overview

This guide summarizes key concepts from the review on modeling excited-state processes in **organic molecular aggregates**—systems of weakly interacting molecules used in:

- Organic Light-Emitting Diodes (OLEDs)
- Organic Solar Cells (OSCs)
- Lasers and Sensors

The focus is on **exciton models**, **electronic structure methods**, **nonradiative decay**, and **energy/charge transport**.

---

## ⚡ Key Excited-State Processes

| Process | Description | Application |
|-------|-------------|-------------|
| **FRET** | Long-range energy transfer via dipole coupling | OLEDs, Light Harvesting |
| **Dexter** | Short-range electron exchange | Triplet transport |
| **CT** | Charge separation between molecules | OSCs, TADF |
| **Singlet Fission (SF)** | One singlet → two triplets | Boosts solar efficiency |
| **TTA** | Two triplets → one singlet | Delayed fluorescence |
| **ISC / rISC** | S₁ ↔ T₁ transitions | TADF, Room-temp phosphorescence |

> 📌 **Figure 1** in the paper illustrates these processes.

---

## 🧩 Modeling Approaches

### 1. Cluster Models

- Small set of molecules (e.g., dimers).
- ✅ Fast, good for mechanism.
- ❌ Misses long-range effects.

### 2. Exciton Models

- Treat excitation as delocalized.
- ✅ Efficient for large systems.
- ❌ Needs vibronic/CT corrections.

### 3. Full System Models

- All atoms included.
- ✅ Most accurate.
- ❌ Computationally expensive.

> Use **Ewald summation** or **continuum models** to include environment.

---

## 📊 Exciton Models

### Frenkel Excitons

- Localized excitation.
- Based on **Kasha’s model**.
- ❌ Fails for CT states and short distances.

### J- vs H-Aggregates

| Type | Alignment | Emission | Brightness |
|------|----------|---------|-----------|
| **J** | Head-to-tail | Red-shifted | Bright |
| **H** | Side-by-side | Blue-shifted | Often dark |

> Determined by transition dipole angle: J if θ < 54.7°, H if θ > 54.7°.

### Advanced Models

- **Frenkel–Holstein**: Adds intramolecular vibrations.
- **Peierls coupling**: Intermolecular lattice modes.
- **Superexchange**: Includes CT-mediated coupling.

---

## 🧪 Electronic Structure Methods

| Method | Best For | Limitations |
|-------|--------|------------|
| **TDDFT** | Standard excited states | Fails for CT, double excitations |
| **CDFT** | Diabatic CT states | Not for dynamics |
| **CASPT2/CASSCF** | SF, TTA, diradicals | Very expensive |
| **ADC(2)** | Better than TDDFT | Costly for large systems |

> ✅ Use **auto-CAS** or **ML** to automate active space selection.

---

## 🌀 Excited-State Dynamics

### Simulation Methods

- **Surface Hopping (FSSH, SHARC)**: Trajectories jump between states.
- **FOB-SH**: Fragment-based, handles >100,000 atoms.
- **ML Potentials**: Accelerate dynamics with high accuracy.

> GPU-accelerated models simulate up to 27 chromophores.

---

## 🔁 Nonradiative Processes

### Conical Intersections (CIs)

- **Intra-CI**: Localized (e.g., bond twist) → IC.
- **Inter-CI**: Between molecules → ultrafast relaxation.

> CIs reduce emission yield but can be engineered.

### ISC & rISC

- Crucial for **TADF** and **phosphorescence**.
- Even light-element organics show **picosecond ISC**.

---

## 🚆 Transport Mechanisms

| Mechanism | Range | Description |
|----------|------|-------------|
| **Förster** | Long | Dipole-dipole |
| **Dexter** | Short | Electron exchange |
| **CT-mediated** | Medium | Important in π-stacked systems |

> **FOB-SH** captures small-to-large polaron transport.

---

## 🤖 Machine Learning in Modeling

### Applications

- Accelerate energy/gradient calculations.
- High-throughput screening of TADF/SF candidates.
- Predict OSC efficiency.
- Assist in active space selection.

> ⚠️ ML struggles with **out-of-distribution** chemistries.

---

## ✅ Conclusion & Tips for Students

### Key Takeaways

1. No single method fits all — match method to process.
2. Exciton models need vibronic/CT corrections.
3. CIs are critical for nonradiative decay.
4. Use multiconfigurational methods for SF/TTA.
5. Leverage **ML** and **GPU acceleration**.

### Recommended Workflow

1. **Screen** with TDDFT + dimer models.
2. **Build** exciton Hamiltonian.
3. **Simulate** dynamics with surface hopping.
4. **Validate** against experiment.

### Useful Tools & References

- `fromage` library: [Rivera et al., J. Comput. Chem. 2020](https://doi.org/10.1002/jcc.26165)
- Auto-CAS: Automated active space selection
- SHARC: Surface hopping with arbitrary couplings

---

> 🌐 **Next Step**: Try building a dimer model of pentacene and compute its SF efficiency using ADC(2) or CASPT2!
