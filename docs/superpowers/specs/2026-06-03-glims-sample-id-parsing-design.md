# Conception — Parsing des noms d'échantillons (GLIMS Genetics + legacy)

Date : 2026-06-03
Branche : `feature/glims-sample-id`

## Contexte

L'application parse le fichier Genemapper et lit la colonne `Sample Name` pour
en déduire :

1. l'identifiant de **regroupement** des tubes d'un même patient (colonne
   `Patient`), utilisé pour la comparaison intra-patient ;
2. si l'échantillon est un **contrôle négatif** (colonne `is_neg`), pour lequel
   aucune donnée d'allèle ne doit apparaître.

### Nomenclature historique (legacy)

Format : `{sample_id}{suffixe_tube:[bis,ter]?}`

| Sample Name    | sample_id | suffixe tube |
|----------------|-----------|--------------|
| `24T768a`      | `24T768a` | —            |
| `24T781abis`   | `24T781a` | `bis`        |

Deux échantillons d'un même patient partagent le même `sample_id` après
suppression du suffixe (`25T478a` et `25T478abis` → patient `25T478a`).

Contrôle négatif : nom contenant `neg` ou `tem` (insensible à la casse).

### Nouvelle nomenclature (GLIMS Genetics)

Format : `{glims_id:\d{9}}{tube_id:\d{2}}-{sample_id}`

| Sample Name             | glims_id    | tube_id | sample_id   |
|-------------------------|-------------|---------|-------------|
| `26011822905-26B279a`   | `260118229` | `05`    | `26B279a`   |
| `26011827406-23B282b`   | `260118274` | `06`    | `23B282b`   |

Deux échantillons d'un même patient partagent le même **`glims_id`**
(`26011822905-26B279a` et `26011822906-26B279a` → patient `260118229`).

Contrôle négatif : `sample_id` se terminant par le suffixe `NE` (insensible à
la casse), ex. `26011715104-26C073aNE` ; ou nom contenant `neg`/`tem`.

### Contraintes

- Les deux nomenclatures **coexistent**. Le code doit fonctionner pour les deux.
- **Ne jamais relier deux tubes de nomenclatures différentes.** Exemple :
  `26011822905-26B279a` et `26B279abis` doivent être considérés comme provenant
  de patients différents.

## Décisions

- **Colonne `Patient` pour GLIMS** = `glims_id` (9 chiffres). Sert à la fois de
  clé de regroupement et de label patient. Le nom complet reste affiché dans la
  colonne `Sample Name`.
- **Détection de contrôle négatif** = le nom (ou le `sample_id` pour GLIMS) se
  termine par un suffixe de `NEGATIVE_SUFFIXES` (`NE`), **OU** contient un
  mot-clé de `NEGATIVE_KEYWORDS` (`neg`, `tem`). Toujours insensible à la casse.
- La contrainte « ne pas matcher les deux nomenclatures » est satisfaite **par
  construction** : un `glims_id` (`260118229`) ne peut pas être égal à un
  `sample_id` legacy (`26B279a`).

## Architecture

Approche retenue : **module de parsing dédié**. Le parsing de la nomenclature
est un concept métier distinct de l'analyse génétique (signatures, sexe) ; il
est isolé pour être testé exhaustivement et évoluer indépendamment.

### 1. `src/utils/config.py` — constantes de nomenclature

```python
NEGATIVE_KEYWORDS = ["neg", "tem"]   # sous-chaîne, insensible à la casse (existant)
NEGATIVE_SUFFIXES = ["NE"]           # suffixe, insensible à la casse (nouveau)

# GLIMS Genetics : {glims_id:9}{tube_id:2}-{sample_id}
GLIMS_SAMPLE_PATTERN = r"^(?P<glims_id>\d{9})(?P<tube_id>\d{2})-(?P<sample_id>.+)$"
# Legacy : {sample_id}{suffixe tube:bis|ter?}
LEGACY_TUBE_SUFFIX_PATTERN = r"^(.*?)(bis|ter)$"
```

### 2. `src/data/sample_name.py` (nouveau)

```python
@dataclass(frozen=True)
class ParsedSampleName:
    patient_id: str
    is_negative: bool

def parse_sample_name(sample_name) -> ParsedSampleName: ...
```

Logique de `parse_sample_name` :

- nom vide / `NaN` → `ParsedSampleName("", False)`
- **match `GLIMS_SAMPLE_PATTERN`** → `patient_id = glims_id` ;
  `is_negative` calculé sur le `sample_id`
- **sinon (legacy)** → `patient_id =` nom débarrassé du suffixe `bis`/`ter`
  (via `LEGACY_TUBE_SUFFIX_PATTERN`) ; `is_negative` calculé sur le nom complet

Helper interne `_is_negative(text)` :
`text` (en minuscules) se termine par un `NEGATIVE_SUFFIXES` **OU** contient un
`NEGATIVE_KEYWORDS`.

Interface : *entrée* = valeur brute de `Sample Name` (str, ou NaN/None toléré) ;
*sortie* = `ParsedSampleName`. *Dépend de* : les constantes de `config`.

### 3. `src/data/genetics.py`

- `is_negative_control(sample_name)` délègue à
  `parse_sample_name(sample_name).is_negative`. La méthode est conservée
  (utilisée par les tests et le code existant).
- Dans `prepare_data()`, la dérivation inline actuelle de `Patient` et le calcul
  séparé de `is_neg` sont remplacés par un parsing unique par ligne :

```python
parsed = df["Sample Name"].apply(parse_sample_name)
df["Patient"] = parsed.apply(lambda p: p.patient_id)
df["is_neg"]  = parsed.apply(lambda p: p.is_negative)
```

### 4. Aval — aucun changement

`comparison.py` et `services/identity_vigilance.py` regroupent déjà sur la
colonne `Patient` (`groupby("Patient")`) et lisent `is_neg`. Comme
`Patient = glims_id` pour GLIMS, le regroupement intra des deux tubes d'un même
patient fonctionne sans modifier ces fichiers.

## Tests (TDD : red-green-refactor)

### `tests/test_sample_name.py` (nouveau)

Table de cas sur `parse_sample_name` :

- GLIMS : `26011822905-26B279a` → `patient_id == "260118229"`, `is_negative is False`
- GLIMS deux tubes même patient : `...05-26B279a` et `...06-26B279a` → même `patient_id`
- GLIMS neg : `26011715104-26C073aNE` → `is_negative is True`
- GLIMS neg casse : `...-26C073ane` → `is_negative is True`
- Legacy : `24T768a` → `patient_id == "24T768a"` ; `24T781abis` → `"24T781a"`
- Legacy neg : `temoinnegatif` → `is_negative is True` (tem/neg)
- Cross-nomenclature : `26011822905-26B279a` (→ `260118229`) ≠ `26B279abis` (→ `26B279a`)
- Vide / `NaN` / `None` → `("", False)`

### `tests/test_genetics.py`

- `prepare_data` sur données GLIMS : deux tubes même `glims_id` → même `Patient`
- contrôle négatif GLIMS (`NE`) → `is_neg is True`
- non-regroupement GLIMS ↔ legacy : `Patient` distincts

Les tests existants de `test_genetics.py` (legacy, neg/tem) doivent continuer à
passer sans modification fonctionnelle.

## Hors périmètre (YAGNI)

- Pas d'extension des suffixes tube legacy au-delà de `bis`/`ter`.
- Pas de modification de la logique de comparaison intra/inter ni du rapport PDF.
- Pas de stockage du `tube_id` (non utilisé fonctionnellement).
