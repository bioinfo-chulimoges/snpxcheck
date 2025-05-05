# ruff: noqa: PLR2004

import numpy as np
import pandas as pd
import pytest

from src.data.processing import DataProcessor
from src.utils.config import COLUMNS_TO_DROP, REQUIRED_COLUMNS


@pytest.fixture
def sample_data():
    """Create a sample DataFrame with all required columns."""
    data = {
        "Sample File": ["file1.txt", "file2.txt"],
        "Sample Name": ["sample1", "sample2"],
        "Panel": ["panel1", "panel2"],
        "Marker": ["marker1", "marker2"],
        "Dye": ["dye1", "dye2"],
    }
    # Add allele columns with realistic values
    for i in range(1, 35):
        if i % 2 == 1:  # First allele of the pair
            data[f"Allele {i}"] = [f"0{i//2 + 1}_C", f"0{i//2 + 1}_T"]
        else:  # Second allele of the pair
            data[f"Allele {i}"] = [f"0{i//2}_T", f"0{i//2}_C"]
    return pd.DataFrame(data)


@pytest.fixture
def sample_data_with_empty_alleles():
    """Create a sample DataFrame with some empty alleles."""
    data = {
        "Sample File": ["file1.txt", "file2.txt"],
        "Sample Name": ["sample1", "sample2"],
        "Panel": ["panel1", "panel2"],
        "Marker": ["marker1", "marker2"],
        "Dye": ["dye1", "dye2"],
    }
    # Add allele columns with some empty values
    for i in range(1, 35):
        if i % 2 == 1:  # First allele of the pair
            if i == 5:  # Special case for empty allele
                data[f"Allele {i}"] = ["", "05_T"]
            else:
                data[f"Allele {i}"] = [f"0{i//2 + 1}_C", f"0{i//2 + 1}_T"]
        elif i == 6:  # Special case for empty allele
            data[f"Allele {i}"] = ["03_T", ""]
        else:
            data[f"Allele {i}"] = [f"0{i//2}_T", f"0{i//2}_C"]
    return pd.DataFrame(data)


@pytest.fixture
def processor(sample_data):
    """Create a DataProcessor instance with sample data."""
    return DataProcessor(sample_data)


def test_validate_file_format_complete(processor, sample_data):
    """Test validate_file_format with a complete DataFrame."""
    processor.df = sample_data
    missing_columns = processor.validate_file_format()
    assert len(missing_columns) == 0


def test_validate_file_format_missing_columns(processor, sample_data):
    """Test validate_file_format with missing columns."""
    # Remove some required columns
    sample_data = sample_data.drop(columns=["Sample File", "Panel"])
    processor.df = sample_data
    missing_columns = processor.validate_file_format()
    assert len(missing_columns) == 2
    assert "Sample File" in missing_columns
    assert "Panel" in missing_columns


def test_load_genemapper_data(tmp_path):
    """Test loading data from a Genemapper file."""
    # Create a temporary file with sample data
    test_file = tmp_path / "test_genemapper.txt"

    # Write header and data to the file
    with open(test_file, "w") as f:
        # Write header
        f.write("\t".join(REQUIRED_COLUMNS) + "\n")
        # Write data with realistic allele values
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
                    "sample2",
                    "panel2",
                    "marker2",
                    "dye2",
                    *allele_values,
                ]
            )
            + "\n"
        )

    processor = DataProcessor(pd.DataFrame())
    df = processor.load_genemapper_data(str(test_file))

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert all(col in df.columns for col in REQUIRED_COLUMNS)
    # Check that allele values are correctly loaded
    assert df.loc[0, "Allele 1"] == "01_C"
    assert df.loc[0, "Allele 2"] == "01_T"
    assert df.loc[1, "Allele 1"] == "01_T"
    assert df.loc[1, "Allele 2"] == "01_C"


def test_load_genemapper_data_with_empty_alleles(tmp_path):
    """Test loading data from a Genemapper file with empty alleles."""
    test_file = tmp_path / "test_genemapper_empty.txt"

    with open(test_file, "w") as f:
        f.write("\t".join(REQUIRED_COLUMNS) + "\n")
        allele_values = []
        for i in range(1, 35):
            if i == 5:  # Empty allele
                allele_values.append("")
            elif i == 6:  # Empty allele
                allele_values.append("03_T")
            elif i % 2 == 1:  # First allele of the pair
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

    processor = DataProcessor(pd.DataFrame())
    df = processor.load_genemapper_data(str(test_file))

    assert np.isnan(df.loc[0, "Allele 5"])
    assert df.loc[0, "Allele 6"] == "03_T"


