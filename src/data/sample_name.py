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


def _is_negative(text: str, *, check_suffix: bool) -> bool:
    """Check whether an identifier denotes a negative control.

    Args:
        text (str): Identifier to test (full name or sample_id).
        check_suffix (bool): Whether to also treat a ``NEGATIVE_SUFFIXES``
            suffix as negative. The ``NE`` suffix is specific to the GLIMS
            nomenclature, so it is only checked on the GLIMS sample_id; the
            legacy path relies on ``NEGATIVE_KEYWORDS`` alone.

    Returns:
        bool: True if ``text`` (case-insensitive) contains a keyword from
            ``NEGATIVE_KEYWORDS``, or — when ``check_suffix`` is True — ends
            with a suffix from ``NEGATIVE_SUFFIXES``.
    """
    name = text.lower()
    if check_suffix and any(name.endswith(s.lower()) for s in NEGATIVE_SUFFIXES):
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
        sample_id = glims_match.group("sample_id")
        return ParsedSampleName(
            patient_id=glims_match.group("glims_id"),
            is_negative=_is_negative(sample_id, check_suffix=True),
        )

    patient_id = _LEGACY_RE.sub(r"\1", name)
    return ParsedSampleName(
        patient_id=patient_id,
        is_negative=_is_negative(name, check_suffix=False),
    )
