import spacy
import re
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ordre de recherche des modèles (priorité à cv_ner_final)
MODEL_CANDIDATES = [
    Path(__file__).parent.parent / "models" / "cv_ner_final",
    Path(__file__).parent.parent / "models" / "cv_ner",
    Path(__file__).parent.parent / "models" / "cv_ner_stage1",
    Path(__file__).parent.parent / "models" / "cv_pipeline",
]
BASE_MODEL = "fr_core_news_md"

# Titres de sections courants à ignorer pour les noms
SECTION_TITLES = {
    "langues", "langue", "compétences", "competences", "competence", "compétence",
    "formations", "formation", "expérience", "experience", "expériences", "experiences",
    "profil", "contact", "projets", "projet", "certification", "certifications",
    "loisirs", "centres d'intérêt", "divers", "informations", "personnelles",
    "coordonnées", "coordonnees", "objectif", "résumé", "resume", "summary",
    "skills", "education", "work experience", "professional experience",
    # Sections à exclure absolument des noms
    "savoirs", "savoir", "savoir-être", "savoirs-être", "savoir-faire", "savoirs-faire",
    "soft skills", "hard skills", "compétences techniques", "compétences comportementales",
    "outils", "outils informatiques", "technologies", "méthodologies",
    "activités", "activités extra-scolaires", "hobbies", "centres", "intérêt",
    "passions", "voyages", "curiosité", "curiosité culturelle"
}

# Mots parasites qui ne peuvent pas être des noms
NOISE_WORDS = {
    "savoirs", "être", "faire", "savoir", "sens", "détails", "méticuleux",
    "calme", "curiosité", "culturelle", "autonomie", "communication",
    "outils", "informatique", "microsoft", "figma", "salesforce", "git", "jira",
    "plotly", "pandas", "python", "java", "javascript", "html", "css", "sql",
    "agile", "scrum", "api", "rest", "analyse", "données", "data",
    # Titres de sections fragmentés
    "compétences", "competences", "competence", "compétence",
    "techniques", "technique", "techniqu", "technologie", "technologies",
    "professionnelles", "professionnelle", "professionnel",
    "personnelles", "personnelle", "personnel",
    "environnement", "méthodologies", "méthodologie",
    "comportementales", "comportementale", "transversales", "transversale"
}

# Fragments de mots à rejeter (pour détecter les titres mal parsés)
SECTION_FRAGMENTS = {
    "competen", "techniqu", "professionn", "personn", "comportem",
    "transvers", "environnem", "certificat", "logiciel", "methodolog",
    "formation", "experience", "langues", "projets", "loisirs"
}

# Mots-clés de postes à exclure des noms
POSTE_KEYWORDS = {
    "développeur", "developpeur", "developer", "ingénieur", "ingenieur", "engineer",
    "consultant", "manager", "chef", "responsable", "directeur", "analyste",
    "technicien", "architecte", "lead", "senior", "junior", "stagiaire", "alternant",
    "full stack", "fullstack", "frontend", "backend", "devops", "data", "web",
    "mobile", "software", "project", "product", "scrum", "agile"
}

