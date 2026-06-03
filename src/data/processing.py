"""Data processing module for the SNPXPlex Streamlit application.

This module handles the processing and preparation of genetic data, including file
validation, data loading, and genotype merging.
"""

from typing import List

import numpy as np
import pandas as pd

from src.utils.config import COLUMNS_TO_DROP, REQUIRED_COLUMNS


def merge_allele_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Group allele columns 2 by 2 into a single genotype per locus (vectorized).

    Equivalent to applying, for each ``(a1, a2)`` pair, the per-cell rule::

        clean(v) = str(v).strip().split("_")[-1].replace("nan", "")
        ""              if both cleaned values are empty
        the non-empty   if exactly one is empty
        the shared one  if both are equal
        "v1/v2"         otherwise

    but computed with pandas/numpy vector operations instead of a row-wise
    ``DataFrame.apply(axis=1)``.

    Args:
        df (pd.DataFrame): DataFrame containing allele columns.

    Returns:
        pd.DataFrame: DataFrame with merged genotypes for each locus.
    """
    keeping_cols = [col for col in df.columns if not col.startswith("Allele")]
    merged_data = df[keeping_cols].copy()

    allele_cols = [col for col in df.columns if col.startswith("Allele")]
    pairs = [
        (allele_cols[i], allele_cols[i + 1])
        for i in range(0, len(allele_cols) - 1, 2)
    ]
    if not pairs:
        return merged_data

    # Clean every allele column at once with C-level numpy string ops:
    # str(v).strip().split("_")[-1].replace("nan", "")
    block = df[allele_cols].to_numpy().astype(str)
    block = np.char.strip(block)
    block = np.char.rpartition(block, "_")[..., 2]  # part after the last "_"
    block = np.char.replace(block, "nan", "")
    cleaned = {col: block[:, i] for i, col in enumerate(allele_cols)}

    for idx, (a1, a2) in enumerate(pairs, start=1):
        v1 = cleaned[a1]
        v2 = cleaned[a2]
        combined = np.char.add(np.char.add(v1, "/"), v2)
        merged_data[f"Locus {idx}"] = np.where(
            (v1 == "") & (v2 == ""),
            "",
            np.where(
                v2 == "",
                v1,
                np.where(v1 == "", v2, np.where(v1 == v2, v1, combined)),
            ),
        )

    return merged_data


def compute_identity_matrix(
    df: pd.DataFrame, allele_columns: List[str]
) -> pd.DataFrame:
    """Compute the pairwise sample identity matrix (% shared alleles), vectorized.

    For every pair of samples the identity is the fraction of ``allele_columns``
    that are considered "common", where a column counts as common when both
    values are missing, or both are present and equal. Missing-vs-present never
    counts. The result is identical to the original O(n^3) double loop but is
    computed with numpy in O(n^2 * k).

    Args:
        df (pd.DataFrame): Prepared data with a ``Sample Name`` column.
        allele_columns (List[str]): Columns compared between samples.

    Returns:
        pd.DataFrame: Square matrix indexed by sample name with identity
            percentages (0-100).
    """
    sample_ids = df["Sample Name"].unique()
    total = len(allele_columns)

    if len(sample_ids) == 0 or total == 0:
        return pd.DataFrame(index=sample_ids, columns=sample_ids, dtype=float)

    # One row per sample, aligned to first-appearance order.
    samples = (
        df.drop_duplicates(subset="Sample Name")
        .set_index("Sample Name")
        .loc[sample_ids, allele_columns]
    )
    n = len(sample_ids)

    na = samples.isna().to_numpy()
    # Integer codes so equality can be compared as integers; NaN -> -1.
    codes, _ = pd.factorize(samples.to_numpy().ravel())
    codes = codes.reshape(samples.shape)

    common = np.zeros((n, n), dtype=np.int64)
    for c in range(total):
        col_codes = codes[:, c]
        present = ~na[:, c]
        both_na = na[:, c][:, None] & na[:, c][None, :]
        both_present = present[:, None] & present[None, :]
        equal = col_codes[:, None] == col_codes[None, :]
        common += both_na
        common += both_present & equal

    identity = common.astype(float) / total * 100.0
    return pd.DataFrame(identity, index=sample_ids, columns=sample_ids)


class DataProcessor:
    """Class responsible for processing and preparing genetic data.

    This class provides methods for validating file formats, loading data,
    and preparing it for analysis by merging genotypes and cleaning the dataset.

    Attributes:
        df (pd.DataFrame): The DataFrame containing the genetic data to process.
    """

    def __init__(self, df: pd.DataFrame):
        """Initialize the DataProcessor with a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing genetic data to process.
        """
        self.df = df

    def validate_file_format(self) -> List[str]:
        """Check if the DataFrame has the required columns.

        Returns:
            List[str]: List of missing required columns. Empty list if all columns
                are present.
        """
        missing_columns = [
            col for col in REQUIRED_COLUMNS if col not in self.df.columns
        ]
        return missing_columns

    def load_genemapper_data(self, file) -> pd.DataFrame:
        """Load the Genemapper data from a file.

        Args:
            file: The file object containing Genemapper data.

        Returns:
            pd.DataFrame: DataFrame containing the loaded genetic data.

        Raises:
            ValueError: If the file is empty or malformatted.
        """
        try:
            df = pd.read_csv(file, sep="\t", engine="python")
            if df.empty:
                raise ValueError("Le fichier est vide ou mal formaté.")
            return df
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier : {e}") from e

    def prepare_data(self) -> pd.DataFrame:
        """Prepare the data for analysis by removing unnecessary columns.

        Returns:
            pd.DataFrame: Cleaned DataFrame ready for analysis.
        """
        df = self.df.copy()
        df = df.drop(columns=COLUMNS_TO_DROP, errors="ignore")
        return df

    def merge_genotypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group the columns of alleles 2 by 2 into a single genotype per locus.

        Args:
            df (pd.DataFrame): DataFrame containing allele data.

        Returns:
            pd.DataFrame: DataFrame with merged genotypes for each locus.
        """
        return merge_allele_pairs(df)
