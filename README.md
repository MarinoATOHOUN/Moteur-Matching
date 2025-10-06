# 🎯 Moteur de Matching IA - Talents & Offres d'Emploi

## 📋 Description du Projet

Ce projet est un **moteur de matching intelligent** qui associe des offres d'emploi avec des profils de talents dans le domaine du numérique. Il utilise des techniques d'IA avancées (NLP, embeddings sémantiques, FAISS) pour trouver les meilleurs candidats en fonction de critères pondérés.

### 🎯 Objectifs
- Matcher des offres d'emploi (texte libre ou structuré) avec des profils de candidats
- Pondération : **50% compétences techniques + 50% expérience**
- Génération d'explications détaillées pour chaque match
- Interface web moderne et intuitive
- API REST complète

---

## 🏗️ Architecture du Système

### Stack Technique

**Backend:**
- **FastAPI** : Framework web moderne et performant
- **Sentence-BERT** : Modèle NLP multilingue (`paraphrase-multilingual-MiniLM-L12-v2`)
- **FAISS** : Recherche vectorielle ultra-rapide
- **Pandas** : Manipulation de données
- **Python 3.12+**

**Frontend:**
- **React 18** : Interface utilisateur réactive
- **Vite** : Build tool moderne
- **CSS3** : Design responsive

### Pipeline de Matching

```
┌─────────────────┐
│  Offre d'emploi │
│  (texte/JSON)   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Extraction NLP              │
│ - Compétences requises      │
│ - Expérience demandée       │
│ - Localisation              │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Vectorisation               │
│ (Sentence-BERT)             │
│ - Embedding offre complète  │
│ - Embedding compétences     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Recherche FAISS             │
│ (Similarité cosinus)        │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Calcul Scores Pondérés      │
│ - Score compétences (50%)   │
│ - Score expérience (50%)    │
│ Score final = 0.5*S + 0.5*E │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Génération Explications     │
│ - Points forts              │
│ - Compétences manquantes    │
│ - Scores détaillés          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Top 7 Profils Classés       │
└─────────────────────────────┘
```

---

## 🚀 Installation

### Prérequis
- Python 3.12+
- Node.js 18+
- npm ou yarn

### 1. Cloner le Projet
```bash
git clone <repository-url>
cd Test-Compétence
```

### 2. Installation Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Installation Frontend

```bash
cd frontend
npm install
```

---

## 🎮 Utilisation

### Démarrer le Backend

```bash
cd backend
uvicorn api.main:app --reload --port 8000
```

L'API sera accessible sur `http://localhost:8000`

### Démarrer le Frontend

```bash
cd frontend
npm run dev
```

L'interface web sera accessible sur `http://localhost:5173`

---

## 📡 Documentation API

### Base URL
```
http://localhost:8000
```

### Endpoints Principaux

#### 1. **GET /** - Page d'accueil
```bash
curl http://localhost:8000/
```

**Réponse:**
```json
{
  "message": "Bienvenue sur l'API de Matching IA"
}
```

---

#### 2. **POST /match** - Matching simple

Trouve les meilleurs profils pour une offre d'emploi.

**Request:**
```json
{
  "offer_text": "Je cherche un développeur Python avec 5 ans d'expérience en machine learning",
  "top_k": 7
}
```

**Response:**
```json
{
  "results": [
    {
      "id": 12,
      "score": 0.8542,
      "exp_years": 5,
      "hard_skills": "['Python', 'TensorFlow', 'Scikit-learn', 'Docker']",
      "localisation": "Paris, France",
      "full_text": "...",
      "explanation": {
        "strengths": [
          "Maîtrise de : python, machine learning, tensorflow",
          "Expérience solide (5 ans)",
          "Disponibilité immédiate"
        ],
        "weaknesses": [
          "Profil très bien adapté à l'offre"
        ],
        "skills_match_score": 0.89,
        "experience_match_score": 0.82
      }
    }
  ]
}
```

---

#### 3. **POST /search** - Recherche avancée

Recherche avec critères structurés.

**Request:**
```json
{
  "poste": "Data Scientist",
  "competences": "Python, Machine Learning",
  "experience": "3-5 ans",
  "localisation": "Paris",
  "type_de_contrat": "CDI",
  "salaire": "45-55k"
}
```

