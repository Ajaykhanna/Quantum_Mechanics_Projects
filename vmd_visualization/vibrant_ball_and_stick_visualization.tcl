# VMD TCL script to exactly recreate the ball-and-stick representation from the image
# Load your molecule file first (e.g., mol new "molecule.pdb")

# Set the molecule ID (assuming it's the first/top molecule)
set molid [molinfo top]

# Clear all existing representations
mol delrep 0 $molid

# Method 1: Using separate representations for precise control (RECOMMENDED)
# This matches the image more accurately

# Add atoms as spheres with precise sizing
mol representation VDW 0.35
mol color Name  
mol selection "all"
mol material Opaque
mol addrep $molid

# Add bonds as thin cylinders
mol representation DynamicBonds 1.6 0.08
mol color Name
mol selection "all" 
mol material Opaque
mol addrep $molid

# Set the exact background color - blue gradient
color Display Background blue2

# Display settings to match the image
display projection orthographic
display depthcue off
display rendermode GLSL
display shadows on
display ambientocclusion on

# Lighting setup for clean appearance
light 0 on
light 1 on  
light 2 off
light 3 on

# Set light positions for optimal rendering
light 0 rot x -10
light 0 rot y 10
light 1 rot x 10 
light 1 rot y -10

# Color definitions to exactly match CPK coloring in image
color Name C gray
color Name H white
color Name N blue2
color Name O red2
color Name S yellow2
color Name P orange

# View optimization
mol top $molid
display resetview

# Alternative Method 2: Single CPK representation (uncomment if preferred)
# mol delrep 0 $molid
# mol delrep 0 $molid
# mol representation CPK 0.7 0.08
# mol color Name
# mol selection "all"
# mol material Opaque  
# mol addrep $molid

puts "Exact ball-and-stick representation applied!"
puts "Atom spheres: VDW 0.35"
puts "Bond cylinders: DynamicBonds 1.6 0.08" 
puts "Adjust viewing angle as needed to match your reference image."