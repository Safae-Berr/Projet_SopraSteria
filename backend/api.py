import sys
from pathlib import Path
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import json
import logging
from datetime import datetime
logging.basicConfig(level=logging.DEBUG)

sys.path.append(str(Path(__file__).resolve().parent.parent))

from extractors.version_mapper import normalize_old_cv_to_new, convert_v2_to_old_format
from extractors.robust_extractor import extract_cv_robust, extract_text
from extractors.hybrid_extractor import extract_cv_hybrid

app = Flask(__name__)
CORS(app)  # Autorise les requêtes cross-origin

UPLOAD_FOLDER = Path('data/input')
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_cv(file_path):
    try:
        # 🚀 PIPELINE HYBRIDE ACTIVÉ
        # Utilise les règles en priorité + fallback ML automatique
        resultats = extract_cv_hybrid(
            str(file_path),
            extract_robust_fn=extract_cv_robust,
            extract_text_fn=extract_text
        )

        # Sauvegarde JSON
        nom_candidat = (resultats.get("contact", {}).get("nom") or "Inconnu").replace(" ", "_")
        json_filename = f"CV_{nom_candidat}.json"
        json_path = Path("data/output") / json_filename

        os.makedirs("data/output", exist_ok=True)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(resultats, f, ensure_ascii=False, indent=2)

        resultats["json_filename"] = json_filename

        return resultats, None

    except Exception as e:
        return None, str(e)


@app.route('/api/cv/analyze', methods=['POST'])
def analyze_cv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Aucun fichier envoyé'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Type de fichier non autorisé (PDF ou DOCX uniquement)'}), 400

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        filename = secure_filename(file.filename)
        file_path = Path(app.config['UPLOAD_FOLDER']) / filename
        file.save(str(file_path))

        results, error = process_cv(file_path)

        if error:
            return jsonify({'success': False, 'error': error}), 500

        
        return jsonify(results)

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# -------------------------------------------------
#           ROUTE DOWNLOAD JSON
# -------------------------------------------------
@app.route('/api/cv/json/<filename>', methods=['GET'])
def download_json(filename):

    base = Path("data/output")
    json_path = base / f"{filename}.json"

    if not json_path.exists():
        return jsonify({"error": "JSON introuvable"}), 404

    return send_file(
        str(json_path),
        mimetype="application/json",
        as_attachment=True,
        download_name=f"{filename}.json"
    )
# -------------------------------------------------
#           ROUTE DOWNLOAD DOCX       
# -------------------------------------------------
@app.route('/api/cv/docx/<filename>', methods=['GET'])
def download_docx(filename):
    from generators.generate_sopra_docx import generate_sopra_docx
    
    base = Path("data/output")
    json_path = base / f"{filename}.json"
    docx_path = base / f"{filename}.docx"

    if not json_path.exists():
        return jsonify({"error": "JSON introuvable"}), 404

    # Charger JSON
    cv_data = json.loads(json_path.read_text(encoding='utf-8'))

    # Générer DOCX
    generate_sopra_docx(cv_data, str(docx_path))

    return send_file(
        str(docx_path),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=f"{filename}.docx"
    )

# -------------------------------------------------
#           ROUTE CONVERT DOCX TO PDF
# -------------------------------------------------
@app.route('/api/cv/convert', methods=['POST'])
def convert_docx_to_pdf_route():
    from generators.docx_to_pdf import convert_docx_to_pdf

    try:
        base_input = Path("data/input")
        base_output = Path("data/output")

        os.makedirs(base_input, exist_ok=True)
        os.makedirs(base_output, exist_ok=True)

        # ==============================
        # MODE 1 : Upload d’un DOCX
        # ==============================
        if 'file' in request.files:
            file = request.files['file']
            filename = secure_filename(file.filename)

            if not filename.endswith('.docx'):
                return jsonify({"error": "Veuillez envoyer un fichier .docx"}), 400

            temp_docx = base_input / filename
            file.save(temp_docx)

            output_pdf = base_output / f"{temp_docx.stem}.pdf"

            convert_docx_to_pdf(str(temp_docx), str(output_pdf))

            return send_file(
                str(output_pdf),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"{temp_docx.stem}.pdf"
            )

        # ==============================
        # MODE 2 : Conversion directe
        # ==============================
        data = request.get_json(silent=True)

        if data and "filename" in data:
            filename = data["filename"]

            docx_path = base_output / f"{filename}.docx"
            pdf_path = base_output / f"{filename}.pdf"

            if not docx_path.exists():
                return jsonify({
                    "error": "DOCX introuvable. Générez d'abord le DOCX."
                }), 404

            convert_docx_to_pdf(str(docx_path), str(pdf_path))

            return send_file(
                str(pdf_path),
                mimetype="application/pdf",
                as_attachment=True,
                download_name=f"{filename}.pdf"
            )

        return jsonify({
            "error": "Envoyez soit un fichier DOCX, soit un nom de fichier"
        }, 400)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------------------------
