import json
from pathlib import Path

class Checks:
    def __init__(self,group):self.group=group;self.rows=[]
    def check(self,name,operation):
        operation();self.rows.append({'name':name,'passed':True});print('PASS '+self.group+': '+name)
    def save(self,**extra):
        result={'group':self.group,'total':len(self.rows),'checks':self.rows,**extra}
        Path(__file__).with_name(self.group+'-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
        return result

def equal(actual,expected):
    if actual!=expected:raise AssertionError((actual,expected))

def require(condition):
    if not condition:raise AssertionError('condition failed')

def rejects(kind,operation):
    try:operation()
    except kind:return
    raise AssertionError('expected '+kind.__name__)
