"""
Script simplifié utilisant le nouvel extracteur robuste
"""

import json
from extractors.robust_extractor import extract_cv_robust


def analyser_cv(fichier):
    resultats = extract_cv_robust(fichier)

    with open("resultat.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    print("Analyse terminée → resultat.json")


if __name__ == "__main__":
    analyser_cv("data/input/mon_cv.pdf")