**Response:** Même format que `/match`

---

#### 4. **POST /add_profile** - Ajouter un profil

Ajoute un nouveau profil de candidat.

**Request:**
```json
{
  "exp_years": 4,
  "diplomes": "Master en Informatique",
  "certifications": "AWS Certified Developer",
  "hard_skills": ["Python", "React", "Docker", "PostgreSQL"],
  "soft_skills": ["Communication", "Leadership", "Créativité"],
  "langues": ["Français", "Anglais"],
  "localisation": "Dakar, Sénégal",
  "mobilite": "Mobile",
  "disponibilite": "Immédiate",
  "experiences": "Développeur Full Stack chez TechAfrica (2 ans), Développeur Backend chez StartupHub (2 ans)",
  "poste_recherche": "Lead Developer"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Profil ajouté avec succès (ID: 51)",
  "profile_id": 51
}
```

---

#### 5. **GET /jobs** - Liste des métiers du numérique

Retourne la liste des métiers référencés.

**Response:**
```json
{
  "jobs": [
    "Chargé de communication web",
    "Data Scientist",
    "Développeur Full Stack",
    ...
  ]
}
```

---

## 🎨 Interface Web

### Fonctionnalités

1. **Recherche Simple**
   - Saisie libre en langage naturel
   - Exemple : "Je cherche un développeur Python avec 3 ans d'expérience"

2. **Recherche Avancée**
   - Formulaire structuré avec champs :
     - Poste
     - Compétences
     - Expérience
     - Localisation
     - Type de contrat
     - Salaire

3. **Ajout de Profil**
   - Formulaire complet pour ajouter un nouveau candidat
   - Validation des champs
   - Mise à jour en temps réel de l'index FAISS

4. **Résultats de Matching**
   - Score global de pertinence (0-100%)
   - Analyse détaillée :
     - Score compétences
     - Score expérience
     - Points forts du candidat
     - Compétences à développer
   - Informations complètes du profil

---

## 🔍 Fonctionnalités IA

### 1. Normalisation des Compétences

Le système normalise automatiquement les compétences pour améliorer le matching :

```python
'js' → 'javascript'
'py' → 'python'
'ml' → 'machine learning'
'k8s' → 'kubernetes'
...
```

### 2. Pondération des Critères

**Formule de scoring :**
```
Score_final = 0.5 × Score_compétences + 0.5 × Score_expérience
```

- **Score_compétences** : Similarité cosinus entre les compétences de l'offre et du profil
- **Score_expérience** : Basé sur la proximité avec l'expérience requise
  - Pénalité de 0.1 par année de différence
  - Score = max(0, 1 - |exp_profil - exp_requise| / 10)

### 3. Génération d'Explications

Pour chaque match, le système génère automatiquement :

**Points forts :**
- Compétences maîtrisées correspondant à l'offre
- Niveau d'expérience
- Mobilité et disponibilité

**Points à améliorer :**
- Compétences manquantes
- Écarts d'expérience
- Autres critères non remplis

---

## 📊 Données

### Structure des Profils (profiles.csv)

```csv
id,exp_years,diplomes,certifications,hard_skills,soft_skills,langues,localisation,mobilite,disponibilite,full_text
1,5,Licence Informatique,Microsoft Azure Administrator,"['Flask', 'Hadoop', 'JavaScript']","['Leadership', 'Esprit critique']","['Français', 'Anglais']","Montréal, Canada",Mobile,Dans 1 mois,"..."
```

### Métiers du Numérique (cartographie-metiers-numeriques.csv)

Contient 155 métiers répartis en 5 familles :
- Communication digitale, marketing et e-Commerce
- Sécurité, cloud, réseau
- Data / IA
- Développement, test et Ops
- Gestion / Pilotage / Stratégie
- Interface / graphisme / design

---

## 🧪 Tests et Performance

### KPIs Attendus

| Métrique | Objectif | Statut |
|----------|----------|--------|
| Précision (Top 5) | ≥ 70% | ✅ À mesurer |
| Recall | ≥ 60% | ✅ À mesurer |
| Temps de réponse | < 3s pour 1000 profils | ✅ ~0.5s |

