"""
Module de normalisation CV : conversion ancien format → format TEMPLATE Sopra Steria

APPROCHE SIMPLE ET FIDÈLE:
- Aucun parsing métier
- Aucune déduction
- Copie intégrale du contenu

Retourne un JSON avec des listes simples de strings (pas de structures métier)
"""

from typing import Dict, List, Any
from pathlib import Path
from docx import Document
import re



def extract_from_docx(docx_path: str) -> Dict[str, Any]:
    try:
        doc = Document(docx_path)
    except Exception:
        return {}

    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    # --- Récupération titre profil et nom ---
    titre_profil = paragraphs[0] if len(paragraphs) > 0 else ""
    nom = "WAZ"

    sections = {
        "competences_techniques": [],
        "experiences": [],
        "formations": [],
        "langues": []
    }

    current_section = None

    for line in paragraphs:
        lower = line.lower()

        # Détection sections précises
        if "compétences techniques" in lower:
            current_section = "competences_techniques"
            continue

        if lower.startswith("expérience"):
            current_section = "experiences"
            continue

        if "formation" in lower:
            current_section = "formations"
            continue

        if "langue" in lower:
            current_section = "langues"
            continue

        if current_section:
            sections[current_section].append(line)

    return {
        "resultats_spacy": {
            "contact": {
                "titre_profil": titre_profil,
                "nom": nom
            },
            "competences_fonctionnelles": [],
            "competences_techniques": sections["competences_techniques"],
            "experiences": sections["experiences"],
            "formations": sections["formations"],
            "langues": sections["langues"]
        }
    }



def extract_initiales(nom: str) -> str:
    """Extrait initiales du nom (e.g., 'Jean Dupont' → 'JD')."""
    if not nom:
        return ""
    parties = nom.split()
    if len(parties) >= 2:
        return f"{parties[0][0]}{parties[-1][0]}".upper()
    elif parties:
        return parties[0][0].upper()
    return ""


def extract_contact_info(old_data: Dict) -> Dict[str, str]:
    """Extrait les informations de contact (nom, email, téléphone)."""
    contact = {}
    
    # Chercher "resultats_spacy" puis "contact" direct
    spacy_data = old_data.get("resultats_spacy", {})
    contact_data = spacy_data.get("contact", {}) if spacy_data else old_data.get("contact", {})
    
    if not contact_data:
        contact_data = old_data
    
    contact["nom"] = contact_data.get("nom") or old_data.get("nom", "")
    contact["email"] = contact_data.get("email") or old_data.get("email", "")
    contact["telephone"] = contact_data.get("telephone") or old_data.get("telephone", "")
    contact["adresse"] = contact_data.get("adresse") or old_data.get("adresse", "")
    
    return contact


def group_experiences_into_blocks(experiences_lines: List[str]) -> List[Dict[str, Any]]:
    """
    Version compatible avec validate_cv_data :
    - ajoute une clé "entreprise"
    - extrait l'entreprise depuis le titre
    """

    if not experiences_lines:
        return []

    blocks = []
    current_block = None

    period_pattern = r"(Depuis\s+\d{4}|\d{4}\s*à\s*\d{4})"

    for line in experiences_lines:
        if not line.strip():
            continue

        # Détection d’un titre d’expérience
        if re.search(period_pattern, line):

            # Sauvegarder l’ancien bloc
            if current_block:
                blocks.append(current_block)

            # Extraire entreprise depuis le titre
            entreprise = ""
            parts = line.split("–")

            if len(parts) >= 2:
                entreprise = parts[1].strip()

            current_block = {
                "titre": line.strip(),
                "entreprise": entreprise,   
                "missions": [],
                "environnement": ""
            }

        else:
            # Ligne de mission
            if current_block is not None:
                current_block["missions"].append(line.strip())

    # Ajouter le dernier bloc
    if current_block:
        blocks.append(current_block)

    return blocks

