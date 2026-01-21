# 📚 Backend – Analyse et Génération Automatique de CV

## 📋 Description

Ce backend a été développé dans le cadre d'un projet étudiant en partenariat avec **Sopra Steria**.  
Son objectif est d'automatiser le traitement de CV non structurés (PDF ou DOCX) afin de :

- simplifier l'analyse des informations d'un candidat,
- standardiser la présentation de ces données,
- générer automatiquement des documents professionnels (DOCX & PDF),
- tout en respectant les contraintes de **confidentialité** (traitement 100% local).

L'application analyse un CV grâce à un **pipeline robuste** mêlant expressions régulières, NLP (spaCy), classification heuristique et fuzzy matching.

---

## ✨ Fonctionnalités

### ✔ Fonctionnalités principales (implémentées)

- ✅ Import de CV **PDF** ou **DOCX**
- ✅ Extraction d'informations complètes :
  - **Contact** : Nom, email, téléphone, adresse postale, LinkedIn, GitHub
  - **Expériences** : Titre, entreprise, dates, description, technos
  - **Formations** : Diplôme, école, dates, niveau
  - **Compétences** : Techniques, métiers, outils, langages
  - **Certifications** : Nom, organisme, date
  - **Langues** : Langue, niveau
  - **Projets** : Titre, description, technologies
- ✅ Analyse NLP via **spaCy** (NER + classification texte)
- ✅ Règles heuristiques intelligentes pour segmentation
- ✅ Fuzzy matching pour normalisation des données
- ✅ Export automatique en **JSON structuré**
- ✅ API RESTful complète
- ✅ Gestion des fichiers temporaires
- ✅ Traitement **100% local** (aucune API externe)

### 📋 Fonctionnalités futures (à implémenter)

- [ ] Génération automatique DOCX (template Sopra)
- [ ] Conversion DOCX → PDF (branding Sopra Steria)
- [ ] Conversion PDF d'entrée → DOCX

---

## 🛠️ Technologies

| Domaine | Outils |
|---------|--------|
| **Framework** | Flask, Flask-CORS |
| **Extraction** | Regex, spaCy (fr_core_news_md) |
| **Manipulation docs** | python-docx, docxtpl, PyPDF2 |
| **Conversion** | docx2pdf, win32com |
| **NLP avancé** | rapidfuzz, dateparser |
| **Génération PDF** | ReportLab |
| **Tests** | pytest |

---

## 📂 Architecture

```
backend/
│
├── api.py                       # Point d'entrée API Flask
├── requirements.txt             # Dépendances Python
│
├── extractors/                  # 🔍 Modules d'extraction
│   ├── robust_extractor.py      # Pipeline d'extraction PRINCIPAL
│   ├── spacy_extractor.py       # NER spaCy + classification
│   ├── enhanced_extractor.py    # Extraction regex avancée
│   ├── heuristic_rules.py       # Règles heuristiques
│   ├── section_classifier.py    # Classification sections
│   ├── version_mapper.py        # Conversion formats de données
│   └── config.py                # Configuration centralisée
│
├── generators/                  # 📝 Génération documents
│   ├── generate_sopra_docx.py   # DOCX standardisé
│   └── docx_to_pdf.py           # Conversion DOCX → PDF
│
├── models/                      # 🧠 Modèles spaCy
│   ├── cv_ner/                  # Modèle NER personnalisé
│   └── cv_pipeline/             # Pipeline complet
│
├── training/                    # 🎓 Scripts d'entraînement
│   ├── train_ner.py
│   ├── train_pipeline.py
│   ├── train_textcat.py
│   ├── generate_training_data.py
│   └── training_data.py
│
├── templates/                   # 📋 Templates DOCX
│   └── sopra_template.docx
│
├── data/                        # 📊 Données
│   ├── input/                   # CV uploadés
│   └── output/                  # JSON générés
│
└── test_*.py                    # 🧪 Tests
    ├── test_integration.py
    ├── test_cv.py
    ├── test_nom_prenom.py
    ├── test_cas_rue.py
    └── ...
```

---

## 🚀 Installation & Configuration

### 1. Cloner le projet

```bash
git clone https://github.com/DorianLn/Projet-Sopra-Steria.git
cd Projet-Sopra-Steria/backend
```

### 2. Créer l'environnement Python

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Installer le modèle spaCy français

```bash
python -m spacy download fr_core_news_md
```

### 5. Lancer le serveur API

```bash
python api.py
```

✅ L'API démarre sur **http://localhost:5000**

---

## 🔌 Endpoints API

### 1️⃣ Analyser un CV

**`POST /api/cv/analyze`**

