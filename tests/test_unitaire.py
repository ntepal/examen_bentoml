import requests
import pytest
import jwt
from datetime import datetime, timedelta, timezone

# CONFIGURATION
# Dans le Makefile
PORT = 3001
BASE_URL = f"http://localhost:{PORT}"

# Dans le src/service.py
JWT_SECRET_KEY = "AvoidInsecureKeyLengthWarning_WithHMAC_HigherThan32bytes"
JWT_ALGORITHM = "HS256"
# Identifiants de test
VALID_CREDENTIALS = {"credentials": {"username": "user123", "password": "password123"}}
INVALID_CREDENTIALS = {"credentials": {"username": "hacker", "password": "wrong"}}

# Données de prédiction (dans test/test_api.py)
VALID_INPUT = {
    "input_data": {
        "gre_score": 320, "toefl_score": 110, "univ_rating": 3,
        "sop": 4.0, "lor": 4.0, "cgpa": 8.5, "research": 1
    }
}

########################################################################################
# NB: Tous les request passent par le middleware JWTAuthMiddleware grâce à la cmd
# AdmissionClassifierService.add_asgi_middleware(JWTAuthMiddleware)
# Mais seuls ceux pour "{BASE_URL}/predict" sont traités
########################################################################################

### --- 1. TEST DE L'API DE CONNEXION ---

def test_login_success():
    """Vérifiez que l'API renvoie un jeton JWT pour des identifiants corrects"""
    # "{BASE_URL}/login" retourne le dico key/value "token"/ valeur token
    # pour l'authentification avec cas OK ici (src/service.py def login())
    response = requests.post(f"{BASE_URL}/login", json=VALID_CREDENTIALS)
    assert response.status_code == 200
    assert "token" in response.json()

def test_login_invalid_credentials():
    """Vérifiez que l'API renvoie une erreur 401 pour des identifiants incorrects"""
    # Si dans def login, le if est faux alors on a le return status_code 401
    response = requests.post(f"{BASE_URL}/login", json=INVALID_CREDENTIALS)
    assert response.status_code == 401

### --- 2. TEST DE L'AUTHENTIFICATION JWT ---

def test_auth_missing_token():
    """Vérifiez que l'authentification échoue si le jeton est manquant"""
    # On peut ne pas ajouter le headers vu qu'il est vide dans ce test
    # Mais on l'ajoute explicitement pour le test pour plus de clarté
    empty_headers = {}
    response = requests.post(
        f"{BASE_URL}/predict", json=VALID_INPUT, headers=empty_headers
    )
    assert response.status_code == 401

def test_auth_invalid_standard():
    """Vérifiez que l'authentification échoue si le jeton est invalide car
    il n'utilise pas le standard Bearer"""
    # On génère un token valide pour ne pas que l'erreur vienne du token lui-même
    user_id = VALID_CREDENTIALS["credentials"]["username"]
    token = jwt.encode({"sub": user_id}, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    # ERREUR VOLONTAIRE : On met juste le token, sans "Bearer " devant
    headers = {"Authorization": token}

    response = requests.post(f"{BASE_URL}/predict", json=VALID_INPUT, headers=headers)

    # On vérifie le code 401
    assert response.status_code == 401

    # On vérifie que le message d'erreur est bien celui du cas 2
    data = response.json()
    assert "Invalid authentication standard" in data["detail"]
    assert "Use 'Bearer <token>'" in data["detail"]

def test_auth_invalid_token():
    """Vérifiez que l'authentification échoue si le jeton est invalide"""
    headers = {"Authorization": "Bearer token_totalement_faux"}
    response = requests.post(
        f"{BASE_URL}/predict", json=VALID_INPUT, headers=headers
    )
    assert response.status_code == 401

def test_auth_expired_token():
    """Vérifiez que l'authentification échoue si le jeton a expiré"""
    # On crée un token qui a expiré il y a 1 heure
    # expiration = heure courante - 1h (donc expiré depuis 1h
    expiration = datetime.now(timezone.utc) - timedelta(hours=1)
    user_id = VALID_CREDENTIALS["credentials"]["username"]
    payload = {"sub": user_id, "exp": expiration}

    expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    headers = {"Authorization": f"Bearer {expired_token}"}

    response = requests.post(f"{BASE_URL}/predict", json=VALID_INPUT, headers=headers)
    assert response.status_code == 401

### --- 3. TEST DE L'API DE PRÉDICTION ---

def test_predict_returns_401_if_token_missing_or_invalid():
    """Vérifiez que l'API renvoie une erreur 401 si le jeton est manquant ou invalide"""
    # Cas jeton manquant (champs headers absent)
    r1 = requests.post(f"{BASE_URL}/predict", json=VALID_INPUT)
    # Cas jeton invalide
    headers_invalid_token_value = {"Authorization": "Bearer 000"}
    r2 = requests.post(
        f"{BASE_URL}/predict",
        json=VALID_INPUT,
        headers=headers_invalid_token_value
    )
    assert r1.status_code == 401
    assert r2.status_code == 401

def test_predict_success_with_valid_token():
    """Vérifiez que l'authentification réussit avec un jeton valide + Prédiction OK"""
    # Obtenir un token valide
    token = requests.post(f"{BASE_URL}/login", json=VALID_CREDENTIALS).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Prédire
    response = requests.post(f"{BASE_URL}/predict", json=VALID_INPUT, headers=headers)
    assert response.status_code == 200

    # --- LES ASSERTIONS COHÉRENTES ---
    # On analyse le contenu JSON
    data = response.json()

    # On vérifie que le status est bien "success" comme écrit dans le service
    assert data["status"] == "success"

    # On vérifie que la clé est bien "chance_of_admit"
    assert "chance_of_admit" in data

    # On vérifie que c'est bien un chiffre (float)
    assert isinstance(data["chance_of_admit"], float)

def test_predict_invalid_data():
    """Vérifiez que l'API renvoie une erreur pour des données d'entrée invalides"""
    token = requests.post(f"{BASE_URL}/login", json=VALID_CREDENTIALS).json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # On envoie une chaîne au lieu d'un float pour le score GRE
    invalid_input = {"input_data": {"gre_score": "PasUnChiffre"}}
    response = requests.post(f"{BASE_URL}/predict", json=invalid_input, headers=headers)

    # BentoML renvoie généralement 422 (Unprocessable Entity) pour les erreurs de type Pydantic
    assert response.status_code in [422, 400, 500]
