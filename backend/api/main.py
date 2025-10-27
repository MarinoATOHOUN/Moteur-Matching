
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from contextlib import asynccontextmanager
import logging
import numpy as np
import re
import ast # For safe evaluation of string-represented lists
from typing import List, Dict, Optional
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Modèles et Données ---
# Utiliser un dictionnaire pour stocker les modèles et données chargés
ml_models = {}

# --- Modèles Pydantic (définis avant les fonctions qui les utilisent) ---
class MatchExplanation(BaseModel):
    strengths: List[str]  # Points forts du candidat
    weaknesses: List[str]  # Points à améliorer / compétences manquantes
    skills_match_score: float  # Score de correspondance des compétences (0-1)
    experience_match_score: float  # Score de correspondance de l'expérience (0-1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code exécuté au démarrage de l'application
    logger.info("Chargement des modèles et des données...")
    try:
        # Résoudre les chemins relatifs par rapport à ce fichier
        logger.info("Étape 1 : Résolution des chemins de fichiers...")
        base_dir = Path(__file__).resolve().parent
        profiles_path = base_dir / "profiles.csv"
        # Fallback : si le fichier n'existe pas au même niveau, essayer ../profiles.csv (pour endpoint add_profile)
        if not profiles_path.exists():
            alt = base_dir.parent / "profiles.csv"
            if alt.exists():
                profiles_path = alt
        logger.info(f"Chemin des profils : {profiles_path}")

        logger.info("Étape 2 : Chargement du DataFrame des profils...")
        df_profiles = pd.read_csv(profiles_path)
        ml_models["profiles"] = df_profiles
        logger.info(f"{len(df_profiles)} profils chargés.")
        
        # Charger la cartographie des métiers du numérique
        try:
            logger.info("Étape 3 : Chargement de la cartographie des métiers...")
            carto_path = base_dir.parent / "data" / "cartographie-metiers-numeriques.csv"
            df_metiers = pd.read_csv(carto_path, sep=';')
            ml_models["metiers_digital"] = df_metiers
            logger.info(f"✅ Cartographie des métiers chargée : {len(df_metiers)} métiers.")
        except FileNotFoundError:
            logger.warning("⚠️ Fichier cartographie-metiers-numeriques.csv non trouvé. Fonctionnalité métiers désactivée.")
            ml_models["metiers_digital"] = pd.DataFrame()
        
        logger.info("Étape 4 : Chargement du modèle SentenceTransformer...")
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        ml_models["model"] = model
        logger.info("Modèle SentenceTransformer chargé.")
        
        logger.info("Étape 5 : Encodage des profils (full_text)...")
        profile_embeddings = model.encode(df_profiles["full_text"].tolist(), convert_to_numpy=True)
        d = profile_embeddings.shape[1]
        logger.info("Encodage des profils terminé.")
        
        logger.info("Étape 6 : Normalisation et création de l'index FAISS...")
        faiss.normalize_L2(profile_embeddings)
        
        index = faiss.IndexFlatIP(d)
        index.add(profile_embeddings)
        ml_models["faiss_index"] = index
        logger.info("Index FAISS créé.")
        
        # Créer des embeddings séparés pour les compétences et l'expérience
        logger.info("Étape 7 : Encodage des compétences (hard_skills)...")
        skills_embeddings = model.encode(df_profiles["hard_skills"].tolist(), convert_to_numpy=True)
        faiss.normalize_L2(skills_embeddings)
        ml_models["skills_embeddings"] = skills_embeddings
        logger.info("Encodage des compétences terminé.")
        
        logger.info(f"✅ Index FAISS construit avec {index.ntotal} profils.")
        logger.info("Application démarrée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors du chargement des modèles : {e}", exc_info=True)
        # Vous pourriez vouloir arrêter l'application si les modèles ne se chargent pas
        # raise HTTPException(status_code=500, detail="Impossible de charger les modèles de ML.")
    
    yield
    
    # Code exécuté à l'arrêt de l'application
    logger.info("Nettoyage et arrêt de l'application...")
    ml_models.clear()
    logger.info("Application arrêtée.")

