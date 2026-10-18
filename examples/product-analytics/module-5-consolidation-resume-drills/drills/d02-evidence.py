from pathlib import Path
import sys,json
base=Path(__file__).resolve().parents[2]/'module-0-product-thinking'
sys.path.insert(0,str(base))
from workshop import trace_report
case=json.loads((base/'case.json').read_text(encoding='utf-8'))
report=trace_report(case['requirements'],case['checks'])
print(json.dumps({key:report[key] for key in ['criteria','supplied_passes','passed_fraction','worksheet_ready']}))
