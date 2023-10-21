%oldchk=mock_ex_w0200000000.chk
%chk=nr_vde_w0200000000.chk
#P tda=(root=1) LC-wHPBE/ChkBasis Iop(3/107=0200000000, 3/108=0200000000)
SCRF=Check nosymm Geom=AllCheck Guess=Read

VDE in dmso

