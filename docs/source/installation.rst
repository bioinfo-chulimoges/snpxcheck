Installation
============

Prérequis
---------

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

Installation
------------

1. Clonez le dépôt :

.. code-block:: bash

   git clone https://gitlab.com/UFBioinformatique_CHULimoges/snpxcheck.git
   cd snpxcheck

2. Créez un environnement virtuel :

.. code-block:: bash

   python -m venv venv
   source venv/bin/activate  # Sur Linux/Mac
   # ou
   .\venv\Scripts\activate  # Sur Windows

3. Installez les dépendances :

.. code-block:: bash

   pip install -r requirements.txt
   apt install -r packages.txt

4. Installez l'application :

.. code-block:: bash

   pip install -e .

Lancement
---------

Pour lancer l'application :

.. code-block:: bash

   streamlit run main.py 