import os.path # necessary for reading in previously genereated files

import time # to be used for calculating computation times
import math # Math Library
import argparse # to be used for allowing user to specify input file
import numpy as np # mathematical, linear algebra lbirary
from scipy import misc, special # Scipy Binomial and Factorial SubRoutines
from scipy import linalg # Linear Algebra SubRoutine


## set print options of Numpy output for readability
np.set_printoptions(threshold=np.inf)
np.set_printoptions(precision=6)
np.set_printoptions(linewidth=200)
np.set_printoptions(suppress=True)

start = time.time()


# Basis-Set Routine
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
  
# Overlap Integral Routine
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
  
# Kinetic Energy Integral
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
  
# Potential Energy Integral
def buildV(basis, V, R, Z, atoms):
  """
  Calculate the product of the x, y, and z components of the nuclear-attraction 
  integral over the Gaussian primitives.
  (part of Handout 4, Eq. 13)
  """  
  for A, bA in enumerate(basis):
    for B, bB in enumerate(basis):
      for C, rC in enumerate(R):

        for a, dA in zip(bA['a'],bA['d']):
          for b, dB in zip(bB['a'],bB['d']):

            RA, RB, RC = bA['R'], bB['R'], rC

            lA, mA, nA = bA['l'], bA['m'], bA['n']
            lB, mB, nB = bB['l'], bB['m'], bB['n']

            V[C,A,B] += dA*dB*Vxyz(lA,mA,nA,lB,mB,nB,a,b,RA,RB,RC,Z[atoms[C]])

  return V

def Vxyz(lA,mA,nA,lB,mB,nB,a,b,RA,RB,RC,Z):
  """
  Calculate the product of the x, y, and z components of the nuclear-attraction 
  integral over the Gaussian primitives.
  (the "integral" part of Handout 4, Eq. 13)
  """
  g = a + b

  RP = gaussianProduct(a,RA,b,RB,g)

  ABsq = IJsq(RA,RB)
  PCsq = IJsq(RP,RC)
  Vxyz = 0.0
  for l in range(0,lA+lB+1):
    for r in range(0,int(l/2)+1):
      for i in range(0,int((l-2*r)/2)+1):
        vx = vi(l,r,i, lA,lB,RA[0],RB[0],RC[0],RP[0],g)

        for m in range(0,mA+mB+1):
          for s in range(0,int(m/2)+1):
            for j in range(0,int((m-2*s)/2)+1):
              vy = vi(m,s,j, mA,mB,RA[1],RB[1],RC[1],RP[1],g)

              for n in range(0,nA+nB+1):
                for t in range(0,int(n/2)+1):
                  for k in range(0,int((n-2*t)/2)+1):
                    vz = vi(n,t,k, nA,nB,RA[2],RB[2],RC[2],RP[2],g)

                    nu  = l+m+n-2*(r+s+t)-(i+j+k)
                    F   = BoysFunction(nu, g*abs(PCsq))

                    Vxyz  += vx * vy * vz * F

  Na = N(a,lA,mA,nA) # calculate the normalization constant for orbital A
  Nb = N(b,lB,mB,nB) # calculate the normalization constant for orbital B

  Vxyz *= 2*math.pi/g
  Vxyz *= math.exp(-a*b*abs(ABsq)/g)
  Vxyz *= Na * Nb 
  Vxyz *= -Z
  return Vxyz

def vi(l,r,i, lA,lB,Ai,Bi,Ci,Pi,g):
  """
  Calculate the $i-th$ component of the nuclear-attraction integral over
  Gaussian primitives.
  (Handout 4, Eq. 14)
  """

  eps = 1/(4*g) # (Handout 4, Eq. 15)
  
  vi  = (-1)**l
  vi *= ck(l,lA,lB,Pi-Ai,Pi-Bi)
  vi *= (-1)**i * special.factorial(l,exact=True)
  vi *= (Pi-Ci)**(l-2*r-2*i) * eps**(r+i)
  vi /= special.factorial(r,exact=True)
  vi /= special.factorial(i,exact=True)
  vi /= special.factorial(l-2*r-2*i,exact=True)

  return vi
 
