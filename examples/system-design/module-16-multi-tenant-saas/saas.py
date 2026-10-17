"""Local tenant-scoped SaaS authority; opaque sessions issued by trusted fixture login."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
import hashlib
import re
import secrets
import uuid
from runtime import Database, Error, document, identity, number


def token_hash(token):
    if type(token) is not str or not 32<=len(token)<=128 or not token.isascii():
        raise Error(401,'invalid_token')
    return hashlib.sha256(token.encode()).hexdigest()


class SaaS(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,active INTEGER);
        CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY,doc_limit INTEGER);
        CREATE TABLE IF NOT EXISTS members(tenant TEXT,user TEXT,role TEXT,active INTEGER,
            PRIMARY KEY(tenant,user),FOREIGN KEY(tenant) REFERENCES tenants(id),FOREIGN KEY(user) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS sessions(hash TEXT PRIMARY KEY,user TEXT,tenant TEXT,expires INTEGER,revoked INTEGER);
        CREATE TABLE IF NOT EXISTS docs(tenant TEXT,id TEXT,owner TEXT,title TEXT,version INTEGER,deleted INTEGER,
            PRIMARY KEY(tenant,id),FOREIGN KEY(tenant) REFERENCES tenants(id));
        CREATE TABLE IF NOT EXISTS creates(tenant TEXT,user TEXT,operation TEXT,title TEXT,doc TEXT,PRIMARY KEY(tenant,user,operation));
        CREATE TABLE IF NOT EXISTS shares(tenant TEXT,doc TEXT,reader TEXT,PRIMARY KEY(tenant,doc,reader));
        CREATE TABLE IF NOT EXISTS invitations(id TEXT UNIQUE,hash TEXT PRIMARY KEY,tenant TEXT,recipient TEXT,
            role TEXT,audience TEXT,expires INTEGER,revoked INTEGER,used_by TEXT);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,tenant TEXT,actor TEXT,action TEXT,resource TEXT);
        CREATE TABLE IF NOT EXISTS exports(id TEXT PRIMARY KEY,tenant TEXT,requester TEXT,doc TEXT,
            state TEXT,version INTEGER,title TEXT);
    '''

    def user(self,user):
        self.db.execute('INSERT INTO users VALUES(?,1) ON CONFLICT DO NOTHING',(identity(user),))

    def bootstrap(self,tenant,owner,doc_limit=8):
        identity(tenant)
        number(doc_limit,1,128)
        with self.transaction():
            self.user(owner)
            self.db.execute('INSERT INTO tenants VALUES(?,?)',(tenant,doc_limit))
            self.db.execute("INSERT INTO members VALUES(?,?,'owner',1)",(tenant,owner))

    def seed_member(self,tenant,user,role):
        # Trusted setup only; no public equivalent bypassing change_member.
        if role not in ('owner','admin','member','viewer'):
            raise Error(400,'invalid_role')
        self.user(user)
        self.db.execute('INSERT INTO members VALUES(?,?,?,1)',(identity(tenant),user,role))

    def _session(self,user,tenant,now,ttl):
        number(now)
        number(ttl,1,3600000)
        row = self.db.execute('SELECT 1 FROM members m JOIN users u ON u.id=m.user WHERE m.tenant=? AND m.user=? AND m.active=1 AND u.active=1',(identity(tenant),identity(user))).fetchone()
        if row is None:
            raise Error(403,'membership_required')
        if self.db.execute('SELECT count(*) FROM sessions').fetchone()[0]>=256:
            raise Error(503,'lesson_session_retention_cap')
        token = secrets.token_urlsafe(32)
        self.db.execute('INSERT INTO sessions VALUES(?,?,?,?,0)',(token_hash(token),user,tenant,now+ttl))
        return {'token':token,'tenant':tenant,'expires':now+ttl}

    def session(self,user,tenant,now,ttl=60000):
        # Only after trusted upstream identity verification; no password/login endpoint.
        with self.transaction():
            return self._session(user,tenant,now,ttl)

    def context(self,token,now):
        number(now)
        row = self.db.execute('''SELECT s.user,s.tenant,m.role FROM sessions s
            JOIN users u ON u.id=s.user JOIN members m ON m.tenant=s.tenant AND m.user=s.user
            WHERE s.hash=? AND s.revoked=0 AND s.expires>? AND u.active=1 AND m.active=1''',(token_hash(token),now)).fetchone()
        if row is None:
            raise Error(401,'session_or_membership_inactive')
        return dict(row)

    def who(self,token,now):
        with self.transaction():
            return self.context(token,now)

    def switch(self,token,now,tenant):
        with self.transaction():
            actor = self.context(token,now)
            result = self._session(actor['user'],tenant,now,60000)
            self.db.execute('UPDATE sessions SET revoked=1 WHERE hash=?',(token_hash(token),))
            return result

    def logout(self,token,now):
        with self.transaction():
            self.context(token,now)
            self.db.execute('UPDATE sessions SET revoked=1 WHERE hash=?',(token_hash(token),))

    def log(self,actor,action,resource):
        self.db.execute('INSERT INTO audit(tenant,actor,action,resource) VALUES(?,?,?,?)',
            (actor['tenant'],actor['user'],action,resource))

    def admin(self,actor):
        if actor['role'] not in ('owner','admin'):
            raise Error(403,'admin_required')

    def doc(self,actor,doc_id,write=False):
        row = self.db.execute('SELECT * FROM docs WHERE tenant=? AND id=? AND deleted=0',(actor['tenant'],identity(doc_id))).fetchone()
        manager = row and (actor['role'] in ('owner','admin') or row['owner']==actor['user'])
        shared = row and self.db.execute('SELECT 1 FROM shares WHERE tenant=? AND doc=? AND reader=?',(actor['tenant'],doc_id,actor['user'])).fetchone()
        allowed = manager and actor['role']!='viewer' if write else manager or shared
        if row is None or not allowed:
            raise Error(404,'document_not_found')
        return dict(row)

    def create(self,token,now,operation,title):
        identity(operation)
        if type(title) is not str or not 1<=len(title)<=120:
            raise Error(400,'invalid_title')
        with self.transaction():
            actor = self.context(token,now)
            if actor['role']=='viewer':
                raise Error(403,'writer_required')
            old = self.db.execute('SELECT * FROM creates WHERE tenant=? AND user=? AND operation=?',(actor['tenant'],actor['user'],operation)).fetchone()
            if old:
                if old['title']!=title:
                    raise Error(409,'changed_create_intent')
                return self.doc(actor,old['doc'])
            count = self.db.execute('SELECT count(*) FROM docs WHERE tenant=? AND deleted=0',(actor['tenant'],)).fetchone()[0]
            limit = self.db.execute('SELECT doc_limit FROM tenants WHERE id=?',(actor['tenant'],)).fetchone()[0]
            if count>=limit:
                raise Error(409,'document_quota')
            if self.db.execute('SELECT count(*) FROM docs').fetchone()[0]>=256:
                raise Error(503,'lesson_document_retention_cap')
            doc = uuid.uuid4().hex
            self.db.execute('INSERT INTO docs VALUES(?,?,?,?,1,0)',(actor['tenant'],doc,actor['user'],title))
            self.db.execute('INSERT INTO creates VALUES(?,?,?,?,?)',(actor['tenant'],actor['user'],operation,title,doc))
            self.log(actor,'document.create',doc)
            return self.doc(actor,doc)

    def read(self,token,now,doc):
        with self.transaction():
            return self.doc(self.context(token,now),doc)

    def list_docs(self,token,now):
        with self.transaction():
            actor = self.context(token,now)
            rows = self.db.execute('''SELECT d.* FROM docs d WHERE tenant=? AND deleted=0 AND
                (? IN ('owner','admin') OR owner=? OR EXISTS(SELECT 1 FROM shares s WHERE s.tenant=d.tenant AND s.doc=d.id AND s.reader=?)) ORDER BY id''',
                (actor['tenant'],actor['role'],actor['user'],actor['user'])).fetchall()
            return [dict(row) for row in rows]

    def edit(self,token,now,doc_id,expected_version,title):
        number(expected_version,1)
        if type(title) is not str or not 1<=len(title)<=120:
            raise Error(400,'invalid_title')
        with self.transaction():
            actor = self.context(token,now)
            row = self.doc(actor,doc_id,True)
            if row['version']!=expected_version:
                raise Error(409,'version_conflict')
            self.db.execute('UPDATE docs SET title=?,version=version+1 WHERE tenant=? AND id=?',(title,actor['tenant'],doc_id))
            self.log(actor,'document.edit',doc_id)
            return self.doc(actor,doc_id)

    def share(self,token,now,doc_id,reader,allow):
        identity(reader)
        if type(allow) is not bool:
            raise Error(400,'invalid_share')
        with self.transaction():
            actor = self.context(token,now)
            self.doc(actor,doc_id,True)
            target = self.db.execute('SELECT 1 FROM members WHERE tenant=? AND user=? AND active=1',(actor['tenant'],reader)).fetchone()
            if target is None:
                raise Error(404,'reader_not_found')
            if allow:
                self.db.execute('INSERT INTO shares VALUES(?,?,?) ON CONFLICT DO NOTHING',(actor['tenant'],doc_id,reader))
            else:
                self.db.execute('DELETE FROM shares WHERE tenant=? AND doc=? AND reader=?',(actor['tenant'],doc_id,reader))
            self.log(actor,'document.share' if allow else 'document.unshare',doc_id)
            return {'allowed':allow}

    def change_member(self,token,now,target,role,active):
        identity(target)
        if role not in ('owner','admin','member','viewer') or type(active) is not bool:
            raise Error(400,'invalid_member_change')
        with self.transaction():
            actor = self.context(token,now)
            self.admin(actor)
            old = self.db.execute('SELECT * FROM members WHERE tenant=? AND user=?',(actor['tenant'],target)).fetchone()
            if old is None:
                raise Error(404,'member_not_found')
            if actor['role']!='owner' and (old['role'] in ('owner','admin') or role in ('owner','admin')):
                raise Error(403,'owner_required')
            owners = self.db.execute("SELECT count(*) FROM members WHERE tenant=? AND role='owner' AND active=1",(actor['tenant'],)).fetchone()[0]
            if old['role']=='owner' and old['active'] and (role!='owner' or not active) and owners<=1:
                raise Error(409,'last_owner')
            self.db.execute('UPDATE members SET role=?,active=? WHERE tenant=? AND user=?',(role,int(active),actor['tenant'],target))
            if not active:
                self.db.execute('DELETE FROM shares WHERE tenant=? AND reader=?',(actor['tenant'],target))
                self.db.execute('UPDATE sessions SET revoked=1 WHERE tenant=? AND user=?',(actor['tenant'],target))
            self.log(actor,'membership.change',target)

    def invite(self,token,now,recipient,role,expires):
        identity(recipient)
        number(expires,now+1,now+3600000)
        if role not in ('member','viewer'):
            raise Error(400,'invite_role_not_allowed')
        with self.transaction():
            actor = self.context(token,now)
            self.admin(actor)
            if not self.db.execute('SELECT 1 FROM users WHERE id=? AND active=1',(recipient,)).fetchone():
                raise Error(404,'recipient_not_found')
            if self.db.execute('SELECT count(*) FROM invitations').fetchone()[0]>=64:
                raise Error(503,'lesson_invitation_retention_cap')
            raw,invite_id = secrets.token_urlsafe(32),uuid.uuid4().hex
            self.db.execute("INSERT INTO invitations VALUES(?,?,?,?,?,'workspace_join',?,0,NULL)",
                (invite_id,token_hash(raw),actor['tenant'],recipient,role,expires))
            self.log(actor,'invitation.create',invite_id)
            return {'id':invite_id,'token':raw,'expires':expires}

    def revoke_invite(self,token,now,invite_id):
        with self.transaction():
            actor = self.context(token,now)
            self.admin(actor)
            changed = self.db.execute('UPDATE invitations SET revoked=1 WHERE tenant=? AND id=?',(actor['tenant'],identity(invite_id))).rowcount
            if not changed:
                raise Error(404,'invitation_not_found')
            self.log(actor,'invitation.revoke',invite_id)

    def accept(self,token,now,invitation,audience):
        with self.transaction():
            actor = self.context(token,now)
            row = self.db.execute('SELECT * FROM invitations WHERE hash=?',(token_hash(invitation),)).fetchone()
            if row is None:
                raise Error(404,'invitation_not_found')
            if row['recipient']!=actor['user'] or audience!=row['audience']:
                raise Error(403,'invitation_binding')
            if row['revoked'] or row['expires']<=now:
                raise Error(410,'invitation_expired_or_revoked')
            prior = self.db.execute('SELECT active FROM members WHERE tenant=? AND user=?',(row['tenant'],actor['user'])).fetchone()
            if row['used_by']:
                if prior and prior['active']:
                    return {'state':'already_accepted','tenant':row['tenant']}
                raise Error(409,'accepted_membership_removed')
            if prior:
                raise Error(409,'membership_exists')
            self.db.execute('INSERT INTO members VALUES(?,?,?,1)',(row['tenant'],actor['user'],row['role']))
            self.db.execute('UPDATE invitations SET used_by=? WHERE hash=?',(actor['user'],row['hash']))
            self.log({'tenant':row['tenant'],'user':actor['user']},'invitation.accept',row['id'])
            return {'state':'accepted','tenant':row['tenant']}

    def export(self,token,now,doc_id):
        with self.transaction():
            actor = self.context(token,now)
            self.doc(actor,doc_id)
            if self.db.execute('SELECT count(*) FROM exports').fetchone()[0]>=64:
                raise Error(503,'lesson_export_retention_cap')
            job = uuid.uuid4().hex
            self.db.execute("INSERT INTO exports VALUES(?,?,?,?,'pending',0,'')",(job,actor['tenant'],actor['user'],doc_id))
            self.log(actor,'export.create',job)
            return {'id':job,'state':'pending'}

    def work(self,job_id):
        with self.transaction():
            job = self.db.execute('SELECT * FROM exports WHERE id=?',(identity(job_id),)).fetchone()
            if job is None:
                raise Error(404,'export_not_found')
            if job['state']!='pending':
                return job['state']
            member = self.db.execute('SELECT m.role FROM members m JOIN users u ON u.id=m.user WHERE tenant=? AND user=? AND m.active=1 AND u.active=1',(job['tenant'],job['requester'])).fetchone()
            try:
                if member is None:
                    raise Error(404,'inactive_member')
                doc = self.doc({'tenant':job['tenant'],'user':job['requester'],'role':member['role']},job['doc'])
            except Error:
                self.db.execute("UPDATE exports SET state='denied' WHERE id=?",(job_id,))
                return 'denied'
            self.db.execute("UPDATE exports SET state='ready',version=?,title=? WHERE id=?",(doc['version'],doc['title'],job_id))
            return 'ready'

    def result(self,token,now,job_id):
        with self.transaction():
            actor = self.context(token,now)
            job = self.db.execute('SELECT * FROM exports WHERE tenant=? AND requester=? AND id=?',(actor['tenant'],actor['user'],identity(job_id))).fetchone()
            if job is None:
                raise Error(404,'export_not_found')
            doc = self.doc(actor,job['doc'])
            if job['state']!='ready' or job['version']!=doc['version']:
                raise Error(409,'export_not_ready_or_stale')
            return {'title':job['title'],'version':job['version']}


def estimates():
    return {'tenants':1000,'assumed_users_per_tenant':20,'membership_rows':20000,
        'assumed_documents_per_tenant':500,'documents':500000,'fixture_quota_is_per_tenant':True,
        'session_max_ttl_ms':3600000,'invitation_max_ttl_ms':3600000,'measured_capacity':False}


def dispatch(item,_lesson_identity,method,path,raw,headers,clock):
    # The shared helper's fixed lesson identities are deliberately NOT authority here.
    auth = headers.get('Authorization','')
    token = auth[7:] if auth.startswith('Bearer ') else ''
    now = clock()
    if path=='/session' and method=='GET':
        return 200,item.who(token,now)
    if path=='/session/switch' and method=='POST':
        return 200,item.switch(token,now,**document(raw,['tenant']))
    if path=='/session/logout' and method=='POST':
        item.logout(token,now)
        return 200,{'logged_out':True}
    if path=='/docs' and method=='GET':
        return 200,{'items':item.list_docs(token,now)}
    if path=='/docs' and method=='POST':
        return 201,item.create(token,now,headers.get('Idempotency-Key',''),**document(raw,['title']))
    match = re.fullmatch(r'/docs/([a-f0-9]{32})(?:/(shares|exports)(?:/([A-Za-z0-9_-]{1,64}))?)?',path)
    if match and not match[2] and method=='GET':
        return 200,item.read(token,now,match[1])
    if match and not match[2] and method=='PUT':
        return 200,item.edit(token,now,match[1],**document(raw,['expected_version','title']))
    if match and match[2]=='shares' and match[3] and method in ('PUT','DELETE'):
        return 200,item.share(token,now,match[1],match[3],method=='PUT')
    if match and match[2]=='exports' and not match[3] and method=='POST':
        return 202,item.export(token,now,match[1])
    if method=='POST' and path=='/invitations':
        return 201,item.invite(token,now,**document(raw,['recipient','role','expires']))
    if method=='POST' and path=='/invitations/accept':
        return 200,item.accept(token,now,**document(raw,['invitation','audience']))
    match = re.fullmatch(r'/invitations/([a-f0-9]{32})',path)
    if match and method=='DELETE':
        item.revoke_invite(token,now,match[1])
        return 200,{'revoked':True}
    match = re.fullmatch(r'/members/([A-Za-z0-9_-]{1,64})',path)
    if match and method=='PUT':
        item.change_member(token,now,match[1],**document(raw,['role','active']))
        return 200,{'updated':True}
    match = re.fullmatch(r'/exports/([a-f0-9]{32})',path)
    if match and method=='GET':
        return 200,item.result(token,now,match[1])
    item.who(token,now)
    raise Error(404,'unknown_route')
