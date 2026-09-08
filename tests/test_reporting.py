import inspect
import sys

import pandas as pd
import plotly.graph_objects as go
import pytest
from pypdf import PdfReader

from src.reporting.generator import ReportGenerator
from src.version import VERSION

# xhtml2pdf does not implement @page margin boxes: parsing this document fails.
UNRENDERABLE_DOCUMENT = (
    '<html><head><style>@page { @bottom-left { content: "x"; } }</style>'
    "</head><body><p>report</p></body></html>"
)


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


def test_generate_html_report(report_generator, sample_data, tmp_path):
    """Test generating the HTML report."""
    html_content = report_generator.generate_html_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
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
    html_content = report_generator.generate_html_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
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
        metadata=sample_data["metadata"],
        errors_intra=sample_data["errors_intra"],
        errors_inter=sample_data["errors_inter"],
        output_path=str(pdf_path),
    )

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def _pdf_text(pdf_path) -> str:
    """Extract the whole text content of a PDF file."""
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() for page in reader.pages)


def _generate_report(report_generator, sample_data, pdf_path) -> None:
    """Generate the PDF report for the sample data into pdf_path."""
    report_generator.generate_pdf_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
        metadata=sample_data["metadata"],
        errors_intra=sample_data["errors_intra"],
        errors_inter=sample_data["errors_inter"],
        output_path=str(pdf_path),
    )


def test_pdf_contains_report_headings_and_metadata(
    report_generator, sample_data, tmp_path
):
    """The PDF exposes the title, the metadata block and both section headings."""
    pdf_path = tmp_path / "report.pdf"
    _generate_report(report_generator, sample_data, pdf_path)

    text = _pdf_text(pdf_path)

    assert "Rapport identitovigilance" in text
    assert sample_data["metadata"]["filename"] in text
    assert sample_data["metadata"]["interpreter"] in text
    assert "Comparaison Intra-Patients" in text
    assert "Comparaison Inter-Patients" in text


def test_pdf_contains_every_compared_sample_name(
    report_generator, sample_data, tmp_path
):
    """Every sample of the inter-patient table is rendered in the PDF."""
    pdf_path = tmp_path / "report.pdf"
    _generate_report(report_generator, sample_data, pdf_path)

    text = _pdf_text(pdf_path)

    for sample_name in sample_data["df_inter"]["Sample Name"]:
        assert sample_name in text


def test_pdf_footer_shows_version_and_pagination(
    report_generator, sample_data, tmp_path
):
    """The page footer carries the application version and the page counter."""
    pdf_path = tmp_path / "report.pdf"
    _generate_report(report_generator, sample_data, pdf_path)

    text = _pdf_text(pdf_path)

    assert f"SNPXCheck - Identitovigilance - {VERSION}" in text
    assert "Page 1 / 1" in text


def test_pdf_pages_are_a4_portrait(report_generator, sample_data, tmp_path):
    """Pages are A4 portrait (595 x 842 pt), not the PDF engine default."""
    pdf_path = tmp_path / "report.pdf"
    _generate_report(report_generator, sample_data, pdf_path)

    page = PdfReader(str(pdf_path)).pages[0]

    assert (round(float(page.mediabox.width)), round(float(page.mediabox.height))) == (
        595,
        842,
    )


def test_pdf_generation_needs_no_system_libraries():
    """PDF rendering relies on pure-Python packages only.

    WeasyPrint needs Cairo/Pango shared libraries, which cannot be installed on
    Streamlit Community Cloud. The renderer must stay importable without them.
    """
    source = inspect.getsource(sys.modules[ReportGenerator.__module__])

    assert "weasyprint" not in source.lower()


def test_generated_html_embeds_the_stylesheet(report_generator, sample_data):
    """The HTML report is self-contained: the stylesheet is inlined, not linked.

    xhtml2pdf silently ignores a stylesheet it fails to load, which would yield a
    valid but completely unstyled report.
    """
    html_content = report_generator.generate_html_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
        metadata=sample_data["metadata"],
        errors_intra=sample_data["errors_intra"],
        errors_inter=sample_data["errors_inter"],
    )

    assert "<link" not in html_content
    assert "-pdf-frame-content" in html_content


def test_save_pdf_from_html_fails_loudly_on_unrenderable_document(tmp_path):
    """A document the PDF engine cannot render raises instead of failing silently."""
    generator = ReportGenerator()

    with pytest.raises(RuntimeError):
        generator.save_pdf_from_html(
            UNRENDERABLE_DOCUMENT, str(tmp_path / "report.pdf")
        )


def test_failed_conversion_leaves_the_target_file_untouched(tmp_path):
    """A rendering failure must not replace an existing report with a broken file."""
    pdf_path = tmp_path / "report.pdf"
    pdf_path.write_bytes(b"previous report")
    generator = ReportGenerator()

    with pytest.raises(RuntimeError):
        generator.save_pdf_from_html(UNRENDERABLE_DOCUMENT, str(pdf_path))

    assert pdf_path.read_bytes() == b"previous report"


def test_report_tables_carry_their_css_classes(report_generator, sample_data):
    """Both comparison tables are tagged so the stylesheet can size their columns.

    xhtml2pdf ignores <colgroup>, so column widths are driven by the per-column
    classes pandas emits on styled tables.
    """
    html_content = report_generator.generate_html_report(
        df_intra=sample_data["df_intra"],
        df_inter=sample_data["df_inter"],
        metadata=sample_data["metadata"],
        errors_intra=sample_data["errors_intra"],
        errors_inter=sample_data["errors_inter"],
    )

    assert 'class="table table-intra"' in html_content
    assert 'class="table table-inter"' in html_content
    assert "col_heading" in html_content
