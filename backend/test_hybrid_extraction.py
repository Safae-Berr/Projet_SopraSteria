"""
Script de test du pipeline HYBRIDE

Démontre :
1. Extraction par règles seule
2. Extraction hybride (règles + ML)
3. Comparaison des résultats
4. Validation automatique

Usage:
    python test_hybrid_extraction.py <chemin_cv.pdf ou .docx>
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any

# Ajouter le chemin backend
sys.path.insert(0, str(Path(__file__).parent))

from extractors.robust_extractor import extract_cv_robust, extract_text
from extractors.hybrid_extractor import (
    extract_cv_hybrid,
    is_valid_extraction,
    model_based_extraction
)


def print_section(title: str):
    """Affiche un titre de section formaté."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def print_validation_result(data: Dict, label: str) -> bool:
    """Affiche les résultats de validation."""
    is_valid = is_valid_extraction(data)

    contact = data.get("contact", {})
    nom = contact.get("nom", "?")
    email = contact.get("email", "?")

    exp_count = len(data.get("experiences", []))
    form_count = len(data.get("formations", []))

    competences = data.get("competences", {})
    if isinstance(competences, dict):
        comp_count = len(competences.get("techniques", [])) + len(competences.get("fonctionnelles", []))
    else:
        comp_count = len(competences) if competences else 0

    status = "✅ VALIDE" if is_valid else "❌ INVALIDE"
    print(f"{label}")
    print(f"  Status: {status}")
    print(f"  Nom: {nom}")
    print(f"  Email: {email}")
    print(f"  Expériences: {exp_count}")
    print(f"  Formations: {form_count}")
    print(f"  Compétences: {comp_count}")

    return is_valid


def test_hybrid_pipeline(file_path: str):
    """Test complet du pipeline hybride."""

    file_path = Path(file_path)
    if not file_path.exists():
        print(f"❌ ERREUR: Fichier non trouvé: {file_path}")
        return

    print_section(f"TEST PIPELINE HYBRIDE - {file_path.name}")

    # TEST 1: Extraction par RÈGLES uniquement
    print_section("TEST 1: Extraction par RÈGLES (robust_extractor)")

    try:
        rules_result = extract_cv_robust(str(file_path))
        print("✓ Extraction par règles complétée\n")

        rules_valid = print_validation_result(rules_result, "Résultat extraction par règles:")
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        rules_result = None
        rules_valid = False

    # TEST 2: Extraction par MODÈLE spaCy (ML)
    print_section("TEST 2: Extraction par MODÈLE spaCy (ML)")

    try:
        text = extract_text(str(file_path))
        ml_result = model_based_extraction(text)
        print("✓ Extraction par ML complétée\n")

        ml_valid = print_validation_result(ml_result, "Résultat extraction ML:")
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        ml_result = None
        ml_valid = False

    # TEST 3: Pipeline HYBRIDE complet
    print_section("TEST 3: Pipeline HYBRIDE complet (Règles + Validation + ML + Fusion)")

    try:
        hybrid_result = extract_cv_hybrid(
            str(file_path),
            extract_robust_fn=extract_cv_robust,
            extract_text_fn=extract_text
        )
        print("✓ Pipeline hybride complété\n")

        hybrid_valid = print_validation_result(hybrid_result, "Résultat extraction HYBRIDE:")
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        hybrid_result = None
        hybrid_valid = False

    # TEST 4: Comparaison
    print_section("COMPARAISON DES RÉSULTATS")

    print(f"Extraction par RÈGLES:  {'✅ VALIDE' if rules_valid else '❌ INVALIDE'}")
    print(f"Extraction par ML:      {'✅ VALIDE' if ml_valid else '❌ INVALIDE'}")
    print(f"Extraction HYBRIDE:     {'✅ VALIDE' if hybrid_valid else '❌ INVALIDE'}")

    print(f"\n📊 Synthèse:")
    print(f"  - Amélioration apportée par la fusion: {'OUI 🎉' if (not rules_valid and hybrid_valid) else 'NON'}")
    print(f"  - Qualité stable pour CV bien structurés: {'OUI ✓' if (rules_valid and hybrid_valid) else 'ATTENTION ⚠️'}")

    # TEST 5: Détail complet du résultat hybride
    if hybrid_result:
        print_section("DÉTAIL COMPLET - Résultat HYBRIDE")

        print("📋 CONTACT:")
        for key, val in hybrid_result.get("contact", {}).items():
            if key != "titre_profil" or val:
                print(f"  {key}: {val}")

        print("\n💼 COMPÉTENCES:")
        comp = hybrid_result.get("competences", {})
        if isinstance(comp, dict):
            tech = comp.get("techniques", [])
            fonc = comp.get("fonctionnelles", [])
            print(f"  Techniques ({len(tech)}): {', '.join(tech[:3])}{'...' if len(tech) > 3 else ''}")
            print(f"  Fonctionnelles ({len(fonc)}): {', '.join(fonc[:3])}{'...' if len(fonc) > 3 else ''}")

        print("\n🎓 FORMATIONS:")
        formations = hybrid_result.get("formations", [])
        for i, formation in enumerate(formations[:3], 1):
            print(f"  {i}. {formation[:70]}{'...' if len(formation) > 70 else ''}")
        if len(formations) > 3:
            print(f"  ... et {len(formations) - 3} de plus")

        print("\n💻 EXPÉRIENCES:")
        experiences = hybrid_result.get("experiences", [])
        for i, exp in enumerate(experiences[:3], 1):
            print(f"  {i}. {exp[:70]}{'...' if len(exp) > 70 else ''}")
        if len(experiences) > 3:
            print(f"  ... et {len(experiences) - 3} de plus")

        print("\n🌍 LANGUES:")
        langues = hybrid_result.get("langues", [])
        print(f"  {', '.join(langues) if langues else 'Aucune'}")

    # SAUVEGARDE RÉSULTATS
    print_section("SAUVEGARDE RÉSULTATS")

    if hybrid_result:
        output_dir = Path(__file__).parent / "data" / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        nom = hybrid_result.get("contact", {}).get("nom", "Inconnu").replace(" ", "_")
        output_file = output_dir / f"TEST_HYBRID_{nom}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(hybrid_result, f, ensure_ascii=False, indent=2)

        print(f"✓ Résultats sauvegardés: {output_file}")

    print("\n")


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 2:
        print("Usage: python test_hybrid_extraction.py <chemin_cv>")
        print("Exemple: python test_hybrid_extraction.py data/input/CV_Adele_PATAROT.pdf")
        sys.exit(1)

    file_path = sys.argv[1]
    test_hybrid_pipeline(file_path)


if __name__ == "__main__":
    main()

