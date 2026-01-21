# Fonctionnement du Projet d'Extraction de CV

Ce document détaille le fonctionnement technique du système d'extraction d'informations à partir de CV.

## 1. Architecture du Projet

```
Projet-Sopra-Steria/
├── backend/
│   ├── api.py                    # Point d'entrée API Flask
│   ├── analyser_cv.py            # Script hors-ligne pour tests
│   ├── requirements.txt
│   │
│   ├── extractors/               # 🔍 Extraction
│   │   ├── robust_extractor.py   # Pipeline principal
│   │   ├── spacy_extractor.py    # NER avec spaCy
│   │   ├── enhanced_extractor.py # Regex avancée
│   │   ├── heuristic_rules.py    # Règles intelligentes
│   │   ├── section_classifier.py # Classification sections
│   │   ├── version_mapper.py     # Conversion formats
│   │   └── config.py             # Configuration
│   │
│   ├── generators/               # 📝 Génération
│   │   ├── generate_sopra_docx.py # DOCX
│   │   └── docx_to_pdf.py        # Conversion DOCX→PDF
│   │
│   ├── models/                   # 🧠 Modèles spaCy
│   │   ├── cv_ner/
│   │   └── cv_pipeline/
│   │
│   ├── training/                 # 🎓 Entraînement
│   │   ├── train_ner.py
│   │   ├── train_pipeline.py
│   │   └── training_data.py
│   │
│   ├── data/
│   │   ├── input/                # CVs uploadés
│   │   └── output/               # JSON générés
│   │
│   └── test_*.py                 # Tests
│
├── frontend/                     # Interface React
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── utils/
│   │   └── styles/
│   └── ...
│
└── Docs/                         # Documentation
    ├── README_BACK.md
    ├── README_FRONT.md
    ├── fonctionnement_du_projet.md
    ├── NORMALISATION_CV.md
    ├── analyse_back.md
    └── CI.md
```

---

## 2. Flux d'Extraction Complet

### 2.1 Étape 1 : Upload et Réception

```
Frontend                          Backend (api.py)
   │                                │
   ├─ Sélection fichier CV          │
   │  (PDF ou DOCX)                 │
   │                                │
   └─────────────────────────────→  POST /api/cv/analyze
                                    └─ Stockage data/input/
```

**Validations** :
- ✅ Format autorisé : PDF ou DOCX
- ✅ Fichier non vide
- ✅ Pas de doublons simultanés

### 2.2 Étape 2 : Extraction de Texte Brut

```
PDF/DOCX (data/input/)
    ↓
robust_extractor.py
├─ PDF → pdfplumber (extraction texte)
└─ DOCX → python-docx (lecture paragraphes)
    ↓
Texte brut standardisé
```

### 2.3 Étape 3 : Pipeline d'Extraction (ROBUST)

Le cœur du système utilise **4 niveaux d'extraction** :

```
┌─────────────────────────────────────────────────┐
│  NIVEAU 1️⃣ : EXTRACTION REGEX                    │
├─────────────────────────────────────────────────┤
│ • Emails : regex@domain.com                     │
│ • Téléphones : +33 6 12 34 56 78                │
│ • URLs : linkedin.com/in/...                    │
│ • Dates : MM/YYYY, YYYY-YYYY, Mois YYYY        │
│ • Adresses : rue, code postal, ville           │
│ → Gérées par enhanced_extractor.py              │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  NIVEAU 2️⃣ : SPACY NER                           │
├─────────────────────────────────────────────────┤
│ • Noms personnels (PER)                         │
│ • Organisations/entreprises (ORG)               │
│ • Localités/villes (LOC)                        │
│ • Dates (DATE)                                  │
│ → Modèle : fr_core_news_md (spaCy)              │
│ → Gérées par spacy_extractor.py                 │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  NIVEAU 3️⃣ : RÈGLES HEURISTIQUES                 │
├─────────────────────────────────────────────────┤
│ • Segmentation sections (Expériences, Formations)│
│ • Détection contexte (type d'emploi)            │
│ • Association dates-entreprises                 │
│ → Gérées par heuristic_rules.py                 │
└─────────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────┐
│  NIVEAU 4️⃣ : FUZZY MATCHING                      │
├─────────────────────────────────────────────────┤
│ • Rapprochement données similaires              │
│ • Suppression doublons intelligente (rapidfuzz) │
│ • Normalisation des noms d'entreprises          │
│ → Gérées par section_classifier.py              │
└─────────────────────────────────────────────────┘
    ↓
JSON STRUCTURÉ VALIDÉ
```

