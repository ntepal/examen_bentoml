# Examen BentoML

# Pré-requis: uv installé et .venv activé

# Installer les dépendances :
uv pip install -r requirements.txt

# Importer le service
bentoml import ./admission_classifier_service.bento

# Lancer le service (à partir du fichier Makefile) sur le 1er terminal
make serve

# Lancer les tests unitaires (à partir du fichier Makefile) sur le 2ème terminal
make test

# Si l'outil make n'est pas installé
# Lancer le service
uv run bentoml serve src.service:AdmissionClassifierService --port 3001

# Lancer les tests unitaire (en mode verbose pour affichage clair)
uv run pytest tests/test_unitaire.py -v



# Informations précédemment fournis pour l'examen
Ce repertoire contient l'architecture basique afin de rendre l'évaluation pour l'examen BentoML.

Vous êtes libres d'ajouter d'autres dossiers ou fichiers si vous jugez utile de le faire.

Voici comment est construit le dossier de rendu de l'examen:

```bash       
├── examen_bentoml          
│   ├── data       
│   │   ├── processed      
│   │   └── raw           
│   ├── models      
│   ├── src       
│   └── README.md
```

Afin de pouvoir commencer le projet vous devez suivre les étapes suivantes:

- Forker le projet sur votre compte github

- Cloner le projet sur votre machine

- Récuperer le jeu de données à partir du lien suivant: [Lien de téléchargement]( https://datascientest.s3-eu-west-1.amazonaws.com/examen_bentoml/admissions.csv)


Bon travail!
