# 🧬 VMD Cube File Visualization Scripts

![VMD](https://img.shields.io/badge/VMD-Molecular%20Visualization-blue?style=flat-square)
![TCL](https://img.shields.io/badge/Language-TCL-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square)

> **Professional-grade VMD scripts for automated cube file visualization and high-quality molecular orbital rendering**

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Scripts Overview](#-scripts-overview)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Usage](#-usage)
- [Output](#-output)
- [Advanced Configuration](#-advanced-configuration)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

## 🔬 Overview

This collection of VMD (Visual Molecular Dynamics) TCL scripts provides automated, high-quality visualization of molecular orbitals from cube files. The scripts are designed for computational chemistry researchers who need to generate publication-ready images of molecular orbitals with consistent styling and professional appearance.

### What These Scripts Do

- **Load and process** Gaussian cube files containing multiple orbital datasets
- **Configure professional display settings** with optimal lighting and materials
- **Generate isosurface representations** for both positive and negative orbital densities
- **Render high-resolution images** (2160×1080) in TGA format
- **Automate batch processing** of multiple orbitals with customizable parameters

## ✨ Features

### 🎨 **Professional Visualization**
- **Orthographic projection** for consistent perspective
- **Custom materials** with optimal shininess and lighting
- **High-resolution output** (2160×1080) for publications
- **White background** for clean presentation
- **Ray tracing** with shadows and ambient occlusion

### 🔧 **Advanced Display Configuration**
- **Licorice molecular representation** with customizable bond radius (0.1 Å)
- **Dual-color isosurfaces** (Blue: positive, Red: negative densities)
- **GLSL rendering** for enhanced visual quality
- **Material23** - Custom non-reflective material based on AOChalky

### 🚀 **Automation & Flexibility**
- **Command-line arguments** for all parameters
- **Batch processing** of multiple orbitals
- **Customizable isovalues** and orbital ranges
- **Automatic file naming** with clear conventions
- **Memory cleanup** after execution

## 📦 Scripts Overview

### 1. 🏗️ **Cube Loader Script** (`vmd_load_cube_script.tcl`)
**Purpose**: Load cube files and configure optimal display settings

```bash
vmd -dispdev text -e vmd_load_cube_script.tcl -args <input_cube_file> [output_directory]
```

**Features**:
- File validation and error checking
- Automatic directory creation
- Professional display configuration
- Material and lighting setup
- Global variable management

### 2. 🎬 **Render Script** (`updated_render_script.tcl`)
**Purpose**: Create isosurface representations and generate images

```bash
vmd -e updated_render_script.tcl -args [start_orbital] [end_orbital] [pos_isovalue] [neg_isovalue]
```

**Features**:
- Custom orbital range processing
- Flexible isovalue configuration
- Sequential rendering with progress tracking
- Automatic variable cleanup

### 3. 🎯 **Combined Script** (`vmd_combined_script.tcl`)
**Purpose**: All-in-one solution for complete automation

```bash
vmd -dispdev text -e vmd_combined_script.tcl -args <input_cube_file> [output_dir] [start_orbital] [end_orbital] [pos_isovalue] [neg_isovalue]
```

**Features**:
- Single-command execution
- Complete automation
- Automatic VMD exit in batch mode
- Comprehensive error handling

## 🔧 Prerequisites

### Software Requirements
- **VMD 1.9.3+** - [Download from UIUC](https://www.ks.uiuc.edu/Research/vmd/)
- **Operating System**: Windows, Linux, or macOS
- **Graphics**: OpenGL-capable graphics card recommended

### Input Files
- **Gaussian cube files** (`.cub`) containing molecular orbital data
- Files should contain multiple volume datasets (typically 6 orbitals)
- Compatible with Gaussian, ORCA, and other quantum chemistry packages

## 📥 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/vmd-cube-visualization.git
cd vmd-cube-visualization
```

### 2. Verify VMD Installation
```bash
vmd -dispdev text -e
# Should open VMD command line interface
```

### 3. Test Scripts (Optional)
```bash
# Test with sample data
vmd -dispdev text -e vmd_combined_script.tcl -args "sample_data/molecule.cub" "output"
```

## 🚀 Usage

### 🎯 Quick Start (Recommended)

For most users, the **combined script** provides the easiest experience:

```bash
# Basic usage with defaults
vmd -dispdev text -e vmd_combined_script.tcl -args "path/to/molecule.cub"

# Full customization
vmd -dispdev text -e vmd_combined_script.tcl -args \
  "C:/data/S1_orbs000474_479.cub" \
  "C:/output" \
  474 479 0.025 -0.025
```

### 📋 Two-Step Process

For more control or interactive work:

#### Step 1: Load and Configure
```bash
# Load cube file and setup display
vmd -e vmd_load_cube_script.tcl -args \
  "C:/data/molecule.cub" \
  "C:/output_directory"
```

#### Step 2: Render Images
```bash
# In the same VMD session
vmd> source updated_render_script.tcl

# Or with custom parameters
vmd -e updated_render_script.tcl -args 474 479 0.05 -0.05
```

### 📊 Parameter Reference

| Parameter | Description | Default | Example |
|-----------|-------------|---------|---------|
| `input_cube_file` | Path to cube file | *Required* | `"molecule.cub"` |
| `output_directory` | Output folder | Input file dir | `"C:/output"` |
| `start_orbital` | First orbital number | `474` | `470` |
| `end_orbital` | Last orbital number | `479` | `475` |
| `positive_isovalue` | Positive density value | `0.025` | `0.05` |
| `negative_isovalue` | Negative density value | `-0.025` | `-0.03` |

## 📁 Output

### 🖼️ Generated Files

The scripts produce several types of output:

#### **Image Files**
- **Format**: TGA (Tachyon format for high quality)
- **Resolution**: 2160 × 1080 pixels
- **Naming**: `Orbitals_XXX.tga` (where XXX is orbital number)
- **Content**: Molecular structure + dual-color isosurfaces

#### **Session Files**
- **Format**: VMD state file (`.vmd`)
- **Purpose**: Save VMD session for later analysis
- **Location**: `{output_dir}/cube_analysis_session.vmd`

### 📊 Example Output Structure
```
output_directory/
├── Orbitals_474.tga
├── Orbitals_475.tga
├── Orbitals_476.tga
├── Orbitals_477.tga
├── Orbitals_478.tga
├── Orbitals_479.tga
└── cube_analysis_session.vmd
```

### 🎨 Visual Features

Each rendered image contains:

| Element | Description | Color/Style |
|---------|-------------|-------------|
| **Molecular Structure** | Licorice representation | Atom-based coloring |
| **Positive Density** | Isosurface at +isovalue | Blue (ColorID 0) |
| **Negative Density** | Isosurface at -isovalue | Red (ColorID 1) |
| **Background** | Clean background | White |
| **Lighting** | Ray tracing enabled | Shadows + Ambient Occlusion |

## ⚙️ Advanced Configuration

### 🎨 Customizing Visual Appearance

#### Modify Isovalues for Different Systems
```bash
# For diffuse orbitals (lower values)
vmd -e script.tcl -args input.cub output 474 479 0.015 -0.015

# For compact orbitals (higher values)
vmd -e script.tcl -args input.cub output 474 479 0.05 -0.05
```

#### Color Customization
Edit the scripts to change isosurface colors:
```tcl
# In the script, change:
mol modcolor $pos_rep $molid ColorID 0  ;# Blue -> Change 0 to desired ColorID
mol modcolor $neg_rep $molid ColorID 1  ;# Red  -> Change 1 to desired ColorID
```

### 📐 Resolution and Quality Settings

#### High-Resolution Rendering
Modify display size in the scripts:
```tcl
# Change from default 2160x1080 to 4K
display resize 3840 2160

# Or for square format
display resize 2160 2160
```

#### Render Quality Options
```tcl
# Alternative renderers
render POV3 filename.pov     # POV-Ray format
render PostScript filename.ps # PostScript format
render TachyonInternal filename.tga # Current (highest quality)
```

### 🔧 Batch Processing Multiple Files

Create a batch script for processing multiple cube files:

#### Windows Batch Script (`process_all.bat`)
```batch
@echo off
for %%f in (*.cub) do (
    echo Processing %%f...
    vmd -dispdev text -e vmd_combined_script.tcl -args "%%f" "output/%%~nf"
)
```

#### Linux/macOS Shell Script (`process_all.sh`)
```bash
#!/bin/bash
for file in *.cub; do
    echo "Processing $file..."
    base=$(basename "$file" .cub)
    vmd -dispdev text -e vmd_combined_script.tcl -args "$file" "output/$base"
done
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### ❌ **"Error: Could not load cube file"**
**Causes:**
- File path contains spaces or special characters
- File doesn't exist or is corrupted
- Insufficient permissions

**Solutions:**
```bash
# Use quotes around file paths
vmd -e script.tcl -args "C:/path with spaces/file.cub"

# Check file existence
ls -la "path/to/file.cub"  # Linux/macOS
dir "path\to\file.cub"     # Windows

# Verify file format
head -20 "file.cub"  # Should show cube file header
```

#### ❌ **"Required global variables not found"**
**Cause:** Running render script without loader script

**Solutions:**
```bash
# Option 1: Use combined script
vmd -dispdev text -e vmd_combined_script.tcl -args "input.cub"

# Option 2: Run in same VMD session
vmd
vmd> source vmd_load_cube_script.tcl
vmd> source updated_render_script.tcl
```

#### ❌ **"No volume data found"**
**Cause:** Cube file doesn't contain orbital data

**Solutions:**
- Verify cube file contains multiple datasets
- Check quantum chemistry calculation output
- Ensure proper cube file generation settings

#### ❌ **Memory Issues**
**Symptoms:** VMD crashes or becomes unresponsive

**Solutions:**
```bash
# Reduce resolution
display resize 1080 540

# Process fewer orbitals at once
vmd -e script.tcl -args input.cub output 474 476  # Only 3 orbitals

# Increase system memory or use workstation
```

#### ❌ **Rendering Quality Issues**
**Solutions:**
```tcl
# Ensure GLSL is supported
display rendermode GLSL

# Alternative rendering modes
display rendermode Normal  # Fallback option

# Check graphics drivers
# Update to latest GPU drivers
```

### 📋 Debug Mode

Enable verbose output by adding debug statements:

```tcl
# Add at the beginning of scripts
set debug_mode 1

# Add debug output throughout
if {$debug_mode} {
    puts "DEBUG: Variable value = $variable_name"
}
```

## 🤝 Contributing

We welcome contributions from the computational chemistry community!

### 🔧 Development Setup

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Test thoroughly** with various cube file formats
4. **Update documentation** if needed
5. **Submit pull request**

### 📝 Contribution Guidelines

- **Code Style**: Follow existing TCL conventions
- **Testing**: Test with different quantum chemistry packages
- **Documentation**: Update README for new features
- **Backwards Compatibility**: Maintain compatibility with existing workflows

### 🐛 Bug Reports

Please include:
- VMD version
- Operating system
- Sample cube file (if possible)
- Complete error messages
- Steps to reproduce

### 💡 Feature Requests

We're particularly interested in:
- Support for additional file formats
- New visualization styles
- Performance optimizations
- Integration with other tools

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 VMD Cube Visualization Scripts

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

## 🙏 Acknowledgments

- **UIUC VMD Development Team** - For creating the excellent VMD software
- **Computational Chemistry Community** - For feedback and testing
- **Contributors** - Thank you for your improvements and bug reports

## 📚 References and Further Reading

### VMD Documentation
- [VMD User Guide](https://www.ks.uiuc.edu/Research/vmd/vmd-1.9.3/ug/)
- [VMD Scripting Tutorial](https://www.ks.uiuc.edu/Research/vmd/script_library/)
- [TCL/Tk Documentation](https://www.tcl.tk/doc/)

### Cube File Format
- [Gaussian Cube File Format](https://gaussian.com/cubegen/)
- [Molecular Orbital Visualization](https://doi.org/10.1021/acs.jcim.9b00725)

### Computational Chemistry
- [Quantum Chemistry Visualization](https://doi.org/10.1002/wcms.1481)
- [Molecular Orbital Theory](https://doi.org/10.1021/ed100889v)

---

## 🚀 Quick Start Summary

```bash
# 1. Download scripts
git clone https://github.com/Ajaykhanna/Quantum_Mechanics_Projects

# 2. Navigate to directory
cd vmd-cube-visualization

# 3. Run with your cube file
vmd -dispdev text -e vmd_combined_script.tcl -args "your_file.cub" "output_folder"

# 4. Find your images in the output folder!
```

**That's it!** Your high-quality molecular orbital visualizations are ready for publication. 🎉

---

*For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/Ajaykhanna/Quantum_Mechanics_Projects) or contact the maintainers.*