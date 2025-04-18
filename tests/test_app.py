from io import StringIO
import pandas as pd
from app import (
    read_file,
    highlight_status,
    insert_blank_rows_between_groups,
    create_plotly_heatmap,
)


def test_app_upload(tmp_path):

    file_path = tmp_path / "input.txt"
    file_path.write_text("Sample Name\tAllele 1\tAllele 2\nS1\tA\tT\n")

    with open(file_path, "rb") as f:
        result = read_file(f)
        assert isinstance(result, pd.DataFrame)


def test_read_file_valid():
    mock_data = "Sample Name\tAllele 1\tAllele 2\nS1\tA\tT\n"
    fake_file = StringIO(mock_data)
    df = read_file(fake_file)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Sample Name", "Allele 1", "Allele 2"]


def test_read_file_invalid():
    fake_file = StringIO("Invalid content")

    df = read_file(fake_file)
    assert df is None


# --- highlight_status ---


def test_highlight_status_error_coloring():
    df = pd.Series({"status_type": "error"})
    styled = highlight_status(df)
    assert styled == ["background-color: #f8d7da"]


def test_highlight_status_warning_coloring():
    df = pd.Series({"status_type": "warning"})
    styled = highlight_status(df)
    assert styled == ["background-color: #fff3cd"]


def test_highlight_status_info_coloring():
    df = pd.Series({"status_type": "info"})
    styled = highlight_status(df)
    assert styled == ["background-color: #d1ecf1"]


def test_highlight_status_success_coloring():
    df = pd.Series({"status_type": "success"})
    styled = highlight_status(df)
    assert styled == ["background-color: #ffffff"]


def test_highlight_status_other_coloring():
    df = pd.Series({"status_type": "unknown"})
    styled = highlight_status(df)
    assert styled == ["background-color: white"]


# --- insert_blank_rows_between_groups ---


def test_insert_blank_rows():
    df = pd.DataFrame(
        {
            "Patient": ["P1", "P1", "P2", "P2"],
            "Sample Name": ["P1a", "P1b", "P2a", "P2b"],
            "Allele 1": ["A", "A", "T", "T"],
        }
    )
    result = insert_blank_rows_between_groups(df, group_col="Patient")

    assert result.shape[0] == df.shape[0] + 1
    assert result["Patient"].tolist() == ["P1", "P1", "", "P2", "P2"]


def test_create_plotly_heatmap():
    data = pd.DataFrame(
        [[1.0, 0.8], [0.8, 1.0]], index=["P1", "P2"], columns=["P1", "P2"]
    )
    fig = create_plotly_heatmap(data)
    assert fig.data is not None
    assert fig.layout is not None