def test_load_genemapper_data_invalid_file():
    """Test loading data from an invalid file."""
    processor = DataProcessor(pd.DataFrame())
    with pytest.raises(ValueError) as exc_info:
        processor.load_genemapper_data("nonexistent_file.txt")
    assert "Erreur lors de la lecture du fichier" in str(exc_info.value)


def test_load_genemapper_data_empty_file(tmp_path):
    """Test loading data from an empty file."""
    # Create an empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("")

    processor = DataProcessor(pd.DataFrame())
    with pytest.raises(ValueError) as exc_info:
        processor.load_genemapper_data(str(empty_file))
    assert "Erreur lors de la lecture du fichier" in str(exc_info.value)


def test_prepare_data(processor):
    """Test the prepare_data method."""
    prepared_df = processor.prepare_data()
    assert isinstance(prepared_df, pd.DataFrame)
    # Check that columns to drop are removed
    for col in COLUMNS_TO_DROP:
        assert col not in prepared_df.columns
    # Check that other columns are preserved
    assert "Sample Name" in prepared_df.columns
    for i in range(1, 35):
        if f"Allele {i}" not in COLUMNS_TO_DROP:
            assert f"Allele {i}" in prepared_df.columns


def test_merge_genotypes(processor):
    """Test the merge_genotypes method with normal alleles."""
    # First prepare the data
    prepared_df = processor.prepare_data()
    # Then merge genotypes
    merged_df = processor.merge_genotypes(prepared_df)

    assert isinstance(merged_df, pd.DataFrame)
    # Check that allele columns are replaced with locus columns
    allele_cols = [col for col in prepared_df.columns if col.startswith("Allele")]
    locus_cols = [col for col in merged_df.columns if col.startswith("Locus")]
    assert len(locus_cols) > 0
    assert len(locus_cols) == len(allele_cols) // 2  # Two alleles per locus

    # Check specific genotype merging
    assert merged_df.loc[0, "Locus 1"] == "C/T"  # From Allele 1=01_C and Allele 2=01_T
    assert merged_df.loc[1, "Locus 1"] == "T/C"  # From Allele 1=01_T and Allele 2=01_C


def test_merge_genotypes_with_empty_alleles(sample_data_with_empty_alleles):
    """Test the merge_genotypes method with empty alleles."""
    processor = DataProcessor(sample_data_with_empty_alleles)
    prepared_df = processor.prepare_data()
    merged_df = processor.merge_genotypes(prepared_df)

    # Check handling of empty alleles
    assert merged_df.loc[0, "Locus 3"] == "T"  # From Allele 5="" and Allele 6=03_T
    assert merged_df.loc[1, "Locus 3"] == "T"  # From Allele 5=05_T and Allele 6=""


def test_prepare_data_drop_columns(processor, sample_data):
    """Test that prepare_data correctly drops specified columns."""
    processor.df = sample_data
    result = processor.prepare_data()

    # Check that columns to drop are removed
    assert "Sample File" not in result.columns
    assert "Panel" not in result.columns
    assert "Marker" not in result.columns
    assert "Dye" not in result.columns

    # Check that other columns are preserved
    assert "Sample Name" in result.columns
    assert "Allele 1" in result.columns
    assert "Allele 2" in result.columns


def test_merge_genotypes_empty_alleles(processor):
    """Test merge_genotypes with empty allele values."""
    df = pd.DataFrame(
        {
            "Patient": ["P1", "P2"],
            "Sample Name": ["S1", "S2"],
            "Allele 1": ["", "A"],
            "Allele 2": ["", "T"],
        }
    )

    result = processor.merge_genotypes(df)
    assert result["Locus 1"].iloc[0] == ""
    assert result["Locus 1"].iloc[1] == "A/T"


def test_merge_genotypes_invalid_alleles(processor):
    """Test merge_genotypes with invalid allele values."""
    df = pd.DataFrame(
        {
            "Patient": ["P1", "P2"],
            "Sample Name": ["S1", "S2"],
            "Allele 1": ["invalid", "A"],
            "Allele 2": ["value", "T"],
        }
    )

    result = processor.merge_genotypes(df)
    assert result["Locus 1"].iloc[0] == "invalid/value"
    assert result["Locus 1"].iloc[1] == "A/T"
