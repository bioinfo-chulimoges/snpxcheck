ALLELE_PREFIX = "Allele"
GENDER_ALLELES_X = "Allele 29"
GENDER_ALLELES_Y = "Allele 30"
NEGATIVE_KEYWORDS = ["neg", "tem"]

REQUIRED_COLUMNS = ["Sample File", "Sample Name", "Panel", "Marker", "Dye"] + [
    f"Allele {i}" for i in range(1, 34 + 1)
]

COLUMNS_TO_DROP = [
    "Sample File",
    "Panel",
    "Marker",
    "Dye",
    "Allele 31",
    "Allele 32",
    "Unnamed: 39",
]