#      ROUTE NORMALISATION (Ancienne → Nouvelle)
# -------------------------------------------------
@app.route('/api/cv/normalize', methods=['POST'])
def normalize_cv():
    """
    Endpoint: POST /api/cv/normalize
    
    Convertit un CV de l'ancienne version vers le nouveau format v2.0.
    
    Accepte deux modes d'entrée (via JSON body):
    1. Mode JSON: {"cv_data": {...ancien JSON...}}
    2. Mode fichier: Upload un fichier JSON/DOCX, on le charge et normalise
    
    Réponse:
    - Success: {
        "success": true,
        "cv_normalized": {...nouveau JSON v2.0...},
        "metadata": {
          "version_source": "old",
          "version_cible": "2.0",
          "nb_experiences": 3,
          "nb_formations": 2,
          "nb_competences": 5
        }
      }
    - Error: {"success": false, "error": "message"}
    """
    try:
        # Mode 1: Envoi du JSON directement en body
        if request.is_json:
            data = request.get_json()
            cv_data = data.get('cv_data')
            
            if not cv_data:
                return jsonify({
                    'success': False,
                    'error': 'Champ "cv_data" manquant'
                }), 400
            
            # Normalisation
            cv_normalized = normalize_old_cv_to_new(cv_data)
            
            metadata = {
                "version_source": "old",
                "version_cible": cv_normalized.get("meta", {}).get("version", "2.0"),
                "nb_experiences": len(cv_normalized.get("experiences", [])),
                "nb_formations": len(cv_normalized.get("formations", [])),
                "nb_competences": (
                    len(cv_normalized.get("competences_techniques", [])) +
                    len(cv_normalized.get("competences_fonctionnelles", []))
                ),
                "nb_langues": len(cv_normalized.get("langues", []))
            }
            
            return jsonify({
                'success': True,
                'cv_normalized': cv_normalized,
                'metadata': metadata
            }), 200
        
        # Mode 2: Fichier uploadé (JSON ou DOCX)
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Aucun fichier envoyé et aucun "cv_data" en JSON'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
        
        filename = secure_filename(file.filename)
        file_path = Path(app.config['UPLOAD_FOLDER']) / filename
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(str(file_path))
        
        # Chargement selon type
        if filename.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                cv_data = json.load(f)
            # Normalisation (pas de path DOCX pour JSON)
            cv_normalized = normalize_old_cv_to_new(cv_data)
        elif filename.endswith('.docx'):
            # Pour DOCX: passer le chemin directement pour extraction optimale
            cv_normalized = normalize_old_cv_to_new({}, docx_path=str(file_path))
        else:
            return jsonify({
                'success': False,
                'error': 'Format de fichier non supporté (JSON ou DOCX requis)'
            }), 400
        
        # Nettoyage fichier temporaire
        try:
            os.remove(file_path)
        except Exception:
            pass
        
        # Calculer métadonnées
        metadata = {
            "version_source": "old",
            "version_cible": "2.0",

            "nb_experiences": len(cv_normalized.get("experiences", [])),
            "nb_formations": len(cv_normalized.get("formations", [])),

            "nb_competences": (
                len(cv_normalized.get("competences_techniques", [])) +
                len(cv_normalized.get("competences_fonctionnelles", []))
            ),

            "nb_langues": len(cv_normalized.get("langues", []))
        }

        
        return jsonify({
            'success': True,
            'cv_normalized': cv_normalized,
            'metadata': metadata
        }), 200
    
    except Exception as e:
        logging.error(f"Erreur normalisation: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur normalisation: {str(e)}'
        }), 500


