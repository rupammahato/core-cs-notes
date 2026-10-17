"""Versioned local RAG mechanics; feature-hash vectors and an extractive model fixture."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'module-16-multi-tenant-saas'))
from saas import SaaS
from runtime import Error, document, identity, number
from collections import Counter
import hashlib
import json
import math
import re
import uuid

CHUNKER,EMBEDDER = 'char120-overlap20-v1','featurehash64-v1'


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


def terms(text):
    return re.findall(r'[^\W_]+',text.casefold(),re.UNICODE)


def vector(text):
    values = [0.0]*64
    for term,count in Counter(terms(text)).items():
        values[int(hashlib.sha256(term.encode()).hexdigest(),16)%64] += count
    norm = math.sqrt(sum(value*value for value in values))
    return [value/norm if norm else 0.0 for value in values]


def pieces(text):
    for ordinal,start in enumerate(range(0,len(text),100)):
        end = min(start+120,len(text))
        yield ordinal,start,end,text[start:end]
        if end==len(text):
            break


def units(question,sources,claims):
    # Exact CHARACTER accounting for this fixture, never provider token/cash usage.
    return 64+len(question)+sum(len(s['text']) for s in sources)+sum(len(c['text']) for c in claims)


class Model:
    def __init__(self,mode='normal',during=None):
        self.mode,self.during,self.calls = mode,during,0

    def call(self,request_id,question,sources):
        self.calls += 1
        if self.during:
            self.during()
        claims = [{'source':sources[0]['chunk'],'text':sources[0]['text']}]
        if self.mode=='bad_citation':
            claims[0]['source'] = 'unprovided_chunk'
        if self.mode=='fabrication':
            claims[0]['text'] = 'Unsupported fabricated statement.'
        result = {'claims':claims,'tools':[],'usage':units(question,sources,claims)}
        if self.mode=='tool_attempt':
            result['tools'] = [{'name':'network_fetch','target':'untrusted-document-url'}]
        if self.mode=='over_usage':
            result['usage'] = 999999
        if self.mode=='timeout':
            raise TimeoutError('injected outcome unknown; no automatic new model call')
        return result


class RAG(SaaS):
    schema = SaaS.schema+'''
        CREATE TABLE IF NOT EXISTS rag_intents(tenant TEXT,user TEXT,operation TEXT,fingerprint TEXT,doc TEXT,
            PRIMARY KEY(tenant,user,operation));
        CREATE TABLE IF NOT EXISTS contents(tenant TEXT,doc TEXT,version INTEGER,text TEXT,digest TEXT,state TEXT,
            PRIMARY KEY(tenant,doc,version));
        CREATE TABLE IF NOT EXISTS ingest(id TEXT PRIMARY KEY,tenant TEXT,doc TEXT,version INTEGER,
            chunker TEXT,embedder TEXT,state TEXT,UNIQUE(tenant,doc,version,chunker,embedder));
        CREATE TABLE IF NOT EXISTS chunks(id TEXT PRIMARY KEY,tenant TEXT,doc TEXT,version INTEGER,
            chunker TEXT,embedder TEXT,ordinal INTEGER,start INTEGER,end INTEGER,text TEXT,vector TEXT);
        CREATE INDEX IF NOT EXISTS chunk_scope ON chunks(tenant,doc,version,embedder);
        CREATE TABLE IF NOT EXISTS budgets(tenant TEXT PRIMARY KEY,total INTEGER,held INTEGER,used INTEGER,
            CHECK(total>=0 AND held>=0 AND used>=0 AND held+used<=total));
        CREATE TABLE IF NOT EXISTS questions(id TEXT PRIMARY KEY,tenant TEXT,user TEXT,operation TEXT,
            fingerprint TEXT,question TEXT,reserved INTEGER,state TEXT,answer TEXT,reason TEXT,used INTEGER,input_units INTEGER,
            UNIQUE(tenant,user,operation));
        CREATE TABLE IF NOT EXISTS evidence(request TEXT,chunk TEXT,tenant TEXT,doc TEXT,version INTEGER,text TEXT,
            PRIMARY KEY(request,chunk));
    '''

    def validate_content(self,title,text):
        if type(title) is not str or not 1<=len(title)<=120 or type(text) is not str or not 1<=len(text)<=1000:
            raise Error(400,'invalid_plain_text_document')
        text = ' '.join(text.split())
        if not terms(text):
            raise Error(400,'empty_document')
        return text

    def enqueue(self,actor,doc,version,text):
        if self.db.execute('SELECT count(*) FROM ingest').fetchone()[0]>=512:
            raise Error(503,'lesson_ingest_retention_cap')
        job = uuid.uuid4().hex
        self.db.execute("INSERT INTO contents VALUES(?,?,?,?,?,'pending')",(actor['tenant'],doc,version,text,fingerprint(text)))
        self.db.execute("INSERT INTO ingest VALUES(?,?,?,?,?,?,'pending')",(job,actor['tenant'],doc,version,CHUNKER,EMBEDDER))
        return job

    def upload(self,token,now,operation,title,text):
        identity(operation)
        text = self.validate_content(title,text)
        intent = fingerprint([title,text])
        with self.transaction():
            actor = self.context(token,now)
            if actor['role']=='viewer':
                raise Error(403,'writer_required')
            old = self.db.execute('SELECT * FROM rag_intents WHERE tenant=? AND user=? AND operation=?',(actor['tenant'],actor['user'],operation)).fetchone()
            if old:
                if old['fingerprint']!=intent:
                    raise Error(409,'changed_upload_intent')
                return self.status_inside(actor,old['doc'])
            count = self.db.execute('SELECT count(*) FROM docs WHERE tenant=? AND deleted=0',(actor['tenant'],)).fetchone()[0]
            quota = self.db.execute('SELECT doc_limit FROM tenants WHERE id=?',(actor['tenant'],)).fetchone()[0]
            if count>=quota:
                raise Error(409,'document_quota')
            if self.db.execute('SELECT count(*) FROM docs').fetchone()[0]>=256:
                raise Error(503,'lesson_document_retention_cap')
            doc = uuid.uuid4().hex
            self.db.execute('INSERT INTO docs VALUES(?,?,?,?,1,0)',(actor['tenant'],doc,actor['user'],title))
            self.db.execute('INSERT INTO rag_intents VALUES(?,?,?,?,?)',(actor['tenant'],actor['user'],operation,intent,doc))
            self.enqueue(actor,doc,1,text)
            self.log(actor,'rag.upload',doc)
            return self.status_inside(actor,doc)

    def status_inside(self,actor,doc_id):
        doc = self.doc(actor,doc_id)
        row = self.db.execute('SELECT state FROM contents WHERE tenant=? AND doc=? AND version=?',(actor['tenant'],doc_id,doc['version'])).fetchone()
        return {'id':doc_id,'title':doc['title'],'version':doc['version'],'index_state':row[0] if row else 'missing'}

    def status(self,token,now,doc_id):
        with self.transaction():
            return self.status_inside(self.context(token,now),doc_id)

    def update(self,token,now,doc_id,expected_version,title,text):
        number(expected_version,1)
        text = self.validate_content(title,text)
        with self.transaction():
            actor = self.context(token,now)
            row = self.doc(actor,doc_id,True)
            if row['version']!=expected_version:
                raise Error(409,'version_conflict')
            self.db.execute('UPDATE docs SET title=?,version=version+1 WHERE tenant=? AND id=?',(title,actor['tenant'],doc_id))
            self.enqueue(actor,doc_id,expected_version+1,text)
            self.log(actor,'rag.update',doc_id)
            return self.status_inside(actor,doc_id)

    def capture(self,job_id):
        row = self.db.execute('''SELECT i.*,c.text,c.digest FROM ingest i JOIN contents c
            ON c.tenant=i.tenant AND c.doc=i.doc AND c.version=i.version WHERE i.id=?''',(identity(job_id),)).fetchone()
        if row is None:
            raise Error(404,'ingest_not_found')
        return dict(row)

    def publish(self,snapshot):
        # Chunking/vector computation is outside the commit transaction.
        prepared = [(n,start,end,text,json.dumps(vector(text))) for n,start,end,text in pieces(snapshot['text'])]
        with self.transaction():
            job = self.db.execute('SELECT * FROM ingest WHERE id=?',(snapshot['id'],)).fetchone()
            source = self.db.execute('SELECT * FROM docs WHERE tenant=? AND id=?',(snapshot['tenant'],snapshot['doc'])).fetchone()
            if not job or not source or source['deleted'] or source['version']!=snapshot['version'] or (snapshot['chunker'],snapshot['embedder'])!=(CHUNKER,EMBEDDER):
                if job:
                    self.db.execute("UPDATE ingest SET state='obsolete' WHERE id=?",(job['id'],))
                return 'stale'
            if tuple(job[k] for k in ('tenant','doc','version','chunker','embedder'))!=tuple(snapshot[k] for k in ('tenant','doc','version','chunker','embedder')):
                raise Error(409,'changed_ingest_identity')
            if job['state']=='ready':
                return 'replay'
            current = self.db.execute('SELECT digest FROM contents WHERE tenant=? AND doc=? AND version=?',(snapshot['tenant'],snapshot['doc'],snapshot['version'])).fetchone()
            if not current or current[0]!=snapshot['digest'] or fingerprint(snapshot['text'])!=snapshot['digest']:
                raise Error(409,'changed_ingest_snapshot')
            self.db.execute('DELETE FROM chunks WHERE tenant=? AND doc=?',(snapshot['tenant'],snapshot['doc']))
            for ordinal,start,end,text,encoded in prepared:
                cid = fingerprint([snapshot['tenant'],snapshot['doc'],snapshot['version'],CHUNKER,EMBEDDER,ordinal])
                self.db.execute('INSERT INTO chunks VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                    (cid,snapshot['tenant'],snapshot['doc'],snapshot['version'],CHUNKER,EMBEDDER,ordinal,start,end,text,encoded))
            self.db.execute("UPDATE contents SET state='ready' WHERE tenant=? AND doc=? AND version=?",(snapshot['tenant'],snapshot['doc'],snapshot['version']))
            self.db.execute("UPDATE ingest SET state='ready' WHERE id=?",(snapshot['id'],))
            return 'applied'

    def retrieve_inside(self,actor,question):
        if type(question) is not str or not 1<=len(question)<=100 or not 1<=len(terms(question))<=8:
            raise Error(400,'invalid_question')
        rows = self.db.execute('''SELECT k.* FROM chunks k JOIN docs d ON d.tenant=k.tenant AND d.id=k.doc
            JOIN contents c ON c.tenant=k.tenant AND c.doc=k.doc AND c.version=k.version
            WHERE k.tenant=? AND d.deleted=0 AND d.version=k.version AND c.state='ready'
            AND k.chunker=? AND k.embedder=? AND (? IN ('owner','admin') OR d.owner=? OR EXISTS(
                SELECT 1 FROM shares s WHERE s.tenant=d.tenant AND s.doc=d.id AND s.reader=?))''',
            (actor['tenant'],CHUNKER,EMBEDDER,actor['role'],actor['user'],actor['user'])).fetchall()
        query_vector,wanted = vector(question),set(terms(question))
        ranked = []
        for row in rows:
            if not wanted.intersection(terms(row['text'])):
                continue
            score = sum(a*b for a,b in zip(query_vector,json.loads(row['vector'])))
            ranked.append((score,row['id'],dict(row)))
        ranked.sort(key=lambda r:(-r[0],r[1]))
        return [{'chunk':r['id'],'doc':r['doc'],'version':r['version'],'text':r['text'],
                 'start':r['start'],'end':r['end']} for _,_,r in ranked[:3]]

    def retrieve(self,token,now,question):
        with self.transaction():
            return self.retrieve_inside(self.context(token,now),question)

    def budget(self,tenant,total):
        # Trusted configuration, not a money account or pricing table.
        identity(tenant)
        number(total,1,1000000)
        self.db.execute('INSERT INTO budgets VALUES(?,?,0,0)',(tenant,total))

    def prepare(self,token,now,operation,question,reserve):
        identity(operation)
        number(reserve,1,2000)
        intent = fingerprint([question,reserve,CHUNKER,EMBEDDER])
        with self.transaction():
            actor = self.context(token,now)
            old = self.db.execute('SELECT id FROM questions WHERE tenant=? AND user=? AND operation=?',(actor['tenant'],actor['user'],operation)).fetchone()
            if old:
                prior = self.db.execute('SELECT * FROM questions WHERE id=?',(old[0],)).fetchone()
                if prior['fingerprint']!=intent:
                    raise Error(409,'changed_question_intent')
                return {'id':prior['id'],'state':prior['state']}
            sources = self.retrieve_inside(actor,question)
            if self.db.execute('SELECT count(*) FROM questions').fetchone()[0]>=128:
                raise Error(503,'lesson_question_retention_cap')
            if sources and reserve<units(question,sources,[])+512:
                raise Error(400,'reservation_below_fixture_worst_case')
            request = uuid.uuid4().hex
            held,state = (reserve,'prepared') if sources else (0,'abstained')
            if held:
                changed = self.db.execute('UPDATE budgets SET held=held+? WHERE tenant=? AND total-held-used>=?',(held,actor['tenant'],held)).rowcount
                if changed!=1:
                    raise Error(409,'budget_unavailable')
            self.db.execute('INSERT INTO questions VALUES(?,?,?,?,?,?,?,?,NULL,NULL,0,?)',
                (request,actor['tenant'],actor['user'],operation,intent,question,held,state,units(question,sources,[])))
            for source in sources:
                self.db.execute('INSERT INTO evidence VALUES(?,?,?,?,?,?)',(request,source['chunk'],actor['tenant'],source['doc'],source['version'],source['text']))
            return {'id':request,'state':state}

    def current_evidence(self,request):
        if request['reason']=='source_purged':
            return False
        member = self.db.execute('SELECT m.role FROM members m JOIN users u ON u.id=m.user WHERE tenant=? AND user=? AND m.active=1 AND u.active=1',(request['tenant'],request['user'])).fetchone()
        if member is None:
            return False
        actor = {'tenant':request['tenant'],'user':request['user'],'role':member['role']}
        for row in self.db.execute('SELECT * FROM evidence WHERE request=?',(request['id'],)).fetchall():
            try:
                doc = self.doc(actor,row['doc'])
            except Error:
                return False
            if doc['version']!=row['version']:
                return False
        return True

    def begin(self,token,now,request_id):
        with self.transaction():
            actor = self.context(token,now)
            request = self.db.execute('SELECT * FROM questions WHERE tenant=? AND user=? AND id=?',(actor['tenant'],actor['user'],identity(request_id))).fetchone()
            if not request:
                raise Error(404,'question_not_found')
            if request['state']!='prepared':
                return None
            if not self.current_evidence(request):
                self.db.execute("UPDATE questions SET state='blocked',reason='sources_changed_before_call' WHERE id=?",(request_id,))
                self.db.execute('UPDATE budgets SET held=held-? WHERE tenant=?',(request['reserved'],request['tenant']))
                return None
            self.db.execute("UPDATE questions SET state='running' WHERE id=?",(request_id,))
            sources = [dict(r) for r in self.db.execute('SELECT * FROM evidence WHERE request=? ORDER BY chunk',(request_id,))]
            return dict(request),sources

    def finish(self,request_id,response):
        with self.transaction():
            request = self.db.execute('SELECT * FROM questions WHERE id=?',(identity(request_id),)).fetchone()
            if request is None:
                raise Error(404,'question_not_found')
            if request['state'] not in ('running','unknown','usage_review'):
                return request['state']
            sources = [dict(r) for r in self.db.execute('SELECT * FROM evidence WHERE request=?',(request_id,))]
            valid = type(response) is dict and set(response)=={'claims','tools','usage'} and type(response['claims']) is list and 1<=len(response['claims'])<=3
            claims = response['claims'] if valid else []
            valid = valid and all(type(c) is dict and set(c)=={'source','text'} and type(c['text']) is str and type(c['source']) is str for c in claims)
            actual = request['input_units']+sum(len(c['text']) for c in claims) if valid else -1
            if not valid or sum(len(c['text']) for c in claims)>512 or type(response['usage']) is not int or response['usage']!=actual or actual>request['reserved']:
                self.db.execute("UPDATE questions SET state='usage_review',reason='untrusted_or_excess_usage' WHERE id=?",(request_id,))
                return 'usage_review'
            allowed = {s['chunk']:s for s in sources}
            accepted = response['tools']==[] and all(c['source'] in allowed and c['text']==allowed[c['source']]['text'] for c in claims)
            state,reason = ('done',None) if accepted else ('rejected','invalid_citation_or_tool')
            if not self.current_evidence(request):
                state,reason = 'blocked','sources_changed_during_call'
            answer = json.dumps(claims,ensure_ascii=False) if state=='done' else None
            self.db.execute('UPDATE budgets SET held=held-?,used=used+? WHERE tenant=?',(request['reserved'],actual,request['tenant']))
            self.db.execute('UPDATE questions SET state=?,answer=?,reason=?,used=? WHERE id=?',(state,answer,reason,actual,request_id))
            return state

    def generate(self,token,now,request_id,model):
        work = self.begin(token,now,request_id)
        if work:
            request,sources = work
            try:
                response = model.call(request_id,request['question'],sources)
            except TimeoutError:
                self.db.execute("UPDATE questions SET state='unknown',reason='model_outcome_unknown' WHERE id=? AND state='running'",(request_id,))
            else:
                self.finish(request_id,response)
        return self.result(token,now,request_id)

    def result(self,token,now,request_id):
        with self.transaction():
            actor = self.context(token,now)
            request = self.db.execute('SELECT * FROM questions WHERE tenant=? AND user=? AND id=?',(actor['tenant'],actor['user'],identity(request_id))).fetchone()
            if request is None:
                raise Error(404,'question_not_found')
            if request['state']=='done' and not self.current_evidence(request):
                raise Error(409,'answer_sources_changed')
            return {'id':request_id,'state':request['state'],'claims':json.loads(request['answer']) if request['answer'] else [],
                'used_character_units':request['used']}

    def citation(self,token,now,chunk_id):
        with self.transaction():
            actor = self.context(token,now)
            row = self.db.execute('SELECT * FROM chunks WHERE tenant=? AND id=?',(actor['tenant'],identity(chunk_id))).fetchone()
            if row is None:
                raise Error(404,'citation_not_found')
            doc = self.doc(actor,row['doc'])
            if doc['version']!=row['version'] or row['embedder']!=EMBEDDER or row['chunker']!=CHUNKER:
                raise Error(404,'citation_not_found')
            return {'document':row['doc'],'title':doc['title'],'version':row['version'],
                'start':row['start'],'end':row['end'],'quote':row['text']}

    def delete(self,token,now,doc_id):
        with self.transaction():
            actor = self.context(token,now)
            self.doc(actor,doc_id,True)
            self.db.execute('UPDATE docs SET deleted=1,version=version+1 WHERE tenant=? AND id=?',(actor['tenant'],doc_id))
            self.log(actor,'rag.delete',doc_id)

    def purge(self,token,now,doc_id):
        with self.transaction():
            actor = self.context(token,now)
            row = self.db.execute('SELECT * FROM docs WHERE tenant=? AND id=?',(actor['tenant'],identity(doc_id))).fetchone()
            if not row or actor['role']=='viewer' or not (actor['role'] in ('owner','admin') or row['owner']==actor['user']):
                raise Error(404,'document_not_found')
            if not row['deleted']:
                raise Error(409,'delete_before_purge')
            requests = [r[0] for r in self.db.execute('SELECT DISTINCT request FROM evidence WHERE tenant=? AND doc=?',(actor['tenant'],doc_id))]
            for request_id in requests:
                # Preserve state/reservation for unresolved calls; wipe stored text/results.
                request = self.db.execute('SELECT state,reserved FROM questions WHERE id=?',(request_id,)).fetchone()
                if request['state']=='prepared':
                    self.db.execute('UPDATE budgets SET held=held-? WHERE tenant=?',(request['reserved'],actor['tenant']))
                self.db.execute("UPDATE questions SET answer=NULL,question='',reason='source_purged' WHERE id=?",(request_id,))
                self.db.execute("UPDATE questions SET state='purged' WHERE id=? AND state IN ('prepared','done','abstained','blocked','rejected')",(request_id,))
                self.db.execute('DELETE FROM evidence WHERE request=?',(request_id,))
            count = self.db.execute('DELETE FROM chunks WHERE tenant=? AND doc=?',(actor['tenant'],doc_id)).rowcount
            self.db.execute('DELETE FROM contents WHERE tenant=? AND doc=?',(actor['tenant'],doc_id))
            self.db.execute("UPDATE ingest SET state='obsolete' WHERE tenant=? AND doc=?",(actor['tenant'],doc_id))
            self.log(actor,'rag.purge',doc_id)
            return {'removed_chunks':count,'requests_redacted':len(requests),'tombstone_retained':True}


def estimates():
    return {'documents':100000,'assumed_chunks_per_document':20,'vectors':2000000,
        'assumed_production_dimensions':768,'float32_vector_bytes':6144000000,
        'logical_float32_vector_GB':6.144,'fixture_dimensions':64,'fixture_context_chunks':3,
        'fixture_output_character_cap':512,'provider_tokens_or_money_measured':False,'measured_capacity':False}


def dispatch(item,_lesson_identity,method,path,raw,headers,clock,model):
    auth = headers.get('Authorization','')
    token,now = auth[7:] if auth.startswith('Bearer ') else '',clock()
    if method=='POST' and path=='/documents':
        return 202,item.upload(token,now,headers.get('Idempotency-Key',''),**document(raw,['title','text']))
    match = re.fullmatch(r'/documents/([a-f0-9]{32})(?:/(purge|shares)(?:/([A-Za-z0-9_-]{1,64}))?)?',path)
    if match and not match[2] and method=='GET':
        return 200,item.status(token,now,match[1])
    if match and not match[2] and method=='PUT':
        return 202,item.update(token,now,match[1],**document(raw,['expected_version','title','text']))
    if match and not match[2] and method=='DELETE':
        item.delete(token,now,match[1])
        return 200,{'deleted':True}
    if match and match[2]=='purge' and not match[3] and method=='POST':
        return 200,item.purge(token,now,match[1])
    if match and match[2]=='shares' and match[3] and method in ('PUT','DELETE'):
        return 200,item.share(token,now,match[1],match[3],method=='PUT')
    if path=='/retrieve' and method=='POST':
        return 200,{'items':item.retrieve(token,now,**document(raw,['question']))}
    if path=='/questions' and method=='POST':
        request = item.prepare(token,now,headers.get('Idempotency-Key',''),**document(raw,['question','reserve']))
        result = item.generate(token,now,request['id'],model)
        return (202 if result['state'] in ('running','unknown','usage_review') else 200),result
    match = re.fullmatch(r'/questions/([a-f0-9]{32})',path)
    if match and method=='GET':
        return 200,item.result(token,now,match[1])
    match = re.fullmatch(r'/citations/([a-f0-9]{64})',path)
    if match and method=='GET':
        return 200,item.citation(token,now,match[1])
    item.who(token,now)
    raise Error(404,'unknown_route')
