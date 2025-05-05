"""Data processing and analysis module.

This package provides functionality for processing and analyzing genetic data, including
data loading, validation, comparison, and genetic analysis.
"""

from src.data.comparison import ComparisonEngine
from src.data.genetics import GeneticAnalyzer
from src.data.processing import DataProcessor

__all__ = [
    "ComparisonEngine",
    "DataProcessor",
    "GeneticAnalyzer",
]
