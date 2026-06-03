# ruff: noqa: PLR2004
"""Equivalence tests for the vectorized comparison code.

These tests pin the *exact* behavior of the original (slow) algorithms by embedding
faithful reference implementations and asserting that the new vectorized production
functions produce identical output, both on the real benchmark dataset and on hand-
crafted edge cases (NaN, empty strings, duplicates, single sample).
"""

from hashlib import sha1
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.data.processing import compute_identity_matrix, merge_allele_pairs
from src.services.identity_vigilance import IdentityVigilanceService
from src.utils.config import GENDER_ALLELES_X, GENDER_ALLELES_Y

BENCH_FILE = Path(__file__).resolve().parents[1] / ".benchmarks" / "genotypes.txt"


# --------------------------------------------------------------------------- #
# Reference (original) implementations — kept verbatim as the source of truth  #
# --------------------------------------------------------------------------- #
def naive_sample_heatmap(df: pd.DataFrame, allele_columns: list) -> pd.DataFrame:
    patient_ids = df["Sample Name"].unique()
    comparison_matrix = pd.DataFrame(index=patient_ids, columns=patient_ids)

    for patient_1 in patient_ids:
        for patient_2 in patient_ids:
            sample_1 = (
                df[df["Sample Name"] == patient_1][allele_columns].values.flatten()
            )
            sample_2 = (
                df[df["Sample Name"] == patient_2][allele_columns].values.flatten()
            )

            common_alleles = 0
            total_alleles = 0
            for a1, a2 in zip(sample_1, sample_2):
                total_alleles += 1
                if pd.isna(a1) and pd.isna(a2):
                    common_alleles += 1
                elif pd.isna(a1) or pd.isna(a2):
                    continue
                elif a1 == a2:
                    common_alleles += 1

            if total_alleles > 0:
                identity_percentage = (common_alleles / total_alleles) * 100
            else:
                identity_percentage = pd.NA
            comparison_matrix.loc[patient_1, patient_2] = identity_percentage

    return comparison_matrix


def naive_merge_genotypes(df: pd.DataFrame) -> pd.DataFrame:
    keeping_cols = [col for col in df.columns if not col.startswith("Allele")]
    merged_data = df[keeping_cols].copy()

    allele_cols = [col for col in df.columns if col.startswith("Allele")]
    pairs = [
        (allele_cols[i], allele_cols[i + 1])
        for i in range(0, len(allele_cols) - 1, 2)
    ]

    for idx, (a1, a2) in enumerate(pairs, start=1):

        def combine(row, a1, a2):
            val1 = str(row[a1]).strip().split("_")[-1].replace("nan", "")
            val2 = str(row[a2]).strip().split("_")[-1].replace("nan", "")
            if not val1 and not val2:
                return ""
            if val1 and not val2:
                return val1
            if not val1 and val2:
                return val2
            if val1 == val2:
                return val1
            return f"{val1}/{val2}"

        merged_data[f"Locus {idx}"] = df.apply(combine, args=(a1, a2), axis=1)

    return merged_data


def naive_signature(df: pd.DataFrame, allele_cols: list) -> pd.Series:
    def compute(row):
        alleles = tuple(str(row[col]).strip() for col in allele_cols)
        return tuple(a for a in alleles if a and a.lower() != "nan")

    return df.apply(compute, axis=1)


def naive_genre(df: pd.DataFrame) -> pd.Series:
    def determine(row):
        x = row.get(GENDER_ALLELES_X)
        y = row.get(GENDER_ALLELES_Y)
        if not pd.isna(x) and x == "X" and (pd.isna(y) or y == ""):
            return "femme"
        elif not pd.isna(x) and x == "X" and not pd.isna(y) and y == "Y":
            return "homme"
        else:
            return "indéterminé"

    return df.apply(determine, axis=1)


# --------------------------------------------------------------------------- #
# Fixtures                                                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture
def prepared_real_data():
    if not BENCH_FILE.exists():
        pytest.skip(f"benchmark file missing: {BENCH_FILE}")
    service = IdentityVigilanceService()
    df, error = service.load_and_validate_file(str(BENCH_FILE))
    assert error is None, error
    prepared = service.prepare_data(df)
    allele_columns = [*service.genetic_analyzer._get_allele_columns(), "Genre"]
    return prepared, allele_columns


