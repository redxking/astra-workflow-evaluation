import json,sys
from pathlib import Path
p=Path(sys.argv[1])
assert json.load(p.open())=={"answer":"ASTRA_CONTROLLER_OK","code":""}
# Deliberate first-attempt rejection for fallback conformance only.
sys.exit(1 if p.parent.name=="attempt-1" else 0)
