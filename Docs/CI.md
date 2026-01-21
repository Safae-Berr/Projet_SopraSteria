# Documentation du Workflow CI/CD

Ce document décrit le pipeline d'intégration continue automatisé du projet.

---

## 🎯 Vue d'ensemble

Le workflow CI est défini dans `.github/workflows/ci.yml` et s'exécute à chaque `push` sur `main`.

Il utilise une architecture **monorepo** avec tests/build indépendants pour :
- ✅ **Backend** (Python 3.11 + pytest)
- ✅ **Frontend** (Node.js 20 + ESLint + Vite)

---

## 🔄 Déclenchement

| Événement | Condition |
|-----------|-----------|
| `push` | Sur branche `main` |
| Fichiers | `backend/**` ou `frontend/**` |
| Fréquence | À chaque commit |

---

## 📋 Jobs du Workflow

### 1️⃣ JOB : `filter`

**Rôle** : Détecter quels dossiers ont changé

```yaml
- dorny/paths-filter@v2
  - Vérifie backend/** → flag: backend_changed
  - Vérifie frontend/** → flag: frontend_changed
```

**Utilité** : Optimiser ressources (ne tester que ce qui change)

---

### 2️⃣ JOB : `backend-ci`

**Condition** : Exécuté seulement si `backend_changed == true`

**Environnement** :
- OS : `ubuntu-latest`
- Python : `3.11`
- Répertoire : `backend/`

**Étapes** :

```yaml
1. Checkout
   └─ Récupère le code du dépôt

2. Setup Python 3.11
   └─ Installation runtime Python

3. Install pip 23.3.1
   └─ Gestionnaire de paquets à jour

4. Install Dependencies
   └─ pip install -r requirements.txt
      ├─ Flask
      ├─ spaCy
      ├─ python-docx
      ├─ pdfplumber
      ├─ rapidfuzz
      ├─ docx2pdf
      └─ pytest

5. Download spaCy Model
   └─ python -m spacy download fr_core_news_md
      (Modèle français pour NER)

6. Run Tests
   └─ pytest
      ├─ test_nom_prenom.py
      ├─ test_cas_rue.py
      ├─ test_cv.py
      └─ test_integration.py
```

**Résultat** :
- ✅ PASS : Tous tests réussis
- ❌ FAIL : Test échoué (bloc le push)

---

### 3️⃣ JOB : `frontend-ci`

**Condition** : Exécuté seulement si `frontend_changed == true`

**Environnement** :
- OS : `ubuntu-latest`
- Node.js : `20.x`
- Répertoire : `frontend/`

**Étapes** :

```yaml
1. Checkout
   └─ Récupère le code du dépôt

2. Setup Node.js 20
   └─ Installation runtime Node

3. Install Dependencies
   └─ npm install
      ├─ React 19
      ├─ Vite
      ├─ TailwindCSS
      ├─ ESLint
      └─ Autres dépendances

4. Lint
   └─ npm run lint
      ├─ Vérification syntaxe
      ├─ Style code
      ├─ Règles ESLint
      └─ Avertissements

5. Build Production
   └─ npm run build
      ├─ Compilation Vite
      ├─ Optimisation bundles
      ├─ Minification CSS/JS
      ├─ Génération dist/
      └─ Vérification taille
```

**Résultat** :
- ✅ PASS : Build réussi, pas d'erreur lint
- ❌ FAIL : Erreur lint ou build (bloc le push)

---

## 📊 Status Check

Le workflow peut avoir 3 états :

| État | Description | Action |
|------|-------------|--------|
| 🟢 **Pass** | Tous jobs réussis | Merge autorisé |
| 🔴 **Fail** | Au moins un job échoué | Merge bloqué |
| ⚪ **Skipped** | Aucun fichier changé | Sans impact |

---

## ⏱️ Durée Typical

- **Backend CI** : ~60-90 secondes
  - Installation dépendances : ~30s
  - Téléchargement spaCy : ~20s
  - Exécution tests : ~20-40s
  
- **Frontend CI** : ~40-60 secondes
  - Installation dépendances : ~20s
  - Lint + Build : ~20-40s

**Total** : ~100-150 secondes (parallélisé)

---

## 📝 Configuration `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]

jobs:
  filter:
    runs-on: ubuntu-latest
    outputs:
      backend: ${{ steps.filter.outputs.backend }}
      frontend: ${{ steps.filter.outputs.frontend }}
    steps:
      - uses: actions/checkout@v3
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            backend:
              - 'backend/**'
            frontend:
              - 'frontend/**'

  backend-ci:
    needs: filter
    if: ${{ needs.filter.outputs.backend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install pip
        run: |
          python -m pip install --upgrade pip==23.3.1
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          python -m spacy download fr_core_news_md
      - name: Run tests
        run: pytest

  frontend-ci:
    needs: filter
    if: ${{ needs.filter.outputs.frontend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: npm install
      - name: Run linter
        run: npm run lint
      - name: Build project
        run: npm run build
```

---

## 🔧 Commandes Manuelles Équivalentes

### Backend Local

```bash
cd backend

# Installation
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate (Windows)
pip install -r requirements.txt
python -m spacy download fr_core_news_md

# Tests
pytest -v
```

### Frontend Local

```bash
cd frontend

# Installation
npm install

# Linter
npm run lint

# Build
npm run build
```

---

## 🚨 Dépannage CI/CD

### ❌ Backend CI échoue

| Symptôme | Cause | Solution |
|----------|-------|----------|
| `ModuleNotFoundError` | Dépendance manquante | Ajouter à `requirements.txt` |
| `spaCy model not found` | Modèle non téléchargé | Vérifier étape download spaCy |
| `pytest failed` | Test échoué | Voir logs test, corriger code |
| `timeout` | Trop lent | Optimiser tests ou augmenter timeout |

### ❌ Frontend CI échoue

| Symptôme | Cause | Solution |
|----------|-------|----------|
| `npm ERR!` | Dépendance incompatible | `npm ci` au lieu de `npm install` |
| `ESLint errors` | Code non conforme | `npm run lint -- --fix` |
| `Build failed` | Erreur de compilation | Vérifier `vite.config.js` |

---

## 🔐 Best Practices

✅ **À faire** :
- Committer des tests en même temps que le code
- Garder les tests rapides (<5 secondes)
- Utiliser des fixtures pour isolation
- Documenter les dépendances

❌ **À éviter** :
- Pousser du code cassé sur `main`
- Tests flaky (parfois pass, parfois fail)
- Ignorances des erreurs lint
- Augmenter inutilement les timeouts

---

## 📈 Monitoring

Les builds sont visibles sur :
- ✅ GitHub Actions tab
- ✅ Badge dans README.md
- ✅ Notifications PR (si applicable)

### Ajouter un badge README

```markdown
![CI Status](https://github.com/DorianLn/Projet-Sopra-Steria/workflows/CI/badge.svg)
```

---

## 🔮 Évolutions Futures

- [ ] Coverage reporter (pytest-cov)
- [ ] SonarQube integration
- [ ] Deployment automation
- [ ] Performance benchmarks
- [ ] Security scanning (bandit, npm audit)
- [ ] Database migration tests

