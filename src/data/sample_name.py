"""Parsing des noms d'échantillons (Sample Name) du fichier Genemapper.

Deux nomenclatures coexistent :

- Legacy : ``{sample_id}{suffixe_tube:[bis,ter]?}`` (ex. ``24T781abis``)
- GLIMS Genetics : ``{glims_id:9}{tube_id:2}-{sample_id}``
  (ex. ``26011822905-26B279a``)

Le module expose :func:`parse_sample_name`, qui renvoie l'identifiant de
regroupement patient et le statut de contrôle négatif.
"""

import re
from dataclasses import dataclass

from src.utils.config import (
    GLIMS_SAMPLE_PATTERN,
    LEGACY_TUBE_SUFFIX_PATTERN,
    NEGATIVE_KEYWORDS,
    NEGATIVE_SUFFIXES,
)

_GLIMS_RE = re.compile(GLIMS_SAMPLE_PATTERN)
_LEGACY_RE = re.compile(LEGACY_TUBE_SUFFIX_PATTERN)


@dataclass(frozen=True)
class ParsedSampleName:
    """Résultat du parsing d'un nom d'échantillon.

    Attributes:
        patient_id (str): Identifiant de regroupement des tubes d'un même
            patient. ``glims_id`` pour la nomenclature GLIMS, ``sample_id``
            débarrassé du suffixe ``bis``/``ter`` pour la nomenclature legacy.
        is_negative (bool): True si l'échantillon est un contrôle négatif.
    """

    patient_id: str
    is_negative: bool


def _is_negative(text: str) -> bool:
    """Détermine si un identifiant correspond à un contrôle négatif.

    Args:
        text (str): Identifiant à tester (nom complet ou sample_id).

    Returns:
        bool: True si ``text`` (insensible à la casse) se termine par un suffixe
            de ``NEGATIVE_SUFFIXES`` ou contient un mot-clé de
            ``NEGATIVE_KEYWORDS``.
    """
    name = text.lower()
    if any(name.endswith(suffix.lower()) for suffix in NEGATIVE_SUFFIXES):
        return True
    return any(keyword.lower() in name for keyword in NEGATIVE_KEYWORDS)


def parse_sample_name(sample_name) -> ParsedSampleName:
    """Parse un nom d'échantillon en identifiant patient + statut négatif.

    Args:
        sample_name: Valeur brute de la colonne ``Sample Name`` (str ; les
            valeurs None/NaN sont tolérées).

    Returns:
        ParsedSampleName: patient_id et is_negative.
    """
    name = "" if sample_name is None else str(sample_name).strip()
    if not name or name.lower() == "nan":
        return ParsedSampleName(patient_id="", is_negative=False)

    glims_match = _GLIMS_RE.match(name)
    if glims_match:
        return ParsedSampleName(
            patient_id=glims_match.group("glims_id"),
            is_negative=_is_negative(glims_match.group("sample_id")),
        )

    patient_id = _LEGACY_RE.sub(r"\1", name)
    return ParsedSampleName(patient_id=patient_id, is_negative=_is_negative(name))
