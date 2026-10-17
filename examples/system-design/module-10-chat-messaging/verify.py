from chat import Chat, Hub, dispatch, estimates
from verification import Fixture
from pathlib import Path

BASE = Path(__file__).resolve().parent
with Fixture('S5',BASE) as h:
    hub = Hub()
    factory = lambda path:Chat(path,hub)
    s = h.store(factory)
    for user in ('alice','bob'):
        s.membership('t1','room',user)
    h.denied('validation','empty message',400,lambda:s.send('t1','alice','room','empty',''))
    h.denied('validation','oversized text',400,lambda:s.send('t1','alice','room','large','x'*501))
    h.denied('validation','invalid client ID',400,lambda:s.send('t1','alice','room','../id','hello'))
    h.denied('validation','nonmember cannot send',404,lambda:s.send('t1','carol','room','id','hello'))
    h.denied('validation','tenant boundary on history',404,lambda:s.catchup('t2','alice','room'))
    h.denied('validation','invalid page limit',400,lambda:s.catchup('t1','alice','room',limit=0))
    h.denied('validation','boolean sequence rejected',400,lambda:s.mark_read('t1','bob','room',True))
    first = s.send('t1','alice','room','client-1','Hello \u4f60\u597d')
    again = s.send('t1','alice','room','client-1','Hello \u4f60\u597d')
    h.check('durability','retry returns original sequence',again['seq']==first['seq']==1 and again['replay'])
    h.check('durability','duplicate retry creates one message',s.db.execute('SELECT count(*) FROM messages').fetchone()[0]==1)
    h.denied('durability','changed same-client intent conflicts',409,lambda:s.send('t1','alice','room','client-1','changed'))
    second = s.send('t1','bob','room','client-1','another sender')
    h.check('durability','client ID scope includes sender',second['seq']==2)
    s.db.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON messages WHEN NEW.client_id='fail' BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('durability','message failure does not advance committed sequence',lambda:s.send('t1','alice','room','fail','failed'),
        lambda:s.db.execute("SELECT last_seq FROM rooms WHERE id='room'").fetchone()[0]==2)
    s.db.execute('DROP TRIGGER fail_insert')
    h.check('durability','next successful sequence has no rollback gap',s.send('t1','alice','room','third','third')['seq']==3)
    old_page = s.catchup('t1','bob','room',0,1)
    s.send('t1','alice','room','fourth','fourth')
    remaining = s.catchup('t1','bob','room',old_page['next_after'],50,old_page['high_water'])
    h.check('history','catchup high-water excludes later arrivals',remaining['high_water']==3 and [row['seq'] for row in remaining['messages']]==[2,3])
    h.check('history','fresh catchup discovers later message',s.catchup('t1','bob','room',3)['messages'][0]['seq']==4)
    h.check('history','first page exposes continuation',old_page['has_more'] and old_page['next_after']==1)
    h.denied('history','ahead-of-history cursor rejected',409,lambda:s.catchup('t1','bob','room',99))
    h.denied('history','snapshot beyond durable head rejected',400,lambda:s.catchup('t1','bob','room',until=99))
    h.check('history','empty tail retains cursor',s.catchup('t1','bob','room',4)['next_after']==4)
    h.check('receipts','read cursor advances',s.mark_read('t1','bob','room',3)==3)
    h.check('receipts','late device acknowledgement cannot regress cursor',s.mark_read('t1','bob','room',1)==3)
    h.denied('receipts','future read acknowledgement rejected',409,lambda:s.mark_read('t1','bob','room',5))
    h.observations['durability'] = {'first_sequence':1,'replay_sequence':again['seq'],
        'same_client_id_other_sender_sequence':2,'rollback_advances_sequence':False,
        'snapshot_high_water':3,'snapshot_remaining_sequences':[row['seq'] for row in remaining['messages']],
        'later_message_requires_new_catchup':True,'read_cursor_after_late_ack':3,'human_read_proven':False}

    connection = s.connect('t1','bob','room','phone')
    hub.drop_next = True
    dropped = s.send('t1','alice','room','lost-hint','persisted without hint')
    h.check('hints','ephemeral hint can be lost after durable commit',s.hints('t1','bob',connection)['sequences']==[])
    h.check('hints','catchup recovers message despite lost hint',s.catchup('t1','bob','room',4)['messages'][0]['seq']==dropped['seq'])
    for n in range(3):
        s.send('t1','alice','room','slow'+str(n),'slow receiver')
    overflow = s.hints('t1','bob',connection)
    h.check('hints','slow consumer receives resync marker',overflow['resync_required'] and overflow['sequences']==[])
    h.check('hints','local hint queue remains bounded',all(len(value['queue'])<=2 for value in hub.sessions.values()))
    h.denied('hints','another user cannot poll connection',404,lambda:s.hints('t1','alice',connection))
    s.disconnect('t1','bob',connection)
    h.denied('hints','closed connection cannot be polled',404,lambda:s.hints('t1','bob',connection))
    revoked = s.connect('t1','bob','room','laptop')
    s.send('t1','alice','room','before-revoke','queued hint')
    s.membership('t1','room','bob',False)
    h.denied('permissions','membership rechecked before hint delivery',404,lambda:s.hints('t1','bob',revoked))
    h.check('permissions','revoked connection routing state removed',revoked not in hub.sessions)
    h.denied('permissions','removed member cannot fetch old history',404,lambda:s.catchup('t1','bob','room'))
    h.denied('permissions','removed member cannot resend old ID',404,lambda:s.send('t1','bob','room','client-1','another sender'))
    h.denied('permissions','removed member cannot update receipt',404,lambda:s.mark_read('t1','bob','room',1))
    s.close()
    fresh_hub = Hub()
    reopened = h.store(lambda path:Chat(path,fresh_hub))
    h.check('recovery','connection state is ephemeral after restart',not fresh_hub.sessions)
    h.check('recovery','durable replay survives close/reopen',reopened.send('t1','alice','room','client-1','Hello \u4f60\u597d')['seq']==1)
    h.check('recovery','history survives loss of all hints',len(reopened.catchup('t1','alice','room')['messages'])==9)
    h.observations['hints_and_permissions'] = {'lost_hint_recovered_from_history':True,'hint_capacity':2,
        'slow_consumer_resync_required':overflow['resync_required'],'ephemeral_sessions_survive_restart':False,
        'revoked_member_history_status':404,'revoked_connection_status':404,'WebSocket_protocol_executed':False}
    racing = h.store(factory,'racing')
    racing.membership('t1','r','alice')
    same = h.race(lambda:Chat(h.root/'racing.sqlite',hub),[
        lambda item:item.send('t1','alice','r','same','same'),lambda item:item.send('t1','alice','r','same','same')])
    h.check('concurrency','concurrent duplicate sends share saved acknowledgement',same[0]['seq']==same[1]['seq']==1)
    h.check('concurrency','one duplicate is replay and one is new',sorted(row['replay'] for row in same)==[False,True])
    distinct = h.race(lambda:Chat(h.root/'racing.sqlite',hub),[
        lambda item:item.send('t1','alice','r','left','left'),lambda item:item.send('t1','alice','r','right','right')])
    h.check('concurrency','independent sends allocate distinct room sequence',sorted(row['seq'] for row in distinct)==[2,3])
    h.check('concurrency','history is authoritative order regardless hint timing',[row['seq'] for row in racing.catchup('t1','alice','r')['messages']]==[1,2,3])
    h.observations['concurrency'] = {'competing_worker_calls':4,'duplicate_send_ack_sequences':[row['seq'] for row in same],
        'distinct_send_sequences_sorted':sorted(row['seq'] for row in distinct),'hint_order_assumed':False}
    web = h.store(factory,'http')
    for user in ('alice','bob'):
        web.membership('t1','r',user)
    port = h.serve(lambda:Chat(h.root/'http.sqlite',hub),dispatch)
    h.check('http','history requires authentication',h.request(port,'GET','/rooms/r/messages',token='')[0]==401)
    h.check('http','nonmember history hidden',h.request(port,'GET','/rooms/r/messages',token='lesson-carol')[0]==404)
    opened = h.request(port,'POST','/rooms/r/connections',{'device':'phone'},token='lesson-bob')
    token = opened[2]['connection']
    sent = h.request(port,'POST','/rooms/r/messages',{'client_id':'web','text':'hello'})
    retry = h.request(port,'POST','/rooms/r/messages',{'client_id':'web','text':'hello'})
    h.check('http','real send acknowledges durable sequence',sent[0]==201 and sent[2]['seq']==1)
    h.check('http','real resend returns original saved sequence',retry[2]['seq']==1 and retry[2]['replay'])
    h.check('http','read response is no-store',sent[1]['Cache-Control']=='no-store')
    h.check('http','online hint identifies sequence not durable replacement',h.request(port,'GET','/connections/'+token,token='lesson-bob')[2]['sequences']==[1])
    h.check('http','HTTP catchup returns saved text',h.request(port,'GET','/rooms/r/messages?after=0&limit=1',token='lesson-bob')[2]['messages'][0]['text']=='hello')
    h.check('http','invalid query limit rejected',h.request(port,'GET','/rooms/r/messages?limit=bad')[0]==400)
    h.check('http','repeated cursor query rejected',h.request(port,'GET','/rooms/r/messages?after=0&after=1')[0]==400)
    h.check('http','real read ack is monotonic',h.request(port,'POST','/rooms/r/read',{'seq':1},token='lesson-bob')[2]['read_seq']==1)
    h.check('http','real connection close frees routing state',h.request(port,'DELETE','/connections/'+token,token='lesson-bob')[0]==200)
    h.check('http','other tenant cannot read messages',h.request(port,'GET','/rooms/r/messages',token='lesson-other')[0]==404)
    h.observations['http_contract'] = {'send_status':201,'original_and_retry_sequence':1,
        'online_hint_sequences':[1],'nonmember_status':404,'malformed_cursor_status':400,
        'cache_control':'no-store','actual_transport':'loopback HTTP polling','WebSocket_handshake_implemented':False}
    h.observations['estimates'] = estimates()
    h.check('estimates','daily-to-second units',estimates()['average_messages_per_second']==11.574)
    h.check('estimates','logical retained bytes',estimates()['thirty_day_logical_message_GB']==15.36)
    h.check('estimates','connection-memory units',estimates()['connection_memory_MiB']==156.25)
h.report('Local SQLite room history and bounded process-local hints with actual loopback HTTP polling. No WebSocket/SSE protocol, external messages, Redis/broker, production auth/TLS, distributed sequencing/clock, load test or proof of human reading. Current members can read retained history; removed members cannot use new API requests.')
