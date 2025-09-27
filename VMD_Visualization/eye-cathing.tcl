# VMD Creative Molecular Visualization Scripts
# 5 Eye-catching representation styles suitable for both small and large molecules
# Load your molecule first: mol new "molecule.pdb"

set molid [molinfo top]

# ==============================================================================
# STYLE 1: NEON GLOW EFFECT - Perfect for presentations and posters
# ==============================================================================

proc style_neon_glow {} {
    global molid
    
    # Clear existing representations
    while {[molinfo $molid get numreps] > 0} {
        mol delrep 0 $molid
    }
    
    # Background - Dark for glow effect
    color Display Background black
    
    # Main structure - Bright colors
    mol representation Licorice 0.5 20.0 20.0
    mol color ColorID 4  # Yellow core
    mol selection "all"
    mol material Glossy
    mol addrep $molid
    
    # Glow layer 1 - Larger, transparent
    mol representation Licorice 0.8 20.0 20.0
    mol color ColorID 1  # Red glow
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 1 $molid Transparent
    mol modmaterial 1 $molid {Opacity 0.3}
    
    # Glow layer 2 - Even larger, more transparent
    mol representation Licorice 1.2 20.0 20.0
    mol color ColorID 11  # Purple outer glow
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 2 $molid {Opacity 0.15}
    
    # Atom highlights
    mol representation VDW 0.3
    mol color Name
    mol selection "not hydrogen"
    mol material EdgyShiny
    mol addrep $molid
    
    display rendermode GLSL
    display shadows on
    display ambientocclusion on
    
    puts "NEON GLOW style applied!"
}

# ==============================================================================
# STYLE 2: GLASS CRYSTAL - Elegant transparent look
# ==============================================================================

proc style_glass_crystal {} {
    global molid
    
    while {[molinfo $molid get numreps] > 0} {
        mol delrep 0 $molid
    }
    
    # Gradient background
    color Display Background white
    color Display BackgroundTop blue2
    color Display BackgroundBot white
    
    # Main structure - Glass-like
    mol representation NewCartoon 0.8 15.0 4.0
    mol color Structure
    mol selection "protein or nucleic"
    mol material Glass3
    mol addrep $molid
    
    # Bonds as glass tubes
    mol representation Licorice 0.3 20.0 20.0
    mol color ColorID 0  # Blue glass
    mol selection "all"
    mol material Glass2
    mol addrep $molid
    mol modmaterial 1 $molid {Opacity 0.6}
    
    # Important atoms highlighted
    mol representation VDW 0.4
    mol color Name
    mol selection "heteroatom and not hydrogen"
    mol material Glossy
    mol addrep $molid
    
    # Reflective base
    mol representation QuickSurf 1.0 0.5 1.0 3.0
    mol color ColorID 8  # White base
    mol selection "all"
    mol material Mirror
    mol addrep $molid
    mol modmaterial 3 $molid {Opacity 0.2}
    
    display rendermode GLSL
    display shadows on
    light 2 on
    
    puts "GLASS CRYSTAL style applied!"
}

# ==============================================================================
# STYLE 3: HOLOGRAPHIC WIREFRAME - Futuristic sci-fi look
# ==============================================================================

proc style_holographic {} {
    global molid
    
    while {[molinfo $molid get numreps] > 0} {
        mol delrep 0 $molid
    }
    
    # Dark cosmic background
    color Display Background black
    
    # Wireframe structure - Cyan hologram
    mol representation Licorice 0.1 20.0 20.0
    mol color ColorID 10  # Cyan
    mol selection "all"
    mol material Goodsell
    mol addrep $molid
    
    # Energy nodes at atoms
    mol representation VDW 0.2
    mol color ColorID 10  # Cyan nodes
    mol selection "not hydrogen"
    mol material HardPlastic
    mol addrep $molid
    
    # Glowing outline
    mol representation QuickSurf 2.0 1.0 1.0 1.0
    mol color ColorID 3  # Orange outline glow
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 2 $molid {Opacity 0.1}
    
    # Data points
    mol representation Points 3.0
    mol color ColorID 12  # Electric blue
    mol selection "name CA or name P or name N1"
    mol material Glossy
    mol addrep $molid
    
    display rendermode GLSL
    display depthcue on
    
    puts "HOLOGRAPHIC WIREFRAME style applied!"
}

# ==============================================================================
# STYLE 4: RAINBOW ENERGY FIELD - Dynamic multicolor glow (FIXED)
# ==============================================================================

