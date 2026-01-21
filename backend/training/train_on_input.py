"""
Pipeline d'entraînement sur les CV réels (backend/data/input).
- Analyse chaque fichier .pdf/.docx via extractors.robust_extractor.extract_cv_robust
- Sauve les JSON dans backend/data/output
- Génère les exemples NER avec generate_training_data.py
- Entraîne en deux étapes : manuel -> fine-tune (manuel + générés)

Usage:
    python train_on_input.py
"""
from pathlib import Path
import json
import importlib
import sys

ROOT = Path(__file__).parent.parent
INPUT_DIR = ROOT / "data" / "input"
OUTPUT_DIR = ROOT / "data" / "output"
TRAINING_DIR = ROOT / "training"

# Ajouter le dossier backend au path pour importer les modules du package
sys.path.insert(0, str(ROOT))

print("[train_on_input] Début du pipeline d'entraînement sur les CV d'entrée...")

# 1) Analyser les fichiers d'entrée
from extractors.robust_extractor import extract_cv_robust

processed = 0
for path in sorted(INPUT_DIR.glob("*")):
    if path.suffix.lower() not in (".pdf", ".docx"):
        continue
    out_name = path.stem
    out_json = OUTPUT_DIR / f"{out_name}.json"

    try:
        # Si JSON existe, on le remplace pour s'assurer d'utiliser la même logique
        result = extract_cv_robust(str(path))
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[train_on_input] Analyse et sauvegarde: {path.name} -> {out_json.name}")
        processed += 1
    except Exception as e:
        print(f"[train_on_input] Erreur analyse {path.name}: {e}")

print(f"[train_on_input] Analyse terminée : {processed} fichiers traités.")

# 2) Générer les exemples NER automatiquement
print("[train_on_input] Génération des exemples NER via generate_training_data.py...")
try:
    gen_module = importlib.import_module('training.generate_training_data')
    importlib.reload(gen_module)
    # appeler main() pour écrire generated_data.py
    gen_module.main()
    print("[train_on_input] génération terminée.")
except Exception as e:
    print(f"[train_on_input] Erreur lors de la génération: {e}")

# 3) Préparer jeux et entraînement en deux étapes
print("[train_on_input] Préparation et entraînement en deux étapes (manuel -> fine-tune)")
import training.training_data as td
# Tentative d'import spaCy pour vérifier l'alignement des offsets
try:
    import spacy
    from spacy.training.iob_utils import offsets_to_biluo_tags
    _HAS_SPACY = True
    _NLP = spacy.blank("fr")
except Exception:
    _HAS_SPACY = False
    _NLP = None


def filter_aligned_examples(examples):
    """Garde uniquement les exemples dont les entités s'alignent sur la tokenisation spaCy.

    Si spaCy n'est pas disponible, retourne la liste d'origine.
    """
    if not _HAS_SPACY or _NLP is None:
        return examples

    kept = []
    rejected = []
    for text, ann in examples:
        entities = ann.get('entities', [])
        try:
            tags = offsets_to_biluo_tags(_NLP.make_doc(text), entities)
            if any(t == '-' for t in tags):
                rejected.append((text, ann))
            else:
                kept.append((text, ann))
        except Exception:
            rejected.append((text, ann))

    if rejected:
        print(f"[train_on_input] {len(rejected)} exemples rejetés pour mauvais alignement (spaCy)")
        for t, a in rejected[:3]:
            print(f" - Rejet: {t[:60]!s}... -> {a.get('entities', [])}")

    return kept

# Charger les exemples générés si présents
generated = []
try:
    gendata = importlib.import_module('training.generated_data')
    importlib.reload(gendata)
    generated = getattr(gendata, 'GENERATED_NER_DATA', [])
except Exception:
    generated = []

# Serialisation simple pour comparaison (texte + str(entities))
def serialize_example(ex):
    text, ann = ex
    return text + '||' + str(ann.get('entities', []))

generated_set = set(serialize_example(x) for x in generated)

# Construire manuel_only en retirant les exemples générés de NER_TRAINING_DATA
current_all = list(td.NER_TRAINING_DATA)
manual_only = [ex for ex in current_all if serialize_example(ex) not in generated_set]

# Filtrer les exemples mal alignés (manuel + générés)
manual_only_filtered = filter_aligned_examples(manual_only)
generated_filtered = filter_aligned_examples(generated)

print(f"[train_on_input] Exemples manuels détectés: {len(manual_only)} (après filtrage: {len(manual_only_filtered)})")
print(f"[train_on_input] Exemples générés détectés: {len(generated)} (après filtrage: {len(generated_filtered)})")
print(f"[train_on_input] Total actuel dans training_data: {len(current_all)}")

# Remplacer dynamiquement td.NER_TRAINING_DATA pour les deux étapes et recharger train_ner
# Étape 1: entraîner sur manuel_only
print("[train_on_input] Étape 1: entraînement sur les exemples manuels (pré-entrainement)")

td.NER_TRAINING_DATA = manual_only_filtered

# recharger le module train_ner pour qu'il prenne la nouvelle variable lors de l'import
if 'training.train_ner' in sys.modules:
    importlib.reload(importlib.import_module('training.train_ner'))
train_ner_mod = importlib.import_module('training.train_ner')
importlib.reload(train_ner_mod)

try:
    model_stage1 = ROOT / 'models' / 'cv_ner_stage1'
    train_ner_mod.train_ner(base_model='blank:fr', output_dir=str(model_stage1), n_iter=20)
    print(f"[train_on_input] Étape 1 terminée, modèle sauvegardé dans: {model_stage1}")
except Exception as e:
    print(f"[train_on_input] Erreur pendant étape 1: {e}")

# Étape 2: fine-tune sur manuel + générés (jeu complet)
print("[train_on_input] Étape 2: fine-tune sur jeu complet (manuel + générés)")
full = manual_only_filtered + generated_filtered
if not full:
    print("[train_on_input] Aucune donnée disponible pour l'étape 2. Fin.")
else:
    td.NER_TRAINING_DATA = full
    # recharger train_ner
    importlib.reload(importlib.import_module('training.train_ner'))
    train_ner_mod = importlib.import_module('training.train_ner')
    importlib.reload(train_ner_mod)

    try:
        model_final = ROOT / 'models' / 'cv_ner_final'
        # utiliser le modèle stage1 comme base si disponible
        base = str(model_stage1) if model_stage1.exists() else 'blank:fr'
        train_ner_mod.train_ner(base_model=base, output_dir=str(model_final), n_iter=10)
        print(f"[train_on_input] Étape 2 terminée, modèle final sauvegardé dans: {model_final}")
    except Exception as e:
        print(f"[train_on_input] Erreur pendant étape 2: {e}")

print("[train_on_input] Pipeline terminé.")
