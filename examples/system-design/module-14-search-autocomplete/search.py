"""SQLite FTS5 projection with version fences and authoritative read authorization."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
import json
import re
import uuid
from urllib.parse import parse_qs, urlsplit
from runtime import Database, Error, document, identity, number, require


class Search(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS documents(tenant TEXT,id TEXT,owner TEXT,version INTEGER,
            deleted INTEGER,title TEXT,body TEXT,public INTEGER,PRIMARY KEY(tenant,id));
        CREATE TABLE IF NOT EXISTS creates(tenant TEXT,owner TEXT,operation TEXT,doc TEXT,fingerprint TEXT,
            PRIMARY KEY(tenant,owner,operation));
        CREATE TABLE IF NOT EXISTS grants(tenant TEXT,doc TEXT,reader TEXT,PRIMARY KEY(tenant,doc,reader));
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,tenant TEXT,doc TEXT,
            version INTEGER,deleted INTEGER,title TEXT,body TEXT,done INTEGER DEFAULT 0,
            UNIQUE(tenant,doc,version));
        CREATE TABLE IF NOT EXISTS watermarks(tenant TEXT,doc TEXT,version INTEGER,deleted INTEGER,PRIMARY KEY(tenant,doc));
        CREATE VIRTUAL TABLE IF NOT EXISTS search USING fts5(tenant UNINDEXED,doc UNINDEXED,version UNINDEXED,
            title,body,tokenize='unicode61',prefix='2 3 4');
    '''

    def content(self,title,body):
        if type(title) is not str or not 1<=len(title)<=120 or not title.strip():
            raise Error(400,'invalid_title')
        if type(body) is not str or len(body)>2000:
            raise Error(400,'invalid_body')

    def owned(self,tenant,owner,doc):
        row = self.db.execute('SELECT * FROM documents WHERE tenant=? AND owner=? AND id=?',
            (identity(tenant),identity(owner),identity(doc))).fetchone()
        if row is None:
            raise Error(404,'document_not_found')
        return dict(row)

    def outbox(self,row):
        if self.db.execute('SELECT count(*) FROM events').fetchone()[0]>=512:
            raise Error(503,'lesson_event_retention_cap')
        self.db.execute('INSERT INTO events(tenant,doc,version,deleted,title,body) VALUES(?,?,?,?,?,?)',
            (row['tenant'],row['id'],row['version'],row['deleted'],row['title'],row['body']))

    def create(self,tenant,owner,operation,title,body,public):
        for value in (tenant,owner,operation):
            identity(value)
        self.content(title,body)
        if type(public) is not bool:
            raise Error(400,'invalid_visibility')
        fingerprint = json.dumps([title,body,public],ensure_ascii=False)
        with self.transaction():
            old = self.db.execute('SELECT * FROM creates WHERE tenant=? AND owner=? AND operation=?',(tenant,owner,operation)).fetchone()
            if old:
                if old['fingerprint']!=fingerprint:
                    raise Error(409,'changed_create_intent')
                return self.owned(tenant,owner,old['doc'])
            if self.db.execute('SELECT count(*) FROM documents').fetchone()[0]>=128:
                raise Error(503,'lesson_document_retention_cap')
            doc = uuid.uuid4().hex
            self.db.execute('INSERT INTO documents VALUES(?,?,?,1,0,?,?,?)',(tenant,doc,owner,title,body,int(public)))
            self.db.execute('INSERT INTO creates VALUES(?,?,?,?,?)',(tenant,owner,operation,doc,fingerprint))
            row = self.owned(tenant,owner,doc)
            self.outbox(row)
            return row

    def edit(self,tenant,owner,doc,expected_version,title,body):
        self.content(title,body)
        number(expected_version,1)
        with self.transaction():
            row = self.owned(tenant,owner,doc)
            if row['deleted']:
                raise Error(410,'document_deleted')
            if row['version']!=expected_version:
                raise Error(409,'version_conflict')
            self.db.execute('UPDATE documents SET version=version+1,title=?,body=? WHERE tenant=? AND id=?',(title,body,tenant,doc))
            result = self.owned(tenant,owner,doc)
            self.outbox(result)
            return result

    def delete(self,tenant,owner,doc):
        with self.transaction():
            row = self.owned(tenant,owner,doc)
            if not row['deleted']:
                self.db.execute('UPDATE documents SET version=version+1,deleted=1 WHERE tenant=? AND id=?',(tenant,doc))
                row = self.owned(tenant,owner,doc)
                self.outbox(row)
            return row

    def grant(self,tenant,owner,doc,reader,allow):
        identity(reader)
        if type(allow) is not bool:
            raise Error(400,'invalid_grant')
        with self.transaction():
            row = self.owned(tenant,owner,doc)
            if row['deleted']:
                raise Error(410,'document_deleted')
            if allow:
                self.db.execute('INSERT INTO grants VALUES(?,?,?) ON CONFLICT DO NOTHING',(tenant,doc,reader))
            else:
                self.db.execute('DELETE FROM grants WHERE tenant=? AND doc=? AND reader=?',(tenant,doc,reader))
            return {'reader':reader,'allowed':allow}

    def apply(self,event_id):
        number(event_id,1)
        with self.transaction():
            event = self.db.execute('SELECT * FROM events WHERE id=?',(event_id,)).fetchone()
            if event is None:
                raise Error(404,'event_not_found')
            if event['done']:
                return 'replay'
            prior = self.db.execute('SELECT version FROM watermarks WHERE tenant=? AND doc=?',(event['tenant'],event['doc'])).fetchone()
            outcome = 'stale' if prior and prior[0]>=event['version'] else 'applied'
            if outcome=='applied':
                self.db.execute('DELETE FROM search WHERE tenant=? AND doc=?',(event['tenant'],event['doc']))
                if not event['deleted']:
                    self.db.execute('INSERT INTO search(tenant,doc,version,title,body) VALUES(?,?,?,?,?)',
                        (event['tenant'],event['doc'],event['version'],event['title'],event['body']))
                self.db.execute('INSERT INTO watermarks VALUES(?,?,?,?) ON CONFLICT(tenant,doc) DO UPDATE SET version=excluded.version,deleted=excluded.deleted',
                    (event['tenant'],event['doc'],event['version'],event['deleted']))
            self.db.execute('UPDATE events SET done=1 WHERE id=?',(event_id,))
            return outcome

    def find(self,tenant,reader,query,mode='full',limit=10):
        identity(tenant)
        identity(reader)
        if type(query) is not str or not 1<=len(query)<=100 or mode not in ('full','prefix'):
            raise Error(400,'invalid_query')
        number(limit,1,20)
        terms = re.findall(r'[^\W_]+',query,re.UNICODE)
        if not 1<=len(terms)<=4:
            raise Error(400,'invalid_term_count')
        # Quoted literal tokens only. Client text cannot supply FTS syntax.
        tokens = ['"'+term+'"' for term in terms]
        if mode=='prefix':
            tokens[-1] += '*'
        expression = ' AND '.join(('title : '+token if mode=='prefix' else token) for token in tokens)
        rows = self.db.execute('''SELECT d.id,d.title,substr(d.body,1,100) AS snippet
            FROM search JOIN documents d ON d.tenant=search.tenant AND d.id=search.doc
            WHERE search MATCH ? AND d.tenant=? AND d.version=search.version AND d.deleted=0
            AND (d.owner=? OR d.public=1 OR EXISTS(SELECT 1 FROM grants g
                WHERE g.tenant=d.tenant AND g.doc=d.id AND g.reader=?))
            ORDER BY bm25(search,0,0,0,5,1),d.id LIMIT ?''',
            (expression,tenant,reader,reader,limit+1)).fetchall()
        return {'items':[dict(row) for row in rows[:limit]],'returned':min(len(rows),limit),'has_more':len(rows)>limit}

    def rebuild(self,tenant):
        identity(tenant)
        with self.transaction():
            self.db.execute('DELETE FROM search WHERE tenant=?',(tenant,))
            rows = self.db.execute('SELECT * FROM documents WHERE tenant=?',(tenant,)).fetchall()
            for row in rows:
                if not row['deleted']:
                    self.db.execute('INSERT INTO search(tenant,doc,version,title,body) VALUES(?,?,?,?,?)',
                        (tenant,row['id'],row['version'],row['title'],row['body']))
                self.db.execute('INSERT INTO watermarks VALUES(?,?,?,?) ON CONFLICT(tenant,doc) DO UPDATE SET version=excluded.version,deleted=excluded.deleted',
                    (tenant,row['id'],row['version'],row['deleted']))
            return len(rows)


def estimates():
    return {'documents':1000000,'assumed_average_document_bytes':2000,'logical_document_GB':2,
        'assumed_index_multiplier':1.5,'assumed_index_GB':3,'updates_per_second':100,
        'sixty_second_outage_backlog':6000,'drain_seconds_at_150_service_100_arrival':120,'measured_capacity':False}


def dispatch(item,user,method,path,raw,headers):
    tenant,owner = require(user)
    parsed = urlsplit(path)
    if method=='GET' and parsed.path=='/search':
        query = parse_qs(parsed.query,keep_blank_values=True)
        if set(query)-{'q','mode','limit'} or 'q' not in query or any(len(v)!=1 for v in query.values()):
            raise Error(400,'invalid_query_parameters')
        raw_limit = query.get('limit',['10'])[0]
        if not re.fullmatch(r'[0-9]{1,2}',raw_limit):
            raise Error(400,'invalid_limit')
        return 200,item.find(tenant,owner,query['q'][0],query.get('mode',['full'])[0],int(raw_limit))
    if path=='/docs' and method=='POST':
        value = document(raw,['title','body','public'])
        return 201,item.create(tenant,owner,headers.get('Idempotency-Key',''),**value)
    match = re.fullmatch(r'/docs/([a-f0-9]{32})(?:/grants/([A-Za-z0-9_-]{1,64}))?',path)
    if match and match[2] and method in ('PUT','DELETE'):
        return 200,item.grant(tenant,owner,match[1],match[2],method=='PUT')
    if match and not match[2] and method=='PUT':
        return 200,item.edit(tenant,owner,match[1],**document(raw,['expected_version','title','body']))
    if match and not match[2] and method=='DELETE':
        return 200,item.delete(tenant,owner,match[1])
    raise Error(404,'unknown_route')
