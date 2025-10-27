
import requests
from bs4 import BeautifulSoup
import csv
import time
import re
import xml.etree.ElementTree as ET
from tqdm import tqdm
import os

# --- Configuration ---
SITEMAP_INDEX_URL = "https://www.malt.fr/sitemap.xml"
CSV_PATH = "backend/api/profiles.csv"
MAX_PROFILES = 1000
# Ajout d'un User-Agent pour simuler un navigateur et éviter un blocage HTTP 403
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_profile_urls():
    """
    Récupère les URLs des profils depuis les sitemaps de Malt.
    """
    print("Étape 1 : Récupération des URLs des profils depuis les sitemaps...")
    profile_urls = []
    
    # 1. Récupérer le sitemap principal
    response = requests.get(SITEMAP_INDEX_URL, headers=REQUEST_HEADERS)
    if response.status_code != 200:
        print(f"Erreur : Impossible de récupérer le sitemap principal. Statut : {response.status_code}")
        return []

    sitemap_index_root = ET.fromstring(response.content)
    
    # 2. Extraire les URLs des sitemaps de profils
    profile_sitemap_urls = [
        elem.text
        for elem in sitemap_index_root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        if 'profiles-fr_fr' in elem.text
    ]

    # 3. Parcourir chaque sitemap de profil pour extraire les URLs individuelles
    for sitemap_url in tqdm(profile_sitemap_urls, desc="Lecture des sitemaps"):
        response = requests.get(sitemap_url, headers=REQUEST_HEADERS)
        if response.status_code == 200:
            sitemap_root = ET.fromstring(response.content)
            urls = [
                elem.text
                for elem in sitemap_root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
            ]
            profile_urls.extend(urls)
        else:
            print(f"Avertissement : Impossible de lire le sitemap {sitemap_url}")
        
        if len(profile_urls) >= MAX_PROFILES:
            break
            
    print(f"Trouvé {len(profile_urls)} URLs de profils.")
    return profile_urls[:MAX_PROFILES]

def parse_profile(url):
    """
    Extrait les informations d'une seule page de profil Malt.
    """
    try:
        response = requests.get(url, headers=REQUEST_HEADERS)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, 'lxml')

        # --- Extraction des données ---
        # Le titre du profil
        poste_recherche = soup.find('h1').get_text(strip=True) if soup.find('h1') else ""

        # La localisation
        location_element = soup.find('div', class_='freelancer-header__freelancer-location')
        localisation = location_element.find('span').get_text(strip=True) if location_element else ""

        # Années d'expérience (recherche d'un élément spécifique)
        exp_years = 0
        experience_div = soup.find('div', string=re.compile(r"ans d'expérience"))
        if experience_div:
            # Tente d'extraire le nombre du texte (ex: "8-15 ans d'expérience")
            match = re.search(r'(\d+)', experience_div.get_text())
            if match:
                exp_years = int(match.group(1))

        # Compétences (hard_skills)
        skills_section = soup.find('div', id='skills')
        hard_skills = []
        if skills_section:
            hard_skills = [skill.get_text(strip=True) for skill in skills_section.find_all('a', class_='freelancer-skills__skill-item')]

        # Expériences professionnelles
        experiences_text = ""
        experience_section = soup.find('div', id='experiences')
        if experience_section:
            experiences_text = experience_section.get_text(separator=' ', strip=True)

        # Diplômes / Formation
        education_section = soup.find('div', id='educations')
        diplomes = education_section.get_text(separator=' ', strip=True) if education_section else ""

        # Création du champ full_text pour la recherche sémantique
        full_text = (
            f"Poste recherché: {poste_recherche}. "
            f"Localisation: {localisation}. "
            f"Compétences: {', '.join(hard_skills)}. "
            f"Expériences: {experiences_text}. "
            f"Formation: {diplomes}. "
        )

        return {
            "exp_years": exp_years,
            "diplomes": diplomes,
            "certifications": "",  # Non trouvé de manière fiable
            "hard_skills": str(hard_skills), # Sauvegardé comme une chaîne de liste
            "soft_skills": "", # Non trouvé
            "langues": "", # Non trouvé
            "localisation": localisation,
            "mobilite": "", # Non trouvé
            "disponibilite": "", # Non trouvé
            "full_text": full_text,
            "poste_recherche": poste_recherche
        }

    except Exception as e:
        print(f"Erreur lors de l'analyse de {url}: {e}")
        return None

def main():
    """
    Fonction principale du script.
    """
    profile_urls = get_profile_urls()
    
    if not profile_urls:
        print("Aucune URL à traiter. Arrêt du script.")
        return

    # Récupérer le dernier ID du fichier CSV pour continuer l'incrémentation
    last_id = 0
    if os.path.exists(CSV_PATH):
        try:
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                # Sauter l'en-tête
                next(reader, None) 
                # Lire les lignes et prendre le dernier ID
                all_rows = list(reader)
                if all_rows:
                    last_id = int(all_rows[-1][0])
        except (IOError, IndexError, ValueError) as e:
            print(f"Avertissement : n'a pas pu lire le dernier ID depuis {CSV_PATH}. Démarrage de l'ID à 0. Erreur: {e}")

    print(f"Démarrage de la collecte de {len(profile_urls)} profils. Les données seront ajoutées à {CSV_PATH}")
    print(f"L'ID de départ est {last_id + 1}.")

    # Ouvrir le fichier CSV en mode 'append'
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        # Définir les noms des colonnes
        fieldnames = ['id', 'exp_years', 'diplomes', 'certifications', 'hard_skills', 'soft_skills', 'langues', 'localisation', 'mobilite', 'disponibilite', 'full_text', 'poste_recherche']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        # Boucle sur les URLs avec une barre de progression
        for i, url in enumerate(tqdm(profile_urls, desc="Scraping des profils")):
            profile_data = parse_profile(url)
            
            if profile_data:
                # Ajouter l'ID et l'écrire dans le fichier
                profile_data['id'] = last_id + 1 + i
                writer.writerow(profile_data)

            # Pause pour être respectueux envers le serveur
            time.sleep(1.5) 

    print(f"\nTerminé ! {len(profile_urls)} profils ont été traités et ajoutés à {CSV_PATH}.")


if __name__ == "__main__":
    main()
