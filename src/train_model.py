import pandas as pd
import bentoml
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, root_mean_squared_error, r2_score

# 1. Charger les données traitées
X_train = pd.read_csv("data/processed/X_train.csv")
# y_train = pd.read_csv("data/processed/y_train.csv") est vue comme
# un dataframe (2D) et non pas comme une série.
# Le .values convertit le df comme un tableau numpy
# et le .ravel() le convertiten une liste de valeur donc comme une série
y_train = pd.read_csv("data/processed/y_train.csv").values.ravel()
X_test = pd.read_csv("data/processed/X_test.csv")
y_test = pd.read_csv("data/processed/y_test.csv").values.ravel()

# 2. Création et entraînement du modèle
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 3. Évaluation
y_pred = model.predict(X_test)
print(f"MSE: {mean_squared_error(y_test, y_pred):.4f}")
print(f"RMSE: {root_mean_squared_error(y_test, y_pred):.4f}")
print(f"R2 Score: {r2_score(y_test, y_pred):.4f}")

# 4. Sauvegarde dans BentoML Model Store
saved_model = bentoml.sklearn.save_model(
    "admission_regressor",
    model,
    signatures={"predict": {"batchable": False}}
)
print(f"Modèle sauvegardé : {saved_model}")
