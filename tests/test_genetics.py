import pandas as pd
import pytest

from src.data.genetics import GeneticAnalyzer
from src.utils.config import (
    GENDER_ALLELES_X,
    GENDER_ALLELES_Y,
    NEGATIVE_KEYWORDS,
)


@pytest.fixture
def sample_data():
    """Create a sample DataFrame with allele data."""
    data = {
        "Sample Name": [
            "sample1",
            "sample2",
            "sample3",
            "sample4",
            "neg_control",
        ],
        "Panel": ["panel1", "panel1", "panel1", "panel1", "panel1"],
        "Marker": ["marker1", "marker1", "marker1", "marker1", "marker1"],
        "Dye": ["dye1", "dye1", "dye1", "dye1", "dye1"],
    }
    # Add allele columns
    for i in range(1, 35):
        data[f"Allele {i}"] = [
            f"0{i//2 + 1}_C",
            f"0{i//2 + 1}_T",
            "",
            f"0{i//2 + 1}_G",
            "",
        ]

    # Set specific values for gender alleles
    data[GENDER_ALLELES_X] = ["X", "X", "", "X", "X"]
    data[GENDER_ALLELES_Y] = ["Y", "", "", "Y", ""]

    return pd.DataFrame(data)


@pytest.fixture
def analyzer(sample_data):
    """Create a GeneticAnalyzer instance with sample data."""
    return GeneticAnalyzer(sample_data)


def test_determine_sex(analyzer, sample_data):
    """Test the determine_sex method."""
    # Test male sample (X and Y present)
    assert analyzer.determine_sex(sample_data.iloc[0]) == "homme"

    # Test female sample (X present, Y empty)
    assert analyzer.determine_sex(sample_data.iloc[1]) == "femme"

    # Test invalid sample (X present, Y missing)
    assert analyzer.determine_sex(sample_data.iloc[2]) == "indéterminé"

    # Test male sample (X and Y present)
    assert analyzer.determine_sex(sample_data.iloc[3]) == "homme"

    # Test female sample (X present, Y empty)
    assert analyzer.determine_sex(sample_data.iloc[4]) == "femme"


def test_compute_signature(analyzer, sample_data):
    """Test the compute_signature method."""
    # Test with a sample that has all alleles
    signature = analyzer.compute_signature(sample_data.iloc[0])
    assert isinstance(signature, tuple)
    assert len(signature) > 0
    assert all(isinstance(allele, str) for allele in signature)

    # Test with a sample that has empty alleles
    signature = analyzer.compute_signature(sample_data.iloc[2])
    assert isinstance(signature, tuple)
    assert len(signature) < len(
        analyzer._get_allele_columns()
    )  # Should be shorter due to empty alleles


def test_determine_sex_invalid_values(analyzer):
    """Test determine_sex with invalid values."""
    # Create a row with invalid gender alleles
    row = pd.Series({GENDER_ALLELES_X: "invalid", GENDER_ALLELES_Y: "invalid"})

    # Should return "indéterminé" for invalid values
    assert analyzer.determine_sex(row) == "indéterminé"


def test_determine_sex_missing_columns(analyzer):
    """Test determine_sex with missing gender columns."""
    # Create a row without gender columns
    row = pd.Series({"Sample Name": "S1", "Allele 1": "A", "Allele 2": "T"})

    # Should return "indéterminé" when columns are missing
    assert analyzer.determine_sex(row) == "indéterminé"


def test_compute_signature_hash(analyzer, sample_data):
    """Test the compute_signature_hash method."""
    # Add signature column for testing
    sample_data["signature"] = sample_data.apply(analyzer.compute_signature, axis=1)

    # Test hash computation
    hash_value = analyzer.compute_signature_hash(sample_data.iloc[0])
    assert isinstance(hash_value, str)
    assert len(hash_value) == 40  # SHA-1 hash length  # noqa: PLR2004

    # Test that same signature gives same hash
    hash1 = analyzer.compute_signature_hash(sample_data.iloc[0])
    hash2 = analyzer.compute_signature_hash(sample_data.iloc[0])
    assert hash1 == hash2


def test_is_negative_control(analyzer):
    """Test the is_negative_control method."""
    # Test with negative control keywords
    for keyword in NEGATIVE_KEYWORDS:
        assert analyzer.is_negative_control(f"test_{keyword}_control")

    # Test with non-negative control
    assert not analyzer.is_negative_control("normal_sample")
    assert not analyzer.is_negative_control("control_positive")


def test_is_negative_control_edge_cases(analyzer):
    """Test is_negative_control with edge cases."""
    # Test with empty string
    assert not analyzer.is_negative_control("")

    # Test with None
    assert not analyzer.is_negative_control(None)

    # Test with uppercase
    assert analyzer.is_negative_control("TEST_NEG_CONTROL")

    # Test with mixed case
    assert analyzer.is_negative_control("TEST_NeG_cOntRoL")

    # Test with partial match
    assert analyzer.is_negative_control("negative")


def test_prepare_data(analyzer, sample_data):
    """Test the prepare_data method."""
    prepared_df = analyzer.prepare_data()

    # Check that all required columns are present
    assert "signature" in prepared_df.columns
    assert "signature_hash" in prepared_df.columns
    assert "signature_len" in prepared_df.columns
    assert "Genre" in prepared_df.columns
    assert "Patient" in prepared_df.columns
    assert "is_neg" in prepared_df.columns
    assert "status_type" in prepared_df.columns
    assert "status_description" in prepared_df.columns

    # Check that signatures are computed correctly
    assert all(isinstance(sig, tuple) for sig in prepared_df["signature"])

    # Check that hashes are computed correctly
    assert all(
        isinstance(hash, str) and len(hash) == 40  # noqa: PLR2004
        for hash in prepared_df["signature_hash"]
    )

    # Check that gender is determined correctly
    assert prepared_df.loc[0, "Genre"] == "homme"
    assert prepared_df.loc[1, "Genre"] == "femme"

    # Check that negative controls are identified
    assert prepared_df.loc[4, "is_neg"]
    assert all(not neg for neg in prepared_df.loc[:3, "is_neg"])
