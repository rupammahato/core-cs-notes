"""Insert exact recorded traces and the three actually executed model SQL files."""
import hashlib
import json
from warehouse import BASE,fixture

ROOT=BASE.parents[1];NOTES=ROOT/'Analytics Engineering Notes'
START='<!-- BEGIN WAREHOUSE LAB -->';END='<!-- END WAREHOUSE LAB -->'


def displayed(value):
    if isinstance(value,dict):return {k:displayed(v) for k,v in value.items()}
    if isinstance(value,list):return [displayed(v) for v in value]
    if isinstance(value,float):return round(value,6)
    return value


def lesson_markdown(lesson,output):
    chunks=[f"### {lesson['id']}. {lesson['title']}",lesson['question'],
            '**Worked explanation:** '+lesson['reasoning'],
            f"Run `python examples/analytics-engineering/lab.py {lesson['id']}`. The runner executes and closes the full isolated lesson, then prints this selected trace."]
    if lesson.get('model'):
        chunks+=['**Exact model SELECT executed by the pipeline:**','```sql\n'+(BASE/lesson['model']).read_text(encoding='utf-8').rstrip()+'\n```']
    chunks+=['**Verified output** (six-decimal display; raw values are in observations.json):',
             '```json\n'+json.dumps(displayed(output),indent=2)+'\n```',
             '**Common trap:** '+lesson['trap'],'**Interview follow-up:** '+lesson['follow_up']]
    return '\n\n'.join(chunks)


def build():
    proof=json.loads((BASE/'verification-results.json').read_text(encoding='utf-8'))
    assert proof['total']==74 and all(row['passed'] for row in proof['checks'])
    assert all(hashlib.sha256((BASE/name).read_bytes()).hexdigest()==digest for name,digest in proof['source_sha256'].items())
    lessons=json.loads((BASE/'lessons.json').read_text(encoding='utf-8'))
    output=json.loads((BASE/'observations.json').read_text(encoding='utf-8'))
    assert [row['id'] for row in lessons]==[f'L{n:02}' for n in range(1,33)]
    for part in range(2,10):
        selected=[row for row in lessons if row['chapter']==part];assert len(selected)==4
        path,=NOTES.glob(f'*-part-{part}-*.md');source=path.read_text(encoding='utf-8')
        assert source.count(START)==source.count(END)==1
        before,rest=source.split(START);_,after=rest.split(END)
        body='## Worked warehouse traces\n\n'+'\n\n'.join(lesson_markdown(row,output[row['id']]) for row in selected)
        path.write_text(before+START+'\n\n'+body+'\n\n'+END+after,encoding='utf-8')
    path,=NOTES.glob('*-part-2-*.md');source=path.read_text(encoding='utf-8')
    marker='<!-- BEGIN COMPLETE RAW FIXTURE -->';end='<!-- END COMPLETE RAW FIXTURE -->'
    before,rest=source.split(marker);_,after=rest.split(end)
    lines=['## Complete supplied raw-change fixture','Every row below is one delivered envelope. Payload keys are preserved; no abbreviated source sample is used.',
           '| Batch | Delivery | Stream | Tenant | Entity | Version | Payload |','| --- | --- | --- | --- | --- | --- | --- |']
    for n,batch in enumerate(fixture()['batches'],1):
        for row in batch:
            payload=json.dumps(row['payload'],sort_keys=True,separators=(',',':')).replace('|','\\|')
            lines.append(f"| {n} | {row['delivery_id']} | {row['stream']} | {row['tenant_id']} | {row['entity_id']} | {row['source_version']} | `{payload}` |")
    lines+=['','The separate illustrative order-lines list is used only for L08; it is not a maintained CDC line-item mart.',
            '```json\n'+json.dumps(fixture()['illustrative_order_lines'],indent=2)+'\n```']
    path.write_text(before+marker+'\n\n'+'\n'.join(lines)+'\n\n'+end+after,encoding='utf-8')
    print('Rendered 32 recorded traces, three model SQL listings and the complete fixture.')


if __name__=='__main__':build()