def normalize_skills(skills_text: str) -> List[str]:
    """
    Normalise les compétences en appliquant une taxonomie simple.
    """
    # Dictionnaire de normalisation des compétences
    skills_mapping = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'reactjs': 'react',
        'vuejs': 'vue.js',
        'nodejs': 'node.js',
        'ml': 'machine learning',
        'ai': 'intelligence artificielle',
        'ia': 'intelligence artificielle',
        'dl': 'deep learning',
        'nlp': 'natural language processing',
        'cv': 'computer vision',
        'db': 'database',
        'sql': 'sql',
        'nosql': 'nosql',
        'aws': 'amazon web services',
        'gcp': 'google cloud platform',
        'k8s': 'kubernetes',
    }
    
    # Extraire les compétences (entre crochets ou séparées par virgules)
    skills = []
    if '[' in skills_text and ']' in skills_text:
        # Format liste Python
        skills_text = skills_text.strip('[]').replace("'", "").replace('"', '')
    
    raw_skills = [s.strip().lower() for s in skills_text.split(',')]
    
    # Normaliser chaque compétence
    for skill in raw_skills:
        normalized = skills_mapping.get(skill, skill)
        if normalized and normalized not in skills:
            skills.append(normalized)
    
    return skills

def extract_skills_from_text(text: str) -> List[str]:
    """
    Extrait les compétences techniques d'un texte libre.
    """
    # Liste de compétences techniques courantes
    common_skills = [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'react', 'angular', 'vue.js', 'node.js', 'django', 'flask', 'spring', 'express',
        'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'terraform', 'ansible',
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'scikit-learn',
        'git', 'ci/cd', 'jenkins', 'gitlab', 'github',
        'agile', 'scrum', 'devops', 'microservices', 'api', 'rest', 'graphql'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill)
    
    return found_skills

def calculate_weighted_score(skills_score: float, exp_score: float, 
                            skills_weight: float = 0.5, exp_weight: float = 0.5) -> float:
    """
    Calcule un score pondéré basé sur les compétences et l'expérience.
    Par défaut : 50% compétences + 50% expérience
    """
    return (skills_score * skills_weight) + (exp_score * exp_weight)

