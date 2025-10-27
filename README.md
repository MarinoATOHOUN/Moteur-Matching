
----
# Moteur de Matching IA - Documentation Technique

**Auteur** : Marino ATOHOUN, Data Scientist  
**Version** : 1.0 (Octobre 2025)

---

## 1. Contexte et Objectifs

Ce document présente l'architecture technique et le fonctionnement du moteur de matching IA, développé dans le cadre d'un test de recrutement. L'objectif principal était de concevoir et de livrer un **système de Proof of Concept (PoC) fonctionnel** capable d'associer des offres d'emploi du secteur numérique avec une base de profils de talents.

Le cahier des charges imposait une **pondération stricte de 50% sur les compétences techniques (hard skills) et 50% sur l'expérience professionnelle**, tout en fournissant des résultats interprétables.

## 2. Architecture du Système

Pour répondre aux exigences de performance et de scalabilité, j'ai opté pour une architecture découplée avec un backend Python et un frontend JavaScript.

### Stack Technique

| Domaine | Technologie | Version/Modèle | Rôle |
|---|---|---|---|
| **Backend** | **FastAPI** | 0.118.0 | Framework web asynchrone pour une API performante et documentée (Swagger UI). |
| **NLP** | **Sentence-BERT** | `paraphrase-multilingual-MiniLM-L12-v2` | Création d'embeddings sémantiques de haute qualité pour le texte (offres et profils). |
| **Recherche** | **FAISS** | 1.8.0 | Bibliothèque de Facebook AI pour une recherche de similarité vectorielle ultra-rapide. |
| **Données** | **Pandas** | 2.2.2 | Manipulation et gestion des données tabulaires (profils, métiers). |
| **Frontend** | **React** | 18.2.0 | Construction d'une interface utilisateur réactive et modulaire. |
| **Build Tool** | **Vite** | 5.3.1 | Environnement de développement frontend rapide et optimisé. |

### Pipeline de Matching : de la Requête au Résultat

Le processus de matching, au cœur du système, a été conçu pour être à la fois rapide et pertinent. Il se déroule en plusieurs étapes clés :

```mermaid
graph TD
    A[1. Requête Utilisateur<br>(Texte libre ou structuré)] --> B{2. Construction de la Query Text};
    B --> C[3. Vectorisation de l'Offre<br>(Sentence-BERT)];
    C --> D[4. Recherche K-NN<br>(FAISS IndexFlatIP)];
    D --> E{5. Scoring & Classement};
    subgraph "Étape 5 : Scoring & Classement (match_offer_sync)"
        direction LR
        E1[Calcul Score Compétences<br><i>(similarité vectorielle)</i>] --> F;
        E2[Calcul Score Expérience<br><i>(proximité avec l'exigence)</i>] --> F;
        F[Calcul Score de Base<br><b>(50% Skills + 50% Exp)</b>] --> G;
        G --> H{Application Bonus/Malus};
        H --> I[Calcul Score Final];
    end
    E --> J[6. Génération des Explications];
    J --> K[7. Shortlist<br>(Top 7 profils)];
```

1.  **Requête Utilisateur** : L'API reçoit une offre soit en texte libre (`description`), soit via des champs structurés (poste, compétences, etc.).
2.  **Construction de la Query Text** : Les champs structurés sont assemblés en une chaîne de caractères cohérente pour l'analyse sémantique.
3.  **Vectorisation de l'Offre** : Le texte de l'offre est transformé en un vecteur numérique (embedding) par le modèle Sentence-BERT.
4.  **Recherche K-NN (K-Nearest Neighbors)** : FAISS effectue une recherche de similarité cosinus (via `IndexFlatIP`) pour trouver les `k*5` profils les plus proches sémantiquement dans la base de données pré-vectorisée. Cette recherche élargie permet d'éviter de manquer des candidats pertinents.
5.  **Scoring & Classement** : C'est l'étape la plus critique. Pour chaque candidat présélectionné :
   *   Un **score de base** est calculé en respectant la pondération 50/50.
   *   Des **bonus** sont ajoutés pour des correspondances explicites (poste, localisation).
   *   Des **malus** sont appliqués pour des incompatibilités claires (localisation, mobilité, disponibilité), ce qui permet de déclasser un profil sans l'éliminer complètement.
   *   Le **score final** est obtenu, et les candidats sont classés.
