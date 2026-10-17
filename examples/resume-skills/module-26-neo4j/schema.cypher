CREATE CONSTRAINT concept_identity IF NOT EXISTS
FOR (c:Concept) REQUIRE (c.tenant, c.id) IS UNIQUE;

CREATE CONSTRAINT document_identity IF NOT EXISTS
FOR (d:Document) REQUIRE (d.tenant, d.id) IS UNIQUE;