def BoysFunction(nu, x):
  """
  The analytical function coded herein was suggested by CCL forum; similar to
  result when evaluating the Boys Function integral in Mathematica. 
  Depends on gamma functions, which are easily computed with SciPy's 
  library of special functions.
  """
  if x < 1e-7:
    return (2*nu+1)**(-1) - x*(2*nu+3)**(-1) # (Handout 4, Eq. 17)
  else:
    return (1/2) * x**(-(nu+0.5)) * special.gamma(nu+0.5) * special.gammainc(nu+0.5,x) # (Handout 4, Eq. 16)
    
# Two Electron Integral
def buildG(basis, G, K):
  """
  Calling the intermediate function Gxyz to calculate integrals over primitives,
  compute all elements of the G = (AB|CD) 4-dimensional matrix.
  (part of Handout 4, Eq. 18)
  """
  Ntei = 0 # create a two-electron integral counter, as TEIs can take a long time
  for A, bA in enumerate(basis): # retrieve atomic orbital A from basis
    for B, bB in enumerate(basis):
      for C, bC in enumerate(basis):
        for D, bD in enumerate(basis):
  
          Ntei +=1
          if Ntei % 250 == 0:
            print ('Computed '+ str(Ntei) + ' of ' + str(K**4) + ' integrals.')
  
          for a, dA in zip(bA['a'],bA['d']): # retrieve alpha and contract coefficients for atomic orbital A
            for b, dB in zip(bB['a'],bB['d']):
              for c, dC in zip(bC['a'],bC['d']):
                for d, dD in zip(bD['a'],bD['d']):
   
                  RA, RB, RC, RD = bA['R'], bB['R'], bC['R'], bD['R'] # hold coordinates of AOs A, B, C, and D
  
                  ## variables for angular momenta, in terms of x,y,z, for each orbital
                  lA, mA, nA = bA['l'], bA['m'], bA['n']
                  lB, mB, nB = bB['l'], bB['m'], bB['n']
                  lC, mC, nC = bC['l'], bC['m'], bC['n']
                  lD, mD, nD = bD['l'], bD['m'], bD['n']
  
                  tei  = dA * dB * dC * dD # multiply together the contraction coefficients
                  tei *= Gxyz(lA,mA,nA,lB,mB,nB,lC,mC,nC,lD,mD,nD,a,b,c,d,RA,RB,RC,RD) # multiply by integral over primitives
   
                  G[A,B,C,D] += tei

  return G

def Gxyz(lA,mA,nA,lB,mB,nB,lC,mC,nC,lD,mD,nD,a,b,c,d,RA,RB,RC,RD):
  """
  Calling intermediate function gi to calculate individual x,y,z components,
  calculate integrals over primitives.
  (bracketed part of Handout 4, Eq. 18)
  """
  gP = a + b
  gQ = c + d

  delta = 1/(4*gP) + 1/(4*gQ)

  RP = gaussianProduct(a,RA,b,RB,gP)
  RQ = gaussianProduct(c,RC,d,RD,gQ)

  ABsq = IJsq(RA,RB)
  CDsq = IJsq(RC,RD)
  PQsq = IJsq(RP,RQ)

  Gxyz = 0
  for l in range(0,lA+lB+1):
    for r in range(0,int(l/2)+1):
      for lp in range(0,lC+lD+1):
        for rp in range(0,int(lp/2)+1):
          for i in range(0,int((l+lp-2*r-2*rp)/2)+1):
            gx = gi(l,lp,r,rp,i, lA,lB,RA[0],RB[0],RP[0],gP, lC,lD,RC[0],RD[0],RQ[0],gQ )

            for m in range(0,mA+mB+1):
              for s in range(0,int(m/2)+1):
                for mp in range(0,mC+mD+1):
                  for sp in range(0,int(mp/2)+1):
                    for j in range(0,int((m+mp-2*s-2*sp)/2)+1):
                      gy = gi(m,mp,s,sp,j, mA,mB,RA[1],RB[1],RP[1],gP, mC,mD,RC[1],RD[1],RQ[1],gQ)

                      for n in range(0,nA+nB+1):
                        for t in range(0,int(n/2)+1):
                          for np in range(0,nC+nD+1):
                            for tp in range(0,int(np/2)+1):
                              for k in range(0,int((n+np-2*t-2*tp)/2)+1):
                                gz = gi(n,np,t,tp,k, nA,nB,RA[2],RB[2],RP[2],gP, nC,nD,RC[2],RD[2],RQ[2],gQ)

                                nu    = l+lp+m+mp+n+np-2*(r+rp+s+sp+t+tp)-(i+j+k)
                                F     = BoysFunction(nu, PQsq/(4*delta))
                                Gxyz += gx * gy * gz * F

  Gxyz *= ( 2 * math.pi**2 ) / ( gP * gQ ) 
  Gxyz *= math.sqrt( math.pi / ( gP + gQ ) )
  Gxyz *= math.exp( -(a*b*ABsq)/gP ) 
  Gxyz *= math.exp( -(c*d*CDsq)/gQ )

  Na = N(a,lA,mA,nA)
  Nb = N(b,lB,mB,nB)
  Nc = N(c,lC,mC,nC)
  Nd = N(d,lD,mD,nD)

  Gxyz *= Na * Nb * Nc * Nd

  return Gxyz

