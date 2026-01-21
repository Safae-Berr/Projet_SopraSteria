# Documentation : Normalisation CV et Conversion de Format

## 🎯 Objectif

Ce document décrit le processus de **normalisation et conversion de CV** entre différents formats au sein du système.

---

## 📐 Schéma JSON Standardisé (v2.0)

Tous les CV extraits sont normalisés selon ce schéma :

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
      "niveau": "string (Bac+3, Master, etc)"
    }
  ],
  "competences": ["string"],
  "certifications": [
    {
      "nom": "string",
      "organisme": "string",
      "date": "YYYY-MM"
    }
  ],
  "langues": [
    {
      "langue": "string",
      "niveau": "string (Natif, Courant, Intermédiaire, Basique)"
    }
  ],
  "projets": [
    {
      "nom": "string",
      "description": "string",
      "technologies": ["string"]
    }
  ]
}
```

---

## 🔄 Conversions de Format Supportées

### 1. PDF → JSON

```
PDF (data/input/)
    ↓
pdfplumber.open() - Extraction texte
    ↓
robust_extractor.py - Pipeline complet
    ↓
JSON Standardisé (data/output/)
```

**Avantages** :
- Préservation complète du contenu textuel
- Gestion des documents multi-pages
- Pas de perte de formatage critique

### 2. DOCX → JSON

```
DOCX (data/input/)
    ↓
python-docx - Lecture paragraphes/tableaux
    ↓
robust_extractor.py - Pipeline complet
    ↓
JSON Standardisé (data/output/)
```

**Avantages** :
- Extraction de structure (listes, tableaux)
- Accès direct au texte formaté
- Métadonnées DOCX exploitables

### 3. JSON → DOCX

```
JSON Standardisé
    ↓
generate_sopra_docx.py - Formatage
    ↓
Template Sopra (templates/sopra_template.docx)
    ↓
DOCX Généré (data/output/CV_[NOM].docx)
```

**Caractéristiques** :
- ✅ Format Sopra Steria branding
- ✅ Mise en page professionnelle
- ✅ Couleurs et polices standardisées
- ✅ Métadonnées complètes

### 4. DOCX → PDF

```
DOCX Généré
    ↓
docx_to_pdf.py
    ├─ pythoncom.CoInitialize() (Windows COM)
    ├─ docx2pdf.convert()
    └─ pythoncom.CoUninitialize()
    ↓
PDF (data/output/CV_[NOM].pdf)
```

**Dépendances** :
- `docx2pdf` library
- `pythoncom` (Windows)
- Microsoft Word (optionnel, utilise LibreOffice en fallback sur Linux)

---

## 🧹 Normalisation des Données

### Dates

| Format d'entrée | Normalisation | Exemple |
|-----------------|---------------|---------|
| `06/2016` | `YYYY-MM` | `2016-06` |
| `Juin 2019` | `YYYY-MM` | `2019-06` |
| `2017-2019` | Plage convertie | `2017-01 à 2019-12` |
| `2020-01-15` | ISO date | `2020-01` |

**Parsing via** : `dateparser` library (multilingue)

### Adresses

| Cas | Traitement |
|-----|-----------|
| "5 rue des Remparts, 69001 Lyon" | Complet préservé |
| "Paris, France" | Complété si possible |
| "Télétravail" | Marqué comme `remote` |

### Téléphones

| Format d'entrée | Normalisé |
|-----------------|-----------|
| `06 12 34 56 78` | `+33 6 12 34 56 78` |
| `+33612345678` | `+33 6 12 34 56 78` |
| `07.65.43.21.09` | `+33 7 65 43 21 09` |

### Emails

- Extraction simple : `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}`
- Nettoyage : suppression espaces, conversion minuscules
- Déduplication : fuzzy matching `rapidfuzz`

### Compétences

| Catégorie | Normalisation |
|-----------|---------------|
| Techniques | "Python" → "Python" |
| Outils | "Docker" → "Docker" |
| Méthodologies | "Agile" → "Agile" |

**Fuzzy matching** : `rapidfuzz` pour regrouper variantes ("js" = "JavaScript")

---

## 📝 Module version_mapper.py

Gère la conversion entre anciens et nouveaux formats.

### Fonctions Clés

```python
def normalize_old_cv_to_new(old_cv_dict: Dict) -> Dict:
    """
    Convertit ancien format → nouveau format v2.0
    """

def convert_v2_to_old_format(new_cv_dict: Dict) -> Dict:
    """
    Convertit nouveau format → ancien format (backward compatibility)
    """
```

---

## ⚙️ Configuration et Constantes

**Fichier** : `extractors/config.py`

```python
# Formats de dates acceptés
DATEFORMATS = ['DD/MM/YYYY', 'MM/YYYY', 'YYYY-YYYY', 'MOIS YYYY']

# Modèle spaCy
SPACY_MODEL = 'fr_core_news_md'

# Seuil de fuzzy matching
FUZZY_THRESHOLD = 80  # Similitude en %

# Extensions autorisées
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
```

---

## 🔗 Flux Complet : Upload → JSON → DOCX → PDF

```
┌─────────────────────────────────────────┐
│  1️⃣ FRONTEND : Upload CV                 │
└─────────────────────────────────────────┘
            ↓ (POST /api/cv/analyze)
┌─────────────────────────────────────────┐
│  2️⃣ BACKEND : Extraction → JSON         │
│  • robust_extractor.py                  │
│  • Stockage data/output/                │
└─────────────────────────────────────────┘
            ↓ (Affichage frontend)
┌─────────────────────────────────────────┐
│  3️⃣ UTILISATEUR : Édition JSON (optionnel) │
└─────────────────────────────────────────┘
            ↓ (POST /api/cv/generate-docx)
┌─────────────────────────────────────────┐
│  4️⃣ GÉNÉRATION DOCX                     │
│  • generate_sopra_docx.py               │
│  • Template Sopra branding              │
└─────────────────────────────────────────┘
            ↓ (POST /api/cv/convert-docx-to-pdf)
┌─────────────────────────────────────────┐
│  5️⃣ CONVERSION DOCX → PDF               │
│  • docx_to_pdf.py (docx2pdf)            │
│  • Stockage data/output/                │
└─────────────────────────────────────────┘
            ↓ Download
┌─────────────────────────────────────────┐
│  6️⃣ FRONTEND : Téléchargement           │
│  • CV_[NOM].pdf                         │
│  • CV_[NOM].docx                        │
└─────────────────────────────────────────┘
```

---

## 🧪 Validation et Tests

### Tests de Normalisation

```bash
pytest test_nom_prenom.py -v       # Extraction noms corrects
pytest test_cas_rue.py -v          # Adresses spéciales
pytest test_cv.py -v               # Cas complets
pytest test_integration.py -v      # Flux complet
```

### Validation Schéma JSON

Chaque JSON retourné respecte le schéma v2.0 validé via :
- Type checking (contact dict, experiences list, etc)
- Regex validation (emails, téléphones)
- Date format checking (YYYY-MM)

---

## 📊 Statistiques et Monitoring

Pour chaque extraction :
- Temps de traitement
- Nombre de champs extraits
- Taux de confiance par section
- Erreurs/avertissements

---

## 🔮 Évolutions Futures

- [ ] Support multilangue (anglais, espagnol, allemand)
- [ ] Import depuis LinkedIn API
- [ ] Fusion multiple CVs
- [ ] Migration assistée ancien → nouveau format
- [ ] Templates DOCX personnalisables par client
