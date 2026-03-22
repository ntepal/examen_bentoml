import requests

BASE_URL = "http://localhost:3000"

def test_login():
    payload = {"username": "admin", "password": "bentoml_2026"}
    response = requests.post(f"{BASE_URL}/login", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    return response.json()["token"]

def test_predict():
    # On récupère le token d'abord
    token = test_login()
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        "GRE_Score": 320,
        "TOEFL_Score": 110,
        "University_Rating": 3,
        "SOP": 4.0,
        "LOR": 4.0,
        "CGPA": 8.5,
        "Research": 1
    }

    response = requests.post(f"{BASE_URL}/predict", json=data, headers=headers)
    assert response.status_code == 200
    assert "chance_of_admit" in response.json()
