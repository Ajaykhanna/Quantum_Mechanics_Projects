# VMD TCL Script for loading cube file, configuring display, and rendering
# Combined Script: Load cube file, setup display, create representations, and render images
#
# Usage: vmd -dispdev text -e combined_script.tcl -args <input_cube_file> [output_directory] [start_orbital] [end_orbital] [positive_isovalue] [negative_isovalue]
# Example: vmd -dispdev text -e combined_script.tcl -args "C:/path/to/file.cub" "C:/output" 474 479 0.025 -0.025

# Parse command line arguments
if {$argc < 1} {
    puts "Usage: vmd -e combined_script.tcl -args <input_cube_file> \[output_directory\] \[start_orbital\] \[end_orbital\] \[positive_isovalue\] \[negative_isovalue\]"
    puts "Example: vmd -e combined_script.tcl -args \"C:/path/to/file.cub\" \"C:/output\" 474 479 0.025 -0.025"
    puts "\nParameters:"
    puts "  input_cube_file  : Path to the cube file (required)"
    puts "  output_directory : Output directory (optional, defaults to input file directory)"
    puts "  start_orbital    : Starting orbital number (optional, default: 474)"
    puts "  end_orbital      : Ending orbital number (optional, default: 479)"
    puts "  positive_isovalue: Positive isovalue (optional, default: 0.025)"
    puts "  negative_isovalue: Negative isovalue (optional, default: -0.025)"
    exit
}

# Get input cube file path
set cube_file_path [lindex $argv 0]

# Get output directory (optional, default to same directory as input file)
if {$argc >= 2 && [lindex $argv 1] != ""} {
    set output_dir [lindex $argv 1]
} else {
    set output_dir [file dirname $cube_file_path]
}

# Get orbital parameters with defaults
set start_orbital 474
set end_orbital 479
set pos_isovalue 0.025
set neg_isovalue -0.025

if {$argc >= 3} {
    set start_orbital [lindex $argv 2]
}
if {$argc >= 4} {
    set end_orbital [lindex $argv 3]
}
if {$argc >= 5} {
    set pos_isovalue [lindex $argv 4]
}
if {$argc >= 6} {
    set neg_isovalue [lindex $argv 5]
}

puts "=== VMD Cube File Processing ==="
puts "Input cube file: $cube_file_path"
puts "Output directory: $output_dir"
puts "Orbital range: $start_orbital to $end_orbital"
puts "Isovalues: +$pos_isovalue / $neg_isovalue"

# Check if input file exists
if {![file exists $cube_file_path]} {
    puts "Error: Input cube file does not exist: $cube_file_path"
    exit
}

# Create output directory if it doesn't exist
if {![file exists $output_dir]} {
    file mkdir $output_dir
    puts "Created output directory: $output_dir"
}

# ==================== LOADING SECTION ====================

puts "\n=== Loading cube file and configuring display ==="

# Load the cube file
puts "Loading cube file: $cube_file_path"
set molid [mol new $cube_file_path type cube first 0 last -1 step 1 filebonds 1 autobonds 1 waitfor all]

# Check if molecule was loaded successfully
if {$molid == -1} {
    puts "Error: Could not load cube file"
    exit
}

puts "Successfully loaded molecule with ID: $molid"

# Get information about volume data
set num_volumes [molinfo $molid get numvolumedata]
puts "Number of volume datasets: $num_volumes"

# Print volume information (if available)
if {$num_volumes > 0} {
    puts "Available volume datasets:"
    for {set vol_idx 0} {$vol_idx < $num_volumes} {incr vol_idx} {
        puts "  Volume $vol_idx: vol$vol_idx"
    }
} else {
    puts "Warning: No volume data found in the cube file"
    exit
}

# Configure display settings
puts "\nConfiguring display settings..."

# 1. Set display to Orthographic
display projection Orthographic
puts "✓ Set projection to Orthographic"

# 2. Turn off AXES and Depth Cueing
axes location off
display depthcue off
puts "✓ Turned off axes and depth cueing"

# 3. Set background to White
color Display Background white
puts "✓ Set background to white"

# 4. Set display size to 2160x1080
display resize 2160 1080
puts "✓ Set display size to 2160x1080"

# 5. Set Rendermode to GLSL
display rendermode GLSL
puts "✓ Set render mode to GLSL"

# 6. Turn on Shadows and Ambient Occlusion in Ray Tracing Options
display shadows on
display ambientocclusion on
puts "✓ Enabled shadows and ambient occlusion"

# 7. Create new material (Material 23) based on AOChalky with Shininess 0.0
material add Material23
material change shininess Material23 0.0
material change ambient Material23 0.15
material change diffuse Material23 0.65
material change specular Material23 0.0
material change opacity Material23 1.0
puts "✓ Created Material23 with shininess 0.0"

# Set the first representation to Licorice with Bond Radius 0.1 and apply Material23
mol modstyle 0 $molid Licorice 0.1 12.0 12.0
mol modcolor 0 $molid Name
mol modmaterial 0 $molid Material23
puts "✓ Set first representation to Licorice with bond radius 0.1 and Material23"

# Extract base filename without extension for naming convention
set base_filename [file rootname [file tail $cube_file_path]]

puts "✓ Display setup completed"

# ==================== RENDERING SECTION ====================

puts "\n=== Creating representations and rendering ==="

# Calculate number of orbitals to process
set num_orbitals [expr $end_orbital - $start_orbital + 1]
set max_volumes [expr {$num_volumes < $num_orbitals ? $num_volumes : $num_orbitals}]

