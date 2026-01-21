"""
Extracteur HYBRIDE : Combine robust_extractor + spaCy ML

Pipeline intelligent :
1. Essayer extraction par règles (robust_extractor)
2. Valider le résultat avec is_valid_extraction()
3. Si invalide → utiliser model_based_extraction avec spaCy entraîné
4. Retourner le meilleur résultat

Avantages :
- Garde la performance des règles pour CV bien structurés (Leo, JLA)
- Utilise le ML pour les CV mal structurés (Adèle)
- 100% compatible avec le format JSON existant
- Pas de réentraînement nécessaire
"""

import re
import spacy
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Ordre de recherche des modèles (priorité à cv_ner_final)
MODEL_CANDIDATES = [
    Path(__file__).parent.parent / "models" / "cv_ner_final",
    Path(__file__).parent.parent / "models" / "cv_ner",
    Path(__file__).parent.parent / "models" / "cv_ner_stage1",
    Path(__file__).parent.parent / "models" / "cv_pipeline",
]
BASE_MODEL = "fr_core_news_md"

# Cache du modèle spaCy
_nlp_cache = None

# =============================================================================
# CHARGEMENT DU MODÈLE SPACY
# =============================================================================

def load_spacy_model():
    """Charge le modèle spaCy entraîné ou fallback."""
    global _nlp_cache

    if _nlp_cache is not None:
        return _nlp_cache

    # Essayer chaque candidat dans l'ordre
    for candidate in MODEL_CANDIDATES:
        try:
            if candidate.exists():
                _nlp_cache = spacy.load(str(candidate))
                logger.info(f"✓ Modèle spaCy chargé depuis {candidate}")
                return _nlp_cache
        except Exception as e:
            logger.warning(f"Erreur chargement modèle {candidate}: {e}")

    # Fallback vers le modèle spaCy public
    try:
        _nlp_cache = spacy.load(BASE_MODEL)
        logger.info(f"✓ Modèle standard {BASE_MODEL} chargé (fallback)")
        return _nlp_cache
    except OSError as e:
        logger.error(f"ERREUR: Aucun modèle disponible. {BASE_MODEL} non trouvé.")
        raise RuntimeError(
            f"Impossible de charger un modèle spaCy. "
            f"Installez avec: python -m spacy download {BASE_MODEL}"
        ) from e


# =============================================================================
# VALIDATION DE L'EXTRACTION
# =============================================================================

def is_valid_extraction(data: Dict[str, Any]) -> bool:
    """
    Valide si l'extraction a réussi selon les critères minimums.

    Critères :
    - contact.nom doit exister et ne pas être vide
    - au moins 1 expérience
    - au moins 1 formation
    - compétences non vides (techniques OU fonctionnelles)

    Args:
        data: Dict JSON extrait

    Returns:
        True si extraction valide, False sinon
    """
    try:
        # Vérifier nom
        contact = data.get("contact", {})
        if not isinstance(contact, dict):
            logger.warning("Contact n'est pas un dict")
            return False

        nom = contact.get("nom", "").strip() if contact.get("nom") else None
        if not nom:
            logger.warning("❌ VALIDATION: Nom absent ou vide")
            return False

        # Vérifier expériences
        experiences = data.get("experiences", [])
        if not experiences or (isinstance(experiences, list) and len(experiences) == 0):
            logger.warning("❌ VALIDATION: Aucune expérience trouvée")
            return False

        # Vérifier formations
        formations = data.get("formations", [])
        if not formations or (isinstance(formations, list) and len(formations) == 0):
            logger.warning("❌ VALIDATION: Aucune formation trouvée")
            return False

        # Vérifier compétences
        competences = data.get("competences", {})
        if isinstance(competences, dict):
            tech = competences.get("techniques", [])
            fonc = competences.get("fonctionnelles", [])
            if not tech and not fonc:
                logger.warning("❌ VALIDATION: Aucune compétence trouvée")
                return False
        elif isinstance(competences, list) and len(competences) == 0:
            logger.warning("❌ VALIDATION: Aucune compétence trouvée (list)")
            return False

        logger.info(f"✓ VALIDATION RÉUSSIE: {nom} | "
                   f"Exp:{len(experiences)} | Form:{len(formations)} | Compétences OK")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la validation: {e}")
        return False


# =============================================================================
# EXTRACTION BASÉE SUR SPACY (Fallback pour CV mal structurés)
# =============================================================================

