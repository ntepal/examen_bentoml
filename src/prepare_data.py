import pandas as pd
from sklearn.model_selection import train_test_split
import os

# 1. Chargement
df = pd.read_csv("data/raw/admission.csv")

# 2. Nettoyage
# On retire 'Serial No.' car c'est juste un index
if 'Serial No.' in df.columns:
    df = df.drop(columns=['Serial No.'])

# On supprime toutes les lignes qui contiennent au moins un NaN
df = df.dropna()

# 3. Séparation Features (X) et Cible (y)
X = df.drop(columns=['Chance of Admit'])
y = df['Chance of Admit']

# 4. Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Sauvegarde
os.makedirs("data/processed", exist_ok=True)
X_train.to_csv("data/processed/X_train.csv", index=False)
X_test.to_csv("data/processed/X_test.csv", index=False)
y_train.to_csv("data/processed/y_train.csv", index=False)
y_test.to_csv("data/processed/y_test.csv", index=False)

print("Données préparées et sauvegardées dans data/processed/")
