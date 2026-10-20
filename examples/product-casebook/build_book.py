"""Render authored case reasoning around complete fixture inputs and verified outputs."""
import hashlib
import json
from compute import BASE,displayed,fixture

ROOT=BASE.parents[1]
NOTES=ROOT/'Product Casebook Notes'
START='<!-- BEGIN WORKED CASES -->'
END='<!-- END WORKED CASES -->'


def case_markdown(case,inputs,output):
    chunks=[f"## {case['id']}. {case['title']}",case['prompt'],
            '### Clarify the question','\n'.join('- '+item for item in case['clarify']),
            '### Frame the user and objective',case['framing'],
            '### Evidence status and complete fixture inputs',case['evidence'],
            '```json\n'+json.dumps(inputs,indent=2)+'\n```',
            '### Metric and decision contract',case['metric_contract'],
            '### Work the evidence',case['analysis'],
            f"Run `python examples/product-casebook/compute.py {case['id']}` from the repository root.",
            '**Verified calculation output** (six-decimal presentation; tiny probabilities retain significant digits):',
            '```json\n'+json.dumps(displayed(output),indent=2)+'\n```',
            'The output verifies arithmetic and any named supplied gate rule. It does not verify the source labels, a real causal effect or the quality of a product recommendation.',
            '### Compare options','\n'.join('- '+item for item in case['options']),
            '### Worked recommendation',case['recommendation'],
            '**What would change this recommendation:** '+case['change_mind'],
            '### Engineering and architecture implications',case['architecture'],
            f"Review the [related technical chapter]({case['bridge']}) for implementation depth.",
            '### Interviewer follow-ups']
    for i,row in enumerate(case['follow_ups'],1):
        chunks.extend([f"**F{i}. {row['question']}**",row['answer']])
    chunks.extend(['### Practice task',case['exercise'],
                   '- [ ] I attempted the prompt before reading the worked recommendation.\n- [ ] I can explain a changed assumption and defend a different valid decision.'])
    return '\n\n'.join(chunks)


def build():
    proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
    assert proof['total']==41 and all(row['passed'] for row in proof['checks'])
    assert all(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest for name,digest in proof['source_sha256'].items())
    cases=json.loads((BASE/'cases.json').read_text(encoding='utf-8'))
    inputs=fixture();results=json.loads((BASE/'results.json').read_text(encoding='utf-8'))
    assert [c['id'] for c in cases]==[f'C{n:02}' for n in range(1,19)]
    for part in range(3,9):
        selected=[c for c in cases if c['chapter']==part]
        assert len(selected)==3
        path,=NOTES.glob(f'*-part-{part}-*.md')
        source=path.read_text(encoding='utf-8')
        assert source.count(START)==source.count(END)==1
        before,rest=source.split(START);_,after=rest.split(END)
        body='\n\n'.join(case_markdown(c,inputs[c['id']],results[c['id']]) for c in selected)
        path.write_text(before+START+'\n\n'+body+'\n\n'+END+after,encoding='utf-8')
    print('Rendered all 18 complete worked cases into six case chapters.')


if __name__=='__main__':build()
