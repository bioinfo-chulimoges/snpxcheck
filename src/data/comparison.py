"""Comparison module for genetic data analysis.

This module provides functionality for comparing genetic data between samples, including
intra-patient and inter-patient comparisons.
"""

from typing import List, Optional, Tuple

import pandas as pd

from src.data.genetics import GeneticAnalyzer
from src.data.processing import (
    DataProcessor,
    compute_identity_matrix,
    merge_allele_pairs,
)
from src.visualization.plots import create_plotly_heatmap


class ComparisonEngine:
    """Service for performing genetic comparisons.

    This class provides methods for comparing genetic data between samples,
    including intra-patient and inter-patient comparisons, and generating
    visualization of the results.

    Attributes:
        data (pd.DataFrame): DataFrame containing the genetic data to analyze.
    """

    def __init__(self, data: pd.DataFrame):
        """Initialize the ComparisonEngine with genetic data.

        Args:
            data (pd.DataFrame): DataFrame containing genetic data to analyze.
        """
        self.data = data
        processor = DataProcessor(data)
        analyzer = GeneticAnalyzer(processor.prepare_data())
        self.prepared_data = analyzer.prepare_data()

    def perform_intra_comparison(self) -> Tuple[pd.DataFrame, int]:
        """Perform intra-patient comparison analysis.

        Returns:
            Tuple[pd.DataFrame, int]: DataFrame with comparison results and error count.
        """
        df_intra = self._intra_comparison(self.prepared_data)
        df_intra = self._merge_genotypes(df_intra)
        error_count = df_intra["status_type"].value_counts().get("error", 0)
        return df_intra, error_count

    def perform_inter_comparison(self) -> Tuple[pd.DataFrame, int]:
        """Perform inter-patient comparison analysis.

        Returns:
            Tuple[pd.DataFrame, int]: DataFrame with comparison results and error count.
        """
        df_inter = self._inter_comparison(self.prepared_data)
        error_count = len(df_inter)
        if not df_inter.empty:
            df_inter = self._merge_genotypes(df_inter)
        return df_inter, error_count

    def generate_heatmap(self) -> Optional[object]:
        """Generate a heatmap of genetic similarities between patients.

        Returns:
            plotly.graph_objects.Figure: Plotly figure containing the heatmap.
        """
        comparison_matrix = self._sample_heatmap(self.prepared_data)
        if not comparison_matrix.empty:
            return create_plotly_heatmap(comparison_matrix)
        return None

    def get_alleles_columns(self, df: pd.DataFrame) -> List[str]:
        """Get the list of allele columns from a dataframe."""
        return [str(col) for col in df.columns if col.startswith("Locus")]

    def get_intra_column_order(self, df: pd.DataFrame) -> List[str]:
        """Get the column order for intra-patient comparison display."""
        alleles_columns = self.get_alleles_columns(df)
        return [
            "Patient",
            "Sample Name",
            "Genre",
            "status_description",
            *alleles_columns,
            "status_type",
        ]

    def get_inter_column_order(self, df: pd.DataFrame) -> List[str]:
        """Get the column order for inter-patient comparison display."""
        locus_columns = self.get_alleles_columns(df)
        return [
            "Patient",
            "Sample Name",
            "Genre",
            *locus_columns,
            "signature_hash",
        ]

    def _intra_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method for intra-patient comparison."""
        df = df.copy()
        for _pid, group in df.groupby("Patient"):
            if len(group) == 1 and not group["is_neg"].iloc[0]:
                if df.loc[group.index, "status_type"].unique() == "success":
                    df.loc[group.index, "status_type"] = "warning"
                    df.loc[group.index, "status_description"] = "Echantillon unique"
            elif len(group) == 1 and group["is_neg"].iloc[0]:
                if df.loc[group.index, "signature_len"].any() > 0:
                    df.loc[group.index, "status_type"] = "error"
                    df.loc[group.index, "status_description"] = (
                        "Contrôle négatif avec alleles"
                    )
                elif df.loc[group.index, "status_type"].unique() == "success":
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
        return df

    def _inter_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method for inter-patient comparison."""
        df = df.copy()
        df.drop(columns=["signature"], inplace=True)

        duplicated = []
        df_filtered = df[df["signature_len"] > 0].copy()

        for _sig, group in df_filtered.groupby("signature_hash"):
            if len(group["Patient"].unique()) > 1:
                duplicated.append(group)

        if duplicated:
            inconsistent_df = pd.concat(duplicated)
            inconsistent_df.drop(
                columns=[
                    "is_neg",
                    "signature_len",
                    "status_type",
                    "status_description",
                ],
                inplace=True,
            )
            return inconsistent_df
        else:
            return pd.DataFrame()

    def _merge_genotypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group the columns of alleles 2 by 2 into a single genotype per locus."""
        return merge_allele_pairs(df)

    def _sample_heatmap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method for generating the heatmap data."""
        allele_columns = [
            col
            for col in df.columns
            if col.startswith("Allele") and col not in {"Allele 29", "Allele 30"}
        ] + ["Genre"]
        return compute_identity_matrix(df, allele_columns)
