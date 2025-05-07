"""Report generation module.

This module handles the generation of HTML and PDF reports from analysis results,
including heatmap visualization and comparison data.
"""

import os
import tempfile
from typing import Optional

import pandas as pd
import plotly
from jinja2 import Environment, FileSystemLoader
from weasyprint import CSS, HTML

from src.version import VERSION


class ReportGenerator:
    """Class responsible for generating analysis reports.

    This class provides methods for creating HTML and PDF reports from analysis results,
    including heatmap visualization and comparison data.

    Attributes:
        env (Environment): Jinja2 template environment.
        template_dir (str): Directory containing report templates.
    """

    def __init__(self, template_dir: str = "src/reporting/templates"):
        """Initialize the ReportGenerator with template directory.

        Args:
            template_dir (str, optional): Directory containing report templates.
                Defaults to "src/reporting/templates".
        """
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_dir = template_dir

    def save_heatmap_as_image(
        self,
        fig: plotly.graph_objects.Figure,
        output_dir: Optional[str] = None,
    ) -> str:
        """Save a Plotly figure to a PNG image.

        Args:
            fig (plotly.graph_objects.Figure): Plotly figure to save.
            output_dir (str, optional): Directory to save the image.
                If None, uses a temporary file. Defaults to None.

        Returns:
            str: Path to the saved image file.
        """
        if output_dir is None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                fig.write_image(tmpfile.name, width=1200, height=1200)
                return tmpfile.name
        else:
            output_path = os.path.join(output_dir, "heatmap.png")
            fig.write_image(output_path, width=1200, height=1200)
            return output_path

    def generate_html_report(  # noqa: PLR0913
        self,
        df_intra: pd.DataFrame,
        df_inter: pd.DataFrame,
        fig_path: str,
        metadata: dict,
        errors_intra: int,
        errors_inter: int,
    ) -> str:
        """Generate a HTML report using jinja2 template.

        Args:
            df_intra (pd.DataFrame): DataFrame containing intra-patient comparison.
            df_inter (pd.DataFrame): DataFrame containing inter-patient comparison.
            fig_path (str): Path to the heatmap image.
            metadata (dict): Dictionary containing report metadata.
            errors_intra (int): Number of intra-patient errors.
            errors_inter (int): Number of inter-patient errors.

        Returns:
            str: Generated HTML content.
        """
        template = self.env.get_template("report_template.html")

        return template.render(
            date=metadata.get("date", ""),
            filename=metadata.get("filename", ""),
            interpreter=metadata.get("interpreter", ""),
            week=metadata.get("week", ""),
            serie=metadata.get("serie", ""),
            comment=metadata.get("comment", ""),
            df_intra=df_intra.to_html(classes="table"),
            df_inter=df_inter.to_html(classes="table", index=False),
            heatmap_path=fig_path,
            errors_intra=errors_intra,
            errors_inter=errors_inter,
            version=VERSION,
        )

    def save_pdf_from_html(self, html_content: str, output_path: str):
        """Convert the HTML content to a PDF file.

        Args:
            html_content (str): HTML content to convert.
            output_path (str): Path where to save the PDF file.
        """
        css_path = os.path.join(self.template_dir, "styles.css")
        HTML(string=html_content).write_pdf(output_path, stylesheets=[CSS(css_path)])

    def generate_pdf_report(  # noqa: PLR0913
        self,
        df_intra: pd.DataFrame,
        df_inter: pd.DataFrame,
        figure_path: str,
        metadata: dict,
        errors_intra: int,
        errors_inter: int,
        output_path: str,
    ):
        """Generate a PDF report from the data.

        Args:
            df_intra (pd.DataFrame): DataFrame containing intra-patient comparison.
            df_inter (pd.DataFrame): DataFrame containing inter-patient comparison.
            figure_path (str): Path to the heatmap image.
            metadata (dict): Dictionary containing report metadata.
            errors_intra (int): Number of intra-patient errors.
            errors_inter (int): Number of inter-patient errors.
            output_path (str): Path where to save the PDF file.
        """
        html = self.generate_html_report(
            df_intra,
            df_inter,
            figure_path,
            metadata,
            errors_intra,
            errors_inter,
        )
        self.save_pdf_from_html(html, output_path)
