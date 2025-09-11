# VMD TCL Script for loading cube file and configuring display settings
# Script 1: Load cube file and setup display

# Set the path to your cube file
set cube_file_path "/data/TSM/LC_wPBE/vacuum/cube_out/S1_orbs000474_479.cub"

set cube_output_dir "/data/TSM/LC_wPBE/vacuum/cube_out"

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
}

# Configure display settings
puts "\nConfiguring display settings..."

# 1. Set display to Orthographic
display projection Orthographic
puts "Set projection to Orthographic"

# 2. Turn off AXES and Depth Cueing
axes location off
display depthcue off
puts "Turned off axes and depth cueing"

# 3. Set background to White
color Display Background white
puts "Set background to white"

# 4. Set display size to 2160x1080
display resize 2160 1080
puts "Set display size to 2160x1080"

# 5. Set Rendermode to GLSL
display rendermode GLSL
puts "Set render mode to GLSL"

# 6. Turn on Light 3, Shadows and Ambient Occlusion in Ray Tracing Options
light 3 on
display shadows on
display ambientocclusion on
puts "Enabled shadows and ambient occlusion"

# 7. Create new material (Material 23) based on AOChalky with Shininess 0.0
material add Material23
material change shininess Material23 0.0
material change ambient Material23 0.15
material change diffuse Material23 0.65
material change specular Material23 0.0
material change opacity Material23 1.0
puts "Created Material23 with shininess 0.0"

# Set the first representation to Licorice with Bond Radius 0.1 and apply Material23
mol modstyle 0 $molid Licorice 0.1 12.0 12.0
mol modcolor 0 $molid Name
mol modmaterial 0 $molid Material23
puts "Set first representation to Licorice with bond radius 0.1 and Material23"

# Store molecule ID and volume count in global variables for use in the next script
set ::cube_molid $molid
set ::cube_num_volumes $num_volumes

puts "\n=== Cube file loading and display setup completed ==="
puts "Molecule ID: $molid"
puts "Number of volumes: $num_volumes"
puts "Ready for representation creation and rendering!"
puts "\nNext step: Run the rendering script to create isosurfaces and generate images."