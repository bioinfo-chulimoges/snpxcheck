# Changelog

Tous les changements notables de ce projet seront documentés dans ce fichier.

## [Unreleased]

## Changed

- Remplacement de WeasyPrint par xhtml2pdf pour la génération du rapport PDF : plus
  aucune dépendance système, l'application se déploie sur Streamlit Community Cloud
  sans `packages.txt`

## Removed

- Fichier `packages.txt` et ses dépendances apt (Cairo, Pango, gdk-pixbuf)
- Dépendance `kaleido`, inutilisée

## [1.2.0] - 2026-06-03

## Added

- Prise en compte des nouveau identifiants patient basés sur l'id glims

## Fixed

- Amélioration du temps de calcul pour réaliser les comparaisons de génotypes

## [1.1.1] - 2026-03-03

## Fixed

- Mise à jour de la dépendance libgdk-pixbuf2.0-0 suite à la mise à jour de streamlit #12

## [1.1.0] - 2024-05-02

## Added
- Si le contrôle négatif ne contient aucun allèle, la phrase "Absence de contamination," est ajoutée en préfix du champ "Série conforme" du rapport pdf #8

## Fixed
- Prend en compte les reours à la ligne dans les commentaire du rapport #10
- Corrige les rules des jobs dans le pipeline CI/CD #6 #5
- L'application ne retraite pas le fichier à chaque modification des widgets #11

## Removed
- La heatmap n'apparait plus dans le rapport pdf #9

## [1.0.0] - 2024-05-02
### Added
- Version initiale
- Interface Streamlit
- Documentation Sphinx
- Pipeline CI/CD 
- LICENSE