6.  **Génération des Explications** : Pour chaque profil du top, le système analyse les correspondances et les écarts pour générer des points forts et des points faibles.
7.  **Shortlist** : L'API retourne la liste finale des 7 meilleurs profils.

## 3. Installation et Lancement

### Prérequis
- Python 3.10+
- Node.js 18+ et npm

### Backend

```bash
# Se placer dans le dossier backend
cd backend

# Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# venv\Scripts\activate    # Sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur d'API
uvicorn api.main:app --reload --port 8000
```
L'API est alors accessible à `http://localhost:8000` et la documentation interactive (Swagger) à `http://localhost:8000/docs`.

### Frontend

```bash
# Se placer dans le dossier frontend
cd frontend

# Installer les dépendances
npm install

# Lancer le serveur de développement
npm run dev
```
L'interface web est accessible à `http://localhost:5173`.

## 4. Documentation de l'API

L'API REST est le point d'entrée unique pour toutes les interactions avec le moteur de matching.

**Base URL** : `http://localhost:8000`

---

### `POST /search`

Endpoint principal pour la recherche de profils. Il accepte des requêtes simples (texte libre) ou avancées (champs structurés).

**Requête (Recherche Avancée)**
```json
{
  "poste": "Data Scientist",
  "competences": "PyTorch, TensorFlow, Machine Learning",
  "experience": "5 ans",
  "localisation": "Montréal, Canada"
}
```

**Réponse**
```json
{
  "results": [
    {
      "id": 618,
      "score": 0.6103,
      "exp_years": 15,
      "hard_skills": "['Numpy', 'BigQuery', 'Data Visualization', 'Kafka']",
      "localisation": "Paris, France",
      "full_text": "...",
      "explanation": {
        "strengths": ["Expérience très solide (15 ans)", "Localisation : Paris, France"],
        "weaknesses": ["Quelques légers écarts de compétences ou d'expérience"],
        "skills_match_score": 0.31,
        "experience_match_score": 0.75
      }
    }
    // ... autres résultats
  ]
}
```

---

### `POST /add_profile`

Permet d'ajouter un nouveau profil talent à la base de données. Le système met à jour le fichier `profiles.csv` et l'index FAISS en mémoire.

**Requête**
```json
{
  "exp_years": 4,
  "diplomes": "Master en Informatique",
  "certifications": "AWS Certified Developer",
  "hard_skills": ["Python", "React", "Docker"],
  "soft_skills": ["Communication", "Créativité"],
  "langues": ["Français", "Anglais"],
  "localisation": "Dakar, Sénégal",
  "mobilite": "Mobile",
  "disponibilite": "Immédiate",
  "experiences": "Développeur Full Stack chez TechAfrica (2 ans)",
  "poste_recherche": "Lead Developer"
}
```

**Réponse**
```json
{
  "status": "success",
  "message": "Profil ajouté avec succès (ID: 1001)",
  "profile_id": 1001
}
```

---

### `GET /jobs`

Retourne la liste unique des intitulés de poste extraits du fichier `cartographie-metiers-numeriques.csv`.

**Réponse**
```json
{
  "jobs": [
    "Chargé de communication web",
    "Chef de projet communication digitale",
    "Data Scientist",
    "Développeur Full Stack",
    ...
  ]
}
```

## 5. Décisions Techniques et Implémentation

En tant que Data Scientist sur ce projet, plusieurs décisions clés ont été prises pour garantir la qualité et la pertinence des résultats.

### 5.1. Normalisation et Filtrage

*   **Taxonomie des Compétences** : Une fonction `normalize_skills` a été implémentée pour regrouper les synonymes et acronymes (`py` -> `python`, `k8s` -> `kubernetes`). C'est une étape cruciale pour ne pas pénaliser un profil à cause d'une simple variation terminologique.
*   **Filtrage par Métier du Numérique** : Le système utilise la `cartographie-metiers-numeriques.csv` pour s'assurer que les profils retournés correspondent bien à des métiers du secteur digital. Un profil dont le `poste_recherche` n'est pas dans cette liste est écarté, conformément au cahier des charges.

### 5.2. Algorithme de Scoring Avancé