def generate_explanation(offer_text: str, profile_row: pd.Series, 
                        skills_score: float, exp_score: float) -> MatchExplanation:
    """
    Génère une explication détaillée du matching.
    """
    strengths = []
    weaknesses = []
    
    # Extract required skills from offer_text
    required_skills = extract_skills_from_text(offer_text)
    
    # Safely parse profile hard skills (which might be a string representation of a list)
    profile_hard_skills_str = profile_row["hard_skills"]
    try:
        profile_skills_list = ast.literal_eval(profile_hard_skills_str)
        if not isinstance(profile_skills_list, list):
            profile_skills_list = [s.strip() for s in profile_hard_skills_str.split(',')]
    except (ValueError, SyntaxError):
        profile_skills_list = [s.strip() for s in profile_hard_skills_str.split(',')]

    # Normalize profile skills for comparison
    profile_skills_normalized = []
    for skill_item in profile_skills_list:
        profile_skills_normalized.extend(normalize_skills(skill_item))
    profile_skills_normalized = list(set(profile_skills_normalized)) # Remove duplicates

    # Analyze skills
    matched_skills = []
    missing_skills = []

    for req_skill in required_skills:
        found = False
        for prof_skill in profile_skills_normalized:
            # Check for exact match or substring match (e.g., 'python' in 'python_django')
            if req_skill == prof_skill or req_skill in prof_skill or prof_skill in req_skill:
                matched_skills.append(req_skill)
                found = True
                break
        if not found:
            missing_skills.append(req_skill)

    if matched_skills:
        strengths.append(f"Maîtrise de : {', '.join(list(set(matched_skills))[:5])}") # Use set to avoid duplicates

    if missing_skills:
        weaknesses.append(f"Compétences à développer : {', '.join(list(set(missing_skills))[:3])}")
    
    # Analyser l'expérience
    exp_years = int(profile_row["exp_years"])
    if exp_years >= 10: # More specific thresholds for "solid" vs "good"
        strengths.append(f"Expérience très solide ({exp_years} ans)")
    elif exp_years >= 5:
        strengths.append(f"Expérience solide ({exp_years} ans)")
    elif exp_years >= 3:
        strengths.append(f"Bonne expérience ({exp_years} ans)")
    else:
        strengths.append(f"Profil junior ({exp_years} ans d'expérience)")
    
    # Analyze location, mobility, availability based on offer text
    offer_text_lower = offer_text.lower()
    profile_location_lower = profile_row['localisation'].lower()

    # Location
    loc_required_match = re.search(r"(?:à|au|basé à|depuis)\s+([A-Za-zÀ-ÖØ-öø-ÿ\s\-']{2,})", offer_text_lower, flags=re.IGNORECASE)
    if loc_required_match:
        loc_required_str = loc_required_match.group(1).strip()
        if ',' in loc_required_str:
            loc_required_str = loc_required_str.split(',')[0].strip() # Take first part if comma separated
        if loc_required_str in profile_location_lower:
            strengths.append(f"Localisation : {profile_row['localisation']}")
        else:
            weaknesses.append(f"Localisation différente de l'offre ({profile_row['localisation']})")
    elif "localisation" in offer_text_lower or "localisé" in offer_text_lower or "basé" in offer_text_lower:
        # If offer mentions location generally, and profile has one
        strengths.append(f"Localisation : {profile_row['localisation']}")

    # Mobility
    if "mobile" in offer_text_lower or "déplacement" in offer_text_lower:
        if profile_row.get("mobilite") == "Mobile":
            strengths.append("Ouvert à la mobilité")
        else:
            weaknesses.append("Mobilité non compatible avec l'offre")
    elif "télétravail" in offer_text_lower or "remote" in offer_text_lower:
        if profile_row.get("mobilite") == "Ouvert au télétravail":
            strengths.append("Ouvert au télétravail")
        else:
            weaknesses.append("Télétravail non compatible avec l'offre")
    
    # Availability
    if "immédiatement" in offer_text_lower or "disponible de suite" in offer_text_lower:
        if profile_row.get("disponibilite") == "Immédiate":
            strengths.append("Disponibilité immédiate")
        else:
            weaknesses.append(f"Disponibilité ({profile_row['disponibilite']}) non immédiate")
    
    # If no specific weaknesses found, but overall score is not perfect, add a general one
    if not weaknesses and (skills_score < 0.9 or exp_score < 0.9): # Threshold for "very good match"
        weaknesses.append("Quelques légers écarts de compétences ou d'expérience")
    
    # If few strengths, add a generic one if no specific strengths were found
    if not strengths:
        strengths.append("Profil correspondant aux critères généraux")
    
    return MatchExplanation(
        strengths=strengths[:5],  # Limiter à 5 points forts
        weaknesses=weaknesses[:3],  # Limiter à 3 points faibles
        skills_match_score=round(skills_score, 2),
        experience_match_score=round(exp_score, 2)
    )

def update_faiss_index(new_profile_text: str, new_skills_text: str):
    """
    Met à jour l'index FAISS avec un nouveau profil.
    """
    try:
        if "model" not in ml_models or "faiss_index" not in ml_models:
            logger.error("Modèle ou index FAISS non chargé")
            return False
            
        model = ml_models["model"]
        index = ml_models["faiss_index"]
        
        # Encoder le nouveau profil
        new_embedding = model.encode([new_profile_text], convert_to_numpy=True)
        faiss.normalize_L2(new_embedding)
        
        # Ajouter au modèle FAISS
        index.add(new_embedding)
        
        # Mettre à jour les embeddings de compétences
        new_skills_embedding = model.encode([new_skills_text], convert_to_numpy=True)
        faiss.normalize_L2(new_skills_embedding)
        
        if "skills_embeddings" in ml_models:
            ml_models["skills_embeddings"] = np.vstack([ml_models["skills_embeddings"], new_skills_embedding])
        
        logger.info("Nouveau profil ajouté à l'index FAISS")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'index FAISS : {e}")
        return False

app = FastAPI(lifespan=lifespan)

# --- Configuration CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise toutes les origines (à ajuster en production)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les en-têtes
)


# --- Modèles Pydantic (pour la validation des requêtes) ---
class MatchRequest(BaseModel):
    offer_text: str | None = None # Now optional
    top_k: int = 7