### 2.4 Étape 4 : Structuration en JSON

```json
{
  "contact": {
    "nom": "Jean Dupont",
    "email": "jean@example.com",
    "telephone": "+33 6 12 34 56 78",
    "adresse": "5 Rue des Remparts, 69001 Lyon",
    "linkedin": "linkedin.com/in/jeandupont",
    "github": "github.com/jeandupont"
  },
  "experiences": [
    {
      "titre": "Développeur Python",
      "entreprise": "TechCorp",
      "date_debut": "2020-01",
      "date_fin": "2023-12",
      "description": "Développement de solutions backend...",
      "technologies": ["Python", "Flask", "PostgreSQL"]
    }
  ],
  "formations": [
    {
      "diplome": "Master Informatique",
      "ecole": "Université Paris Tech",
      "date_fin": "2020",
      "specialisation": "IA",
      "niveau": "Bac+5"
    }
  ],
  "competences": ["Python", "JavaScript", "Docker", "Kubernetes"],
  "langues": [
    {
      "langue": "Français",
      "niveau": "Natif"
    },
    {
      "langue": "Anglais",
      "niveau": "C1"
    }
  ]
}
```

### 2.5 Étape 5 : Stockage et Retour API

```
JSON Validé
    ↓
Stockage : data/output/CV_[NOM].json
    ↓
Réponse API
└─ Retour JSON au frontend
   └─ Affichage et édition possible
```

---

## 3. Pipeline Optionnel : Génération Documents

Après extraction (optionnel) :

```
JSON extraits
    ↓
1️⃣ GÉNÉRER DOCX
   └─ generate_sopra_docx.py
      └─ Formatage template Sopra Steria
         └─ data/output/CV_[NOM].docx
    ↓
2️⃣ CONVERTIR EN PDF
   └─ docx_to_pdf.py (via docx2pdf)
      └─ data/output/CV_[NOM].pdf
```

---

## 4. Détail des Modules Clés

### 4.1 robust_extractor.py (Orchestrateur Principal)

```python
def extract_cv_robust(file_path: str) -> Dict:
    """
    Pipeline principal d'extraction
    
    1. Extrait texte brut (PDF ou DOCX)
    2. Applique extraction regex (emails, téléphones, dates)
    3. Utilise spaCy NER (noms, organisations)
    4. Applique règles heuristiques (segmentation)
    5. Nettoie avec fuzzy matching
    6. Retourne JSON structuré
    """
```

### 4.2 spacy_extractor.py (NER)

- Modèle : `fr_core_news_md`
- Entités détectées : PER (personnes), ORG (organisations), LOC (lieux), DATE
- Fallback regex si NER insuffisant

### 4.3 heuristic_rules.py (Segmentation)

- Classification : Formation vs Expérience
- Association : dates ↔ entreprises/écoles
- Contexte : Détection type d'emploi, niveau, technos

### 4.4 section_classifier.py (Finalisation)

- Fuzzy matching (rapidfuzz) pour doublons
- Normalisation données
- Construction JSON final

---

## 5. Gestion des Erreurs

```
❌ Fichier invalide    → 400 Bad Request
❌ Format non supporté → 400 Bad Request
❌ Extraction échouée  → 500 Internal Server Error
❌ JSON corrompu       → Logging + tentative recovery
```

---

## 6. Performance et Optimisations

- **Regex compilées** : Réutilisées pour rapidité
- **spaCy pipeline** : Chargé une seule fois en mémoire
- **Fuzzy matching intelligent** : Limité aux données similaires
- **Traitement local** : Aucun appel API externe

---

## 7. Tests Disponibles

```bash
# Tests unitaires
pytest test_nom_prenom.py -v        # Extraction noms
pytest test_cv.py -v                # Pipeline complet
pytest test_cas_rue.py -v           # Cas spéciaux adresses
pytest test_integration.py -v       # Intégration complète
```

---

## 8. Extension Future

- **OCR** : Support PDF scannés via Tesseract
- **Multilingue** : Modèles spaCy anglais, espagnol, allemand
- **Templates personnalisés** : DOCX configurables par organisation
- **Webhooks** : Notifications post-analyse
