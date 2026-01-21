# 🎯 Projet Sopra Steria - Analyse et Génération Automatique de CV

## 📋 Description

Application complète d'analyse et de génération automatique de CV développée en partenariat avec **Sopra Steria**.

### ✨ Fonctionnalités

- 📄 **Import de CV** : Support PDF et DOCX
- 🔍 **Extraction intelligente** : NLP (spaCy) + règles heuristiques + regex
- 📊 **Analyse structurée** : Nom, contact, expériences, formations, compétences, langues, adresse, certifications
- 📝 **Génération automatique** : Documents DOCX et PDF au format Sopra Steria
- 🔒 **100% local** : Aucune donnée envoyée à des services externes
- 🌗 **Interface moderne** : React + Vite avec mode clair/sombre
- ⚡ **Performance optimale** : Pipeline d'extraction ultra-rapide

---

## 🏗️ Architecture

```
Projet-Sopra-Steria/
├── backend/                          # API Flask + Extraction NLP
│   ├── api.py                        # Point d'entrée API REST Flask
│   ├── requirements.txt              # Dépendances Python
│   │
│   ├── extractors/                   # Modules d'extraction
│   │   ├── robust_extractor.py       # Pipeline d'extraction principal
│   │   ├── spacy_extractor.py        # NER spaCy entraîné (noms, orgs)
│   │   ├── heuristic_rules.py        # Règles heuristiques avancées
│   │   ├── section_classifier.py     # Classification sections CV
│   │   ├── enhanced_extractor.py     # Extraction avancée (regex)
│   │   ├── version_mapper.py         # Conversion formats de données
│   │   └── config.py                 # Configuration des extracteurs
│   │
│   ├── generators/                   # Génération documents
│   │   ├── generate_sopra_docx.py    # Génération DOCX structuré
│   │   └── docx_to_pdf.py            # Conversion DOCX → PDF
│   │
│   ├── models/                       # Modèles spaCy entraînés
│   │   ├── cv_ner/                   # Modèle NER personnalisé
│   │   └── cv_pipeline/              # Pipeline complet
│   │
│   ├── training/                     # Scripts d'entraînement
│   │   ├── train_ner.py
│   │   ├── train_pipeline.py
│   │   └── training_data.py
│   │
│   ├── templates/                    # Templates DOCX
│   │   └── sopra_template.docx
│   │
│   ├── data/
│   │   ├── input/                    # Fichiers CV uploadés
│   │   └── output/                   # JSON générés
│   │
│   └── test_*.py                     # Tests unitaires et d'intégration
│
├── frontend/                         # Interface React + Vite
│   ├── src/
│   │   ├── components/               # Composants réutilisables
│   │   ├── pages/                    # Pages principales
│   │   ├── hooks/                    # Hooks React (dark mode, etc)
│   │   ├── assets/                   # Images, logos
│   │   ├── utils/                    # Utilitaires (constantes, API calls)
│   │   ├── styles/                   # Styles CSS/Tailwind
│   │   ├── App.jsx                   # Routing et structure app
│   │   └── main.jsx                  # Point d'entrée React
│   ├── public/                       # Assets statiques
│   ├── package.json
│   ├── tailwind.config.js            # Config Tailwind CSS
│   ├── vite.config.js                # Config Vite
│   ├── postcss.config.cjs
│   ├── eslint.config.js
│   └── index.html                    # Page HTML principale
│
├── Docs/                             # Documentation
│   ├── README_BACK.md
│   ├── README_FRONT.md
│   ├── fonctionnement_du_projet.md
│   ├── NORMALISATION_CV.md
│   ├── analyse_back.md
│   └── CI.md
│
└── README.md                         # Ce fichier
```

---

## 🚀 Installation

### Prérequis

- **Python 3.11+**
- **Node.js 18+** et npm
- **Windows, macOS ou Linux** (support complet)

### Backend

