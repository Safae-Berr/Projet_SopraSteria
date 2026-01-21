import json
from extractors.version_mapper import extract_from_docx

docx_path = "data/input/WALLID AZZAOUI_202511.docx" 

result = extract_from_docx(docx_path)

print("\n===== RÉSULTAT BRUT DE L'EXTRACTION =====\n")
print(json.dumps(result, indent=2, ensure_ascii=False))
