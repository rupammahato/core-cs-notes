from pathlib import Path
import sys,json
base=Path(__file__).resolve().parents[2]/'module-4-marketing-measurement-data-visualization'
sys.path.insert(0,str(base))
from measurement import build
case=json.loads((base/'case.json').read_text(encoding='utf-8'));result=build(case)
print(json.dumps({'click_only':result['last_eligible_click_7d']['by_campaign_net_cents'],
 'view_fallback':result['click_7d_else_view_1d']['by_campaign_net_cents'],
 'summed_claim_cents':result['independent_claim_overlap']['summed_claim_value_cents'],
 'unique_claimed_cents':result['independent_claim_overlap']['unique_claimed_net_cents'],
 'ledger_net_cents':result['ledger']['net_cents']}))
