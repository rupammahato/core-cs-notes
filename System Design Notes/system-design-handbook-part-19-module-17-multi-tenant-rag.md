# Architecture and System Design Placement Handbook — Part 19
# S12: Multi-tenant RAG Knowledge-base Platform

**Estimated time: 5–7 hours | Architecture numeric module: 17 | Requires: A0–A4, S3, S7, S9 and S11; Resume M22–M26 refreshers**

---

## Why this module exists

A document is updated while an embedding worker retries its old version. A valid user queries another tenant's chunks. A generated answer cites a real document, but not the excerpt supplied to the model. A timeout leaves usage uncertain. These are architecture and authority problems before they are prompt-engineering problems.

**Organizing principle: keep source, index, request evidence and accepted output tied to verified tenant, permission and version boundaries.**

This chapter combines S11's unchanged session/membership authority with versioned plaintext ingestion, deterministic chunk identities, local vector ranking, current permission checks, generation reservations, strict extractive citation validation and deletion cleanup. A model fixture can return invalid references, fabricated text, a tool request or an unknown outcome. Actual HTTP exercises the request path.

The vectors are feature-hashed word counts, not learned semantic embeddings. The model copies an allowed excerpt; it is not a real LLM. There are no paid APIs, external vector service, PDF parser, object store, tool execution or streaming transport. Those deployment choices are explained separately. The 30 Q&As are curated design practice, not measured employer-frequency rankings. This chapter develops Q37/Q51/Q59 from the architecture bank.

---

## 1. Prompt and clarification questions

**Prompt:** users upload tenant-private knowledge, share selected documents and ask grounded questions. Edits, revocation, deletion and retries must not expose old or foreign content. Model work has a bounded budget and uncertain outcomes must remain visible.

| Clarification | Architectural consequence |
| --- | --- |
| Supported formats and ingestion trust? | Upload validation, extraction isolation, OCR and quarantine |
| User/tenant/document permissions? | Session context, candidate filters and final source checks |
| What does grounded mean? | Citation membership, exact quotes, entailment and answer correctness differ |
| Required edit/delete freshness? | Canonical versions, tombstones and cleanup contracts |
| Lexical, semantic or hybrid retrieval? | Index model, ranking/evaluation and migration |
| Languages and document structure? | Tokenization, chunk boundaries and citation offsets |
| Which model/provider and data policy? | Context limits, transport, retention, region and cost |
| Streaming or buffered answer? | Whether provisional text can escape before validation |
| Tools or read-only answers? | Separate tool authority, allowlists and side-effect budgets |
| Token, money and tenant quotas? | Reservation, provider usage normalization and reconciliation |

The baseline accepts bounded plain text, normalizes whitespace, uses character-window chunks and returns exact quoted evidence. Documents can be privately owned or explicitly read-shared. Owner/admin retain S11's tenant-wide document rights. “Public to all tenants,” anonymous upload, conversations and arbitrary tools are not part of this API.

---

## 2. Contract and invariants

| Concern | Executed policy |
| --- | --- |
| Identity | Current S11 opaque session, active user/membership and scoped role |
| Upload | Stable tenant/user/operation binds normalized text and title |
| Update | Current manager plus expected source version; new durable ingest job |
| Ingest | Source text/digest and job commit with the document mutation |
| Chunk identity | Hash of tenant/doc/version/chunker/embedder/ordinal |
| Publication | Current canonical version only; chunks/readiness/job finish atomically |
| Retrieval | Tenant, current source version and current permission before top-three ranking |
| Generation | One durable request identity, one local begin transition, bounded reservation |
| Acceptance | Exact supplied quote/reference, no tool request, valid fixture usage and current evidence |
| Delivery | Current requester/session plus current permission/version for completed answers/citations |
| Delete | Immediate canonical tombstone; separate row cleanup/redaction |

The model has no authority to select a new tenant, fetch another chunk, execute a tool or override a revoked grant. Retrieved text is data, even when it contains instructions. A reference to an existing chunk is insufficient: it must be evidence actually supplied to this request and still permitted/current at acceptance.

The local read/publish decisions are transactional. They do not promise revocation of bytes already delivered, removal from external providers/backups, or distributed linearizability. The implementation has no learned-model correctness or prompt-injection-immunity claim.

---

## 3. Corpus, vector and generation estimates

```json
{
  "documents": 100000,
  "assumed_chunks_per_document": 20,
  "vectors": 2000000,
  "assumed_production_dimensions": 768,
  "float32_vector_bytes": 6144000000,
  "logical_float32_vector_GB": 6.144,
  "fixture_dimensions": 64,
  "fixture_context_chunks": 3,
  "fixture_output_character_cap": 512,
  "provider_tokens_or_money_measured": false,
  "measured_capacity": false
}
```

100,000 documents with twenty assumed chunks each produce two million vectors. At 768 float32 dimensions, raw vector payload alone is 6.144 decimal GB. Index structures, source text, chunk metadata, replicas, delete history and backups add storage. This arithmetic is not the memory footprint of pgvector or a managed vector service.

