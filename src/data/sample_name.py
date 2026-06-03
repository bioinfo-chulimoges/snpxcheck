"""Sample name parsing for the SNPXPlex Streamlit application.

Two nomenclatures coexist in the ``Sample Name`` column of the Genemapper file:

- Legacy: ``{sample_id}{tube_suffix:[bis,ter]?}`` (e.g. ``24T781abis``)
- GLIMS Genetics: ``{glims_id:9}{tube_id:2}-{sample_id}``
  (e.g. ``26011822905-26B279a``)

This module exposes :func:`parse_sample_name`, which returns the patient
grouping identifier and the negative-control status.
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
    """Result of parsing a sample name.

    Attributes:
        patient_id (str): Identifier used to group tubes of the same patient.
            The ``glims_id`` for the GLIMS nomenclature, the ``sample_id``
            stripped of its ``bis``/``ter`` suffix for the legacy nomenclature.
        is_negative (bool): True if the sample is a negative control.
    """

    patient_id: str
    is_negative: bool


def _is_negative(text: str) -> bool:
    """Check whether an identifier denotes a negative control.

    Args:
        text (str): Identifier to test (full name or sample_id).

    Returns:
        bool: True if ``text`` (case-insensitive) ends with a suffix from
            ``NEGATIVE_SUFFIXES`` or contains a keyword from
            ``NEGATIVE_KEYWORDS``.
    """
    name = text.lower()
    if any(name.endswith(suffix.lower()) for suffix in NEGATIVE_SUFFIXES):
        return True
    return any(keyword.lower() in name for keyword in NEGATIVE_KEYWORDS)


def parse_sample_name(sample_name: str | float | None) -> ParsedSampleName:
    """Parse a sample name into a patient identifier and negative status.

    Args:
        sample_name (str | float | None): Raw value from the ``Sample Name``
            column. None and NaN values are tolerated.

    Returns:
        ParsedSampleName: The patient_id and is_negative flag.
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
