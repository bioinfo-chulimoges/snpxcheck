import pandas as pd
import numpy as np
from hashlib import sha1

ALLELE_PREFIX = "Allele"
GENDER_ALLELES_X = "Allele 29"
GENDER_ALLELES_Y = "Allele 30"
NEGATIVE_KEYWORDS = ["neg", "tem"]
REQUIRED_COLUMNS = ["Sample File", "Sample Name", "Panel", "Marker", "Dye"] + [
    f"Allele {i}" for i in range(1, 35 + 1)
]


def load_genemapper_data(file) -> pd.DataFrame:
    """
    Load the Genemapper data from a file.

    Args:
        file (str): The path to the Genemapper data file.

    Returns:
        pd.DataFrame: A DataFrame containing the Genemapper data.
    """
    # Read the file into a DataFrame
    try:
        df = pd.read_csv(file, sep="\t", engine="python")
        if df.empty:
            raise ValueError("Le fichier est vide ou mal formaté.")
        return df
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture du fichier : {e}")


def validate_file_format(df: pd.DataFrame) -> list[str]:
    """
    Check if the DataFrame has the required columns.

    Args:
        df (pd.DataFrame): The DataFrame to check.

    Returns:
        list[str]: List of missing columns. If all required columns are present, returns an empty list.
    """
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    return missing_columns


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare the data for comparisons.

    Args:
        df (pd.DataFrame): The DataFrame to prepare.

    Returns:
        pd.DataFrame: The prepared DataFrame.
    """
    # drop always empty columns
    df = df.copy().drop(
        columns=[
            "Sample File",
            "Panel",
            "Marker",
            "Dye",
            "Allele 31",
            "Allele 32",
            "Unnamed: 39",
        ],
        errors="ignore",
    )

    allele_cols = [
        col
        for col in df.columns
        if col.startswith(ALLELE_PREFIX)
        and col != GENDER_ALLELES_X
        and col != GENDER_ALLELES_Y
    ]

    # compute the signature and hash from the alleles
    df["signature"] = df.apply(lambda row: compute_signature(row, allele_cols), axis=1)
    df["signature_hash"] = df.apply(lambda row: compute_signature_hash(row), axis=1)
    df["signature_len"] = df["signature"].apply(len)

    # Determine the gender of the sample
    df["Genre"] = df.apply(determine_sex, axis=1)

    # Remove the suffix "bis" or "ter" from the sample name
    df["Patient"] = df["Sample Name"].str.replace(
        r"^(.*?)(bis|ter)$", r"\1", regex=True
    )

    # Check if the sample is a negative control
    df["is_neg"] = df["Sample Name"].apply(is_negative_control)

    # Define default values for status_type and status_description
    df["status_type"] = "success"  # Valeur par défaut
    df["status_description"] = ""  # Valeur par défaut
    return df


def determine_sex(row: pd.Series) -> str:
    """
    Determine the sex of a sample based on the X and Y alleles.

    Args:
        row (pandas Series): A row of the input dataframe.

    Returns:
        str: The sex of the sample, either "homme", "femme" or "indéterminé".
    """

    x = row.get(GENDER_ALLELES_X)
    y = row.get(GENDER_ALLELES_Y)
    if not pd.isna(x) and x == "X" and (pd.isna(y) or y == ""):
        return "femme"
    elif not pd.isna(x) and x == "X" and not pd.isna(y) and y == "Y":
        return "homme"
    else:
        return "indéterminé"


def compute_signature(row: pd.Series, allele_cols: list) -> tuple:
    """Compute the signature from the alleles.

    Args:
        row (pd.Series): A row of the input dataframe.
        allele_cols (list): List of allele column names.

    Returns:
        tuple: A tuple containing the alleles.
    """
    alleles = tuple(str(row[col]).strip() for col in allele_cols)
    return tuple([a for a in alleles if a and a.lower() != "nan"])


def compute_signature_hash(row: pd.Series) -> str:
    """Compute the hash of the signature.

    Args:
        row (pd.Series): A row of the input dataframe.

    Returns:
        str: The hash of the signature.
    """
    return sha1(str(row["signature"]).encode("utf-8")).hexdigest()


def is_negative_control(sample_name: str) -> bool:
    """Check if the sample is a negative control.

    Args:
        sample_name (str): The name of the sample.

    Returns:
        bool: True if the sample is a negative control, False otherwise.
    """
    name = sample_name.lower()
    return any(k in name for k in NEGATIVE_KEYWORDS)


def intra_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare the signatures of each group of patients.
    Samples from the same patient should have the same signature.
    If the sample is a negative control, the signature should be empty.
    If the sample is unique, it should be marked as a warning.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: The DataFrame with the comparison results.
    """

    df = df.copy()

    # When no alleles are found, the signature is empty
    mask_no_alleles = df["signature_len"] == 0
    # df.loc[mask_no_alleles & df["is_neg"], "status_type"] = "info"
    # df.loc[mask_no_alleles & df["is_neg"], "status_description"] = "controle négatif"
    df.loc[mask_no_alleles & ~df["is_neg"], "status_type"] = "error"
    df.loc[mask_no_alleles & ~df["is_neg"], "status_description"] = "no alleles found"

    # Compare the signatures of each group of patients
    for pid, group in df.groupby("Patient"):
        if len(group) == 1 and not group["is_neg"].iloc[0]:
            if df.loc[group.index, "status_type"].unique() == "success":
                df.loc[group.index, "status_type"] = "warning"
                df.loc[group.index, "status_description"] = "Echantillon unique"
        elif len(group) == 1 and group["is_neg"].iloc[0]:
            if df.loc[group.index, "status_type"].unique() == "success":
                df.loc[group.index, "status_type"] = "info"
                df.loc[group.index, "status_description"] = "Contrôle négatif"
        elif group["signature"].nunique() > 1:
            if df.loc[group.index, "status_type"].unique() == "success":
                df.loc[group.index, "status_type"] = "error"
                df.loc[group.index, "status_description"] = "Incohérente de SNPs"
        elif group["Genre"].nunique() > 1:
            if df.loc[group.index, "status_type"].unique() == "success":
                df.loc[group.index, "status_type"] = "error"
                df.loc[group.index, "status_description"] = "Incohérence de genre"

    # remove unused columns
    df.drop(columns=["signature", "signature_len", "is_neg"], inplace=True)

    return df