def gi(l,lp,r,rp,i, lA,lB,Ai,Bi,Pi,gP, lC,lD,Ci,Di,Qi,gQ):
  """
  Calculate the i-th coordinate component of the integral over primitives.
  (Handout 4, Eq. 22)
  """
  delta = 1/(4*gP) + 1/(4*gQ)

  gi  = (-1)**l 
  gi *= theta(l,lA,lB,Pi-Ai,Pi-Bi,r,gP) * theta(lp,lC,lD,Qi-Ci,Qi-Di,rp,gQ)
  gi *= (-1)**i * (2*delta)**(2*(r+rp))
  gi *= special.factorial(l+lp-2*r-2*rp,exact=True) * delta**i
  gi *= (Pi-Qi)**(l+lp-2*(r+rp+i))
  gi /= (4*delta)**(l+lp) * special.factorial(i,exact=True)
  gi /= special.factorial(l+lp-2*(r+rp+i),exact=True)

  return gi

def theta(l,lA,lB,PA,PB,r,g):
  """
  Calculate the theta factor of the gi term.
  (Handout 4, Eq. 23)
  """
  theta  = ck(l,lA,lB,PA,PB) 
  theta *= special.factorial(l,exact=True) * g**(r-l) 
  theta /= special.factorial(r,exact=True) * special.factorial(l-2*r,exact=True) 

  return theta
  
# Nuclear Repulsion Integral
def nuclearRepulsion(atoms):
  """
  Calculate the nuclear-nuclear repulsion energy.
  (Handout 5, Eq. 9)
  """
  Vnn = 0.0
  for a, A in enumerate(atoms):
    for b, B in enumerate(atoms):
      if b > a:
        num  = Z[A] * Z[B]
        den  = math.sqrt( IJsq(R[a],R[b]) )
        Vnn += num / den
  return Vnn
  
# Hartree-Fock-Roothan-Hall
scf_max_iter = 20 # maximum number of SCF iterations

print("")

