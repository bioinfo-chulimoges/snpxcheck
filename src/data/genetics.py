"""Genetic analysis module for the SNPXPlex Streamlit application.

This module handles genetic data analysis, including sex determination, signature
computation, and control sample identification.
"""

from hashlib import sha1
from typing import Tuple

import numpy as np
import pandas as pd

from src.data.sample_name import parse_sample_name
from src.utils.config import (
    ALLELE_PREFIX,
    GENDER_ALLELES_X,
    GENDER_ALLELES_Y,
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
            and col not in (GENDER_ALLELES_X, GENDER_ALLELES_Y)
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
        return parse_sample_name(sample_name).is_negative

    def _compute_signatures(self, df: pd.DataFrame) -> pd.Series:
        """Compute the per-row allele signatures without a row-wise apply.

        Vectorizes the string cleaning per allele column, then assembles the
        variable-length tuples over a numpy row view. Produces output identical
        to applying :meth:`compute_signature` row by row.

        Args:
            df (pd.DataFrame): DataFrame containing the allele columns.

        Returns:
            pd.Series: Series of signature tuples, indexed like ``df``.
        """
        if self.allele_cols:
            stripped = np.column_stack(
                [df[col].astype(str).str.strip().to_numpy() for col in self.allele_cols]
            )
        else:
            stripped = np.empty((len(df), 0), dtype=object)

        signatures = [
            tuple(a for a in row if a and a.lower() != "nan") for row in stripped
        ]
        return pd.Series(signatures, index=df.index, dtype=object)

    def _determine_sex_vectorized(self, df: pd.DataFrame) -> np.ndarray:
        """Determine sex for every row without a row-wise apply.

        Vectorized equivalent of :meth:`determine_sex`.

        Args:
            df (pd.DataFrame): DataFrame containing the gender allele columns.

        Returns:
            np.ndarray: Array of "femme" / "homme" / "indéterminé" values.
        """
        x = df[GENDER_ALLELES_X]
        y = df[GENDER_ALLELES_Y]
        x_is_female_marker = x.notna() & (x == "X")
        y_absent = y.isna() | (y == "")
        y_is_male_marker = y.notna() & (y == "Y")
        return np.where(
            x_is_female_marker & y_absent,
            "femme",
            np.where(x_is_female_marker & y_is_male_marker, "homme", "indéterminé"),
        )

    def prepare_data(self) -> pd.DataFrame:
        """Prepare the data for genetic analysis.

        This method computes signatures, hashes, and adds metadata to the DataFrame.

        Returns:
            pd.DataFrame: DataFrame with added genetic analysis results and metadata.
        """
        df = self.df.copy()

        # Compute signatures and hashes (vectorized; equivalent to the per-row
        # compute_signature / compute_signature_hash / determine_sex methods).
        df["signature"] = self._compute_signatures(df)
        df["signature_hash"] = df["signature"].map(
            lambda sig: sha1(str(sig).encode("utf-8")).hexdigest()
        )
        df["signature_len"] = df["signature"].apply(len)

        # Add metadata
        df["Genre"] = self._determine_sex_vectorized(df)
        parsed = df["Sample Name"].apply(parse_sample_name)
        df["Patient"] = parsed.apply(lambda p: p.patient_id)
        df["is_neg"] = parsed.apply(lambda p: p.is_negative)

        # Initialize status fields
        df["status_type"] = "success"
        df["status_description"] = ""

        return df
