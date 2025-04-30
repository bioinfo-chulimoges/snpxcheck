import pandas as pd
import numpy as np
import plotly
import tempfile
from hashlib import sha1
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from data_processing import DataProcessor
from genetics import GeneticAnalyzer
from reporting import ReportGenerator
from constants import REQUIRED_COLUMNS


ALLELE_PREFIX = "Allele"
GENDER_ALLELES_X = "Allele 29"
GENDER_ALLELES_Y = "Allele 30"
NEGATIVE_KEYWORDS = ["neg", "tem"]


def load_genemapper_data(file) -> pd.DataFrame:
    """
    Load the Genemapper data from a file.

    Args:
        file (str): The path to the Genemapper data file.

    Returns:
        pd.DataFrame: A DataFrame containing the Genemapper data.
    """
    processor = DataProcessor(pd.DataFrame())
    return processor.load_genemapper_data(file)


def validate_file_format(df: pd.DataFrame) -> list[str]:
    """
    Check if the DataFrame has the required columns.

    Args:
        df (pd.DataFrame): The DataFrame to check.

    Returns:
        list[str]: List of missing columns. If all required columns are present, returns an empty list.
    """
    processor = DataProcessor(df)
    return processor.validate_file_format()


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare the data for analysis.

    Args:
        df (pd.DataFrame): The DataFrame to prepare.

    Returns:
        pd.DataFrame: The prepared DataFrame.
    """
    processor = DataProcessor(df)
    analyzer = GeneticAnalyzer(processor.prepare_data())
    return analyzer.prepare_data()


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
    analyzer = GeneticAnalyzer(df)
    prepared_data = analyzer.prepare_data()

    for pid, group in prepared_data.groupby("Patient"):
        if len(group) == 1 and not group["is_neg"].iloc[0]:
            if prepared_data.loc[group.index, "status_type"].unique() == "success":
                prepared_data.loc[group.index, "status_type"] = "warning"
                prepared_data.loc[group.index, "status_description"] = (
                    "Echantillon unique"
                )
        elif len(group) == 1 and group["is_neg"].iloc[0]:
            if prepared_data.loc[group.index, "signature_len"].any() > 0:
                prepared_data.loc[group.index, "status_type"] = "error"
                prepared_data.loc[group.index, "status_description"] = (
                    "Contrôle négatif avec alleles"
                )
            elif prepared_data.loc[group.index, "status_type"].unique() == "success":
                prepared_data.loc[group.index, "status_type"] = "info"
                prepared_data.loc[group.index, "status_description"] = (
                    "Contrôle négatif"
                )
        elif group["signature"].nunique() > 1:
            if prepared_data.loc[group.index, "status_type"].unique() == "success":
                prepared_data.loc[group.index, "status_type"] = "error"
                prepared_data.loc[group.index, "status_description"] = (
                    "Incohérente de SNPs"
                )
        elif group["Genre"].nunique() > 1:
            if prepared_data.loc[group.index, "status_type"].unique() == "success":
                prepared_data.loc[group.index, "status_type"] = "error"
                prepared_data.loc[group.index, "status_description"] = (
                    "Incohérence de genre"
                )

    prepared_data.drop(columns=["signature", "signature_len", "is_neg"], inplace=True)
    return prepared_data


def inter_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """Compare the signatures of each group of patients.
    Samples from from different patients must not have the same signature.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: The DataFrame with the comparison results.
    """
    analyzer = GeneticAnalyzer(df)
    prepared_data = analyzer.prepare_data()
    prepared_data.drop(columns=["signature"], inplace=True)

    duplicated = []
    df_filtered = prepared_data[prepared_data["signature_len"] > 0].copy()

    for sig, group in df_filtered.groupby("signature_hash"):
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


def merge_genotypes(df):
    """
    Group the columns of alleles 2 by 2 into a single genotype per locus.

    Args:
        df (pd.DataFrame) : DataFrame with the columns Allele 1, Allele 2, ...

    Returns:
        pd.DataFrame : Simplified DataFrame with the columns Locus 1, Locus 2, ...
    """
    processor = DataProcessor(df)
    return processor.merge_genotypes(df)


def sample_heatmap(df: pd.DataFrame) -> pd.DataFrame:
    """Create a matrix of similarity percentages between samples.

    Args:
        df (pd.DataFrame): The DataFrame to process.

    Returns:
        pd.DataFrame: A DataFrame containing the similarity percentages.
    """
    analyzer = GeneticAnalyzer(df)
    prepared_data = analyzer.prepare_data()

    allele_columns = analyzer._get_allele_columns() + ["Genre"]
    patient_ids = prepared_data["Sample Name"].unique()
    comparison_matrix = pd.DataFrame(index=patient_ids, columns=patient_ids)

    for patient_1 in patient_ids:
        for patient_2 in patient_ids:
            sample_1 = prepared_data[prepared_data["Sample Name"] == patient_1][
                allele_columns
            ].values.flatten()
            sample_2 = prepared_data[prepared_data["Sample Name"] == patient_2][
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
                identity_percentage = np.nan
            comparison_matrix.loc[patient_1, patient_2] = identity_percentage

    return comparison_matrix


def save_heatmap_as_image(fig: plotly.graph_objects.Figure) -> str:
    """
    Save a Plotly figure to a png image

    Args:
        fig (plotly.graph_objects.Figure): The plotly figure to save

    Returns:
        str : path to the temporary image file
    """
    generator = ReportGenerator()
    return generator.save_heatmap_as_image(fig)


def generate_html_report(
    df_intra, df_inter, fig_path, metadata, errors_intra, errors_inter
):
    """
    Generate a HTML to be converted in PDF with jinja2
    """
    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report_template.html")

    html = template.render(
        interpreter=metadata.get("interpreter", ""),
        week=metadata.get("week", ""),
        serie=metadata.get("serie", ""),
        comment=metadata.get("comment", ""),
        df_intra=df_intra.to_html(
            classes="table",
        ),
        df_inter=df_inter.to_html(classes="table", index=False),
        heatmap_path=fig_path,
        errors_intra=errors_intra,
        errors_inter=errors_inter,
    )
    return html


def save_pdf_from_html(html_content, output_path):
    """Convert the html to a pdf file"""
    with open("test.html", "w") as o:
        o.write(html_content)
    HTML(string=html_content).write_pdf(
        output_path, stylesheets=[CSS("templates/styles.css")]
    )


def generate_pdf_report_custom(
    df_intra, df_inter, figure_path, metadata, errors_intra, errors_inter, output_path
):
    """Generate a PDF report from the data."""
    generator = ReportGenerator()
    generator.generate_pdf_report(
        df_intra,
        df_inter,
        figure_path,
        metadata,
        errors_intra,
        errors_inter,
        output_path,
    )
