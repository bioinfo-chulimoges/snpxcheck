"""Genetic analysis module for the SNPXPlex Streamlit application.

This module handles genetic data analysis, including sex determination, signature
computation, and control sample identification.
"""

import pandas as pd
from typing import Tuple
from hashlib import sha1
from src.utils.config import (
    ALLELE_PREFIX,
    GENDER_ALLELES_X,
    GENDER_ALLELES_Y,
    NEGATIVE_KEYWORDS,
)


class GeneticAnalyzer:
    """Class responsible for genetic data analysis.

    This class provides methods for analyzing genetic data, including
    sex determination, signature computation, and control sample identification.

    Attributes:
        df (pd.DataFrame): The DataFrame containing the genetic data to analyze.
        allele_cols (list): List of allele columns excluding gender alleles.
    """

    def __init__(self, df: pd.DataFrame):
        """Initialize the GeneticAnalyzer with a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame containing genetic data to analyze.
        """
        self.df = df
        self.allele_cols = self._get_allele_columns()

    def _get_allele_columns(self) -> list:
        """Get the list of allele columns excluding gender alleles.

        Returns:
            list: List of allele column names.
        """
        return [
            col
            for col in self.df.columns
            if col.startswith(ALLELE_PREFIX)
            and col != GENDER_ALLELES_X
            and col != GENDER_ALLELES_Y
        ]

    def determine_sex(self, row: pd.Series) -> str:
        """Determine the sex of a sample based on the X and Y alleles.

        Args:
            row (pd.Series): Row containing allele data for a sample.

        Returns:
            str: "femme" for female, "homme" for male, "indéterminé" if undetermined.
        """
        x = row.get(GENDER_ALLELES_X)
        y = row.get(GENDER_ALLELES_Y)

        if not pd.isna(x) and x == "X" and (pd.isna(y) or y == ""):
            return "femme"
        elif not pd.isna(x) and x == "X" and not pd.isna(y) and y == "Y":
            return "homme"
        else:
            return "indéterminé"

    def compute_signature(self, row: pd.Series) -> Tuple:
        """Compute the signature from the alleles.

        Args:
            row (pd.Series): Row containing allele data for a sample.

        Returns:
            Tuple: Tuple of non-empty allele values.
        """
        alleles = tuple(str(row[col]).strip() for col in self.allele_cols)
        return tuple([a for a in alleles if a and a.lower() != "nan"])

    def compute_signature_hash(self, row: pd.Series) -> str:
        """Compute the hash of the signature.

        Args:
            row (pd.Series): Row containing signature data.

        Returns:
            str: SHA1 hash of the signature.
        """
        return sha1(str(row["signature"]).encode("utf-8")).hexdigest()

    def is_negative_control(self, sample_name: str) -> bool:
        """Check if the sample is a negative control.

        Args:
            sample_name (str): Name of the sample to check.

        Returns:
            bool: True if the sample is a negative control, False otherwise.
        """
        if not sample_name:
            return False
        name = sample_name.lower()
        return any(k in name for k in NEGATIVE_KEYWORDS)

    def prepare_data(self) -> pd.DataFrame:
        """Prepare the data for genetic analysis.

        This method computes signatures, hashes, and adds metadata to the DataFrame.

        Returns:
            pd.DataFrame: DataFrame with added genetic analysis results and metadata.
        """
        df = self.df.copy()

        # Compute signatures and hashes
        df["signature"] = df.apply(self.compute_signature, axis=1)
        df["signature_hash"] = df.apply(self.compute_signature_hash, axis=1)
        df["signature_len"] = df["signature"].apply(len)

        # Add metadata
        df["Genre"] = df.apply(self.determine_sex, axis=1)
        df["Patient"] = df["Sample Name"].str.replace(
            r"^(.*?)(bis|ter)$", r"\1", regex=True
        )
        df["is_neg"] = df["Sample Name"].apply(self.is_negative_control)

        # Initialize status fields
        df["status_type"] = "success"
        df["status_description"] = ""

        return df
