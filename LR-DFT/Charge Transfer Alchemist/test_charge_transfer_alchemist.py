
import pytest
from unittest import mock
from charge_transfer_alchemist import load_configuration, load_coordinates, write_input_files

@pytest.fixture
def mocker():
    return mock.Mock()

# Mocking the load_configuration function
@pytest.fixture
def mock_load_config(mocker):
    mocker.patch('charge_transfer_alchemist.load_configuration', return_value=mock_config)
    return mock_config

# Mocking the load_coordinates function
@pytest.fixture
def mock_load_coords(mocker):
    mocker.patch('charge_transfer_alchemist.load_coordinates', return_value=mock_coordinates)
    return mock_coordinates

@pytest.fixture
def mock_write_files(mocker):
    mocker.patch('charge_transfer_alchemist.write_input_files', side_effect=mock_write_input_files)

def test_load_configuration(mock_load_config):
    config = load_configuration()
    assert config["gs_filename"] == "mock_gs"
    assert config["ex_filename"] == "mock_ex"
    assert "{omega}" in config["gs_content"]

def test_load_coordinates(mock_load_coords):
    coordinates = load_coordinates()
    assert "C 0.0 0.0 0.0" in coordinates
    assert "H 1.0 1.0 1.0" in coordinates

def test_write_input_files(mock_load_config, mock_load_coords, mock_write_files):
    omega_values = ["0100000000", "0200000000"]
    generated_files = write_input_files(omega_values, mock_load_config, mock_load_coords)
    assert len(generated_files) == 2
    for omega in omega_values:
        file_content = generated_files[f"mock_gs_w{omega}.com"]
        assert str(omega) in file_content
        assert "C 0.0 0.0 0.0" in file_content

mock_coordinates = "C 0.0 0.0 0.0\nH 1.0 1.0 1.0"

# Mocking the write_input_files function for testing
mock_write_input_files = mocker.patch.object(charge_transfer_alchemist, 'write_input_files', side_effect=mock_write_input_files)

# Mock data for testing
mock_config = {
    "gs_filename": "mock_gs",
    "ex_filename": "mock_ex",
    "gs_content": "mock content with {omega} and {coordinates}",
    "ex_content": "%oldchk={gs_filename}_w{omega}.chk\n %chk={filename}_w{omega}.chk\n #P tda=(root=1) opt=calcfc freq=(savenm,hpmodes) LC-wHPBE/ChkBasis Iop(3/107={omega}, 3/108={omega})\nSCRF=Check nosymm Geom=AllCheck Guess=Read\n\nExcited State Opt_Freq in dmso\n\n",
    "vee_filename": "nr_vee",
    "vde_filename": "nr_vde",
    "vee_content": "%oldchk={gs_filename}_w{omega}.chk\n%chk={filename}_w{omega}.chk\n#P tda=(root=1) LC-wHPBE/ChkBasis Iop(3/107={omega}, 3/108={omega})\nSCRF=Check nosymm Geom=AllCheck Guess=Read\n\nVEE in dmso\n\n",
    "vde_content": "%oldchk={ex_filename}_w{omega}.chk\n%chk={filename}_w{omega}.chk\n#P tda=(root=1) LC-wHPBE/ChkBasis Iop(3/107={omega}, 3/108={omega})\nSCRF=Check nosymm Geom=AllCheck Guess=Read\n\nVDE in dmso\n\n",
    "abs_vibronic_filename": "nr_vib_abs",
    "ems_vibronic_filename": "nr_vib_ems",
    "abs_vib_content": "%chk={gs_filename}_w{omega}.chk\n#Geom=Check freq=(readfc,FC,readFCHT) nosymm\n\nVibronic Absorption calculation\n\n0 1\n\nTimeDependent\nTemperature=Value=300\nTransition=Absorption\nPrint=(Spectra=All,Matrix=JK)\n\n{ex_filename}_w{omega}.chk\n",
    "ems_vib_content": "%chk={gs_filename}_w{omega}.chk\n#Geom=Check freq=(readfc,FC,readFCHT) nosymm\n\nVibronic Emission calculation\n\n0 1\n\nTimeDependent\nTemperature=Value=300\nTransition=Emission\nPrint=(Spectra=All,Matrix=JK)\n\n{ex_filename}_w{omega}.chk\n"
}
