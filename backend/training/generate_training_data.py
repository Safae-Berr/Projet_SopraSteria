"""
Générateur de données d'entraînement à partir des CV existants.

Ce script:
1. Lit les fichiers JSON de sortie existants
2. Génère des exemples d'entraînement NER annotés
3. Enrichit les données d'entraînement automatiquement
"""

from pathlib import Path
from typing import List, Tuple, Dict, Any

import os
import json
import re

try:
    import spacy
    from spacy.training.iob_utils import offsets_to_biluo_tags
    _HAS_SPACY = True
except Exception:
    _HAS_SPACY = False

# Chemin vers les CV analysés
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "output"


def normalize_text(s: str) -> str:
    """Normalize le texte pour la génération d'exemples.

    - remplace les retours chariot par des espaces
    - collapse les espaces multiples
    - supprime les caractères de contrôle invisibles
    """
    if not isinstance(s, str):
        return s
    # remplacer retours chariot et tab par espace
    t = s.replace('\r', ' ').replace('\n', ' ')
    t = t.replace('\t', ' ')
    # retirer caractères invisibles courants
    t = re.sub(r'[\u200B-\u200D\uFEFF]', '', t)
    # collapse espaces multiples
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def load_existing_results() -> List[Dict[str, Any]]:
    """Charge tous les résultats JSON existants."""
    results = []
    
    if not OUTPUT_DIR.exists():
        print(f"Dossier {OUTPUT_DIR} non trouvé")
        return results
    
    for json_file in OUTPUT_DIR.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                data["_source_file"] = json_file.name
                results.append(data)
        except Exception as e:
            print(f"Erreur lecture {json_file}: {e}")
    
    return results


def generate_ner_example_from_header(cv_data: Dict) -> List[Tuple[str, Dict]]:
    """Génère des exemples NER depuis les données d'en-tête."""
    examples = []
    
    contact = cv_data.get("contact", {})
    nom = contact.get("nom")
    email = contact.get("email")
    telephone = contact.get("telephone")
    adresse = contact.get("adresse")
    
    if not nom:
        return examples
    
    # Construire un en-tête synthétique
    header_parts = [nom]
    if telephone:
        header_parts.append(telephone)
    if email:
        header_parts.append(email)
    if adresse:
        header_parts.append(adresse)
    
    header_text = "\n".join(header_parts)
    header_text = normalize_text(header_text)

    # Annoter
    entities = []
    
    # Position du nom
    nom_start = header_text.find(nom)
    if nom_start >= 0:
        entities.append((nom_start, nom_start + len(nom), "PERSON_NAME"))
    
    # Position de l'adresse
    if adresse and adresse in header_text:
        addr_start = header_text.find(adresse)
        entities.append((addr_start, addr_start + len(adresse), "LOCATION"))
    
    if entities:
        examples.append((header_text, {"entities": entities}))
    
    return examples


def generate_ner_example_from_formation(formation: Dict) -> List[Tuple[str, Dict]]:
    """Génère des exemples NER depuis une formation.

    Accepte soit un dict structuré (avec 'etablissement', 'diplome', 'dates'),
    soit une string brute. Utilise des heuristiques pour extraire des entités
    lorsque l'entrée est une string.
    """
    examples = []

    # Si c'est une string, essayer d'en extraire des informations simples
    if isinstance(formation, str):
        text = normalize_text(formation.strip())
        if not text:
            return examples

        entities = []
        # Chercher une plage d'années (ex: 2018-2020 ou 2018 – 2020)
        date_match = re.search(r"(19|20)\d{2}(?:\s*[-–à—]\s*(19|20)\d{2})?", text)
        if date_match:
            s, e = date_match.span()
            entities.append((s, e, "DATE_RANGE"))

        # Chercher un diplôme par mots-clés
        dip_match = re.search(r"\b(master|licence|bachelor|bts|dipl[oô]me|ing[eé]nieur|doctorat|mba|certificat)\b", text, re.I)
        if dip_match:
            s, e = dip_match.span()
            # étendre le span pour prendre la phrase autour du diplôme si possible
            rest_end = text.find(",", e)
            if rest_end == -1:
                rest_end = len(text)
            entities.append((s, rest_end, "DIPLOMA"))

        # Chercher un établissement commun
        school_match = re.search(r"\b(Universit[eé]|École|EPITA|HEC|Polytechnique|IMT|Lyc[eée]|INSA|ENS|IUT|Université)\b", text, re.I)
        if school_match:
            s, e = school_match.span()
            rest_end = text.find("(", e)
            if rest_end == -1:
                rest_end = len(text)
            entities.append((s, rest_end, "SCHOOL"))

        if entities:
            examples.append((text, {"entities": entities}))
        return examples

    # Si c'est déjà un dict structuré
    etablissement = formation.get("etablissement", "") if isinstance(formation, dict) else ""
    diplome = formation.get("diplome", "") if isinstance(formation, dict) else ""
    dates = formation.get("dates", "") if isinstance(formation, dict) else ""

    if not (etablissement or diplome or dates):
        return examples

    # Différents formats
    formats = []

    if dates and diplome and etablissement:
        formats.append(f"{dates}: {diplome} - {etablissement}")
        formats.append(f"{diplome} | {etablissement} | {dates}")
        formats.append(f"{etablissement} ({dates})\n{diplome}")
    elif diplome and etablissement:
        formats.append(f"{diplome} - {etablissement}")
    elif etablissement:
        formats.append(f"{etablissement}")
    elif diplome:
        formats.append(f"{diplome}")

    for text in formats:
        text = normalize_text(text)
        entities = []

        if dates and dates in text:
            pos = text.find(dates)
            entities.append((pos, pos + len(dates), "DATE_RANGE"))

        if diplome and diplome in text:
            pos = text.find(diplome)
            entities.append((pos, pos + len(diplome), "DIPLOMA"))

        if etablissement and etablissement in text:
            pos = text.find(etablissement)
            entities.append((pos, pos + len(etablissement), "SCHOOL"))

        if entities:
            examples.append((text, {"entities": entities}))

    return examples