puts "Processing $max_volumes orbital datasets (orbitals $start_orbital to [expr $start_orbital + $max_volumes - 1])"

# Create isosurface pairs for each density 
set rep_pairs {}  ;# Store representation pairs for each volume

puts "\nCreating representations for $max_volumes volume datasets..."

for {set i 0} {$i < $max_volumes} {incr i} {
    set current_orbital [expr $start_orbital + $i]
    puts "Creating isosurface representations for vol$i (orbital $current_orbital)"
    
    # Add positive isosurface representation
    mol addrep $molid
    set pos_rep [expr [molinfo $molid get numreps] - 1]
    mol modstyle $pos_rep $molid Isosurface $pos_isovalue $i 0 0 1
    mol modcolor $pos_rep $molid ColorID 0  ;# Blue
    mol modmaterial $pos_rep $molid Material23
    
    # Add negative isosurface representation
    mol addrep $molid
    set neg_rep [expr [molinfo $molid get numreps] - 1]
    mol modstyle $neg_rep $molid Isosurface $neg_isovalue $i 0 0 1
    mol modcolor $neg_rep $molid ColorID 1  ;# Red
    mol modmaterial $neg_rep $molid Material23
    
    # Store the representation pair
    lappend rep_pairs [list $pos_rep $neg_rep]
    
    puts "✓ Created representations $pos_rep (positive) and $neg_rep (negative) for orbital $current_orbital"
    
    # Initially hide these representations (will show them one by one during rendering)
    mol showrep $molid $pos_rep off
    mol showrep $molid $neg_rep off
}

# Function to render image for a specific volume
proc render_volume {molid vol_index rep_pairs output_dir base_filename start_orbital pos_isovalue neg_isovalue} {
    set current_orbital [expr $start_orbital + $vol_index]
    set vol_name "orbital_$current_orbital"
    puts "\nRendering volume: $vol_name (dataset $vol_index, orbital $current_orbital)"
    
    # Hide all isosurface representations first (keep licorice visible)
    foreach pair $rep_pairs {
        set pos_rep [lindex $pair 0]
        set neg_rep [lindex $pair 1]
        mol showrep $molid $pos_rep off
        mol showrep $molid $neg_rep off
    }
    
    # Show only the current volume's isosurfaces
    set current_pair [lindex $rep_pairs $vol_index]
    set pos_rep [lindex $current_pair 0]
    set neg_rep [lindex $current_pair 1]
    
    mol showrep $molid $pos_rep on  ;# Positive isosurface
    mol showrep $molid $neg_rep on  ;# Negative isosurface
    
    puts "Showing representations: 0 (licorice), $pos_rep (positive $pos_isovalue), $neg_rep (negative $neg_isovalue)"
    
    # Wait for representations to update
    display update
    display update ui
    
    # Small delay to ensure rendering is complete
    after 1000
    
    # Set output filename as "Orbitals_#orbital_num.tga"
    set output_file "${output_dir}/Orbitals_${current_orbital}.tga"
    
    # Render the image
    render TachyonInternal $output_file
    
    puts "✓ Rendered: $output_file"
}

# Loop through all available densities and render images
puts "\n=== Starting rendering process for orbitals $start_orbital to [expr $start_orbital + $max_volumes - 1] ==="
for {set i 0} {$i < $max_volumes} {incr i} {
    render_volume $molid $i $rep_pairs $output_dir $base_filename $start_orbital $pos_isovalue $neg_isovalue
}

# Show all representations at the end
puts "\nShowing all representations..."
for {set rep 0} {$rep < [molinfo $molid get numreps]} {incr rep} {
    mol showrep $molid $rep on
}

puts "\n=== All processing completed successfully! ==="
puts "Total representations created: [molinfo $molid get numreps]"

# Print summary of created representations
puts "\nRepresentation Summary:"
puts "Rep 0: Licorice (Name coloring, Material23)"
for {set i 0} {$i < $max_volumes} {incr i} {
    set pair [lindex $rep_pairs $i]
    set pos_rep [lindex $pair 0]
    set neg_rep [lindex $pair 1]
    set current_orbital [expr $start_orbital + $i]
    puts "Orbital $current_orbital: Rep $pos_rep (positive $pos_isovalue, blue), Rep $neg_rep (negative $neg_isovalue, red)"
}

# Optional: Save the VMD session
set session_file "${output_dir}/${base_filename}_session.vmd"
# Uncomment the next line if you want to save the VMD session
# save_state $session_file

puts "\n=== Final Summary ==="
puts "Input file: $cube_file_path"
puts "Images saved to: $output_dir"
puts "Filename pattern: Orbitals_XXX.tga (where XXX is the orbital number)"
puts "Orbital range processed: $start_orbital to [expr $start_orbital + $max_volumes - 1]"
puts "Isovalues used: +$pos_isovalue / $neg_isovalue"

# Clear all variables and clean up
puts "\nCleaning up variables..."

# Clear local variables
foreach var {cube_file_path output_dir start_orbital end_orbital pos_isovalue neg_isovalue molid num_volumes base_filename num_orbitals max_volumes rep_pairs session_file} {
    if {[info exists $var]} {
        unset $var
        puts "✓ Cleared $var"
    }
}

puts "All variables have been cleared."

# Exit VMD if running in text mode
if {[string match "*text*" [display get]]} {
    puts "Exiting VMD..."
    quit
}