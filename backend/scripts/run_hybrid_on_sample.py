import sys
from pathlib import Path
import importlib
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

# modules
h = importlib.import_module('extractors.hybrid_extractor')
r = importlib.import_module('extractors.robust_extractor')

# sample file (adjust if needed)
sample = Path(__file__).parent.parent / 'data' / 'input' / 'CV_JLA_202504.docx'
print('Sample exists:', sample.exists(), str(sample))

# Which model will be used
try:
    nlp = h.load_spacy_model()
    print('Hybrid loaded model meta.name =', getattr(nlp, 'meta', {}).get('name'))
    print('Hybrid nlp pipe_names =', getattr(nlp, 'pipe_names', None))
except Exception as e:
    print('Error loading model in hybrid:', e)

# Run extraction
try:
    res = h.extract_cv_hybrid(str(sample), r.extract_cv_robust, r.extract_text)
    print('\n--- Extraction result (truncated) ---')
    print(json.dumps(res, indent=2, ensure_ascii=False)[:4000])
except Exception as e:
    print('Extraction error:', e)

