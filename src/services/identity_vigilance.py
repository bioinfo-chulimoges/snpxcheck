from typing import Optional, Tuple

import pandas as pd

from src.data.genetics import GeneticAnalyzer
from src.data.processing import DataProcessor
from src.reporting.generator import ReportGenerator
from src.visualization.plots import (
    create_plotly_heatmap,
    highlight_status,
    insert_blank_rows_between_groups,
)


class IdentityVigilanceService:
    def __init__(self):
        self.data_processor = DataProcessor(pd.DataFrame())
        self.genetic_analyzer = GeneticAnalyzer(pd.DataFrame())
        self.report_generator = ReportGenerator()

    def load_and_validate_file(
        self, file
    ) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Load and validate the input file."""
        try:
            df = self.data_processor.load_genemapper_data(file)
            self.data_processor = DataProcessor(df)
            missing_columns = self.data_processor.validate_file_format()
            if missing_columns:
                return (
                    None,
                    f"Le fichier ne semble pas au bon format.\n\n"
                    f"Colonnes manquantes : {missing_columns}",
                )
            return df, None
        except Exception as e:
            return None, str(e)

    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare the data for analysis."""
        # clean the data
        prepared_df = self.data_processor.prepare_data()
        # prepare the genetics data
        self.genetic_analyzer = GeneticAnalyzer(prepared_df)
        return self.genetic_analyzer.prepare_data()

    def perform_intra_comparison(
        self, prepared_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, int, bool]:
        """Perform intra-patient comparison."""
        df_intra = self._intra_comparison(prepared_data)

        neg_control_clean = False
        neg_control_rows = df_intra[df_intra["is_neg"]]
        if not neg_control_rows.empty:
            if (neg_control_rows["signature_len"] == 0).all():
                neg_control_clean = True

        df_intra = self.data_processor.merge_genotypes(df_intra)
        df_intra = self.format_intra_comparison(df_intra)
        error_count = df_intra["status_type"].value_counts().get("error", 0)
        return df_intra, error_count, neg_control_clean

    def format_intra_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format the intra-comparison DataFrame for display.

        Args:
            df: The DataFrame to format

        Returns:
            DataFrame with columns reordered and unnecessary columns removed
        """
        # Get the list of locus columns
        locus_columns = [col for col in df.columns if col.startswith("Locus")]

        # Define the column order
        column_order = [
            "Patient",
            "Sample Name",
            "Genre",
            "status_description",
            "status_type",
            *locus_columns,
        ]

        # Remove unnecessary columns and reorder
        return df[column_order].copy()

    def format_inter_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format the inter-comparison DataFrame for display.

        Args:
            df: The DataFrame to format

        Returns:
            DataFrame with columns reordered and unnecessary columns removed
        """
        # Get the list of locus columns
        locus_columns = [col for col in df.columns if col.startswith("Locus")]

        # Define the column order
        column_order = [
            "Patient",
            "Sample Name",
            "Genre",
            *locus_columns,
            "signature_hash",
        ]

        # Remove unnecessary columns and reorder
        return df[column_order].copy()

    def perform_inter_comparison(
        self, prepared_data: pd.DataFrame
    ) -> Tuple[pd.DataFrame, int]:
        """Perform inter-patient comparison."""
        df_inter = self._inter_comparison(prepared_data)
        error_count = len(df_inter)
        if not df_inter.empty:
            df_inter = self.data_processor.merge_genotypes(df_inter)
            df_inter = self.format_inter_comparison(df_inter)
        return df_inter, error_count

    def generate_heatmap(self, prepared_data: pd.DataFrame) -> Optional[object]:
        """Generate the comparison heatmap."""
        comparison_matrix = self._sample_heatmap(prepared_data)
        if not comparison_matrix.empty:
            return create_plotly_heatmap(comparison_matrix)
        return None

    def format_intra_for_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format the intra-comparison DataFrame for the PDF report.

        Args:
            df: The DataFrame to format

        Returns:
            DataFrame with selected columns in the correct order
        """
        # Define the column order
        column_order = [
            "Patient",
            "Sample Name",
            "Genre",
            "status_description",
            "status_type",
        ]

        # Select and reorder columns
        df = df[column_order].copy()
        return df.style.apply(highlight_status, axis=1).hide(axis="index")

    def format_inter_for_report(self, df: pd.DataFrame) -> pd.DataFrame:
        """Format the inter-comparison DataFrame for the PDF report.

        Args:
            df: The DataFrame to format

        Returns:
            DataFrame with selected columns in the correct order
        """
        if df.empty:
            return pd.DataFrame()

        # Get the list of locus columns
        locus_columns = [col for col in df.columns if col.startswith("Locus")]

        # Define the column order
        column_order = ["Sample Name", "signature_hash", *locus_columns]

        # Select and reorder columns
        df = df[column_order].copy()

        # Rename locus columns to remove 'Locus ' prefix
        rename_dict = {col: col.replace("Locus ", "") for col in locus_columns}
        df = df.rename(columns=rename_dict)

        df = insert_blank_rows_between_groups(df, "signature_hash")
        return df.drop(columns=["signature_hash"])

    def generate_pdf_report(  # noqa: PLR0913
        self,
        df_intra: pd.DataFrame,
        df_inter: pd.DataFrame,
        heatmap: object,
        metadata: dict,
        errors_intra: int,
        errors_inter: int,
        output_path: str,
    ):
        """Generate a PDF report."""
        # Format the intra DataFrame for the report
        df_intra_formatted = self.format_intra_for_report(df_intra)
        df_inter_formatted = self.format_inter_for_report(df_inter)

        self.report_generator.generate_pdf_report(
            df_intra=df_intra_formatted,
            df_inter=df_inter_formatted,
            metadata=metadata,
            errors_intra=errors_intra,
            errors_inter=errors_inter,
            output_path=output_path,
        )

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

    def _sample_heatmap(self, df: pd.DataFrame) -> pd.DataFrame:
        """Internal method for generating the heatmap data."""
        allele_columns = [
            *self.genetic_analyzer._get_allele_columns(),
            "Genre",
        ]
        patient_ids = df["Sample Name"].unique()
        comparison_matrix = pd.DataFrame(index=patient_ids, columns=patient_ids)

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
                    identity_percentage = (common_alleles / total_alleles) * 100
                else:
                    identity_percentage = pd.NA
                comparison_matrix.loc[patient_1, patient_2] = identity_percentage

        return comparison_matrix