The fixture uses 64-dimensional feature-hash vectors, at most three context chunks and a 512-character output bound. These limits make orchestration reproducible; they do not model a provider's tokenization or context window. Input normalization, repeated overlap, metadata prompts, tools and conversation history all affect real input-token cost.

For production planning, estimate ingestion bytes/day, parse/OCR time, chunk count, embedding requests/tokens, searchable lag, question rate, retrieval/rerank latency, model input/output tokens and retry amplification. Separate one-time reindex cost from ongoing questions. A new model/index generation may temporarily double stored vectors and embedding spend.

---

## 4. Data model, source versions and index profiles

| Table | Responsibility |
| --- | --- |
| Inherited `users/members/sessions/docs/shares` | Current identity, scope, source title/version and visibility |
| `rag_intents` | Original immutable upload fingerprint and source identity |
| `contents(tenant,doc,version)` | Normalized version text, checksum and indexing readiness |
| `ingest` | Durable unique version/chunker/embedder job and state |
| `chunks` | Exact normalized-source offsets, text, vector and profile identity |
| `budgets` | Tenant's total/held/used fixture character units |
| `questions` | Scoped operation, request state, reservation, input-unit count and accepted answer |
| `evidence(request,chunk)` | Exact request-scoped source/version/text snapshot |

Chunk offsets refer to normalized text, not original PDF page coordinates. A real parser must preserve a mapping to pages/sections/cells if citations need those anchors. Do not invent page numbers from character windows or silently change normalization without changing the parser/chunker profile.

Embedding dimensions alone do not define a vector space. Model identity/version, preprocessing and distance metric also matter. The executed profiles are fixed as `char120-overlap20-v1` and `featurehash64-v1`; unknown profiles are rejected for publication. A migration would need parallel generations, evaluation and a controlled query switch. This code does not implement that online migration.

---

## 5. API and trust boundaries

| Actual endpoint | Meaning |
| --- | --- |
| `POST /documents` | title/text plus Idempotency-Key; 202 pending source/ingest |
| `GET /documents/:id` | Current scoped title/version/index status |
| `PUT /documents/:id` | expected_version/title/text; 202 new version |
| `PUT/DELETE /documents/:id/shares/:reader` | S11 current manager/read-share policy |
| `POST /retrieve` | Bounded question; authorized current context candidates |
| `POST /questions` | question/reserve plus Idempotency-Key; buffered fixture generation |
| `GET /questions/:id` | Current requester and source checks before answer delivery |
| `GET /citations/:chunk` | Current authorized exact source/version/offset/quote |
| `DELETE /documents/:id` | Current manager commits a newer tombstone |
| `POST /documents/:id/purge` | Authorized cleanup after deletion |

Tenant comes from the verified S11 session, and the fixed lesson bearer identity is not authority. Status/citation/answer routes cannot use another tenant's IDs as permission. The question body cannot supply a namespace, raw retrieval filter, model tool or another owner.

Session issuance, budget configuration, indexing capture/publication and completion reconciliation are trusted fixture methods. Production ingestion workers and model adapters need authenticated service identities and bounded access of their own. The runtime does not contact an external identity, model or storage provider.

---

## 6. Smallest architecture and end-to-end traces

```mermaid
flowchart LR
    Writer[Authenticated writer] --> Source[Validate source and expected version]
    Source --> Canonical[(Canonical documents and content)]
    Source --> Jobs[(Durable versioned ingest)]
    Jobs --> Build[Chunk and compute local vectors]
    Build --> Fence[Current-version publication fence]
    Fence --> Chunks[(Versioned chunks and readiness)]
    Reader[Authenticated questioner] --> Retrieve[Current tenant permission and version]
    Chunks --> Retrieve
    Canonical --> Retrieve
    Retrieve --> Reserve[Store exact evidence and reserve budget]
    Reserve --> Model[Untrusted model fixture output]
    Model --> Validate[Quote reference tool usage and current-source checks]
    Validate --> Accepted[(Accepted answer and atomic settlement)]
    Accepted --> Deliver[Recheck access and version]
```

**Ingestion:** authorized source mutation → versioned text/checksum/job commit → compute chunks/vectors outside the publication transaction → check current document/profile → replace chunk set and mark ready together. A delayed old build cannot delete the new generation's chunks.

**Question:** authorized current retrieval → save exact request evidence and reserve tenant units → transition prepared to running → call model outside the database transaction → validate structure/evidence/usage/current access → settle budget and store only accepted output → recheck at delivery.

**Deletion:** canonical tombstone immediately removes new retrieval/citation access → cleanup removes local content/chunk rows and redacts associated stored request text/results → retain tombstone and minimal operation/usage evidence. Unknown already-started work keeps its reservation until known completion/reconciliation.

---

## 7. Shared runtime and reused S11 authority

