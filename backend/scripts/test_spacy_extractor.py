import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print('PYTHON PATH:', sys.path[0])
try:
    import importlib
    s = importlib.import_module('extractors.spacy_extractor')
    print('Imported spacy_extractor OK')
    print('MODEL_CANDIDATES:')
    for p in s.MODEL_CANDIDATES:
        print(' -', p, 'exists=', p.exists())
    print('IS_TRAINED_MODEL =', getattr(s, 'IS_TRAINED_MODEL', None))
    nlp = getattr(s, 'nlp', None)
    if nlp:
        print('nlp.meta.name =', getattr(nlp, 'meta', {}).get('name'))
        print('nlp.pipe_names =', getattr(nlp, 'pipe_names', None))
    else:
        print('nlp is None')
except Exception as e:
    print('Error importing spacy_extractor:', e)

