import pandas as pd
import plotly
import numpy as np
from natsort import natsorted
from typing import List


def highlight_status(row: pd.Series) -> List[str]:
    """Highlight rows based on the status_type column."""
    color = {
        "success": "#ffffff",  # green clair
        "error": "#f8d7da",  # red clair
        "info": "#d1ecf1",  # blue clair
        "warning": "#fff3cd",  # yellow clair
    }.get(row["status_type"], "white")
    return [f"background-color: {color}"] * len(row)


def insert_blank_rows_between_groups(
    df: pd.DataFrame, group_col: str = "Patient"
) -> pd.DataFrame:
    """Insert blank rows between groups in a DataFrame."""
    df = df.sort_values(group_col)
    rows = []

    def create_empty_row(columns):
        return {col: "" for col in columns}

    previous_value = None
    for _, row in df.iterrows():
        if previous_value is not None and row[group_col] != previous_value:
            rows.append(create_empty_row(df))
        rows.append(row.to_dict())
        previous_value = row[group_col]

    return pd.DataFrame(rows).reset_index(drop=True)


def create_plotly_heatmap(
    comparison_matrix: pd.DataFrame,
) -> plotly.graph_objects.Figure:
    """Create a heatmap using Plotly."""
    sorted_patients = natsorted(comparison_matrix.index.tolist())
    comparison_matrix = comparison_matrix.loc[sorted_patients, sorted_patients]

    masked_matrix = comparison_matrix.where(
        np.tril(np.ones(comparison_matrix.shape)).astype(bool)
    )

    n = len(sorted_patients) / 2
    cell_size = 30
    fig_size = n * cell_size

    fig = plotly.graph_objects.Figure(
        data=plotly.graph_objects.Heatmap(
            z=masked_matrix.values,
            x=masked_matrix.columns,
            y=masked_matrix.index,
            colorscale=plotly.colors.sequential.Viridis.reverse(),
            coloraxis="coloraxis",
            zmin=0,
            zmax=100,
            hovertemplate=(
                "<b>Patient 1:</b> %{y}<br>"
                "<b>Patient 2:</b> %{x}<br>"
                "<b>Identité:</b> %{z:.2f}<extra>%</extra>"
            ),
        )
    )

    fig.update_layout(
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        xaxis_title=None,
        yaxis_title=None,
        width=fig_size,
        height=fig_size,
        template="plotly_white",
        xaxis_scaleanchor="y",
        xaxis_side="bottom",
        coloraxis=dict(
            colorbar=dict(
                title="Identité (%)",
                lenmode="fraction",
                len=0.8,
                yanchor="middle",
                y=0.5,
            )
        ),
        margin=dict(t=0, b=10, l=10, r=10),
    )

    fig.update_xaxes(
        tickmode="array",
        tickvals=list(masked_matrix.columns),
        ticktext=list(masked_matrix.columns),
    )

    fig.update_yaxes(
        tickmode="array",
        tickvals=list(masked_matrix.index),
        ticktext=list(masked_matrix.index),
        autorange="reversed",
    )

    return fig
