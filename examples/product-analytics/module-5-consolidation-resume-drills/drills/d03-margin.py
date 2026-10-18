from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'module-1-pricing-unit-economics'))
from economics import margins,price_for_margin
result=margins('100','40','10')
print(json.dumps({'gross_margin_pct':result['gross_margin_pct'],
                  'contribution_margin_pct':result['contribution_margin_pct'],
                  'price_for_60pct_margin_usd':price_for_margin('40','0.6')['cent_price_usd']}))
