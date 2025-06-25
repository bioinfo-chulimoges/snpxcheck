import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

from src.services.identity_vigilance import IdentityVigilanceService
from src.utils.config import REQUIRED_COLUMNS


@pytest.fixture
def sample_genemapper_file(tmp_path):
    """Create a sample Genemapper file for testing."""
    test_file = tmp_path / "test_genemapper.txt"

    # Write header and data to the file
    with open(test_file, "w") as f:
        # Write header
        f.write("\t".join(REQUIRED_COLUMNS) + "\n")

        # Write data for two samples
        # Sample 1: Normal sample
        allele_values = []
        for i in range(1, 35):
            if i % 2 == 1:  # First allele of the pair
                allele_values.append(f"0{i//2 + 1}_C")
            else:  # Second allele of the pair
                allele_values.append(f"0{i//2}_T")
        f.write(
            "\t".join(
                [
                    "file1.txt",
                    "sample1",
                    "panel1",
                    "marker1",
                    "dye1",
                    *allele_values,
                ]
            )
            + "\n"
        )

        # Sample 2: Negative control
        allele_values = []
        for i in range(1, 35):
            if i % 2 == 1:  # First allele of the pair
                allele_values.append(f"0{i//2 + 1}_T")
            else:  # Second allele of the pair
                allele_values.append(f"0{i//2}_C")
        f.write(
            "\t".join(
                [
                    "file2.txt",
                    "neg_control",
                    "panel1",
                    "marker1",
                    "dye1",
                    *allele_values,
                ]
            )
            + "\n"
        )

    return test_file


@pytest.fixture
def service():
    """Create an IdentityVigilanceService instance."""
    return IdentityVigilanceService()


def test_full_processing_flow(service, sample_genemapper_file, tmp_path):
    """Test the complete processing flow from file loading to report generation."""
    # 1. Load and validate file
    df, error = service.load_and_validate_file(sample_genemapper_file)
    assert df is not None
    assert error is None
    assert isinstance(df, pd.DataFrame)
    assert all(col in df.columns for col in REQUIRED_COLUMNS)

    # 2. Prepare data
    prepared_data = service.prepare_data(df)
    assert isinstance(prepared_data, pd.DataFrame)
    assert "signature" in prepared_data.columns
    assert "signature_hash" in prepared_data.columns
    assert "Genre" in prepared_data.columns
    assert "Patient" in prepared_data.columns
    assert "is_neg" in prepared_data.columns

    # 3. Perform intra-comparison
    df_intra, errors_intra, neg_control_is_clean = service.perform_intra_comparison(
        prepared_data
    )
    assert isinstance(df_intra, pd.DataFrame)
    assert isinstance(errors_intra, (int, np.int64))
    assert "status_type" in df_intra.columns
    assert "status_description" in df_intra.columns

    # 4. Perform inter-comparison
    df_inter, errors_inter = service.perform_inter_comparison(prepared_data)
    assert isinstance(df_inter, pd.DataFrame)
    assert isinstance(errors_inter, (int, np.int64))

    # 5. Generate heatmap
    heatmap = service.generate_heatmap(prepared_data)
    assert isinstance(heatmap, go.Figure)
    assert len(heatmap.data) == 1
    assert isinstance(heatmap.data[0], go.Heatmap)

    # 6. Generate PDF report
    output_path = tmp_path / "test_report.pdf"
    metadata = {
        "date": "2024-04-30",
        "filename": "test.txt",
        "interpreter": "John Doe",
        "week": "2024-W18",
        "serie": "Oui",
        "comment": "Test comment",
    }

    service.generate_pdf_report(
        df_intra=df_intra,
        df_inter=df_inter,
        heatmap=heatmap,
        metadata=metadata,
        errors_intra=errors_intra,
        errors_inter=errors_inter,
        output_path=str(output_path),
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_flow_with_invalid_data(service, tmp_path):
    """Test the processing flow with invalid data."""
    # Create an invalid file
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("invalid,data\n1,2")

    # 1. Load and validate file
    df, error = service.load_and_validate_file(invalid_file)
    assert df is None
    assert error is not None
    assert "Le fichier ne semble pas au bon format" in error


def test_flow_with_empty_data(service, tmp_path):
    """Test the processing flow with empty data."""
    # Create an empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    # 1. Load and validate file
    df, error = service.load_and_validate_file(empty_file)
    assert df is None
    assert error is not None
    assert "Erreur lors de la lecture du fichier" in error


def test_flow_with_duplicate_samples(service, tmp_path):
    """Test the processing flow with samples that should trigger errors."""
    test_file = tmp_path / "duplicates.txt"

    # Write header and data to the file
    with open(test_file, "w") as f:
        # Write header
        f.write("\t".join(REQUIRED_COLUMNS) + "\n")

        # Sample 1: Patient 1, first sample
        allele_values = []
        for i in range(1, 35):
            if i % 2 == 1:  # First allele of the pair
                allele_values.append(f"0{i//2 + 1}_C")
            else:  # Second allele of the pair
                allele_values.append(f"0{i//2}_T")
        f.write(
            "\t".join(
                [
                    "file1.txt",
                    "patient1",
                    "panel1",
                    "marker1",
                    "dye1",
                    *allele_values,
                ]
            )
            + "\n"
        )

        # Sample 2: Patient 1, second sample with different alleles
        # (should trigger intra error)
        allele_values = []
        for i in range(1, 35):
            if i % 2 == 1:  # First allele of the pair
                allele_values.append(f"0{i//2 + 1}_T")  # Changed from C to T
            else:  # Second allele of the pair
                allele_values.append(f"0{i//2}_C")  # Changed from T to C
        f.write(
            "\t".join(
                [
                    "file2.txt",
                    "patient1bis",
                    "panel1",
                    "marker1",
                    "dye1",
                    *allele_values,
                ]
            )
            + "\n"
        )

        # Sample 3: Patient 2 with same alleles as Patient 1's first sample
        # (should trigger inter error)
        allele_values = []
        for i in range(1, 35):
            if i % 2 == 1:  # First allele of the pair
                allele_values.append(f"0{i//2 + 1}_C")
            else:  # Second allele of the pair
                allele_values.append(f"0{i//2}_T")
        f.write(
            "\t".join(
                [
                    "file3.txt",
                    "patient3",
                    "panel1",
                    "marker1",
                    "dye1",
                    *allele_values,
                ]
            )
            + "\n"
        )

    # 1. Load and validate file
    df, error = service.load_and_validate_file(test_file)
    assert df is not None
    assert error is None

    # 2. Prepare data
    prepared_data = service.prepare_data(df)

    # 3. Perform intra-comparison
    df_intra, errors_intra, neg_control_is_clean = service.perform_intra_comparison(
        prepared_data
    )
    assert errors_intra > 0  # Should detect different signatures for same patient

    # 4. Perform inter-comparison
    df_inter, errors_inter = service.perform_inter_comparison(prepared_data)
    assert errors_inter > 0  # Should detect same signature for different patients
