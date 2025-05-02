# SNPXPlex Streamlit

Application web pour l'analyse génétique des données SNPXPlex.

## Description

SNPXPlex Streamlit est une application web qui permet d'analyser et de comparer des données génétiques issues de la plateforme SNPXPlex. Elle offre une interface intuitive pour :

- Charger et valider des fichiers Genemapper
- Effectuer des analyses intra et inter-patients
- Générer des visualisations (heatmaps)
- Produire des rapports PDF détaillés

## Installation

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. Clonez le dépôt :
   ```bash
   git clone https://gitlab.com/your-username/snpxplex_streamlit.git
   cd snpxplex_streamlit
   ```

2. Créez un environnement virtuel :
   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # ou
   .\venv\Scripts\activate  # Sur Windows
   ```

3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

4. Installez l'application :
   ```bash
   pip install -e .
   ```

## Utilisation

Pour lancer l'application :
```bash
streamlit run src/app/main.py
```

## Documentation

La documentation complète est disponible dans le dossier `docs`. Pour la générer :

```bash
cd docs
make html
```

## Tests

Pour exécuter les tests :
```bash
pytest
```

Pour générer un rapport de couverture :
```bash
pytest --cov=src tests/
```

## Structure du projet

```
snpxplex_streamlit/
├── src/
│   ├── app/           # Application Streamlit
│   ├── data/          # Traitement des données
│   ├── services/      # Services métier
│   ├── utils/         # Utilitaires
│   ├── visualization/ # Visualisation
│   └── reporting/     # Génération de rapports
├── tests/             # Tests unitaires
├── docs/              # Documentation
├── requirements.txt   # Dépendances
└── setup.py          # Configuration du package
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Forker le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 