"""Local durable analytics: event identity, event-time windows and atomic projection."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'worked-systems-s4-s6'))
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit
import hashlib
import json
import re
from runtime import Database, Error, identity, number, document, require

WINDOW,LATENESS = 300,120
CHANNELS,KINDS = ('organic','paid','referral'),('page_view','signup','activation')


def timestamp(value):
    if type(value) is not str or len(value)>40:
        raise Error(400,'invalid_event_time')
    try:
        parsed = datetime.fromisoformat(value.replace('Z','+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.microsecond:
            raise ValueError('explicit offset and whole seconds required')
        result = int(parsed.timestamp())
    except (ValueError,OverflowError):
        raise Error(400,'invalid_event_time') from None
    return number(result,1262304000,4102444800)


def iso(value):
    return datetime.fromtimestamp(value,timezone.utc).isoformat().replace('+00:00','Z')


class Pipeline(Database):
    schema = '''
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,tenant TEXT,producer TEXT,
            event_id TEXT,fingerprint TEXT,subject TEXT,kind TEXT,channel TEXT,event_time INTEGER,
            received INTEGER,decision TEXT,UNIQUE(tenant,producer,event_id));
        CREATE INDEX IF NOT EXISTS event_frontier ON events(tenant,seq);
        CREATE TABLE IF NOT EXISTS active(tenant TEXT PRIMARY KEY,generation INTEGER);
        CREATE TABLE IF NOT EXISTS checkpoints(tenant TEXT,generation INTEGER,last_seq INTEGER,
            updated INTEGER,watermark INTEGER,PRIMARY KEY(tenant,generation));
        CREATE TABLE IF NOT EXISTS effects(tenant TEXT,generation INTEGER,event INTEGER,decision TEXT,
            PRIMARY KEY(tenant,generation,event));
        CREATE TABLE IF NOT EXISTS counts(tenant TEXT,generation INTEGER,bucket INTEGER,channel TEXT,kind TEXT,
            n INTEGER,PRIMARY KEY(tenant,generation,bucket,channel,kind));
        CREATE TABLE IF NOT EXISTS participants(tenant TEXT,generation INTEGER,bucket INTEGER,channel TEXT,kind TEXT,
            subject TEXT,PRIMARY KEY(tenant,generation,bucket,channel,kind,subject));
        CREATE TABLE IF NOT EXISTS erased(tenant TEXT,subject TEXT,PRIMARY KEY(tenant,subject));
    '''

    def setup(self,tenant):
        identity(tenant)
        self.db.execute('INSERT INTO active VALUES(?,1) ON CONFLICT DO NOTHING',(tenant,))
        self.db.execute('INSERT INTO checkpoints VALUES(?,1,0,0,0) ON CONFLICT DO NOTHING',(tenant,))

    def checkpoint(self,tenant):
        row = self.db.execute('''SELECT c.* FROM checkpoints c JOIN active a
            ON a.tenant=c.tenant AND a.generation=c.generation WHERE c.tenant=?''',(identity(tenant),)).fetchone()
        if row is None:
            raise Error(404,'pipeline_not_configured')
        return dict(row)

    def validate(self,value,now):
        fields = {'id','subject','kind','channel','event_time','schema_version'}
        if type(value) is not dict or set(value)!=fields or type(value['schema_version']) is not int or value['schema_version']!=1:
            raise Error(400,'invalid_event_schema')
        for field in ('id','subject'):
            identity(value[field])
        if value['kind'] not in KINDS or value['channel'] not in CHANNELS:
            raise Error(400,'unknown_event_dimension')
        at = timestamp(value['event_time'])
        if at>now+60:
            raise Error(400,'future_event_skew')
        canonical = [value['subject'],value['kind'],value['channel'],at,1]
        digest = hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()
        return dict(value,event_time=at,fingerprint=digest)

    def append(self,tenant,producer,values,now):
        identity(tenant)
        identity(producer)
        number(now)
        if type(values) is not list or not 1<=len(values)<=16:
            raise Error(400,'batch_size')
        normalized = [self.validate(v,now) for v in values]
        result = []
        with self.transaction():
            self.checkpoint(tenant)
            for event in normalized:
                if self.db.execute('SELECT 1 FROM erased WHERE tenant=? AND subject=?',(tenant,event['subject'])).fetchone():
                    raise Error(410,'subject_erased')
                old = self.db.execute('SELECT * FROM events WHERE tenant=? AND producer=? AND event_id=?',(tenant,producer,event['id'])).fetchone()
                if old:
                    if old['fingerprint']!=event['fingerprint']:
                        raise Error(409,'changed_event_intent')
                    seq = old['seq']
                else:
                    if self.db.execute('SELECT count(*) FROM events').fetchone()[0]>=512:
                        raise Error(503,'lesson_event_retention_cap')
                    seq = self.db.execute('''INSERT INTO events(tenant,producer,event_id,fingerprint,subject,
                        kind,channel,event_time,received,decision) VALUES(?,?,?,?,?,?,?,?,?,NULL)''',
                        (tenant,producer,event['id'],event['fingerprint'],event['subject'],event['kind'],event['channel'],event['event_time'],now)).lastrowid
                result.append({'id':event['id'],'seq':seq,'replay':old is not None})
        return result

    def apply(self,tenant,generation,event,decision):
        inserted = self.db.execute('INSERT INTO effects VALUES(?,?,?,?) ON CONFLICT DO NOTHING',
            (tenant,generation,event['seq'],decision)).rowcount
        if not inserted or decision!='included':
            return
        bucket = event['event_time']//WINDOW*WINDOW
        self.db.execute('''INSERT INTO counts VALUES(?,?,?,?,?,1) ON CONFLICT(tenant,generation,bucket,channel,kind)
            DO UPDATE SET n=n+1''',(tenant,generation,bucket,event['channel'],event['kind']))
        self.db.execute('INSERT INTO participants VALUES(?,?,?,?,?,?) ON CONFLICT DO NOTHING',
            (tenant,generation,bucket,event['channel'],event['kind'],event['subject']))

    def process(self,tenant,limit,now):
        number(limit,1,32)
        number(now)
        with self.transaction():
            checkpoint = self.checkpoint(tenant)
            rows = self.db.execute('SELECT * FROM events WHERE tenant=? AND seq>? ORDER BY seq LIMIT ?',
                (tenant,checkpoint['last_seq'],limit)).fetchall()
            for event in rows:
                closes = (event['event_time']//WINDOW+1)*WINDOW+LATENESS
                decision = event['decision'] or ('late_excluded' if closes<=checkpoint['watermark'] else 'included')
                self.apply(tenant,checkpoint['generation'],event,decision)
                self.db.execute('UPDATE events SET decision=? WHERE seq=?',(decision,event['seq']))
            frontier = rows[-1]['seq'] if rows else checkpoint['last_seq']
            self.db.execute('UPDATE checkpoints SET last_seq=?,updated=? WHERE tenant=? AND generation=?',
                (frontier,now,tenant,checkpoint['generation']))
            return {'processed':len(rows),'last_seq':frontier,'generation':checkpoint['generation']}

    def watermark(self,tenant,value,now):
        number(now)
        number(value,0,now)
        with self.transaction():
            checkpoint = self.checkpoint(tenant)
            if value<checkpoint['watermark']:
                raise Error(409,'watermark_regression')
            if self.db.execute('SELECT 1 FROM events WHERE tenant=? AND seq>?',(tenant,checkpoint['last_seq'])).fetchone():
                raise Error(409,'drain_before_watermark')
            self.db.execute('UPDATE checkpoints SET watermark=?,updated=? WHERE tenant=? AND generation=?',(value,now,tenant,checkpoint['generation']))
            return value

    def rebuild(self,tenant,now):
        number(now)
        with self.transaction():
            old = self.checkpoint(tenant)
            if self.db.execute('SELECT 1 FROM events WHERE tenant=? AND seq>?',(tenant,old['last_seq'])).fetchone():
                raise Error(409,'drain_before_rebuild')
            generation = old['generation']+1
            if generation>4:
                raise Error(503,'lesson_generation_retention_cap')
            self.db.execute('INSERT INTO checkpoints VALUES(?,?,?,?,?)',(tenant,generation,old['last_seq'],now,old['watermark']))
            for event in self.db.execute('SELECT * FROM events WHERE tenant=? ORDER BY seq',(tenant,)).fetchall():
                self.apply(tenant,generation,event,event['decision'])
            self.db.execute('UPDATE active SET generation=? WHERE tenant=?',(generation,tenant))
            return generation

    def forget(self,tenant,subject,now):
        # Trusted privacy-admin fixture operation; no public deletion endpoint.
        identity(subject)
        number(now)
        with self.transaction():
            checkpoint = self.checkpoint(tenant)
            self.db.execute('INSERT INTO erased VALUES(?,?) ON CONFLICT DO NOTHING',(tenant,subject))
            removed = self.db.execute('DELETE FROM events WHERE tenant=? AND subject=?',(tenant,subject)).rowcount
            for table in ('effects','counts','participants'):
                self.db.execute('DELETE FROM '+table+' WHERE tenant=?',(tenant,))
            for event in self.db.execute('SELECT * FROM events WHERE tenant=? AND decision IS NOT NULL ORDER BY seq',(tenant,)).fetchall():
                self.apply(tenant,checkpoint['generation'],event,event['decision'])
            self.db.execute('UPDATE checkpoints SET updated=? WHERE tenant=? AND generation=?',(now,tenant,checkpoint['generation']))
            return {'removed_event_rows':removed,'erasure_marker_retained':True}

    def dashboard(self,tenant,start,buckets):
        number(start)
        number(buckets,1,12)
        if start%WINDOW:
            raise Error(400,'unaligned_window')
        with self.transaction():
            checkpoint = self.checkpoint(tenant)
            rows = []
            for bucket in range(start,start+buckets*WINDOW,WINDOW):
                for channel in CHANNELS:
                    where = (tenant,checkpoint['generation'],bucket,channel)
                    views = self.db.execute("SELECT n FROM counts WHERE tenant=? AND generation=? AND bucket=? AND channel=? AND kind='page_view'",where).fetchone()
                    signups = self.db.execute("SELECT subject FROM participants WHERE tenant=? AND generation=? AND bucket=? AND channel=? AND kind='signup'",where).fetchall()
                    activated = self.db.execute("SELECT subject FROM participants WHERE tenant=? AND generation=? AND bucket=? AND channel=? AND kind='activation'",where).fetchall()
                    cohort = {r[0] for r in signups}
                    converted = cohort.intersection(r[0] for r in activated)
                    rows.append({'window_start':iso(bucket),'channel':channel,'page_view_events':views[0] if views else 0,
                        'signed_up_subjects':len(cohort),'activated_signup_subjects':len(converted),
                        'activation_rate':len(converted)/len(cohort) if cohort else None,
                        'finalized_under_policy':bucket+WINDOW+LATENESS<=checkpoint['watermark']})
            high = self.db.execute('SELECT coalesce(max(seq),0) FROM events WHERE tenant=?',(tenant,)).fetchone()[0]
            pending = self.db.execute('SELECT count(*) FROM events WHERE tenant=? AND seq>?',(tenant,checkpoint['last_seq'])).fetchone()[0]
            return {'metric_definition':'same_window_same_channel_signup_activation_v1','generation':checkpoint['generation'],
                'as_of_seq':checkpoint['last_seq'],'retained_source_high_seq':high,'pending_events':pending,
                'projection_updated_at':checkpoint['updated'],'watermark':checkpoint['watermark'],'rows':rows}


def estimates():
    return {'events_per_day':8640000,'average_events_per_second':100,'assumed_peak_multiplier':5,
        'peak_events_per_second':500,'assumed_raw_event_bytes':400,'logical_raw_GB_per_day':3.456,
        'outage_seconds':600,'backlog_at_average':60000,'drain_seconds_at_150_service_100_arrival':1200,
        'fixture_window_seconds':WINDOW,'fixture_allowed_lateness_seconds':LATENESS,'measured_capacity':False}


def dispatch(item,user,method,path,raw,headers,clock):
    tenant,producer = require(user)
    parsed = urlsplit(path)
    if path=='/events' and method=='POST':
        value = document(raw,['events'])
        return 202,{'accepted':item.append(tenant,producer,value['events'],clock())}
    if parsed.path=='/dashboard' and method=='GET':
        query = parse_qs(parsed.query,keep_blank_values=True)
        if set(query)!={'start','buckets'} or any(len(v)!=1 for v in query.values()):
            raise Error(400,'invalid_query')
        if any(not re.fullmatch(r'[0-9]{1,12}',v[0]) for v in query.values()):
            raise Error(400,'invalid_window_parameters')
        return 200,item.dashboard(tenant,int(query['start'][0]),int(query['buckets'][0]))
    raise Error(404,'unknown_route')
