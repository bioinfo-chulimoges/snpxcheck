from dataclasses import dataclass
from typing import Dict, Optional
import pandas as pd


@dataclass
class Metadata:
    interpreter: str
    week: str
    comment: str
    serie: str


@dataclass
class ComparisonResult:
    df_intra: pd.DataFrame
    df_inter: pd.DataFrame
    heatmap: Optional[object] = None
    errors_intra: int = 0
    errors_inter: int = 0


class SessionState:
    def __init__(self):
        self.metadata: Optional[Metadata] = None
        self.comparison_result: Optional[ComparisonResult] = None

    def update_metadata(self, interpreter: str, week: str, comment: str, serie: str):
        self.metadata = Metadata(interpreter, week, comment, serie)

    def update_comparison_result(
        self,
        df_intra: pd.DataFrame,
        df_inter: pd.DataFrame,
        heatmap: Optional[object] = None,
        errors_intra: int = 0,
        errors_inter: int = 0,
    ):
        self.comparison_result = ComparisonResult(
            df_intra=df_intra,
            df_inter=df_inter,
            heatmap=heatmap,
            errors_intra=errors_intra,
            errors_inter=errors_inter,
        )
