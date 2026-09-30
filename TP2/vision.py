"""
TP2 - Appels REST à Azure AI Vision avec la bibliothèque requests.

Utilisation :
    python vision.py tags    "URL_SAS_IMAGE"
    python vision.py ocr     "URL_SAS_IMAGE"
    python vision.py caption "URL_SAS_IMAGE"

Les secrets ne sont jamais écrits dans le code : ils sont lus
depuis les variables d'environnement VISION_ENDPOINT et VISION_KEY.
"""

import os
import sys

import requests

ENDPOINT = os.environ["VISION_ENDPOINT"].rstrip("/")
KEY = os.environ["VISION_KEY"]

HEADERS = {
    "Ocp-Apim-Subscription-Key": KEY,
    "Content-Type": "application/json",
}


def post(url, params, image_url):
    """Envoie la requête POST et affiche le message d'erreur Azure en cas d'échec."""
    response = requests.post(
        url, headers=HEADERS, params=params, json={"url": image_url}, timeout=30
    )
    if not response.ok:
        print(f"Erreur HTTP {response.status_code} : {response.text}")
        sys.exit(1)
    return response.json()


def analyze_v4(image_url, features):
    """Image Analysis 4.0 (parties V et VI)."""
    url = f"{ENDPOINT}/computervision/imageanalysis:analyze"
    params = {"api-version": "2024-02-01", "features": features}
    return post(url, params, image_url)


def analyze_v32(image_url):
    """Image Analysis 3.2 : caption disponible dans toutes les régions (partie VII)."""
    url = f"{ENDPOINT}/vision/v3.2/analyze"
    params = {"visualFeatures": "Tags,Description"}
    return post(url, params, image_url)


def show_tags(image_url):
    data = analyze_v4(image_url, "tags")
    print("Tags détectés :")
    for tag in data["tagsResult"]["values"]:
        print(f"  - {tag['name']:<12} confiance = {tag['confidence']:.3f}")


def show_ocr(image_url):
    data = analyze_v4(image_url, "read")
    print("Texte détecté :")
    for block in data["readResult"]["blocks"]:
        for line in block["lines"]:
            points = [(p["x"], p["y"]) for p in line["boundingPolygon"]]
            print(f"  - \"{line['text']}\"  position = {points}")


def show_caption(image_url):
    data = analyze_v32(image_url)
    print("Tags détectés :")
    for tag in data["tags"]:
        print(f"  - {tag['name']:<12} confiance = {tag['confidence']:.3f}")
    print("Caption :")
    for caption in data["description"]["captions"]:
        print(f"  \"{caption['text']}\"  confiance = {caption['confidence']:.3f}")


if __name__ == "__main__":
    actions = {"tags": show_tags, "ocr": show_ocr, "caption": show_caption}

    if len(sys.argv) != 3 or sys.argv[1] not in actions:
        print('Usage : python vision.py [tags|ocr|caption] "URL_SAS_IMAGE"')
        sys.exit(1)

    actions[sys.argv[1]](sys.argv[2])