from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'module-0-product-thinking'))
from workshop import rice_score
print(json.dumps({'baseline':str(rice_score(120,2,'0.8',2)),
                  'lower_confidence':str(rice_score(120,2,'0.4',2))}))
