import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

# Configuration de Sphinx
project = "SNPXPlex Streamlit"
copyright = "2024, Paco"
author = "Paco"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
]

# Configuration des extensions
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

# Configuration du thème
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Configuration de la documentation
templates_path = ["_templates"]
exclude_patterns = []
language = "fr"

# Configuration de l'index
master_doc = "index"
