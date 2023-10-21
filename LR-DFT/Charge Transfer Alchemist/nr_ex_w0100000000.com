%oldchk=nr_gs_w0100000000.chk
%chk=nr_ex_w0100000000.chk
#P tda=(root=1) opt=calcfc freq=(savenm,hpmodes) LC-wHPBE/ChkBasis Iop(3/107=0100000000, 3/108=0100000000)
SCRF=Check nosymm Geom=AllCheck Guess=Read

Excited State Opt_Freq in dmso

