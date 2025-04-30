import tempfile
import pandas as pd
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
import plotly
import os


class ReportGenerator:
    def __init__(self, template_dir: str = "src/reporting/templates"):
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.template_dir = template_dir

    def save_heatmap_as_image(
        self, fig: plotly.graph_objects.Figure, output_dir: str = None
    ) -> str:
        """Save a Plotly figure to a png image."""
        if output_dir is None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                fig.write_image(tmpfile.name, width=1200, height=1200)
                return tmpfile.name
        else:
            output_path = os.path.join(output_dir, "heatmap.png")
            fig.write_image(output_path, width=1200, height=1200)
            return output_path

    def generate_html_report(
        self,
        df_intra: pd.DataFrame,
        df_inter: pd.DataFrame,
        fig_path: str,
        metadata: dict,
        errors_intra: int,
        errors_inter: int,
    ) -> str:
        """Generate a HTML report using jinja2 template."""
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
        )

    def save_pdf_from_html(self, html_content: str, output_path: str):
        """Convert the html to a pdf file."""
        css_path = os.path.join(self.template_dir, "styles.css")
        HTML(string=html_content).write_pdf(output_path, stylesheets=[CSS(css_path)])

    def generate_pdf_report(
        self,
        df_intra: pd.DataFrame,
        df_inter: pd.DataFrame,
        figure_path: str,
        metadata: dict,
        errors_intra: int,
        errors_inter: int,
        output_path: str,
    ):
        """Generate a PDF report from the data."""
        html = self.generate_html_report(
            df_intra, df_inter, figure_path, metadata, errors_intra, errors_inter
        )
        self.save_pdf_from_html(html, output_path)