class ProfileResult(BaseModel):
    id: int
    score: float
    # On peut ajouter d'autres champs du profil si nécessaire
    exp_years: int
    hard_skills: str # Gardé comme string pour la simplicité
    localisation: str
    full_text: str
    explanation: Optional[MatchExplanation] = None  # Explications du matching

class MatchResponse(BaseModel):
    results: list[ProfileResult]

# --- Fonctions Métier ---
def match_offer_sync(offer_text: str, top_k: int = 7, with_explanation: bool = True):
    """
    Fonction de matching synchrone avec pondération (50% skills + 50% expérience).
    """
    
    if "model" not in ml_models or "faiss_index" not in ml_models or "profiles" not in ml_models:
        raise HTTPException(status_code=503, detail="Les modèles ne sont pas encore prêts. Veuillez réessayer dans quelques instants.")

    model = ml_models["model"]
    index = ml_models["faiss_index"]
    df_profiles = ml_models["profiles"]
    skills_embeddings = ml_models.get("skills_embeddings")
    
    # Get digital job titles for filtering (Suggestion 4)
    df_metiers = ml_models.get("metiers_digital")
    digital_job_titles = []
    if not df_metiers.empty:
        digital_job_titles = df_metiers["Poste"].astype(str).str.lower().unique().tolist()

    # Extraire les compétences et l'expérience de l'offre
    required_skills = extract_skills_from_text(offer_text)

    # Heuristiques simples pour détecter des exigences explicites dans l'offre
    def detect_requirements(text: str):
        txt = text.lower()
        # rôle / poste (exemples courants)
        # Tenter de détecter un intitulé de poste plus précis en utilisant la cartographie des métiers
        role = None
        if "metiers_digital" in ml_models and not ml_models["metiers_digital"].empty:
            try:
                jobs = ml_models["metiers_digital"]["Poste"].astype(str).str.lower().unique().tolist()
                for j in jobs:
                    if j in txt:
                        role = j
                        break
            except Exception:
                role = None

        # Si la cartographie n'a rien trouvé, fallback sur des mots-clés simples
        if not role:
            role_keywords = ['dev', 'développeur', 'developer', 'web', 'frontend', 'backend', 'full stack', 'fullstack', 'data', 'engineer']
            for r in role_keywords:
                if r in txt:
                    role = r
                    break

        # localisation (heuristique : chercher "à <ville>" ou "@ <ville>")
        loc = None
        m = re.search(r"\bà\s+([A-Za-zÀ-ÖØ-öø-ÿ\-']{2,})", text, flags=re.IGNORECASE)
        if m:
            loc = m.group(1).strip().lower()

        # diplôme demandé (master, licence, phd, ingénieur...)
        degree_keywords = ['master', 'licence', 'phd', 'doctorat', 'diplôme', 'ingénieur', "d'ingénieur"]
        degree = None
        for d in degree_keywords:
            if d in txt:
                degree = d
                break

        return {
            'role': role,
            'location': loc,
            'degree': degree,
            'required_skills': required_skills
        }

    reqs = detect_requirements(offer_text)

    def profile_matches_requirements(row: pd.Series, reqs: dict) -> bool:
        """Retourne True si le profil satisfait (heuristiquement) les exigences détectées dans l'offre."""
        txt = str(row.get('full_text', '')).lower()
        # role: accepter une correspondance si le titre du profil ou le champ 'poste_recherche' contient la valeur
        if reqs['role']:
            profile_title = str(row.get('poste_recherche', '')).lower()
            if reqs['role'] not in txt and reqs['role'] not in profile_title:
                return False
        # location
        if reqs['location']:
            loc_field = str(row.get('localisation', '')).lower()
            if reqs['location'] not in loc_field and reqs['location'] not in txt:
                return False
        # degree
        if reqs['degree']:
            dipl = str(row.get('diplomes', '')).lower()
            if reqs['degree'] not in dipl and reqs['degree'] not in txt:
                return False
        # skills: si l'offre demande des skills explicites, vérifier qu'au moins un est présent
        if reqs.get('required_skills'):
            skills_ok = False
            for s in reqs['required_skills']:
                if s in txt:
                    skills_ok = True
                    break
            if reqs['required_skills'] and not skills_ok:
                return False

        return True

    
    # Extraire l'expérience requise (recherche de patterns comme "3 ans", "5 années")
    exp_pattern = re.search(r'(\d+)\s*(ans?|années?|years?)', offer_text.lower())
    required_exp = int(exp_pattern.group(1)) if exp_pattern else None  # None si pas précisé
    
    # Encoder l'offre complète pour le matching global
    offer_emb = model.encode([offer_text], convert_to_numpy=True)
    faiss.normalize_L2(offer_emb)
    
    # Encoder les compétences de l'offre
    skills_text = ", ".join(required_skills) if required_skills else offer_text
    offer_skills_emb = model.encode([skills_text], convert_to_numpy=True)
    faiss.normalize_L2(offer_skills_emb)
    
    # Recherche FAISS élargie pour avoir plus de candidats à scorer
    search_k = min(top_k * 5, len(df_profiles))  # Chercher plus large pool (5x top_k)
    distances, indices = index.search(offer_emb, search_k)

    logger.info(f"match_offer_sync: Initial FAISS search found {len(indices[0])} candidates.")

    # Extract specific requirements from offer_text for post-filtering (Suggestion 3)
    offer_text_lower = offer_text.lower()
    
    loc_required = None
    loc_match_patterns = [
        r"(?:à|au|basé à|depuis)\s+([A-Za-zÀ-ÖØ-öø-ÿ\s\-']{2,})",
        r"localisé\s+en\s+([A-Za-zÀ-ÖØ-öø-ÿ\s\-']{2,})",
        r"localisé\s+à\s+([A-Za-zÀ-ÖØ-öø-ÿ\s\-']{2,})"
    ]
    for pattern in loc_match_patterns:
        m = re.search(pattern, offer_text_lower, flags=re.IGNORECASE)
        if m:
            loc_required = m.group(1).strip()
            if ',' in loc_required:
                loc_required = loc_required.split(',')[0].strip()
            break

    mobil_required_offer = "mobile" in offer_text_lower or "déplacement" in offer_text_lower
    telework_allowed_offer = "télétravail" in offer_text_lower or "remote" in offer_text_lower
    immediate_required_offer = "immédiatement" in offer_text_lower or "disponible de suite" in offer_text_lower

    # Calculer des attributs de matching pour chaque profil
    candidates = []
    for i, idx in enumerate(indices[0]):
        row = df_profiles.iloc[idx]

        # Compter combien des compétences requises apparaissent dans le texte du profil
        txt = str(row.get('full_text', '')).lower()
        skills_match_count = 0
        for s in required_skills:
            if s and s in txt:
                skills_match_count += 1

        # --- Digital profession filter (Suggestion 4) ---
        profile_job_title = str(row.get('poste_recherche', '')).lower()
        # If the profile's stated job title is not in the digital jobs list, skip this profile.
        if digital_job_titles and profile_job_title and profile_job_title not in digital_job_titles:
            continue # Skip this profile, it's not a digital profession
        elif not digital_job_titles and profile_job_title: # If no digital jobs list, but profile has a job title, try to infer
                skills_match_count += 1

        # role/title match: vérifier titre profil (`poste_recherche`) + texte complet
        role_match = False
        if reqs['role']:
            profile_title = str(row.get('poste_recherche', '')).lower()
            if reqs['role'] in txt or reqs['role'] in profile_title:
                role_match = True

        # location match
        location_match = False
        if reqs['location']:
            loc_field = str(row.get('localisation', '')).lower()
            if reqs['location'] in loc_field or reqs['location'] in txt:
                location_match = True

        # expérience
        profile_exp = int(row.get('exp_years', 0))

        # Score compétences (pour information / fallback)
        if skills_embeddings is not None:
            try:
                profile_skills_emb = skills_embeddings[idx].reshape(1, -1)
                skills_similarity = np.dot(offer_skills_emb, profile_skills_emb.T)[0][0]
                skills_score = max(0, min(1, skills_similarity))
            except Exception:
                skills_score = 0.0
        else:
            skills_score = 0.0

        # Calculer un score d'expérience (toujours, utilisé pour le score final)
        if required_exp is not None:
            if profile_exp >= required_exp:
                # L'expérience est suffisante ou supérieure, le score est élevé
                # Bonus pour l'expérience supplémentaire, plafonné pour ne pas surpondérer
                exp_score = min(1.0, 0.8 + (profile_exp - required_exp) * 0.05)
            else:
                # L'expérience est inférieure, le score est proportionnel
                if required_exp > 0:
                    exp_score = max(0, (profile_exp / required_exp) * 0.7)
                else:
                    exp_score = 0
        else:
            # Pas d'exigence, on normalise sur une échelle de 20 ans
            exp_score = min(1.0, profile_exp / 20)

        # Générer l'explication (optionnel)
        explanation = None
        if with_explanation:
            explanation = generate_explanation(offer_text, row, skills_score, exp_score)

        # Pondération fixe 50% compétences / 50% expérience, comme demandé
        skills_weight = 0.5
        exp_weight = 0.5

        # Calculer un score de pertinence combiné (compétences + expérience)
        try:
            base_score = calculate_weighted_score(skills_score, exp_score, skills_weight=skills_weight, exp_weight=exp_weight)
        except Exception:
            base_score = 0.0

        # --- Malus pour les filtres stricts (remplace le post-filtrage) ---
        malus = 0.0
        profile_row = df_profiles.iloc[idx]

        # Malus de localisation
        if loc_required:
            profile_location_lower = profile_row['localisation'].lower()
            if loc_required not in profile_location_lower:
                malus += 0.15 # Malus important si la localisation ne correspond pas

        # Malus de mobilité
        if mobil_required_offer and profile_row.get('mobilite') == "Pas mobile":
            malus += 0.1 # Malus si la mobilité est requise mais que le profil n'est pas mobile

        # Malus de télétravail
        if telework_allowed_offer and profile_row.get('mobilite') != "Ouvert au télétravail":
            malus += 0.1 # Malus si le télétravail est mentionné mais que le profil n'est pas ouvert

        # Malus de disponibilité
        if immediate_required_offer and profile_row.get('disponibilite') != "Immédiate":
            malus += 0.1 # Malus si la disponibilité immédiate est requise

        # Petites primes pour role_match / location_match / nombre de skills matchés
        bonus = 0.0
        if role_match:
            bonus += 0.08
        if location_match:
            bonus += 0.04
        # bonus croissant mais plafonné pour skills_match_count
        bonus += min(0.03 * skills_match_count, 0.12)

        final_score = max(0.0, min(1.0, base_score + bonus - malus))

        candidates.append({
            'profile': ProfileResult(
                id=int(row['id']),
                score=round(float(final_score), 4),
                exp_years=profile_exp,
                hard_skills=row['hard_skills'],
                localisation=row['localisation'],
                full_text=row['full_text'],
                explanation=explanation
            ),
            'skills_match_count': skills_match_count,
            'role_match': role_match,
            'location_match': location_match,
            'profile_exp': profile_exp
        })

    logger.info(f"match_offer_sync: {len(candidates)} candidates scored before post-matching filters.")

    # La logique de filtrage a été remplacée par un système de malus.
    # On trie maintenant directement la liste complète des candidats.
    logger.info(f"match_offer_sync: No hard filtering applied. Sorting all {len(candidates)} candidates by final score.")

    candidates.sort(key=lambda c: -c.get('profile').score)

    # Retourner les top_k profils
    return [c['profile'] for c in candidates[:top_k]]

