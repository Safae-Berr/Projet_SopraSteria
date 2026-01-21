"""
Script de VALIDATION COMPLÈTE du Pipeline Hybride

Vérifie que tout est bien en place avant production.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# VÉRIFICATIONS
# =============================================================================

class ValidationChecker:
    """Effectue toutes les vérifications préalables."""

    def __init__(self):
        self.backend_path = Path(__file__).parent
        self.issues: List[Tuple[str, str, str]] = []
        self.warnings: List[Tuple[str, str]] = []
        self.success: List[str] = []

    def check_files(self) -> bool:
        """Vérifie que tous les fichiers nécessaires existent."""
        print("\n📁 Vérification des fichiers...")

        files_required = {
            "extractors/hybrid_extractor.py": "Pipeline hybride principal",
            "extractors/robust_extractor.py": "Extraction par règles",
            "api.py": "API Flask",
        }

        all_ok = True
        for file_path, description in files_required.items():
            full_path = self.backend_path / file_path
            if full_path.exists():
                self.success.append(f"✓ {file_path}")
            else:
                self.issues.append(("ERREUR", "Fichier manquant", f"{file_path}: {description}"))
                all_ok = False

        return all_ok

    def check_models(self) -> bool:
        """Vérifie que les modèles spaCy existent."""
        print("🧠 Vérification des modèles spaCy...")

        models_path = self.backend_path.parent / "models"

        # accepter plusieurs candidats (ordre de préférence)
        candidates = [
            models_path / "cv_ner_final",
            models_path / "cv_ner",
            models_path / "cv_ner_stage1",
            models_path / "cv_pipeline",
        ]

        found = None
        for c in candidates:
            if c.exists() and (c / "meta.json").exists():
                found = c
                break

        if found:
            self.success.append(f"✓ Modèle spaCy trouvé: {found.name}")
        else:
            # aucun modèle entraîné trouvé: avertir et indiquer le fallback
            self.issues.append(
                ("ERREUR", "Aucun modèle ML entraîné trouvé",
                 "Aucun des modèles attendus (cv_ner_final, cv_ner, cv_ner_stage1, cv_pipeline) n'a été détecté.\n"
                 "Le fallback utilisera fr_core_news_md.")
            )
            return False

        return True

    def check_dependencies(self) -> bool:
        """Vérifie que les dépendances Python sont installées."""
        print("📦 Vérification des dépendances...")

        required_modules = {
            "flask": "API Flask",
            "spacy": "NLP avec spaCy",
            "pdfplumber": "Extraction PDF",
            "pathlib": "Gestion des chemins",
        }

        all_ok = True
        for module, description in required_modules.items():
            try:
                __import__(module)
                self.success.append(f"✓ {module} installé")
            except ImportError:
                self.issues.append(
                    ("ERREUR", f"Dépendance manquante",
                     f"{module}: {description}\n    Installez avec: pip install -r requirements.txt")
                )
                all_ok = False

        return all_ok

    def check_spacy_models(self) -> bool:
        """Vérifie que le modèle spaCy français est installé."""
        print("🌍 Vérification du modèle spaCy français...")

        try:
            import spacy
            nlp = spacy.load("fr_core_news_md")
            self.success.append(f"✓ Modèle fr_core_news_md installé")
            return True
        except OSError:
            self.issues.append(
                ("ERREUR", "Modèle spaCy français manquant",
                 "fr_core_news_md n'est pas installé.\n"
                 "    Installez avec: python -m spacy download fr_core_news_md")
            )
            return False
        except ImportError:
            self.issues.append(
                ("ERREUR", "spaCy non installé",
                 "pip install spacy")
            )
            return False

    def check_test_file(self) -> bool:
        """Vérifie que le script de test existe."""
        print("🧪 Vérification du script de test...")

        test_path = self.backend_path / "test_hybrid_extraction.py"

        if test_path.exists():
            self.success.append(f"✓ Script de test disponible")
            return True
        else:
            self.warnings.append(
                ("Script de test absent",
                 "test_hybrid_extraction.py n'existe pas.")
            )
            return True

    def check_data_dirs(self) -> bool:
        """Vérifie que les répertoires de données existent."""
        print("📂 Vérification des répertoires de données...")

        dirs_required = {
            "data/input": "CVs uploadés",
            "data/output": "Résultats JSON/DOCX",
        }

        all_ok = True
        for dir_path, description in dirs_required.items():
            full_path = self.backend_path / dir_path
            if full_path.exists():
                self.success.append(f"✓ {dir_path} existe")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                self.success.append(f"✓ {dir_path} créé")

        return all_ok

    def run_all_checks(self) -> bool:
        """Exécute tous les vérifications."""
        print("\n" + "="*70)
        print("  VALIDATION COMPLÈTE - Pipeline Hybride")
        print("="*70)

        results = {
            "Fichiers": self.check_files(),
            "Modèles ML": self.check_models(),
            "Dépendances": self.check_dependencies(),
            "Modèle spaCy FR": self.check_spacy_models(),
            "Script de test": self.check_test_file(),
            "Répertoires": self.check_data_dirs(),
        }

        return all(results.values())

    def print_report(self):
        """Affiche le rapport de validation."""

        if self.success:
            print("\n✅ SUCCÈS:")
            for item in self.success:
                print(f"   {item}")

        if self.warnings:
            print("\n⚠️  AVERTISSEMENTS:")
            for title, desc in self.warnings:
                print(f"   {title}")
                print(f"      {desc}\n")

        if self.issues:
            print("\n❌ ERREURS:")
            for type_, title, desc in self.issues:
                print(f"   {title}")
                print(f"      {desc}\n")

        print("="*70)

        if not self.issues:
            print("✅ VALIDATION RÉUSSIE - Vous êtes prêt à déployer ! 🚀\n")
            return True
        else:
            print(f"❌ VALIDATION ÉCHOUÉE - {len(self.issues)} erreur(s) à corriger\n")
            return False


def test_imports() -> bool:
    """Teste que tous les imports fonctionnent."""
    print("\n🔗 Test des imports...")

    try:
        from extractors.hybrid_extractor import (
            extract_cv_hybrid,
            is_valid_extraction,
            model_based_extraction,
            load_spacy_model
        )
        from extractors.robust_extractor import extract_cv_robust, extract_text
        print("✓ Tous les imports fonctionnent")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False


def test_validation_function() -> bool:
    """Teste la fonction de validation."""
    print("\n🧪 Test de la fonction de validation...")

    try:
        from extractors.hybrid_extractor import is_valid_extraction

        # Test 1: Extraction valide
        valid_data = {
            "contact": {"nom": "John Doe"},
            "experiences": ["Exp 1"],
            "formations": ["Formation 1"],
            "competences": {"techniques": ["Python"]}
        }

        if is_valid_extraction(valid_data):
            print("✓ Validation correcte pour données valides")
        else:
            print("❌ Validation échouée pour données valides")
            return False

        # Test 2: Extraction invalide (pas de nom)
        invalid_data = {
            "contact": {"nom": None},
            "experiences": [],
            "formations": [],
            "competences": {}
        }

        if not is_valid_extraction(invalid_data):
            print("✓ Validation correcte pour données invalides")
        else:
            print("❌ Validation échouée pour données invalides")
            return False

        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    """Exécute la validation complète."""

    checker = ValidationChecker()
    validation_ok = checker.run_all_checks()
    checker.print_report()

    if validation_ok:
        print("\n🔗 Exécution des tests fonctionnels...")
        print("="*70)

        test_results = {
            "Imports": test_imports(),
            "Validation": test_validation_function(),
        }

        print("\n" + "="*70)
        if all(test_results.values()):
            print("✅ TOUS LES TESTS FONCTIONNELS RÉUSSIS 🎉")
            print("\n📊 Résumé:")
            print("   ✓ Fichiers présents")
            print("   ✓ Modèles spaCy disponibles")
            print("   ✓ Dépendances installées")
            print("   ✓ Imports fonctionnels")
            print("   ✓ Validation de données")
            print("\n🚀 PRÊT À DÉPLOYER !\n")
            return 0
        else:
            print("❌ CERTAINS TESTS FONCTIONNELS ONT ÉCHOUÉ")
            print(f"\n{sum(1 for v in test_results.values() if v)}/{len(test_results)} tests réussis\n")
            return 1
    else:
        print("\n⚠️  VEUILLEZ CORRIGER LES ERREURS AVANT DE CONTINUER\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