def is_probable_name(text: str) -> bool:
    """Heuristique améliorée pour détecter un vrai nom (ex: Jean Martin)"""
    text = text.strip()
    if len(text) < 4 or len(text) > 50:
        return False
    
    text_lower = text.lower()
    
    # IMPORTANT: Rejeter si contient un fragment de titre de section
    for frag in SECTION_FRAGMENTS:
        if frag in text_lower:
            return False
    
    # Exclure si contient des mots-clés de poste
    if any(kw in text_lower for kw in POSTE_KEYWORDS):
        return False
    if any(kw in text_lower for kw in SECTION_TITLES):
        return False
    
    # Exclure si contient des mots parasites (TRÈS IMPORTANT)
    text_parts_lower = set(re.split(r"[\s\-]+", text_lower))
    if text_parts_lower & NOISE_WORDS:
        return False
    
    # Exclure si c'est un seul mot parasite
    if text_lower.replace("-", " ").replace("  ", " ").strip() in NOISE_WORDS:
        return False
    
    # Exclure si contient des caractères suspects
    if re.search(r'[@#$%&*=+\[\]{}|\\<>]', text):
        return False
    if re.search(r'\d{3,}', text):
        return False
    
    # Exclure si ressemble à une compétence ou outil
    if re.search(r'\b(python|java|sql|html|css|api|git|agile|scrum)\b', text_lower):
        return False
    
    parts = [p for p in re.split(r"[\s\-]+", text) if p and len(p) > 1]
    if not (2 <= len(parts) <= 4):
        return False
    
    # Vérifier que chaque partie ressemble à un nom propre
    valid_parts = 0
    for p in parts:
        p_lower = p.lower()
        # Exclure si le mot est dans les mots parasites
        if p_lower in NOISE_WORDS:
            return False
        # Accepter: Prénom (Capitale+minuscules), NOM (MAJUSCULES)
        if re.match(r"^[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ][a-zàâäçéèêëîïôöùûüÿœæ']+$", p) and len(p) >= 2:
            valid_parts += 1
        elif re.match(r"^[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒÆ]{2,}$", p) and len(p) >= 2:  # NOM en majuscules
            valid_parts += 1
    
    # Au moins 2 parties valides (prénom + nom)
    return valid_parts >= 2 and valid_parts >= len(parts) * 0.8

