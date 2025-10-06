
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
from typing import List, Dict, Optional

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
        df_profiles = pd.read_csv("../profiles.csv")
        ml_models["profiles"] = df_profiles
        
        # Charger la cartographie des métiers du numérique
        try:
            df_metiers = pd.read_csv("../../cartographie-metiers-numeriques.csv", sep=';')
            ml_models["metiers_digital"] = df_metiers
            logger.info(f"✅ Cartographie des métiers chargée : {len(df_metiers)} métiers.")
        except FileNotFoundError:
            logger.warning("⚠️ Fichier cartographie-metiers-numeriques.csv non trouvé. Fonctionnalité métiers désactivée.")
            ml_models["metiers_digital"] = pd.DataFrame()
        
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        ml_models["model"] = model
        
        profile_embeddings = model.encode(df_profiles["full_text"].tolist(), convert_to_numpy=True)
        d = profile_embeddings.shape[1]
        
        faiss.normalize_L2(profile_embeddings)
        
        index = faiss.IndexFlatIP(d)
        index.add(profile_embeddings)
        ml_models["faiss_index"] = index
        
        # Créer des embeddings séparés pour les compétences et l'expérience
        skills_embeddings = model.encode(df_profiles["hard_skills"].tolist(), convert_to_numpy=True)
        faiss.normalize_L2(skills_embeddings)
        ml_models["skills_embeddings"] = skills_embeddings
        
        logger.info(f"✅ Index FAISS construit avec {index.ntotal} profils.")
        logger.info("Application démarrée avec succès.")
    except Exception as e:
        logger.error(f"Erreur lors du chargement des modèles : {e}")
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
    
    # Extraire les compétences demandées et celles du profil
    required_skills = extract_skills_from_text(offer_text)
    profile_skills = normalize_skills(profile_row["hard_skills"])
    
    # Analyser les compétences
    matched_skills = [skill for skill in required_skills if any(ps in skill or skill in ps for ps in profile_skills)]
    missing_skills = [skill for skill in required_skills if not any(ps in skill or skill in ps for ps in profile_skills)]
    
    if matched_skills:
        strengths.append(f"Maîtrise de : {', '.join(matched_skills[:5])}")
    
    if missing_skills:
        weaknesses.append(f"Compétences à développer : {', '.join(missing_skills[:3])}")
    
    # Analyser l'expérience
    exp_years = int(profile_row["exp_years"])
    if exp_years >= 5:
        strengths.append(f"Expérience solide ({exp_years} ans)")
    elif exp_years >= 3:
        strengths.append(f"Bonne expérience ({exp_years} ans)")
    else:
        strengths.append(f"Profil junior ({exp_years} ans d'expérience)")
    
    # Analyser la localisation
    if "localisation" in offer_text.lower():
        strengths.append(f"Localisation : {profile_row['localisation']}")
    
    # Analyser la mobilité
    if profile_row.get("mobilite") == "Mobile":
        strengths.append("Ouvert à la mobilité")
    
    # Analyser la disponibilité
    if profile_row.get("disponibilite") == "Immédiate":
        strengths.append("Disponibilité immédiate")
    
    # Si peu de points forts, ajouter des éléments génériques
    if len(strengths) < 2:
        strengths.append("Profil correspondant aux critères généraux")
    
    if len(weaknesses) == 0:
        weaknesses.append("Profil très bien adapté à l'offre")
    
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
    offer_text: str
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

    # Extraire les compétences et l'expérience de l'offre
    required_skills = extract_skills_from_text(offer_text)
    
    # Extraire l'expérience requise (recherche de patterns comme "3 ans", "5 années")
    exp_pattern = re.search(r'(\d+)\s*(ans?|années?|years?)', offer_text.lower())
    required_exp = int(exp_pattern.group(1)) if exp_pattern else 3  # Par défaut 3 ans
    
    # Encoder l'offre complète pour le matching global
    offer_emb = model.encode([offer_text], convert_to_numpy=True)
    faiss.normalize_L2(offer_emb)
    
    # Encoder les compétences de l'offre
    skills_text = ", ".join(required_skills) if required_skills else offer_text
    offer_skills_emb = model.encode([skills_text], convert_to_numpy=True)
    faiss.normalize_L2(offer_skills_emb)
    
    # Recherche FAISS élargie pour avoir plus de candidats à scorer
    search_k = min(top_k * 3, len(df_profiles))  # Chercher 3x plus de profils
    distances, indices = index.search(offer_emb, search_k)
    
    # Calculer les scores pondérés pour chaque profil
    weighted_results = []
    for i, idx in enumerate(indices[0]):
        row = df_profiles.iloc[idx]
        
        # Score de similarité global (base FAISS)
        global_score = float(distances[0][i])
        
        # Score de compétences (similarité cosinus entre compétences)
        if skills_embeddings is not None:
            profile_skills_emb = skills_embeddings[idx].reshape(1, -1)
            skills_similarity = np.dot(offer_skills_emb, profile_skills_emb.T)[0][0]
            skills_score = max(0, min(1, skills_similarity))  # Normaliser entre 0 et 1
        else:
            skills_score = global_score  # Fallback
        
        # Score d'expérience (basé sur la proximité avec l'expérience requise)
        profile_exp = int(row["exp_years"])
        exp_diff = abs(profile_exp - required_exp)
        # Score décroissant avec la différence (max 1 si égal, diminue avec la différence)
        exp_score = max(0, 1 - (exp_diff / 10))  # Pénalité de 0.1 par année de différence
        
        # Score pondéré final : 50% compétences + 50% expérience
        weighted_score = calculate_weighted_score(skills_score, exp_score, 0.5, 0.5)
        
        # Générer l'explication
        explanation = None
        if with_explanation:
            explanation = generate_explanation(offer_text, row, skills_score, exp_score)
        
        weighted_results.append({
            'profile': ProfileResult(
                id=int(row["id"]),
                score=round(weighted_score, 4),
                exp_years=int(row["exp_years"]),
                hard_skills=row["hard_skills"],
                localisation=row["localisation"],
                full_text=row["full_text"],
                explanation=explanation
            ),
            'weighted_score': weighted_score
        })
    
    # Trier par score pondéré décroissant
    weighted_results.sort(key=lambda x: x['weighted_score'], reverse=True)
    
    # Retourner les top_k meilleurs
    return [r['profile'] for r in weighted_results[:top_k]]

# --- Endpoints de l'API ---
@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API de Matching IA"}

@app.post("/match", response_model=MatchResponse)
async def match_endpoint(request: MatchRequest):
    """
    Endpoint pour trouver les meilleurs profils correspondant à une offre.
    """
    try:
        results = match_offer_sync(request.offer_text, request.top_k)
        return MatchResponse(results=results)
    except HTTPException as e:
        # Propage l'exception HTTP si les modèles ne sont pas prêts
        raise e
    except Exception as e:
        logger.error(f"Erreur lors du matching pour l'offre '{request.offer_text}': {e}")
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue lors du matching.")

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
