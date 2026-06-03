"""Configuration module for the SNPXPlex Streamlit application.

This module contains constants and configurations used in the application, including
allele prefixes, required columns, and columns to drop.
"""

# Prefix used for allele columns
ALLELE_PREFIX = "Allele"

# Columns used for gender determination
GENDER_ALLELES_X = "Allele 29"
GENDER_ALLELES_Y = "Allele 30"

# Keywords indicating a negative control (substring match, case-insensitive)
NEGATIVE_KEYWORDS = ["neg", "tem"]

# Suffixes indicating a negative control (suffix match, case-insensitive)
NEGATIVE_SUFFIXES = ["NE"]

# Sample name nomenclatures
# GLIMS Genetics: {glims_id:9}{tube_id:2}-{sample_id}
GLIMS_SAMPLE_PATTERN = r"^(?P<glims_id>\d{9})(?P<tube_id>\d{2})-(?P<sample_id>.+)$"
# Legacy: {sample_id}{tube_suffix:bis|ter?}
LEGACY_TUBE_SUFFIX_PATTERN = r"^(.*?)(bis|ter)$"

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
