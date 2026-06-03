# GLIMS Sample ID Parsing — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parser la colonne `Sample Name` pour gérer la nouvelle nomenclature GLIMS Genetics (`{glims_id:9}{tube_id:2}-{sample_id}`) en plus de la nomenclature legacy, de façon à regrouper les tubes d'un même patient et à détecter les contrôles négatifs.

**Architecture:** Un module de parsing dédié (`src/data/sample_name.py`) expose `parse_sample_name()` qui renvoie un `ParsedSampleName(patient_id, is_negative)`. `GeneticAnalyzer` l'utilise pour alimenter les colonnes `Patient` et `is_neg`. Pour GLIMS, `Patient = glims_id` (9 chiffres), ce qui satisfait par construction la contrainte « ne pas relier deux nomenclatures différentes ». Le reste de la chaîne (comparaison intra/inter) regroupe déjà sur `Patient` et reste inchangé.

**Tech Stack:** Python, pandas, pytest, ruff. Tests : `python -m pytest` (pythonpath=".").

**Spec:** `docs/superpowers/specs/2026-06-03-glims-sample-id-parsing-design.md`

---

## File Structure

- `src/utils/config.py` (modify) — constantes de nomenclature (regex GLIMS, regex suffixe legacy, suffixes négatifs).
- `src/data/sample_name.py` (create) — parsing de la nomenclature : `ParsedSampleName` + `parse_sample_name()`. Responsabilité unique : traduire un `Sample Name` brut en `(patient_id, is_negative)`.
- `src/data/genetics.py` (modify) — `GeneticAnalyzer` délègue au parser pour `is_negative_control()`, `Patient` et `is_neg`.
- `tests/test_sample_name.py` (create) — tests unitaires du parser.
- `tests/test_genetics.py` (modify) — tests d'intégration de `prepare_data` sur la nomenclature GLIMS.

---

## Task 1: Constantes de nomenclature dans config

**Files:**
- Modify: `src/utils/config.py`

- [ ] **Step 1: Ajouter les constantes**

Dans `src/utils/config.py`, remplacer le bloc actuel :

```python
# Keywords indicating a negative control
NEGATIVE_KEYWORDS = ["neg", "tem"]
```

par :

```python
# Keywords indicating a negative control (substring match, case-insensitive)
NEGATIVE_KEYWORDS = ["neg", "tem"]

# Suffixes indicating a negative control (suffix match, case-insensitive)
NEGATIVE_SUFFIXES = ["NE"]

# Sample name nomenclatures
# GLIMS Genetics: {glims_id:9}{tube_id:2}-{sample_id}
GLIMS_SAMPLE_PATTERN = r"^(?P<glims_id>\d{9})(?P<tube_id>\d{2})-(?P<sample_id>.+)$"
# Legacy: {sample_id}{tube_suffix:bis|ter?}
LEGACY_TUBE_SUFFIX_PATTERN = r"^(.*?)(bis|ter)$"
```

- [ ] **Step 2: Vérifier l'import**

Run: `python -c "from src.utils.config import NEGATIVE_SUFFIXES, GLIMS_SAMPLE_PATTERN, LEGACY_TUBE_SUFFIX_PATTERN; print(NEGATIVE_SUFFIXES, GLIMS_SAMPLE_PATTERN, LEGACY_TUBE_SUFFIX_PATTERN)"`
Expected: affiche `['NE'] ^(?P<glims_id>\d{9})(?P<tube_id>\d{2})-(?P<sample_id>.+)$ ^(.*?)(bis|ter)$`

- [ ] **Step 3: Commit**

```bash
git add src/utils/config.py
git commit -m "add sample name nomenclature constants to config"
```

---

## Task 2: Module de parsing `sample_name` (TDD)

**Files:**
- Create: `tests/test_sample_name.py`
- Create: `src/data/sample_name.py`

- [ ] **Step 1: Écrire les tests qui échouent**

Créer `tests/test_sample_name.py` :

```python
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


def test_parse_none_and_nan():
    """None et NaN sont tolérés et donnent un patient vide non négatif."""
    assert parse_sample_name(None) == ParsedSampleName("", False)
    assert parse_sample_name(float("nan")) == ParsedSampleName("", False)
```

- [ ] **Step 2: Lancer les tests pour vérifier l'échec**

Run: `python -m pytest tests/test_sample_name.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.data.sample_name'`

- [ ] **Step 3: Écrire l'implémentation minimale**

Créer `src/data/sample_name.py` :

```python
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
```

- [ ] **Step 4: Lancer les tests pour vérifier le succès**

Run: `python -m pytest tests/test_sample_name.py -q`
Expected: PASS (13 tests : 10 paramétrés + 3 fonctions)

- [ ] **Step 5: Lint**

Run: `ruff check src/data/sample_name.py tests/test_sample_name.py`
Expected: aucune erreur

- [ ] **Step 6: Commit**

```bash
git add src/data/sample_name.py tests/test_sample_name.py
git commit -m "add sample name parser for glims and legacy nomenclatures"
```

---

## Task 3: Intégration dans `GeneticAnalyzer` (TDD)

**Files:**
- Modify: `tests/test_genetics.py`
- Modify: `src/data/genetics.py`

- [ ] **Step 1: Ajouter les tests d'intégration qui échouent**

Ajouter à la fin de `tests/test_genetics.py` :

