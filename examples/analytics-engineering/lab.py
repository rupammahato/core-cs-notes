"""Run the complete isolated lesson, then print one selected verified observation."""
import json
import sys
from verify import run

observations,_=run(write=False)
key=sys.argv[1].upper() if len(sys.argv)>1 else 'L01'
if key not in observations:raise SystemExit('Choose L01 through L32')
print(json.dumps(observations[key],indent=2))
