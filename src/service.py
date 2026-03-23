# service.py dans src
import numpy as np
import bentoml
from pydantic import BaseModel, Field, ConfigDict
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURATION SÉCURITÉ ---
# Clé secrête hardcodé pour l'évaluation
# Mais à mettre dans le .venv en production réelle
JWT_SECRET_KEY = "admission_secret_key_2026"
JWT_ALGORITHM = "HS256"

USERS = {
    "user123": "password123",
}

class Credentials(BaseModel):
    username: str
    password: str

# --- MODÈLE DE DONNÉES ---
class StudentData(BaseModel):
    # Pour pouvoir définir des noms de variables (pour le code)
    # plus fonctionnels et sans ambiguïté versus les noms d'origine
    model_config = ConfigDict(populate_by_name=True)

    # Nom Python (sans espace) : Type = Field(alias="Nom CSV exact")
    gre_score: float = Field(alias="GRE Score")
    toefl_score: float = Field(alias="TOEFL Score")
    univ_rating: float = Field(alias="University Rating")
    sop: float = Field(alias="SOP")
    lor: float = Field(alias="LOR")
    cgpa: float = Field(alias="CGPA")
    research: int = Field(alias="Research")

# --- UTILITAIRES JWT ---
def create_jwt_token(user_id: str) -> str:
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {"sub": user_id, "exp": expiration}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# --- MIDDLEWARE DE SÉCURITÉ ---
# Créer l'API sécurisée
class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # On protège l'accès à la prédiction
        if request.url.path.endswith("/predict"):
            # On extrait toute la ligne
            auth_header = request.headers.get("Authorization")

            # Cas 1 : Le header est totalement absent
            if not auth_header:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Missing Authorization header"}
                )
            # Cas 2 : Le header existe mais n'utilise pas le standard Bearer
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Invalid authentication scheme. Use 'Bearer <token>'"
                    }
                )

            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
                payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
                request.state.user = payload.get("sub")
            except jwt.ExpiredSignatureError:
                return JSONResponse(status_code=401, content={"detail": "Token has expired"})
            except jwt.InvalidTokenError:
                return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)

# --- SERVICES BENTOML ---
# Grâce au décorateur, lancement en passant par le service BentoML 1.4 orienté classes
@bentoml.service
class AdmissionModelService:
    """Service interne pour charger le modèle sauvegardé"""
    def __init__(self):
        # Le nom entre guillement = celui inclus dans saved_model du train_model.py
        self.model = bentoml.sklearn.load_model("admission_regressor:latest")

    # Pour la requête HTTP POST (via @bentoml.api qui génère des requêtes POST)
    # Vérifiable via curl -X POST.
    @bentoml.api
    def predict_array(self, features: list[float]) -> list[float]:
        # Conversion explicite en float pour éviter les erreurs de type
        x = np.array(features, dtype=float).reshape(1, -1)
        pred = self.model.predict(x)
        return pred.tolist()

@bentoml.service
class AdmissionClassifierService:
    """Service principal exposé via l'API"""
    model_service = bentoml.depends(AdmissionModelService)

    # Endpoint nommé login
    @bentoml.api(route="/login")
    def login(self, credentials: Credentials):
        if USERS.get(credentials.username) == credentials.password:
            token = create_jwt_token(credentials.username)
            return {"token": token}
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

    # Endpoint nommé predict
    @bentoml.api(route="/predict")
    def predict(self, input_data: StudentData):
        # Extraction des caractéristiques
        features = [
            input_data.gre_score,
            input_data.toefl_score,
            input_data.univ_rating,
            input_data.sop,
            input_data.lor,
            input_data.cgpa,
            input_data.research
        ]

        pred = self.model_service.predict_array(features)
        # Résultat de la prédiction de chance d'admission
        # d'un étudiant dans une université (d'où pred[0])
        # Retourne la prédiction pour la variable cible
        # 'Chance of Admit' convertie en float standard
        # pour la compatibilité JSON.
        return {
            "chance_of_admit": float(pred[0]),
            # Indicateur explicite de réussite pour faciliter
            # le traitement de la réponse par la suite
            "status": "success"
        }

# Appliquer le Middleware sur tout le service
AdmissionClassifierService.add_asgi_middleware(JWTAuthMiddleware)
