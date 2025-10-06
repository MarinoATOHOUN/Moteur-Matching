import React, { useState } from 'react';
import './App.css';

function App() {
  const [offerText, setOfferText] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [searchType, setSearchType] = useState('simple'); // 'simple', 'advanced', or 'add'
  const [poste, setPoste] = useState('');
  const [competences, setCompetences] = useState('');
  const [experience, setExperience] = useState('');
  const [localisation, setLocalisation] = useState('');
  const [typeDeContrat, setTypeDeContrat] = useState('');
  const [salaire, setSalaire] = useState('');

  // États pour l'ajout de profil
  const [newProfile, setNewProfile] = useState({
    exp_years: '',
    diplomes: '',
    certifications: '',
    hard_skills: '',
    soft_skills: '',
    langues: '',
    localisation: '',
    mobilite: '',
    disponibilite: '',
    experiences: '',
    poste_recherche: ''
  });
  const [addProfileSuccess, setAddProfileSuccess] = useState(null);
  const [addProfileError, setAddProfileError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setResults([]);

    let requestBody;

    if (searchType === 'simple') {
      requestBody = { description: offerText };
    } else {
      // Build the request body only with non-empty fields
      const advancedFields = {
        poste,
        competences,
        experience,
        localisation,
        type_de_contrat: typeDeContrat,
        salaire,
      };
      requestBody = Object.entries(advancedFields).reduce((acc, [key, value]) => {
        if (value) {
          acc[key] = value;
        }
        return acc;
      }, {});
    }

    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Une erreur est survenue.');
      }

      const data = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetAdvanced = () => {
    setPoste('');
    setCompetences('');
    setExperience('');
    setLocalisation('');
    setTypeDeContrat('');
    setSalaire('');
  };

  const handleProfileInputChange = (field, value) => {
    setNewProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleAddProfile = async (event) => {
    event.preventDefault();
    setIsLoading(true);
    setAddProfileError(null);
    setAddProfileSuccess(null);

    // Convertir les chaînes en tableaux pour les compétences et langues
    const profileData = {
      ...newProfile,
      exp_years: parseInt(newProfile.exp_years),
      hard_skills: newProfile.hard_skills.split(',').map(s => s.trim()).filter(s => s),
      soft_skills: newProfile.soft_skills.split(',').map(s => s.trim()).filter(s => s),
      langues: newProfile.langues.split(',').map(s => s.trim()).filter(s => s)
    };

    try {
      const response = await fetch('http://localhost:8000/add_profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Une erreur est survenue.');
      }

      const data = await response.json();
      setAddProfileSuccess(`Profil ajouté avec succès ! ID: ${data.profile_id}`);
      
      // Réinitialiser le formulaire
      setNewProfile({
        exp_years: '',
        diplomes: '',
        certifications: '',
        hard_skills: '',
        soft_skills: '',
        langues: '',
        localisation: '',
        mobilite: '',
        disponibilite: '',
        experiences: '',
        poste_recherche: ''
      });
    } catch (err) {
      setAddProfileError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetNewProfile = () => {
    setNewProfile({
      exp_years: '',
      diplomes: '',
      certifications: '',
      hard_skills: '',
      soft_skills: '',
      langues: '',
      localisation: '',
      mobilite: '',
      disponibilite: '',
      experiences: '',
      poste_recherche: ''
    });
    setAddProfileSuccess(null);
    setAddProfileError(null);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Moteur de Matching IA</h1>
        <p>Saisissez une offre d'emploi pour trouver les meilleurs talents.</p>
      </header>
      <main>
        <div className="search-type-selector">
          <button onClick={() => setSearchType('simple')} className={`search-type-btn ${searchType === 'simple' ? 'active' : ''}`}>
            Recherche Simple
          </button>
          <button onClick={() => setSearchType('advanced')} className={`search-type-btn ${searchType === 'advanced' ? 'active' : ''}`}>
            Recherche Avancée
          </button>
          <button onClick={() => setSearchType('add')} className={`search-type-btn ${searchType === 'add' ? 'active' : ''}`}>
            Ajouter un Profil
          </button>
        </div>

        {searchType === 'simple' ? (
          <form onSubmit={handleSubmit} className="offer-form">
            <textarea
              value={offerText}
              onChange={(e) => setOfferText(e.target.value)}
              placeholder="Ex: 'Je cherche un développeur Python spécialisé en fintech avec 3 ans d'expérience au Sénégal'"
              rows="5"
            />
            <button type="submit" disabled={isLoading || !offerText.trim()}>
              {isLoading ? 'Recherche en cours...' : 'Trouver les talents'}
            </button>
          </form>
        ) : searchType === 'advanced' ? (
          <form onSubmit={handleSubmit} className="advanced-form">
            <div className="form-grid">
              <input type="text" value={poste} onChange={(e) => setPoste(e.target.value)} placeholder="Poste (ex: Développeur Frontend)" />
              <input type="text" value={competences} onChange={(e) => setCompetences(e.target.value)} placeholder="Compétences (ex: React, Node.js)" />
              <input type="text" value={experience} onChange={(e) => setExperience(e.target.value)} placeholder="Expérience (ex: 3 ans, 5-7 ans)" />
              <input type="text" value={localisation} onChange={(e) => setLocalisation(e.target.value)} placeholder="Localisation (ex: Dakar, Sénégal)" />
              <input type="text" value={typeDeContrat} onChange={(e) => setTypeDeContrat(e.target.value)} placeholder="Type de contrat (ex: CDI, Freelance)" />
              <input type="text" value={salaire} onChange={(e) => setSalaire(e.target.value)} placeholder="Salaire (ex: 30-40k€)" />
            </div>
            <div className="form-actions">
              <button type="button" onClick={handleResetAdvanced} className="secondary-btn">Réinitialiser</button>
              <button type="submit" disabled={isLoading}>
                {isLoading ? 'Recherche en cours...' : 'Trouver les talents'}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleAddProfile} className="add-profile-form">
            <h2>Ajouter un nouveau profil</h2>
            <div className="form-grid-add">
              <div className="form-field">
                <label>Années d'expérience *</label>
                <input 
                  type="number" 
                  value={newProfile.exp_years} 
                  onChange={(e) => handleProfileInputChange('exp_years', e.target.value)}
                  placeholder="Ex: 5"
                  required
                />
              </div>
              <div className="form-field">
                <label>Diplômes *</label>
                <input 
                  type="text" 
                  value={newProfile.diplomes} 
                  onChange={(e) => handleProfileInputChange('diplomes', e.target.value)}
                  placeholder="Ex: Master en Informatique"
                  required
                />
              </div>
              <div className="form-field">
                <label>Certifications</label>
                <input 
                  type="text" 
                  value={newProfile.certifications} 
                  onChange={(e) => handleProfileInputChange('certifications', e.target.value)}
                  placeholder="Ex: AWS Certified Developer"
                />
              </div>
              <div className="form-field">
                <label>Compétences techniques * (séparées par des virgules)</label>
                <input 
                  type="text" 
                  value={newProfile.hard_skills} 
                  onChange={(e) => handleProfileInputChange('hard_skills', e.target.value)}
                  placeholder="Ex: Python, Docker, AWS, FastAPI"
                  required
                />
              </div>
              <div className="form-field">
                <label>Compétences comportementales * (séparées par des virgules)</label>
                <input 
                  type="text" 
                  value={newProfile.soft_skills} 
                  onChange={(e) => handleProfileInputChange('soft_skills', e.target.value)}
                  placeholder="Ex: Communication, Travail d'équipe"
                  required
                />
              </div>
              <div className="form-field">
                <label>Langues * (séparées par des virgules)</label>
                <input 
                  type="text" 
                  value={newProfile.langues} 
                  onChange={(e) => handleProfileInputChange('langues', e.target.value)}
                  placeholder="Ex: Français, Anglais"
                  required
                />
              </div>
              <div className="form-field">
                <label>Localisation *</label>
                <input 
                  type="text" 
                  value={newProfile.localisation} 
                  onChange={(e) => handleProfileInputChange('localisation', e.target.value)}
                  placeholder="Ex: Paris, France"
                  required
                />
              </div>
              <div className="form-field">
                <label>Mobilité *</label>
                <select 
                  value={newProfile.mobilite} 
                  onChange={(e) => handleProfileInputChange('mobilite', e.target.value)}
                  required
                >
                  <option value="">Sélectionner...</option>
                  <option value="Mobile">Mobile</option>
                  <option value="Pas mobile">Pas mobile</option>
                  <option value="Ouvert au télétravail">Ouvert au télétravail</option>
                </select>
              </div>
              <div className="form-field">
                <label>Disponibilité *</label>
                <select 
                  value={newProfile.disponibilite} 
                  onChange={(e) => handleProfileInputChange('disponibilite', e.target.value)}
                  required
                >
                  <option value="">Sélectionner...</option>
                  <option value="Immédiate">Immédiate</option>
                  <option value="Dans 1 mois">Dans 1 mois</option>
                  <option value="Dans 3 mois">Dans 3 mois</option>
                </select>
              </div>
              <div className="form-field full-width">
                <label>Expériences professionnelles *</label>
                <textarea 
                  value={newProfile.experiences} 
                  onChange={(e) => handleProfileInputChange('experiences', e.target.value)}
                  placeholder="Ex: Développeur Full Stack à TechCorp (2 ans), Développeur Backend à WebSolutions (1 an)"
                  rows="3"
                  required
                />
              </div>
              <div className="form-field full-width">
                <label>Poste recherché (optionnel)</label>
                <input 
                  type="text" 
                  value={newProfile.poste_recherche} 
                  onChange={(e) => handleProfileInputChange('poste_recherche', e.target.value)}
                  placeholder="Ex: Développeur Full Stack"
                />
              </div>
            </div>
            
            {addProfileSuccess && <p className="success-message">{addProfileSuccess}</p>}
            {addProfileError && <p className="error-message">Erreur : {addProfileError}</p>}
            
            <div className="form-actions">
              <button type="button" onClick={handleResetNewProfile} className="secondary-btn">Réinitialiser</button>
              <button type="submit" disabled={isLoading}>
                {isLoading ? 'Ajout en cours...' : 'Ajouter le profil'}
              </button>
            </div>
          </form>
        )}

        {error && <p className="error-message">Erreur : {error}</p>}

        {results.length > 0 && (
          <div className="results-container">
            <h2>Résultats du Matching</h2>
            <div className="results-grid">
              {results.map((profile) => (
                <div key={profile.id} className="profile-card">
                  <h3>Profil #{profile.id}</h3>
                  <p><strong>Score de pertinence :</strong> {Math.round(profile.score * 100)}%</p>
                  <p><strong>Expérience :</strong> {profile.exp_years} ans</p>
                  <p><strong>Localisation :</strong> {profile.localisation}</p>
                  <p><strong>Compétences :</strong> {profile.hard_skills}</p>
                  
                  {profile.explanation && (
                    <div className="explanation-section">
                      <h4>📊 Analyse du matching</h4>
                      <div className="scores-grid">
                        <div className="score-item">
                          <span className="score-label">Compétences</span>
                          <span className="score-value">{Math.round(profile.explanation.skills_match_score * 100)}%</span>
                        </div>
                        <div className="score-item">
                          <span className="score-label">Expérience</span>
                          <span className="score-value">{Math.round(profile.explanation.experience_match_score * 100)}%</span>
                        </div>
                      </div>
                      
                      <div className="strengths">
                        <h5>✅ Points forts</h5>
                        <ul>
                          {profile.explanation.strengths.map((strength, idx) => (
                            <li key={idx}>{strength}</li>
                          ))}
                        </ul>
                      </div>
                      
                      <div className="weaknesses">
                        <h5>⚠️ Points à améliorer</h5>
                        <ul>
                          {profile.explanation.weaknesses.map((weakness, idx) => (
                            <li key={idx}>{weakness}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                  
                  <details>
                    <summary>Voir le texte complet</summary>
                    <p className="full-text">{profile.full_text}</p>
                  </details>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
