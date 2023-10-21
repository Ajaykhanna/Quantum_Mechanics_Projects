%chk=nr_gs_w0100000000.chk
#Geom=Check freq=(readfc,FC,readFCHT) nosymm

Vibronic Absorption calculation

0 1

TimeDependent
Temperature=Value=300
Transition=Absorption
Print=(Spectra=All,Matrix=JK)

nr_ex_w0100000000.chk