Le cahier des charges demandait une pondération 50/50. J'ai implémenté cette base, mais je l'ai enrichie pour obtenir un classement plus fin et plus réaliste.

**Formule de Score Final :**
`FinalScore = max(0, min(1, BaseScore + Bonus - Malus))`

*   **`BaseScore`** : `0.5 * SkillsScore + 0.5 * ExperienceScore`. C'est le cœur du calcul, respectant l'exigence initiale.
*   **`Bonus` (jusqu'à +0.20)** : Pour valoriser les "quick wins". Un profil dont le titre de poste ou la localisation correspondent explicitement à la demande reçoit un léger boost. Cela permet de faire remonter des profils manifestement pertinents.
*   **`Malus` (jusqu'à -0.45)** : C'est une approche de "soft filtering". Plutôt que d'éliminer brutalement un excellent profil parce qu'il n'est pas "disponible immédiatement" ou qu'il est dans une ville voisine, on lui applique une pénalité. Il reste ainsi dans les résultats, mais est moins bien classé qu'un profil équivalent qui coche toutes les cases.

Cette approche hybride est plus robuste et évite le problème des "résultats vides" pour des requêtes très spécifiques, un écueil courant dans les systèmes de filtrage stricts.

### 5.3. Gestion des Données

*   **Chargement au Démarrage** : Les modèles (Sentence-BERT, FAISS) et les données (profils, métiers) sont chargés une seule fois au démarrage de l'application FastAPI grâce au `lifespan manager`. Cela garantit des temps de réponse très faibles pour les requêtes, car il n'y a pas de rechargement à chaque appel.
*   **Mise à Jour en Mémoire** : Lors de l'ajout d'un nouveau profil via l'API, non seulement le fichier CSV est mis à jour, mais l'index FAISS et le DataFrame Pandas en mémoire sont également actualisés. Le nouveau profil est donc immédiatement disponible pour les recherches suivantes sans nécessiter de redémarrage du serveur.

## 6. Structure du Projet

Le projet est organisé en deux dossiers principaux pour une séparation claire des préoccupations.

```
Test-Compétence/
├── backend/
│   ├── api/
│   │   └── main.py              # Logique API, matching et endpoints
│   ├── requirements.txt         # Dépendances Python
│   └── profiles.csv             # Base de données des profils
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # Composant React principal et logique UI
│   │   └── App.css              # Styles
│   ├── package.json
│   └── vite.config.js
├── cartographie-metiers-numeriques.csv # Référentiel des métiers
├── RAPPORT_EVALUATION.md        # Rapport de performance et KPIs
└── README.md                    # Cette documentation
```

## 7. Déploiement

Le projet est conçu pour être facilement déployable sur des plateformes modernes.

### Backend (FastAPI)

Recommandation : **Render** ou **Railway**.

*   **Build Command** : `pip install -r requirements.txt`
*   **Start Command** : `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

*Note : Les plateformes comme Render gèrent automatiquement la variable d'environnement `$PORT`.*

### Frontend (React)

Recommandation : **Vercel** ou **Netlify**.

Le déploiement est standard pour une application Vite/React. Il suffit de lier le dépôt Git et de configurer le build. La variable d'environnement `VITE_API_URL` doit être configurée pour pointer vers l'URL du backend déployé.

## 8. Pistes d'Amélioration

Ce PoC constitue une base solide. Voici quelques axes d'amélioration que j'envisagerais pour une V2 :

1.  **Fine-Tuning du Modèle** : Entraîner plus spécifiquement le modèle Sentence-BERT sur des paires (offre, CV pertinent) pour améliorer la compréhension sémantique propre au domaine du recrutement.
2.  **Extraction d'Entités Nommées (NER)** : Utiliser un modèle de NER pour extraire de manière plus fiable les compétences, les noms d'entreprises et les intitulés de poste directement depuis le texte, plutôt que de se baser sur des listes prédéfinies.
3.  **Cache Redis** : Mettre en cache les résultats des requêtes fréquentes pour réduire encore les temps de réponse et la charge sur le serveur.
4.  **Tests Automatisés** : Développer une suite de tests unitaires (`pytest`) et d'intégration pour garantir la non-régression et la fiabilité du code lors des évolutions futures.

