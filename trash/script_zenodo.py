import requests
import json
import os

# ==========================================
# CONFIGURATION
# ==========================================
ACCESS_TOKEN = "kvTr6bg5EpZQII1GkNPweSb9JvIYQja646wxvi91LNGCPmIduxVNQAR8KLlU"
API_BASE = "https://zenodo.org/api"

# Fichiers à uploader (chemins locaux)
FILES_TO_UPLOAD = [
    "Documents/fr/doc_unique_fr_22734768.pdf",
    "Documents/en/doc_unique_en_22734768.pdf",
    # Ajoutez ici votre ZIP de sources si nécessaire
]

# Métadonnées du record
METADATA = {
    "title": "The Economic Heavenly Way - Discrete Topology of Complex Systems and the Diplomacy of Regeneration",
    "upload_type": "publication",
    "publication_type": "report",
    "description": "This repository hosts a research report on 'The Economic Heavenly Way' (Tiandao Jingji). The report formalizes Thierry Rebour's Rent Extraction Theory using Clifford Algebra Cl(6,6)...",
    "creators": [
        {
            "name": "De Dominicis, Bruno",
            "affiliation": "Think Tank indépendant"
        }
    ],
    "keywords": [
        "clifford-algebra", "rent-extraction-theory", "chinese-economy", 
        "topology", "complex-systems", "discrete-topology", 
        "economic-modeling", "china", "territorial-regeneration-rent", 
        "tiandao-jingji"
    ],
    "license": "CC-BY-4.0",
    "access_right": "open",
    "language": "eng"  # ou "fra" pour la version française
}

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
}

# ==========================================
# ÉTAPE 1 : Lister et nettoyer les brouillons
# ==========================================
print("=== Recherche des brouillons ===")
r = requests.get(f"{API_BASE}/deposit/depositions", headers=headers)
depositions = r.json()

corrupted_draft_id = None
for dep in depositions:
    if dep.get("state") == "unsubmitted":
        # Vérifie si le titre correspond à votre projet
        title = dep.get("metadata", {}).get("title", "")
        if "Economic Heavenly Way" in title or "TianDao" in title:
            corrupted_draft_id = dep["id"]
            print(f"Brouillon trouvé : ID {corrupted_draft_id} - Titre : {title}")
            print(f"État : {dep.get('state')}")
            print(f"DOI réservé : {dep.get('metadata', {}).get('prereserve_doi', {}).get('doi', 'Aucun')}")
            break

if corrupted_draft_id:
    # Suppression du brouillon corrompu
    print(f"\n=== Suppression du brouillon {corrupted_draft_id} ===")
    del_response = requests.delete(
        f"{API_BASE}/deposit/depositions/{corrupted_draft_id}",
        headers=headers
    )
    if del_response.status_code == 204:
        print("Brouillon supprimé avec succès.")
    else:
        print(f"Erreur lors de la suppression : {del_response.status_code} - {del_response.text}")
else:
    print("Aucun brouillon correspondant trouvé.")

# ==========================================
# ÉTAPE 2 : Créer un nouveau brouillon et réserver un DOI
# ==========================================
print("\n=== Création d'un nouveau brouillon ===")
create_payload = {
    "metadata": {
        "title": METADATA["title"],
        "upload_type": METADATA["upload_type"],
        "prereserve_doi": True  # Important : réserve un DOI immédiatement
    }
}

r = requests.post(
    f"{API_BASE}/deposit/depositions",
    headers=headers,
    json=create_payload
)

if r.status_code != 201:
    print(f"Erreur lors de la création : {r.status_code} - {r.text}")
    exit(1)

deposition = r.json()
deposition_id = deposition["id"]
reserved_doi = deposition["metadata"]["prereserve_doi"]["doi"]
bucket_url = deposition["links"]["bucket"]

print(f"Nouveau brouillon créé : ID {deposition_id}")
print(f"DOI réservé : {reserved_doi}")
print(f"URL du bucket : {bucket_url}")

# ==========================================
# ÉTAPE 3 : Uploader les fichiers
# ==========================================
print("\n=== Upload des fichiers ===")
for file_path in FILES_TO_UPLOAD:
    if not os.path.exists(file_path):
        print(f"Fichier introuvable : {file_path}")
        continue
    
    filename = os.path.basename(file_path)
    print(f"Upload de {filename}...")
    
    with open(file_path, "rb") as f:
        r = requests.put(
            f"{bucket_url}/{filename}",
            data=f,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
    
    if r.status_code == 201:
        print(f"  ✓ {filename} uploadé.")
    else:
        print(f"  ✗ Erreur : {r.status_code} - {r.text}")

# ==========================================
# ÉTAPE 4 : Mettre à jour les métadonnées
# ==========================================
print("\n=== Mise à jour des métadonnées ===")
update_payload = {"metadata": METADATA}

r = requests.put(
    f"{API_BASE}/deposit/depositions/{deposition_id}",
    headers=headers,
    json=update_payload
)

if r.status_code == 200:
    print("Métadonnées mises à jour avec succès.")
else:
    print(f"Erreur : {r.status_code} - {r.text}")

# ==========================================
# ÉTAPE 5 : Publier le record
# ==========================================
print("\n=== Publication ===")
r = requests.post(
    f"{API_BASE}/deposit/depositions/{deposition_id}/actions/publish",
    headers=headers
)

if r.status_code == 202:
    published_record = r.json()
    final_doi = published_record["doi"]
    print(f"✓ Record publié avec succès !")
    print(f"DOI final : {final_doi}")
    print(f"URL : {published_record['links']['html']}")
else:
    print(f"Erreur lors de la publication : {r.status_code} - {r.text}")
