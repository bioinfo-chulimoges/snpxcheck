import pandas as pd
import pytest
from src.app.main import (
    render_intra_comparison,
    render_inter_comparison,
    render_heatmap,
    generate_pdf_report,
    main,
)
from src.utils.models import SessionState, ComparisonResult, Metadata
import warnings

# Ignore the setDaemon deprecation warning from kaleido
warnings.filterwarnings("ignore", category=DeprecationWarning, module="kaleido")


@pytest.fixture
def sample_comparison_data():
    """Create sample comparison data."""
    df_intra = pd.DataFrame(
        {
            "Patient": ["P1", "P1", "P2", "P2"],
            "Sample Name": ["S1", "S2", "S3", "S4"],
            "Genre": ["homme", "homme", "femme", "femme"],
            "status_description": ["", "Warning", "Error", ""],
            "status_type": ["success", "warning", "error", "success"],
        }
    )

    df_inter = pd.DataFrame(
        {
            "Sample Name": ["S1", "S2", "S3", "S4"],
            "signature_hash": ["hash1", "hash1", "hash2", "hash2"],
            "1": ["C/T", "C/T", "C/C", "T/T"],
            "2": ["A/G", "A/A", "G/G", "A/G"],
            "3": ["T", "T/C", "C", "T/C"],
        }
    )

    return df_intra, df_inter


@pytest.fixture
def sample_heatmap():
    """Create a sample heatmap."""
    import plotly.graph_objects as go

    return go.Figure(
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


@pytest.fixture
def session_state(sample_comparison_data, sample_heatmap):
    """Create a sample session state."""
    df_intra, df_inter = sample_comparison_data
    return SessionState(
        comparison_result=ComparisonResult(
            df_intra=df_intra,
            df_inter=df_inter,
            heatmap=sample_heatmap,
            errors_intra=1,
            errors_inter=2,
        ),
        metadata=Metadata(
            date="2024-04-30",
            filename="test.txt",
            interpreter="John Doe",
            week="2024-W18",
            serie="Oui",
            comment="Test comment",
        ),
    )


def test_render_intra_comparison(sample_comparison_data):
    """Test rendering intra-comparison results."""
    df_intra, _ = sample_comparison_data
    error_count = 1

    result = render_intra_comparison(df_intra, error_count)

    assert isinstance(result, pd.DataFrame)
    assert all(
        col in result.columns
        for col in [
            "Patient",
            "Sample Name",
            "Genre",
            "status_description",
            "status_type",
        ]
    )


def test_render_inter_comparison(sample_comparison_data):
    """Test rendering inter-comparison results."""
    _, df_inter = sample_comparison_data

    # This function doesn't return anything, we just check it doesn't raise an error
    render_inter_comparison(df_inter)


def test_render_heatmap(sample_heatmap):
    """Test rendering the heatmap."""
    # This function doesn't return anything, we just check it doesn't raise an error
    render_heatmap(sample_heatmap)


def test_generate_pdf_report(session_state, tmp_path):
    """Test generating the PDF report."""
    # Call the function
    result_path = generate_pdf_report(session_state)

    # Verify the returned path and file
    assert result_path is not None
    assert result_path.exists()
    assert result_path.stat().st_size > 0

    # Clean up
    result_path.unlink()


def test_main():
    """Test the main function."""
    # This is a basic test that just checks the function can be called
    # without raising an error. More detailed testing would require
    # mocking Streamlit's components.
    main()
