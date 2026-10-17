from pathlib import Path
from saas import SaaS, token_hash, dispatch, estimates
from runtime import Error
from verification import Fixture

BASE = Path(__file__).resolve().parent
with Fixture('S11',BASE) as h:
    s = h.store(SaaS)
    for tenant,owner in [('t1','alice'),('t2','dave'),('home','erin'),('frank_home','frank'),('gina_home','gina')]:
        s.bootstrap(tenant,owner)
    for tenant,user,role in [('t1','bob','member'),('t1','carol','viewer'),('t1','admin','admin'),('t2','alice','member')]:
        s.seed_member(tenant,user,role)
    tokens = {u:s.session(u,t,0)['token'] for u,t in [('alice','t1'),('bob','t1'),('carol','t1'),('admin','t1'),('dave','t2'),('erin','home'),('frank','frank_home'),('gina','gina_home')]}
    a,b,c,ad,d,e,f,g = [tokens[u] for u in ('alice','bob','carol','admin','dave','erin','frank','gina')]
    h.check('sessions','trusted session derives tenant and role',s.who(a,1)=={'user':'alice','tenant':'t1','role':'owner'})
    h.check('sessions','database stores hash not bearer',s.db.execute('SELECT count(*) FROM sessions WHERE hash=?',(token_hash(a),)).fetchone()[0]==1 and a not in '\n'.join(str(tuple(r)) for r in s.db.execute('SELECT * FROM sessions')))
    h.denied('sessions','fixed shared-helper token is not authority',401,lambda:s.who('lesson-alice',1))
    h.denied('sessions','unknown opaque bearer',401,lambda:s.who('x'*43,1))
    brief = s.session('bob','t1',0,10)['token']
    h.check('sessions','session live before expiry',s.who(brief,9)['user']=='bob')
    h.denied('sessions','session expires at exact boundary',401,lambda:s.who(brief,10))
    h.denied('sessions','session cannot issue for nonmember',403,lambda:s.session('erin','t1',0))
    h.denied('sessions','oversize TTL rejected',400,lambda:s.session('bob','t1',0,3600001))
    bob_doc = s.create(b,1,'bobdoc','Bob private')
    alice_doc = s.create(a,1,'alicedoc','Alice private')
    foreign = s.create(d,1,'foreign','Other tenant')
    h.check('documents','create operation replay',s.create(b,2,'bobdoc','Bob private')['id']==bob_doc['id'])
    h.denied('documents','changed operation intent',409,lambda:s.create(b,2,'bobdoc','Changed'))
    h.check('documents','member sees own list only',[x['id'] for x in s.list_docs(b,2)]==[bob_doc['id']])
    h.check('documents','owner sees tenant documents',len(s.list_docs(a,2))==2)
    h.check('documents','admin reads other owner',s.read(ad,2,bob_doc['id'])['owner']=='bob')
    h.denied('isolation','viewer cannot read unshared document',404,lambda:s.read(c,2,bob_doc['id']))
    h.denied('isolation','member cannot read other private document',404,lambda:s.read(b,2,alice_doc['id']))
    h.denied('isolation','owner cannot read another tenant',404,lambda:s.read(a,2,foreign['id']))
    h.denied('isolation','owner cannot edit another tenant',404,lambda:s.edit(a,2,foreign['id'],1,'Attack'))
    h.denied('isolation','cross tenant share target hidden',404,lambda:s.share(a,2,alice_doc['id'],'dave',True))
    s.share(b,3,bob_doc['id'],'carol',True)
    h.check('documents','same tenant share enables read',s.read(c,3,bob_doc['id'])['title']=='Bob private')
    h.check('documents','share reflected in list',[x['id'] for x in s.list_docs(c,3)]==[bob_doc['id']])
    h.denied('roles','viewer cannot create',403,lambda:s.create(c,3,'viewer','Denied'))
    h.denied('roles','read grant does not enable edit',404,lambda:s.edit(c,3,bob_doc['id'],1,'Denied'))
    h.denied('roles','read grant does not enable resharing',404,lambda:s.share(c,3,bob_doc['id'],'alice',True))
    export = s.export(c,4,bob_doc['id'])
    h.check('exports','scoped job initially pending',export['state']=='pending')
    h.check('exports','worker rechecks and produces metadata',s.work(export['id'])=='ready')
    h.check('exports','owned result current access',s.result(c,4,export['id'])=={'title':'Bob private','version':1})
    h.denied('exports','other requester cannot read result',404,lambda:s.result(b,4,export['id']))
    s.share(b,5,bob_doc['id'],'carol',False)
    h.denied('exports','revoked grant hides completed export',404,lambda:s.result(c,5,export['id']))
    s.share(b,6,bob_doc['id'],'carol',True)
    pending = s.export(c,6,bob_doc['id'])
    s.share(b,7,bob_doc['id'],'carol',False)
    h.check('exports','worker denies revoked pending job',s.work(pending['id'])=='denied')
    s.share(b,8,bob_doc['id'],'carol',True)
    ready = s.export(c,8,bob_doc['id'])
    s.work(ready['id'])
    s.edit(b,9,bob_doc['id'],1,'Bob updated')
    h.denied('exports','changed source makes result stale',409,lambda:s.result(c,9,ready['id']))
    h.denied('documents','stale edit version conflicts',409,lambda:s.edit(b,9,bob_doc['id'],1,'Lost edit'))
    h.check('documents','create replay survives edits',s.create(b,9,'bobdoc','Bob private')['version']==2)
    h.observations['isolation_exports']={'foreign_tenant_read':404,'foreign_tenant_edit':404,
        'private_nonowner_read':404,'shared_viewer_edit':404,'completed_export_after_revoke':404,
        'pending_export_after_revoke':'denied','changed_source_export':409,'worker_result_is_metadata_not_file':True}
    s.change_member(a,10,'bob','viewer',True)
    h.check('roles','existing session sees current demotion',s.who(b,10)['role']=='viewer')
    h.denied('roles','demoted owner cannot write own doc',404,lambda:s.edit(b,10,bob_doc['id'],2,'Denied'))
    h.denied('roles','demoted member cannot create',403,lambda:s.create(b,10,'demoted','Denied'))
    h.denied('roles','admin cannot grant owner',403,lambda:s.change_member(ad,10,'carol','owner',True))
    h.denied('roles','admin cannot demote owner',403,lambda:s.change_member(ad,10,'alice','member',True))
    h.denied('roles','last owner protected',409,lambda:s.change_member(a,10,'alice','member',True))
    s.change_member(a,11,'bob','member',False)
    h.denied('roles','removed membership invalidates session',401,lambda:s.who(b,11))
    s.change_member(a,12,'bob','member',True)
    h.denied('roles','reactivation does not revive old bearer',401,lambda:s.who(b,12))
    b = s.session('bob','t1',12)['token']
    h.check('roles','new session after explicit reactivation',s.read(b,12,bob_doc['id'])['version']==2)
    switcher = s.session('alice','t1',12)['token']
    h.denied('sessions','switch to nonmember tenant denied',403,lambda:s.switch(switcher,13,'home'))
    h.check('sessions','failed switch preserves old session',s.who(switcher,13)['tenant']=='t1')
    switched = s.switch(switcher,14,'t2')
    h.check('sessions','switch rotates into verified membership',s.who(switched['token'],14)['tenant']=='t2')
    h.denied('sessions','old switched session revoked',401,lambda:s.who(switcher,14))
    h.denied('isolation','switch does not grant old tenant docs',404,lambda:s.read(switched['token'],14,alice_doc['id']))
    s.logout(switched['token'],15)
    h.denied('sessions','logout revokes bearer',401,lambda:s.who(switched['token'],15))
    h.observations['sessions_roles']={'opaque_token_stored_as_hash':True,'current_role_after_demotion':'viewer',
        'removed_member_session':401,'reactivated_old_session':401,'tenant_switch_rotates_token':True,
        'old_switch_token':401,'logout_token':401,'last_owner_change':409,'password_or_OAuth_login_executed':False}
    invitation = s.invite(a,20,'erin','member',100)
    h.denied('invitations','recipient binding',403,lambda:s.accept(f,21,invitation['token'],'workspace_join'))
    h.denied('invitations','audience binding',403,lambda:s.accept(e,21,invitation['token'],'other_app'))
    h.denied('invitations','member cannot issue invitations',403,lambda:s.invite(b,20,'frank','member',100))
    h.denied('invitations','privileged role cannot be invited',400,lambda:s.invite(a,20,'frank','owner',100))
    outcomes = h.race(lambda:SaaS(h.root/'main.sqlite'),[
        lambda x:x.accept(e,21,invitation['token'],'workspace_join'),lambda x:x.accept(e,21,invitation['token'],'workspace_join')])
    h.check('concurrency','two accepts converge on one membership',sorted(x['state'] for x in outcomes)==['accepted','already_accepted'])
    h.check('invitations','single target membership',s.db.execute("SELECT count(*) FROM members WHERE tenant='t1' AND user='erin'").fetchone()[0]==1)
    s.change_member(a,22,'erin','member',False)
    h.denied('invitations','used invite cannot reactivate removed member',409,lambda:s.accept(e,22,invitation['token'],'workspace_join'))
    expired = s.invite(a,20,'frank','viewer',30)
    h.denied('invitations','expiry exact boundary',410,lambda:s.accept(f,30,expired['token'],'workspace_join'))
    revoked = s.invite(a,20,'frank','viewer',100)
    h.denied('invitations','foreign tenant cannot revoke',404,lambda:s.revoke_invite(d,21,revoked['id']))
    s.revoke_invite(a,21,revoked['id'])
    h.denied('invitations','revoked token rejected',410,lambda:s.accept(f,22,revoked['token'],'workspace_join'))
    atomic = s.invite(a,20,'gina','viewer',100)
    s.db.execute("CREATE TRIGGER stop_accept BEFORE INSERT ON audit WHEN NEW.action='invitation.accept' BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','invite acceptance and membership rollback with audit',lambda:s.accept(g,21,atomic['token'],'workspace_join'),
        lambda:s.db.execute("SELECT count(*) FROM members WHERE tenant='t1' AND user='gina'").fetchone()[0]==0
        and s.db.execute('SELECT used_by FROM invitations WHERE id=?',(atomic['id'],)).fetchone()[0] is None)
    s.db.execute('DROP TRIGGER stop_accept')
    h.check('atomicity','invite acceptance recovers after rollback',s.accept(g,21,atomic['token'],'workspace_join')['state']=='accepted')
    h.observations['invitations']={'wrong_recipient':403,'wrong_audience':403,'exact_expiry_boundary':410,'revoked':410,
        'competing_accept_states':sorted(x['state'] for x in outcomes),'membership_rows_created':1,
        'used_invite_after_removal':409,'accept_membership_audit_rollback_tested':True,'email_sent':False}
    q = h.store(SaaS,'quota')
    q.bootstrap('small','owner',1)
    qt = q.session('owner','small',0)['token']
    def create(item,key):
        try:
            return item.create(qt,1,key,'Quota document')['id']
        except Error as error:
            return error.status
    outcomes = h.race(lambda:SaaS(h.root/'quota.sqlite'),[lambda x:create(x,'a'),lambda x:create(x,'b')])
    h.check('concurrency','last quota slot has one winner',sum(type(x) is str for x in outcomes)==1 and 409 in outcomes)
    h.check('concurrency','quota row count stays one',q.db.execute('SELECT count(*) FROM docs').fetchone()[0]==1)
    winning = q.db.execute('SELECT operation FROM creates').fetchone()[0]
    h.check('quota','create replay allowed at quota',q.create(qt,2,winning,'Quota document')['id']==next(x for x in outcomes if type(x) is str))
    h.denied('quota','different operation cannot exceed quota',409,lambda:q.create(qt,2,'new','Extra'))
    q.bootstrap('other','owner',1)
    other_token = q.session('owner','other',0)['token']
    h.check('quota','quota separated per tenant',q.create(other_token,2,'other','Separate')['tenant']=='other')
    q.bootstrap('atomic','owner',1)
    at = q.session('owner','atomic',0)['token']
    q.db.execute("CREATE TRIGGER stop_create BEFORE INSERT ON audit WHEN NEW.action='document.create' BEGIN SELECT RAISE(ABORT,'injected'); END")
    h.fault('atomicity','create quota and idempotency rollback with audit',lambda:q.create(at,2,'fault','Fault'),
        lambda:q.db.execute("SELECT count(*) FROM docs WHERE tenant='atomic'").fetchone()[0]==0
        and q.db.execute("SELECT count(*) FROM creates WHERE tenant='atomic'").fetchone()[0]==0)
    q.db.execute('DROP TRIGGER stop_create')
    h.check('atomicity','create recovers after rollback',q.create(at,3,'fault','Fault')['version']==1)
    h.observations['quota_atomicity']={'tenant_quota':1,'simultaneous_new_creates':2,'committed_documents':1,
        'rejected_create_status':409,'replay_at_full_quota_succeeds':True,'other_tenant_has_separate_quota':True,
        'document_intent_audit_rollback_tested':True}
    s.close()
    s = h.store(SaaS)
    h.check('atomicity','session and scope survive reopen',s.who(a,23)['tenant']=='t1' and s.read(a,23,alice_doc['id'])['owner']=='alice')
    port = h.serve(lambda:SaaS(h.root/'main.sqlite'),lambda item,u,m,p,raw,hd:dispatch(item,u,m,p,raw,hd,lambda:40))
    h.check('http','opaque session accepted',h.request(port,'GET','/session',token=a)[2]['tenant']=='t1')
    h.check('http','shared-helper identity rejected',h.request(port,'GET','/session',token='lesson-alice')[0]==401)
    h.check('http','anonymous rejected',h.request(port,'GET','/docs',token=None)[0]==401)
    h.check('http','cross tenant document hidden',h.request(port,'GET','/docs/'+foreign['id'],token=a)[0]==404)
    h.check('http','foreign document update hidden',h.request(port,'PUT','/docs/'+foreign['id'],{'expected_version':1,'title':'Attack'},token=a)[0]==404)
    h.check('http','tenant override body rejected',h.request(port,'POST','/docs',{'title':'Attack','tenant':'t2'},token=a,headers={'Idempotency-Key':'attack'})[0]==400)
    h.check('http','viewer create denied',h.request(port,'POST','/docs',{'title':'Denied'},token=c,headers={'Idempotency-Key':'view'})[0]==403)
    h.check('http','list is tenant scoped',all(x['tenant']=='t1' for x in h.request(port,'GET','/docs',token=a)[2]['items']))
    h.check('http','viewer privilege escalation denied',h.request(port,'PUT','/members/carol',{'role':'owner','active':True},token=c)[0]==403)
    h.check('http','owner share endpoint',h.request(port,'PUT','/docs/'+alice_doc['id']+'/shares/carol',token=a)[0]==200)
    job = h.request(port,'POST','/docs/'+alice_doc['id']+'/exports',token=c)
    h.check('http','export durable acceptance',job[0]==202 and job[2]['state']=='pending')
    s.work(job[2]['id'])
    h.check('http','export result endpoint',h.request(port,'GET','/exports/'+job[2]['id'],token=c)[2]['title']=='Alice private')
    h.check('http','other tenant export hidden',h.request(port,'GET','/exports/'+job[2]['id'],token=d)[0]==404)
    h.check('http','unshare endpoint',h.request(port,'DELETE','/docs/'+alice_doc['id']+'/shares/carol',token=a)[0]==200)
    h.check('http','revoked export hidden',h.request(port,'GET','/exports/'+job[2]['id'],token=c)[0]==404)
    http_session = s.session('bob','t1',0)['token']
    h.check('http','logout endpoint',h.request(port,'POST','/session/logout',token=http_session)[0]==200)
    h.check('http','logged out session rejected',h.request(port,'GET','/session',token=http_session)[0]==401)
    hi = h.request(port,'POST','/invitations',{'recipient':'frank','role':'viewer','expires':90},token=a)
    h.check('http','invitation issue endpoint',hi[0]==201)
    h.check('http','wrong audience at accept endpoint',h.request(port,'POST','/invitations/accept',{'invitation':hi[2]['token'],'audience':'wrong'},token=f)[0]==403)
    h.check('http','bound invitation accepted over HTTP',h.request(port,'POST','/invitations/accept',{'invitation':hi[2]['token'],'audience':'workspace_join'},token=f)[2]['state']=='accepted')
    h.check('http','accepted invitation cannot select tenant alone',h.request(port,'GET','/session',token=f)[2]['tenant']=='frank_home')
    switched_http = h.request(port,'POST','/session/switch',{'tenant':'t1'},token=f)
    h.check('http','verified switch endpoint',switched_http[0]==200 and switched_http[2]['tenant']=='t1')
    h.check('http','switch revokes previous HTTP bearer',h.request(port,'GET','/session',token=f)[0]==401)
    h.check('http','revoke invite endpoint',h.request(port,'DELETE','/invitations/'+hi[2]['id'],token=a)[0]==200)
    h.observations['http_contract']={'session':200,'fixed_lesson_token':401,'anonymous':401,'foreign_document':404,
        'foreign_document_update':404,'tenant_body_override':400,'viewer_create':403,'export_acceptance':202,
        'foreign_export':404,'revoked_export':404,'logout_reuse':401,'invite_issue':201,'invite_accept':200,
        'verified_tenant_switch':200,'old_switch_bearer':401,'invite_revoke':200,'real_loopback_HTTP':True,
        'browser_cookie_BFF_or_OAuth_executed':False}
    h.observations['estimates'] = estimates()
h.report('Local durable hashed opaque bearer sessions after trusted fixture login, current membership/role and tenant/document/share checks, rotated tenant switch, expiring revocable recipient/audience-bound invitation capabilities, atomic quota and audit, scoped metadata export with worker/delivery rechecks, four competing calls, rollback/reopen and real HTTP. No password/OIDC login, browser cookie/BFF/CSRF implementation, email, object storage, RLS deployment or production security/load claim.')
