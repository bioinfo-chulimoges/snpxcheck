import pandas as pd
import plotly.graph_objects as go
import pytest

from src.visualization.plots import (
    create_plotly_heatmap,
    highlight_status,
    insert_blank_rows_between_groups,
)


@pytest.fixture
def sample_comparison_data():
    """Create a sample DataFrame for comparison visualization."""
    data = {
        "Sample Name": ["sample1", "sample2", "sample3", "sample4"],
        "Locus 1": ["C/T", "C/T", "C/C", "T/T"],
        "Locus 2": ["A/G", "A/A", "G/G", "A/G"],
        "Locus 3": ["T", "T/C", "C", "T/C"],
        "status_type": ["success", "warning", "error", "success"],
        "status_description": ["", "Warning message", "Error message", ""],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_heatmap_matrix():
    """Create a sample comparison matrix for heatmap generation."""
    data = {
        "sample1": [100, 50, 25, 0],
        "sample2": [50, 100, 75, 25],
        "sample3": [25, 75, 100, 50],
        "sample4": [0, 25, 50, 100],
    }
    return pd.DataFrame(data, index=["sample1", "sample2", "sample3", "sample4"])


def test_create_plotly_heatmap(sample_heatmap_matrix):
    """Test the create_plotly_heatmap function."""
    heatmap = create_plotly_heatmap(sample_heatmap_matrix)

    assert isinstance(heatmap, go.Figure)
    assert len(heatmap.data) == 1  # Should have one heatmap trace
    assert isinstance(heatmap.data[0], go.Heatmap)

    # Check dimensions
    assert len(heatmap.data[0].x) == len(sample_heatmap_matrix.columns)
    assert len(heatmap.data[0].y) == len(sample_heatmap_matrix.index)


def test_highlight_status(sample_comparison_data):
    """Test the highlight_status function."""
    styled_row = highlight_status(sample_comparison_data.iloc[0])

    # Check that the styling is a list of strings
    assert isinstance(styled_row, list)
    assert all(isinstance(style, str) for style in styled_row)

    # Check that the styling contains background-color
    assert any("background-color" in style for style in styled_row)

    # Test different status types
    for status in ["success", "error", "info", "warning"]:
        row = sample_comparison_data.iloc[0].copy()
        row["status_type"] = status
        styled_row = highlight_status(row)
        assert any("background-color" in style for style in styled_row)


def test_insert_blank_rows_between_groups(sample_comparison_data):
    """Test the insert_blank_rows_between_groups function."""
    # Add a group column
    sample_comparison_data["Patient"] = ["A", "A", "B", "B"]

    result_df = insert_blank_rows_between_groups(sample_comparison_data, "Patient")

    # Check that the result has more rows than the input
    assert len(result_df) > len(sample_comparison_data)

    # Check that blank rows are inserted between groups
    patient_values = result_df["Patient"].tolist()
    assert patient_values.count("") > 0  # Should have blank rows

    # Check that the blank rows are in the correct positions
    patient_indices = [i for i, x in enumerate(patient_values) if x != ""]
    for i in range(len(patient_indices) - 1):
        if patient_values[patient_indices[i]] != patient_values[patient_indices[i + 1]]:
            # There should be a blank row between different groups
            assert patient_values[patient_indices[i] + 1] == ""
