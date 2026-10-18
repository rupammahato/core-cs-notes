from pathlib import Path
import sys,json
base=Path(__file__).resolve().parents[2]/'module-4-marketing-measurement-data-visualization'
sys.path.insert(0,str(base))
from measurement import campaign_report
case=json.loads((base/'case.json').read_text(encoding='utf-8'))
report=campaign_report(case['campaigns'])
print(json.dumps({'ctr_pct':report['blended_metrics']['ctr_pct'],
 'wrong_mean_pct':report['wrong_unweighted_ctr_pct'],'reported_roas':report['blended_metrics']['reported_roas']}))