```python
"""Standard-library support shared by S4-S6; no production auth/server claim."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re
import sqlite3

CREDENTIALS = {'lesson-alice':('t1','alice'), 'lesson-bob':('t1','bob'),
               'lesson-carol':('t1','carol'), 'lesson-other':('t2','alice')}


class Error(Exception):
    def __init__(self, status, reason):
        self.status, self.reason = status, reason


def identity(value):
    if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', value):
        raise Error(400,'invalid_identity')
    return value


def number(value, low=0, high=10**15):
    if type(value) is not int or not low <= value <= high:
        raise Error(400,'invalid_integer')
    return value


def require(user):
    if user is None:
        raise Error(401,'lesson_credential_required')
    return user


def document(raw, fields):
    try:
        value = json.loads(raw)
    except (ValueError,UnicodeError):
        raise Error(400,'invalid_json') from None
    if type(value) is not dict or set(value) != set(fields):
        raise Error(400,'invalid_fields')
    return value


class Database:
    schema = ''

    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=0.5, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        try:
            self.db.executescript('PRAGMA foreign_keys=ON;'+self.schema)
        except BaseException:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise


def server(factory, dispatch):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, status, value):
            raw = json.dumps(value,ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('Connection','close')
            self.end_headers()
            self.wfile.write(raw)
            self.close_connection = True

        def handle_request(self):
            item = None
            try:
                length = self.headers.get('Content-Length','0')
                if self.headers.get('Transfer-Encoding') or not length.isascii() or not length.isdigit() or len(length)>6 or int(length)>8192:
                    raise Error(413,'body_or_framing_limit')
                raw = self.rfile.read(int(length))
                if len(raw) != int(length):
                    raise Error(400,'incomplete_body')
                auth = self.headers.get('Authorization','')
                user = CREDENTIALS.get(auth[7:]) if auth.startswith('Bearer ') else None
                item = factory()
                status, value = dispatch(item,user,self.command,self.path,raw,self.headers)
                self.reply(status,value)
            except Error as error:
                self.reply(error.status,{'error':error.reason})
            except sqlite3.Error:
                self.reply(503,{'error':'metadata_unavailable'})
            except (ValueError,UnicodeError):
                self.reply(400,{'error':'invalid_input'})
            finally:
                if item is not None:
                    item.close()

        do_GET = handle_request
        do_POST = handle_request
        do_PUT = handle_request
        do_DELETE = handle_request
    return ThreadingHTTPServer(('127.0.0.1',0),Handler)
```

`rag.py` imports `SaaS` from `../module-16-multi-tenant-saas/saas.py`, unchanged from [S11](/docs/system-design/multi-tenant-saas). It reuses current session, membership, ownership, share and audit helpers; the RAG dispatcher exposes only this chapter's stated endpoints. Run the repository example with its dependency folders intact. The content audit records the dependency checksum separately from the embedded local source.

The helper supplies bounded JSON and real loopback HTTP, not production sessions, TLS, browser authentication or streaming. Inherited methods that create title-only documents are not exposed by the RAG API; source changes use the versioned upload/update path shown below.

---

## 8. Executable versioned ingestion, retrieval and acceptance

```python
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
```

`vector` hashes normalized term counts into 64 bins and normalizes them. This implements actual deterministic numerical ranking but has collisions and no learned synonym/semantic knowledge. Retrieval also requires a literal term overlap, then ranks the current authorized candidate set by dot product. It scans a bounded local corpus; no ANN index runs.

`Model` emits one copied chunk. Invalid-reference, fabrication, tool and timeout modes are controlled fault fixtures. The exact quote rule is intentionally stricter than abstractive RAG and cannot evaluate general paraphrase entailment. A model's output is still untrusted even when it parses as JSON.

---

## 9. Source/index lag and atomic publication

```json
{
  "source_after_edit_version": 2,
  "old_chunks_during_index_lag": 0,
  "old_citation_after_edit": 404,
  "delayed_old_publish": "stale",
  "new_chunk_identity_changed": true,
  "profile": {
    "chunker": "char120-overlap20-v1",
    "embedder": "featurehash64-v1"
  },
  "old_and_new_embedding_spaces_mixed": false
}
```

An edit increments source version before the new index is ready. Old chunks disappear from retrieval through the canonical-version predicate; the new text can be temporarily unavailable until publication. The original upload operation still identifies the same edited document because its fingerprint is retained independently from current text.

The worker captures immutable version text and checksum. On commit, it verifies canonical version, job identity and profile before replacing chunks. A late old retry becomes stale; it cannot overwrite the current generation. A completed current publication replays without duplicate chunks.

```json
{
  "source_content_intent_job_rollback_tested": true,
  "chunk_readiness_job_rollback_tested": true,
  "competing_publish_results": [
    "applied",
    "replay"
  ],
  "lease_or_external_embedding_service_executed": false
}
```

Fault injection verifies source/content/intent rollback when job insertion fails, and chunk/readiness rollback when job completion fails. Two publishers use separate connections and converge on applied/replay. The example has no ingest daemon, external embedding API, worker lease/attempt budget or durable provider response. S7 supplies the relevant claim/retry concepts when those boundaries are added.

---

