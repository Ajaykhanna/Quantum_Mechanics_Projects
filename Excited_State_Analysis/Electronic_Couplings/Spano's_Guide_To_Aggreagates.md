# 🧪 Spano’s H/J Aggregate Field Guide — *A Lab-Ready README*

![Level](https://img.shields.io/badge/Level-1%20st%20year%20grad-blue) ![Focus](https://img.shields.io/badge/Focus-Excitons%20%7C%20Vibronics%20%7C%20CT-green) ![Use](https://img.shields.io/badge/Use-Spectra%20Diagnosis%20%7C%20Parameter%20Extraction-orange)

A clear, practical digest of Frank C. Spano’s expanded theory of molecular aggregates — built for first-year grad students and new researchers who need to **interpret spectra** and **extract physical parameters** quickly and defensibly.

---

## 🚀 TL;DR

* **J-aggregates:** red-shifted absorption, **strong 0–0 PL** (often superradiant), near-zero Stokes shift at low T.
* **H-aggregates:** blue-shifted absorption, **suppressed 0–0 PL**, weak “false-origin” absorption/PL from Herzberg–Teller (HT) intensity borrowing.
* **Ratios you can measure today:**

  * $R_{\text{abs}} = I_{A_1}/I_{A_2}$ → tracks bandwidth/bright-state shift (H vs J trend flips).
  * $R_{\text{PL}} = I_{00}/I_{01} \approx N_{\text{coh}}/\lambda^2$ (J) → coherence size from PL.
* **CT mixing (electron/hole transfer):** in-phase $t_e,t_h$ → CT-J; out-of-phase → CT-H. (See CT section below.)

---

## 🧭 Table of Contents

* [Quick Diagnostic Cheat-Sheet](#-quick-diagnostic-cheat-sheet)
* [Core Concepts (fast)](#-core-concepts-fast)
* [How to Use This Guide](#-how-to-use-this-guide)
* [Decision Tree (Mermaid)](#-decision-tree-mermaid)
* [Parameter Extraction Recipes](#-parameter-extraction-recipes)
* [What to Measure → What It Tells You](#-what-to-measure--what-it-tells-you)
* [Equations at a Glance](#-equations-at-a-glance)
* [📐 Computing Exciton Bandwidth from Dimer, Trimer, …](#-computing-exciton-bandwidth-from-dimer-trimer-)
* [Disorder & Size Effects](#-disorder--size-effects)
* [CT-Mediated Aggregates](#-ctmediated-aggregates)
* [Pitfalls & Pro Tips](#-pitfalls--pro-tips)
* [Attribution](#-attribution)

---

## 🔎 Quick Diagnostic Cheat-Sheet

| Feature (low T)                     | J-Aggregate                           | H-Aggregate                             | Why it matters                   |
| ----------------------------------- | ------------------------------------- | --------------------------------------- | -------------------------------- |
| Absorption shift vs monomer         | **Red**                               | **Blue** (watch solvation offsets)      | Sign of Coulomb/geometry         |
| PL origin (0–0)                     | **Strong**, superradiant, \~no Stokes | **Suppressed/forbidden**; PL starts 0–1 | Selection rules at band edge     |
| Abs vibronic ratio $R_{\text{abs}}$ | **Increases** with $W$                | **Decreases** with $W$                  | Different bright-state placement |
| PL ratio $R_{\text{PL}}$            | $\sim N_{\text{coh}}/\lambda^2$ (big) | n/a (0–0 dark)                          | Coherence size in J              |
| Tiny “false origin”                 | Rare                                  | **Common** via HT                       | HT intensity borrowing           |
| Polarization (two-mol/cell)         | LDC ≈ **J-like**                      | UDC ≈ **H-like**                        | Davydov splitting fingerprint    |

---

## 🧠 Core Concepts (fast)

* **H vs J (sign of $J_C$)**: Bright state at band **bottom** for J ($J_C<0$), band **top** for H ($J_C>0$).
* **Vibronic coupling (Holstein):** Intramolecular modes with Huang–Rhys $\lambda^2$ reshape intensities and enable HT borrowing.
* **Bandwidth vs curvature:** $W$ gives overall spread; **parabolic curvature** near the bright edge often controls line shapes (key in herringbone crystals).
* **Coherence:** Absorption quickly becomes $N$-independent; **PL 0–0** scales with **coherence size** $N_{\text{coh}}$.
* **Disorder:** Sets widths and **selects lower states** in PL (narrowing/red-shift even without coupling).
* **CT mixing:** Electron/hole transfer amplitudes $t_e,t_h$ **interfere** and can flip H↔J behavior.

---

## 🗺️ How to Use This Guide

1. **Collect spectra:** monomer + aggregate absorption; low-T PL if possible.
2. **Classify H vs J** from shift + 0–0 behavior.
3. **Quantify vibronic coupling** from monomer ($\lambda^2,\ \omega_{\text{vib}}$).
4. **Extract $W$ / bright-state shift** from $R_{\text{abs}}$.
5. **Estimate $N_{\text{coh}}$** from $R_{\text{PL}}$ (J).
6. **Check disorder** (abs vs PL widths, temperature).
7. **Probe CT** if bands are broad/split or packing is tight (use second moment).

---

## 🌳 Decision Tree (Mermaid)

```mermaid
flowchart TD
  A[Aggregate spectra collected];
  B{Absorption shift vs monomer?};
  A --> B;

  B -->|Red| J1[J-candidate];
  B -->|Blue| H1[H-candidate];

  J1 --> C{PL 0-0 strong and Stokes ~ 0?};
  C -->|Yes| J2[Confirm J];
  C -->|No| J3[Check disorder or CT; also check temperature];

  H1 --> D{0-0 emission suppressed and false origin present?};
  D -->|Yes| H2[Confirm H (with HT)];
  D -->|No| H3[Check solvation shift (D - D') and disorder];

  J2 --> E{Compute R_PL = I00 / I01};
  E --> F[N_coh ≈ lambda^2 * R_PL];

  H2 --> G{Compute R_abs = I_A1 / I_A2};
  J2 --> H{Compute R_abs};

  G --> I[H: R_abs decreases as bandwidth W increases];
  H --> J[J: R_abs increases as bandwidth W increases];

  J3 --> K{Suspect CT?};
  H3 --> K;

  K -->|Yes| L[Use second spectral moment to estimate abs(t_e + t_h)];
  K -->|No| M[Refine disorder model and fit widths];

```

---

## 🧰 Parameter Extraction Recipes

### 1) Absorption vibronic ratio → bandwidth/bright-state shift

* Measure $R_{\text{abs}} = I_{A_1}/I_{A_2}$.
* Trend: **J:** $R_{\text{abs}}\uparrow$ with $W$. **H:** $R_{\text{abs}}\downarrow$ with $W$.
* Use n.n. (nearest-neighbor) or extended-coupling fits to estimate:

  * **Bright-state shift** $J_{k=0}$ (most robust).
  * **Bandwidth** $W$ (model-dependent; curvature matters in 2D).

### 2) PL vibronic ratio → coherence size (J)

* Measure $R_{\text{PL}} = I_{00}/I_{01}$ at low T.
* Estimate **coherence size**: $N_{\text{coh}} \approx \lambda^2\, R_{\text{PL}}$.

### 3) Second spectral moment → CT coupling

* Compute the **second central moment** of absorption to estimate $|t_e + t_h|$ when $\lambda^2,\ \omega_{\text{vib}}$ are known (see CT section).

---

## 📏 What to Measure → What It Tells You

| Measurement                       | Extract                     | Notes                                                        |   |                                                   |
| --------------------------------- | --------------------------- | ------------------------------------------------------------ | - | ------------------------------------------------- |
| Peak shift (abs vs monomer)       | H/J identity (first pass)   | Correct for solution/solvation offsets if small blue shifts  |   |                                                   |
| $R_{\text{abs}}=I_{A_1}/I_{A_2}$  | $J_{k=0}$, trend in $W$     | Opposite monotonicity for H vs J                             |   |                                                   |
| $R_{\text{PL}}=I_{00}/I_{01}$ (J) | $N_{\text{coh}}$            | Take at low T; replace $N$ by $N_{\text{coh}}$ with disorder |   |                                                   |
| PL 0–0 visibility                 | Selection rules             | Dark in ideal H; bright and superradiant in J                |   |                                                   |
| Polarization (two-mol/cell)       | Davydov splitting (UDC/LDC) | LDC ≈ J-like; UDC ≈ H-like                                   |   |                                                   |
| Second spectral moment            | (                           | t\_e+t\_h                                                    | ) | CT estimator even without resolved band splitting |

---

## 🧮 Equations at a Glance

* **Exciton dispersion (1D, n.n., periodic)**
  $J_k = 2J_C\cos k$; **bandwidth** $W=|J_{k=0}-J_{k=\pi}|=4|J_C|$.
* **Finite size (open boundaries)**
  $J_p=2J_C\cos\!\big(\tfrac{\pi p}{N+1}\big)$, $p=1,\dots,N$ → $W(N)=4|J_C|\cos\!\big(\tfrac{\pi}{N+1}\big)$. 
* **PL scaling (J, low T)**
  $I_{00}\propto N_{\text{coh}}$, $I_{01}\propto \lambda^2$ ⇒ $R_{\text{PL}}=N_{\text{coh}}/\lambda^2$.

---

## 📐 Computing Exciton Bandwidth from Dimer, Trimer, …

**Why this matters:** Many experiments control or observe **oligomer** size (N=2–5). You can estimate the **free-exciton bandwidth** $W$ from these finite aggregates and extrapolate to longer chains.

### A) Open vs periodic boundaries

* **Open chains (common for short oligomers):**
  Energies follow $J_p=2J_C\cos\!\big(\frac{\pi p}{N+1}\big)$ with $p=1..N$. The **bandwidth** is

  $$
  W(N)=E_{\max}-E_{\min}=4|J_C|\cos\!\Big(\frac{\pi}{N+1}\Big)
  $$

  which rapidly approaches $4|J_C|$ as $N$ grows (already \~converged by $N\approx20$).

* **Periodic chains (idealized polymer):**
  $J_k = 2J_C\cos k$ and $W=4|J_C|$.

### B) Concrete oligomer values (n.n. coupling)

* **Monomer (N=1):** $W(1)=0$.
* **Dimer (N=2):** $W(2)=2|J_C|$. Also, the **symmetric splitting** between bright/dark dimer states is $2|J_C|$ → a direct handle on $|J_C|$.
* **Trimer (N=3):** $W(3)=2\sqrt{2}\,|J_C|$.
* **Tetramer (N=4):** $W(4)=4|J_C|\cos(\pi/5)\approx3.236|J_C|$.
* **Pentamer (N=5):** $W(5)=4|J_C|\cos(\pi/6)\approx3.464|J_C|$.
* *(General)* $W(N)=4|J_C|\cos\!\big(\frac{\pi}{N+1}\big)$ (open chain).

### C) From experiment → $W$

1. **Measure a dimer spectrum** and read the **splitting** of the two exciton lines → $|J_C|=\tfrac{1}{2}\,\text{splitting}$.
2. **Plug $|J_C|$** into $W(N)=4|J_C|\cos(\pi/(N+1))$ for your **N-mer**.
3. **Assign H vs J** from the **sign** of $J_C$: J if $J_C<0$, H if $J_C>0$. (Use red/blue shift & vibronic signatures to corroborate.)

### D) What you’ll see in real systems

* In J-type **head-to-tail** oligomers (e.g., PDI chains), $W$ **grows** as you go from monomer → dimer → trimer, tracking the spectral **red-shift** and increasing $R_{\text{abs}}$.
* For small $N$, **open boundaries** and **thermal population** can slightly reduce ideal $R_{\text{PL}}=N/\lambda^2$; treat end-effects like weak disorder.

---

## 🌫️ Disorder & Size Effects

* **Absorption** reports primarily on **$W$**; **PL** reports on **$N_{\text{coh}}$** (coherence size).
* **End effects/temperature** (small $N$, room T) lower observed $R_{\text{PL}}$ vs the ideal $N/\lambda^2$.

---

## 🔌 CT-Mediated Aggregates

* **When to suspect CT:** tight packing, large/split bands, unexpected H/J flips, photoconductivity.
* **Interference physics:** sign and magnitude of $t_e, t_h$ determine whether the lowest bright state is J-like or H-like.
* **How to quantify:** if two bands merge, compute the **second spectral moment** to estimate $|t_e+t_h|$; if split, analyze **Davydov splitting** and polarization.

---

## ⚠️ Pitfalls & Pro Tips

* Don’t assign H/J by **shift alone** — small blue shifts can be masked by solvent/packing offsets. Always check **0–0 PL** and **vibronic ratios**.
* In herringbone crystals, **curvature** (not just $W$) controls line shapes — a broad band can still behave “weak-coupling-like.”
* For J-aggregates, **take low-T PL** to read out $N_{\text{coh}}$; room-T values are underestimates.
* HT “false origin” in H is a **feature, not a bug** — use it to confirm H character under strong coupling.

---

## 📚 Attribution

This README distills the insights of Frank C. Spano’s review *“Expanded Theory of H- and J-Molecular Aggregates: The Effects of Vibronic Coupling and Intermolecular Charge Transfer”* (Chem. Rev., 2018) into a lab-ready format for teaching and rapid spectral diagnosis, with explicit oligomer-to-bandwidth rules and examples.
Key derivations and formulas cited inline: dispersion/bandwidth and finite-size formulas, dimer splitting, and trimer bandwidth.
