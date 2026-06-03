"""Performance regression benchmarks for the comparison pipeline.

Uses the real GeneMapper export in ``.benchmarks/genotypes.txt`` (105 samples).

Run only the benchmarks::

    pytest tests/test_benchmark_comparison.py --benchmark-only

Skip benchmarks in a normal run::

    pytest --benchmark-skip
"""

from pathlib import Path

import pytest

from src.data.processing import compute_identity_matrix, merge_allele_pairs
from src.services.identity_vigilance import IdentityVigilanceService

BENCH_FILE = Path(__file__).resolve().parents[1] / ".benchmarks" / "genotypes.txt"


def _prepare():
    service = IdentityVigilanceService()
    df, error = service.load_and_validate_file(str(BENCH_FILE))
    assert error is None, error
    prepared = service.prepare_data(df)
    allele_columns = [*service.genetic_analyzer._get_allele_columns(), "Genre"]
    return prepared, allele_columns


@pytest.fixture(scope="module")
def prepared():
    if not BENCH_FILE.exists():
        pytest.skip(f"benchmark file missing: {BENCH_FILE}")
    return _prepare()


def test_benchmark_identity_matrix(benchmark, prepared):
    prepared_data, allele_columns = prepared
    result = benchmark(compute_identity_matrix, prepared_data, allele_columns)
    assert result.shape[0] == prepared_data["Sample Name"].nunique()


def test_benchmark_merge_genotypes(benchmark, prepared):
    prepared_data, _ = prepared
    result = benchmark(merge_allele_pairs, prepared_data)
    assert any(col.startswith("Locus") for col in result.columns)


def test_benchmark_full_analysis(benchmark):
    if not BENCH_FILE.exists():
        pytest.skip(f"benchmark file missing: {BENCH_FILE}")

    def run():
        service = IdentityVigilanceService()
        df, _ = service.load_and_validate_file(str(BENCH_FILE))
        prepared_data = service.prepare_data(df)
        service.perform_intra_comparison(prepared_data)
        service.perform_inter_comparison(prepared_data)
        service.generate_heatmap(prepared_data)

    benchmark(run)