def model_based_extraction(text: str) -> Dict[str, Any]:
    """
    Extrait les informations du CV en utilisant le modèle spaCy entraîné.

    Utilise les entités reconnues (PERSON_NAME, COMPANY, SCHOOL, DIPLOMA, SKILL, LANGUAGE, etc.)
    pour reconstruire un JSON structuré compatible avec le format existant.

    Args:
        text: Texte brut du CV

    Returns:
        Dict structuré avec contact, compétences, formations, expériences, langues, loisirs
    """
    logger.info("🚀 Extraction basée sur le modèle spaCy (ML-based)...")

    nlp = load_spacy_model()

    # Traiter le texte avec spaCy
    doc = nlp(text)

    # Initialiser les conteneurs
    extracted = {
        "contact": {
            "nom": None,
            "email": None,
            "telephone": None,
            "adresse": None,
            "titre_profil": None
        },
        "competences": {
            "techniques": [],
            "fonctionnelles": []
        },
        "formations": [],
        "experiences": [],
        "langues": [],
        "loisirs": [],
        "texte_brut": text
    }

    # Extraction des entités nommées
    person_names = []
    companies = []
    schools = []
    diplomas = []
    job_titles = []
    skills = []
    languages = []
    locations = []
    date_ranges = []

    for ent in doc.ents:
        label = ent.label_
        text_clean = ent.text.strip()

        if label == "PERSON_NAME" and text_clean:
            person_names.append(text_clean)
        elif label == "COMPANY" and text_clean:
            companies.append(text_clean)
        elif label == "SCHOOL" and text_clean:
            schools.append(text_clean)
        elif label == "DIPLOMA" and text_clean:
            diplomas.append(text_clean)
        elif label == "JOB_TITLE" and text_clean:
            job_titles.append(text_clean)
        elif label == "SKILL" and text_clean:
            skills.append(text_clean)
        elif label == "LANGUAGE" and text_clean:
            languages.append(text_clean)
        elif label == "LOCATION" and text_clean:
            locations.append(text_clean)
        elif label == "DATE_RANGE" and text_clean:
            date_ranges.append(text_clean)

    # Construire contact
    if person_names:
        extracted["contact"]["nom"] = person_names[0]  # Premier nom trouvé

    if locations:
        extracted["contact"]["adresse"] = locations[0]

    # Chercher email et téléphone par regex (spaCy ne les identifie pas toujours)
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    if email_match:
        extracted["contact"]["email"] = email_match.group(0)

    tel_match = re.search(r"(?:0|\+33)[\s\d\(\)\.]{8,20}", text)
    if tel_match:
        extracted["contact"]["telephone"] = tel_match.group(0)

    # Titre profil : utiliser le premier job_title si disponible
    if job_titles:
        extracted["contact"]["titre_profil"] = job_titles[0]

    # Compétences : tout dans "techniques" si pas de distinction claire
    # On essaie de classifier par pattern
    tech_keywords = {
        'python', 'java', 'javascript', 'react', 'angular', 'node', 'docker',
        'sql', 'postgres', 'mongodb', 'git', 'aws', 'azure', 'kubernetes',
        'api', 'rest', 'graphql', 'devops', 'ci/cd', 'linux', 'windows'
    }

    for skill in skills:
        skill_lower = skill.lower()
        if any(tech in skill_lower for tech in tech_keywords):
            extracted["competences"]["techniques"].append(skill)
        else:
            extracted["competences"]["fonctionnelles"].append(skill)

    # Si pas de distinction technique/fonctionnelle, tout en techniques
    if not extracted["competences"]["techniques"] and not extracted["competences"]["fonctionnelles"]:
        extracted["competences"]["techniques"] = skills

    # Formations : combiner écoles + diplômes
    formations_set = set()
    for school in schools:
        formations_set.add(school)
    for diploma in diplomas:
        formations_set.add(diploma)
    extracted["formations"] = list(formations_set)

    # Expériences : combiner entreprises + job_titles + dates
    experiences_list = []

    # Si on a entreprises et dates, créer des expériences
    for i, company in enumerate(companies):
        date_str = date_ranges[i] if i < len(date_ranges) else ""
        job_str = job_titles[i] if i < len(job_titles) else ""

        exp_text = f"{company}"
        if job_str:
            exp_text = f"{job_str} chez {exp_text}"
        if date_str:
            exp_text = f"{exp_text} ({date_str})"

        experiences_list.append(exp_text.strip())

    # Si pas assez d'expériences, chercher des patterns dans le texte
    if not experiences_list:
        # Chercher des lignes qui commencent par une date ou contiennent des mots-clés
        lines = text.split('\n')
        for line in lines:
            if re.search(r'\b(20|19)\d{2}\b', line) and len(line) > 10:
                experiences_list.append(line.strip())

    extracted["experiences"] = experiences_list if experiences_list else ["Expériences à extraire manuellement"]

    # Langues
    extracted["langues"] = languages if languages else []

    logger.info(f"✓ Extraction ML complète: {extracted['contact']['nom']}")

    return extracted


# =============================================================================
# FUSION INTELLIGENTE DES RÉSULTATS
# =============================================================================