def generate_ner_example_from_experience(experience: Dict) -> List[Tuple[str, Dict]]:
    """Génère des exemples NER depuis une expérience.

    Accepte soit un dict structuré (avec 'entreprise','poste','dates') soit une string.
    Utilise heuristiques pour extraire dates, poste et entreprise lorsque l'entrée est une string.
    """
    examples = []

    if isinstance(experience, str):
        text = normalize_text(experience.strip())
        if not text:
            return examples

        entities = []
        # Dates
        date_match = re.search(r"(19|20)\d{2}(?:\s*[-–à—]\s*(19|20)\d{2})?|(?:Janvier|F[eé]vrier|Mars|Avril|Mai|Juin|Juillet|Ao[uû]t|Septembre|Octobre|Novembre|D[eé]cembre)\s+\d{4}", text, re.I)
        if date_match:
            s, e = date_match.span()
            entities.append((s, e, "DATE_RANGE"))

        # Poste (heuristique: mots métiers)
        poste_match = re.search(r"\b(D[eé]veloppeur|Developpeur|Ing[eé]nieur|Consultant|Chef de Projet|Lead|Architecte|Stagiaire|Product Owner|Analyst|Business Analyst)\b", text, re.I)
        if poste_match:
            s, e = poste_match.span()
            # étendre jusqu'à 'chez' ou fin
            chez_idx = text.lower().find("chez ", e)
            end_pos = chez_idx if chez_idx != -1 else min(len(text), e + 40)
            entities.append((s, end_pos, "JOB_TITLE"))

        # Entreprise (heuristique: 'chez X' ou mot après '- ' ou ', ')
        chez = re.search(r"chez\s+([A-Za-zÀ-ÖØ-öø-ÿ0-9 &.-]{2,})", text, re.I)
        if chez:
            s = chez.start(1)
            e = chez.end(1)
            entities.append((s, e, "COMPANY"))
        else:
            parts = re.split(r"[-–,:]\s*", text)
            if len(parts) >= 2:
                candidate = parts[-1].strip()
                if 1 < len(candidate) <= 60 and any(c.isalpha() for c in candidate):
                    idx = text.rfind(candidate)
                    if idx != -1:
                        entities.append((idx, idx + len(candidate), "COMPANY"))

        if entities:
            examples.append((text, {"entities": entities}))
        return examples

    # Cas dict structuré
    entreprise = experience.get("entreprise", "") if isinstance(experience, dict) else ""
    poste = experience.get("poste", "") if isinstance(experience, dict) else ""
    dates = experience.get("dates", "") if isinstance(experience, dict) else ""

    if not (entreprise or poste or dates):
        return examples

    formats = []

    if dates and poste and entreprise:
        formats.append(f"{dates}: {poste} chez {entreprise}")
        formats.append(f"{poste} | {entreprise} | {dates}")
        formats.append(f"{entreprise} - {poste} ({dates})")
    elif poste and entreprise:
        formats.append(f"{poste} - {entreprise}")
    elif entreprise:
        formats.append(f"{entreprise}")
    elif poste:
        formats.append(f"{poste}")

    for text in formats:
        text = normalize_text(text)
        entities = []

        if dates and dates in text:
            pos = text.find(dates)
            entities.append((pos, pos + len(dates), "DATE_RANGE"))

        if poste and poste in text:
            pos = text.find(poste)
            entities.append((pos, pos + len(poste), "JOB_TITLE"))

        if entreprise and entreprise in text:
            pos = text.find(entreprise)
            entities.append((pos, pos + len(entreprise), "COMPANY"))

        if entities:
            examples.append((text, {"entities": entities}))

    return examples


