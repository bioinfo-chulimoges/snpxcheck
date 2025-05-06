# SNPXCheck

Application web pour l'analyse génétique des données SNPXPlex.

## Description

SNPXCheck est une application web qui permet d'analyser et de comparer des données génétiques issues de la plateforme SNPXPlex. Elle offre une interface intuitive pour :

- Charger et valider des fichiers Genemapper
- Effectuer des analyses intra et inter-patients
- Produire un rapport PDF

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
   ```bash
   apt install -r packages.txt
   ```

4. Installez l'application :
   ```bash
   pip install -e .
   ```

## Utilisation

Pour lancer l'application :
```bash
streamlit run main.py
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

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 