# --- Endpoints de l'API ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Matching IA"}
    
# Suggestion 1: Add Support for Structured Offers in JSON
class MatchRequest(BaseModel):
    offer_text: str | None = None  # Original field, now optional
    Poste: str | None = None
    Compétences_techniques: list[str] | None = None
    Expérience_requise: str | None = None
    Localisation: str | None = None
    Type_de_contrat: str | None = None
    Salaire: str | None = None
    top_k: int = 7
    
@app.post("/match", response_model=MatchResponse)
async def match_endpoint(request: MatchRequest):
    """
    Endpoint pour trouver les meilleurs profils correspondant à une offre.
    Supporte les requêtes en texte libre (offer_text) ou structurées en JSON.
    """
    query_text = request.offer_text
    if not query_text: # If offer_text is not provided, construct it from structured fields
        parts = []
        if request.Poste: parts.append(f"Poste: {request.Poste}")
        if request.Compétences_techniques: parts.append(f"Compétences techniques: {', '.join(request.Compétences_techniques)}")
        if request.Expérience_requise: parts.append(f"Expérience requise: {request.Expérience_requise}")
        if request.Localisation: parts.append(f"Localisation: {request.Localisation}")
        if request.Type_de_contrat: parts.append(f"Type de contrat: {request.Type_de_contrat}")
        if request.Salaire: parts.append(f"Salaire: {request.Salaire}")
        
        if not parts:
            raise HTTPException(status_code=400, detail="Veuillez fournir une description ou au moins un critère de recherche.")
        
        query_text = ". ".join(parts)

    try:
        results = match_offer_sync(query_text, request.top_k)
        return MatchResponse(results=results)
    except HTTPException as e:
        # Propage l'exception HTTP si les modèles ne sont pas prêts
        raise e
    except Exception as e:
        logger.error(f"Erreur lors du matching pour l'offre '{request.offer_text}': {e}")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue lors du matching.")