def generate_training_data_from_results(results: List[Dict]) -> List[Tuple[str, Dict]]:
    """Génère toutes les données d'entraînement."""
    all_examples = []
    
    for cv_data in results:
        # En-tête
        all_examples.extend(generate_ner_example_from_header(cv_data))
        
        # Formations
        for formation in cv_data.get("formations", []):
            all_examples.extend(generate_ner_example_from_formation(formation))
        
        # Expériences
        for experience in cv_data.get("experiences", []):
            all_examples.extend(generate_ner_example_from_experience(experience))
    
    return all_examples


def validate_examples(examples: List[Tuple[str, Dict]]) -> List[Tuple[str, Dict]]:
    """Valide les exemples générés.

    Filtre aussi les exemples dont les offsets ne s'alignent pas avec la tokenisation
    (utilise spaCy si disponible)."""
    valid = []
    rejected = []

    nlp = None
    if _HAS_SPACY:
        try:
            nlp = spacy.blank("fr")
        except Exception:
            nlp = None

    for text, annotations in examples:
        entities = annotations.get("entities", [])
        all_valid = True
        # vérification basique des bornes
        for start, end, label in entities:
            if start < 0 or end > len(text) or start >= end:
                all_valid = False
                break
            # Vérifier que l'entité n'est pas vide
            entity_text = text[start:end].strip()
            if not entity_text:
                all_valid = False
                break
        
        # Si spaCy est disponible, vérifier l'alignement sur la tokenisation
        if all_valid and nlp is not None and entities:
            try:
                doc = nlp.make_doc(text)
                # Tentative de réalignement automatique faible: pour chaque entité,
                # essayer d'obtenir un char_span aligné; si pas possible, chercher
                # le texte de l'entité dans le document et recalculer les offsets.
                realigned = []
                for (start, end, label) in entities:
                    span = doc.char_span(start, end, label=label, alignment_mode='expand')
                    if span is not None:
                        realigned.append((span.start_char, span.end_char, label))
                    else:
                        # tentative par recherche textuelle du texte de l'entité
                        ent_text = text[start:end].strip()
                        if ent_text:
                            idx = text.find(ent_text)
                            if idx != -1:
                                realigned.append((idx, idx + len(ent_text), label))
                            else:
                                realigned.append((start, end, label))
                        else:
                            realigned.append((start, end, label))

                # vérifier avec offsets_to_biluo_tags si les realigned passent
                try:
                    biluo = offsets_to_biluo_tags(doc, realigned)
                    if any(tag == '-' for tag in biluo):
                        all_valid = False
                    else:
                        # remplacer entities par realigned
                        annotations['entities'] = realigned
                except Exception:
                    all_valid = False
            except Exception:
                # En cas d'erreur, ne pas casser la génération — rejeter l'exemple
                all_valid = False

        if all_valid and entities:
            valid.append((text, annotations))
        else:
            rejected.append((text, annotations))

    # Petit rapport pour debug
    if rejected:
        print(f"\n[generate_training_data] {len(rejected)} exemples rejetés (mauvais offsets / alignement)")
        # afficher quelques exemples rejetés (jusqu'à 5)
        for text, ann in rejected[:5]:
            print(f" - Exemple rejeté: {text[:60]!s}... -> {ann.get('entities', [])}")

    return valid


def export_to_python(examples: List[Tuple[str, Dict]], output_file: str):
    """Exporte les exemples en format Python."""
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# Données d'entraînement générées automatiquement\n\n")
        f.write("GENERATED_NER_DATA = [\n")
        
        for text, annotations in examples:
            # Échapper les caractères
            text_escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            
            f.write(f'    (\n')
            f.write(f'        "{text_escaped}",\n')
            f.write(f'        {{"entities": {annotations.get("entities", [])}}}\n')
            f.write(f'    ),\n')
        
        f.write("]\n")


def main():
    print("=" * 60)
    print("GÉNÉRATION DE DONNÉES D'ENTRAÎNEMENT")
    print("=" * 60)
    
    # Charger les résultats existants
    print("\n📂 Chargement des CV existants...")
    results = load_existing_results()
    print(f"   {len(results)} fichiers JSON chargés")
    
    if not results:
        print("\n⚠️ Aucun résultat trouvé. Créez d'abord des CV analysés.")
        return
    
    # Générer les exemples
    print("\n🔄 Génération des exemples...")
    examples = generate_training_data_from_results(results)
    print(f"   {len(examples)} exemples générés")
    
    # Valider
    print("\n✓ Validation...")
    valid_examples = validate_examples(examples)
    print(f"   {len(valid_examples)} exemples valides")
    
    # Exporter
    output_file = Path(__file__).parent / "generated_data.py"
    export_to_python(valid_examples, str(output_file))
    print(f"\n💾 Exporté vers: {output_file}")
    
    # Afficher quelques exemples
    print("\n📝 Exemples générés:")
    for text, ann in valid_examples[:5]:
        print(f"\n   Texte: {text[:60]}...")
        for start, end, label in ann.get("entities", []):
            print(f"      [{label}] '{text[start:end]}'")


if __name__ == "__main__":
    main()