@pytest.fixture
def edge_case_df():
    """Small frame exercising NaN, empty strings, equality and divergence."""
    return pd.DataFrame(
        {
            "Sample Name": ["A", "B", "C", "D"],
            "Allele 1": ["12", "12", np.nan, ""],
            "Allele 2": [np.nan, np.nan, "7", "7"],
            "Allele 3": ["", "", "", ""],
            "Allele 4": ["X_15", "15", "9", np.nan],
            "Genre": ["homme", "femme", "homme", "homme"],
        }
    )


# --------------------------------------------------------------------------- #
# Identity matrix (heatmap)                                                    #
# --------------------------------------------------------------------------- #
def test_identity_matrix_matches_naive_real_data(prepared_real_data):
    prepared, allele_columns = prepared_real_data
    expected = naive_sample_heatmap(prepared, allele_columns)
    result = compute_identity_matrix(prepared, allele_columns)
    assert_frame_equal(
        result.astype(float),
        expected.astype(float),
        check_dtype=False,
        check_names=False,
    )


def test_identity_matrix_edge_cases(edge_case_df):
    allele_columns = ["Allele 1", "Allele 2", "Allele 3", "Allele 4", "Genre"]
    expected = naive_sample_heatmap(edge_case_df, allele_columns)
    result = compute_identity_matrix(edge_case_df, allele_columns)
    assert_frame_equal(
        result.astype(float),
        expected.astype(float),
        check_dtype=False,
        check_names=False,
    )


def test_identity_matrix_single_sample():
    df = pd.DataFrame({"Sample Name": ["only"], "Allele 1": ["5"], "Genre": ["homme"]})
    result = compute_identity_matrix(df, ["Allele 1", "Genre"])
    assert result.shape == (1, 1)
    assert float(result.iloc[0, 0]) == 100.0


def test_identity_matrix_diagonal_is_100(prepared_real_data):
    prepared, allele_columns = prepared_real_data
    result = compute_identity_matrix(prepared, allele_columns)
    diag = np.diag(result.to_numpy().astype(float))
    assert np.allclose(diag, 100.0)


# --------------------------------------------------------------------------- #
# Genotype merging                                                             #
# --------------------------------------------------------------------------- #
def test_merge_allele_pairs_matches_naive_real_data(prepared_real_data):
    prepared, _ = prepared_real_data
    expected = naive_merge_genotypes(prepared)
    result = merge_allele_pairs(prepared)
    assert_frame_equal(result, expected, check_dtype=False)


def test_merge_allele_pairs_edge_cases(edge_case_df):
    expected = naive_merge_genotypes(edge_case_df)
    result = merge_allele_pairs(edge_case_df)
    assert_frame_equal(result, expected, check_dtype=False)


# --------------------------------------------------------------------------- #
# prepare_data internals: signature + Genre                                    #
# --------------------------------------------------------------------------- #
def test_prepare_data_signature_matches_naive(prepared_real_data):
    prepared, _ = prepared_real_data
    service = IdentityVigilanceService()
    allele_cols = service.genetic_analyzer.__class__(prepared)._get_allele_columns()
    # exclude the engineered columns; rebuild signature from raw allele columns
    allele_cols = [c for c in allele_cols if c.startswith("Allele")]
    expected = naive_signature(prepared, allele_cols).tolist()
    got = prepared["signature"].tolist()
    assert got == expected


def test_prepare_data_hash_consistent(prepared_real_data):
    prepared, _ = prepared_real_data
    expected = [
        sha1(str(sig).encode("utf-8")).hexdigest() for sig in prepared["signature"]
    ]
    assert prepared["signature_hash"].tolist() == expected


def test_prepare_data_genre_matches_naive(prepared_real_data):
    prepared, _ = prepared_real_data
    expected = naive_genre(prepared).tolist()
    assert prepared["Genre"].tolist() == expected
