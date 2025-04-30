from dataclasses import dataclass
from typing import Optional
import pandas as pd
import plotly.graph_objects as go


@dataclass
class ComparisonResult:
    df_intra: pd.DataFrame
    df_inter: pd.DataFrame
    heatmap: Optional[go.Figure]
    errors_intra: int
    errors_inter: int


@dataclass
class Metadata:
    date: str
    filename: str
    interpreter: str
    week: str
    serie: str
    comment: str


@dataclass
class SessionState:
    comparison_result: Optional[ComparisonResult] = None
    metadata: Optional[Metadata] = None