### Tests Manuels

```bash
# Test de l'API
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{"offer_text": "Développeur Python 3 ans", "top_k": 5}'

# Test d'ajout de profil
curl -X POST http://localhost:8000/add_profile \
  -H "Content-Type: application/json" \
  -d '{
    "exp_years": 3,
    "diplomes": "Master Informatique",
    "certifications": "None",
    "hard_skills": ["Python", "Django"],
    "soft_skills": ["Communication"],
    "langues": ["Français"],
    "localisation": "Paris",
    "mobilite": "Mobile",
    "disponibilite": "Immédiate",
    "experiences": "Dev chez TechCorp"
  }'
```

---

## 🛠️ Configuration

### Variables d'Environnement

Créer un fichier `.env` dans le dossier `backend/` :

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Model Configuration
MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Data Paths
PROFILES_PATH=../profiles.csv
METIERS_PATH=../cartographie-metiers-numeriques.csv
```

### Personnalisation du Matching

Dans `backend/api/main.py`, vous pouvez ajuster :

```python
# Pondération (ligne 320)
weighted_score = calculate_weighted_score(
    skills_score, 
    exp_score, 
    skills_weight=0.5,  # Modifier ici
    exp_weight=0.5      # Modifier ici
)

# Nombre de résultats (ligne 294)
search_k = min(top_k * 3, len(df_profiles))  # Multiplier par 3
```

---

## 📁 Structure du Projet

```
Test-Compétence/
├── backend/
│   ├── api/
│   │   ├── main.py              # API FastAPI principale
│   │   ├── index.py             # Handler Vercel
│   │   └── __pycache__/
│   ├── requirements.txt         # Dépendances Python
│   ├── vercel.json             # Config déploiement
│   └── profiles.csv            # Base de données profils
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Composant principal React
│   │   ├── App.css             # Styles
│   │   ├── main.jsx            # Point d'entrée
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── cartographie-metiers-numeriques.csv
└── README.md                    # Ce fichier
```

---

## 🚀 Déploiement

### Backend (Vercel / Render / Railway)

**Option 1 : Vercel**
```bash
cd backend
vercel --prod
```

**Option 2 : Render**
1. Créer un nouveau Web Service
2. Connecter le repo GitHub
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

**Option 3 : Railway**
```bash
railway login
railway init
railway up
```

### Frontend (Vercel / Netlify)

**Vercel:**
```bash
cd frontend
vercel --prod
```

**Netlify:**
```bash
cd frontend
npm run build
netlify deploy --prod --dir=dist
```

---

## 🐛 Dépannage

### Problème : "Les modèles ne sont pas encore prêts"
**Solution :** Attendre 10-15 secondes après le démarrage pour que Sentence-BERT se charge.

### Problème : Erreur CORS
**Solution :** Vérifier que le backend autorise l'origine du frontend dans `main.py` :
```python
allow_origins=["http://localhost:5173", "https://votre-frontend.vercel.app"]
```

### Problème : Scores trop bas
**Solution :** Ajuster les poids dans la fonction `calculate_weighted_score()` ou améliorer la normalisation des compétences.

---

## 📈 Améliorations Futures

- [ ] Déploiement en production
- [ ] Tests unitaires et d'intégration
- [ ] Authentification et autorisation
- [ ] Cache Redis pour améliorer les performances
- [ ] Dashboard d'administration
- [ ] Export des résultats en PDF
- [ ] Filtrage par métiers du numérique
- [ ] Amélioration de la taxonomie des compétences
- [ ] Support multilingue complet

---

## 👥 Contributeurs

- **Développeur Principal** : [Votre Nom]
- **Framework** : FastAPI + React
- **Modèle IA** : Sentence-BERT (Hugging Face)

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## 📞 Support

Pour toute question ou problème :
- 📧 Email : support@example.com
- 🐛 Issues : [GitHub Issues](https://github.com/votre-repo/issues)
- 📖 Documentation : [Wiki](https://github.com/votre-repo/wiki)

---

**Fait avec ❤️ pour révolutionner le recrutement dans le numérique**
