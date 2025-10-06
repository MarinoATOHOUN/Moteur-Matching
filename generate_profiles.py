#!/usr/bin/env python3
"""
Script pour générer des profils fictifs basés sur la cartographie des métiers du numérique.
Génère au moins 5 profils par famille de métiers.
"""

import pandas as pd
import random
from typing import List, Dict

# Lire les fichiers existants
df_metiers = pd.read_csv("cartographie-metiers-numeriques.csv", sep=';')
df_profiles_existing = pd.read_csv("backend/profiles.csv")

# Obtenir le dernier ID
last_id = df_profiles_existing['id'].max()

# Données pour la génération de profils
DIPLOMES = [
    "Licence Informatique",
    "Master Data Science",
    "Master Informatique",
    "Diplôme d'ingénieur Logiciel",
    "Diplôme d'ingénieur Informatique",
    "PhD en Intelligence Artificielle",
    "MBA Management Digital",
    "Master Marketing Digital",
    "Licence Communication",
    "Master Design",
    "BTS Informatique",
    "DUT Réseaux et Télécommunications"
]

CERTIFICATIONS = [
    "AWS Certified Solutions Architect",
    "Microsoft Azure Administrator",
    "Google Data Engineer",
    "Scrum Master",
    "PMP",
    "CISSP",
    "CEH",
    "Google Analytics",
    "HubSpot Marketing",
    "Adobe Certified Expert",
    "Kubernetes Administrator",
    "Aucune"
]

SOFT_SKILLS = [
    "Leadership", "Communication", "Travail en équipe", "Créativité",
    "Résolution de problèmes", "Adaptabilité", "Esprit critique",
    "Gestion du temps", "Empathie", "Pensée analytique"
]

LANGUES = [
    ["Français", "Anglais"],
    ["Français", "Anglais", "Espagnol"],
    ["Français", "Anglais", "Allemand"],
    ["Anglais", "Espagnol"],
    ["Français", "Arabe"],
    ["Français"]
]

LOCALISATIONS = [
    "Paris, France",
    "Dakar, Sénégal",
    "Abidjan, Côte d'Ivoire",
    "Casablanca, Maroc",
    "Montréal, Canada",
    "Lyon, France",
    "Tunis, Tunisie",
    "Bruxelles, Belgique",
    "Genève, Suisse",
    "Bamako, Mali"
]

MOBILITES = ["Mobile", "Pas mobile", "Ouvert au télétravail"]
DISPONIBILITES = ["Immédiate", "Dans 1 mois", "Dans 3 mois"]

ENTREPRISES = [
    "TechCorp", "DataSolutions", "CloudInnovate", "DigitalFirst",
    "StartupHub", "InnovateLab", "TechVentures", "DataDriven",
    "CloudMasters", "DevFactory", "AgileTeam", "SmartTech"
]