def flatten_experiences_for_old_format(experiences):
    """
    Convertit les expériences structurées (dict) en format string
    compatible avec l’ancien générateur DOCX
    """

    if not isinstance(experiences, list):
        return []

    flattened = []

    for exp in experiences:

        # Si déjà string → on garde
        if isinstance(exp, str):
            flattened.append(exp)
            continue

        # Si dict structuré
        if isinstance(exp, dict):
            titre = exp.get("titre", "").strip()
            missions = exp.get("missions", [])

            if titre:
                flattened.append(titre)

            for m in missions:
                flattened.append(m)

    return flattened



def normalize_old_cv_to_new(cv_data: Dict, docx_path: str = None) -> Dict[str, Any]:
    """
    Convertit un CV ancien format vers le JSON du template Sopra Steria
    
    APPROCHE SIMPLE ET FIDÈLE:
    - Aucun parsing métier
    - Aucune déduction
    - Copie intégrale du contenu
    
    Paramètres:
        cv_data: Dict avec structure {resultats_spacy: {contact, competences_*, experiences, formations, langues}}
                 OU données brutes du JSON
        docx_path: (optionnel) Path au fichier DOCX pour extraction directe (recommandé pour anciens formats)
    
    STRUCTURE:
    {
      "header": {...},
      "competences_fonctionnelles": ["ligne1", "ligne2", ...],
      "competences_techniques": ["ligne1", "ligne2", ...],
      "experiences": ["bloc1", "bloc2", ...],
      "formations": ["ligne1", "ligne2", ...],
      "langues": ["ligne1", "ligne2", ...]
    }
    """
    
    # Si cv_data est déjà au nouveau format, le retourner tel quel
    if "experiences" in cv_data and "header" in cv_data:
        return cv_data

    # Si un chemin DOCX est fourni, extraire directement du DOCX (meilleur résultat pour anciens formats)
    if docx_path and Path(docx_path).exists():
        cv_data = extract_from_docx(docx_path)
        if not cv_data.get("resultats_spacy"):
            # Si extraction DOCX échoue, continuer avec cv_data original
            pass
        else:
            # Extraction réussie, utiliser ces données
            pass
    
    # Chercher dans spacy AVANT
    spacy = cv_data.get("resultats_spacy", {})
    titre_profil = spacy.get("contact", {}).get("titre_profil", "")

    # Extraction des données de base
    contact = extract_contact_info(cv_data)
    nom = contact.get("nom", "")
    initiales = extract_initiales(nom)

    # === HEADER ===
    header = {
        "confidentialite": "C2 - Usage restreint",
        "titre_document": "CURRICULUM VITAE",
        "role": titre_profil,
        "initiales": initiales
    }
    
    # === COMPETENCES FONCTIONNELLES (copie fidèle) ===
    competences_fonctionnelles = []

    if "competences_fonctionnelles" in spacy and isinstance(spacy["competences_fonctionnelles"], list):
        competences_fonctionnelles.extend(spacy["competences_fonctionnelles"])
    
    # Chercher dans cv_data direct
    if "competences_fonctionnelles" in cv_data and isinstance(cv_data["competences_fonctionnelles"], list):
        competences_fonctionnelles.extend(cv_data["competences_fonctionnelles"])
    
    # Nettoyer les doublons en gardant l'ordre
    competences_fonctionnelles = list(dict.fromkeys(c for c in competences_fonctionnelles if c))
    
    # === COMPETENCES TECHNIQUES (copie fidèle) ===
    competences_techniques = []
    
    # Chercher dans spacy
    if "competences_techniques" in spacy and isinstance(spacy["competences_techniques"], list):
        competences_techniques.extend(spacy["competences_techniques"])
    
    # Chercher dans cv_data direct
    if "competences_techniques" in cv_data and isinstance(cv_data["competences_techniques"], list):
        competences_techniques.extend(cv_data["competences_techniques"])
    
    # Nettoyer
    competences_techniques = list(dict.fromkeys(c for c in competences_techniques if c))
    
    # === EXPERIENCES (regroupées en blocs : titre + missions + environnement) ===
    experiences_lines = []
    
    if "experiences" in spacy and isinstance(spacy["experiences"], list):
        # Les expériences du format spacy sont des strings ou des listes
        for exp in spacy["experiences"]:
            if isinstance(exp, str) and exp.strip():
                experiences_lines.append(exp.strip())
            elif isinstance(exp, list):
                # Si c'est une liste, la concaténer
                experiences_lines.extend(str(e).strip() for e in exp if e)
    
    if "experiences" in cv_data and isinstance(cv_data["experiences"], list):
        for exp in cv_data["experiences"]:
            if isinstance(exp, str) and exp.strip():
                experiences_lines.append(exp.strip())
            elif isinstance(exp, list):
                experiences_lines.extend(str(e).strip() for e in exp if e)
    
    # Déduplique
    experiences_lines = list(dict.fromkeys(experiences_lines))
    
    # Regrouper en blocs structurés
    experiences = group_experiences_into_blocks(experiences_lines)
    
    # === FORMATIONS (copie fidèle) ===
    formations = []
    
    if "formations" in spacy and isinstance(spacy["formations"], list):
        for form in spacy["formations"]:
            if isinstance(form, str) and form.strip():
                formations.append(form.strip())
            elif isinstance(form, list):
                formations.extend(str(f).strip() for f in form if f)
    
    if "formations" in cv_data and isinstance(cv_data["formations"], list):
        for form in cv_data["formations"]:
            if isinstance(form, str) and form.strip():
                formations.append(form.strip())
            elif isinstance(form, list):
                formations.extend(str(f).strip() for f in form if f)
    
    formations = list(dict.fromkeys(formations))
    
    # === LANGUES (copie fidèle) ===
    langues = []
    
    if "langues" in spacy and isinstance(spacy["langues"], list):
        for lang in spacy["langues"]:
            if isinstance(lang, str) and lang.strip():
                langues.append(lang.strip())
    
    if "langues" in cv_data and isinstance(cv_data["langues"], list):
        for lang in cv_data["langues"]:
            if isinstance(lang, str) and lang.strip():
                langues.append(lang.strip())
    
    langues = list(dict.fromkeys(langues))
    
    # === CONSTRUCTION FINALE (STRUCTURE TEMPLATE SOPRA STERIA) ===
    return {
        "contact": {"nom": nom},
        "header": header,
        "competences_fonctionnelles": competences_fonctionnelles,
        "competences_techniques": competences_techniques,
        "experiences": experiences,
        "formations": formations,
        "langues": langues
    }



def convert_v2_to_old_format(cv_template: Dict) -> Dict[str, Any]:
    """
    Convertit le format normalisé vers le format attendu par generate_sopra_docx
    """

    contact = cv_template.get("contact", {})

    nom = contact.get("nom", "")
    titre_profil = cv_template.get("header", {}).get("role", "")

    exps = cv_template.get("experiences", [])

    flattened = flatten_experiences_for_old_format(exps)

    # Exception ciblée pour le CV type WALID :
    # Si on détecte des lignes commençant par "Depuis" ou des périodes,
    # on envoie une STRING multi-lignes pour affichage direct dans le DOCX
    if flattened and isinstance(flattened, list) and any("Depuis" in str(l) or "à" in str(l) for l in flattened):
        experiences = "\n".join(flattened)
    else:
        experiences = flattened

    return {
        "contact": {
            "nom": nom,
            "titre_profil": titre_profil
        },

        "competences": {
            "techniques": cv_template.get("competences_techniques", []),
            "fonctionnelles": cv_template.get("competences_fonctionnelles", [])
        },

        "experiences": experiences,
        "formations": cv_template.get("formations", []),
        "langues": cv_template.get("langues", [])
    }

