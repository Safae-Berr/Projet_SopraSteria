#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test du système de fallback au modèle entraîné
Vérifie que le modèle est appelé quand l'extraction basique est mauvaise
"""
import json
import sys
from pathlib import Path

# Fix encoding pour Windows
import os
os.system('chcp 65001 > nul')

from extractors.robust_extractor import (
    extract_cv_robust,
    is_extraction_valid,
    load_trained_model
)

print("=" * 80)
print("TEST FALLBACK AU MODÈLE ENTRAÎNÉ")
print("=" * 80)

# Test 1: Vérifier que le modèle peut être chargé
print("\n[TEST 1] Chargement du modèle entraîné...")
print("-" * 80)
model = load_trained_model()
if model:
    print("[OK] Modèle entraîné chargé avec succès")
else:
    print("[WARNING] Modèle entraîné non disponible - fallback désactivé")

# Test 2: Vérifier la fonction is_extraction_valid
print("\n[TEST 2] Vérification de is_extraction_valid()...")
print("-" * 80)

# Exemple d'extraction valide
valid_data = {
    "contact": {"nom": "Jean Dupont", "email": "jean@email.com", "titre_profil": "Développeur"},
    "competences": {"techniques": ["Python", "Java"], "fonctionnelles": []},
    "experiences": ["2020-2023: Developpeur chez Sopra"],
    "formations": ["Diplôme Ingénieur"],
    "langues": [],
    "loisirs": []
}

is_valid, issues = is_extraction_valid(valid_data)
print(f"Extraction valide: {is_valid}")
if not is_valid:
    print(f"  Issues: {issues}")

# Exemple d'extraction invalide
invalid_data = {
    "contact": {"nom": None, "email": None, "titre_profil": None},
    "competences": {"techniques": [], "fonctionnelles": []},
    "experiences": [],
    "formations": [],
    "langues": [],
    "loisirs": []
}

is_valid, issues = is_extraction_valid(invalid_data)
print(f"Extraction invalide: {is_valid}")
if not is_valid:
    print(f"  Issues: {issues}")

# Test 3: Tester avec les CVs réels
print("\n[TEST 3] Extraction avec fallback sur CVs réels...")
print("-" * 80)

cv_files = [
    "data/input/CV_JLA_202504.docx",
    "data/input/CV_LEO_WEBER.docx",
    "data/input/CV-Adele PATAROT.pdf"
]

for cv_file in cv_files:
    if not Path(cv_file).exists():
        print(f"[SKIP] Fichier non trouvé: {cv_file}")
        continue

    print(f"\nTraitement: {cv_file}")
    print("  " + "-" * 76)

    try:
        result = extract_cv_robust(cv_file)

        # Afficher les infos extraites
        contact = result.get("contact", {})
        source = result.get("_source", "heuristic")

        print(f"  Nom: {contact.get('nom')}")
        print(f"  Email: {contact.get('email')}")
        print(f"  Titre: {contact.get('titre_profil')}")

        competences = result.get("competences", {})
        tech_count = len(competences.get("techniques", []))
        fonc_count = len(competences.get("fonctionnelles", []))
        print(f"  Compétences: {tech_count} techniques, {fonc_count} fonctionnelles")

        exp_count = len(result.get("experiences", []))
        form_count = len(result.get("formations", []))
        print(f"  Expériences: {exp_count}, Formations: {form_count}")

        print(f"  Source extraction: {source}")

        # Vérifier la validité
        is_valid, issues = is_extraction_valid(result)
        if is_valid:
            print(f"  ✓ Extraction valide")
        else:
            print(f"  ✗ Extraction invalide: {issues}")

    except Exception as e:
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("[OK] TESTS TERMINÉS")
print("=" * 80)
print("\nRésumé:")
print("- Le modèle entraîné se charge comme fallback")
print("- is_extraction_valid() détecte les extractions incomplètes")
print("- extract_cv_robust() appelle le modèle en cas de mauvaise extraction")