# Compétences par famille de métiers
COMPETENCES_PAR_FAMILLE = {
    "Communication digitale, marketing et e-Commerce": {
        "hard_skills": [
            "Google Analytics", "SEO", "SEA", "Google Ads", "Facebook Ads",
            "Content Marketing", "Email Marketing", "WordPress", "Photoshop",
            "Illustrator", "InDesign", "Hootsuite", "Buffer", "Mailchimp",
            "HubSpot", "Salesforce", "HTML", "CSS", "JavaScript"
        ],
        "experiences": [
            "Community Manager", "Chargé de communication", "Responsable marketing",
            "Chef de projet digital", "Consultant SEO", "Traffic Manager"
        ]
    },
    "Sécurité, cloud, réseau": {
        "hard_skills": [
            "AWS", "Azure", "GCP", "Kubernetes", "Docker", "Linux",
            "Windows Server", "Cisco", "Firewall", "VPN", "SIEM",
            "Penetration Testing", "Wireshark", "Nmap", "Metasploit",
            "Python", "Bash", "PowerShell", "Terraform", "Ansible"
        ],
        "experiences": [
            "Administrateur système", "Ingénieur Cloud", "Analyste cybersécurité",
            "Architecte réseau", "Ingénieur DevOps", "Expert sécurité"
        ]
    },
    "Data / IA": {
        "hard_skills": [
            "Python", "R", "SQL", "NoSQL", "MongoDB", "PostgreSQL",
            "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "Numpy",
            "Spark", "Hadoop", "Tableau", "Power BI", "Jupyter",
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision"
        ],
        "experiences": [
            "Data Scientist", "Data Engineer", "Data Analyst",
            "ML Engineer", "AI Researcher", "Data Architect"
        ]
    },
    "Développement, test et Ops": {
        "hard_skills": [
            "Python", "Java", "JavaScript", "TypeScript", "C#", "PHP",
            "React", "Angular", "Vue.js", "Node.js", "Django", "Flask",
            "Spring Boot", "Docker", "Kubernetes", "Git", "Jenkins",
            "CI/CD", "Agile", "Scrum", "REST API", "GraphQL"
        ],
        "experiences": [
            "Développeur Full Stack", "Développeur Backend", "Développeur Frontend",
            "Ingénieur DevOps", "Architecte logiciel", "Tech Lead"
        ]
    },
    "Gestion / Pilotage / Stratégie": {
        "hard_skills": [
            "Agile", "Scrum", "Kanban", "Jira", "Confluence", "MS Project",
            "Trello", "Asana", "Slack", "Teams", "Zoom", "Excel",
            "PowerPoint", "Gestion de budget", "KPI", "Roadmap",
            "Stratégie digitale", "Transformation digitale"
        ],
        "experiences": [
            "Chef de projet", "Product Owner", "Scrum Master",
            "Directeur de projet", "Product Manager", "CTO"
        ]
    },
    "Interface / graphisme / design": {
        "hard_skills": [
            "Figma", "Adobe XD", "Sketch", "Photoshop", "Illustrator",
            "InDesign", "After Effects", "Premiere Pro", "Blender",
            "Unity", "Unreal Engine", "UI Design", "UX Design",
            "Prototyping", "Wireframing", "Design Thinking", "HTML", "CSS"
        ],
        "experiences": [
            "UX Designer", "UI Designer", "Webdesigner", "Motion Designer",
            "Game Designer", "Graphiste", "Directeur artistique"
        ]
    }
}

