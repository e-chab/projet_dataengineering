import requests
import json

# Exemple d'ID produit IKEA avec avis (à adapter si besoin)
product_id = "40394118"

url = f"https://web-api.ikea.com/tugc/public/v5/reviews/fr/fr/{product_id}"
headers = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "x-client-id": "a1047798-0fc4-446e-9616-0afe3256d0d7",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
}
payload = {
    "filter": {"and": [], "not": []},
    "sort": [{"field": "submissionOn", "direction": "desc"}],
    "page": {"size": 20, "number": 1}
}

response = requests.post(url, headers=headers, data=json.dumps(payload))
print(f"Status code: {response.status_code}")
try:
    reviews = response.json()
    print(f"Nombre d'avis trouvés: {len(reviews)}")
    for review in reviews:
        print(f"Auteur: {review.get('reviewer', {}).get('displayName')}")
        print(f"Titre: {review.get('title')}")
        print(f"Texte: {review.get('text')}")
        print(f"Note: {review.get('primaryRating', {}).get('ratingValue')}")
        print("-")
except Exception as e:
    print("Erreur lors du décodage JSON:", e)