```bash
cd backend

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement (Windows)
venv\Scripts\activate

# Ou sur macOS/Linux
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Installer le modèle spaCy français
python -m spacy download fr_core_news_md
```

### Frontend

```bash
cd frontend

# Installer les dépendances
npm install
```

---

## ▶️ Lancement

### Backend (Terminal 1)

```bash
cd backend
venv\Scripts\activate      # (ou source venv/bin/activate sur Unix)
python api.py
```
→ API disponible sur **http://localhost:5000**

### Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```
→ Interface disponible sur **http://localhost:5173**

---

## 🔌 API Endpoints

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/cv/analyze` | Analyser un CV (PDF/DOCX) → retourne JSON |
| `GET` | `/api/cv/json/<filename>` | Télécharger le JSON généré |

### Exemple

```bash
curl -X POST -F "file=@mon_cv.pdf" http://localhost:5000/api/cv/analyze
```

**Réponse :**
```json
{
  "contact": {
    "nom": "Victor Hugo",
    "email": "victor@example.com",
    "telephone": "+33612345678",
    "adresse": "Paris, France"
  },
  "formations": [...],
  "experiences": [...],
  "competences": [...],
  "langues": [...],
  "json_filename": "CV_Victor_Hugo.json"
}
```

---

## 🧠 Pipeline de traitement

```
Upload CV (PDF/DOCX)
       ↓
Extraction texte brut
       ↓
┌──────────────────────────────────────────┐
│     EXTRACTION ROBUSTE (Robust)          │
│  • Regex : email, téléphone, dates       │
│  • spaCy NER : noms, organisations      │
│  • Heuristiques : sections, contexte    │
│  • Classification : formations/expérience│
└──────────────────────────────────────────┘
       ↓
JSON Structuré
       ↓
Stockage JSON (data/output)
```

---

## 🧪 Tests

```bash
cd backend

# Lancer tous les tests
pytest

# Tests spécifiques
pytest test_integration.py -v
pytest test_nom_prenom.py -v
pytest test_cv.py -v
```

---

## 📚 Documentation détaillée

- **[Backend](Docs/README_BACK.md)** - Architecture d'extraction, API endpoints, technologies
- **[Frontend](Docs/README_FRONT.md)** - Structure React, composants, styles Tailwind
- **[Fonctionnement du projet](Docs/fonctionnement_du_projet.md)** - Flux complet de traitement
- **[Normalisation CV](Docs/NORMALISATION_CV.md)** - Standards de structure et de champs
- **[Analyse backend](Docs/analyse_back.md)** - Détails techniques avancés

---

## 🔧 Technologies principales

### Backend
- **Flask** - Framework web Python
- **spaCy** - NLP et reconnaissance d'entités nommées
- **python-docx** - Manipulation DOCX
- **dateparser** - Parsing de dates multilingues
- **rapidfuzz** - Fuzzy matching et comparaison de texte

### Frontend
- **React 19** - Interface utilisateur
- **Vite** - Bundler ultra-rapide
- **React Router DOM** - Navigation multi-pages
- **Tailwind CSS** - Styling responsive
- **Lucide React** - Icônes vectorielles

---

## 🎨 Thème et Design

- **Couleur primaire** : rgb(221, 83, 52) / #DD5334
- **Dégradé** : linear-gradient(90deg, #880015, #FF5614)
- **Police** : Raleway (générale), Manrope (titres)
- **Mode** : Clair 🌞 / Sombre 🌙 (persistant avec localStorage)
- **Design** : Responsive, optimisé pour desktop & mobile

---

## 👥 Contributeurs

- Safae Berrichi
- Dorian Lo Negro
- Thomas Gaugeais
- Julien Thepaut
- Nehade El Mokhtari
- Clément

---

## 📜 Licence

Projet réalisé dans le cadre d'un partenariat pédagogique avec **Sopra Steria**.  
Tous droits réservés.
