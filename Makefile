.PHONY: serve token predict test-api

# Variables configurables
PORT ?= 3001
SERVICE ?= src.service:AdmissionClassifierService
BASE_URL ?= http://localhost:$(PORT)

# 1. Lancer le serveur BentoML
serve:
	uv run bentoml serve $(SERVICE) --port $(PORT)

# 2. Récupérer juste le token (Utile pour débugger)
# Note : On utilise jq pour extraire proprement la valeur JSON
token:
	@curl -s -X POST "$(BASE_URL)/login" \
		-H "Content-Type: application/json" \
                -d '{"credentials":{"username":"user123","password":"password123"}}' | jq -r '.token'

# 3. Faire une prédiction complète (Login + Predict)
# Warning: le -d '{"input_data": {"GRE Score": 320.0, ....} sur une seule ligne sinon ça bug. Makefile gère mal les \ dans  {}
predict:
	@echo "--- Récupération du Token ---"
	@token=$$(curl -s -X POST "$(BASE_URL)/login" \
		-H "Content-Type: application/json" \
                -d '{"credentials":{"username":"user123","password":"password123"}}' | jq -r '.token'); \
	echo "--- Envoi de la prédiction avec les données Admission ---"; \
	curl -s -X POST "$(BASE_URL)/predict" \
		-H "Content-Type: application/json" \
		-H "Authorization: Bearer $$token" \
		-d '{"input_data": {"GRE Score": 320.0, "TOEFL Score": 110.0, "University Rating": 3.0, "SOP": 4.0, "LOR": 4.0, "CGPA": 8.5, "Research": 1}}'; \
	echo ""

# 4. Alias pour lancer le test
test-api: predict
