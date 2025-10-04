import React, { useState } from 'react';
import './App.css';

function App() {
  const [offerText, setOfferText] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [searchType, setSearchType] = useState('simple'); // 'simple' or 'advanced'
  const [poste, setPoste] = useState('');
  const [competences, setCompetences] = useState('');
  const [experience, setExperience] = useState('');
  const [localisation, setLocalisation] = useState('');
  const [typeDeContrat, setTypeDeContrat] = useState('');
  const [salaire, setSalaire] = useState('');

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
  }

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
        </div>

        {searchType === 'simple' ? (
          <form onSubmit={handleSubmit} className="offer-form">
            <textarea
              value={offerText}
              onChange={(e) => setOfferText(e.target.value)}
              placeholder="Ex: 'Je cherche un développeur Python spécialisé en fintech avec 3 ans d’expérience au Sénégal'"
              rows="5"
            />
            <button type="submit" disabled={isLoading || !offerText.trim()}>
              {isLoading ? 'Recherche en cours...' : 'Trouver les talents'}
            </button>
          </form>
        ) : (
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