proc style_rainbow_energy {} {
    global molid
    
    while {[molinfo $molid get numreps] > 0} {
        mol delrep 0 $molid
    }
    
    # Dark background for glow effect
    color Display Background black
    
    # Core structure - Use safe coloring method
    mol representation NewCartoon 1.0 15.0 4.0
    mol color ResType
    mol selection "protein or nucleic"
    mol material EdgyShiny
    mol addrep $molid
    
    # If no protein/nucleic, use all atoms with licorice
    mol representation Licorice 0.3 20.0 20.0
    mol color Name
    mol selection "all and not (protein or nucleic)"
    mol material EdgyShiny
    mol addrep $molid
    
    # Energy field layer 1 - Inner glow (Red)
    mol representation QuickSurf 1.5 1.0 1.0 2.0
    mol color ColorID 1  # Red
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    # Set transparency for this representation
    set rep_num [expr [molinfo $molid get numreps] - 1]
    mol modmaterial $rep_num $molid {Opacity 0.4}
    
    # Energy field layer 2 - Middle glow (Blue)
    mol representation QuickSurf 2.5 1.5 1.0 2.0
    mol color ColorID 0  # Blue
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    set rep_num [expr [molinfo $molid get numreps] - 1]
    mol modmaterial $rep_num $molid {Opacity 0.25}
    
    # Energy field layer 3 - Outer glow (Green)
    mol representation QuickSurf 4.0 2.0 1.0 2.0
    mol color ColorID 7  # Green
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    set rep_num [expr [molinfo $molid get numreps] - 1]
    mol modmaterial $rep_num $molid {Opacity 0.1}
    
    # Lightning bonds - only if bonds exist
    mol representation DynamicBonds 2.0 0.2
    mol color ColorID 10  # Cyan
    mol selection "all"
    mol material Glossy
    mol addrep $molid
    
    display rendermode GLSL
    display shadows on
    display ambientocclusion on
    
    puts "RAINBOW ENERGY FIELD style applied successfully!"
}

# ==============================================================================
# STYLE 5: METALLIC SCULPTURE - Artistic metallic finish
# ==============================================================================

proc style_metallic_sculpture {} {
    global molid
    
    while {[molinfo $molid get numreps] > 0} {
        mol delrep 0 $molid
    }
    
    # Studio lighting background
    color Display Background white
    color Display BackgroundTop silver
    color Display BackgroundBot gray
    
    # Main structure - Brushed metal
    mol representation NewCartoon 1.2 15.0 6.0
    mol color ColorID 23  # Silver
    mol selection "protein or nucleic"
    mol material BrushedMetal
    mol addrep $molid
    
    # Secondary structure - Copper accents
    mol representation Tube 0.8 15.0
    mol color ColorID 3  # Orange copper
    mol selection "alpha or sheet"
    mol material AOShiny
    mol addrep $molid
    
    # Active sites - Gold highlights
    mol representation VDW 0.6
    mol color ColorID 4  # Yellow gold
    mol selection "heteroatom and not hydrogen"
    mol material AOEdgy
    mol addrep $molid
    
    # Surface detail
    mol representation MSMS 1.5 1.0
    mol color ColorID 2  # Gray steel
    mol selection "all"
    mol material Steel
    mol addrep $molid
    mol modmaterial 3 $molid {Opacity 0.3}
    
    # Reflective base platform
    mol representation QuickSurf 8.0 4.0 1.0 1.0
    mol color ColorID 15  # Black chrome base
    mol selection "all"
    mol material Mirror
    mol addrep $molid
    mol modmaterial 4 $molid {Opacity 0.15}
    
    display rendermode GLSL
    display shadows on
    display ambientocclusion on
    light 0 on
    light 1 on
    light 2 on
    
    puts "METALLIC SCULPTURE style applied!"
}

# ==============================================================================
# CONVENIENCE FUNCTIONS TO APPLY STYLES
# ==============================================================================

puts "======================================"
puts "VMD Creative Molecular Representations"
puts "======================================"
puts ""
puts "Available styles:"
puts "1. style_neon_glow        - Neon glow effect with multiple layers"
puts "2. style_glass_crystal    - Elegant transparent glass look"  
puts "3. style_holographic      - Futuristic sci-fi wireframe"
puts "4. style_rainbow_energy   - Dynamic multicolor energy field"
puts "5. style_metallic_sculpture - Artistic metallic finish"
puts ""
puts "Usage: Just type the function name, e.g. 'style_neon_glow'"
puts "======================================"

# ==============================================================================
# STYLE 6: MOLECULAR ORBITALS WITH CONTEXT - Scientific orbital visualization
# ==============================================================================

