import sqlite3,json
db=sqlite3.connect(':memory:')
try:
    db.executescript('CREATE TABLE jobs(id TEXT PRIMARY KEY,bill INTEGER); CREATE TABLE attempts(id TEXT PRIMARY KEY,job TEXT,cost INTEGER);')
    db.executemany('INSERT INTO jobs VALUES (?,?)',[('j1',200),('j2',0),('j3',None),('j4',None),('j5',90)])
    db.executemany('INSERT INTO attempts VALUES (?,?,?)',[('a1','j1',30),('a2','j1',10),('a3','j2',20),('a4','j3',15),('a5','j4',25),('a6','j5',10)])
    wrong=db.execute('SELECT count(*),sum(bill) FROM jobs LEFT JOIN attempts ON jobs.id=attempts.job').fetchone()
    correct=db.execute('SELECT count(*),sum(bill),sum(cost),sum(bill IS NULL) FROM jobs LEFT JOIN (SELECT job,sum(cost) cost FROM attempts GROUP BY job) c ON jobs.id=c.job').fetchone()
    output={'job_rows':correct[0],'joined_rows':wrong[0],'known_bill_cents':correct[1],
            'wrong_bill_cents':wrong[1],'cost_cents':correct[2],'missing_bills':correct[3]}
finally:db.close()
print(json.dumps(output))
