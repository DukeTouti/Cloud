"""
TP2 - Appels REST au LLM déployé sur Microsoft Foundry.

Utilisation :
    python llm.py ask "Explain cloud computing in three sentences."
    python llm.py memory      (reproduit les deux expériences de la partie X)
    python llm.py chat        (conversation interactive avec historique)

Variables d'environnement :
    FOUNDRY_ENDPOINT : URL complète se terminant par /chat/completions
    FOUNDRY_KEY      : clé du déploiement
    FOUNDRY_MODEL    : nom du déploiement (par défaut gpt-5-mini)
"""

import os
import sys

import requests

ENDPOINT = os.environ["FOUNDRY_ENDPOINT"]
KEY = os.environ["FOUNDRY_KEY"]
MODEL = os.environ.get("FOUNDRY_MODEL", "gpt-5-mini")


def call_llm(messages):
    """Envoie la liste complète des messages au modèle et renvoie le JSON de réponse."""
    headers = {
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "messages": messages,
        "model": MODEL,
        "max_completion_tokens": 4096,
        "reasoning_effort": "medium",
    }
    response = requests.post(ENDPOINT, headers=headers, json=body, timeout=120)
    if not response.ok:
        print(f"Erreur HTTP {response.status_code} : {response.text}")
        sys.exit(1)
    return response.json()


def answer_and_usage(data):
    """Extrait le texte généré et le nombre de tokens utilisés."""
    text = data["choices"][0]["message"]["content"]
    usage = data["usage"]
    return text, usage


def print_usage(usage):
    reasoning = usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0)
    print(
        f"[tokens] prompt = {usage['prompt_tokens']}, "
        f"completion = {usage['completion_tokens']} (dont raisonnement = {reasoning}), "
        f"total = {usage['total_tokens']}"
    )


def ask(question):
    """Partie IX : une seule question."""
    data = call_llm([{"role": "user", "content": question}])
    text, usage = answer_and_usage(data)
    print(f"Assistant : {text}")
    print_usage(usage)


def memory_demo():
    """Partie X : requêtes indépendantes, puis requête avec historique."""
    print("=== Expérience 1 : deux requêtes séparées ===")
    ask("My favorite programming language is Python. Remember this information.")
    print()
    ask("What is my favorite programming language?")

    print("\n=== Expérience 2 : historique envoyé dans une seule requête ===")
    history = [
        {"role": "user", "content": "My favorite programming language is Python."},
        {"role": "assistant", "content": "Understood."},
        {"role": "user", "content": "What is my favorite programming language?"},
    ]
    text, usage = answer_and_usage(call_llm(history))
    print(f"Assistant : {text}")
    print_usage(usage)


def chat():
    """Conversation interactive : c'est le programme qui maintient l'historique."""
    history = []
    print("Conversation avec le modèle (tape 'quit' pour arrêter).")
    while True:
        user_input = input("\nToi : ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue

        history.append({"role": "user", "content": user_input})
        text, usage = answer_and_usage(call_llm(history))
        history.append({"role": "assistant", "content": text})

        print(f"Assistant : {text}")
        # prompt_tokens augmente à chaque tour, car tout l'historique est renvoyé
        print_usage(usage)


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "ask":
        ask(" ".join(sys.argv[2:]))
    elif len(sys.argv) == 2 and sys.argv[1] == "memory":
        memory_demo()
    elif len(sys.argv) == 2 and sys.argv[1] == "chat":
        chat()
    else:
        print('Usage : python llm.py [ask "question" | memory | chat]')
        sys.exit(1)