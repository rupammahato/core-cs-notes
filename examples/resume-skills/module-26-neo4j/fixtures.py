"""Synthetic prerequisite graph with a cycle, shared neighbor and invalid cross-tenant edges."""
CONCEPTS = [
    {'tenant': 'alpha', 'id': 'backend', 'title': 'Backend'},
    {'tenant': 'alpha', 'id': 'http', 'title': 'HTTP'},
    {'tenant': 'alpha', 'id': 'network', 'title': 'Networking'},
    {'tenant': 'alpha', 'id': 'database', 'title': 'Databases'},
    {'tenant': 'alpha', 'id': 'transactions', 'title': 'Transactions'},
    {'tenant': 'alpha', 'id': 'framework', 'title': 'Frameworks'},
    {'tenant': 'beta', 'id': 'backend', 'title': 'Private beta backend'},
    {'tenant': 'beta', 'id': 'secret', 'title': 'Private beta procedure'},
]
EDGES = [('backend', 'http'), ('backend', 'database'), ('http', 'network'),
         ('database', 'transactions'), ('transactions', 'database'), ('framework', 'backend'),
         ('backend', 'network')]


def seed(tx):
    tx.run('CYPHER 5 UNWIND $rows AS row CREATE (c:Concept) SET c=row', rows=CONCEPTS).consume()
    tx.run('''CYPHER 5 UNWIND $edges AS edge
        MATCH (a:Concept {tenant:'alpha',id:edge[0]}), (b:Concept {tenant:'alpha',id:edge[1]})
        CREATE (a)-[:REQUIRES {tenant:'alpha'}]->(b)''', edges=EDGES).consume()
    tx.run('''CYPHER 5 MATCH (a:Concept {tenant:'alpha',id:'http'}),
        (b:Concept {tenant:'beta',id:'secret'}), (c:Concept {tenant:'alpha',id:'transactions'})
        CREATE (a)-[:REQUIRES {tenant:'alpha'}]->(b)-[:REQUIRES {tenant:'alpha'}]->(c)''').consume()
    tx.run('''CYPHER 5 CREATE
        (a:Document {tenant:'alpha',id:'notes',revision:1,deleted:false,text:'Transactions group changes atomically.'}),
        (b:Document {tenant:'beta',id:'notes',revision:1,deleted:false,text:'Private beta instructions.'})
        WITH a,b
        MATCH (c:Concept {tenant:'alpha',id:'transactions'}), (d:Concept {tenant:'beta',id:'secret'})
        CREATE (a)-[:EXPLAINS {tenant:'alpha',source_revision:1}]->(c),
               (b)-[:EXPLAINS {tenant:'beta',source_revision:1}]->(d)''').consume()