def generate_profile(famille: str, metier: str, poste: str, profile_id: int) -> Dict:
    """Génère un profil fictif réaliste pour un métier donné."""
    
    # Sélectionner les compétences appropriées
    competences = COMPETENCES_PAR_FAMILLE.get(famille, COMPETENCES_PAR_FAMILLE["Développement, test et Ops"])
    
    # Générer les données du profil
    exp_years = random.randint(1, 15)
    diplome = random.choice(DIPLOMES)
    certification = random.choice(CERTIFICATIONS)
    
    # Sélectionner 5-8 hard skills aléatoires
    hard_skills = random.sample(competences["hard_skills"], min(random.randint(5, 8), len(competences["hard_skills"])))
    
    # Sélectionner 3 soft skills
    soft_skills = random.sample(SOFT_SKILLS, 3)
    
    # Autres attributs
    langues = random.choice(LANGUES)
    localisation = random.choice(LOCALISATIONS)
    mobilite = random.choice(MOBILITES)
    disponibilite = random.choice(DISPONIBILITES)
    
    # Générer l'expérience professionnelle
    nb_experiences = min(exp_years // 2, 3)  # 1 expérience tous les 2 ans, max 3
    experiences_list = []
    
    for i in range(max(1, nb_experiences)):
        exp_poste = random.choice(competences["experiences"])
        entreprise = random.choice(ENTREPRISES)
        annee_debut = 2024 - exp_years + (i * 2)
        annee_fin = annee_debut + random.randint(1, 3)
        experiences_list.append(f"{exp_poste} chez {entreprise} ({annee_debut}-{annee_fin})")
    
    experiences = ". ".join(experiences_list)
    
    # Créer le texte complet
    full_text = (
        f"Expériences: {experiences}. "
        f"Diplômes: {diplome}. "
        f"Certifications: {certification}. "
        f"Compétences techniques: {', '.join(hard_skills)}. "
        f"Compétences comportementales: {', '.join(soft_skills)}. "
        f"Langues: {', '.join(langues)}. "
        f"Localisation: {localisation}. "
        f"Mobilité: {mobilite}. "
        f"Disponibilité: {disponibilite}. "
        f"Poste recherché: {poste}."
    )
    
    return {
        'id': profile_id,
        'exp_years': exp_years,
        'diplomes': diplome,
        'certifications': certification,
        'hard_skills': str(hard_skills),
        'soft_skills': str(soft_skills),
        'langues': str(langues),
        'localisation': localisation,
        'mobilite': mobilite,
        'disponibilite': disponibilite,
        'full_text': full_text
    }

def main():
    """Génère les profils et les ajoute au fichier CSV."""
    
    print("🚀 Génération de profils fictifs...")
    print(f"📊 Nombre de métiers dans la cartographie: {len(df_metiers)}")
    print(f"📋 ID de départ: {last_id + 1}")
    
    # Grouper par famille
    familles = df_metiers.groupby('Famille')
    
    new_profiles = []
    current_id = last_id + 1
    
    # Calculer combien de profils générer pour atteindre 300
    target_total = 300
    current_total = len(df_profiles_existing)
    profiles_needed = target_total - current_total
    
    # Répartir équitablement entre les familles
    nb_familles = len(familles)
    profiles_per_famille = profiles_needed // nb_familles
    
    print(f"\n🎯 Objectif: {target_total} profils")
    print(f"📊 Profils existants: {current_total}")
    print(f"🆕 Profils à générer: {profiles_needed}")
    print(f"📁 Profils par famille: ~{profiles_per_famille}")
    
    for famille_name, groupe in familles:
        print(f"\n📁 Famille: {famille_name}")
        print(f"   Nombre de métiers: {len(groupe)}")
        
        # Générer le nombre calculé de profils par famille
        nb_profiles_to_generate = profiles_per_famille
        
        for i in range(nb_profiles_to_generate):
            # Sélectionner un métier aléatoire dans la famille
            metier_row = groupe.sample(1).iloc[0]
            
            profile = generate_profile(
                famille=famille_name,
                metier=metier_row['Metiers'],
                poste=metier_row['Poste'],
                profile_id=current_id
            )
            
            new_profiles.append(profile)
            current_id += 1
        
        print(f"   ✅ {nb_profiles_to_generate} profils générés")
    
    # Créer un DataFrame avec les nouveaux profils
    df_new_profiles = pd.DataFrame(new_profiles)
    
    # Combiner avec les profils existants
    df_all_profiles = pd.concat([df_profiles_existing, df_new_profiles], ignore_index=True)
    
    # Sauvegarder
    df_all_profiles.to_csv("backend/profiles.csv", index=False)
    
    print(f"\n✅ Génération terminée!")
    print(f"📊 Nombre total de profils: {len(df_all_profiles)}")
    print(f"🆕 Nouveaux profils ajoutés: {len(new_profiles)}")
    print(f"💾 Fichier sauvegardé: backend/profiles.csv")
    
    # Afficher quelques statistiques
    print(f"\n📈 Statistiques:")
    print(f"   - Profils par localisation:")
    for loc, count in df_all_profiles['localisation'].value_counts().head(5).items():
        print(f"     • {loc}: {count}")
    
    print(f"\n   - Distribution de l'expérience:")
    print(f"     • Junior (1-3 ans): {len(df_all_profiles[df_all_profiles['exp_years'] <= 3])}")
    print(f"     • Intermédiaire (4-7 ans): {len(df_all_profiles[(df_all_profiles['exp_years'] > 3) & (df_all_profiles['exp_years'] <= 7)])}")
    print(f"     • Senior (8+ ans): {len(df_all_profiles[df_all_profiles['exp_years'] > 7])}")

if __name__ == "__main__":
    main()