## 10. Scoped retrieval, citations and permission races

```json
{
  "private_other_reader_results": 0,
  "shared_reader_results": 1,
  "revoked_reader_results": 0,
  "revoked_citation": 404,
  "foreign_document_status": 404,
  "tenant_permission_version_filter_before_top_k": true,
  "embedding": "deterministic feature hashing, not learned semantics"
}
```

The SQL candidate query checks tenant, nondeleted current document version, ready content, profile and current owner/admin/share policy before Python ranking/top-three selection. A private higher-scoring candidate cannot displace permitted results by being selected first and discarded afterward. Direct citation access repeats the source authorization and version check.

A request evidence record binds exact chunk ID, source document version and supplied text. Accepting a reference requires membership in that request's evidence, exact quote equality under this extractive contract and current source authority. It does not prove that the source is true, the answer is relevant, or a paraphrase is entailed.

```json
{
  "revoke_during_call": "blocked",
  "known_inflight_usage_settled": true,
  "revoke_before_call_model_calls": 0,
  "revoke_before_call_reservation_released": true,
  "completed_answer_after_revoke": 409,
  "already_delivered_bytes_revoked": false
}
```

Revocation before the model call blocks and releases an unstarted reservation. Revocation during the call suppresses output but still settles known fixture usage because work already happened. A completed answer cannot be read after later revocation; an edit similarly makes its source snapshot outdated. A valid session alone never overrides these source checks.

This revalidation cannot undo text already sent to a model provider or previously delivered to a user. Provider data handling and external download/stream boundaries require their own contract. Use least necessary context and prevent unauthorized data from entering the prompt in the first place.

---

## 11. Request identity, budgets, uncertainty and deletion

```json
{
  "accepted_state": "done",
  "claims": 1,
  "usage_character_units": 171,
  "reservation_units": 1000,
  "held_after_known_completion": 0,
  "model_calls_after_idempotent_retry": 1,
  "no_context_state": "abstained",
  "no_context_model_calls": 0,
  "provider_tokens_or_cash": false
}
```

The fixture reserves a worst-case character allowance before calling the model, stores request input-unit count, and atomically settles known usage with answer acceptance. The counter includes fixed overhead plus question/context/output characters; it is not provider tokens, money or the S8 CREDIT ledger. No context means abstention without a model call or reservation.

```json
{
  "invalid_output_states": {
    "bad_citation": "rejected",
    "fabrication": "rejected",
    "tool_attempt": "rejected",
    "over_usage": "usage_review"
  },
  "timeout_state": "unknown",
  "automatic_retry_model_calls": 1,
  "unknown_reservation_released_automatically": false,
  "known_response_reconciled": "done",
  "network_tool_executed": false,
  "real_provider_contacted": false
}
```

Unsupported references, fabricated quotes and tool requests cannot become accepted output. Valid known usage can still consume budget for a rejected response. An untrusted/excess usage response goes to usage_review and retains the reservation; timeout becomes unknown and also retains it. An idempotent HTTP retry does not start another model call. A trusted known response can reconcile once.

```json
{
  "competing_publish_results": [
    "applied",
    "replay"
  ],
  "budget_units_available": 1000,
  "simultaneous_reservations_of": 1000,
  "accepted_reservations": 1,
  "rejected_reservation_status": 409,
  "held_after_race": 1000,
  "simultaneous_generation_model_calls": 1,
  "usage_and_answer_rollback_tested": true
}
```

Two callers can capture the same question identity, but only one transitions prepared to running. Concurrent tenant reservations cannot exceed the configured allowance. An injected acceptance failure rolls back both usage settlement and stored answer; retrying the known completion does not need another model call. A process crash after begin can leave running work needing reconciliation; no automatic crash recovery/sweeper is implemented.

```json
{
  "deleted_before_purge_results": 0,
  "deleted_citation": 404,
  "late_publish_after_delete": "stale",
  "removed_chunk_rows": 1,
  "source_content_rows_remaining": 0,
  "prepared_request_after_purge": "purged",
  "inflight_reservation_kept_until_known_completion": true,
  "late_completion_after_purge": "blocked",
  "tombstone_retained": true,
  "backups_or_external_provider_data_erased": false
}
```

Delete immediately hides chunks/citations and fences delayed indexing. Purge separately removes local source/chunk rows and redacts all stored context/answers for affected requests, conservatively including their other supplied context. It releases unstarted reservations but keeps unresolved in-flight reservations. A late known response is blocked and can settle its retained input count without restoring text.

The retained tombstone prevents replay resurrection. SQL DELETE here is logical row removal, not secure disk erasure, backup removal or deletion from a provider that already received text. Cleanup covers this local source/index/request model only; original files, OCR caches, graph nodes, vector services, conversations and backups need explicit lifecycle coverage in a deployment.

---

## 12. Actual HTTP evidence