def merge_extractions(rules_based: Dict, ml_based: Dict) -> Dict:
    """
    Fusionne intelligemment l'extraction par règles et celle par ML.
    Prend le meilleur de chaque approche.

    Stratégie :
    - Contact : ML si plus complet, sinon règles
    - Compétences : fusion (union)
    - Formations : ML si plus nombreuses, sinon règles
    - Expériences : règles (plus structurées), ML pour combler les gaps
    - Langues : fusion
    """
    merged = rules_based.copy()

    # Contact : prendre les champs vides de ML
    for key in ["email", "telephone", "adresse", "titre_profil"]:
        if not merged.get("contact", {}).get(key) and ml_based.get("contact", {}).get(key):
            merged["contact"][key] = ml_based["contact"][key]

    # Compétences : fusion (union) si les deux ont des résultats
    if ml_based.get("competences"):
        merged_comp = merged.get("competences", {})
        ml_comp = ml_based.get("competences", {})

        if isinstance(merged_comp, dict) and isinstance(ml_comp, dict):
            tech = set(merged_comp.get("techniques", []))
            tech.update(ml_comp.get("techniques", []))

            fonc = set(merged_comp.get("fonctionnelles", []))
            fonc.update(ml_comp.get("fonctionnelles", []))

            merged["competences"] = {
                "techniques": list(tech),
                "fonctionnelles": list(fonc)
            }

    # Formations : garder les deux listes (meilleure couverture)
    if ml_based.get("formations"):
        merged_forms = set(merged.get("formations", []))
        merged_forms.update(ml_based.get("formations", []))
        merged["formations"] = list(merged_forms)

    # Expériences : garder les règles (plus fiables), ML pour combler les gaps
    if len(merged.get("experiences", [])) < 2 and ml_based.get("experiences"):
        merged["experiences"].extend(ml_based["experiences"])

    # Langues : fusion
    if ml_based.get("langues"):
        merged_langs = set(merged.get("langues", []))
        merged_langs.update(ml_based.get("langues", []))
        merged["langues"] = list(merged_langs)

    return merged


# =============================================================================
# FONCTION PRINCIPALE : EXTRACTION HYBRIDE
# =============================================================================

def extract_cv_hybrid(file_path: str, extract_robust_fn, extract_text_fn) -> Dict[str, Any]:
    """
    Pipeline hybride intelligent :
    1. Essayer extraction par règles (robust_extractor)
    2. Valider le résultat
    3. Si invalide → extraction basée sur spaCy
    4. Retourner le meilleur résultat

    Args:
        file_path: Chemin du fichier CV (PDF/DOCX)
        extract_robust_fn: Fonction d'extraction par règles (robust_extractor.extract_cv_robust)
        extract_text_fn: Fonction d'extraction de texte brut

    Returns:
        Dict JSON structuré avec contact, compétences, formations, expériences, etc.
    """
    logger.info(f"\n{'='*70}")
    logger.info(f"EXTRACTION HYBRIDE: {Path(file_path).name}")
    logger.info(f"{'='*70}")

    # PHASE 1: Extraction par règles
    logger.info("\n[PHASE 1] Extraction par RÈGLES (robust_extractor)...")
    try:
        rules_result = extract_robust_fn(file_path)
        logger.info("✓ Extraction par règles complétée")
    except Exception as e:
        logger.error(f"Erreur extraction règles: {e}")
        rules_result = None

    # PHASE 2: Validation
    if rules_result:
        is_valid = is_valid_extraction(rules_result)

        if is_valid:
            logger.info("\n✅ RÉSULTAT VALIDE - Utilisation extraction par règles")
            logger.info(f"{'='*70}\n")
            return rules_result

        logger.warning("\n⚠️ RÉSULTAT INVALIDE - Recours au modèle spaCy...")
    else:
        logger.warning("\n⚠️ Extraction par règles échouée - Recours au modèle spaCy...")

    # PHASE 3: Extraction par ML (fallback)
    logger.info("\n[PHASE 2] Extraction par MODÈLE spaCy (ML)...")
    try:
        text = extract_text_fn(file_path)
        ml_result = model_based_extraction(text)
        logger.info("✓ Extraction par ML complétée")
    except Exception as e:
        logger.error(f"Erreur extraction ML: {e}")
        # Retourner l'extraction par règles même si invalide
        if rules_result:
            logger.info("Retour au résultat par règles (même si invalide)")
            return rules_result
        # Sinon retourner une extraction vide
        return {
            "contact": {"nom": "Inconnu", "email": None, "telephone": None, "adresse": None, "titre_profil": None},
            "competences": {"techniques": [], "fonctionnelles": []},
            "formations": [],
            "experiences": [],
            "langues": [],
            "loisirs": [],
            "texte_brut": ""
        }

    # PHASE 4: Fusion intelligente
    if rules_result:
        logger.info("\n[PHASE 3] Fusion intelligente des résultats...")
        final_result = merge_extractions(rules_result, ml_result)
        logger.info("✓ Résultats fusionnés")
    else:
        final_result = ml_result
        logger.info("✓ Utilisation résultat ML uniquement")

    # PHASE 5: Validation finale
    if is_valid_extraction(final_result):
        logger.info(f"\n✅ RÉSULTAT FINAL VALIDE - Pipeline hybride réussi")
    else:
        logger.warning(f"\n⚠️ Résultat final suboptimal, mais utilisable")

    logger.info(f"{'='*70}\n")
    return final_result