@app.route('/api/cv/normalize-batch', methods=['POST'])
def normalize_cv_batch():
    """
    Endpoint: POST /api/cv/normalize-batch
    
    Normalise plusieurs CVs en une seule requête.
    
    Body:
    {
      "cvs": [
        {...ancien JSON 1...},
        {...ancien JSON 2...}
      ]
    }
    
    Réponse:
    {
      "success": true,
      "results": [
        {"success": true, "cv_normalized": {...}},
        {"success": false, "error": "..."}
      ],
      "summary": {
        "total": 2,
        "success": 1,
        "errors": 1
      }
    }
    """
    try:
        data = request.get_json()
        cvs_input = data.get('cvs', [])
        
        if not isinstance(cvs_input, list):
            return jsonify({
                'success': False,
                'error': 'Champ "cvs" doit être une liste'
            }), 400
        
        results = []
        for cv_data in cvs_input:
            try:
                cv_normalized = normalize_old_cv_to_new(cv_data)
                results.append({
                    'success': True,
                    'cv_normalized': cv_normalized
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e)
                })
        
        summary = {
            'total': len(results),
            'success': sum(1 for r in results if r.get('success')),
            'errors': sum(1 for r in results if not r.get('success'))
        }
        
        return jsonify({
            'success': summary['errors'] == 0,
            'results': results,
            'summary': summary
        }), 200
    
    except Exception as e:
        logging.error(f"Erreur normalisation batch: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erreur normalisation batch: {str(e)}'
        }), 500

# -------------------------------------------------
#     ROUTES EXPORT (DOCX + PDF) POUR NORMALISATION
# -------------------------------------------------
@app.route('/api/cv/normalize/docx', methods=['POST'])
def normalize_and_export_docx():
    """
    Reçoit un CV déjà normalisé (format v2.0)
    et génère directement un DOCX à partir de celui-ci.
    """

    try:
        from generators.generate_sopra_docx import generate_sopra_docx

        # Vérifier qu’on a bien du JSON
        if not request.is_json:
            return jsonify({
                "error": "Le body doit être du JSON contenant { cv_data }"
            }), 400

        data = request.get_json()

        cv_normalized = data.get("cv_data")

        if not cv_normalized:
            return jsonify({
                "error": "Champ 'cv_data' manquant dans la requête"
            }), 400

        # Conversion du format v2 vers l’ancien format attendu par generate_sopra_docx
        cv_old_format = convert_v2_to_old_format(cv_normalized)

        # Dossier de sortie
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Nom unique
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        docx_path = output_dir / f"cv_normalized_{timestamp}.docx"

        # Génération du DOCX
        generate_sopra_docx(cv_old_format, str(docx_path))

        return send_file(
            str(docx_path),
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            as_attachment=True,
            download_name="cv_normalized.docx"
        )

    except Exception as e:
        logging.error(f"[DOCX EXPORT] Erreur: {str(e)}")
        return jsonify({
            "error": f"Erreur lors de la génération DOCX: {str(e)}"
        }), 500


@app.route('/api/cv/normalize/pdf', methods=['POST'])
def normalize_and_export_pdf():
    """
    Reçoit un CV déjà normalisé (format v2.0)
    et génère directement un PDF à partir de celui-ci.
    """

    try:
        from generators.generate_sopra_docx import generate_sopra_docx
        from generators.docx_to_pdf import convert_docx_to_pdf

        # Vérifier qu’on a bien du JSON
        if not request.is_json:
            return jsonify({
                "error": "Le body doit être du JSON contenant { cv_data }"
            }), 400

        data = request.get_json()

        cv_normalized = data.get("cv_data")

        if not cv_normalized:
            return jsonify({
                "error": "Champ 'cv_data' manquant dans la requête"
            }), 400

        # Conversion au format ancien attendu par le générateur
        cv_old_format = convert_v2_to_old_format(cv_normalized)

        # Dossiers de sortie
        output_dir = Path("data/output")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Noms uniques
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        docx_path = output_dir / f"cv_temp_{timestamp}.docx"
        pdf_path = output_dir / f"cv_normalized_{timestamp}.pdf"

        # Étape 1 : générer DOCX
        generate_sopra_docx(cv_old_format, str(docx_path))

        # Étape 2 : convertir en PDF
        convert_docx_to_pdf(str(docx_path), str(pdf_path))

        return send_file(
            str(pdf_path),
            mimetype="application/pdf",
            as_attachment=True,
            download_name="cv_normalized.pdf"
        )

    except Exception as e:
        logging.error(f"[PDF EXPORT] Erreur: {str(e)}")
        return jsonify({
            "error": f"Erreur lors de la génération PDF: {str(e)}"
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False)
