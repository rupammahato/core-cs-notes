"""Manual revision-score helper; it never grades answer quality or learner readiness."""
from pathlib import Path
import json
import re
import sys

BASE = Path(__file__).resolve().parent
QUESTIONS = json.loads((BASE.parent/'roadmap/questions.json').read_text(encoding='utf-8'))
DEMO = {'Q01':2,'Q02':1,'Q19':3,'Q23':0,'Q35':1,'Q37':2,'Q47':2,'Q52':1}
MOCK = [('Clarify scope and invariant',5),('Estimate workload and skew',7),('Define state and APIs',8),
        ('Trace baseline and authority',10),('Inject failure or changed requirement',10),('Defend evidence and tradeoff',5)]


def review(scores):
    valid = {q['id'] for q in QUESTIONS}
    if type(scores) is not dict or set(scores)-valid or any(type(n) is not int or not 0<=n<=3 for n in scores.values()):
        raise ValueError('Use known Q01-Q60 IDs and manually assigned integer scores 0-3.')
    weak = sorted((score,key) for key,score in scores.items() if score<3)
    mapping = {q['id']:q for q in QUESTIONS}
    return {'assessed':len(scores),'unassessed':len(valid-set(scores)),'manual_points':sum(scores.values()),
        'maximum_for_assessed':3*len(scores),'rubric':'0 cannot explain; 1 vocabulary; 2 mechanism; 3 mechanism/tradeoff/failure/evidence',
        'next_cards':[{'id':key,'manual_score':score,'revisit':list(dict.fromkeys(re.findall(r'\b[AS]\d+\b',mapping[key]['mapping'])))} for score,key in weak],
        'automatically_graded':False,'interview_outcome_predicted':False}


if __name__=='__main__':
    if sys.argv[1:]==['--demo']:
        print(json.dumps(review(DEMO),indent=2))
    elif len(sys.argv)==2:
        print(json.dumps(review(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))),indent=2))
    else:
        print(json.dumps({q['id']:None for q in QUESTIONS},indent=2))
        print('Fill assessed entries with 0-3 and remove unassessed entries; then pass that JSON path.',file=sys.stderr)
