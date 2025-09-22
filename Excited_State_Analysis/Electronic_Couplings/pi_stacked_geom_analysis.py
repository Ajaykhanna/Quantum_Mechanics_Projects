import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import cdist
import MDAnalysis as mda  # type: ignore
import pandas as pd
from collections import OrderedDict


class PiStackAnalyzer:
    def __init__(self, xyz_files, monomer_indices_dict):
        """
        Initialize analyzer with XYZ files and monomer atom indices

        Parameters:
        -----------
        xyz_files : dict
            {'unattached': path, 'sandwich': path, 'zigzag': path}
        monomer_indices_dict : dict
            Structure-specific monomer indices (1-based indexing)
        """
        self.structures = OrderedDict()
        self.monomer_indices = monomer_indices_dict

        for key, filepath in xyz_files.items():
            self.structures[key] = mda.Universe(filepath)

        self.labels = list(self.structures.keys())

    def parse_indices(self, index_string):
        """
        Parse index string like '86-127,130-131,133-135,154-183' to list
        Converts from 1-based to 0-based indexing for Python
        """
        indices = []
        parts = index_string.split(",")
        for part in parts:
            part = part.strip()
            if "-" in part:
                start, end = map(int, part.split("-"))
                # Convert from 1-based to 0-based indexing
                indices.extend(
                    range(start - 1, end)
                )  # end is inclusive in original, so we use end not end-1
            else:
                # Single index, convert from 1-based to 0-based
                indices.append(int(part) - 1)
        return indices

    def get_monomer_atoms(self, universe, structure_type, monomer_key):
        """Get atoms for a specific monomer"""
        indices = self.monomer_indices[structure_type][monomer_key]
        return universe.atoms[indices]

    def get_monomer_COM(self, universe, structure_type, monomer_key):
        """Calculate center of mass for a monomer"""
        atoms = self.get_monomer_atoms(universe, structure_type, monomer_key)
        return atoms.center_of_mass()

    def get_monomer_plane(self, universe, structure_type, monomer_key):
        """Calculate best-fit plane for aromatic monomer"""
        atoms = self.get_monomer_atoms(universe, structure_type, monomer_key)
        positions = atoms.positions

        # Calculate best-fit plane using SVD
        centroid = np.mean(positions, axis=0)
        centered = positions - centroid
        u, s, vh = np.linalg.svd(centered.T)
        normal = u[:, -1]  # Normal vector to plane

        # Ensure normal points in consistent direction (e.g., positive z)
        if normal[2] < 0:
            normal = -normal

        return centroid, normal

    def calculate_interplanar_distance(self, universe, structure_type):
        """Calculate distances between monomer planes"""
        results = {}

        # Get plane parameters for each monomer
        planes = {}
        for key in ["top", "middle", "bottom"]:
            planes[key] = self.get_monomer_plane(universe, structure_type, key)

        # Calculate distances
        # Top to middle
        top_com = self.get_monomer_COM(universe, structure_type, "top")
        middle_centroid, middle_normal = planes["middle"]
        d_top_middle = abs(np.dot(top_com - middle_centroid, middle_normal))

        # Bottom to middle
        bottom_com = self.get_monomer_COM(universe, structure_type, "bottom")
        d_bottom_middle = abs(np.dot(bottom_com - middle_centroid, middle_normal))

        results["top_middle_distance"] = d_top_middle
        results["bottom_middle_distance"] = d_bottom_middle

        return results

    def calculate_twist_angles(self, universe, structure_type):
        """Calculate twist angles between monomers"""
        results = {}

        # Get plane normals
        _, top_normal = self.get_monomer_plane(universe, structure_type, "top")
        _, middle_normal = self.get_monomer_plane(universe, structure_type, "middle")
        _, bottom_normal = self.get_monomer_plane(universe, structure_type, "bottom")

        # Calculate angles between normals
        # This gives the tilt angle between planes
        tilt_top_middle = np.arccos(
            np.clip(np.abs(np.dot(top_normal, middle_normal)), 0, 1)
        )
        tilt_bottom_middle = np.arccos(
            np.clip(np.abs(np.dot(bottom_normal, middle_normal)), 0, 1)
        )

        results["top_middle_tilt"] = np.degrees(tilt_top_middle)
        results["bottom_middle_tilt"] = np.degrees(tilt_bottom_middle)

        # For twist angle, project onto perpendicular plane
        # Get COMs to define rotation axis
        top_com = self.get_monomer_COM(universe, structure_type, "top")
        middle_com = self.get_monomer_COM(universe, structure_type, "middle")
        bottom_com = self.get_monomer_COM(universe, structure_type, "bottom")

        # Define reference vectors in each plane perpendicular to stacking axis
        top_atoms = self.get_monomer_atoms(universe, structure_type, "top")
        middle_atoms = self.get_monomer_atoms(universe, structure_type, "middle")
        bottom_atoms = self.get_monomer_atoms(universe, structure_type, "bottom")

        # Reference vectors in plane
        top_ref = top_atoms.positions[0] - top_com
        middle_ref = middle_atoms.positions[0] - middle_com
        bottom_ref = bottom_atoms.positions[0] - bottom_com

        # Project onto plane perpendicular to stacking axis
        stack_axis = middle_normal

        top_ref_proj = top_ref - np.dot(top_ref, stack_axis) * stack_axis
        middle_ref_proj = middle_ref - np.dot(middle_ref, stack_axis) * stack_axis
        bottom_ref_proj = bottom_ref - np.dot(bottom_ref, stack_axis) * stack_axis

        # Normalize
        if np.linalg.norm(top_ref_proj) > 1e-6:
            top_ref_proj /= np.linalg.norm(top_ref_proj)
        if np.linalg.norm(middle_ref_proj) > 1e-6:
            middle_ref_proj /= np.linalg.norm(middle_ref_proj)
        if np.linalg.norm(bottom_ref_proj) > 1e-6:
            bottom_ref_proj /= np.linalg.norm(bottom_ref_proj)

        # Calculate twist angles
        twist_top_middle = np.arccos(
            np.clip(np.dot(top_ref_proj, middle_ref_proj), -1, 1)
        )
        twist_bottom_middle = np.arccos(
            np.clip(np.dot(bottom_ref_proj, middle_ref_proj), -1, 1)
        )

        results["top_middle_twist"] = np.degrees(twist_top_middle)
        results["bottom_middle_twist"] = np.degrees(twist_bottom_middle)

        return results

    def calculate_slip_distances(self, universe, structure_type):
        """Calculate lateral slip between monomers"""
        results = {}

        # Get COMs
        top_com = self.get_monomer_COM(universe, structure_type, "top")
        middle_com = self.get_monomer_COM(universe, structure_type, "middle")
        bottom_com = self.get_monomer_COM(universe, structure_type, "bottom")

        # Get middle plane normal
        _, middle_normal = self.get_monomer_plane(universe, structure_type, "middle")

        # Project COM differences onto middle plane
        top_diff = top_com - middle_com
        top_slip = top_diff - np.dot(top_diff, middle_normal) * middle_normal

        bottom_diff = bottom_com - middle_com
        bottom_slip = bottom_diff - np.dot(bottom_diff, middle_normal) * middle_normal

        results["top_middle_slip"] = np.linalg.norm(top_slip)
        results["bottom_middle_slip"] = np.linalg.norm(bottom_slip)

        # Also calculate slip components (x and y if z is stacking axis)
        results["top_middle_slip_x"] = top_slip[0]
        results["top_middle_slip_y"] = top_slip[1]
        results["bottom_middle_slip_x"] = bottom_slip[0]
        results["bottom_middle_slip_y"] = bottom_slip[1]

        return results

    def verify_indices(self):
        """Verify that indices are valid for each structure"""
        print("\n" + "=" * 80)
        print("VERIFYING ATOM INDICES")
        print("=" * 80)

        for struct_type, universe in self.structures.items():
            print(f"\n{struct_type.upper()}:")
            print(f"  Total atoms in structure: {len(universe.atoms)}")

            for monomer in ["top", "middle", "bottom"]:
                indices = self.monomer_indices[struct_type][monomer]
                print(f"  {monomer:8s} monomer: {len(indices)} atoms")

                # Check if any indices are out of bounds
                max_idx = max(indices)
                if max_idx >= len(universe.atoms):
                    print(
                        f"    WARNING: Index {max_idx+1} (1-based) exceeds number of atoms!"
                    )

                # Show index ranges for verification
                if len(indices) > 0:
                    # Convert back to 1-based for display
                    indices_1based = [i + 1 for i in indices]
                    print(
                        f"    Index range: {min(indices_1based)}-{max(indices_1based)} (1-based)"
                    )

    def analyze_all_structures(self):
        """Perform complete analysis on all structures"""
        all_results = []

        for structure_type, universe in self.structures.items():
            print(f"\nAnalyzing {structure_type}...")

            results = {"Structure": structure_type}

            try:
                # Calculate all parameters
                distances = self.calculate_interplanar_distance(
                    universe, structure_type
                )
                angles = self.calculate_twist_angles(universe, structure_type)
                slips = self.calculate_slip_distances(universe, structure_type)

                results.update(distances)
                results.update(angles)
                results.update(slips)

            except Exception as e:
                print(f"  Error analyzing {structure_type}: {e}")
                # Add NaN values for failed calculations
                for key in [
                    "top_middle_distance",
                    "bottom_middle_distance",
                    "top_middle_tilt",
                    "bottom_middle_tilt",
                    "top_middle_twist",
                    "bottom_middle_twist",
                    "top_middle_slip",
                    "bottom_middle_slip",
                    "top_middle_slip_x",
                    "top_middle_slip_y",
                    "bottom_middle_slip_x",
                    "bottom_middle_slip_y",
                ]:
                    results[key] = np.nan

            all_results.append(results)

        return pd.DataFrame(all_results)

    def plot_comparison(self, df):
        """Create comprehensive comparison plots"""
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Plot settings
        x = np.arange(len(self.labels))
        width = 0.35
        colors = {"top": "#FF6B6B", "bottom": "#4ECDC4"}

        # Interplanar distances
        ax = fig.add_subplot(gs[0, 0])
        ax.bar(
            x - width / 2,
            df["top_middle_distance"],
            width,
            label="Top-Middle",
            color=colors["top"],
            alpha=0.8,
        )
        ax.bar(
            x + width / 2,
            df["bottom_middle_distance"],
            width,
            label="Bottom-Middle",
            color=colors["bottom"],
            alpha=0.8,
        )
        ax.set_ylabel("Distance (Å)", fontsize=10)
        ax.set_title("Interplanar Distances", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self.labels, rotation=45, ha="right")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # Tilt angles
        ax = fig.add_subplot(gs[0, 1])
        ax.bar(
            x - width / 2,
            df["top_middle_tilt"],
            width,
            label="Top-Middle",
            color=colors["top"],
            alpha=0.8,
        )
        ax.bar(
            x + width / 2,
            df["bottom_middle_tilt"],
            width,
            label="Bottom-Middle",
            color=colors["bottom"],
            alpha=0.8,
        )
        ax.set_ylabel("Angle (degrees)", fontsize=10)
        ax.set_title("Tilt Angles", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self.labels, rotation=45, ha="right")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # Twist angles
        ax = fig.add_subplot(gs[0, 2])
        ax.bar(
            x - width / 2,
            df["top_middle_twist"],
            width,
            label="Top-Middle",
            color=colors["top"],
            alpha=0.8,
        )
        ax.bar(
            x + width / 2,
            df["bottom_middle_twist"],
            width,
            label="Bottom-Middle",
            color=colors["bottom"],
            alpha=0.8,
        )
        ax.set_ylabel("Angle (degrees)", fontsize=10)
        ax.set_title("Twist Angles", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self.labels, rotation=45, ha="right")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # Slip distances
        ax = fig.add_subplot(gs[1, 0])
        ax.bar(
            x - width / 2,
            df["top_middle_slip"],
            width,
            label="Top-Middle",
            color=colors["top"],
            alpha=0.8,
        )
        ax.bar(
            x + width / 2,
            df["bottom_middle_slip"],
            width,
            label="Bottom-Middle",
            color=colors["bottom"],
            alpha=0.8,
        )
        ax.set_ylabel("Distance (Å)", fontsize=10)
        ax.set_title("Total Lateral Slip", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self.labels, rotation=45, ha="right")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        # Changes relative to reference (unattached)
        ref_idx = 0
        ref_values = df.iloc[ref_idx]

        # Distance changes
        ax = fig.add_subplot(gs[1, 1])
        distance_changes_top = (
            df["top_middle_distance"] - ref_values["top_middle_distance"]
        )
        distance_changes_bottom = (
            df["bottom_middle_distance"] - ref_values["bottom_middle_distance"]
        )
        ax.bar(
            x - width / 2,
            distance_changes_top,
            width,
            label="Top-Middle",
            color=colors["top"],
            alpha=0.8,
        )
        ax.bar(
            x + width / 2,
            distance_changes_bottom,
            width,
            label="Bottom-Middle",
            color=colors["bottom"],
            alpha=0.8,
        )
        ax.set_ylabel("Change (Å)", fontsize=10)
        ax.set_title("Distance Changes vs Unattached", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self.labels, rotation=45, ha="right")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

        # Slip changes
        ax = fig.add_subplot(gs[1, 2])
        slip_changes_top = df["top_middle_slip"] - ref_values["top_middle_slip"]
        slip_changes_bottom = (
            df["bottom_middle_slip"] - ref_values["bottom_middle_slip"]
        )
        ax.bar(
            x - width / 2,
            slip_changes_top,
            width,
            label="Top-Middle",
            color=colors["top"],
            alpha=0.8,
        )
        ax.bar(
            x + width / 2,
            slip_changes_bottom,
            width,
            label="Bottom-Middle",
            color=colors["bottom"],
            alpha=0.8,
        )
        ax.set_ylabel("Change (Å)", fontsize=10)
        ax.set_title("Slip Changes vs Unattached", fontsize=11, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(self.labels, rotation=45, ha="right")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

        # 2D slip vector plot
        ax = fig.add_subplot(gs[2, :2])

        # Plot slip vectors in xy plane
        for i, label in enumerate(self.labels):
            # Top monomer slip
            ax.arrow(
                0,
                0,
                df.iloc[i]["top_middle_slip_x"],
                df.iloc[i]["top_middle_slip_y"],
                head_width=0.1,
                head_length=0.05,
                fc=colors["top"],
                ec=colors["top"],
                alpha=0.6,
                width=0.02,
                label=f"{label} (top)" if i == 0 else "",
            )

            # Bottom monomer slip
            ax.arrow(
                0,
                0,
                df.iloc[i]["bottom_middle_slip_x"],
                df.iloc[i]["bottom_middle_slip_y"],
                head_width=0.1,
                head_length=0.05,
                fc=colors["bottom"],
                ec=colors["bottom"],
                alpha=0.6,
                width=0.02,
                linestyle="--",
                label=f"{label} (bottom)" if i == 0 else "",
            )

            # Add labels
            ax.text(
                df.iloc[i]["top_middle_slip_x"],
                df.iloc[i]["top_middle_slip_y"],
                f"T{i+1}",
                fontsize=9,
                ha="center",
            )
            ax.text(
                df.iloc[i]["bottom_middle_slip_x"],
                df.iloc[i]["bottom_middle_slip_y"],
                f"B{i+1}",
                fontsize=9,
                ha="center",
            )

        ax.set_xlabel("X Slip (Å)", fontsize=10)
        ax.set_ylabel("Y Slip (Å)", fontsize=10)
        ax.set_title(
            "Lateral Slip Vectors (relative to middle monomer)",
            fontsize=11,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color="black", linestyle="-", linewidth=0.5)
        ax.axvline(x=0, color="black", linestyle="-", linewidth=0.5)
        ax.set_aspect("equal")

        # Summary table
        ax = fig.add_subplot(gs[2, 2])
        ax.axis("tight")
        ax.axis("off")

        # Create summary statistics
        summary_data = []
        for col in [
            "top_middle_distance",
            "bottom_middle_distance",
            "top_middle_slip",
            "bottom_middle_slip",
        ]:
            row = [col.replace("_", " ").title()]
            for i in range(len(df)):
                if i == 0:
                    row.append(f"{df.iloc[i][col]:.3f}")
                else:
                    change = df.iloc[i][col] - df.iloc[0][col]
                    row.append(f"{df.iloc[i][col]:.3f}\n({change:+.3f})")
            summary_data.append(row)

        table = ax.table(
            cellText=summary_data,
            colLabels=["Parameter"] + self.labels,
            cellLoc="center",
            loc="center",
            bbox=[0, 0, 1, 1],  # type: ignore
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 2)

        # Add title to summary
        ax.set_title(
            "Summary Table\n(changes vs unattached)",
            fontsize=11,
            fontweight="bold",
            pad=20,
        )

        plt.suptitle(
            "π-Stack Geometry Analysis: Bridge Effects",
            fontsize=14,
            fontweight="bold",
            y=0.98,
        )

        plt.tight_layout()
        plt.savefig("pi_stack_analysis_detailed.png", dpi=300, bbox_inches="tight")
        plt.show()

        return fig


# Usage
if __name__ == "__main__":
    # Define your XYZ files
    xyz_files = {
        "unattached": "C:/Users/401770/OneDrive - Los Alamos National Laboratory/PostDoc/LANL/UNM_Project/NSF_Purposal/ndi_unattached/ndi_trimer_unattached.xyz",
        "sandwich": "C:/Users/401770/OneDrive - Los Alamos National Laboratory/PostDoc/LANL/UNM_Project/NSF_Purposal/ndi_sandwiched/ndi_trimer_attached_three_anhydride.xyz",
        "zigzag": "C:/Users/401770/OneDrive - Los Alamos National Laboratory/PostDoc/LANL/UNM_Project/NSF_Purposal/ndi_loop/ndi_trimer_attached_four_anhydride.xyz",
    }

    # Your monomer indices (1-based, as provided)
    monomer_indices_raw = {
        "unattached": {
            "top": "197-218,222-223",
            "middle": "99-120,124-125",
            "bottom": "1-22,26-27",
        },
        "sandwich": {
            "top": "190-211,215-216",
            "middle": "96-117,121-122",
            "bottom": "1-22,26-27",
        },
        "zigzag": {
            "top": "189-210,214-215",
            "middle": "96-117,121-122",
            "bottom": "1-22,26-27",
        },
    }

    # Create temporary analyzer for parsing
    analyzer_temp = PiStackAnalyzer(xyz_files, {})

    # Convert string indices to lists (1-based to 0-based)
    monomer_indices = {}
    for struct_type in monomer_indices_raw:
        monomer_indices[struct_type] = {}
        for monomer in ["top", "middle", "bottom"]:
            monomer_indices[struct_type][monomer] = analyzer_temp.parse_indices(
                monomer_indices_raw[struct_type][monomer]
            )

            # Debug: Print first few indices to verify conversion
            print(
                f"{struct_type} - {monomer}: First 5 indices (0-based): {monomer_indices[struct_type][monomer][:5]}"
            )

    # Create analyzer with parsed indices
    analyzer = PiStackAnalyzer(xyz_files, monomer_indices)

    # Verify indices are correct
    analyzer.verify_indices()

    # Run analysis
    results_df = analyzer.analyze_all_structures()

    # Display results
    print("\n" + "=" * 80)
    print("STRUCTURAL ANALYSIS RESULTS")
    print("=" * 80)
    print(results_df.to_string(index=False, float_format="%.3f"))

    # Save results
    results_df.to_csv("pi_stack_analysis_results.csv", index=False, float_format="%.3f")
    print("\nResults saved to 'pi_stack_analysis_results.csv'")

    # Create visualizations
    fig = analyzer.plot_comparison(results_df)

    # Print summary of changes
    print("\n" + "=" * 80)
    print("SUMMARY OF CHANGES RELATIVE TO UNATTACHED STRUCTURE")
    print("=" * 80)

    ref = results_df.iloc[0]
    for i in range(1, len(results_df)):
        print(f"\n{results_df.iloc[i]['Structure'].upper()} vs UNATTACHED:")
        print("-" * 40)

        for col in results_df.columns[1:]:
            change = results_df.iloc[i][col] - ref[col]
            percent_change = (change / ref[col] * 100) if ref[col] != 0 else 0

            if "distance" in col or "slip" in col:
                if "slip_x" in col or "slip_y" in col:
                    print(f"  {col:25s}: {change:+7.3f} Å")
                else:
                    print(f"  {col:25s}: {change:+7.3f} Å ({percent_change:+6.1f}%)")
            else:
                print(f"  {col:25s}: {change:+7.2f}°")

    print("\nAnalysis complete!")