**Body** : FormData avec le fichier

```bash
curl -X POST -F "file=@mon_cv.pdf" http://localhost:5000/api/cv/analyze
```

**Réponse :**
```json
{
  "contact": {
    "nom": "Jean Dupont",
    "email": "jean.dupont@email.com",
    "telephone": "+33612345678",
    "adresse": "Paris, France",
    "linkedin": "linkedin.com/in/jeandupont"
  },
  "experiences": [
    {
      "titre": "Développeur Senior",
      "entreprise": "Tech Corp",
      "date_debut": "2020-01",
      "date_fin": "Présent",
      "description": "Développement backend...",
      "technologies": ["Python", "Flask", "PostgreSQL"]
    }
  ],
  "formations": [
    {
      "diplome": "Master Informatique",
      "ecole": "Université Paris Tech",
      "date_fin": "2019",
      "specialisation": "Intelligence Artificielle"
    }
  ],
  "competences": ["Python", "JavaScript", "Machine Learning"],
  "langues": [
    {
      "langue": "Français",
      "niveau": "Natif"
    }
  ],
  "json_filename": "CV_Jean_Dupont.json"
}
```

### 2️⃣ Télécharger le JSON

**`GET /api/cv/json/<filename>`**

Récupère le fichier JSON structuré généré lors de l'analyse

### 3️⃣ Générer DOCX depuis JSON

**`POST /api/cv/generate-docx`**

Génère un DOCX structuré au format Sopra Steria à partir du JSON extrait

### 4️⃣ Convertir DOCX → PDF

**`POST /api/cv/convert-docx-to-pdf`**

Convertit un DOCX généré en PDF avec branding Sopra Steria

---

## 🧠 Pipeline d'extraction

```
Input CV (PDF/DOCX)
    ↓
Extraction texte brut
    ↓
┌─────────────────────────────────────────┐
│   ROBUST EXTRACTOR (Pipeline Principal) │
│                                         │
│  1️⃣ REGEX EXTRACTION                    │
│     • Emails, téléphones, URLs          │
│     • Dates (multiples formats)         │
│     • Adresses postales                 │
│                                         │
│  2️⃣ SPACY NER                           │
│     • Noms, prénoms                     │
│     • Organisations (entreprises)       │
│     • Localités                         │
│                                         │
│  3️⃣ HEURISTIC RULES                     │
│     • Segmentation sections             │
│     • Détection formations/expériences  │
│     • Normalisation contexte            │
│                                         │
│  4️⃣ FUZZY MATCHING                      │
│     • Rapprochement données             │
│     • Suppression doublons              │
└─────────────────────────────────────────┘
    ↓
JSON Structuré validé
    ↓
Stockage JSON (data/output)
```

---

## 📋 Structure des données (JSON output)

```json
{
  "contact": {
    "nom": "string",
    "email": "string",
    "telephone": "string",
    "adresse": "string",
    "linkedin": "string",
    "github": "string"
  },
  "experiences": [
    {
      "titre": "string",
      "entreprise": "string",
      "date_debut": "YYYY-MM",
      "date_fin": "YYYY-MM ou 'Présent'",
      "description": "string",
      "technologies": ["string"]
    }
  ],
  "formations": [
    {
      "diplome": "string",
      "ecole": "string",
      "date_fin": "YYYY-MM",
      "specialisation": "string",
      "niveau": "string"
    }
  ],
  "competences": ["string"],
  "langues": [
    {
      "langue": "string",
      "niveau": "string (Natif, Courant, Intermédiaire, Basique)"
    }
  ]
}
```

---

## 🧪 Tests

```bash
cd backend

# Tous les tests
pytest -v

# Avec couverture
pytest --cov=. --cov-report=html

# Tests spécifiques
pytest test_integration.py -v
pytest test_nom_prenom.py -v
pytest test_cv.py -v
pytest test_cas_rue.py -v
```

---

## 🔄 Réentraîner les modèles

Les modèles spaCy personnalisés sont dans `models/cv_ner/` et `models/cv_pipeline/`.

```bash
cd backend

# Réentraîner le NER
python training/train_ner.py

# Réentraîner le pipeline
python training/train_pipeline.py

# Générer les données d'entraînement
python training/generate_training_data.py
```

---

## 🚀 Améliorations futures

- [ ] OCR pour PDF scannés
- [ ] Support multilingue (EN, ES, DE)
- [ ] API documentation Swagger/OpenAPI
- [ ] Authentification et historique utilisateur
- [ ] Templates DOCX personnalisables
- [ ] Export JSON schema validation
- [ ] Cache et optimisation performance
- [ ] Webhooks pour intégrations

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
