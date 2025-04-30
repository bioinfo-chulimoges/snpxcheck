import pandas as pd
import numpy as np
from typing import List, Tuple, Optional
import utils
from visualization import create_plotly_heatmap


class ComparisonEngine:
    def __init__(self, data: pd.DataFrame):
        self.data = data
        self.prepared_data = utils.prepare_data(data)

    def perform_intra_comparison(self) -> Tuple[pd.DataFrame, int]:
        """Perform intra-patient comparison and return the results with error count."""
        df_intra = utils.intra_comparison(self.prepared_data)
        df_intra = utils.merge_genotypes(df_intra)
        error_count = df_intra["status_type"].value_counts().get("error", 0)
        return df_intra, error_count

    def perform_inter_comparison(self) -> Tuple[pd.DataFrame, int]:
        """Perform inter-patient comparison and return the results with error count."""
        df_inter = utils.inter_comparison(self.prepared_data)
        error_count = len(df_inter)
        if not df_inter.empty:
            df_inter = utils.merge_genotypes(df_inter)
        return df_inter, error_count

    def generate_heatmap(self) -> Optional[object]:
        """Generate the comparison heatmap."""
        comparison_matrix = utils.sample_heatmap(self.prepared_data)
        if not comparison_matrix.empty:
            return create_plotly_heatmap(comparison_matrix)
        return None

    def validate_file_format(self) -> List[str]:
        """Validate the input file format."""
        return utils.validate_file_format(self.data)

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
