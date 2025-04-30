import pandas as pd
from typing import List
from src.utils.config import COLUMNS_TO_DROP, REQUIRED_COLUMNS


class DataProcessor:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def validate_file_format(self) -> List[str]:
        """Check if the DataFrame has the required columns."""
        missing_columns = [
            col for col in REQUIRED_COLUMNS if col not in self.df.columns
        ]
        return missing_columns

    def load_genemapper_data(self, file) -> pd.DataFrame:
        """Load the Genemapper data from a file."""
        try:
            df = pd.read_csv(file, sep="\t", engine="python")
            if df.empty:
                raise ValueError("Le fichier est vide ou mal formaté.")
            return df
        except Exception as e:
            raise ValueError(f"Erreur lors de la lecture du fichier : {e}")

    def prepare_data(self) -> pd.DataFrame:
        """Prepare the data for analysis."""
        df = self.df.copy()
        df = df.drop(columns=COLUMNS_TO_DROP, errors="ignore")
        return df

    def merge_genotypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group the columns of alleles 2 by 2 into a single genotype per locus."""
        keeping_cols = [col for col in df.columns if not col.startswith("Allele")]
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
