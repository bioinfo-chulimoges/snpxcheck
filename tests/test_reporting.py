import pytest
import pandas as pd
import plotly.graph_objects as go
from src.reporting.generator import ReportGenerator
import os


@pytest.fixture
def sample_data():
    """Create sample data for report generation."""
    # Sample intra-comparison DataFrame
    df_intra = pd.DataFrame(
        {
            "Patient": ["P1", "P1", "P2", "P2"],
            "Sample Name": ["S1", "S2", "S3", "S4"],
            "Genre": ["homme", "homme", "femme", "femme"],
            "status_description": ["", "Warning", "Error", ""],
            "status_type": ["success", "warning", "error", "success"],
        }
    )

    # Sample inter-comparison DataFrame
    df_inter = pd.DataFrame(
        {
            "Sample Name": ["S1", "S2", "S3", "S4"],
            "1": ["C/T", "C/T", "C/C", "T/T"],
            "2": ["A/G", "A/A", "G/G", "A/G"],
            "3": ["T", "T/C", "C", "T/C"],
        }
    )

    # Sample heatmap
    heatmap = go.Figure(
        data=go.Heatmap(
            z=[
                [100, 50, 25, 0],
                [50, 100, 75, 25],
                [25, 75, 100, 50],
                [0, 25, 50, 100],
            ],
            x=["S1", "S2", "S3", "S4"],
            y=["S1", "S2", "S3", "S4"],
        )
    )

    # Sample metadata
    metadata = {
        "date": "2024-04-30",
        "filename": "test.txt",
        "interpreter": "John Doe",
        "week": "2024-W18",
        "serie": "Oui",
        "comment": "Test comment",
    }

    return {
        "df_intra": df_intra,
        "df_inter": df_inter,
        "heatmap": heatmap,
        "metadata": metadata,
        "errors_intra": 1,
        "errors_inter": 2,
    }


@pytest.fixture
def report_generator():
    """Create a ReportGenerator instance."""
    return ReportGenerator()


def test_save_heatmap_as_image(report_generator, sample_data, tmp_path):
    """Test saving the heatmap as an image."""
    heatmap_path = report_generator.save_heatmap_as_image(
        sample_data["heatmap"], str(tmp_path)
    )

    assert heatmap_path.endswith(".png")
    assert (
        str(tmp_path) in heatmap_path
    )  # Vérifie que le chemin temporaire est dans le chemin retourné
    assert os.path.exists(heatmap_path)  # Vérifie que le fichier existe


def test_generate_html_report(report_generator, sample_data, tmp_path):
    """Test generating the HTML report."""
    # Save heatmap first
    heatmap_path = report_generator.save_heatmap_as_image(sample_data["heatmap"])

    html_content = report_generator.generate_html_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
        fig_path=heatmap_path,
        metadata=sample_data["metadata"],
        errors_intra=sample_data["errors_intra"],
        errors_inter=sample_data["errors_inter"],
    )

    assert isinstance(html_content, str)
    assert "Rapport identitovigilance" in html_content
    assert sample_data["metadata"]["date"] in html_content
    assert sample_data["metadata"]["filename"] in html_content
    assert sample_data["metadata"]["week"] in html_content
    assert sample_data["metadata"]["serie"] in html_content
    assert sample_data["metadata"]["comment"] in html_content
    assert sample_data["metadata"]["interpreter"] in html_content
    assert "table" in html_content  # Check for table HTML


def test_save_pdf_from_html(report_generator, sample_data, tmp_path):
    """Test converting HTML to PDF."""
    # Generate HTML content first
    heatmap_path = report_generator.save_heatmap_as_image(sample_data["heatmap"])
    html_content = report_generator.generate_html_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
        fig_path=heatmap_path,
        metadata=sample_data["metadata"],
        errors_intra=sample_data["errors_intra"],
        errors_inter=sample_data["errors_inter"],
    )

    # Create a temporary file for the PDF
    pdf_path = tmp_path / "test_report.pdf"

    # Convert HTML to PDF
    report_generator.save_pdf_from_html(html_content, str(pdf_path))

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_generate_pdf_report(report_generator, sample_data, tmp_path):
    """Test the complete PDF report generation process."""
    # Create a temporary file for the PDF
    pdf_path = tmp_path / "test_report.pdf"

    # Generate the PDF report
    report_generator.generate_pdf_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
        figure_path="",  # Will be generated internally
        metadata=sample_data["metadata"],
        errors_intra=sample_data["errors_intra"],
        errors_inter=sample_data["errors_inter"],
        output_path=str(pdf_path),
    )

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
