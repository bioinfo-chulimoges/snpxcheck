# ruff: noqa: PLR2004

import pandas as pd
import pytest

from src.services.identity_vigilance import IdentityVigilanceService


@pytest.fixture
def sample_genemapper_data():
    """Create sample Genemapper data with all required columns."""
    # Base data with required non-allele columns
    data = {
        "Sample File": ["file1.txt", "file2.txt", "file3.txt", "file4.txt"],
        "Sample Name": ["S1", "S2", "S3", "S4"],
        "Panel": ["Panel1", "Panel1", "Panel2", "Panel2"],
        "Marker": ["M1", "M2", "M1", "M2"],
        "Dye": ["D1", "D2", "D1", "D2"],
    }

    # Add all allele columns (1-34)
    for i in range(1, 35):
        col_name = f"Allele {i}"
        if i == 29:  # Gender allele X
            data[col_name] = ["X", "X", "X", "X"]
        elif i == 30:  # Gender allele Y
            data[col_name] = ["Y", "", "Y", ""]
        else:  # Regular alleles
            data[col_name] = ["A", "A", "G", "G"]

    return pd.DataFrame(data)


@pytest.fixture
def service():
    """Create an IdentityVigilanceService instance."""
    return IdentityVigilanceService()


def test_load_and_validate_file_valid(service, sample_genemapper_data, tmp_path):
    """Test loading and validating a valid Genemapper file."""
    # Create a temporary file with valid data
    file_path = tmp_path / "test.txt"
    sample_genemapper_data.to_csv(file_path, sep="\t", index=False)

    df, error = service.load_and_validate_file(str(file_path))

    assert error is None
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert all(col in df.columns for col in sample_genemapper_data.columns)


def test_load_and_validate_file_invalid(service, tmp_path):
    """Test loading and validating an invalid file."""
    # Create a temporary file with invalid data
    file_path = tmp_path / "test.txt"
    with open(file_path, "w") as f:
        f.write("invalid,data\n1,2")

    df, error = service.load_and_validate_file(str(file_path))

    assert df is None
    assert error is not None
    assert "Le fichier ne semble pas au bon format" in error


def test_load_and_validate_file_missing_columns(
    service, sample_genemapper_data, tmp_path
):
    """Test loading and validating a file with missing columns."""
    # Create a temporary file with missing columns
    file_path = tmp_path / "test.txt"
    sample_genemapper_data.drop(columns=["Sample File", "Panel"]).to_csv(
        file_path, sep="\t", index=False
    )

    df, error = service.load_and_validate_file(str(file_path))

    assert df is None
    assert error is not None
    assert "Colonnes manquantes" in error
    assert "Sample File" in error
    assert "Panel" in error


def test_prepare_data(service, sample_genemapper_data):
    """Test data preparation."""
    # First load and validate the data
    service.data_processor = service.data_processor.__class__(sample_genemapper_data)

    prepared_data = service.prepare_data(sample_genemapper_data)

    assert isinstance(prepared_data, pd.DataFrame)
    assert "signature" in prepared_data.columns
    assert "signature_hash" in prepared_data.columns
    assert "signature_len" in prepared_data.columns
    assert "Genre" in prepared_data.columns
    assert "Patient" in prepared_data.columns
    assert "is_neg" in prepared_data.columns
    assert "status_type" in prepared_data.columns
    assert "status_description" in prepared_data.columns


def test_perform_intra_comparison(service, sample_genemapper_data):
    """Test intra-patient comparison."""
    # First prepare the data
    service.data_processor = service.data_processor.__class__(sample_genemapper_data)
    prepared_data = service.prepare_data(sample_genemapper_data)

    df_intra, error_count, neg_control_is_clean = service.perform_intra_comparison(
        prepared_data
    )

    assert isinstance(df_intra, pd.DataFrame)
    assert isinstance(error_count, int)
    assert isinstance(neg_control_is_clean, bool)
    assert "status_type" in df_intra.columns
    assert "status_description" in df_intra.columns


def test_perform_intra_comparison_clean_neg_control(service):
    """Test intra-patient comparison with a clean negative control."""
    data = {
        "Sample Name": ["S1", "S1_dup", "neg"],
        "Patient": ["P1", "P1", "neg"],
        "signature": ["sig1", "sig1", ""],
        "signature_len": [10, 10, 0],
        "is_neg": [False, False, True],
        "Genre": ["M", "M", ""],
        "status_type": ["success", "success", "success"],
        "status_description": ["", "", ""],
    }
    df = pd.DataFrame(data)
    service.data_processor.df = df  # Mock the data processor's dataframe
    _, _, neg_control_is_clean = service.perform_intra_comparison(df)
    assert neg_control_is_clean is True


def test_perform_intra_comparison_contaminated_neg_control(service):
    """Test intra-patient comparison with a contaminated negative control."""
    data = {
        "Sample Name": ["S1", "S1_dup", "neg"],
        "Patient": ["P1", "P1", "neg"],
        "signature": ["sig1", "sig1", "contam"],
        "signature_len": [10, 10, 2],
        "is_neg": [False, False, True],
        "Genre": ["M", "M", ""],
        "status_type": ["success", "success", "success"],
        "status_description": ["", "", ""],
    }
    df = pd.DataFrame(data)
    service.data_processor.df = df  # Mock the data processor's dataframe
    _, _, neg_control_is_clean = service.perform_intra_comparison(df)
    assert neg_control_is_clean is False


def test_perform_inter_comparison(service, sample_genemapper_data):
    """Test inter-patient comparison."""
    # First prepare the data
    service.data_processor = service.data_processor.__class__(sample_genemapper_data)
    prepared_data = service.prepare_data(sample_genemapper_data)

    df_inter, error_count = service.perform_inter_comparison(prepared_data)

    assert isinstance(df_inter, pd.DataFrame)
    assert isinstance(error_count, int)


def test_generate_heatmap(service, sample_genemapper_data):
    """Test heatmap generation."""
    # First prepare the data
    service.data_processor = service.data_processor.__class__(sample_genemapper_data)
    prepared_data = service.prepare_data(sample_genemapper_data)

    heatmap = service.generate_heatmap(prepared_data)

    assert heatmap is not None
    assert hasattr(heatmap, "data")
    assert len(heatmap.data) > 0
