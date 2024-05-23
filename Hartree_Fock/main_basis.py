import os.path # necessary for reading in previously genereated files

import time # to be used for calculating computation times
import math
import argparse # to be used for allowing user to specify input file
import numpy as np # mathematical, linear algebra lbirary


## set print options of Numpy output for readability
np.set_printoptions(threshold=np.inf)
np.set_printoptions(precision=6)
np.set_printoptions(linewidth=200)
np.set_printoptions(suppress=True)


# Basis-Set Builder Routine
## STO-3G (from EMSL Basis Set Exchange): 
##   exponent coefficient alpha 'a'
a = \
   (
    (
     (    0.16885540,    0.62391373,    3.42525091),    # H  1s
     (    0.00000000,    0.00000000,    0.0000000 )     # H  2s,2p
                                                   ),
    (
     (    0.31364979,    1.15892300,    6.36242139),    # He 1s
     (    0.00000000,    0.00000000,    0.0000000 )     # He 2s,2p
                                                   ),
    (    
     (    0.7946505,     2.9362007,    16.1195750 ),    # Li 1s
     (    0.0480887,     0.1478601,     0.6362897 )     # Li 2s,2p
                                                   ), 
    (
     (    1.4871927,     5.4951153,    30.1678710 ),    # Be 1s
     (    0.0993707,     0.3055389,     1.3148331 )     # Be 2s,2p
                                                   ),
    (
     (    2.4052670,     8.8873622,    48.7911130 ),    # B  1s
     (    0.1690618,     0.5198205,     2.2369561 )     # B  2s,2p
                                                   ),
    (
     (    3.5305122,    13.0450960,    71.6168370 ),    # C  1s
     (    0.2222899,     0.6834831,     2.9412494 )     # C  2s,2p
                                                   ),
    (
     (    4.8856602,    18.0523120,    99.1061690 ),    # N  1s
     (    0.2857144,     0.8784966,     3.7804559 )     # N  2s,2p
                                                   ),
    (
     (    6.4436083,    23.8088610,   130.7093200 ),    # O  1s
     (    0.3803890,     1.1695961,     5.0331513 )     # O  2s,2p
                                                   ),
   )

## STO-3G (from EMSL basis set exchange): 
##   contraction coefficient 'd' applies to all atoms
d = ((0.44463454, 0.53532814, 0.15432897),     # 1s
     (0.70011547, 0.39951283,-0.09996723),     # 2s
     (0.39195739, 0.60768372, 0.15591627))     # 2p

## dictionary: name --> atomic number
Z = {'H':1,'He':2,'Li':3,'Be':4,'B':5,'C':6,'N':7,'O':8,'F':9,'Ne':10,'K':19,'Ca':20,'Sc':21}

## minimal basis orbital configuration, it a dictionary
subshells = {
            'H':['1s'],
            'O':['1s','2s','2p'],
           }

def build_sto3Gbasis(atoms, R):
  """
  This function depends on the atoms array, which lists strings of atomic symbols of the atoms of the input
  molecule, in the same order as the input .xyz file.
  This function additionally depends on the molecule's coordinates R (a nested array), where each element is
  an array holding the coordinates of each atom, also in the same order as atoms.
  """

  sto3Gbasis = []
  K = 0 # indexing the orbitals ==> matrix size
  for i, atom in enumerate(atoms):
    for subshell in subshells[atom]:
      if subshell == '1s':
        sto3Gbasis.append( 
                           {
                             'Z': Z[atom],                # atom name --> atomic number
                             'o': subshell,               # append the orbital-type string ('1s','2s',etc.)
                             'R': R[ i ],                 # get list [x,y,z] of atom coordinates
                             'l': 0,                      # s orbital ==> 0 angular momentum
                             'm': 0,
                             'n': 0,
                             'a': a[ (Z[atom]-1) ][0],    # append list of 1s orbital exponential factors
                             'd': d[0]                    # append list of 1s orbital contraction coefficients
                           }
                         )
        K += 1
      if subshell == '2s':
        sto3Gbasis.append( 
                           { 
                             'Z': Z[atom],
                             'o': subshell,
                             'R': R[ i ],
                             'l': 0,
                             'm': 0,
                             'n': 0,
                             'a': a[ (Z[atom]-1) ][1],   # append list of 2s orbital exponential factors
                             'd': d[1]                   # append list of 2s orbital contraction coefficients
                           }
                         )
        K += 1
      if subshell == '2p':
        sto3Gbasis.append( 
                           { 
                             'Z': Z[atom],
                             'o': '2px',
                             'R': R[ i ],
                             'l': 1,                     # 2px orbital has angular momentum in X direction
                             'm': 0,
                             'n': 0,                     
                             'a': a[ (Z[atom]-1) ][1],   # 2p orbital exponent = 2s orbital exponent
                             'd': d[2]                   # append list of 2p orbital contraction coefficients
                           }
                         )
        K += 1
        sto3Gbasis.append( 
                           { 
                             'Z': Z[atom],
                             'o': '2py',
                             'R': R[ i ],
                             'l': 0,
                             'm': 1,                     # 2py orbital has angular momentum in Y direction
                             'n': 0,
                             'a': a[ (Z[atom]-1) ][1],
                             'd': d[2]
                           }
                         )
        K += 1
        sto3Gbasis.append( 
                           { 
                             'Z': Z[atom],
                             'o': '2pz',
                             'R': R[ i ],
                             'l': 0,                     
                             'm': 0,
                             'n': 1,                     # 2pz orbital has angular momentum in Z direction
                             'a': a[ (Z[atom]-1) ][1],
                             'd': d[2]
                           }
                         )
        K += 1

  return sto3Gbasis, K
  
  
# Building H2O Molecule
# Total Number of Atoms in H2O
n = 3
# Atomic Symbol List
atoms = ['O', 'H', 'H']

# XYZ Coordinates Nested list aka matrix
R = [[0.000000, 0.000000, 0.227000],
     [0.000000, 1.353000, -0.908000],
     [0.000000, -1.353000, -0.908000]]

orbitalbasis, K = build_sto3Gbasis(atoms, R) # K = basis size ==> dimensions of matrix

print(orbitalbasis)
with open('orbitalbasis_file.txt', 'w') as f:
    f.write(str(orbitalbasis))
    f.close()
    
orbitalbasis_file = open("orbitalbasis_file.txt")
lines = orbitalbasis_file.readlines()
for line in lines:
    print(line)
    
    
# Good Job You Just Built a minimal basis-set for H2O molecule