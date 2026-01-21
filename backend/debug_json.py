from extractors.robust_extractor import extract_cv_robust
import json

print("---- CV_LEO_WEBER ----")
res = extract_cv_robust("data/input/CV_LEO_WEBER_1.pdf")
print(json.dumps(res, indent=2, ensure_ascii=False))



