import io
import pytest
import pandas as pd
import numpy as np

from utils import (
    load_genemapper_data,
    determine_sex,
    compute_signature,
    compute_signature_hash,
    is_negative_control,
    intra_comparison,
    inter_comparison,
    sample_heatmap,
)


def test_valid_file():
    content = "SNP1\tSNP2\nAA\tTT\nGG\tCC"
    file = io.StringIO(content)
    df = load_genemapper_data(file)
    assert not df.empty
    assert df.shape == (2, 2)


def test_empty_file():
    file = io.StringIO("")
    with pytest.raises(RuntimeError):
        load_genemapper_data(file)


def test_determine_sex_male():
    row = pd.Series({"Allele 29": "X", "Allele 30": "Y"})
    assert determine_sex(row) == "homme"


def test_determine_sex_female():
    row = pd.Series({"Allele 29": "X", "Allele 30": None})
    assert determine_sex(row) == "femme"


def test_determine_sex_unknown():
    row = pd.Series({"Allele 29": None, "Allele 30": None})
    assert determine_sex(row) == "indéterminé"


def test_compute_signature():
    row = pd.Series({"Allele 1": "A", "Allele 2": "T", "Allele 3": ""})
    result = compute_signature(row, ["Allele 1", "Allele 2", "Allele 3"])
    assert result == ("A", "T")


def test_compute_signature_hash():
    row = pd.Series({"signature": ("A", "T", "C")})
    hash_val = compute_signature_hash(row)
    assert isinstance(hash_val, str)
    assert len(hash_val) == 40  # SHA1 hash length


def test_is_negative_control_true():
    assert is_negative_control("temoin_negatif") is True


def test_is_negative_control_false():
    assert is_negative_control("sample1") is False


# ----------------------------
# Tests for intra_comparison function
# ----------------------------


def test_intra_comparison_consistent_group():
    df = pd.DataFrame(
        {
            "Sample Name": ["patient1", "patient1bis"],
            "Allele 1": ["A", "A"],
            "Allele 2": ["T", "T"],
            "Allele 29": ["X", "X"],
            "Allele 30": ["Y", "Y"],
            "signature_len": [2, 2],
            "signature": [("A", "T"), ("A", "T")],
            "signature_hash": ["hash1", "hash1"],
            "is_neg": [False, False],
            "Patient": ["patient1", "patient1"],
            "Genre": ["homme", "homme"],
            "status_type": ["success", "success"],
            "status_description": ["", ""],
        }
    )
    result = intra_comparison(df)
    assert len(result) == 2
    assert all(result["status_type"] == "success")


def test_intra_comparison_patient_no_allele_error():
    df = pd.DataFrame(
        {
            "Sample Name": ["patient1"],
            "Allele 1": [""],
            "Allele 2": [""],
            "Allele 29": [""],
            "Allele 30": [""],
            "signature_len": [0],
            "signature": [""],
            "signature_hash": [""],
            "is_neg": [False],
            "Patient": ["patient1"],
            "Genre": ["homme"],
            "status_type": ["success"],
            "status_description": [""],
        }
    )
    result = intra_comparison(df)
    assert len(result) == 1
    assert all(result["status_type"] == "error")


def test_intra_comparison_inconsistent_signature():
    df = pd.DataFrame(
        {
            "Sample Name": ["patient1", "patient1bis"],
            "Allele 1": ["A", "T"],  # différence
            "Allele 2": ["C", "C"],
            "Allele 29": ["X", "X"],
            "Allele 30": ["Y", "Y"],
            "signature_len": [2, 2],
            "signature": [("A", "T"), ("T", "C")],
            "signature_hash": ["hash1", "hash2"],
            "is_neg": [False, False],
            "Patient": ["patient1", "patient1"],
            "Genre": ["homme", "homme"],
            "status_type": ["success", "success"],
            "status_description": ["", ""],
        }
    )
    result = intra_comparison(df)
    assert all(result["status_type"] == "error")
    assert all("SNPs" in status for status in result["status_description"])


def test_intra_comparison_inconsistent_sex():
    df = pd.DataFrame(
        {
            "Sample Name": ["patient1", "patient1bis"],
            "Allele 1": ["A", "A"],
            "Allele 2": ["C", "C"],
            "Allele 29": ["X", "X"],
            "Allele 30": ["Y", ""],  # one men, one women
            "signature_len": [2, 2],
            "signature": [("A", "C"), ("A", "C")],
            "signature_hash": ["hash1", "hash2"],
            "is_neg": [False, False],
            "Patient": ["patient1", "patient1"],
            "Genre": ["homme", "femme"],
            "status_type": ["success", "success"],
            "status_description": ["", ""],
        }
    )
    result = intra_comparison(df)
    assert all(result["status_type"] == "error")
    assert all("genre" in status for status in result["status_description"])


