"""Data models for the SNPXPlex Streamlit application.

This module contains the data classes used to structure and store the application's
data, including comparison results, metadata, and session state.
"""

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import plotly.graph_objects as go


@dataclass
class ComparisonResult:
    """Class representing the results of genetic comparisons.

    This class stores the results of both intra-patient and inter-patient comparisons,
    along with visualization data and error counts.

    Attributes:
        df_intra (pd.DataFrame): DataFrame containing intra-patient comparison results.
        df_inter (pd.DataFrame): DataFrame containing inter-patient comparison results.
        heatmap (Optional[go.Figure]): Plotly figure for the comparison heatmap.
        errors_intra (int): Number of errors found in intra-patient comparisons.
        errors_inter (int): Number of errors found in inter-patient comparisons.
    """

    df_intra: pd.DataFrame
    df_inter: pd.DataFrame
    heatmap: Optional[go.Figure]
    errors_intra: int
    errors_inter: int


@dataclass
class Metadata:
    """Class representing metadata about the analysis session.

    This class stores information about when and how the analysis was performed,
    including date, filename, interpreter information, and additional notes.

    Attributes:
        date (str): Date of the analysis.
        filename (str): Name of the input file.
        interpreter (str): Name of the person who performed the analysis.
        week (str): Week number of the analysis.
        serie (str): Series identifier.
        comment (str): Additional comments or notes.
    """

    date: str
    filename: str
    interpreter: str
    week: str
    serie: str
    comment: str


@dataclass
class SessionState:
    """Class representing the current state of the Streamlit session.

    This class maintains the state of the application between reruns,
    storing comparison results and metadata.

    Attributes:
        comparison_result (Optional[ComparisonResult]): Results of the comparisons.
        metadata (Optional[Metadata]): Metadata about the current analysis session.
    """

    comparison_result: Optional[ComparisonResult] = None
    metadata: Optional[Metadata] = None
