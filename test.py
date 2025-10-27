import requests
import json

# Endpoint URL
url = "https://rinogeek-test-r.hf.space/match"

# List of requests to send (text as offer_text, structured as direct fields)
requests_list = [
    {"offer_text": "Je cherche un développeur Python spécialisé en fintech avec 3 ans d’expérience au Sénégal", "top_k": 7},
    {
        "Poste": "Data Scientist",
        "Compétences techniques": ["PyTorch", "TensorFlow", "Machine Learning"],
        "Expérience requise": "5 ans",
        "Localisation": "Montréal, Canada",
        "Type de contrat": "CDI",
        "Salaire": "80000",
        "top_k": 7
    },
    {"offer_text": "Besoin d'un Ingénieur DevOps mobile, disponible immédiatement, avec compétences en Docker et Kubernetes, basé à Dakar, Sénégal", "top_k": 7},
    {"offer_text": "Cherche un Expert SEO avec 4 ans d'expérience en marketing digital, parlant français et anglais, ouvert au télétravail depuis Abidjan", "top_k": 7},
    {"offer_text": "Je cherche un plombier qualifié avec 2 ans d'expérience à Casablanca", "top_k": 7},
    {
        "Poste": "Chief Data Officer",
        "Compétences techniques": ["Big Data", "Hadoop", "Spark", "Leadership data teams"],
        "Expérience requise": "10 ans",
        "Localisation": "Paris, France",
        "Type de contrat": "Freelance",
        "top_k": 7
    },
    {"offer_text": "Trouve-moi des talents en IA pour un projet innovant", "top_k": 7},
]

# Output file
output_file = "output.txt"

with open(output_file, "w", encoding="utf-8") as f:
    for i, body in enumerate(requests_list, start=1):
        try:
            response = requests.post(url, json=body)
            f.write(f"Request {i}:\n{json.dumps(body, indent=2, ensure_ascii=False)}\n\n")
            f.write(f"Response {i} (Status: {response.status_code}):\n{response.text}\n\n")
            f.write("-" * 80 + "\n\n")
        except Exception as e:
            f.write(f"Error for Request {i}: {str(e)}\n\n")
            f.write("-" * 80 + "\n\n")

print(f"All requests sent. Results saved to {output_file}.")
