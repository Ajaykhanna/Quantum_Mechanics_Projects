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
  
  
from scipy import misc, special

def buildS(basis, S):
  """
  Pass in an empty KxK overlap integral matrix, S.
  Calling the function (Sxyz) to calculate each Gaussian primitive overlap integral,
  compute all elements of the S = (A|B) 2-dimensional matrix.
  (Handout 4, Eq. 1)
  """
  for A, bA in enumerate(basis):    # retrieve atomic orbital A from the basis
    for B, bB in enumerate(basis):  # retrieve atomic orbital B from the basis

      for a, dA in zip(bA['a'],bA['d']):    # retrieve A.O. A alpha and contraction coefficients
        for b, dB in zip(bB['a'],bB['d']):  # retrieve A.O. B alpha and contraction coefficients

          RA, RB = bA['R'], bB['R']  # 

          lA, mA, nA = bA['l'], bA['m'], bA['n'] # instantiate angular momentum exponent variables, A.O. A
          lB, mB, nB = bB['l'], bB['m'], bB['n'] # instantiate angular momentum exponent variables, A.O. B

          # using all of the collected information on A.O.s A and B, calculate Handout 4, Eq. 1
          S[A,B] += (
                     math.exp(-a*b*IJsq(RA,RB)/(a+b)) * #
                     N(a,lA,mA,nA) * N(b,lB,mB,nB) * # normalization constant
                     dA * dB * Sxyz(RA,RB,a,b,lA,lB,mA,mB,nA,nB)
                    )

  return S

def Sxyz(RA,RB,a,b,lA,lB,mA,mB,nA,nB):
  """
  Calculate the Gaussian primitive overlap integral.
  (Handout 4, Eq. 2)
  """
  RP = gaussianProduct(a,RA,b,RB,a+b) # g = a + b

  sx = si(lA,lB,a+b,RA[0],RB[0],RP[0])
  sy = si(mA,mB,a+b,RA[1],RB[1],RP[1])
  sz = si(nA,nB,a+b,RA[2],RB[2],RP[2])

  return sx*sy*sz

def si(lA,lB,g,Ai,Bi,Pi):
  """
  Calculate the i-th component (x, y, or z) contribution to (A|B).
  (Handout 4, Eq. 3)
  """
  si = 0.0
  for j in range(0,int((lA+lB)/2)+1):
    si += ck(2*j,lA,lB,Pi-Ai,Pi-Bi) * special.factorial2(2*j-1, exact=True) / (2*g)**j
  si *= math.sqrt(math.pi/g)

  return si 
  
def ck(j,l,m,a,b):
  """
  Calculate the coefficient 'ck' factor within the theta expression,
  associated with a third center between position vectors
  of the nuclei A and B.
  (Handout 4, Eq. 8)
  """
  coefficient = 0.0
 
  for k in range(0,l+1):
    for i in range(0,m+1):
      if i + k == j:
        coefficient += special.binom(l,k) * special.binom(m,i) * a**(l-k) * b**(m-i)

  return coefficient

def N(a,l,m,n):
  """
  Calculate the normalization factors.
  (Handout 4, Eq. 9)
  """
  N  = (4*a)**(l+m+n)
  #N /= misc.factorial2(2*l-1,exact=True) * misc.factorial2(2*m-1,exact=True) * misc.factorial2(2*n-1,exact=True)
  N /= special.factorial2(2*l-1,exact=True) * special.factorial2(2*m-1,exact=True) * special.factorial2(2*n-1,exact=True)
  N *= ((2*a)/math.pi)**(1.5)
  N  = N**(0.5)

  return N

def gaussianProduct(a,RA,b,RB,g):
  """
  The product of two Gaussians is a third Gaussian.
  (Handout 4, Eq. 5)
  """
  P = []
  for i in range(3):
    P.append( (a*RA[i]+b*RB[i])/g )

  return P

def IJsq(RI,RJ):
  """
  Calculate the square of the distance between two points.
  (Handout 4, Eq. 6)
  """
  return sum( (RI[i]-RJ[i])**2 for i in (0,1,2) )
  
# Building Kinetic Energy Integrals
def buildT(basis, T):
  """
  Build the kinetic energy integral matrix. 
  Call on function Kxyz to calculate integrals over primitives.
  (part of Handout 4, Eq. 10)
  """
  for A, bA in enumerate(basis):
    for B, bB in enumerate(basis):

      for a, dA in zip(bA['a'],bA['d']):
        for b, dB in zip(bB['a'],bB['d']):

          RA, RB = bA['R'], bB['R']

          lA, mA, nA = bA['l'], bA['m'], bA['n']
          lB, mB, nB = bB['l'], bB['m'], bB['n']

          T[A,B] += (
                     math.exp(-a*b*IJsq(RA,RB)/(a+b)) * 
                     N(a,lA,mA,nA) * N(b,lB,mB,nB) * 
                     dA * dB 
                    ) * Kxyz(RA,RB,a,b,lA,lB,mA,mB,nA,nB)

  return T

def Kxyz(RA,RB,a,b,lA,lB,mA,mB,nA,nB):
  """
  Calculate the kinetic energy integral over primitives, for components x, y, z.
  (the "integral" part of Handout 4, Eq. 10)
  """
  K  = b*(2*(lB+mB+nB)+3)*Sxyz(RA,RB,a,b,lA,lB,mA,mB,nA,nB) # line 1 of Eq. 10

  K -= (2*b**2)*Sxyz(RA,RB,a,b,lA,lB+2,mA,mB,nA,nB) # line 2
  K -= (2*b**2)*Sxyz(RA,RB,a,b,lA,lB,mA,mB+2,nA,nB)
  K -= (2*b**2)*Sxyz(RA,RB,a,b,lA,lB,mA,mB,nA,nB+2)

  K -= (1/2)*(lB*(lB-1))*Sxyz(RA,RB,a,b,lA,lB-2,mA,mB,nA,nB) # line 3
  K -= (1/2)*(mB*(mB-1))*Sxyz(RA,RB,a,b,lA,lB,mA,mB-2,nA,nB)
  K -= (1/2)*(nB*(nB-1))*Sxyz(RA,RB,a,b,lA,lB,mA,mB,nA,nB-2)

  return K
  
# Total Number of Atoms in H2O
n = 3
# Atomic Symbol List
atoms = ['O', 'H', 'H']

# XYZ Coordinates Nested list aka matrix
R = [[0.000000, 0.000000, 0.227000],
     [0.000000, 1.353000, -0.908000],
     [0.000000, -1.353000, -0.908000]]

orbitalbasis, K = build_sto3Gbasis(atoms, R) # K = basis size ==> dimensions of matrix

# Execute overlap integral evaluation
S = np.zeros((K,K))
S = buildS(orbitalbasis, S)
print('Overlap integrals, (A|B), complete!')
print(S)

## import or execute kinetic energy integral evaluation
T = np.zeros((K,K)) 
T = buildT(orbitalbasis, T)
print('\nKinetic energy integrals, (A|(-1/2*∇^2)|B), complete!')
print(T)


# Congratulations, so far you have build a STO-3G basis-set, Overlap integral, and a Kinectic Energy Integral.
 