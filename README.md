# SNPXPlex Streamlit

Application Streamlit pour l'analyse et la visualisation des données SNPXPlex.

## Structure du projet

```
snpxplex_streamlit/
├── app/                    # Application Streamlit
│   ├── main.py            # Point d'entrée de l'application
│   └── static/            # Fichiers statiques
├── src/                   # Code source
│   ├── services/          # Services métier
│   ├── data/             # Traitement des données
│   ├── visualization/    # Visualisation des données
│   ├── reporting/        # Génération de rapports
│   └── utils/            # Utilitaires et constantes
└── tests/                # Tests unitaires
```

## Installation

1. Cloner le dépôt :
```bash
git clone [URL_DU_REPO]
cd snpxplex_streamlit
```

2. Créer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# ou
venv\Scripts\activate     # Sur Windows
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

Lancer l'application :
```bash
streamlit run app/main.py
```

## Fonctionnalités

- Chargement et validation de fichiers GeneMapper
- Analyse intra et inter-patients
- Visualisation des résultats via heatmap
- Génération de rapports PDF

## Développement

Pour contribuer au projet :

1. Créer une branche pour votre fonctionnalité
2. Implémenter les changements
3. Ajouter des tests si nécessaire
4. Soumettre une pull request

## Tests

Lancer les tests :
```bash
pytest
``` 