"""Execute the complete lesson and verify state transitions against independent references."""
from collections import Counter
from copy import deepcopy
from graphlib import TopologicalSorter,CycleError
import hashlib
import json
import platform
import sqlite3
from warehouse import BASE,QualityError,bounded_candidates,connect,facts,fixture,ingest,mart,publish,quality,rows,state
from reference import expected


def run(write=True):
    checks=[];observations={};closed=0;opened=0
    source_paths=[BASE/'schema.sql',BASE/'fixture.json',BASE/'warehouse.py',BASE/'reference.py',BASE/'verify.py',*sorted((BASE/'models').glob('*.sql'))]
    hashes={str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths}
    def check(group,name,actual,want):
        assert actual==want,(name,actual,want)
        checks.append({'group':group,'name':name,'passed':True})
    def owned():
        nonlocal opened
        opened+=1;return connect()
    def close(db):
        nonlocal closed
        db.close();closed+=1
    def normalized_facts(db):
        return [{k:v for k,v in row.items() if k!='customer_sk'} for row in facts(db)]
    def verify_state(db,source,label):
        reference=expected(source)
        check('independent-reference',label+' complete fact projection',normalized_facts(db),reference['facts'])
        dimensions=rows(db,'SELECT tenant_id,customer_id,valid_from,valid_to,plan FROM dim_customer WHERE is_unknown=0 ORDER BY tenant_id,customer_id,valid_from')
        check('independent-reference',label+' dimension history',dimensions,reference['dimensions'])
        check('independent-reference',label+' complete mart',mart(db),reference['mart'])
        for name,value in quality(db).items():check('quality',label+' '+name,value,0)
        return {'facts':facts(db),'dimensions':dimensions,'mart':mart(db),'state':state(db)}
    batches=fixture()['batches'];source=[];stages=[];publications=[]
    db=owned()
    try:
        check('constraint','Foreign keys enabled',db.execute('PRAGMA foreign_keys').fetchone()[0],1)
        ingest(db,batches[0]);source+=batches[0]
        first=publish(db,'run1');publications.append(first)
        stages.append(verify_state(db,source,'initial'))
        observations['L01']={'raw_deliveries':db.execute('SELECT COUNT(*) FROM raw_changes').fetchone()[0],
            'distinct_unblocked_source_versions':db.execute('SELECT COUNT(*) FROM valid_changes').fetchone()[0],
            'fact_orders':len(facts(db)),'mart_rows':len(mart(db))}
        observations['L02']=rows(db,"SELECT tenant_id,COUNT(*) all_current_orders,SUM(status='paid') paid_orders FROM fact_orders GROUP BY tenant_id ORDER BY tenant_id")
        observations['L03']=rows(db,'SELECT * FROM runs ORDER BY run_id')
        observations['L04']=rows(db,"SELECT tenant_id,COUNT(*) paid_orders,SUM(billed_cents) known_cents,COUNT(*)-COUNT(billed_cents) missing_bills,CASE WHEN COUNT(*)=COUNT(billed_cents) THEN SUM(billed_cents) END complete_cents FROM fact_orders WHERE status='paid' GROUP BY tenant_id ORDER BY tenant_id")
        observations['L05']=stages[0]['dimensions']
        observations['L06']=[{k:row[k] for k in ['tenant_id','order_id','order_day','plan']} for row in facts(db)]
        observations['L07']=rows(db,"SELECT tenant_id,order_id,customer_id,customer_sk FROM fact_orders WHERE customer_sk='unknown' ORDER BY tenant_id,order_id")
        observations['L08']={'wrong_join_bill_cents':db.execute("SELECT SUM(f.billed_cents) FROM fact_orders f JOIN order_lines l USING(tenant_id,order_id) WHERE f.tenant_id='t1' AND f.order_id='o1'").fetchone()[0],
                             'correct_bill_cents':1000,'supplied_line_cents':db.execute("SELECT SUM(line_cents) FROM order_lines WHERE tenant_id='t1' AND order_id='o1'").fetchone()[0]}
        check('counterexample','Line fan-out repeats order bill',observations['L08'],{'wrong_join_bill_cents':2000,'correct_bill_cents':1000,'supplied_line_cents':1000})
        observations['L09']=rows(db,'SELECT stream,tenant_id,entity_id,source_version,COUNT(*) deliveries,COUNT(DISTINCT payload_json) payloads FROM raw_changes GROUP BY stream,tenant_id,entity_id,source_version HAVING COUNT(*)>1 ORDER BY tenant_id,entity_id')
        observations['L10']=rows(db,'SELECT * FROM blocked_entities ORDER BY stream,tenant_id,entity_id')
        observations['L13']=rows(db,"SELECT tenant_id,entity_id order_id,json_extract(payload_json,'$.schema_version') schema_version,json_extract(payload_json,'$.order_day') order_day FROM valid_changes WHERE stream='orders' AND entity_id='o1' ORDER BY tenant_id,source_version")
        dag={'raw':set(),'canonical':{'raw'},'dimensions':{'canonical'},'facts':{'dimensions','canonical'},'mart':{'facts','dimensions'},'quality':{'mart','facts','dimensions'},'publication':{'quality'}}
        order=list(TopologicalSorter(dag).static_order())
        check('orchestration','Topological order satisfies every dependency',all(order.index(dep)<order.index(node) for node,deps in dag.items() for dep in deps),True)
        observations['L14']={'declared_dependency_order':order,'dbt_or_airflow_executed':False}
        cyclic=deepcopy(dag);cyclic['raw']={'publication'}
        try:list(TopologicalSorter(cyclic).static_order())
        except CycleError:check('orchestration','Cyclic declared lineage is rejected',True,True)
        else:raise AssertionError('Expected cycle rejection')
        observations['L15']=quality(db)
        ingest(db,batches[1]);source+=batches[1]
        before={'state':state(db),'facts':facts(db),'mart':mart(db)}
        try:publish(db,'run2-failed',fail_after_replace=True)
        except RuntimeError as error:failure=str(error)
        else:raise AssertionError('Injected interruption did not fail')
        check('recovery','Pointer and watermark rolled back',state(db),before['state'])
        check('recovery','Fact/dimension replacement rolled back',facts(db),before['facts'])
        check('recovery','Readers retain last-good mart',mart(db),before['mart'])
        check('recovery','Failed run manifest absent',db.execute("SELECT COUNT(*) FROM runs WHERE run_id='run2-failed'").fetchone()[0],0)
        check('recovery','Raw input remains accepted after publication failure',db.execute('SELECT MAX(ingest_seq) FROM raw_changes').fetchone()[0],20)
        observations['L22']={'injected_error':failure,'before':before['state'],'after':state(db),'raw_upper_seq':20,'last_good_rows_unchanged':mart(db)==before['mart']}
        second=publish(db,'run2');publications.append(second);stages.append(verify_state(db,source,'corrected'))
        observations['L11']={'initial_order_o1':[r for r in stages[0]['facts'] if r['tenant_id']=='t1' and r['order_id']=='o1'],
                             'corrected_order_o1':[r for r in facts(db) if r['tenant_id']=='t1' and r['order_id']=='o1']}
        observations['L17']={'initial':stages[0]['mart'],'corrected':mart(db)}
        observations['L18']=second
        check('incremental','Deleted final paid day removed',any(r['tenant_id']=='t1' and r['order_day']=='2026-10-04' for r in mart(db)),False)
        check('incremental','Other tenant not in changed partition set',any(r['tenant_id']=='t2' for r in second['affected_partitions']),False)
        check('replay','Repeating delivery batch inserts nothing',ingest(db,batches[1]),0)
        check('replay','Repeating successful run id is idempotent',publish(db,'run2'),{'already_published':True,'run_id':'run2'})
        ingest(db,batches[2]);source+=batches[2]
        third=publish(db,'run3');publications.append(third);stages.append(verify_state(db,source,'final'))
        observations['L12']={'stale_deliveries':rows(db,"SELECT delivery_id,entity_id,source_version FROM raw_changes WHERE delivery_id IN ('o1-old-again','o2-old-again') ORDER BY delivery_id"),
                             'o2_current_fact_count':db.execute("SELECT COUNT(*) FROM fact_orders WHERE tenant_id='t1' AND order_id='o2'").fetchone()[0]}
        observations['L16']={'retained_raw_campaign':db.execute("SELECT json_extract(payload_json,'$.campaign') FROM raw_changes WHERE delivery_id='o1-extra-field'").fetchone()[0],
                             'modeled_order':[r for r in facts(db) if r['tenant_id']=='t1' and r['order_id']=='o1']}
        observations['L19']={'publication':third,'final_mart':mart(db)}
        check('incremental','Moving last order removes old partition',any(r['tenant_id']=='t1' and r['order_day']=='2026-10-05' for r in mart(db)),False)
        final_mart=mart(db);full=publish(db,'full-check',force_full=True)
        check('incremental','Full refresh equals partition-selected result',mart(db),final_mart)
        check('replay','No-change rebuild preserves semantic output',mart(db),stages[2]['mart'])
        check('publication','Old published mart remains immutable',mart(db,'run1'),stages[0]['mart'])
        observations['L21']={'failed_row_counts':quality(db),'all_eight_gates_passed':not any(quality(db).values()),'quarantine_is_separate_warning':full['quarantined_entities']}
        observations['L25']=[{'run_id':f'run{i+1}','tenant_id':tenant,'known_bill_cents':sum(r['known_bill_cents'] for r in snapshot['mart'] if r['tenant_id']==tenant),
                              'paid_orders':sum(r['paid_orders'] for r in snapshot['mart'] if r['tenant_id']==tenant)} for i,snapshot in enumerate(stages) for tenant in ['t1','t2']]
        observations['L26']=rows(db,"SELECT tenant_id,SUM(paid_orders) paid_orders,SUM(known_bill_cents) known_cents,SUM(missing_bills) missing_bills,CASE WHEN SUM(missing_bills)=0 THEN SUM(known_bill_cents) END complete_cents,CASE WHEN SUM(missing_bills)=0 THEN 1.0*SUM(known_bill_cents)/SUM(paid_orders) END complete_average_cents FROM mart_daily WHERE run_id='run3' GROUP BY tenant_id ORDER BY tenant_id")
        observations['L27']=final_mart
        observations['L28']=rows(db,"WITH days AS(SELECT order_day,SUM(known_bill_cents) amount,SUM(paid_orders) n FROM mart_daily WHERE run_id='run3' AND tenant_id='t1' GROUP BY order_day) SELECT AVG(1.0*amount/n) unweighted_daily_average,1.0*SUM(amount)/SUM(n) correct_order_weighted_average FROM days")
        check('counterexample','Daily average of averages differs from order-weighted mean',round(observations['L28'][0]['correct_order_weighted_average']-observations['L28'][0]['unweighted_daily_average'],6),69.444444)
        observations['L29']=rows(db,"SELECT f.tenant_id,f.order_id,d.plan,f.billed_cents FROM fact_orders f JOIN dim_customer d USING(tenant_id,customer_sk) WHERE f.order_id='o1' ORDER BY f.tenant_id")
        check('tenant-scope','Same business identity stays separate across tenants',[r['billed_cents'] for r in observations['L29']],[1200,9000])
        observations['L31']={'local_raw_upper':25,'committed_upper':state(db)['committed_seq'],'quarantined_entities':full['quarantined_entities'],'all_source_entities_complete':False}
        # Access-path experiment on a separate table, without modifying model inputs.
        db.execute('CREATE TABLE probe_orders(tenant_id TEXT,order_id TEXT,order_day TEXT)')
        db.executemany('INSERT INTO probe_orders VALUES(?,?,?)',[('t1',f'h{i}','2025-01-01') for i in range(10000)]+[('t1','a','2026-10-02'),('t1','b','2026-10-03'),('t2','z','2026-10-02')])
        query="SELECT order_id FROM probe_orders WHERE tenant_id='t1' AND order_day>='2026-10-02' AND order_day<'2026-10-04' ORDER BY order_day,order_id"
        before_plan=rows(db,'EXPLAIN QUERY PLAN '+query);before_rows=rows(db,query)
        db.execute('CREATE INDEX probe_tenant_day ON probe_orders(tenant_id,order_day,order_id)')
        after_plan=rows(db,'EXPLAIN QUERY PLAN '+query)
        check('query-plan','Unindexed probe scans',any('SCAN probe_orders' in r['detail'] for r in before_plan),True)
        check('query-plan','Composite probe index supports covering search',any('COVERING INDEX probe_tenant_day' in r['detail'] for r in after_plan),True)
        check('query-plan','Index preserves ordered rows',rows(db,query),before_rows)
        observations['L30']={'before':before_plan,'after':after_plan,'result':before_rows,'timing_benchmark':False}
        observations['L32']={'assumed_rows':1000000,'assumed_logical_bytes_per_row':1000,'unpruned_logical_bytes':1000000000,
                             'assumed_partition_share':.1,'assumed_column_share':.2,'illustrative_remaining_bytes':20000000,'measured_scan_or_cost':False}
        check('capacity-arithmetic','Declared logical pruning arithmetic',1000000*1000*.1*.2,observations['L32']['illustrative_remaining_bytes'])
        # Quality failures land in raw but cannot move the successful checkpoint.
        bad=deepcopy(batches[2][-1]);bad['delivery_id']='negative-v4';bad['source_version']=4;bad['payload']['billed_cents']=-50
        ingest(db,[bad]);source.append(bad);last_good=state(db);last_rows=mart(db)
        try:publish(db,'negative-rejected')
        except QualityError as error:negative_report=json.loads(str(error))
        else:raise AssertionError('Negative bill was published')
        check('quality-failure','Semantic negative amount fails gate',negative_report['negative_bills'],1)
        check('quality-failure','Negative candidate preserves pointer',state(db),last_good)
        check('quality-failure','Negative candidate preserves data',mart(db),last_rows)
        observations['L23']={'failure_counts':negative_report,'active_publication_unchanged':state(db)==last_good,'raw_contains_rejected_candidate':True}
        repaired=deepcopy(bad);repaired['delivery_id']='repaired-v5';repaired['source_version']=5;repaired['payload']['billed_cents']=1250
        ingest(db,[repaired]);source.append(repaired);publish(db,'repaired')
        check('quality-failure','Higher source version repairs semantic candidate',mart(db),expected(source)['mart'])
        old_upper=db.execute('SELECT MAX(ingest_seq) FROM raw_changes').fetchone()[0]
        invalid=deepcopy(repaired);invalid['delivery_id']='bad-schema';invalid['payload']['schema_version']=2
        first_valid=deepcopy(repaired);first_valid['delivery_id']='would-have-landed'
        try:ingest(db,[first_valid,invalid])
        except ValueError:pass
        else:raise AssertionError('Unknown schema accepted')
        check('input-contract','Unsupported schema rolls back whole ingestion batch',db.execute('SELECT MAX(ingest_seq) FROM raw_changes').fetchone()[0],old_upper)
        observations['L24']={'unsupported_schema_version':2,'raw_upper_before':old_upper,'raw_upper_after':db.execute('SELECT MAX(ingest_seq) FROM raw_changes').fetchone()[0],'partial_valid_delivery_present':db.execute("SELECT COUNT(*) FROM raw_changes WHERE delivery_id='would-have-landed'").fetchone()[0]}
        conflicting_delivery=deepcopy(repaired);conflicting_delivery['payload']['billed_cents']=999
        try:ingest(db,[conflicting_delivery])
        except ValueError:check('input-contract','Delivery identity cannot change its payload',True,True)
        else:raise AssertionError('Conflicting delivery accepted')
        db.execute('BEGIN');bounded_candidates(db,old_upper)
        db.execute("UPDATE next_dim SET valid_to='2026-10-04' WHERE tenant_id='t1' AND customer_id='c1' AND valid_from='2026-10-01'")
        check('quality-failure','Overlapping effective intervals detected',quality(db)['overlapping_dimension_intervals'],1)
        db.execute('ROLLBACK')
        for name,sql in [
            ('Duplicate fact key rejected',"INSERT INTO fact_orders SELECT * FROM fact_orders LIMIT 1"),
            ('Missing tenant dimension rejected',"INSERT INTO fact_orders VALUES('absent','bad','c1','unknown','2026-10-01',1,'paid',1)")]:
            try:db.execute(sql)
            except sqlite3.IntegrityError:check('constraint',name,True,True)
            else:raise AssertionError(name)
    finally:close(db)
    reverse=owned()
    try:
        for i,batch in enumerate(batches):
            ingest(reverse,list(reversed(batch)));publish(reverse,f'reverse{i}')
            check('input-order',f'Batch {i+1} arrival order does not choose source truth',mart(reverse),stages[i]['mart'])
    finally:close(reverse)
    conflict=owned()
    try:
        original=[r for batch in batches for r in batch]
        ingest(conflict,original);publish(conflict,'before-conflict')
        late=deepcopy(batches[0][4]);late['delivery_id']='late-conflict';late['payload']['billed_cents']=1234
        ingest(conflict,[late]);publish(conflict,'after-conflict')
        check('conflict-policy','Late conflicting identity retracts entire entity',rows(conflict,"SELECT order_id FROM fact_orders WHERE tenant_id='t1' AND order_id='o1'"),[])
        check('conflict-policy','Conflict retraction agrees with independent oracle',mart(conflict),expected(original+[late])['mart'])
    finally:close(conflict)
    lookback=owned()
    try:
        ingest(lookback,batches[0]);publish(lookback,'before')
        skipped=[r for r in batches[1] if r['stream']=='orders' and r['payload']['order_day']<'2026-10-03']
        retained=[r for r in batches[1] if r not in skipped]
        ingest(lookback,retained);publish(lookback,'wrong-lookback')
        wrong=sum(r['known_bill_cents'] for r in mart(lookback) if r['tenant_id']=='t1')
        correct=sum(r['known_bill_cents'] for r in stages[1]['mart'] if r['tenant_id']=='t1')
        check('counterexample','Order-date-only cutoff misses correction and late fact',[wrong,correct],[2700,3200])
        observations['L20']={'wrong_event_date_cutoff':'2026-10-03','skipped_delivery_ids':[r['delivery_id'] for r in skipped],
                             'wrong_t1_known_cents':wrong,'correct_t1_known_cents':correct,'all_three_publications_match_full_candidates':all(p['incremental_equals_full'] for p in publications)}
    finally:close(lookback)
    check('resource-cleanup','All owned in-memory connections closed',closed,opened)
    snapshot=json.loads((BASE/'prior-notes-snapshot.json').read_text(encoding='utf-8'))
    check('preservation','All 153 earlier handbooks unchanged',len(snapshot)==153 and all(hashlib.sha256((BASE.parents[1]/name).read_bytes()).hexdigest()==digest for name,digest in snapshot.items()),True)
    check('preservation','Pipeline inputs and implementation unchanged during run',{str(p.relative_to(BASE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},hashes)
    assert sorted(observations)==[f'L{n:02}' for n in range(1,33)]
    observations=dict(sorted(observations.items()))
    proof={'verified_date':'2026-10-21','python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'total':len(checks),
           'breakdown':dict(Counter(c['group'] for c in checks)),'checks':checks,'source_sha256':hashes,'connections_opened':opened,'connections_closed':closed,
           'persistent_database_created':False,'external_services_called':False,'dbt_executed':False,'airflow_executed':False,
           'scope':'Local SQLite transactions and model queries, independent Python oracle, injected exceptions and selected policy boundaries. No power-loss, concurrent-reader, distributed CDC, cloud warehouse or production performance test.'}
    if write:
        for name,value in [('observations.json',observations),('verification-results.json',proof)]:
            (BASE/name).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({key:proof[key] for key in ['verified_date','python','sqlite','total','breakdown','connections_closed']},indent=2))
    return observations,proof


if __name__=='__main__':run()
