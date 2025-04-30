"""Configuration module for the SNPXPlex Streamlit application.

This module contains constants and configurations used in the application,
including allele prefixes, required columns, and columns to drop.
"""

# Prefix used for allele columns
ALLELE_PREFIX = "Allele"

# Columns used for gender determination
GENDER_ALLELES_X = "Allele 29"
GENDER_ALLELES_Y = "Allele 30"

# Keywords indicating a negative control
NEGATIVE_KEYWORDS = ["neg", "tem"]

# List of required columns in the input file
REQUIRED_COLUMNS = ["Sample File", "Sample Name", "Panel", "Marker", "Dye"] + [
    f"Allele {i}" for i in range(1, 34 + 1)
]

# List of columns to drop during data processing
COLUMNS_TO_DROP = [
    "Sample File",
    "Panel",
    "Marker",
    "Dye",
    "Allele 31",
    "Allele 32",
    "Unnamed: 39",
]
