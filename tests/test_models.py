import pandas as pd
import plotly.graph_objects as go

from src.utils.models import ComparisonResult, Metadata, SessionState


def test_comparison_result_creation():
    """Test the creation of a ComparisonResult object."""
    # Create sample data
    df_intra = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    df_inter = pd.DataFrame({"col1": [5, 6], "col2": [7, 8]})
    heatmap = go.Figure()
    errors_intra = 1
    errors_inter = 2

    # Create ComparisonResult
    result = ComparisonResult(
        df_intra=df_intra,
        df_inter=df_inter,
        heatmap=heatmap,
        errors_intra=errors_intra,
        errors_inter=errors_inter,
    )

    # Test attributes
    assert result.df_intra.equals(df_intra)
    assert result.df_inter.equals(df_inter)
    assert result.heatmap == heatmap
    assert result.errors_intra == errors_intra
    assert result.errors_inter == errors_inter


def test_metadata_creation():
    """Test the creation of a Metadata object."""
    # Create Metadata
    metadata = Metadata(
        date="2024-04-30",
        filename="test.txt",
        interpreter="John Doe",
        week="2024-W18",
        serie="Oui",
        comment="Test comment",
    )

    # Test attributes
    assert metadata.date == "2024-04-30"
    assert metadata.filename == "test.txt"
    assert metadata.interpreter == "John Doe"
    assert metadata.week == "2024-W18"
    assert metadata.serie == "Oui"
    assert metadata.comment == "Test comment"


def test_session_state_initialization():
    """Test the initialization of a SessionState object."""
    # Create SessionState
    state = SessionState()

    # Test initial values
    assert state.comparison_result is None
    assert state.metadata is None


def test_session_state_with_data():
    """Test SessionState with data."""
    # Create sample data
    df_intra = pd.DataFrame({"col1": [1, 2]})
    df_inter = pd.DataFrame({"col1": [3, 4]})
    heatmap = go.Figure()
    result = ComparisonResult(
        df_intra=df_intra,
        df_inter=df_inter,
        heatmap=heatmap,
        errors_intra=1,
        errors_inter=2,
    )

    metadata = Metadata(
        date="2024-04-30",
        filename="test.txt",
        interpreter="John Doe",
        week="2024-W18",
        serie="Oui",
        comment="Test comment",
    )

    # Create SessionState with data
    state = SessionState(
        comparison_result=result,
        metadata=metadata,
    )

    # Test attributes
    assert state.comparison_result == result
    assert state.metadata == metadata