def clean_name(text: str) -> str:
    """Nettoie un nom extrait en supprimant les titres/postes parasites"""
    text = re.sub(
        r'\b(?:développeur|developpeur|developer|ingénieur|ingenieur|consultant|'
        r'manager|chef|full\s*stack|data|web|senior|junior|lead|stagiaire|alternant)\b.*',
        '', text, flags=re.IGNORECASE
    ).strip()
    text = re.sub(r'\s*[,\-:]+\s*$', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def load_spacy_model():
    """Charge le modèle spaCy : essaie plusieurs dossiers en priorité, retourne (nlp, is_trained).

    Ordre : cv_ner_final, cv_ner, cv_ner_stage1, cv_pipeline, ensuite fr_core_news_md.
    """
    for candidate in MODEL_CANDIDATES:
        try:
            if candidate.exists():
                logger.info(f"Chargement du modèle entraîné depuis: {candidate}")
                model = spacy.load(str(candidate))
                logger.info("✓ Modèle entraîné chargé avec succès")
                return model, True
        except Exception as e:
            logger.warning(f"Erreur lors du chargement du modèle {candidate}: {e}")

    # fallback to base model
    try:
        logger.info(f"Chargement du modèle de base: {BASE_MODEL}")
        return spacy.load(BASE_MODEL), False
    except Exception as e:
        logger.error(f"Impossible de charger le modèle de base {BASE_MODEL}: {e}")
        raise

# Charge le modèle de langue français (entraîné ou base)
nlp, IS_TRAINED_MODEL = load_spacy_model()

def extraire_entites(texte):
    """
    Extrait les entités (organisations, lieux, personnes, etc.) avec fallback regex.
    Gère à la fois les labels personnalisés (modèle entraîné) et les labels standards.
    """
    doc = nlp(texte)
    entites = {
        "noms": [],
        "organisations": [],
        "lieux": [],
        "dates": [],
        "competences": [],
        "langues": [],
        # Nouvelles catégories du modèle entraîné
        "diplomes": [],
        "ecoles": [],
        "postes": []
    }

    # --- 1. Extraction SpaCy avec validation ---
    for ent in doc.ents:
        val = ent.text.strip()
        if not val or len(val) < 2:
            continue
        
        label = ent.label_
        val_lower = val.lower()
        
        # Labels personnalisés du modèle entraîné
        if label == "PERSON_NAME":
            if val_lower not in SECTION_TITLES and is_probable_name(val):
                cleaned = clean_name(val)
                if cleaned and len(cleaned) >= 3:
                    entites["noms"].append(cleaned)
        
        elif label == "COMPANY":
            if val_lower not in SECTION_TITLES and len(val) >= 2:
                if not re.match(r'^[\d\s\-/]+$', val):
                    entites["organisations"].append(val)
        
        elif label == "SCHOOL":
            if val_lower not in SECTION_TITLES and len(val) >= 2:
                entites["ecoles"].append(val)
        
        elif label == "DIPLOMA":
            if len(val) >= 3:
                entites["diplomes"].append(val)
        
        elif label == "JOB_TITLE":
            # Filtrer les faux positifs pour les postes
            invalid_job_titles = {"un master en", "master en", "licence en", "bac", "diplôme"}
            if len(val) >= 3 and val_lower not in invalid_job_titles:
                entites["postes"].append(val)
        
        elif label == "SKILL":
            if val_lower not in SECTION_TITLES and len(val) >= 2:
                entites["competences"].append(val)
        
        elif label == "LANGUAGE":
            # Filtrer les faux positifs pour les langues
            valid_languages = {
                "français", "anglais", "espagnol", "allemand", "italien", "portugais",
                "chinois", "japonais", "arabe", "russe", "néerlandais", "coréen", "hindi",
                "french", "english", "spanish", "german", "italian", "portuguese",
                "chinese", "japanese", "arabic", "russian", "dutch", "korean",
                "mandarin", "cantonais", "polonais", "turc", "grec", "hébreu"
            }
            if val_lower in valid_languages:
                entites["langues"].append(val.capitalize())
        
        elif label == "DATE_RANGE":
            entites["dates"].append(val)
        
        elif label == "LOCATION":
            if len(val) >= 2 and val_lower not in SECTION_TITLES:
                entites["lieux"].append(val)
        
        # Labels standards du modèle de base (fallback)
        elif label == "PER":
            if val_lower not in SECTION_TITLES and is_probable_name(val):
                cleaned = clean_name(val)
                if cleaned and len(cleaned) >= 3:
                    entites["noms"].append(cleaned)
        
        elif label == "ORG":
            if val_lower not in SECTION_TITLES and len(val) >= 2:
                if not re.match(r'^[\d\s\-/]+$', val):
                    entites["organisations"].append(val)
        
        elif label == "LOC" or label == "GPE":
            if len(val) >= 2 and val_lower not in SECTION_TITLES:
                entites["lieux"].append(val)
        
        elif label == "DATE":
            if not re.match(r'^\d{5}$', val):
                entites["dates"].append(val)

    # --- 2. Heuristique nom en en-tête (si spaCy n'a rien trouvé) ---
    if not entites["noms"]:
        lines = [l.strip() for l in texte.split('\n') if l.strip()][:15]
        for line in lines:
            line_clean = line.strip(" •\t·-–—")
            line_lower = line_clean.lower()
            
            if any(title in line_lower for title in SECTION_TITLES):
                continue
            if re.search(r'[@\d]{5,}', line_clean):
                continue
            
            if 4 <= len(line_clean) <= 50 and is_probable_name(line_clean):
                cleaned = clean_name(line_clean)
                if cleaned:
                    entites["noms"].append(cleaned)
                    break
        
        if not entites["noms"]:
            for line in lines[:10]:
                m = re.search(r'(?:Nom|Name)\s*[:\-]\s*([A-Za-zÀ-ÿ]+(?:\s+[A-Za-zÀ-ÿ\-]+)+)', line, re.IGNORECASE)
                if m and is_probable_name(m.group(1)):
                    entites["noms"].append(clean_name(m.group(1)))
                    break
                
                m = re.match(r'^([A-Za-zÀ-ÿ][a-zà-ÿ\-]+)\s+([A-Za-zÀ-ÿ]{2,}[A-Za-zà-ÿ\-]*)(?:\s|$)', line)
                if m:
                    nom_candidat = f"{m.group(1)} {m.group(2)}"
                    if is_probable_name(nom_candidat):
                        entites["noms"].append(clean_name(nom_candidat))
                        break

    # --- 3. Fallback ORG (universités, entreprises connues) ---
    org_patterns_list = [
        r'(Université\s+(?:de\s+)?[A-Za-zÀ-ÿ0-9\s\-\']+)',
        r'(École\s+(?:Nationale\s+)?(?:Supérieure\s+)?[A-Za-zÀ-ÿ\s\-\']+)',
        r'(IUT\s+[A-Za-zÀ-ÿ\s\-\']+)',
        r'(Master\s+[A-Za-zÀ-ÿ\s\-\']+)',
        r'(Licence\s+[A-Za-zÀ-ÿ\s\-\']+)',
        r'\b(Sopra\s*Steria|Capgemini|Accenture|Atos|CGI|Thales|Orange|BNP|Société Générale)\b',
    ]
    
    for pattern in org_patterns_list:
        for m in re.finditer(pattern, texte, flags=re.IGNORECASE):
            org_clean = m.group(1).strip(" :-\n\t")
            org_clean = re.sub(r'\s+', ' ', org_clean)
            if org_clean and len(org_clean) >= 3:
                if org_clean not in entites["organisations"]:
                    entites["organisations"].append(org_clean)

    # --- 4. Fallback compétences techniques (regex) ---
    skills_patterns = [
        # Langages de programmation
        r'\b(Python|Java|JavaScript|TypeScript|C\+\+|C#|PHP|Ruby|Go|Rust|Swift|Kotlin|Scala|R|MATLAB)\b',
        # Frameworks et bibliothèques
        r'\b(React|Angular|Vue\.?js|Node\.?js|Django|Flask|FastAPI|Spring|Laravel|Rails|Express|Next\.?js)\b',
        # Bases de données
        r'\b(SQL|MySQL|PostgreSQL|MongoDB|Oracle|Redis|Elasticsearch|Cassandra|SQLite|MariaDB)\b',
        # Cloud et DevOps
        r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins|GitLab|GitHub|Terraform|Ansible|CI/CD)\b',
        # Outils et méthodologies
        r'\b(Git|Jira|Confluence|Agile|Scrum|Kanban|DevOps|REST|GraphQL|API)\b',
        # Data Science / ML
        r'\b(TensorFlow|PyTorch|Pandas|NumPy|Scikit-learn|Keras|Machine Learning|Deep Learning|NLP)\b',
    ]
    
    for pattern in skills_patterns:
        for m in re.finditer(pattern, texte, flags=re.IGNORECASE):
            skill = m.group(1).strip()
            if skill and skill.lower() not in [s.lower() for s in entites["competences"]]:
                entites["competences"].append(skill)

    # --- 5. Fallback langues (regex) ---
    lang_patterns = r'\b(Français|Anglais|Espagnol|Allemand|Italien|Portugais|Chinois|Japonais|Arabe|Russe|Néerlandais|Coréen|Hindi|French|English|Spanish|German|Italian|Portuguese|Chinese|Japanese|Arabic|Russian|Dutch|Korean)\b'
    for m in re.finditer(lang_patterns, texte, flags=re.IGNORECASE):
        lang = m.group(1).strip().capitalize()
        # Éviter les doublons FR/EN
        lang_normalized = lang.lower()
        existing_lower = [l.lower() for l in entites["langues"]]
        if lang_normalized not in existing_lower:
            entites["langues"].append(lang)

    # --- 6. Fallback diplômes (regex) ---
    diploma_patterns = [
        r'\b(Bac\s*\+?\s*[0-9]+)',
        r'\b(Master\s+(?:en\s+)?[A-Za-zÀ-ÿ\s\-\']{3,50})',
        r'\b(Licence\s+(?:en\s+)?[A-Za-zÀ-ÿ\s\-\']{3,50})',
        r'\b(DUT|BTS|BEP|CAP)\s+[A-Za-zÀ-ÿ\s\-\']{3,50}',
        r'\b(Dipl[oô]me\s+[A-Za-zÀ-ÿ\s\-\']{3,50})',
        r'\b(MBA|PhD|Doctorat|Ing[eé]nieur|Engineer)\b',
    ]

    for pattern in diploma_patterns:
        for m in re.finditer(pattern, texte, flags=re.IGNORECASE):
            diploma = m.group(0).strip()
            diploma = re.sub(r'\s+', ' ', diploma)
            if diploma and len(diploma) >= 3:
                if diploma.lower() not in [d.lower() for d in entites["diplomes"]]:
                    entites["diplomes"].append(diploma)

    # --- 7. Nettoyage et dédoublonnage final ---
    for k in entites:
        seen = set()
        unique = []
        for x in entites[k]:
            if not x:
                continue
            x = re.sub(r"\s+", " ", x).strip()
            x_lower = x.lower()
            if x and x_lower not in SECTION_TITLES and x_lower not in seen:
                seen.add(x_lower)
                unique.append(x)
        entites[k] = unique

    return entites
