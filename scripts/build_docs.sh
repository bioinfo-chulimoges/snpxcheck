#!/bin/bash

# Créer un environnement virtuel si nécessaire
if [ ! -d "venv" ]; then
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    pip install sphinx sphinx-rtd-theme
else
    source venv/bin/activate
fi

# Déterminer la version
if [ -n "$1" ]; then
    VERSION=$1
else
    VERSION="latest"
fi

# Construire la documentation
cd docs
VERSION=$VERSION sphinx-build -b html -D version=$VERSION -D release=$VERSION source build

# Créer le dossier public si nécessaire
mkdir -p public

# Copier la documentation dans le dossier approprié
if [ "$VERSION" != "latest" ]; then
    mkdir -p public/$VERSION
    cp -r build/* public/$VERSION/
fi

# Copier la documentation dans le dossier latest
mkdir -p public/latest
cp -r build/* public/latest/

# Copier uniquement le fichier index.html de la page d'accueil dans le dossier public racine
cp source/_static/index.html public/

# Générer le fichier versions.json
echo "{\"versions\": [\"latest\", \"$VERSION\"]}" > public/versions.json

echo "Documentation built successfully!"
echo "You can view it by opening docs/public/index.html in your browser" 