```json
{
  "upload": 202,
  "question_with_accepted_quote": 200,
  "foreign_citation": 404,
  "other_requester_answer": 404,
  "tenant_override": 400,
  "revoked_retrieval_results": 0,
  "old_answer_after_edit": 409,
  "delete": 200,
  "purge": 200,
  "anonymous": 401,
  "model_calls_after_question_retry": 1,
  "real_loopback_HTTP": true,
  "real_LLM_embedding_or_vector_service": false
}
```

The verifier sends real upload/status, retrieval, question, citation, share/revoke, update, delete and purge requests through an owned loopback listener. HTTP question replay keeps one model-fixture call. The worker publication and upstream session issuance remain direct trusted calls, not external queue/auth integrations.

Unknown/running/usage-review question submission returns 202; known completed/abstained/rejected states return 200 with explicit state. A successful HTTP transport response does not mean the answer was accepted. The listener and database connections close and the temporary directory is removed; port 3000 stays unused.

---

## 13. Retrieval, chunking and orchestration alternatives

| Choice | Benefit | Question to evaluate |
| --- | --- | --- |
| Fixed character/token windows | Simple bounded chunks | Broken tables/sentences, overlap cost and citation anchors |
| Structure-aware chunks | Preserve headings/pages/sections | Parser fidelity, large sections and stable identifiers |
| Lexical retrieval | Useful for exact identifiers/terms | Language normalization and vocabulary mismatch |
| Learned dense vectors | Retrieve conceptual similarity | Model space, recall, permissions and drift |
| Hybrid plus reranking | Combine candidates and improve selected ordering | More latency, budgets and judged evaluation |
| Database-native vector retrieval | Close source/ACL joins and operational reuse | Query plan, selectivity, ANN recall and scale |
| Managed vector service | Independent retrieval operations | Namespace authority, metadata lag, external deletion and cost |

