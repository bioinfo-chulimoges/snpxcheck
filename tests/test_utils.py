import io
import pytest
import tests.resources
import utils
from importlib.resources import files


from . import resources


def test_valid_file():
    content = "SNP1\tSNP2\nAA\tTT\nGG\tCC"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    assert not df.empty
    assert df.shape == (2, 2)


def test_empty_file():
    file = io.StringIO("")
    with pytest.raises(RuntimeError):
        utils.load_genemapper_data(file)


def test_should_find_negative_control_with_neg_keyword():
    content = "Sample Name\tAllele 1\tAllele 2\nneg_sample\t\t\n"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 1
    assert result.iloc[0]["comparison"] == "🧪 contrôle négatif"


def test_should_find_negative_control_with_tem_keyword():
    content = "Sample Name\tAllele 1\tAllele 2\ntem_sample\t\t\n"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 1
    assert result.iloc[0]["comparison"] == "🧪 contrôle négatif"


def test_should_not_find_negative_control_if_allele_is_present():
    content = "Sample Name\tAllele 1\tAllele 2\ntem_sample\tT\t\n"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 1
    assert result.iloc[0]["comparison"] == "ℹ️ échantillon unique"


def test_should_find_identical_samples_with_bis_suffix():
    content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1bis\tA\tT"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 1
    assert all(result["comparison"] == "✅ identiques")


def test_should_find_identical_samples_with_ter_suffix():
    content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1ter\tA\tT"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 1
    assert all(result["comparison"] == "✅ identiques")


def test_should_find_identical_samples_with_bis_and_ter_suffixes():
    content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1bis\tA\tT\nsample1ter\tA\tT"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 1
    assert all(result["comparison"] == "✅ identiques")


def test_should_find_unique_sample():
    content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample2bis\tA\tT"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 2
    assert all(result["comparison"] == "ℹ️ échantillon unique")


def test_should_detect_samples_with_different_alleles():
    content = "Sample Name\tAllele 1\tAllele 2\nsample1\tA\tT\nsample1bis\tA\tC"
    file = io.StringIO(content)
    df = utils.load_genemapper_data(file)
    result = utils.intra_comparison(df)
    assert len(result) == 1
    assert all(result["comparison"] == "❌ différents")


# def test_test():
#     path = files(resources).joinpath("genemapper_valid.txt")
#     df = utils.load_genemapper_data(path)
#     utils.intra_comparison(df)