@app.post("/match_debug")
async def match_debug_endpoint(request: MatchRequest):
    """
    Endpoint debug: renvoie pour les top_k candidats les métadonnées de tri permettant
    de comprendre pourquoi un profil a été ordonné de cette manière.
    """
    try:
        # On récupère les mêmes candidats mais sans transformer en ProfileResult
        if "model" not in ml_models or "faiss_index" not in ml_models or "profiles" not in ml_models:
            raise HTTPException(status_code=503, detail="Les modèles ne sont pas encore prêts.")

        # Copier une version simplifiée de la logique de match_offer_sync mais en retournant
        # les métadonnées (skills_match_count, role_match, location_match, profile_exp)
        model = ml_models["model"]
        index = ml_models["faiss_index"]
        df_profiles = ml_models["profiles"]

        offer_text = request.offer_text
        top_k = request.top_k

        # Reutiliser la fonction de matching existante, mais récupérer les candidats bruts
        # Pour éviter duplication lourde, appeler match_offer_sync(with_explanation=True) et
        # reconstruire les métadonnées à partir des explanations et profils retournés.
        results = match_offer_sync(offer_text, top_k=top_k, with_explanation=True)

        debug_list = []
        for pr in results:
            debug_list.append({
                'profile_id': pr.id,
                'exp_years': pr.exp_years,
                'localisation': pr.localisation,
                'skills': pr.hard_skills,
                'strengths': pr.explanation.strengths if pr.explanation else [],
                'weaknesses': pr.explanation.weaknesses if pr.explanation else [],
                'skills_match_score': pr.explanation.skills_match_score if pr.explanation else None,
                'experience_match_score': pr.explanation.experience_match_score if pr.explanation else None
            })

        return {'debug': debug_list}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur match_debug: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne lors du debug du matching.")