The original RAG research combines parametric generation with retrieved nonparametric evidence; it does not make every application with a vector database grounded or secure. [Lewis et al. RAG paper](https://arxiv.org/abs/2005.11401).

pgvector supports exact and approximate search, with filtering/ANN choices affecting candidate recall and query behavior. The fixture executes neither pgvector nor a managed service. If a remote engine returns a fixed unfiltered top-k, current permission postfiltering can underfill results; use supported filters or bounded overfetch with a truthful result contract. [pgvector documentation](https://github.com/pgvector/pgvector).

Namespaces are useful tenant partitioning mechanisms when selected from trusted context. They do not establish the caller's membership or document-level sharing rights by themselves. A client-supplied namespace remains an untrusted request parameter. [Pinecone production multi-tenancy discussion](https://www.pinecone.io/learn/series/vector-databases-in-production-for-busy-engineers/vector-database-multi-tenancy/).

---

## 14. Generation, tools, streaming and model migration

Start with bounded read-only retrieval/generation. Add an agent/tool loop only when the workflow needs it. Tools require their own server-side allowlist, authenticated scope, argument validation, maximum steps, wall-clock deadline and side-effect identity. Retrieved text or model JSON must not mint a new permission or network capability.

A deployed request may involve query rewriting, reranking, generation and validation models. Each call consumes latency/context/cost budgets and can fail independently. Frameworks can organize those steps, but state, retries, authorization, checkpointing and acceptance remain application contracts. The fixture makes one extractive call and executes no tool.

Buffered output permits source/citation validation before final delivery. Streaming can release provisional text before validation or revocation is known. If used, define provisional/accepted/failure events, client rendering behavior, cancellation and final citation mapping. A final rejection cannot retract bytes already streamed. This chapter implements buffered JSON only.

Model/parser/prompt changes require a versioned evaluation and rollout plan. Rebuild vectors for a changed embedding space; do not assume equal dimensions make old/new embeddings comparable. Keep provenance sufficient to reproduce a request while respecting sensitive-data retention. Provider-native citations can expose source offsets, but the application still owns authorization and acceptance checks. [Claude citation documentation](https://platform.claude.com/docs/en/build-with-claude/citations).

---

## 15. Prompt injection and security boundaries

Retrieved documents can contain hostile instructions, fake system messages, URLs or tool requests. Treat them as untrusted evidence, keep instructions/data distinguishable, minimize tool permissions and validate output. A phrase such as “ignore prior rules” is not authority, whether it comes from an upload, search result or model response. [OWASP prompt-injection guidance](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html).

The controlled tool-request case proves that this fixture does not execute a requested tool. It does not prove that prompt injection cannot influence a real model's answer. Exact quote acceptance can still quote a malicious instruction as text; render untrusted content safely and never execute it. JSON parsing and citation presence alone are not safety or factuality proofs.

Limit uploads, parsing resources, context length, generated output, simultaneous calls and retry horizons. Avoid raw private text/tokens in logs. Give vector/model/storage credentials least necessary authority, verify tenant context at every adapter and protect internal worker/completion APIs. Private query and answer caches need user/permission/version-aware identity; a shared answer cache can leak data even with correct initial retrieval.

---

## 16. Evaluation, observability and incident diagnosis

```json
{
  "judged_positive_queries": [
    {
      "query": "queue lease",
      "expected": "queue",
      "top_document_correct": true
    },
    {
      "query": "credit balance",
      "expected": "ledger",
      "top_document_correct": true
    },
    {
      "query": "membership grants",
      "expected": "acl",
      "top_document_correct": true
    }
  ],
  "positive_queries": 3,
  "selected_corpus_top1_accuracy": 1.0,
  "selected_no_answer_contexts": 0,
  "selected_unshared_contexts": 0,
  "tool_request_case": "rejected",
  "network_tool_executed": false,
  "learned_model_quality_or_prompt_injection_immunity_proved": false
}
```

The judged micro-corpus has three positive queries, a no-answer case, an unshared source and an injected tool request. It is a deterministic regression set with authored labels, not a holdout benchmark or evidence of learned-model answer quality. Its top-one accuracy is reported only for those three positive queries.

Evaluate retrieval coverage/rank against reviewed relevant documents, then separately evaluate answer relevance, supported claims, citation correctness and appropriate abstention. A correct retrieved chunk can still yield a bad answer; a plausible answer can hide retrieval failure. Include stale/deleted/revoked sources, multilingual text, identifiers, tables, contradictory evidence and adversarial content. Model-based judges need their own validation and human review. [Microsoft RAG evaluation overview](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/tutorials/ai-cookbook/fundamentals-evaluation-monitoring-rag).

Track source-to-searchable lag, stale-job drops, permission-filtered candidates, no-context rate, context/output size, model calls, unknown/review reservations, citation rejection and deletion backlog. Correlate request, source version, chunk/index profile and provider operation without exposing raw secrets. An incident should distinguish wrong retrieval, unauthorized context, model misuse, citation acceptance error and stale delivery.

---

## 17. Run, inspect and evidence limits

From repository root with the existing dependency folders intact:

```powershell
python examples/system-design/module-17-multi-tenant-rag/verify.py
```

Verified 2026-10-17 on Python 3.12.10, SQLite 3.49.1, Windows. **125 local checks passed**: 5 ingestion, 8 isolation, 10 bounds, 5 vectors, 4 retrieval, 3 citations, 13 versions, 5 concurrency, 6 atomicity, 5 budget, 5 generation, 4 validation, 5 uncertainty, 4 revocation, 14 deletion, 6 evaluation, 19 http, 4 cleanup. Six synchronized worker calls cover paired publishers, paired reservations and paired generation attempts. Tests include a judged micro-corpus, injected rollback, reopen persistence, actual HTTP and owned-resource cleanup. Results are stored in `verification-results.json`.

The source is bounded to 1,000 raw characters/document, at most 256 retained source identities, 512 ingest jobs and 128 questions, plus inherited S11 caps. There is no retention sweeper, distributed queue/lease daemon, process-kill test or provider integration. The exact-scan vectors and extractive model validate architecture mechanics, not learned semantic relevance, token pricing, streaming, production security or throughput.

---

## 18. Interview questions and answers

### Q1. What is RAG?

Retrieving relevant external evidence and providing it to a generator for a task. It separates some updatable knowledge from model parameters. Retrieval does not automatically make output correct, authorized or properly cited; those need explicit contracts and evaluation.

### Q2. How is RAG different from fine-tuning?

RAG changes supplied evidence at request time, while fine-tuning changes model behavior/parameters through training. They can be complementary. Choose from freshness, task behavior, privacy, cost and evaluation requirements rather than assuming either universally replaces the other.

### Q3. Why separate source and index?

The source owns canonical text/version/permission; the index accelerates candidate retrieval and may lag. This allows rebuild and version fencing. A stale indexed permission or chunk cannot become the only authority for disclosure.

### Q4. What should a chunk identifier contain?

A stable binding to tenant, document, source version, chunker/parser profile, embedding/index profile and ordinal or content identity. The fixture hashes those fields. Replacing text under an old chunk ID would undermine reproducible citations and retries.

### Q5. How do you choose chunk size and overlap?

Evaluate document structure, expected questions, context budget and citation precision. Larger chunks provide context but can dilute retrieval; overlap increases duplication and cost. The fixed 120/20-character policy is a mechanical fixture, not a recommended universal setting.

### Q6. Are these real semantic embeddings?

No. They are normalized feature-hashed word counts with collisions and no learned meaning. They make vector mathematics reproducible locally. Semantic quality requires an actual embedding model and a representative judged dataset.

### Q7. Why version the embedding model?

Different model/preprocessing versions define different spaces even at equal dimensions. Mixing them can invalidate similarity comparisons. A deployment should tag generations, rebuild/evaluate and switch query/index profiles deliberately.

### Q8. What if an old embedding worker finishes late?

Check current canonical source version and index profile before publication. A stale job must not replace current chunks. Chunk replacement and readiness/job completion commit together in the local fixture.

### Q9. What happens during edit/index lag?

Old chunks fail the current-version check and new content may temporarily be unsearchable. This accepts false negatives under the chosen freshness policy. A product allowing older versions needs a different explicit provenance and permission contract.

### Q10. Does a vector namespace guarantee authorization?

No. It partitions queries under an adapter contract. The server must derive the namespace from verified tenant context and enforce document sharing/current membership. A client-chosen tenant namespace is not proof of access.

### Q11. Why filter access before top-k?

Selecting forbidden high-ranked candidates first and discarding them can omit allowed lower matches. The fixture filters current scope/version/permission before ranking. External ANN retrieval may require supported filters or bounded iterative overfetch.

### Q12. What is the request evidence set?

The exact chunk/version/text snapshots supplied to one generation request. Citation acceptance checks against that set rather than every chunk that exists in storage. This prevents a plausible reference to an unrelated unsupplied source from being accepted.

### Q13. What does an accepted citation prove here?

Its reference belongs to the supplied evidence, its quote exactly matches and its source remains current/permitted. It does not prove world truth, relevance or general paraphrase entailment. The model fixture is intentionally extractive.

### Q14. Can a model-generated citation be trusted directly?

No. Validate reference structure, membership, source version, quoted span and current permission. Provider-native citation fields can help represent provenance but do not decide application authorization or answer acceptance.

### Q15. What if no evidence is retrieved?

The fixture abstains without calling the model or reserving generation units. A real product can offer a clearly separate general-knowledge mode, but must not present unsupported output as a grounded answer from private documents.

### Q16. Why reserve budget before generation?

Concurrent requests otherwise can all observe available capacity and exceed it. Reserve a bounded worst case atomically with request identity/evidence, then settle trusted actual usage once. The fixture units are characters, not tokens or money.

### Q17. How does retry avoid duplicate model work?

A durable client operation returns the same request, and only one local prepared-to-running transition may call the model. Running/unknown retries do not automatically call again. A real provider's operation/reconciliation contract still matters across crash windows.

### Q18. What does a model timeout mean?

The outcome/usage may be unknown. Retain the reservation and reconcile evidence rather than blindly refunding or starting another paid call. This fixture injects TimeoutError and records unknown; it does not emulate real provider billing.

### Q19. Why can rejected output still consume budget?

The model performed work even if citations or tools were invalid. Known usage settles under the stated policy. Customer billing/refunds can differ, but require an explicit ledger/pricing policy rather than silently equating rejected with free.

### Q20. What if access changes during generation?

Recheck evidence at acceptance and suppress newly forbidden/stale output. Known work can still consume usage. The context already sent to an external provider cannot be recalled by this local check; prevent unauthorized prompt construction first.

### Q21. Why recheck stored answer delivery?

Permissions and versions can change after acceptance. A stored answer containing old private evidence must not become an enduring bypass. This fixture rejects completed-answer delivery after relevant source change/revocation.

### Q22. What does prompt injection change architecturally?

Retrieved text and model outputs remain untrusted data. Tool scope, arguments and side effects need server authority independent of prompts. The fixture rejects tool requests and executes no tools; it makes no real-model injection-immunity claim.

### Q23. Is a tool allowlist enough?

No. Allowed tools still require caller/resource scope, argument validation, destination policy, deadlines, step/cost limits and safe side-effect identity. A trusted tool with untrusted parameters can still perform an unauthorized action.

### Q24. Why is streaming harder to validate?

Provisional text may reach the client before final source/citation checks. Define acceptance/failure events and rendering behavior, or buffer until validation. A final rejection cannot retract text already sent. Only buffered JSON is implemented here.

### Q25. How is deletion more than removing vectors?

Source objects, extracted text, chunks, request evidence, accepted answers, caches and other projections may retain content. Block logical access immediately and perform tracked cleanup for each store. Backups/provider retention need separate stated boundaries.

### Q26. Why keep tombstones after cleanup?

Old jobs and original operation replays must not resurrect deleted content. A retained version/deletion fence preserves that authority after payload removal. Cleanup is not permission to reuse an old source identity for unrelated bytes.

### Q27. How should retrieval and generation be evaluated?

Use reviewed query/document labels for retrieval rank/coverage, then evaluate supported claims, relevance, citations and abstention separately. Include denied/stale/adversarial cases. A few deterministic successes are regression evidence, not a production-quality benchmark.

### Q28. What changes for hybrid retrieval or reranking?

Define lexical/vector candidate pools, fusion, current access filtering and the rerank budget. Evaluate the combined result on judged queries. Adding another model can increase latency/cost and introduce another untrusted-output boundary.

### Q29. What should you measure in production?

Searchable lag, relevant/authorized context coverage, no-context rate, accepted/blocked/rejected output, provider usage, unknown reservations, latency and cleanup backlog. Correlate source/index/request versions without logging live credentials or unnecessary private text.

### Q30. Give a compact design answer.

Version canonical sources and durable ingestion, publish deterministic chunk generations behind current-version fences, and retrieve only current authorized evidence. Reserve request budget, validate model output against the supplied evidence and current authority, reconcile unknown outcomes, and enforce deletion across source/index/request/delivery boundaries.

---

## 19. A 45-minute mock and answer skeleton

**Mock prompt:** “Design a private multi-tenant knowledge assistant. An old embedding job retries after an edit, a share is revoked during generation, and a model call times out.”

| Segment | Minutes |
| --- | --- |
| Clarify formats, authority, grounding and freshness | 5 |
| Estimate chunks, vectors, latency and model budgets | 7 |
| Define source/index/request/evidence identities | 8 |
| Trace current retrieval and accepted generation | 10 |
| Inject stale indexing, revoked access, timeout and delete | 10 |
| Defend evaluation, migration, streaming and limits | 5 |
| **Total** | **45** |

A defensible short answer:

> I would keep canonical source versions and current permissions independent from replaceable chunks/vectors. A durable versioned ingest job publishes only if the source/profile remains current. Retrieval filters verified tenant, current version and access before ranking. Each question stores its exact evidence and reserves a bounded budget before the model call. Output remains untrusted: validate supplied references, claims, tools, usage and current authority before acceptance, then recheck delivery. Unknown outcomes retain reconciliation state. Deletion immediately fences reads and separately cleans source, projections and retained request data. Quality requires judged retrieval and answer evaluations, not citation presence alone.

---

## 20. Practice tasks

1. Clarify the source formats, permissions, grounding standard, freshness, streaming and model/tool contract for a private research platform.
2. Estimate chunk/vector storage, source-to-searchable backlog, context sizes and real provider token/cost components; separate fixture character units.
3. Change normalization/chunk/model profiles and design stable citation anchors plus a generation migration and rollback strategy.
4. Capture an ingest job, update and publish the new source, then finish the old job. Inspect current chunks, readiness and replay.
5. Inject job/publication failure and race publishers. Explain local transaction guarantees versus external vector upsert/worker retry boundaries.
6. Query as another owner/tenant, grant/revoke access and inspect candidates before top-k, direct citation access and stored answer delivery.
7. Submit invalid references, fabricated quotes and a tool request. Separate citation membership, exact support, relevance and world truth.
8. Race request reservations/generation, lose the model reply and inject settlement failure. Explain retained uncertainty and trusted reconciliation.
9. Delete before delayed indexing and purge during prepared/running requests. Enumerate remaining object/cache/provider/backup deletion obligations.
10. Complete the mock and Q37/Q51/Q59 with a judged evaluation set, prompt-injection boundaries, streaming acceptance and explicit proof limits.

---

## 21. Completion checklist

- [ ] I can separate canonical source authority from replaceable retrieval data.
- [ ] I can version parser, chunk, embedding and index identities.
- [ ] I can atomically accept source and durable ingest intent.
- [ ] I can fence stale publication and explain edit/index lag.
- [ ] I can enforce current tenant/permission/version before retrieval top-k.
- [ ] I can bind citations to exact supplied request evidence.
- [ ] I can distinguish accepted quotes from semantic correctness.
- [ ] I can reserve/settle bounded usage and retain unknown outcomes.
- [ ] I can prevent local duplicate model invocation on request retry.
- [ ] I can recheck acceptance/delivery after access changes.
- [ ] I can explain tool/streaming/deletion boundaries and external retention.
- [ ] I can finish the mock and distinguish regression tests from model-quality evidence.

---

## 22. Research references and continuation

Reviewed 2026-10-17. Primary references: [RAG research](https://arxiv.org/abs/2005.11401), [pgvector](https://github.com/pgvector/pgvector), [Pinecone multi-tenancy](https://www.pinecone.io/learn/series/vector-databases-in-production-for-busy-engineers/vector-database-multi-tenancy/), [Claude citations](https://platform.claude.com/docs/en/build-with-claude/citations), [OWASP prompt injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html), and [Microsoft RAG evaluation](https://learn.microsoft.com/en-us/azure/databricks/generative-ai/tutorials/ai-cookbook/fundamentals-evaluation-monitoring-rag). The local vectors/model, policies, workload and interview answers are authored teaching mechanisms, not those products' implementation or measured production performance.

Return to the [architecture roadmap](/docs/system-design), [S3 file lifecycle](/docs/system-design/file-upload-processing), [S7 workers](/docs/system-design/job-scheduler-workers), [S8 credit boundary](/docs/system-design/checkout-payments-credit-ledger), [S9 retrieval](/docs/system-design/search-autocomplete), [S11 tenancy](/docs/system-design/multi-tenant-saas), [Resume M23 ingestion](/docs/resume-skills/rag-document-ingestion), [M24 embeddings](/docs/resume-skills/embeddings-pinecone-pgvector) or [M25 orchestration](/docs/resume-skills/langchain-langgraph-llamaindex).

**Next: [S13 — Analytics event pipeline and dashboard](/docs/system-design/analytics-event-pipeline)**, architecture part 20 / numeric module 18. It develops scoped event identity, atomic projection progress, cohorts, lateness, rebuild and privacy with local SQLite/HTTP evidence. Finish with [Consolidation and design mocks](/docs/system-design/consolidation), Part 21. All 21 planned architecture files are authored; learner self-assessment remains manual.
