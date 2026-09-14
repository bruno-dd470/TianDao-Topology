import requests

ACCESS_TOKEN = "VOTRE_TOKEN_ICI"  # Remplacez par votre token
API_BASE = "https://zenodo.org/api"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

print("=== Test de connexion à l'API Zenodo ===")
r = requests.get(f"{API_BASE}/deposit/depositions", headers=headers)

print(f"Status code : {r.status_code}")
print(f"Content-Type : {r.headers.get('Content-Type')}")
print(f"\n--- Premiers 500 caractères de la réponse ---")
print(r.text[:500])
