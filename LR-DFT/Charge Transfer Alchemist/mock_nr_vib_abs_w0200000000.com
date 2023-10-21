%chk=mock_gs_w0200000000.chk
#Geom=Check freq=(readfc,FC,readFCHT) nosymm

Vibronic Absorption calculation

0 1

TimeDependent
Temperature=Value=300
Transition=Absorption
Print=(Spectra=All,Matrix=JK)

mock_ex_w0200000000.chk
