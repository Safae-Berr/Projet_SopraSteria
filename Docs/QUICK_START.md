# ⚡ QUICK START - Pipeline Hybride

## 3 étapes pour mettre en place le pipeline hybride

### ✅ Étape 1 : Valider l'installation
```bash
python validate_hybrid_setup.py
```

Vous devriez voir :
```
✅ VALIDATION RÉUSSIE - Vous êtes prêt à déployer ! 🚀
```

### ✅ Étape 2 : Tester avec les CVs réels
```bash
# Test avec Adèle (CV mal structuré)
python test_hybrid_extraction.py data/input/CV-Adele_PATAROT.pdf

# Test avec Leo (CV bien structuré)
python test_hybrid_extraction.py data/input/CV_LEO_WEBER_1.pdf

# Test avec JLA (CV bien structuré)
python test_hybrid_extraction.py data/input/CV_JLA_202504.docx
```

### ✅ Étape 3 : C'est prêt !

L'API utilise **automatiquement** le pipeline hybride :
```bash
python api.py
```

---

## 📁 Fichiers créés

| Fichier | Type | Description |
|---------|------|-------------|
| `extractors/hybrid_extractor.py` | Code | Pipeline hybride principal |
| `extractors/hybrid_config.py` | Config | Configuration personnalisable |
| `test_hybrid_extraction.py` | Test | Tests complets |
| `validate_hybrid_setup.py` | Validation | Diagnostic d'installation |
| `HYBRID_EXTRACTION_GUIDE.md` | Doc | Guide complet |
| `QUICK_START.md` | Doc | Ce fichier |
| `EXAMPLES_COPY_PASTE.md` | Doc | 12 exemples prêts |
| `DEPLOYMENT_GUIDE.md` | Doc | Guide production |
| `README_HYBRID.md` | Doc | Résumé final |

---

## 🎯 Points clés

✅ **100% compatible** avec votre code existant
✅ **Pas de breaking changes** - tout continue de fonctionner
✅ **Transparent pour le frontend** - aucun changement requis
✅ **Pas de réentraînement** - utilise les modèles existants
✅ **Production-ready** - logs, validation, error handling

---

## 🚀 Prochaines étapes

1. Valider : `python validate_hybrid_setup.py`
2. Tester : `python test_hybrid_extraction.py <cv.pdf>`
3. Déployer : `python api.py`

C'est tout ! 🎉

