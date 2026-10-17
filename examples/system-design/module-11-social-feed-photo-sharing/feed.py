"""Bounded hybrid feed: durable batched pointers, pull posts and current visibility."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
from urllib.parse import parse_qs, urlsplit
import base64
import hashlib
import hmac
import json
import re
from runtime import Database, Error, document, identity, number, require

CURSOR_SECRET = b'published-s6-cursor-lesson-secret'


class Feed(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS authors(tenant TEXT,user TEXT,mode TEXT,PRIMARY KEY(tenant,user));
        CREATE TABLE IF NOT EXISTS media(tenant TEXT,id TEXT,owner TEXT,version INTEGER,state TEXT,
            PRIMARY KEY(tenant,id));
        CREATE TABLE IF NOT EXISTS follows(tenant TEXT,viewer TEXT,author TEXT,PRIMARY KEY(tenant,viewer,author));
        CREATE TABLE IF NOT EXISTS blocks(tenant TEXT,blocker TEXT,blocked TEXT,PRIMARY KEY(tenant,blocker,blocked));
        CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY AUTOINCREMENT,tenant TEXT,author TEXT,
            operation TEXT,media_id TEXT,media_version INTEGER,caption TEXT,state TEXT,mode TEXT,
            UNIQUE(tenant,author,operation));
        CREATE INDEX IF NOT EXISTS author_posts ON posts(tenant,author,id DESC);
        CREATE TABLE IF NOT EXISTS jobs(post INTEGER PRIMARY KEY,cursor TEXT,state TEXT);
        CREATE TABLE IF NOT EXISTS inbox(tenant TEXT,viewer TEXT,post INTEGER,PRIMARY KEY(tenant,viewer,post));
    '''

    def author_mode(self, tenant, author, mode):
        for value in (tenant,author):
            identity(value)
        if mode not in ('push','pull'):
            raise Error(400,'invalid_mode')
        self.db.execute('INSERT INTO authors VALUES(?,?,?) ON CONFLICT(tenant,user) DO UPDATE SET mode=excluded.mode',(tenant,author,mode))

    def media_state(self, tenant, media_id, owner, version, state):
        # Trusted lifecycle projection fixture, NOT S3 integration/image processing.
        for value in (tenant,media_id,owner):
            identity(value)
        number(version,1,1000000)
        if state not in ('ready','quarantined','deleted'):
            raise Error(400,'invalid_media_state')
        self.db.execute('INSERT INTO media VALUES(?,?,?,?,?) ON CONFLICT(tenant,id) DO UPDATE SET owner=excluded.owner,version=excluded.version,state=excluded.state',
                        (tenant,media_id,owner,version,state))

    def follow(self, tenant, viewer, author, enabled=True):
        for value in (tenant,viewer,author):
            identity(value)
        with self.transaction():
            if enabled:
                if viewer == author:
                    raise Error(400,'self_follow_not_required')
                if self.db.execute('SELECT count(*) FROM follows WHERE tenant=? AND viewer=?',(tenant,viewer)).fetchone()[0]>=16 and not self.db.execute('SELECT 1 FROM follows WHERE tenant=? AND viewer=? AND author=?',(tenant,viewer,author)).fetchone():
                    raise Error(503,'lesson_follow_cap')
                self.db.execute('INSERT INTO follows VALUES(?,?,?) ON CONFLICT DO NOTHING',(tenant,viewer,author))
                # Bounded retained-dataset backfill closes new-follow/batch-cursor gaps.
                self.db.execute("INSERT INTO inbox SELECT tenant,?,id FROM posts WHERE tenant=? AND author=? AND mode='push' AND state='published' ON CONFLICT DO NOTHING",(viewer,tenant,author))
            else:
                self.db.execute('DELETE FROM follows WHERE tenant=? AND viewer=? AND author=?',(tenant,viewer,author))

    def block(self, tenant, user, other, enabled=True):
        for value in (tenant,user,other):
            identity(value)
        if enabled:
            self.db.execute('INSERT INTO blocks VALUES(?,?,?) ON CONFLICT DO NOTHING',(tenant,user,other))
        else:
            self.db.execute('DELETE FROM blocks WHERE tenant=? AND blocker=? AND blocked=?',(tenant,user,other))

    def publish(self, tenant, author, operation, media_id, media_version, caption):
        for value in (tenant,author,operation,media_id):
            identity(value)
        number(media_version,1,1000000)
        if type(caption) is not str or len(caption)>280:
            raise Error(400,'invalid_caption')
        with self.transaction():
            old = self.db.execute('SELECT * FROM posts WHERE tenant=? AND author=? AND operation=?',(tenant,author,operation)).fetchone()
            if old:
                if (old['media_id'],old['media_version'],old['caption']) != (media_id,media_version,caption):
                    raise Error(409,'changed_post_intent')
                return dict(old)
            asset = self.db.execute("SELECT * FROM media WHERE tenant=? AND id=? AND owner=? AND version=? AND state='ready'",(tenant,media_id,author,media_version)).fetchone()
            if asset is None:
                raise Error(409,'media_not_owned_ready_version')
            if self.db.execute('SELECT count(*) FROM posts WHERE tenant=?',(tenant,)).fetchone()[0]>=256:
                raise Error(503,'lesson_post_retention_cap')
            mode = self.db.execute('SELECT mode FROM authors WHERE tenant=? AND user=?',(tenant,author)).fetchone()
            mode = mode[0] if mode else 'push'
            post_id = self.db.execute("INSERT INTO posts(tenant,author,operation,media_id,media_version,caption,state,mode) VALUES(?,?,?,?,?,?,'published',?)",
                (tenant,author,operation,media_id,media_version,caption,mode)).lastrowid
            if mode == 'push':
                self.db.execute("INSERT INTO jobs VALUES(?,'','pending')",(post_id,))
                self.db.execute('INSERT INTO inbox VALUES(?,?,?)',(tenant,author,post_id))
            return dict(self.db.execute('SELECT * FROM posts WHERE id=?',(post_id,)).fetchone())

    def fanout(self, post_id, batch=2):
        number(post_id,1)
        number(batch,1,50)
        with self.transaction():
            job = self.db.execute('SELECT j.cursor,j.state,p.* FROM jobs j JOIN posts p ON p.id=j.post WHERE j.post=?',(post_id,)).fetchone()
            if job is None or job['state'] == 'done':
                return 0
            if self.db.execute('SELECT state FROM posts WHERE id=?',(post_id,)).fetchone()[0] != 'published':
                self.db.execute("UPDATE jobs SET state='done' WHERE post=?",(post_id,))
                return 0
            recipients = self.db.execute('SELECT viewer FROM follows WHERE tenant=? AND author=? AND viewer>? ORDER BY viewer LIMIT ?',
                                        (job['tenant'],job['author'],job['cursor'],batch)).fetchall()
            for recipient in recipients:
                self.db.execute('INSERT INTO inbox VALUES(?,?,?) ON CONFLICT DO NOTHING',(job['tenant'],recipient['viewer'],post_id))
            self.db.execute('UPDATE jobs SET cursor=?,state=? WHERE post=?',
                (recipients[-1]['viewer'] if recipients else job['cursor'],'pending' if len(recipients)==batch else 'done',post_id))
            return len(recipients)

    def visible(self, tenant, viewer, post):
        if post['tenant'] != tenant or post['state'] != 'published':
            return False
        author = post['author']
        if self.db.execute('SELECT 1 FROM blocks WHERE tenant=? AND ((blocker=? AND blocked=?) OR (blocker=? AND blocked=?))',
                           (tenant,viewer,author,author,viewer)).fetchone():
            return False
        if viewer != author and not self.db.execute('SELECT 1 FROM follows WHERE tenant=? AND viewer=? AND author=?',(tenant,viewer,author)).fetchone():
            return False
        return self.db.execute("SELECT 1 FROM media WHERE tenant=? AND id=? AND owner=? AND version=? AND state='ready'",
            (tenant,post['media_id'],author,post['media_version'])).fetchone() is not None

    def cursor(self, tenant, viewer, high, before):
        raw = base64.urlsafe_b64encode(json.dumps([tenant,viewer,high,before],separators=(',',':')).encode()).decode()
        return raw+'.'+hmac.new(CURSOR_SECRET,raw.encode(),hashlib.sha256).hexdigest()

    def page(self, tenant, viewer, limit=10, cursor=None):
        identity(tenant)
        identity(viewer)
        number(limit,1,50)
        with self.transaction():
            if cursor:
                if type(cursor) is not str or not cursor.isascii() or len(cursor)>2048 or cursor.count('.')!=1:
                    raise Error(400,'invalid_cursor')
                raw,signature = cursor.split('.')
                if not hmac.compare_digest(hmac.new(CURSOR_SECRET,raw.encode(),hashlib.sha256).hexdigest(),signature):
                    raise Error(400,'invalid_cursor_signature')
                try:
                    owner_tenant,owner_viewer,high,before = json.loads(base64.b64decode(raw,altchars=b'-_',validate=True))
                except (ValueError,TypeError):
                    raise Error(400,'invalid_cursor_body') from None
                if (owner_tenant,owner_viewer) != (tenant,viewer):
                    raise Error(403,'cursor_scope_mismatch')
                number(high)
                number(before,1,high+1)
            else:
                high = self.db.execute('SELECT coalesce(max(id),0) FROM posts WHERE tenant=?',(tenant,)).fetchone()[0]
                before = high+1
            # Bounded teaching scan, not a production query plan or ranking engine.
            candidates = self.db.execute('''SELECT DISTINCT p.* FROM posts p LEFT JOIN inbox i
                ON i.post=p.id AND i.tenant=p.tenant AND i.viewer=?
                WHERE p.tenant=? AND p.id<=? AND p.id<? AND (p.mode='pull' OR i.post IS NOT NULL)
                ORDER BY p.id DESC''',(viewer,tenant,high,before)).fetchall()
            allowed = [dict(post) for post in candidates if self.visible(tenant,viewer,post)]
            selected = allowed[:limit]
            return {'posts':selected,'high_water':high,'next_cursor':self.cursor(tenant,viewer,high,selected[-1]['id']) if len(allowed)>limit else None}

    def delete(self, tenant, author, post_id):
        number(post_id,1)
        if not self.db.execute('SELECT 1 FROM posts WHERE id=? AND tenant=? AND author=?',(post_id,identity(tenant),identity(author))).fetchone():
            raise Error(404,'post_not_found')
        self.db.execute("UPDATE posts SET state='deleted' WHERE id=?",(post_id,))


def estimates():
    return {'new_posts_per_second':400,'assumed_mean_followers':100,'hypothetical_push_pointer_writes_per_second':40000,
        'celebrity_followers':1000000,'assumed_pointer_bytes':64,'logical_pointer_MB_for_one_celebrity_post':64,
        'fixture_posts_per_tenant_cap':256,'measured_capacity':False}


def dispatch(item, user, method, path, raw, headers):
    tenant, viewer = require(user)
    if path == '/posts' and method == 'POST':
        value = document(raw,['client_id','media_id','media_version','caption'])
        return 201,item.publish(tenant,viewer,value['client_id'],value['media_id'],value['media_version'],value['caption'])
    parsed = urlsplit(path)
    if parsed.path == '/feed' and method == 'GET':
        query = parse_qs(parsed.query,strict_parsing=True,max_num_fields=2)
        if set(query)-{'limit','cursor'} or any(len(value)!=1 for value in query.values()):
            raise Error(400,'invalid_query')
        limit = query.get('limit',['10'])[0]
        if not limit.isascii() or not limit.isdigit():
            raise Error(400,'invalid_limit')
        return 200,item.page(tenant,viewer,int(limit),query.get('cursor',[None])[0])
    match = re.fullmatch(r'/(follows|blocks)/([A-Za-z0-9_-]{1,64})',path)
    if match and method in ('PUT','DELETE'):
        action = item.follow if match[1] == 'follows' else item.block
        action(tenant,viewer,match[2],method=='PUT')
        return 200,{'enabled':method=='PUT'}
    match = re.fullmatch(r'/posts/([0-9]+)',path)
    if match and method == 'DELETE':
        item.delete(tenant,viewer,int(match[1]))
        return 200,{'deleted':True}
    raise Error(404,'unknown_route')
