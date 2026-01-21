"""
Script d'entraînement du NER spaCy personnalisé pour l'extraction de CV.

Version améliorée :
- supporte base_model 'blank:fr' pour tests rapides
- split optionnel train/val/test (import paresseux sklearn)
- nettoyage des entités chevauchantes avant création des Example
- évaluation sur val/test (precision, recall, f1)
- sauvegarde training_meta.json
"""

import os
import sys
import random
import json
from pathlib import Path
from datetime import datetime

import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding

# ajouter dossier parent
sys.path.insert(0, str(Path(__file__).parent.parent))
from training.training_data import NER_TRAINING_DATA, get_ner_labels, validate_training_data


def normalize_entities(entities):
    """Supprime/résout les chevauchements en gardant les spans les plus longs."""
    if not entities:
        return []
    ents = [(int(s), int(e), str(l)) for s, e, l in entities]
    ents.sort(key=lambda x: (x[0], -x[1]))
    result = []
    for s, e, l in ents:
        if s >= e:
            continue
        if not result:
            result.append((s, e, l))
            continue
        last_s, last_e, last_l = result[-1]
        if s >= last_e:
            result.append((s, e, l))
            continue
        # chevauchement : garder le plus long
        last_len = last_e - last_s
        cur_len = e - s
        if cur_len > last_len:
            result[-1] = (s, e, l)
        else:
            pass
    return result


def prepare_examples_from_data(nlp, data_list):
    """Convertit (text, {'entities': [...]}) en Example spaCy en nettoyant les entités.
    Retourne (examples, gold_entities_lists)
    """
    examples = []
    gold_entities = []
    for i, (text, ann) in enumerate(data_list):
        doc = nlp.make_doc(text)
        entities = ann.get('entities', [])
        clean = normalize_entities(entities)
        ann_clean = { 'entities': [(s, e, l) for s, e, l in clean] }
        try:
            example = Example.from_dict(doc, ann_clean)
            examples.append(example)
            gold_entities.append([tuple(e) for e in ann_clean['entities']])
        except Exception as ex:
            print(f"[train_ner] Ignored example #{i} due to alignment error: {ex}")
            continue
    return examples, gold_entities


def compute_entity_scores(gold_list, pred_list):
    tp = fp = fn = 0
    for gold, pred in zip(gold_list, pred_list):
        gset = set(gold)
        pset = set(pred)
        tp += len(gset & pset)
        fp += len(pset - gset)
        fn += len(gset - pset)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return { 'tp': tp, 'fp': fp, 'fn': fn, 'precision': precision, 'recall': recall, 'f1': f1 }


def evaluate_on_data(nlp, data_list):
    docs = [nlp(text) for text, _ in data_list]
    gold = [ [tuple(e) for e in ann.get('entities', [])] for _, ann in data_list]
    preds = []
    for doc in docs:
        ents = []
        for ent in doc.ents:
            ents.append((ent.start_char, ent.end_char, ent.label_))
        preds.append(ents)
    return compute_entity_scores(gold, preds)


def train_ner(
    base_model: str = 'fr_core_news_md',
    output_dir: str = None,
    n_iter: int = 30,
    dropout: float = 0.35,
    split: float = 0.0
):
    """Entraîne le NER. Si split>0, crée val/test chacun de fraction `split` (ex: 0.1 -> 80/10/10).
    Import sklearn paresseusement si nécessaire.
    """
    print("🔍 Validation des données d'entraînement...")
    errors = validate_training_data(NER_TRAINING_DATA)
    if errors:
        print(f"❌ {len(errors)} erreurs: {errors[:5]}")
        raise ValueError('Données invalides')
    print(f"✓ {len(NER_TRAINING_DATA)} exemples valides")

    # charger modèle ou blank
    print(f"\n📦 Chargement du modèle de base: {base_model}")
    try:
        if isinstance(base_model, str) and base_model.startswith('blank:'):
            lang = base_model.split(':',1)[1] or 'fr'
            nlp = spacy.blank(lang)
        else:
            nlp = spacy.load(base_model)
    except Exception:
        print('[train_ner] fallback: création d\'un modèle vide fr')
        nlp = spacy.blank('fr')

    # ner component
    if 'ner' not in nlp.pipe_names:
        ner = nlp.add_pipe('ner', last=True)
    else:
        ner = nlp.get_pipe('ner')

    labels = get_ner_labels()
    for label in labels:
        try:
            ner.add_label(label)
        except Exception:
            pass

    # split data
    data = list(NER_TRAINING_DATA)
    train_data = data
    val_data = []
    test_data = []
    if split and split > 0:
        try:
            from sklearn.model_selection import train_test_split
            rest, test_data = train_test_split(data, test_size=split, random_state=42)
            train_data, val_data = train_test_split(rest, test_size=split / (1 - split), random_state=42)
        except Exception:
            print('[train_ner] sklearn absent ou échec du split -> utilisation de tout le jeu pour entraînement')
            train_data = data
            val_data = []
            test_data = []

    print(f"📚 split -> train: {len(train_data)}, val: {len(val_data)}, test: {len(test_data)}")

    train_examples, _ = prepare_examples_from_data(nlp, train_data)
    if val_data:
        _, gold_val = prepare_examples_from_data(nlp, val_data)
    else:
        gold_val = []
    if test_data:
        _, gold_test = prepare_examples_from_data(nlp, test_data)
    else:
        gold_test = []

    other_pipes = [p for p in nlp.pipe_names if p != 'ner']

    print(f"\n🚀 Démarrage entraînement ({n_iter} itérations)")
    with nlp.disable_pipes(*other_pipes):
        nlp.initialize(lambda: train_examples)
        for it in range(n_iter):
            random.shuffle(train_examples)
            losses = {}
            batches = minibatch(train_examples, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                nlp.update(batch, drop=dropout, losses=losses)
            if (it + 1) % max(1, n_iter//5) == 0 or it == 0:
                print(f"   it {it+1}/{n_iter} loss={losses.get('ner',0):.4f}")

    print('\n✓ Entraînement terminé')

    metrics = {}
    if val_data:
        print('[train_ner] Évaluation sur validation...')
        metrics['validation'] = evaluate_on_data(nlp, val_data)
        print(f" val F1 = {metrics['validation']['f1']:.4f}")
    if test_data:
        print('[train_ner] Évaluation sur test...')
        metrics['test'] = evaluate_on_data(nlp, test_data)
        print(f" test F1 = {metrics['test']['f1']:.4f}")

    # save
    if output_dir:
        outp = Path(output_dir)
        outp.mkdir(parents=True, exist_ok=True)
        nlp.to_disk(outp)
        meta = {
            'base_model': base_model,
            'trained_on': datetime.now().isoformat(),
            'iterations': n_iter,
            'labels': labels,
            'examples_count': len(NER_TRAINING_DATA),
            'train_count': len(train_data),
            'val_count': len(val_data),
            'test_count': len(test_data),
            'metrics': metrics
        }
        with open(outp / 'training_meta.json', 'w', encoding='utf-8') as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"[train_ner] Modèle sauvegardé dans {outp}")

    return nlp


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--iterations', '-n', type=int, default=30)
    parser.add_argument('--output', '-o', type=str, default='models/cv_ner')
    parser.add_argument('--base-model', '-m', type=str, default='fr_core_news_md')
    parser.add_argument('--split', '-s', type=float, default=0.0)
    args = parser.parse_args()
    output_dir = Path(__file__).parent.parent / args.output
    train_ner(base_model=args.base_model, output_dir=str(output_dir), n_iter=args.iterations, split=args.split)