proc style_orbital_context {} {
    global molid
    
    while {[molinfo $molid get numreps] > 0} {
        mol delrep 0 $molid
    }
    
    # Clean white background
    color Display Background white
    
    # Background context molecules - Very transparent wireframe
    mol representation Licorice 0.08 20.0 20.0
    mol color ColorID 2  # Gray
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 0 $molid {Opacity 0.15}
    
    # Background atoms - Small transparent spheres
    mol representation VDW 0.15
    mol color Name
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 1 $molid {Opacity 0.2}
    
    # Main molecular backbone - Bold black bonds
    mol representation Licorice 0.4 20.0 20.0
    mol color ColorID 16  # Black
    mol selection "backbone or (resname UNK and not hydrogen)"
    mol material AOChalky
    mol addrep $molid
    
    # Key atoms - Prominent spheres with CPK colors
    mol representation VDW 0.8
    mol color Name
    mol selection "backbone or heteroatom and not hydrogen"
    mol material AOShiny
    mol addrep $molid
    
    # Molecular orbitals - Blue lobes (positive phase)
    mol representation QuickSurf 3.0 1.5 1.0 2.0
    mol color ColorID 0  # Blue
    mol selection "all"
    mol material Glass1
    mol addrep $molid
    mol modmaterial 4 $molid {Opacity 0.4}
    
    # Molecular orbitals - Red lobes (negative phase)
    mol representation QuickSurf 3.5 1.8 1.0 2.5
    mol color ColorID 1  # Red
    mol selection "all"
    mol material Glass1
    mol addrep $molid
    mol modmaterial 5 $molid {Opacity 0.3}
    
    # Additional orbital cloud - Larger, more diffuse
    mol representation QuickSurf 4.5 2.5 1.0 3.0
    mol color ColorID 23  # Silver/gray
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 6 $molid {Opacity 0.15}
    
    display rendermode GLSL
    display shadows off
    display depthcue off
    display projection orthographic
    
    puts "MOLECULAR ORBITALS WITH CONTEXT style applied!"
}

# ==============================================================================
# STYLE 6B: ENHANCED ORBITAL VISUALIZATION - Alternative version
# ==============================================================================

proc style_enhanced_orbitals {} {
    global molid
    
    while {[molinfo $molid get numreps] > 0} {
        mol delrep 0 $molid
    }
    
    # Clean background
    color Display Background white
    
    # Context network - Ultra-light molecular framework
    mol representation Points 1.0
    mol color ColorID 2  # Gray points
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 0 $molid {Opacity 0.1}
    
    # Thin connecting lines for context
    mol representation DynamicBonds 2.5 0.02
    mol color ColorID 2  # Gray
    mol selection "all" 
    mol material Transparent
    mol addrep $molid
    mol modmaterial 1 $molid {Opacity 0.08}
    
    # Primary molecular chain - Thick representation
    mol representation Licorice 0.5 20.0 20.0
    mol color ColorID 8  # White/light gray
    mol selection "protein or nucleic or (not hydrogen and occupancy > 0.5)"
    mol material Opaque
    mol addrep $molid
    
    # Key functional atoms
    mol representation VDW 1.0
    mol color Name
    mol selection "heteroatom and not hydrogen"
    mol material EdgyShiny
    mol addrep $molid
    
    # Orbital lobe 1 - HOMO (blue)
    mol representation MSMS 2.0 1.5
    mol color ColorID 7  # Green-blue
    mol selection "all"
    mol material Glass2
    mol addrep $molid
    mol modmaterial 4 $molid {Opacity 0.45}
    
    # Orbital lobe 2 - LUMO (red)
    mol representation MSMS 2.5 2.0  
    mol color ColorID 9  # Pink-red
    mol selection "all"
    mol material Glass2
    mol addrep $molid
    mol modmaterial 5 $molid {Opacity 0.35}
    
    # Diffuse electron cloud
    mol representation QuickSurf 6.0 3.0 1.0 3.0
    mol color ColorID 22  # Light blue
    mol selection "all"
    mol material Transparent
    mol addrep $molid
    mol modmaterial 6 $molid {Opacity 0.12}
    
    display rendermode GLSL
    display projection orthographic
    display ambientocclusion off
    
    puts "ENHANCED ORBITALS style applied!"
}

puts ""
puts "NEW STYLES ADDED:"
puts "6. style_orbital_context    - Molecular orbitals with background context"
puts "6B. style_enhanced_orbitals  - Alternative orbital visualization"
puts "======================================"

# Uncomment one of these to apply automatically:
# style_neon_glow
# style_glass_crystal  
# style_holographic
# style_rainbow_energy
# style_metallic_sculpture
# style_orbital_context
# style_enhanced_orbitals