## pass in the number of electrons N, the nuclear repulsion energy Vnn, ...
## ... the molecular integrals S, T, V, and G, and the number of AOs K
def compute_HFenergy(N, Vnn, S, T, V, G, K):
  """
  Calculate the electronic energy using the Hartree-Fock procedure,
  and then append to it the nuclear-nuclear repulsion energy.
  (Handout 5)
  """
  Hcore = T + V # (Eq. 1)
  D     = np.zeros((K,K)) # create an empty KxK density matrix;
  P     = np.zeros((K,K)) # create the KxK two-electron contribution

  X     = linalg.sqrtm(linalg.inv(S)) # generate transformation matrix (Eq. 2)

  count = 1 # instantiate iteration counter
  convergence = 1e-5 # set the HF energy convergence threshold

  ## begin the SCF iteration
  Eel = 0.0 # initial energy is 0.0
  for iteration in range(scf_max_iter+1):
    E_old = Eel # set E_old to energy from previous cycle, for comparison
  
    ## using the indices m and n in lieu of "mu" and "nu" ...
    ## ... calculate the two-electron contribution ...
    ## ... by contracting the density matrix with the two-electron integrals
    ## (Eq. 3)
    for m in range(K):
      for n in range(K):
        P[m,n] = 0.0
        for l in range(K):
          for s in range(K):
            P[m,n] += D[l,s] * (G[m,n,s,l] - 0.5 * G[m,l,s,n])
  
    F = Hcore + P             # Fock matrix = 1e + 2e contribution (Eq. 4)
    Fp = X @ F @ X            # transform Fock matrix to orthonormal basis (Eq. 5)
    e, Cp = linalg.eigh(Fp)   # diagonalize orthonomalized Fock matrix
    C = X @ Cp                # calculate the molecular orbitals (Eq. 6)
 
    ## form a new density matrix D from the molecular orbitals C 
    ## (Eq. 7)
    for m in range(K):
      for n in range(K):
        D[m,n] = 0.0
        for a in range(int(N/2)):
          D[m,n] += 2 * (C[m,a] * C[n,a])
    
    Eel = 0.0 # reset current iteration's electronic energy to 0 Hartrees

    ## calculate the electronic energy, an expectation value 
    ## (Eq. 8)
    for m in range(K):
      for n in range(K):
        Eel += 0.5 * D[n,m] * (Hcore[m,n] + F[m,n])
  
    print('Eel (iteration {:2d}): {:12.6f}'.format(count,Eel)) 
    if (np.fabs(Eel - E_old) < convergence) and (iteration > 0):
      break
    count += 1

  ## (Eq. 9, Etot = Eel + Vnn)
  print("\nEt = Eel + Enn".format(Eel, Vnn, Eel+Vnn, count))
  print("   = {:.6f} + {:.6f}".format(Eel, Vnn))
  print("   = {:.6f} Hartrees ({} iterations)\n".format(Eel+Vnn, count))
  
# Miscellaneous SubRoutine
def electronCount(atoms):
  """
  Assuming a neutrally charged molecule, calculate the number of electrons,
  based on atomic numbers of molecule's constituent atoms.
  """
  N = 0
  for A in atoms:
    N += Z[A] 
  return N

def IJsq(RI,RJ):
  """
  Compute the square of the distance between two points.
  (Handout 4, Eq 6)
  """
  return sum( (RI[i]-RJ[i])**2 for i in (0,1,2) )


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
  
# Final Task
# filename
fname = 'h2o.xyz' 
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

# save integrals as a numpy file that can be re-loaded
#Ssave = open('S.'+fname+'.npy','wb')
#np.save(Ssave,S)
#np.savetxt('out.S.'+fname+'.dat.', S)
#print('Results printed in out.S.'+fname+'.dat.')


## import or execute kinetic energy integral evaluation
T = np.zeros((K,K)) 
T = buildT(orbitalbasis, T)
print('\nKinetic energy integrals, (A|(-1/2*∇^2)|B), complete!')
print(T)

# save integrals as a numpy file that can be re-loaded
Tsave = open('T.'+fname+'.npy','wb')
#np.save(Tsave,T)
#np.savetxt('out.T.'+fname+'.dat.', T)
# print results in output file
#print('Results printed in out.T.'+fname+'.dat.')

## import or execute nuclear attraction integral evaluation
V = np.zeros((n,K,K)) 
V = buildV(orbitalbasis, V, R, Z, atoms)
Vsum = np.zeros((K,K))
for i in range(len(V)):
  Vsum += V[i]

print('\nNuclear attraction integrals, (A|(1/r_iC)|B), complete!')
print(Vsum)
# save integrals as a numpy file that can be re-loaded
#np.save(Vsave,Vsum)
#np.savetxt('out.V.'+fname+'.dat.', Vsum)

## import or execute two-electron tensor evaluation
G = np.zeros((K,K,K,K)) 
G = buildG(orbitalbasis,G,K)
print('\nElectron repulsion integrals, (AB|CD), complete!')
#print(G)

# save tensor as a numpy file that can be re-loaded
#Gsave = open('G.'+fname+'.npy','wb')
#np.save(Gsave,G)
#np.savetxt('out.G.'+fname+'.dat.', G)


# Do it
N = electronCount(atoms) # count the number of electrons present
Vnn = nuclearRepulsion(atoms) # calculate the nuclear repulsion energy

compute_HFenergy(N,Vnn,S,T,Vsum,G, K) # call on HF procedure from hf.py
                                         # ... passing in integrals and other info

# calculate and display total computation time
end = time.time()
print("Calculation time: {:.3f} min. ({:.3f} sec.)".format((end-start)/60.,(end-start)))

# You Are Done