def test_intra_comparison_single_negative():
    df = pd.DataFrame(
        {
            "Sample Name": ["temoinnegatif"],
            "Allele 1": [np.nan],
            "Allele 2": [np.nan],
            "Allele 29": [np.nan],
            "Allele 30": [np.nan],
            "signature_len": [0],
            "signature": [""],
            "signature_hash": [""],
            "is_neg": [True],
            "Patient": ["temoinnegatif"],
            "Genre": ["indéterminé"],
            "status_type": ["success"],
            "status_description": [""],
        }
    )
    result = intra_comparison(df)
    assert all(result["status_type"] == "info")
    assert all("Contrôle négatif" in status for status in result["status_description"])


# ----------------------------
# Tests for inter_comparison function
# ----------------------------


def test_inter_comparison_conflict():
    df = pd.DataFrame(
        {
            "Patient": ["Patient_A", "Patient_B"],
            "signature": [("A", "T"), ("A", "T")],
            "signature_len": [2, 2],
            "signature_hash": ["hash1", "hash1"],
            "is_neg": [False, False],
            "Genre": ["homme", "homme"],
            "status_type": ["success", "success"],
            "status_description": ["", ""],
        }
    )
    result = inter_comparison(df)
    assert len(result) == 2


def test_inter_comparison_no_conflict():
    df = pd.DataFrame(
        {
            "Patient": ["Patient_A", "Patient_A"],
            "signature": [("A", "T"), ("A", "T")],
            "signature_len": [2, 2],
            "signature_hash": ["hash1", "hash1"],
            "is_neg": [False, False],
            "Genre": ["homme", "homme"],
            "status_type": ["success", "success"],
            "status_description": ["", ""],
        }
    )
    result = inter_comparison(df)
    assert result.empty


# ----------------------------
# Tests for samples heatmap
# ----------------------------


def test_sample_heatmap_percent_id():
    df = pd.DataFrame(
        {
            "Patient": ["A", "B"],
            "Sample Name": ["A_1", "B_1"],
            "Allele 1": ["A", "A"],
            "Allele 2": ["T", "G"],
            "Allele 29": ["X", "X"],
            "Allele 30": ["Y", ""],
            "Genre": ["homme", "femme"],
        }
    )
    heatmap = sample_heatmap(df)

    assert heatmap.shape == (2, 2)
    assert heatmap.loc["A_1", "A_1"] == 100.0
    assert heatmap.loc["A_1", "B_1"] < 100


def test_heatmap_sex_diff_only():
    df = pd.DataFrame(
        {
            "Patient": ["P1", "P2"],
            "Sample Name": ["P1_A", "P2_A"],
            "Allele 1": ["A", "A"],
            "Allele 2": ["T", "T"],
            "Allele 29": ["X", "X"],
            "Allele 30": ["Y", ""],  # sexe diff
            "Genre": ["homme", "femme"],
        }
    )
    heatmap = sample_heatmap(df)
    diff = heatmap.loc["P1_A", "P2_A"]
    assert diff < 100


# def test_should_find_negative_control_with_neg_keyword():
#     content = "Sample Name\tAllele 1\tAllele 2\nneg_sample\t\t\n"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 1
#     assert result.iloc[0]["comparison"] == "🧪 contrôle négatif"


# def test_should_find_negative_control_with_tem_keyword():
#     content = "Sample Name\tAllele 1\tAllele 2\ntem_sample\t\t\n"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 1
#     assert result.iloc[0]["comparison"] == "🧪 contrôle négatif"


# def test_should_not_find_negative_control_if_allele_is_present():
#     content = "Sample Name\tAllele 1\tAllele 2\ntem_sample\tT\t\n"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 1
#     assert result.iloc[0]["comparison"] == "ℹ️ échantillon unique"


# def test_should_find_identical_samples_with_bis_suffix():
#     content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1bis\tA\tT"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 1
#     assert all(result["comparison"] == "✅ identiques")


# def test_should_find_identical_samples_with_ter_suffix():
#     content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1ter\tA\tT"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 1
#     assert all(result["comparison"] == "✅ identiques")


# def test_should_find_identical_samples_with_bis_and_ter_suffixes():
#     content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1bis\tA\tT\nsample1ter\tA\tT"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 1
#     assert all(result["comparison"] == "✅ identiques")


# def test_should_find_unique_sample():
#     content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample2bis\tA\tT"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 2
#     assert all(result["comparison"] == "ℹ️ échantillon unique")


# def test_should_detect_samples_with_different_alleles():
#     content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1bis\tA\tC"
#     file = io.StringIO(content)
#     df = utils.load_genemapper_data(file)
#     result = utils.intra_comparison(df)
#     assert len(result) == 1
#     assert all(result["comparison"] == "❌ différents")


# def test_test():
#     path = files(resources).joinpath("genemapper_valid.txt")
#     df = utils.load_genemapper_data(path)
#     utils.intra_comparison(df)
