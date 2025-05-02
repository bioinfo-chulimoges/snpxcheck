"""Comparison module for genetic data analysis.

This module provides functionality for comparing genetic data between samples, including
intra-patient and inter-patient comparisons.
"""

import pandas as pd
from typing import List, Tuple, Optional
from src.data.processing import DataProcessor
from src.data.genetics import GeneticAnalyzer
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
        return (
            [
                "Patient",
                "Sample Name",
                "Genre",
                "status_description",
            ]
            + alleles_columns
            + ["status_type"]
        )

    def get_inter_column_order(self, df: pd.DataFrame) -> List[str]:
        """Get the column order for inter-patient comparison display."""
        locus_columns = self.get_alleles_columns(df)
        return (
            [
                "Patient",
                "Sample Name",
                "Genre",
            ]
            + locus_columns
            + ["signature_hash"]
        )

    def _intra_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method for intra-patient comparison."""
        df = df.copy()
        for pid, group in df.groupby("Patient"):
            if len(group) == 1 and not group["is_neg"].iloc[0]:
                if df.loc[group.index, "status_type"].unique() == "success":
                    df.loc[group.index, "status_type"] = "warning"
                    df.loc[group.index, "status_description"] = (
                        "Echantillon unique"
                    )
            elif len(group) == 1 and group["is_neg"].iloc[0]:
                if df.loc[group.index, "signature_len"].any() > 0:
                    df.loc[group.index, "status_type"] = "error"
                    df.loc[group.index, "status_description"] = (
                        "Contrôle négatif avec alleles"
                    )
                elif df.loc[group.index, "status_type"].unique() == "success":
                    df.loc[group.index, "status_type"] = "info"
                    df.loc[group.index, "status_description"] = (
                        "Contrôle négatif"
                    )
            elif group["signature"].nunique() > 1:
                if df.loc[group.index, "status_type"].unique() == "success":
                    df.loc[group.index, "status_type"] = "error"
                    df.loc[group.index, "status_description"] = (
                        "Incohérente de SNPs"
                    )
            elif group["Genre"].nunique() > 1:
                if df.loc[group.index, "status_type"].unique() == "success":
                    df.loc[group.index, "status_type"] = "error"
                    df.loc[group.index, "status_description"] = (
                        "Incohérence de genre"
                    )
        return df

    def _inter_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method for inter-patient comparison."""
        df = df.copy()
        df.drop(columns=["signature"], inplace=True)

        duplicated = []
        df_filtered = df[df["signature_len"] > 0].copy()

        for sig, group in df_filtered.groupby("signature_hash"):
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
        keeping_cols = [
            col for col in df.columns if not col.startswith("Allele")
        ]
        merged_data = df[keeping_cols].copy()

        allele_cols = [col for col in df.columns if col.startswith("Allele")]
        pairs = [
            (allele_cols[i], allele_cols[i + 1])
            for i in range(0, len(allele_cols) - 1, 2)
        ]

        for idx, (a1, a2) in enumerate(pairs, start=1):

            def combine(row):
                val1 = str(row[a1]).strip().split("_")[-1].replace("nan", "")
                val2 = str(row[a2]).strip().split("_")[-1].replace("nan", "")
                if not val1 and not val2:
                    return ""
                if val1 and not val2:
                    return val1
                if not val1 and val2:
                    return val2
                if val1 == val2:
                    return val1
                return f"{val1}/{val2}"

            merged_data[f"Locus {idx}"] = df.apply(combine, axis=1)

        return merged_data

    def _sample_heatmap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method for generating the heatmap data."""
        allele_columns = [
            col
            for col in df.columns
            if col.startswith("Allele")
            and col != "Allele 29"
            and col != "Allele 30"
        ] + ["Genre"]
        patient_ids = df["Sample Name"].unique()
        comparison_matrix = pd.DataFrame(
            index=patient_ids, columns=patient_ids
        )

        for patient_1 in patient_ids:
            for patient_2 in patient_ids:
                sample_1 = df[df["Sample Name"] == patient_1][
                    allele_columns
                ].values.flatten()
                sample_2 = df[df["Sample Name"] == patient_2][
                    allele_columns
                ].values.flatten()

                common_alleles = 0
                total_alleles = 0

                for a1, a2 in zip(sample_1, sample_2):
                    total_alleles += 1
                    if pd.isna(a1) and pd.isna(a2):
                        common_alleles += 1
                    elif pd.isna(a1) or pd.isna(a2):
                        continue
                    elif a1 == a2:
                        common_alleles += 1

                if total_alleles > 0:
                    identity_percentage = (
                        common_alleles / total_alleles
                    ) * 100
                else:
                    identity_percentage = pd.NA
                comparison_matrix.loc[patient_1, patient_2] = (
                    identity_percentage
                )

        return comparison_matrix
