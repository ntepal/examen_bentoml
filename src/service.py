import bentoml
import numpy as np
from bentoml.io import JSON, NumpyNdarray
from pydantic import BaseModel

# 1. Définition du schéma de données (Pydantic pour la validation)
class StudentData(BaseModel):
    GRE_Score: float
    TOEFL_Score: float
    University_Rating: float
    SOP: float
    LOR: float
    CGPA: float
    Research: int

# 2. Chargement direct (méthode de ta formation)
model = bentoml.sklearn.load_model("admission_regressor:latest")

# 3. Création du service
svc = bentoml.Service("admission_service")


# 2. Récupération du modèle depuis le Model Store
admission_runner = bentoml.sklearn.get("admission_regressor:latest").to_runner()

# 3. Création du service
svc = bentoml.Service("admission_service", runners=[admission_runner])

# --- ENDPOINT LOGIN (Sécurisation simple) ---
@svc.api(input=JSON(), output=JSON())
def login(credentials: dict):
    """
    Simule une authentification. 
    Renvoie un token fictif si l'utilisateur est 'admin'
    """
    username = credentials.get("username")
    password = credentials.get("password")

    if username == "admin" and password == "bentoml_2024":
        return {"status": "success", "token": "secret-token-123"}
    return {"status": "fail", "message": "Identifiants invalides"}

# --- ENDPOINT PREDICT ---
@svc.api(
    input=JSON(pydantic_model=StudentData), 
    output=JSON()
)
async def predict(input_data: StudentData, context: bentoml.Context):
    """
    Effectue la prédiction après vérification d'un header de sécurité
    """
    # Vérification du "Token" dans les headers (Sécurisation)
    headers = context.request.headers
    auth_token = headers.get("Authorization")

    if auth_token != "Bearer secret-token-123":
        context.response.status_code = 401
        return {"error": "Non autorisé. Veuillez vous connecter via /login"}

    # Préparation des données pour le modèle
    # On transforme l'objet Pydantic en array numpy 2D (1 ligne, X colonnes)
    data_array = np.array([list(input_data.dict().values())])

    # Inférence
    prediction = await admission_runner.predict.async_run(data_array)

    return {
        "chance_of_admit": float(prediction[0]),
        "message": "Prédiction réussie"
    }