def inter_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare the signatures of each group of patients.
    Samples from from different patients must not have the same signature.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: The DataFrame with the comparison results.
    """
    df = df.copy()
    df.drop(columns=["signature"], inplace=True)

    duplicated = []
    df_filtered = df[df["signature_len"] > 0].copy()

    # find samples with the same signature_hash
    for sig, group in df_filtered.groupby("signature_hash"):

        # check if samples with the same signature_hash have different patients
        if len(group["Patient"].unique()) > 1:
            duplicated.append(group)

    if duplicated:
        inconsistent_df = pd.concat(duplicated)
        inconsistent_df.drop(
            columns=["is_neg", "signature_len", "status_type", "status_description"],
            inplace=True,
        )
        return inconsistent_df
    else:
        return pd.DataFrame()


def sample_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """Create a matrix of similarity percentages between samples.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: A DataFrame containing the similarity percentages.
    """
    df = df.copy()

    # get the columns to use for the similarity comparison
    allele_columns = [
        col
        for col in df.columns
        if col.startswith(ALLELE_PREFIX)
        and col != GENDER_ALLELES_X
        and col != GENDER_ALLELES_Y
    ] + ["Genre"]

    patient_ids = df["Sample Name"].unique()  # Get unique patient IDs
    comparison_matrix = pd.DataFrame(index=patient_ids, columns=patient_ids)

    # Compare each pair of patients
    for patient_1 in patient_ids:
        for patient_2 in patient_ids:

            sample_1 = df[df["Sample Name"] == patient_1][
                allele_columns
            ].values.flatten()
            sample_2 = df[df["Sample Name"] == patient_2][
                allele_columns
            ].values.flatten()

            # Compare the alleles of the two samples
            common_alleles = 0
            total_alleles = 0

            for a1, a2 in zip(sample_1, sample_2):
                total_alleles += 1
                # If the two values are NaN, they are considered equal
                if pd.isna(a1) and pd.isna(a2):
                    common_alleles += 1
                # If one value is NaN and the other is not, it's a difference
                elif pd.isna(a1) or pd.isna(a2):
                    continue
                # If the values are equal, count them as common
                elif a1 == a2:
                    common_alleles += 1

            # Calculate the percentage of common alleles
            if total_alleles > 0:
                identity_percentage = (common_alleles / total_alleles) * 100
            else:
                identity_percentage = np.nan
            comparison_matrix.loc[patient_1, patient_2] = identity_percentage

    return comparison_matrix
