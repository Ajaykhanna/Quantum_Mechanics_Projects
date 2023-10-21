%oldchk=mock_gs_w0200000000.chk
%chk=mock_nr_vee_w0200000000.chk
#P tda=(root=1) LC-wHPBE/ChkBasis Iop(3/107=0200000000, 3/108=0200000000)
SCRF=Check nosymm Geom=AllCheck Guess=Read

VEE in dmso

