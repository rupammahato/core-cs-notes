"""Durable room sequence/replay with bounded ephemeral hints; HTTP, not WebSocket."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
from collections import deque
from threading import RLock
from urllib.parse import parse_qs, urlsplit
import re
import uuid
from runtime import Database, Error, document, identity, number, require


class Hub:
    def __init__(self):
        self.lock, self.sessions = RLock(), {}
        self.drop_next = False

    def connect(self, tenant, user, room, device):
        with self.lock:
            if len(self.sessions)>=16:
                raise Error(503,'lesson_connection_cap')
            token = uuid.uuid4().hex
            self.sessions[token] = {'tenant':tenant,'user':user,'room':room,
                'device':device,'queue':deque(),'resync_required':False}
            return token

    def push(self, tenant, room, seq):
        with self.lock:
            if self.drop_next:
                self.drop_next = False
                return
            for value in self.sessions.values():
                if (value['tenant'],value['room']) != (tenant,room) or value['resync_required']:
                    continue
                if len(value['queue'])>=2:
                    value['queue'].clear()
                    value['resync_required'] = True
                else:
                    value['queue'].append(seq)


class Chat(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS rooms(tenant TEXT,id TEXT,last_seq INTEGER,PRIMARY KEY(tenant,id));
        CREATE TABLE IF NOT EXISTS members(tenant TEXT,room TEXT,user TEXT,active INTEGER,
            PRIMARY KEY(tenant,room,user));
        CREATE TABLE IF NOT EXISTS messages(tenant TEXT,room TEXT,seq INTEGER,sender TEXT,client_id TEXT,text TEXT,
            PRIMARY KEY(tenant,room,seq),UNIQUE(tenant,room,sender,client_id));
        CREATE TABLE IF NOT EXISTS reads(tenant TEXT,room TEXT,user TEXT,seq INTEGER,
            PRIMARY KEY(tenant,room,user));
    '''

    def __init__(self, path, hub):
        super().__init__(path)
        self.hub = hub

    def member(self, tenant, user, room):
        for value in (tenant,user,room):
            identity(value)
        value = self.db.execute('SELECT active FROM members WHERE tenant=? AND room=? AND user=?',(tenant,room,user)).fetchone()
        if value is None or not value['active']:
            raise Error(404,'room_not_found')

    def membership(self, tenant, room, user, active=True):
        # Trusted administrative fixture; inviting/removing users needs product auth.
        for value in (tenant,room,user):
            identity(value)
        if type(active) is not bool:
            raise Error(400,'invalid_membership')
        with self.transaction():
            self.db.execute('INSERT INTO rooms VALUES(?,?,0) ON CONFLICT DO NOTHING',(tenant,room))
            self.db.execute('INSERT INTO members VALUES(?,?,?,?) ON CONFLICT(tenant,room,user) DO UPDATE SET active=excluded.active',
                            (tenant,room,user,int(active)))

    def send(self, tenant, user, room, client_id, text):
        identity(client_id)
        if type(text) is not str or not 1 <= len(text) <= 500:
            raise Error(400,'invalid_message')
        replay = False
        with self.transaction():
            self.member(tenant,user,room)
            old = self.db.execute('SELECT * FROM messages WHERE tenant=? AND room=? AND sender=? AND client_id=?',
                                  (tenant,room,user,client_id)).fetchone()
            if old:
                if old['text'] != text:
                    raise Error(409,'changed_message_intent')
                result, replay = dict(old), True
            else:
                row = self.db.execute('SELECT last_seq FROM rooms WHERE tenant=? AND id=?',(tenant,room)).fetchone()
                if row['last_seq']>=256:
                    raise Error(503,'lesson_message_retention_cap')
                seq = row['last_seq']+1
                self.db.execute('INSERT INTO messages VALUES(?,?,?,?,?,?)',(tenant,room,seq,user,client_id,text))
                self.db.execute('UPDATE rooms SET last_seq=? WHERE tenant=? AND id=?',(seq,tenant,room))
                result = {'tenant':tenant,'room':room,'seq':seq,'sender':user,'client_id':client_id,'text':text}
        # The durable ack does not depend on an ephemeral notification succeeding.
        if not replay:
            self.hub.push(tenant,room,result['seq'])
        return {**result,'replay':replay}

    def catchup(self, tenant, user, room, after=0, limit=20, until=None):
        number(after)
        number(limit,1,50)
        with self.transaction():
            self.member(tenant,user,room)
            last = self.db.execute('SELECT last_seq FROM rooms WHERE tenant=? AND id=?',(tenant,room)).fetchone()[0]
            high = last if until is None else number(until,0,last)
            if after>high:
                raise Error(409,'cursor_ahead_of_history')
            rows = self.db.execute('SELECT * FROM messages WHERE tenant=? AND room=? AND seq>? AND seq<=? ORDER BY seq LIMIT ?',
                                   (tenant,room,after,high,limit+1)).fetchall()
            page = rows[:limit]
            return {'messages':[dict(row) for row in page],'high_water':high,
                    'next_after':page[-1]['seq'] if page else after,'has_more':len(rows)>limit}

    def connect(self, tenant, user, room, device):
        identity(device)
        with self.transaction():
            self.member(tenant,user,room)
            return self.hub.connect(tenant,user,room,device)

    def hints(self, tenant, user, connection):
        identity(connection)
        with self.transaction(), self.hub.lock:
            value = self.hub.sessions.get(connection)
            if value is None or (value['tenant'],value['user']) != (tenant,user):
                raise Error(404,'connection_not_found')
            try:
                self.member(tenant,user,value['room'])
            except Error:
                del self.hub.sessions[connection]
                raise
            result = {'sequences':list(value['queue']),'resync_required':value['resync_required']}
            value['queue'].clear()
            return result

    def mark_read(self, tenant, user, room, seq):
        number(seq)
        with self.transaction():
            self.member(tenant,user,room)
            last = self.db.execute('SELECT last_seq FROM rooms WHERE tenant=? AND id=?',(tenant,room)).fetchone()[0]
            if seq>last:
                raise Error(409,'read_cursor_ahead')
            self.db.execute('INSERT INTO reads VALUES(?,?,?,?) ON CONFLICT(tenant,room,user) DO UPDATE SET seq=max(reads.seq,excluded.seq)',
                            (tenant,room,user,seq))
            return self.db.execute('SELECT seq FROM reads WHERE tenant=? AND room=? AND user=?',(tenant,room,user)).fetchone()[0]

    def disconnect(self, tenant, user, connection):
        with self.hub.lock:
            value = self.hub.sessions.get(identity(connection))
            if value is None or (value['tenant'],value['user']) != (tenant,user):
                raise Error(404,'connection_not_found')
            del self.hub.sessions[connection]


def estimates():
    return {'daily_messages':1000000,'average_messages_per_second':round(1000000/86400,3),
        'assumed_message_bytes':512,'thirty_day_logical_message_GB':15.36,
        'online_connections':10000,'assumed_connection_memory_KiB':16,
        'connection_memory_MiB':156.25,'fixture_hint_capacity':2,'measured_capacity':False}


def dispatch(item, user, method, path, raw, headers):
    tenant, sender = require(user)
    parsed = urlsplit(path)
    match = re.fullmatch(r'/rooms/([A-Za-z0-9_-]{1,64})/(messages|connections|read)',parsed.path)
    if match:
        room, action = match.groups()
        if method == 'POST' and not parsed.query:
            if action == 'messages':
                value = document(raw,['client_id','text'])
                return 201,item.send(tenant,sender,room,**value)
            if action == 'connections':
                value = document(raw,['device'])
                return 201,{'connection':item.connect(tenant,sender,room,value['device'])}
            value = document(raw,['seq'])
            return 200,{'read_seq':item.mark_read(tenant,sender,room,value['seq'])}
        if method == 'GET' and action == 'messages':
            query = parse_qs(parsed.query,strict_parsing=True,max_num_fields=3)
            if set(query)-{'after','limit','until'} or any(len(values)!=1 or not values[0].isascii() or not values[0].isdigit() for values in query.values()):
                raise Error(400,'invalid_cursor')
            return 200,item.catchup(tenant,sender,room,**{key:int(value[0]) for key,value in query.items()})
    match = re.fullmatch(r'/connections/([a-f0-9]{32})',path)
    if match and method == 'GET':
        return 200,item.hints(tenant,sender,match[1])
    if match and method == 'DELETE':
        item.disconnect(tenant,sender,match[1])
        return 200,{'disconnected':True}
    raise Error(404,'unknown_route')