```python
def _glims_df(sample_names):
    """Construit un DataFrame minimal avec colonnes d'allèles vides."""
    data = {"Sample Name": list(sample_names)}
    for i in range(1, 35):
        data[f"Allele {i}"] = ["" for _ in sample_names]
    return pd.DataFrame(data)


def test_prepare_data_glims_groups_by_glims_id():
    """Deux tubes GLIMS d'un même patient ont le même Patient (glims_id)."""
    df = _glims_df(
        [
            "26011822905-26B279a",
            "26011822906-26B279a",
            "26011825506-26B280a",
        ]
    )
    prepared = GeneticAnalyzer(df).prepare_data()
    patients = prepared["Patient"].tolist()
    assert patients[0] == patients[1] == "260118229"
    assert patients[2] == "260118255"


def test_prepare_data_glims_negative_control():
    """Le suffixe NE marque un contrôle négatif au format GLIMS."""
    df = _glims_df(["26011715104-26C073aNE"])
    prepared = GeneticAnalyzer(df).prepare_data()
    assert bool(prepared.loc[0, "is_neg"]) is True


def test_prepare_data_does_not_mix_nomenclatures():
    """GLIMS et legacy d'apparence proche ne sont pas regroupés."""
    df = _glims_df(["26011822905-26B279a", "26B279abis"])
    prepared = GeneticAnalyzer(df).prepare_data()
    assert prepared.loc[0, "Patient"] != prepared.loc[1, "Patient"]
```

- [ ] **Step 2: Lancer les nouveaux tests pour vérifier l'échec**

Run: `python -m pytest tests/test_genetics.py -q -k "glims or mix"`
Expected: FAIL — `test_prepare_data_glims_groups_by_glims_id` échoue (le `Patient` actuel vaut le nom complet `26011822905-26B279a`, pas `260118229`).

- [ ] **Step 3: Brancher le parser dans `genetics.py`**

Dans `src/data/genetics.py`, ajouter l'import après les imports existants :

```python
from src.data.sample_name import parse_sample_name
```

Remplacer le corps de `is_negative_control` :

```python
    def is_negative_control(self, sample_name: str) -> bool:
        """Check if the sample is a negative control.

        Args:
            sample_name (str): Name of the sample to check.

        Returns:
            bool: True if the sample is a negative control, False otherwise.
        """
        if not sample_name:
            return False
        name = sample_name.lower()
        return any(k in name for k in NEGATIVE_KEYWORDS)
```

par :

```python
    def is_negative_control(self, sample_name: str) -> bool:
        """Check if the sample is a negative control.

        Args:
            sample_name (str): Name of the sample to check.

        Returns:
            bool: True if the sample is a negative control, False otherwise.
        """
        return parse_sample_name(sample_name).is_negative
```

Dans `prepare_data`, remplacer le bloc :

```python
        df["Patient"] = df["Sample Name"].str.replace(
            r"^(.*?)(bis|ter)$", r"\1", regex=True
        )
        df["is_neg"] = df["Sample Name"].apply(self.is_negative_control)
```

par :

```python
        parsed = df["Sample Name"].apply(parse_sample_name)
        df["Patient"] = parsed.apply(lambda p: p.patient_id)
        df["is_neg"] = parsed.apply(lambda p: p.is_negative)
```

- [ ] **Step 4: Nettoyer l'import devenu inutile**

`NEGATIVE_KEYWORDS` n'est plus référencé dans `genetics.py`. Retirer cette ligne du bloc d'import `from src.utils.config import (...)` :

```python
    NEGATIVE_KEYWORDS,
```

L'import final doit être :

```python
from src.utils.config import (
    ALLELE_PREFIX,
    GENDER_ALLELES_X,
    GENDER_ALLELES_Y,
)
```

- [ ] **Step 5: Lancer tout `test_genetics.py` pour vérifier le succès**

Run: `python -m pytest tests/test_genetics.py -q`
Expected: PASS (tous les tests, anciens et nouveaux)

- [ ] **Step 6: Lint**

Run: `ruff check src/data/genetics.py tests/test_genetics.py`
Expected: aucune erreur

- [ ] **Step 7: Commit**

```bash
git add src/data/genetics.py tests/test_genetics.py
git commit -m "use sample name parser for patient grouping and negative control"
```

---

## Task 4: Vérification de non-régression globale

**Files:** aucun (vérification seule)

- [ ] **Step 1: Lancer toute la suite de tests**

Run: `python -m pytest -q`
Expected: PASS — aucun test cassé (intégration, services, comparaison inclus).

- [ ] **Step 2: Lint global du périmètre modifié**

Run: `ruff check src/ tests/`
Expected: aucune erreur introduite par les changements.

---

## Notes de vérification

- La contrainte « ne pas relier deux nomenclatures » est couverte par
  `test_cross_nomenclature_not_same_patient` (unitaire) et
  `test_prepare_data_does_not_mix_nomenclatures` (intégration).
- Les contrôles négatifs GLIMS (suffixe `NE`) et legacy (`neg`/`tem`) sont
  couverts respectivement par les cas paramétrés et `test_prepare_data_glims_negative_control`.
- Le regroupement aval (`groupby("Patient")` dans `comparison.py` et
  `identity_vigilance.py`) n'est pas modifié : il bénéficie automatiquement du
  nouveau calcul de `Patient`.
```