# VMD TCL Script for creating isosurface representations and rendering images
# Script 2: Create representations and render images
#
# Usage: vmd -dispdev text -e render_script.tcl -args [start_orbital] [end_orbital] [positive_isovalue] [negative_isovalue]
# Example: vmd -e render_script.tcl -args 474 479 0.025 -0.025
# If no arguments provided, defaults will be used

# Parse command line arguments
set start_orbital 474  ;# Default start orbital
set end_orbital 479    ;# Default end orbital  
set pos_isovalue 0.025 ;# Default positive isovalue
set neg_isovalue -0.025 ;# Default negative isovalue

if {$argc >= 1} {
    set start_orbital [lindex $argv 0]
}
if {$argc >= 2} {
    set end_orbital [lindex $argv 1]
}
if {$argc >= 3} {
    set pos_isovalue [lindex $argv 2]
}
if {$argc >= 4} {
    set neg_isovalue [lindex $argv 3]
}

puts "Rendering parameters:"
puts "  Start orbital: $start_orbital"
puts "  End orbital: $end_orbital"
puts "  Positive isovalue: $pos_isovalue"
puts "  Negative isovalue: $neg_isovalue"

# Check if global variables from the loading script exist
if {![info exists ::cube_molid] || ![info exists ::cube_num_volumes]} {
    puts "Error: Please run the cube loading script first!"
    puts "Required global variables ::cube_molid and ::cube_num_volumes not found."
    puts "\nTo fix this issue, you have two options:"
    puts "1. Run both scripts in the same VMD session:"
    puts "   vmd> source load_cube_script.tcl"
    puts "   vmd> source render_script.tcl"
    puts ""
    puts "2. Or run the loader script first, then this script in the same VMD instance:"
    puts "   vmd -e load_cube_script.tcl -args \"input.cub\" \"output_dir\""
    puts "   # Then in the VMD console:"
    puts "   vmd> source render_script.tcl"
    puts ""
    puts "The scripts must run in the same VMD session to share variables."
    exit
}

# Get values from global variables
set molid $::cube_molid
set num_volumes $::cube_num_volumes
set output_dir $::cube_output_dir

# Verify molecule still exists
if {[lsearch [molinfo list] $molid] == -1} {
    puts "Error: Molecule ID $molid not found. Please reload the cube file."
    exit
}

puts "\nUsing molecule ID: $molid"
puts "Number of volume datasets: $num_volumes"
puts "Output directory: $output_dir"

# Calculate number of orbitals to process
set num_orbitals [expr $end_orbital - $start_orbital + 1]
set max_volumes [expr {$num_volumes < $num_orbitals ? $num_volumes : $num_orbitals}]

puts "\nProcessing $max_volumes orbital datasets (orbitals $start_orbital to [expr $start_orbital + $max_volumes - 1])"

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
proc render_volume {molid vol_index rep_pairs output_dir start_orbital pos_isovalue neg_isovalue} {
    set current_orbital [expr $start_orbital + $vol_index]
    puts "\nRendering volume: orbital_$current_orbital (dataset $vol_index, orbital $current_orbital)"
    
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
    
    puts "Rendered: $output_file"
}

# Create output directory if it doesn't exist (Windows-compatible)
if {![file exists $output_dir]} {
    file mkdir $output_dir
    puts "Created output directory: $output_dir"
}

# Loop through all available densities and render images
puts "\n=== Starting rendering process for orbitals $start_orbital to [expr $start_orbital + $max_volumes - 1] ==="
for {set i 0} {$i < $max_volumes} {incr i} {
    render_volume $molid $i $rep_pairs $output_dir $start_orbital $pos_isovalue $neg_isovalue
}

# Show all representations at the end
puts "\nShowing all representations..."
for {set rep 0} {$rep < [molinfo $molid get numreps]} {incr rep} {
    mol showrep $molid $rep on
}

puts "\n=== All density visualizations have been rendered! ==="
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

# Save the VMD session
set session_file "${output_dir}/cube_analysis_session.vmd"
save_state $session_file

puts "\n=== Rendering script completed successfully! ==="
puts "Images saved to: $output_dir"
puts "Filename pattern: Orbitals_XXX.tga (where XXX is the orbital number)"

# Clear all variables and clean up
puts "\nCleaning up variables..."

# Clear global variables set by the loader script
if {[info exists ::cube_molid]} {
    unset ::cube_molid
    puts "Cleared ::cube_molid"
}
if {[info exists ::cube_num_volumes]} {
    unset ::cube_num_volumes
    puts "Cleared ::cube_num_volumes"
}
if {[info exists ::cube_output_dir]} {
    unset ::cube_output_dir
    puts "Cleared ::cube_output_dir"
}
if {[info exists ::cube_input_file]} {
    unset ::cube_input_file
    puts "Cleared ::cube_input_file"
}
if {[info exists ::cube_base_filename]} {
    unset ::cube_base_filename
    puts "Cleared ::cube_base_filename"
}

# Clear local variables
foreach var {molid num_volumes output_dir start_orbital end_orbital pos_isovalue neg_isovalue num_orbitals max_volumes rep_pairs session_file} {
    if {[info exists $var]} {
        unset $var
        puts "Cleared $var"
    }
}

puts "All variables have been cleared."