import sys
import importlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

print('PYTHON PATH:', sys.path[0])

# Test hybrid_extractor
print('\n=== hybrid_extractor test ===')
try:
    h = importlib.import_module('extractors.hybrid_extractor')
    for p in getattr(h, 'MODEL_CANDIDATES', []):
        print(f'candidate: {p}  exists={p.exists()}')
    try:
        nlp = h.load_spacy_model()
        # load_spacy_model in hybrid returns nlp object
        meta_name = getattr(nlp, 'meta', {}).get('name') if nlp else None
        pipes = getattr(nlp, 'pipe_names', None)
        print('hybrid loaded nlp meta name =', meta_name)
        print('hybrid nlp pipe_names =', pipes)
    except Exception as e:
        print('hybrid load error:', e)
except Exception as e:
    print('import hybrid_extractor failed:', e)

# Test spacy_extractor
print('\n=== spacy_extractor test ===')
try:
    s = importlib.import_module('extractors.spacy_extractor')
    for p in getattr(s, 'MODEL_CANDIDATES', []):
        print(f'candidate: {p}  exists={p.exists()}')
    print('spacy_extractor.IS_TRAINED_MODEL =', getattr(s, 'IS_TRAINED_MODEL', None))
    try:
        nlp = getattr(s, 'nlp', None)
        meta_name = getattr(nlp, 'meta', {}).get('name') if nlp else None
        pipes = getattr(nlp, 'pipe_names', None)
        print('spacy_extractor nlps meta name =', meta_name)
        print('spacy_extractor nlp pipe_names =', pipes)
    except Exception as e:
        print('spacy_extractor nlp error:', e)
except Exception as e:
    print('import spacy_extractor failed:', e)

print('\nTest script finished')

