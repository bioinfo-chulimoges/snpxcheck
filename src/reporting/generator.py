"""Report generation module.

This module handles the generation of HTML and PDF reports from analysis results,
including the intra- and inter-patient comparison tables.
"""

import html
import io
import os
from typing import Union

import pandas as pd
from jinja2 import Environment, FileSystemLoader
from pandas.io.formats.style import Styler
from xhtml2pdf import pisa

from src.version import VERSION

Table = Union[pd.DataFrame, Styler]


class ReportGenerator:
    """Class responsible for generating analysis reports.

    This class provides methods for creating HTML and PDF reports from analysis
    results. PDF rendering relies on xhtml2pdf, a pure-Python engine, so that the
    application needs no system libraries at runtime.

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

    def _read_stylesheet(self) -> str:
        """Read the report stylesheet.

        The stylesheet is inlined in the generated document rather than linked:
        xhtml2pdf silently ignores a stylesheet it cannot load, which would yield a
        valid but completely unstyled report.

        Returns:
            str: Content of the stylesheet.
        """
        css_path = os.path.join(self.template_dir, "styles.css")
        with open(css_path, encoding="utf-8") as css_file:
            return css_file.read()

    @staticmethod
    def _render_table(table: Table, css_class: str) -> str:
        """Render a comparison table as HTML.

        Tables are rendered through the pandas Styler so that every cell carries the
        per-column classes the stylesheet needs: xhtml2pdf ignores <colgroup>, and
        distributes the width evenly across columns without them.

        Args:
            table (Table): DataFrame or Styler holding the comparison data.
            css_class (str): Additional class identifying the table.

        Returns:
            str: HTML markup of the table.
        """
        styler = table if isinstance(table, Styler) else table.style.hide(axis="index")
        return styler.set_table_attributes(f'class="table {css_class}"').to_html()

    def generate_html_report(
        self,
        df_intra: Table,
        df_inter: Table,
        metadata: dict,
        errors_intra: int,
        errors_inter: int,
    ) -> str:
        """Generate a self-contained HTML report using jinja2 template.

        Args:
            df_intra (Table): Intra-patient comparison table.
            df_inter (Table): Inter-patient comparison table.
            metadata (dict): Dictionary containing report metadata.
            errors_intra (int): Number of intra-patient errors.
            errors_inter (int): Number of inter-patient errors.

        Returns:
            str: Generated HTML content, stylesheet included.
        """
        template = self.env.get_template("report_template.html")

        return template.render(
            styles=self._read_stylesheet(),
            date=metadata.get("date", ""),
            filename=metadata.get("filename", ""),
            interpreter=metadata.get("interpreter", ""),
            week=metadata.get("week", ""),
            serie=metadata.get("serie", ""),
            comment=html.escape(metadata.get("comment", "")).replace("\n", "<br>"),
            df_intra=self._render_table(df_intra, "table-intra"),
            df_inter=self._render_table(df_inter, "table-inter"),
            errors_intra=errors_intra,
            errors_inter=errors_inter,
            version=VERSION,
        )

    def save_pdf_from_html(self, html_content: str, output_path: str):
        """Convert the HTML content to a PDF file.

        Args:
            html_content (str): Self-contained HTML content to convert.
            output_path (str): Path where to save the PDF file.

        Raises:
            RuntimeError: If the document cannot be rendered. The destination file
                is left untouched in that case.
        """
        buffer = io.BytesIO()
        try:
            status = pisa.CreatePDF(src=html_content, dest=buffer, encoding="utf-8")
        except Exception as exc:
            raise RuntimeError(
                f"Could not render the PDF report to {output_path}"
            ) from exc

        if status.err:
            raise RuntimeError(
                f"Could not render the PDF report to {output_path}: "
                f"{status.err} error(s)"
            )

        with open(output_path, "wb") as pdf_file:
            pdf_file.write(buffer.getvalue())

    def generate_pdf_report(  # noqa: PLR0913
        self,
        df_intra: Table,
        df_inter: Table,
        metadata: dict,
        errors_intra: int,
        errors_inter: int,
        output_path: str,
    ):
        """Generate a PDF report from the data.

        Args:
            df_intra (Table): Intra-patient comparison table.
            df_inter (Table): Inter-patient comparison table.
            metadata (dict): Dictionary containing report metadata.
            errors_intra (int): Number of intra-patient errors.
            errors_inter (int): Number of inter-patient errors.
            output_path (str): Path where to save the PDF file.
        """
        html_content = self.generate_html_report(
            df_intra,
            df_inter,
            metadata,
            errors_intra,
            errors_inter,
        )
        self.save_pdf_from_html(html_content, output_path)
