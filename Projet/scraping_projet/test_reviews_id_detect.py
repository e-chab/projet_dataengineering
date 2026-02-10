import requests
import re
import json
from bs4 import BeautifulSoup

# URL d'une page produit IKEA
product_page_url = "https://www.ikea.com/fr/fr/p/vattenkrasse-arrosoir-ivoire-couleur-or-40394118/"

# Récupère le HTML de la page
response = requests.get(product_page_url)
html = response.text

# Utilise BeautifulSoup pour parser le HTML
soup = BeautifulSoup(html, "html.parser")

# Méthode 1 : Extraire l'ID depuis l'URL
product_id_url = re.search(r"-(\d+)/?$", product_page_url)
product_id = product_id_url.group(1) if product_id_url else None
print(f"Product ID extrait de l'URL: {product_id}")

# Méthode 2 : Chercher l'ID dans le HTML (exemple: meta, data-product-id, etc.)
meta_id = soup.find("meta", {"property": "product:item_number"})
if meta_id:
    print(f"Product ID extrait du HTML (meta): {meta_id['content']}")
else:
    print("Aucun product ID trouvé dans le HTML (meta)")

# Test de la requête reviews si un ID a été trouvé
if product_id:
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
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    print(f"Status code: {resp.status_code}")
    try:
        reviews = resp.json()
        print(f"Nombre d'avis trouvés: {len(reviews)}")
        for review in reviews:
            print(f"Auteur: {review.get('reviewer', {}).get('displayName')}")
            print(f"Titre: {review.get('title')}")
            print(f"Texte: {review.get('text')}")
            print(f"Note: {review.get('primaryRating', {}).get('ratingValue')}")
            print("-")
    except Exception as e:
        print("Erreur lors du décodage JSON:", e)
else:
    print("Impossible de trouver un product_id pour la page.")
