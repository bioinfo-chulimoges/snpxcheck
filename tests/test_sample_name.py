import pytest

from src.data.sample_name import ParsedSampleName, parse_sample_name


@pytest.mark.parametrize(
    ("sample_name", "expected_patient", "expected_negative"),
    [
        # GLIMS : glims_id (9 premiers chiffres) comme identifiant patient
        ("26011822905-26B279a", "260118229", False),
        ("26011827406-23B282b", "260118274", False),
        # GLIMS : contrôle négatif via suffixe NE
        ("26011715104-26C073aNE", "260117151", True),
        # GLIMS : suffixe NE insensible à la casse
        ("26011715104-26C073ane", "260117151", True),
        # Legacy : sample_id inchangé sans suffixe tube
        ("24T768a", "24T768a", False),
        # Legacy : suppression du suffixe bis/ter
        ("24T781abis", "24T781a", False),
        ("25T478ater", "25T478a", False),
        # Legacy : contrôle négatif via mots-clés neg/tem
        ("temoinnegatif", "temoinnegatif", True),
        ("NEG_CONTROL", "NEG_CONTROL", True),
        # Vide
        ("", "", False),
    ],
)
def test_parse_sample_name(sample_name, expected_patient, expected_negative):
    parsed = parse_sample_name(sample_name)
    assert parsed == ParsedSampleName(expected_patient, expected_negative)


def test_glims_two_tubes_same_patient():
    """Deux tubes GLIMS d'un même patient partagent le glims_id."""
    a = parse_sample_name("26011822905-26B279a")
    b = parse_sample_name("26011822906-26B279a")
    assert a.patient_id == b.patient_id == "260118229"


def test_cross_nomenclature_not_same_patient():
    """Un échantillon GLIMS et un échantillon legacy ne sont pas reliés."""
    glims = parse_sample_name("26011822905-26B279a")
    legacy = parse_sample_name("26B279abis")
    assert glims.patient_id != legacy.patient_id


def test_legacy_ne_suffix_is_not_negative():
    """Le suffixe NE est spécifique à GLIMS : un nom legacy finissant par 'ne'
    n'est pas un contrôle négatif."""
    parsed = parse_sample_name("24T768ane")
    assert parsed.patient_id == "24T768ane"
    assert parsed.is_negative is False


def test_parse_none_and_nan():
    """None et NaN sont tolérés et donnent un patient vide non négatif."""
    assert parse_sample_name(None) == ParsedSampleName("", False)
    assert parse_sample_name(float("nan")) == ParsedSampleName("", False)