# --- Nouveaux Endpoints pour la Recherche --
@app.get("/jobs")
def get_jobs():
    """
    Endpoint pour récupérer la liste des intitulés de poste uniques.
    """
    try:
        # Utiliser les données chargées en mémoire si disponibles
        if "metiers_digital" in ml_models and not ml_models["metiers_digital"].empty:
            df_jobs = ml_models["metiers_digital"]
            return {"jobs": df_jobs["Poste"].unique().tolist()}
        
        # Sinon, essayer de charger le fichier
        df_jobs = pd.read_csv("../../cartographie-metiers-numeriques.csv", sep=';')
        return {"jobs": df_jobs["Poste"].unique().tolist()}
    except FileNotFoundError:
        logger.error("Le fichier cartographie-metiers-numeriques.csv est introuvable.")
        raise HTTPException(status_code=404, detail="Fichier des métiers non trouvé. Fonctionnalité désactivée.")
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier des métiers : {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur.")

class SearchRequest(BaseModel):
    description: str | None = None
    poste: str | None = None
    competences: str | None = None
    experience: str | None = None
    localisation: str | None = None
    type_de_contrat: str | None = None
    salaire: str | None = None

class NewProfile(BaseModel):
    exp_years: int
    diplomes: str
    certifications: str
    hard_skills: list[str]
    soft_skills: list[str]
    langues: list[str]
    localisation: str
    mobilite: str
    disponibilite: str
    experiences: str
    poste_recherche: str | None = None

@app.post("/search", response_model=MatchResponse)
def search_profiles(request: SearchRequest, top_k: int = 7):
    """
    Endpoint pour rechercher des profils avec pondération et explications.
    """
    if "model" not in ml_models or "faiss_index" not in ml_models or "profiles" not in ml_models:
        raise HTTPException(status_code=503, detail="Les modèles ne sont pas encore prêts.")

    query_text = ""
    if request.description:
        query_text = request.description
    else:
        parts = []
        if request.poste:
            parts.append(f"Poste: {request.poste}")
        if request.competences:
            parts.append(f"Compétences: {request.competences}")
        if request.experience:
            parts.append(f"Expérience: {request.experience}")
        if request.localisation:
            parts.append(f"Localisation: {request.localisation}")
        if request.type_de_contrat:
            parts.append(f"Type de contrat: {request.type_de_contrat}")
        if request.salaire:
            parts.append(f"Salaire: {request.salaire}")
        
        if not parts:
            raise HTTPException(status_code=400, detail="Veuillez fournir une description ou au moins un critère de recherche.")
        
        query_text = " - ".join(parts)

    if not query_text:
        raise HTTPException(status_code=400, detail="La requête de recherche est vide.")

    # Utiliser la fonction de matching améliorée
    results = match_offer_sync(query_text, top_k, with_explanation=True)
    return MatchResponse(results=results)


@app.post("/add_profile")
async def add_profile(profile: NewProfile):
    """
    Endpoint pour ajouter un nouveau profil au système.
    """
    try:
        # Lire le fichier CSV existant
        df_profiles = pd.read_csv("../profiles.csv")
        
        # Générer un nouvel ID
        new_id = df_profiles["id"].max() + 1 if not df_profiles.empty else 1
        
        # Créer le texte complet pour la recherche sémantique
        full_text = (
            f"Expériences: {profile.experiences}. "
            f"Diplômes: {profile.diplomes}. "
            f"Certifications: {profile.certifications}. "
            f"Compétences techniques: {', '.join(profile.hard_skills)}. "
            f"Compétences comportementales: {', '.join(profile.soft_skills)}. "
            f"Langues: {', '.join(profile.langues)}. "
            f"Localisation: {profile.localisation}. "
            f"Mobilité: {profile.mobilite}. "
            f"Disponibilité: {profile.disponibilite}."
        )
        
        # Créer une nouvelle ligne pour le DataFrame
        new_row = {
            'id': new_id,
            'exp_years': profile.exp_years,
            'diplomes': profile.diplomes,
            'certifications': profile.certifications,
            'hard_skills': str(profile.hard_skills),
            'soft_skills': str(profile.soft_skills),
            'langues': str(profile.langues),
            'localisation': profile.localisation,
            'mobilite': profile.mobilite,
            'disponibilite': profile.disponibilite,
            'full_text': full_text
        }
        
        # Ajouter la nouvelle ligne au DataFrame
        df_profiles = pd.concat([df_profiles, pd.DataFrame([new_row])], ignore_index=True)
        
        # Sauvegarder le DataFrame mis à jour
        df_profiles.to_csv("../profiles.csv", index=False)
        
        # Mettre à jour l'index FAISS avec le nouveau profil
        skills_text = ', '.join(profile.hard_skills)
        if update_faiss_index(full_text, skills_text):
            # Mettre à jour le DataFrame en mémoire
            ml_models["profiles"] = df_profiles
            logger.info(f"Nouveau profil ajouté avec succès (ID: {new_id})")
            return {"status": "success", "message": f"Profil ajouté avec succès (ID: {new_id})", "profile_id": int(new_id)}
        else:
            logger.warning("Le profil a été ajouté au CSV mais l'index FAISS n'a pas pu être mis à jour")
            return {"status": "warning", "message": "Profil ajouté, mais l'index de recherche n'a pas pu être mis à jour immédiatement"}
            
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du profil : {e}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'ajout du profil : {str(e)}")

# --- Pour exécuter l'application localement ---
# Commande: uvicorn main:app --reload --port 8000
