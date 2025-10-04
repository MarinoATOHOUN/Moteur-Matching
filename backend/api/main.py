
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from contextlib import asynccontextmanager
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Modèles et Données ---
# Utiliser un dictionnaire pour stocker les modèles et données chargés
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code exécuté au démarrage de l'application
    logger.info("Chargement des modèles et des données...")
    try:
        df_profiles = pd.read_csv("../profiles.csv")
        ml_models["profiles"] = df_profiles
        
        model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        ml_models["model"] = model
        
        profile_embeddings = model.encode(df_profiles["full_text"].tolist(), convert_to_numpy=True)
        d = profile_embeddings.shape[1]
        
        faiss.normalize_L2(profile_embeddings)
        
        index = faiss.IndexFlatIP(d)
        index.add(profile_embeddings)
        ml_models["faiss_index"] = index
        
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

class MatchResponse(BaseModel):
    results: list[ProfileResult]

# --- Fonctions Métier ---
def match_offer_sync(offer_text: str, top_k: int = 7):
    """
    Fonction de matching synchrone utilisant les modèles pré-chargés.
    """
    if "model" not in ml_models or "faiss_index" not in ml_models or "profiles" not in ml_models:
        raise HTTPException(status_code=503, detail="Les modèles ne sont pas encore prêts. Veuillez réessayer dans quelques instants.")

    model = ml_models["model"]
    index = ml_models["faiss_index"]
    df_profiles = ml_models["profiles"]

    # Encoder l'offre
    offer_emb = model.encode([offer_text], convert_to_numpy=True)
    faiss.normalize_L2(offer_emb)
    
    # Recherche FAISS
    distances, indices = index.search(offer_emb, top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        row = df_profiles.iloc[idx]
        results.append(ProfileResult(
            id=int(row["id"]),
            score=float(distances[0][i]),
            exp_years=int(row["exp_years"]),
            hard_skills=row["hard_skills"],
            localisation=row["localisation"],
            full_text=row["full_text"]
        ))
    return results

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
        df_jobs = pd.read_csv("../cartographie-metiers-numeriques.csv", sep=';')
        return {"jobs": df_jobs["Poste"].unique().tolist()}
    except FileNotFoundError:
        logger.error("Le fichier cartographie-metiers-numeriques.csv est introuvable.")
        raise HTTPException(status_code=500, detail="Fichier des métiers non trouvé.")
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

@app.post("/search", response_model=MatchResponse)
def search_profiles(request: SearchRequest, top_k: int = 7):
    """
    Endpoint pour rechercher des profils.
    Peut utiliser une description textuelle (recherche sémantique) ou
    des critères structurés qui sont combinés pour une recherche sémantique.
    """
    if "model" not in ml_models or "faiss_index" not in ml_models or "profiles" not in ml_models:
        raise HTTPException(status_code=503, detail="Les modèles ne sont pas encore prêts.")

    model = ml_models["model"]
    index = ml_models["faiss_index"]
    df_profiles = ml_models["profiles"]

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

    # Encoder la requête
    query_emb = model.encode([query_text], convert_to_numpy=True)
    faiss.normalize_L2(query_emb)
    
    # Recherche FAISS
    distances, indices = index.search(query_emb, top_k)
    
    results = []
    for i, idx in enumerate(indices[0]):
        row = df_profiles.iloc[idx]
        results.append(ProfileResult(
            id=int(row["id"]),
            score=float(distances[0][i]),
            exp_years=int(row["exp_years"]),
            hard_skills=row["hard_skills"],
            localisation=row["localisation"],
            full_text=row["full_text"]
        ))
        
    return MatchResponse(results=results)


# --- Pour exécuter l'application localement ---
# Commande: uvicorn main:app --reload --port 8000
