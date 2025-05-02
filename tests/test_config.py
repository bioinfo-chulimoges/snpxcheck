from src.utils.config import (
    ALLELE_PREFIX,
    COLUMNS_TO_DROP,
    GENDER_ALLELES_X,
    GENDER_ALLELES_Y,
    NEGATIVE_KEYWORDS,
    REQUIRED_COLUMNS,
)


def test_allele_prefix():
    """Test that the allele prefix is correct."""
    assert ALLELE_PREFIX == "Allele"


def test_gender_alleles():
    """Test that the gender allele columns are correct."""
    assert GENDER_ALLELES_X == "Allele 29"
    assert GENDER_ALLELES_Y == "Allele 30"


def test_negative_keywords():
    """Test that the negative control keywords are correct."""
    assert NEGATIVE_KEYWORDS == ["neg", "tem"]


def test_required_columns():
    """Test that the required columns are correctly defined."""
    # Check basic columns
    assert "Sample File" in REQUIRED_COLUMNS
    assert "Sample Name" in REQUIRED_COLUMNS
    assert "Panel" in REQUIRED_COLUMNS
    assert "Marker" in REQUIRED_COLUMNS
    assert "Dye" in REQUIRED_COLUMNS

    # Check allele columns
    for i in range(1, 35):
        assert f"Allele {i}" in REQUIRED_COLUMNS

    # Check total number of columns
    assert (
        len(REQUIRED_COLUMNS) == 5 + 34
    )  # 5 basic columns + 34 allele columns


def test_columns_to_drop():
    """Test that the columns to drop are correctly defined."""
    # Check basic columns
    assert "Sample File" in COLUMNS_TO_DROP
    assert "Panel" in COLUMNS_TO_DROP
    assert "Marker" in COLUMNS_TO_DROP
    assert "Dye" in COLUMNS_TO_DROP

    # Check specific allele columns
    assert "Allele 31" in COLUMNS_TO_DROP
    assert "Allele 32" in COLUMNS_TO_DROP

    # Check unnamed column
    assert "Unnamed: 39" in COLUMNS_TO_DROP

    # Check total number of columns
    assert len(COLUMNS_TO_DROP) == 7  # noqa: PLR2004
