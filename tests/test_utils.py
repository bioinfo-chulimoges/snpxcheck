import io
import pytest
import pandas as pd

from utils import (
    load_genemapper_data,
    determine_sex,
    compute_signature,
    compute_signature_hash,
    is_negative_control,
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
