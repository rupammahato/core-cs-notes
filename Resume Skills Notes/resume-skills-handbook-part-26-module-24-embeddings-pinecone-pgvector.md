# Resume Skills Placement Handbook — Part 26
# Module 24: Embeddings, Pinecone and pgvector

**Estimated time: 4–5 hours | Tier: 2 | Requires: M13 PostgreSQL, M23 RAG/ingestion; M8 authorization and M15 jobs help**

---

## Why this module exists

“I used a vector database” invites several follow-ups: what a vector represents, how similarity is computed, why the nearest result can still be irrelevant, what the index sacrifices for speed, and how a deleted private document stops appearing in results.

This chapter extends the document assistant from M23. It develops the mathematics, executes real PostgreSQL vector queries, compares exact and approximate retrieval, and explains the application changes needed when the search index lives in Pinecone. The interview questions are selected for their usefulness when defending these resume skills; they are not a measured frequency ranking.

**Organizing principle: compatible representations, current permitted records, and measured retrieval quality.**

---

## 1. What an embedding is

An embedding maps an input into a vector: an ordered list of numbers in a particular representation space. For text, an encoder consumes tokens and produces numbers that can be compared with other compatible outputs. Its training objective influences what closeness captures. A model trained for retrieval might place a question near passages that answer it; a different representation might emphasize another relationship.

```text
Text -> preprocessing/tokenization -> embedding model -> vector of d numbers
Query -> matching query encoder/configuration ---------> comparable query vector
```

The vector is not a database row identifier, an answer, or a cryptographic hash. Two texts with similar meaning can have different vectors; similar vectors can still represent passages that disagree on a crucial detail. A nearest-neighbor query operates on the representation, not on a formal proof of the text's truth.

The individual dimensions generally do not come with labels such as “database knowledge” or “React skill.” A three-dimensional sketch can illustrate geometry, but it does not explain each coordinate in a trained text model. This chapter's small vectors are **authored numeric fixtures**, not outputs of a learned encoder.

### Where embeddings help

| Use | What is compared | What still needs validation |
| --- | --- | --- |
| Semantic document search | Query and passage representations | Relevant, current, authorized evidence |
| Similar-question lookup | New question and stored questions | Whether answers apply to this exact question |
| Recommendation candidates | User/item representations from an appropriate model | Freshness, availability, business constraints |
| Duplicate detection | Representations of candidate documents | Exact identity or a suitable duplicate decision |
| Clustering | Representations grouped by a distance rule | Whether groups have useful human meaning |

For an exact error code, lexical search can be better than semantic resemblance. For “how does the app remember that I logged in?”, embeddings may help find a passage titled “session management.” A useful search system can run both routes and combine candidates, as introduced in M23.

---

## 2. What was actually verified

Recorded **15 October 2026** on Windows:

| Component | Recorded version |
| --- | --- |
| Python | 3.12.10 |
| PostgreSQL | 16.15 |
| pgvector | 0.8.6 |
| psycopg / psycopg-binary | 3.3.4 / 3.3.4 |
| Portable runtime | conda-forge native Windows packages, SHA-256 checked |

**92 actual local checks passed.** These include real vector operators, rejection of invalid database values, row security under an application role, atomic replacement rollback, revision guards, tombstones, HNSW/IVFFlat query plans and recall against an exact baseline.

The exact application example uses authored three-dimensional vectors. The ANN experiment uses 1,000 seeded eight-dimensional numeric vectors and five queries. **No learned embedding model, semantic-quality benchmark, LLM generation, Pinecone SDK or hosted Pinecone request was executed.** Pinecone examples verify JSON body construction only. No provider credentials or paid resources are needed.

### Reproduce

From the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-24-vectors/.venv
examples/resume-skills/module-24-vectors/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-24-vectors/requirements-lock.txt
examples/resume-skills/module-24-vectors/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-24-vectors/prepare_runtime.py
examples/resume-skills/module-24-vectors/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-24-vectors/verify.py
```

The runtime helper downloads pinned matching **PostgreSQL 16.15 / pgvector 0.8.6** Windows packages from conda-forge into `.packages/`, verifies their recorded SHA-256 hashes and extracts a portable prefix under `.runtime/`. `runtime-packages.json` records exact package URLs, dependencies and hashes; `runtime-provenance.json` identifies the executed engine. No Conda installation, activation, system extension copy or service registration is performed. The documented conda-forge option is community maintained. [pgvector installation options](https://github.com/pgvector/pgvector), [conda-forge package recipe](https://github.com/conda-forge/pgvector-feedstock/blob/main/recipe/meta.yaml)

`M24_PG_BIN` can select an already prepared compatible runtime. Its matching extension/control/SQL files and native dependencies must be available; pointing it at an arbitrary installed PostgreSQL version is insufficient. The upstream README checked during research describes newer pgvector 0.8.7, while the actual Windows package checks here use 0.8.6. Version-sensitive behavior is tied to the recorded engine, not assumed from an unrelated current release.

The installed PostgreSQL 18 service was not modified. An initial experimental cross-compiler build failed to load; its owned clusters were stopped and removed. The delivered reproduction uses the matching portable packages instead of that build. `setup-recovery.json` records this boundary. Persistent downloaded package caches are ignored by Git; temporary database data is removed after checks.

The fixture uses public local test passwords, loopback networking and no TLS. It starts a hidden native process, verifies the data directory, closes database connections, stops that exact cluster, probes its port and removes its owned temporary directory. The installed PostgreSQL service is untouched; Docker and port 3000 remain stopped.

| Check group | Passing checks |
| --- | --- |
| math | 12 |
| space | 11 |
| contract | 12 |
| engine | 11 |
| lifecycle | 12 |
| retrieval | 8 |
| authorization | 8 |
| ann | 15 |
| cleanup | 3 |

---

## 3. Dimensions and the embedding-space contract

Dimensions describe vector length, not compatibility by themselves. Two unrelated models may each output 1,536 numbers with entirely different coordinate systems. Storing both in one column of the right length can satisfy a database type while destroying the meaning of a nearest-neighbor query.

Track at least the model identifier, model/retrieval revision, output dimensions, preprocessing version and metric. If a model uses distinct query/document modes or instruction prefixes, those modes belong to the contract too: “compatible encoders” can mean a trained pair, not literally identical input formatting.

```text
space = model + model revision + dimensions + preprocessing + metric
chunk = tenant + document + document revision + chunk identity + space
```

A space identifier is application metadata. It does not become reliable just because a client supplied a plausible string. The backend chooses an active configuration, checks the encoder response, and writes that trusted configuration alongside the output.

### Provider example, distinct from the executed fixture

OpenAI's documented defaults are 1,536 dimensions for `text-embedding-3-small` and 3,072 for `text-embedding-3-large`. Its third-generation models support a `dimensions` parameter. The guide describes their embeddings as unit-normalized; that is a provider-specific property, not a rule for all embedding models. [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings)

The documented creation API accepts text inputs and can return float vectors, with response indices for batched inputs. A production adapter must validate output cardinality, associate indices with the correct chunks, enforce dimensions and reject nonfinite values. This chapter does not call that endpoint. [OpenAI embedding API reference](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create)

Before adopting any model, verify its current token limits, supported dimensions, modes, licensing/data policy and versioning. Evaluate the actual notes and questions, including JavaScript/Python code, abbreviations and paraphrases. A popular model's general benchmark does not establish suitability for your placement notes.

### Executed contract and vector mathematics

`vectors.py` is the exact source used in the checks:

```python
"""Small, explicit vector-space contract; numbers here are authored fixtures."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Space:
    model: str
    revision: str
    dimensions: int
    preprocessing: str
    metric: str = 'cosine'

    @property
    def key(self):
        return f'{self.model}:{self.revision}:{self.dimensions}:{self.preprocessing}:{self.metric}'

    def validate(self, values, space_key):
        if space_key != self.key:
            raise ValueError('Incompatible embedding space')
        if len(values) != self.dimensions:
            raise ValueError('Wrong dimensions')
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
            raise ValueError('Expected finite numbers')
        if self.metric == 'cosine' and not any(values):
            raise ValueError('Cosine requires a nonzero vector')
        return [float(v) for v in values]


SPACE = Space('authored-fixture', 'v1', 3, 'identity')


def dot(a, b):
    if len(a) != len(b):
        raise ValueError('Wrong dimensions')
    return sum(x * y for x, y in zip(a, b))


def normalize(a):
    norm = math.sqrt(dot(a, a))
    if norm == 0:
        raise ValueError('Zero norm')
    return [x / norm for x in a]


def cosine(a, b):
    return dot(normalize(a), normalize(b))


def l2(a, b):
    if len(a) != len(b):
        raise ValueError('Wrong dimensions')
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def literal(values):
    return '[' + ','.join(str(float(v)) for v in values) + ']'


def recall_at_k(expected, actual):
    if not expected:
        raise ValueError('Ground truth must be nonempty')
    return len(set(expected) & set(actual)) / len(set(expected))
```

This validator also rejects booleans, which Python otherwise treats as integers. It rejects zero vectors for cosine retrieval even though the raw database vector type can store a zero vector. The database independently checks dimensions and finite elements; layered validation gives clearer application errors while protecting stored data.

The representation key here is readable and intentionally simple. A production registry can use a structured immutable record or digest. Changing a name alone does not verify the encoder; retaining an old name after changing preprocessing is equally unsafe.

---

## 4. Cosine, dot product and Euclidean distance

Let `a` and `b` have `d` coordinates. Their dot product is the sum of coordinate-wise products. Their L2 norm is the square root of the dot product with themselves.

```text
dot(a,b)       = sum(a[i] * b[i])
norm(a)        = sqrt(sum(a[i] ** 2))
cosine(a,b)    = dot(a,b) / (norm(a) * norm(b))
cosine distance = 1 - cosine(a,b)
L2 distance   = sqrt(sum((a[i] - b[i]) ** 2))
```

Cosine compares direction and ignores positive rescaling. Dot product depends on direction and magnitude. L2 measures the straight-line gap between points. Consequently, the choice can change the ranking when vector lengths vary.

For unit vectors, `dot(a,b) = cosine(a,b)` and `L2(a,b)^2 = 2 - 2*cosine(a,b)`. The transformations are monotonic, so their nearest-neighbor rankings agree, apart from ties and numerical differences. Normalizing only the query does not establish that identity for arbitrary stored vectors.

### Actual numeric output

```json
{
  "query": [
    1,
    0,
    0
  ],
  "vectors": {
    "near": [
      0.8,
      0.2,
      0
    ],
    "large": [
      10,
      1,
      0
    ],
    "opposite": [
      -1,
      0,
      0
    ]
  },
  "rankings": {
    "cosine": [
      "large",
      "near",
      "opposite"
    ],
    "dot": [
      "large",
      "near",
      "opposite"
    ],
    "l2": [
      "near",
      "opposite",
      "large"
    ]
  },
  "large_dot": 10,
  "large_cosine": 0.995037,
  "near_l2": 0.282843
}
```

The large vector points almost in the query's direction but is far away in Euclidean space. This is why “larger score means better” requires knowing what the score measures. Cosine similarity is normally larger-is-closer; a distance is smaller-is-closer. Do not reverse a distance ordering because another API returned a similarity score.

Cosine similarity can be negative. It is not a probability of correctness. A cosine score of `0.82` does not mean “82% confidence” or that different embedding models agree about relevance at that threshold. Choose thresholds using labeled queries from the target task.

### Edge cases

Zero has no direction, so cosine is undefined there. The experiment observes `NaN` for raw cosine distance involving a zero vector; the application and schema prohibit it. `NULL` means no vector and yields a null distance. Treat missing embeddings as a visible ingestion state, rather than quietly assuming retrieval covers those documents.

Floating-point vectors can differ slightly from Python's double-precision calculations. Tests use tolerances for numeric agreement and explicit secondary ordering for exact-query ties. Deterministic tie ordering improves reproducibility; it does not make an approximate candidate set exact.

---

## 5. What a vector store does in the backend

A vector store retains representations and the metadata needed to identify/filter them. A search request computes or receives a compatible query vector, restricts the search domain, retrieves candidates and returns IDs/scores. The application then resolves current text and permissions before passing evidence to a generator or presenting results.

```text
Write: source -> chunk -> encode -> validate -> persist vector + provenance
Read:  authenticate -> encode query -> scoped candidates -> current source -> rerank/context
```

The encoder, vector index and generation model have different responsibilities. A plain pgvector column does not call an embedding provider. Pinecone also supports product modes with integrated embedding; those are a separate choice from bringing your own vectors. In both cases, the backend still owns source lifecycle and access decisions. [Pinecone key terms](https://docs.pinecone.io/guides/core-concepts/key-terms)

Store enough provenance to resolve a result: tenant, document, revision, ordinal/chunk ID, embedding space, source location and content hash where appropriate. Decide whether passage text is stored in the search record or fetched from a canonical database. Storing text twice creates a synchronization obligation; storing only IDs introduces a fetch path that must handle missing or stale records.

A result ID is not a citation by itself. Resolve it to the correct current source and its page/section offsets from M23. An old result that points to a newly edited passage cannot honestly support the old excerpt merely because the document ID stayed the same.

---

## 6. Exact search, approximate search and top-k

An exact search considers the complete eligible set under its metric and returns the nearest records. A straightforward implementation calculates distances for `N` eligible vectors of dimension `d`, then selects the best `k`. Its distance work grows roughly with `N*d`; that observation is a starting estimate, not a PostgreSQL execution-time formula.

Approximate nearest-neighbor search explores a smaller candidate region or structure. It can miss true nearest records. Whether this tradeoff helps depends on corpus size, dimension, filters, memory, query distribution and the recall requirement.

### Three distinct limits

| Setting | Purpose | Example failure if confused |
| --- | --- | --- |
| Candidate/search effort | Work performed to find candidates | Too little work misses useful neighbors |
| Retrieval top-k | Maximum number returned | Five unrelated results still satisfy top-k |
| Minimum acceptable similarity | Reject sufficiently distant results | A strict cutoff can legitimately return none |

For RAG, retrieve a candidate pool, optionally rerank, deduplicate overlapping chunks, and apply a context budget. A top-k of 20 does not mean 20 passages should all enter the prompt. Increasing top-k can add noise, duplicate evidence, token cost and unauthorized IDs requiring rejection.

An exact nearest-neighbor result is exact **relative to the stored vectors and predicate**. That says nothing about whether a passage answers the user's question. This distinction matters when reporting evaluation: ANN recall measures approximation loss; relevance recall measures retrieval usefulness against human labels.

---

## 7. pgvector fundamentals: SQL, types and operators

pgvector extends PostgreSQL with vector types, distance operators and approximate indexes. Its `<->` operator computes L2 distance, `<#>` returns negative inner product, and `<=>` computes cosine distance. Metric-specific operator classes connect an ANN index to the supported ordering. HNSW and IVFFlat are approximate alternatives to an exact scan. [pgvector upstream documentation](https://github.com/pgvector/pgvector)

The following query forms were executed in the local example:

```sql
SELECT '[1,0,0]'::vector <-> '[0.8,0.2,0]'::vector AS l2_distance;
SELECT '[1,0,0]'::vector <#> '[10,1,0]'::vector AS negative_dot;
SELECT 1 - ('[1,0,0]'::vector <=> '[10,1,0]'::vector) AS cosine_similarity;
```

The negative inner-product convention allows an ascending nearest-first order. Recover ordinary dot product by negating it. When displaying cosine similarity, calculate `1 - distance`, while keeping the index-oriented distance expression in the nearest-first ordering.

### Executed relational schema

```sql
CREATE EXTENSION vector;

CREATE TABLE documents (
    tenant_id text NOT NULL,
    document_id text NOT NULL,
    revision integer NOT NULL CHECK (revision > 0),
    deleted boolean NOT NULL DEFAULT false,
    PRIMARY KEY (tenant_id, document_id)
);

CREATE TABLE chunks (
    tenant_id text NOT NULL,
    document_id text NOT NULL,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    revision integer NOT NULL,
    space_key text NOT NULL,
    content text NOT NULL,
    embedding vector(3) NOT NULL,
    PRIMARY KEY (tenant_id, document_id, ordinal),
    FOREIGN KEY (tenant_id, document_id)
        REFERENCES documents (tenant_id, document_id) ON DELETE CASCADE,
    CHECK (vector_norm(embedding) > 0)
);

CREATE INDEX chunks_tenant_document ON chunks (tenant_id, document_id);
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY document_scope ON documents
    USING (tenant_id = current_setting('app.tenant', true))
    WITH CHECK (tenant_id = current_setting('app.tenant', true));
CREATE POLICY chunk_scope ON chunks
    USING (tenant_id = current_setting('app.tenant', true))
    WITH CHECK (tenant_id = current_setting('app.tenant', true));
GRANT SELECT, INSERT, UPDATE, DELETE ON documents, chunks TO m24_app;
```

The composite key includes the tenant, so two tenants can use `notes` as a document ID without collision. Chunk ordinals are unique within a document. The foreign key prevents orphan chunks after a hard delete; the example's application deletion uses a tombstone so stale jobs can be rejected.

The schema requires nonzero, non-null vectors for its cosine workload. The database enforces three dimensions; the application enforces the complete space contract. Neither a dimension constraint nor a text `space_key` automatically ensures that the encoder really used the declared model.

For larger models, check the installed extension's **storage and index** dimension limits separately before committing to a column/index design. A type accepting a vector does not imply that a chosen ANN operator class can index it. Reduced dimensions, other vector types or another store require evaluation; blindly truncating coordinates is not a universal migration strategy.

---

## 8. Exact authorized search and atomic publication

This small application table deliberately has no ANN index. The query can therefore establish exact behavior before approximate candidate loss is introduced. Tenant scope comes from a trusted backend authentication result; it is not taken from a public request's namespace or tenant field.

### Executed implementation

```python
"""Trusted backend supplies tenant; transaction-local scope prevents pool leakage."""
from vectors import SPACE, literal


def scoped(conn, tenant):
    if tenant not in ('alpha', 'beta'):
        raise PermissionError('Unknown authenticated tenant')
    conn.execute("SELECT set_config('app.tenant', %s, true)", (tenant,))


def publish(conn, tenant, document, revision, chunks, space_key=SPACE.key):
    prepared = [(content, SPACE.validate(vector, space_key)) for content, vector in chunks]
    with conn.transaction():
        scoped(conn, tenant)
        row = conn.execute('SELECT revision, deleted FROM documents WHERE tenant_id=%s AND document_id=%s FOR UPDATE',
                           (tenant, document)).fetchone()
        if row is None or row[1] or row[0] != revision:
            return False
        conn.execute('DELETE FROM chunks WHERE tenant_id=%s AND document_id=%s', (tenant, document))
        for ordinal, (content, vector) in enumerate(prepared):
            conn.execute('INSERT INTO chunks VALUES (%s,%s,%s,%s,%s,%s,%s::vector)',
                         (tenant, document, ordinal, revision, space_key, content, literal(vector)))
    return True


def search(conn, tenant, vector, top_k=5, min_similarity=-1, space_key=SPACE.key):
    values = SPACE.validate(vector, space_key)
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        raise ValueError('top_k outside application limit')
    if not -1 <= min_similarity <= 1:
        raise ValueError('Bad cosine threshold')
    query = literal(values)
    with conn.transaction():
        scoped(conn, tenant)
        # Exact search in this small teaching table: no ANN index is created here.
        rows = conn.execute('''
            SELECT c.document_id, c.ordinal, c.content, 1 - (c.embedding <=> %s::vector) AS similarity
            FROM chunks c JOIN documents d USING (tenant_id, document_id)
            WHERE c.tenant_id=%s AND c.space_key=%s AND NOT d.deleted AND c.revision=d.revision
              AND c.embedding <=> %s::vector <= %s
            ORDER BY c.embedding <=> %s::vector, c.document_id, c.ordinal LIMIT %s
        ''', (query, tenant, space_key, query, 1 - min_similarity, query, top_k)).fetchall()
    return [{'document': r[0], 'ordinal': r[1], 'content': r[2], 'similarity': round(r[3], 6)} for r in rows]


def delete_document(conn, tenant, document):
    with conn.transaction():
        scoped(conn, tenant)
        conn.execute('UPDATE documents SET deleted=true, revision=revision+1 WHERE tenant_id=%s AND document_id=%s',
                     (tenant, document))
        conn.execute('DELETE FROM chunks WHERE tenant_id=%s AND document_id=%s', (tenant, document))
```

`publish` validates numeric values before starting the write transaction. It locks the source row, verifies the expected revision and tombstone, replaces chunks, and commits as one unit. A failed insertion after deletion rolls the whole replacement back. The tests inject a null content value after the first replacement insert to exercise that rollback.

The source revision is authoritative. Once the source advances to revision 2, revision 1 chunks are excluded even if replacement encoding is unfinished. That design favors freshness over continuous coverage. A different product might serve the previous version with an explicit “update pending” status; the freshness promise must be deliberate.

Same-revision retries here assume deterministic output for that generation. The implementation replaces the set instead of appending duplicates. For multiple competing ingestion configurations, include the ingestion/space generation and content hash in the authoritative comparison. A revision number alone cannot distinguish every possible job configuration.

### Actual retrieval output

```json
{
  "alpha_cosine_results": [
    {
      "document": "notes",
      "ordinal": 1,
      "content": "large text",
      "similarity": 0.995037
    },
    {
      "document": "notes",
      "ordinal": 0,
      "content": "near text",
      "similarity": 0.970142
    },
    {
      "document": "other",
      "ordinal": 0,
      "content": "orthogonal",
      "similarity": 0.0
    },
    {
      "document": "notes",
      "ordinal": 2,
      "content": "opposite text",
      "similarity": -1.0
    }
  ],
  "threshold_0_98": [
    {
      "document": "notes",
      "ordinal": 1,
      "content": "large text",
      "similarity": 0.995037
    }
  ],
  "beta_results": [
    {
      "document": "notes",
      "ordinal": 0,
      "content": "private beta",
      "similarity": 1.0
    }
  ],
  "scope_after_transaction": ""
}
```

The beta passage has the exact query vector but is absent from alpha results. Threshold `0.98` leaves one alpha match; threshold `1` leaves none. These numbers illustrate numeric rules only, not useful semantic thresholds for real questions.

### Row-level security and connection scope

Policies use a transaction-local `app.tenant` setting. The application role is neither superuser nor a role with `BYPASSRLS`. RLS generally applies to ordinary roles; table owners and privileged roles have bypass behavior that must be understood. [PostgreSQL row security](https://www.postgresql.org/docs/18/ddl-rowsecurity.html)

`set_config(..., true)` confines the setting to the transaction. This prevents an application connection reused for beta from retaining alpha's scope. The tests intentionally switch tenants on the same connection and query a table without a tenant `WHERE` clause to exercise policy enforcement. [PostgreSQL transaction-local settings](https://www.postgresql.org/docs/18/sql-set.html)

This is defense against backend query mistakes, not a database credential suitable for handing to untrusted users. A client able to issue arbitrary SQL as that role could set its own custom tenant setting. Authentication, trusted tenant selection, parameterized queries and restricting database credentials to the backend remain essential. The publisher and reader should use separate least-privilege roles in a deployed service; the fixture shares one application role to keep the mechanism visible.

### Actual lifecycle output

```json
{
  "deleted_document": [
    3,
    true
  ],
  "remaining_alpha_vectors": 1,
  "remaining_beta_vectors": 1,
  "failed_publication_rolled_back": true,
  "late_worker_accepted": false
}
```

The alpha tombstone survives, its vector rows are removed, and beta vectors remain. A late revision 2 job cannot recreate the deleted source. Cache invalidation, object-storage retention and backup expiration are additional lifecycle work, not consequences of deleting a vector row.

---

## 9. HNSW: graph navigation and search effort

Hierarchical Navigable Small World search builds multiple layers of proximity links. Upper layers provide coarser navigation; lower layers refine candidate neighborhoods. Search follows the graph rather than comparing every stored point. The hierarchy is central to the original HNSW construction. [Original HNSW paper](https://arxiv.org/abs/1603.09320)

Think of looking for a location using regional roads before local streets. The analogy explains navigation, not a worst-case guarantee. Poor graph coverage, limited search effort or restrictive filters can still hide the nearest eligible point.

In the experiment, `m`/construction settings use defaults, while `hnsw.ef_search` controls the candidate search list. More effort can improve recall while doing more work. It does not repair a wrong embedding model or an authorization predicate that excludes the desired source.

```sql
CREATE INDEX ann_hnsw
ON ann_vectors USING hnsw (embedding vector_cosine_ops);

SET hnsw.ef_search = 100;
SELECT id FROM ann_vectors
ORDER BY embedding <=> '[1,0,0,0,0,0,0,0]'::vector
LIMIT 5;
```

This is the query form used by `verify.py`; its actual query vectors are seeded rows recorded in the script. An HNSW index can be built without first fitting centroids to existing data. Its graph consumes memory and adds work to inserts/builds. Choose settings with measurements from the intended write/query mix.

The fixture discourages sequential scans to exercise the ANN path, then checks `EXPLAIN` for the index's name. That is a controlled demonstration. Do not copy `enable_seqscan=off` into application defaults to conceal a planner decision. A small or selective workload may correctly favor an exact scan.

---

## 10. IVFFlat: lists, training data and probes

An inverted-file search groups vectors into regions/lists and searches selected lists near a query. In IVFFlat, the candidates retain full vector values for distance evaluation. Searching fewer lists reduces work but risks skipping nearby points assigned elsewhere.

Build the index after loading representative data so the grouping reflects the corpus. If the data distribution changes substantially, evaluate whether rebuilding is needed. A fixed list count chosen for a tiny fixture is not a production tuning rule.

```sql
CREATE INDEX ann_ivf
ON ann_vectors USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);

SET ivfflat.probes = 4;
SELECT id FROM ann_vectors
ORDER BY embedding <=> '[1,0,0,0,0,0,0,0]'::vector
LIMIT 5;
```

The executed experiment drops HNSW before creating IVFFlat so the planner cannot silently use the other ANN index. It loads the same 1,000 vectors, uses the same five queries, and compares returned IDs with ground truth. Testing both indexes while leaving the planner free to choose either would make attribution ambiguous.

| Approach | What the experiment uses | Main question to measure on your workload |
| --- | --- | --- |
| Exact | Full eligible set, distance sort | Is it already fast enough after selective filters? |
| HNSW | Graph traversal, ef_search 100 | What memory/build/write cost buys required recall? |
| IVFFlat | 10 lists, four probes | How sensitive is recall to grouping and corpus drift? |

These settings describe this experiment. The notes do not claim that four probes or `ef_search=100` guarantees a particular recall elsewhere.

---

## 11. Metadata filtering, ANN underfill and query plans

Logical SQL semantics say the results satisfy `WHERE`. They do not promise the ANN index explores every eligible neighbor. A shared approximate candidate search can spend effort on many rows that a selective predicate later rejects.

Suppose only one in twenty rows is eligible. A short candidate list may leave fewer than five matches even though the table contains fifty eligible rows. Increasing only `LIMIT` is not always the most useful correction; inspect candidate effort, filtered rows and the actual query plan.

The experiment uses a `rare` category for every twentieth row. With `hnsw.ef_search=10` and iterative scanning off, it observes underfill. Enabling `strict_order` iterative scanning supplies five eligible results on this dataset. It does not promise full recall or unlimited scanning: finite effort/memory limits remain.

```sql
SET hnsw.ef_search = 10;
SET hnsw.iterative_scan = strict_order;
SELECT id FROM ann_vectors WHERE category = 'rare'
ORDER BY embedding <=> '[1,0,0,0,0,0,0,0]'::vector LIMIT 5;
```

Possible designs include an ordinary index on selective metadata followed by exact distance calculation, a partial ANN index for a stable subset, partitioning, or more ANN effort. Compare operational cost too: one index per tenant is not a free solution for thousands of tenants.

### Keep a recognizable distance ordering

`ORDER BY embedding <=> query LIMIT k` matches the cosine index query form. In the experiment, rewriting it as `ORDER BY 1 - (embedding <=> query) DESC` produces a sort without the ANN index. Equivalent mathematical ranking does not imply an equivalent planner path.

Use `EXPLAIN` to inspect the selected plan. `EXPLAIN ANALYZE` actually executes the statement and adds runtime observations; estimates and cost units are not measured milliseconds. [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html)

### Actual index and recall observations

```json
{
  "rows": 1000,
  "dimensions": 8,
  "queries": 5,
  "k": 5,
  "exact_plan": [
    "Limit",
    "Sort",
    "Seq Scan"
  ],
  "hnsw_plan": [
    "Limit",
    "ann_hnsw"
  ],
  "ivfflat_plan": [
    "Limit",
    "ann_ivf"
  ],
  "hnsw_ef_search": 100,
  "hnsw_recall_at_5": [
    1.0,
    1.0,
    1.0,
    1.0,
    1.0
  ],
  "ivfflat_lists": 10,
  "ivfflat_probes": 4,
  "ivfflat_recall_at_5": [
    1.0,
    1.0,
    1.0,
    1.0,
    1.0
  ],
  "filtered_exact": [
    420,
    100,
    540,
    940,
    960
  ],
  "filtered_noniterative": [],
  "filtered_iterative": [
    420,
    100,
    540,
    940,
    960
  ],
  "rewritten_sort_plan": [
    "Limit",
    "Sort",
    "Seq Scan"
  ],
  "planner_note": "enable_seqscan=off used only to demonstrate actual index paths; no latency/capacity claim"
}
```

HNSW graph construction and IVFFlat grouping can vary, so future runs need not produce identical approximate IDs. The verifier checks valid results, real index use, sampled recall bounds, filter correctness, underfill and the iterative recovery observed for this controlled fixture. These are mechanism checks, not production capacity measurements.

---

## 12. Pinecone: index, namespace, record and metadata

For a bring-your-own-vector design, choose an index compatible with the vector dimensions and metric. Records have IDs, vector values and metadata. Namespaces organize records within an index; the backend targets the appropriate namespace for writes, reads and deletes. Pinecone documents a namespace-per-tenant approach for its serverless multitenant design. [Pinecone multitenancy](https://docs.pinecone.io/guides/index-data/implement-multitenancy)

Keep environment and embedding-space separation explicit too. A tenant namespace does not make development and production data compatible, nor does it authorize a caller who can choose another tenant's namespace. The backend derives namespace from authenticated membership and an internal registry.

Metadata filters can restrict returned records using supported expressions such as `$eq` and `$and`. They are structured predicates, not SQL, and provider field/type/limit rules must be checked before implementation. [Pinecone metadata filters](https://docs.pinecone.io/guides/search/filter-by-metadata)

### Executed request-body builder

```python
"""Request-body construction only: no Pinecone SDK, HTTP service or inference."""
import re
from vectors import SPACE


def namespace_for(authenticated_tenant):
    # Demonstration registry; caller is a trusted authentication layer.
    registry = {'alpha': 'tenant-alpha-space-v1', 'beta': 'tenant-beta-space-v1'}
    if authenticated_tenant not in registry:
        raise PermissionError('No tenant namespace')
    return registry[authenticated_tenant]


def record_id(document, revision, ordinal):
    if not re.fullmatch(r'[a-z0-9_-]{1,40}', document):
        raise ValueError('Bad document identifier')
    if revision < 1 or ordinal < 0:
        raise ValueError('Bad revision/ordinal')
    return f'{document}:r{revision}:c{ordinal}'


def upsert_body(tenant, document, revision, ordinal, vector, space_key=SPACE.key):
    values = SPACE.validate(vector, space_key)
    return {'namespace': namespace_for(tenant), 'vectors': [{
        'id': record_id(document, revision, ordinal), 'values': values,
        'metadata': {'document_id': document, 'revision': revision, 'space_key': space_key, 'status': 'ready'},
    }]}


def query_body(tenant, vector, top_k=10, space_key=SPACE.key):
    if isinstance(top_k, bool) or not isinstance(top_k, int) or not 1 <= top_k <= 100:
        raise ValueError('top_k outside application limit')
    return {'namespace': namespace_for(tenant), 'vector': SPACE.validate(vector, space_key),
            'topK': top_k, 'includeMetadata': True, 'includeValues': False,
            'filter': {'$and': [{'status': {'$eq': 'ready'}}, {'space_key': {'$eq': space_key}}]}}


def delete_body(tenant, document, revision, ordinals):
    if not ordinals:
        raise ValueError('Explicit record IDs required')
    return {'namespace': namespace_for(tenant),
            'ids': [record_id(document, revision, ordinal) for ordinal in ordinals]}
```

The helper creates deterministic revision-specific chunk IDs, fixes namespace selection, carries a space filter and separates query payload from an explicit delete payload. Its top-k cap is an **application choice**, not a statement about Pinecone's maximum. Metadata `status=ready` is a local record convention, not a provider publication guarantee.

### Actual local contract output

```json
{
  "upsert": {
    "namespace": "tenant-alpha-space-v1",
    "vectors": [
      {
        "id": "notes:r2:c0",
        "values": [
          1.0,
          0.0,
          0.0
        ],
        "metadata": {
          "document_id": "notes",
          "revision": 2,
          "space_key": "authored-fixture:v1:3:identity:cosine",
          "status": "ready"
        }
      }
    ]
  },
  "query": {
    "namespace": "tenant-alpha-space-v1",
    "vector": [
      1.0,
      0.0,
      0.0
    ],
    "topK": 5,
    "includeMetadata": true,
    "includeValues": false,
    "filter": {
      "$and": [
        {
          "status": {
            "$eq": "ready"
          }
        },
        {
          "space_key": {
            "$eq": "authored-fixture:v1:3:identity:cosine"
          }
        }
      ]
    }
  },
  "delete": {
    "namespace": "tenant-alpha-space-v1",
    "ids": [
      "notes:r2:c0",
      "notes:r2:c1"
    ]
  },
  "executed_scope": "JSON request-body construction only; no SDK, HTTP or hosted Pinecone"
}
```

These bodies have **not been sent to Pinecone**. An actual adapter must use the correct index host, provider authentication, API/SDK version, deadlines and response validation. The three fixture dimensions are not a recommendation for a real text-embedding model.

Upserting uses stable IDs so retries can replace the intended record rather than create duplicates. Application retries still need bounded backoff, classification of transient failures, batch-size limits and reconciliation of ambiguous outcomes. [Pinecone upsert guide](https://docs.pinecone.io/guides/index-data/upsert-data)

For document deletion, retain the published chunk manifest and delete the exact owned IDs in the tenant namespace. Revision-specific IDs make stale generations distinguishable; they also require retiring old generations. Provider delete-by-ID/filter/namespace operations have different scopes, so an empty ID list must never accidentally become a broad delete. [Pinecone deletion guide](https://docs.pinecone.io/guides/manage-data/delete-data)

### Freshness is a separate acceptance condition

Pinecone's serverless Database API documentation describes eventual consistency and namespace-local log sequence numbers. Compare the write's `x-pinecone-request-lsn` with a query's `x-pinecone-max-indexed-lsn`; a query LSN at least as large reflects that write. It does not prove the record was not subsequently changed or deleted. Counts alone cannot establish freshness after an update or equal-sized replacement. [Pinecone freshness checks](https://docs.pinecone.io/guides/index-data/check-data-freshness)

For the assistant, use a bounded freshness check appropriate to the selected API, then verify returned IDs/revisions against canonical source state. Show “indexing” while publication is incomplete. An HTTP success acknowledgment is not a substitute for the product's retrieval-readiness definition.

---

## 13. Pinecone versus pgvector: make a defensible choice

Start with the workload and team constraints. “Which is best?” is incomplete without corpus size, dimensions, write/query rate, filtering, latency, recall, tenancy, recovery, residency and operational requirements.

| Decision | pgvector-based design | Pinecone-based design |
| --- | --- | --- |
| Canonical data relationship | Vectors can share a relational database with source metadata | Search state commonly lives outside the canonical database |
| Atomic source/vector changes | Can use one local database transaction | Application coordinates state across services |
| Filtering | SQL, joins, policies and planner choices | Supported metadata predicates and namespace routing |
| Operations | Own or delegate PostgreSQL capacity, indexes, backups and recovery | Delegate vector-service internals; still own integration and source lifecycle |
| Application access boundary | Backend DB credentials, roles and row policies | Backend API credentials and trusted namespace/filter selection |
| Measurement | Plans, recall, database/resource impact | Provider usage, end-to-end latency, recall and synchronization lag |
| Failure coupling | Search may compete with relational workload | Separate service adds network/dependency failure modes |

This comparison is architectural reasoning, not a comparative benchmark. The example measures neither hosted Pinecone nor a large pgvector deployment. A managed PostgreSQL provider also changes the operational split; “pgvector means self-host everything” is not a valid assumption.

For a small placement-note assistant already using PostgreSQL, an exact filtered pgvector query is a reasonable initial design to evaluate. For a workload needing independent vector-service operation, Pinecone is a candidate to evaluate with actual filters and corpus. Neither conclusion substitutes for a representative prototype.

Record the decision with numbers and an exit condition: expected corpus, growth, QPS, acceptable approximation loss, latency budget, monthly cost assumptions and a trigger for reevaluation. Preserve source/chunk manifests and an internal search interface so a migration can rebuild derived vectors without losing document identity.

---

## 14. Architectural understanding: build a vector-backed notes assistant

Begin with one API service, a canonical document database and an ingestion worker. The browser uploads documents and sends questions; it never receives database credentials or a vector-service API key.

```text
Browser -> authenticated API -> source/document metadata
                  |                      |
                  |                  ingestion job
                  |                      v
                  |        parse -> chunk -> encode -> validate
                  |                      |
                  |               publish vector generation
                  v                      |
         query encoder -----------------+
                  |
         scoped vector/lexical candidates
                  |
         canonical revision + ACL check -> rerank -> context -> answer/citations
```

### APIs and state

| Interface | Contract to make visible |
| --- | --- |
| `POST /documents` | Authenticated owner, durable source ID, ingestion job/revision |
| `GET /documents/:id/status` | Pending, failed, ready or deleted; source and indexed revisions |
| `POST /search` | Query and bounded result count; server derives tenant/space |
| `DELETE /documents/:id` | Canonical tombstone, cleanup intent and user-visible state |
| Source/citation endpoint | Reauthorize and resolve the exact permitted revision/location |

The canonical document row should track source revision, ingestion state and expected embedding space. An ingestion record tracks the source hash, chunking version, encoder configuration, expected chunks and errors. A vector manifest identifies precisely what was published and what must later be removed.

### Write path with pgvector

Encode outside the transaction: provider latency should not hold a source row lock for seconds. Validate the response, begin a short transaction, lock/check the current revision, replace the complete generation, set readiness and commit. If the revision changed while encoding, discard or reschedule that obsolete result.

The fixture implements the lock/check/replacement portion. It does not implement an encoder, queue, document parser or ready-status endpoint. Those pieces connect to M15/M23; separating them prevents a teaching test from being mistaken for a complete deployed assistant.

### Write path with a separate vector service

Commit a source change plus an outbox/job intent in the canonical database. A worker uses deterministic IDs to upsert the expected vector generation, records progress, checks the API's freshness/readiness mechanism, and publishes a canonical manifest when eligible. Retries reconcile the same generation instead of inventing fresh IDs.

A canonical manifest update and a remote vector upsert are not one ACID transaction. A worker can crash after the remote write but before recording success. Model that state explicitly: retry/reconcile, retain cleanup intents for abandoned generations, and reject stale results during read acceptance. This reasoning follows from the separate-service boundary; the fixture does not execute a distributed transaction or a hosted worker.

### Read path and revocation

Authenticate, choose the active embedding space and authorized namespace/filter, encode the query, retrieve candidates, then resolve current canonical permissions and revision. Only accepted passage text enters reranking/context/generation. An authorization rejection can reduce the result count; bounded overfetch may improve coverage, but cannot guarantee enough permitted results for every query.

Rechecking before context helps with stale indexes, but it does not alone guarantee instantaneous revocation across an already-running generation. Define the revocation boundary. A product requiring strict revocation may need request cancellation, a final permission check before release, or coordinated source leases/version gates. Do not promise stronger consistency than the actual design enforces.

### Failure cases to explain in an interview

| Event | Desired behavior |
| --- | --- |
| Encoder returns fewer vectors than inputs | Fail the generation; do not mark partial coverage ready |
| New source revision appears during encoding | Old worker fails the revision guard |
| SQL replacement fails after deletion | Transaction restores the previous committed rows |
| Remote write succeeds but worker loses response | Retry same IDs; reconcile manifest/state |
| Deleted source remains temporarily in search | Canonical tombstone rejects it before context |
| ANN misses relevant candidates under a filter | Measure filtered recall; tune effort or change indexing strategy |
| Space migration is only half complete | Keep spaces separate and route queries to the intended generation |
| Provider unavailable | Bounded timeout; visible failure or a deliberately evaluated fallback |

---

## 15. Updates, deletion and embedding-model migration

Changing the source, chunker or embedding model can invalidate derived vectors. Track these separately. A source revision identifies document content; a chunking version identifies how it was split; an embedding space identifies the encoder contract. One overloaded `version` field makes later debugging unnecessarily difficult.

For deletion, first make the canonical source ineligible and record durable cleanup work. Remove vectors from every active/retained space, invalidate retrieval/answer caches, and retire chunk manifests. Include object-storage and backup policy in the overall data-retention design. Keep enough tombstone/generation information to reject late workers.

### Safe migration sequence

1. Register a new immutable space with its dimensions, modes and preprocessing.
2. Create the new column/table/index or remote index/namespace layout.
3. Backfill from canonical current sources with resumable progress.
4. Keep writes synchronized using explicit per-space jobs and revision checks.
5. Evaluate labeled relevance plus ANN loss separately for both spaces.
6. Shadow representative queries without exposing incompatible merged scores.
7. Switch routing deliberately and monitor failures, latency and quality.
8. Retain an appropriate rollback window, then delete retired derived data.

If two spaces are searched during migration, fuse ranks or use a calibrated reranker rather than directly sorting mixed raw similarities. A score of `0.9` in one space has no inherent equivalence to `0.9` in another. Do not mutate an existing index's declared dimensions and assume old vectors become valid.

The fixture rejects same-dimensional model/revision/preprocessing/metric mismatches and rejects late source revisions. It does not run a two-model backfill or a real encoder migration. Treat the sequence above as a system design and exercise path.

---

## 16. Evaluate retrieval without confusing the measurements

Use two ground truths. One is mathematical: the exact nearest eligible vectors in a frozen dataset. The other is task relevance: passages labeled as useful evidence for representative questions.

```text
ANN recall@k = |approximate IDs intersect exact top-k IDs| / |exact top-k IDs|
Task recall@k = |retrieved relevant passage IDs| / |all labeled relevant passage IDs|
```

The denominators differ. A perfect ANN recall can reproduce an exact embedding search that misses the answer entirely. A reranker can improve the order among retrieved candidates but cannot recover a passage that never entered the candidate set.

The exact baseline must use the same corpus snapshot, metric, namespace/tenant, revision predicate and query vector. Comparing filtered ANN against an unfiltered exact list creates a meaningless apparent recall loss. Handle distance ties explicitly when evaluating real corpora, since several IDs can be equally acceptable at the boundary.

### Evaluation slices for placement notes

Include definition questions, paraphrases, code symbols, abbreviations, long questions, similar-but-different concepts, recent edits, deleted sources, cross-tenant distractors and unanswerable questions. Examples: “event loop versus worker pool,” “what survives after a process crash?”, and an exact lookup for `READ COMMITTED`.

Record top-k coverage, first relevant rank, duplicates, no-result behavior and citation correctness. Measure p50/p95/p99 end-to-end latency under representative concurrency, with encoder, search, source lookup and reranker timing separated. Include ingestion latency and freshness, not only read speed.

The local five-query experiment proves the measurement mechanics and index paths. Eight-dimensional random numbers are not a semantic retrieval benchmark; a tiny warm local dataset cannot establish production p95, memory capacity or Pinecone economics.

---

## 17. Cost, storage and operations

For a rough numeric estimate, `N*d*4` bytes covers float32 coordinates alone. One million 1,536-dimensional vectors need approximately 6.144 billion decimal bytes before row/record metadata, text, indexes, graph/list structure, replicas and backups. This is arithmetic, not a measured database allocation.

Separate four costs: encoding the initial corpus, encoding changed chunks, serving query embeddings, and operating search/storage. Rechunking can change many chunk identities even when a small source paragraph changed. A cache key should include the exact normalized input, embedding-space contract and tenant boundary where sensitive data is involved.

Provider billing and limits change. Measure actual request usage with your chosen configuration and current pricing before claiming a monthly amount. Smaller vectors can reduce coordinate storage and arithmetic, but their effect on task relevance needs evaluation.

For PostgreSQL, observe query plans, index sizes/build time, memory/I/O, insert/update cost, dead tuples, vacuum behavior, connection usage and impact on transactional traffic. Maintain backups and test restore with the required extension version available. A successful backup command is not proof that the restored environment can load its vector extension.

For a separate service, observe authentication failures, deadlines/retries, batch failures, freshness lag, orphan generations, provider usage and canonical reconciliation backlog. A managed index still requires application monitoring and a recovery procedure.

Keep logs useful without dumping passage text or entire embeddings. Log source/generation IDs, space, result counts, rejected-stale/unauthorized counts, trace IDs and stage timing. Treat vectors as sensitive derived data where their inputs are sensitive; they are not an anonymization guarantee.

---

## 18. Common misconceptions and debugging order

| Misconception | Correction |
| --- | --- |
| Same dimensions means compatible embeddings | Model/configuration space must also match |
| The nearest result must be relevant | A ranking can select the best of unrelated records |
| Cosine score is answer confidence | Similarity is not calibrated correctness probability |
| All models output normalized vectors | Verify the chosen encoder's contract |
| Adding an ANN index preserves every exact result | Approximation can lose neighbors |
| LIMIT guarantees that many filtered results | Candidate effort and eligibility can underfill |
| A vector DB solves authorization | Backend identity, scope and current ACL checks remain |
| A remote upsert is a canonical SQL transaction | Cross-service state needs coordination/reconciliation |
| Deleting one vector removes the source everywhere | All generations, caches and retention paths matter |
| Larger top-k always improves the answer | More candidates can add noise, cost and duplication |

When results are poor, first inspect extraction and chunk text. Then inspect source freshness/permissions, encoder inputs/configuration, query/document compatibility, distance direction, predicates, candidate count, actual plan and approximation loss. Finally evaluate reranking/context/generation. Changing the vector store before finding the failing stage can preserve the same underlying mistake.

---

## 19. Interview questions and answers

### Q1. What is an embedding?

It is a numeric representation of an input in a model-defined space. Retrieval compares compatible representations to find candidates with a useful relationship to the query. The vector is neither an answer nor a guarantee of factual similarity. Explain the encoder contract and how the returned IDs resolve to source passages.

### Q2. Why use embeddings instead of keyword search?

They can retrieve related wording that does not share the query's exact terms. Keyword search remains valuable for identifiers, exact error messages and specialized vocabulary. Evaluate both over real questions; combine candidate rankings when the approaches cover different failure cases. M23's lexical baseline is a useful comparison, not something to discard automatically.

### Q3. How does a text embedding model work?

It tokenizes/processes text through a trained encoder and produces a fixed-size representation under the selected configuration. Training determines which relationships the representation tends to preserve. Some retrieval models use different query/document modes. Do not invent semantic labels for individual coordinates or claim that vector closeness proves an answer.

### Q4. Can I compare embeddings from two models if their dimensions match?

Usually no: matching length establishes a numeric shape, not a common coordinate system. Use a compatible encoder pair/configuration and record model, revision, preprocessing and dimensions. Our application rejects a different space key even when both vectors contain three numbers. Migration uses a separate space and deliberate routing.

### Q5. What is cosine similarity?

It is dot product divided by the product of the two nonzero vector norms. It compares direction and is invariant under positive scaling. Cosine distance is one minus that similarity. The fixture checks parallel, opposite and orthogonal directions and rejects zero query vectors because they have no defined cosine direction.

### Q6. How do dot product and Euclidean distance differ?

Dot product includes magnitude; Euclidean distance measures the gap between points. For unit-normalized vectors, dot equals cosine and squared L2 distance is twice cosine distance, so their rankings agree. For arbitrary magnitudes they can disagree, as the fixture's large and near vectors demonstrate. Choose the model-supported metric and verify its score direction.

### Q7. Is a similarity score of 0.9 ninety percent confidence?

No. It is a value under a representation and metric, not calibrated answer correctness. Different models and corpora can have different score distributions. Select relevance thresholds with labeled examples, including unanswerable questions, and evaluate the complete answer pipeline separately from retrieval similarity.

### Q8. What do dimensions affect?

They affect numeric shape, coordinate storage and distance work. More dimensions are not automatically better for your task. Confirm the encoder's supported dimension configuration and the store's type/index limits separately. Changing dimensions requires compatible re-encoding and evaluation; arbitrary truncation is not valid for every model.

### Q9. Does a vector database generate embeddings?

A plain vector store retains/searches vectors. An encoder generates them. Some products provide integrated embedding modes, which combine parts of that workflow under a specific API. Our pgvector example stores authored vectors; our Pinecone helper only constructs bring-your-own-vector payloads. Neither execution demonstrates learned semantic encoding.

### Q10. What is exact nearest-neighbor search?

It returns nearest records from the complete eligible set under the chosen metric and ordering. It is exact relative to the vectors and predicate, not to human relevance. Establish an exact baseline before measuring approximate-index loss, and use the same snapshot, query vector and authorization/filter scope for the comparison.

### Q11. What does ANN trade for speed?

It reduces search work using a candidate structure or region and can miss exact nearest neighbors. Measure recall against exact results alongside latency, memory, build time and update cost. A high recall observed for five random queries is not a general guarantee. Keep application relevance evaluation separate from approximation evaluation.

### Q12. How does HNSW work at a high level?

It uses a hierarchy of proximity graphs to navigate toward nearby candidates, refining the search in denser lower layers. Construction and query effort have different roles. In our experiment, increasing query effort searches a larger candidate list; a separate low-effort filtered case demonstrates why results can underfill.

### Q13. What do HNSW m, ef_construction and ef_search mean?

They control graph connection structure, construction candidate effort and query candidate effort respectively. They affect different costs, so do not treat them as interchangeable top-k values. The fixture uses default construction settings and tests query effort explicitly. Tune against representative data and filters; increasing effort cannot fix incompatible embeddings.

### Q14. How does IVFFlat differ from HNSW?

IVFFlat groups vectors into lists and searches selected nearby lists; HNSW navigates graph links. IVFFlat needs useful build data for its grouping, and probes control list exploration. Compare their recall/resource behavior on the intended workload. Our test drops HNSW before creating IVFFlat so the measured path is unambiguous.

### Q15. What are lists and probes in IVFFlat?

Lists define the grouping granularity; probes control how many groups a query explores. Too little exploration can miss neighbors in unvisited groups. Build on representative data, then vary settings and measure recall. The fixture's ten lists/four probes are experimental choices for 1,000 vectors, not a sizing recommendation for a million-document corpus.

### Q16. Why can filtered ANN return fewer than k results?

Many explored candidates can fail the metadata predicate. A finite candidate budget may stop before enough eligible rows are found even when eligible rows exist elsewhere. Inspect the actual plan and predicate selectivity. More search effort, iterative scans, exact search over a selective subset or a different index layout are possible responses.

### Q17. Does iterative scanning make HNSW exact?

No. It continues searching when needed within configured work/memory limits. Strict ordering controls the order of returned results; it does not guarantee the exact global top-k set. Our fixture observes five filtered results after enabling it and measures their overlap with the exact eligible set.

### Q18. Which pgvector operators should I know?

The executed example uses `<->` for L2, `<#>` for negative inner product and `<=>` for cosine distance. Explain why smaller distance is nearer and why ordinary dot product is the negative of `<#>`. Match the operator class to the query metric and verify index use with a plan.

### Q19. Why might PostgreSQL ignore my vector index?

The planner may prefer another path, the query may lack the recognizable distance ordering/limit, the operator class may not match, or filters may make another plan cheaper. Our rewritten descending similarity expression did not use the ANN index. Read the plan before changing settings; disabling sequential scans is only a diagnostic demonstration here.

### Q20. What is the difference between top-k and a threshold?

Top-k bounds the count of returned nearest candidates. A threshold rejects results whose score/distance does not meet a criterion. Top-k alone can return unrelated passages; a threshold can produce zero results. Our exact application query demonstrates both rules, but its numeric cutoff is not a semantic relevance recommendation.

### Q21. How do you implement multitenant vector search?

Derive the tenant from authenticated membership and apply its authorized search scope on every read/write/delete. pgvector can combine explicit SQL predicates with ordinary-role RLS; Pinecone can use an internal namespace registry and supported metadata filters. Recheck canonical current permissions before context. Never let a browser select arbitrary tenant scope using a public namespace field.

### Q22. Is the custom PostgreSQL tenant setting a complete security boundary?

No. The backend controls the credential and transaction-local setting; untrusted clients must not get arbitrary SQL access as that role. RLS helps contain backend query mistakes. Privileged/owner bypass, pooled connection state and the trust of tenant assignment still matter. Our tests use a nonprivileged application role and verify same-connection tenant reuse.

### Q23. What are a Pinecone index and namespace?

An index defines vector-search configuration such as dimension/metric for this bring-your-own-vector design. Namespaces scope record operations within it. The application derives the namespace from its trusted tenant/configuration registry. Our helper verifies body construction only; hosted isolation, freshness and performance require an actual authorized integration test.

### Q24. How do you make vector ingestion retries idempotent?

Use deterministic IDs for the intended source/chunk generation and verify the canonical expected revision before publication. A retry should reconcile the same generation instead of appending fresh IDs. Our SQL publisher atomically replaces chunks and proves a retry leaves one current row; the remote payload uses revision-specific IDs that need old-generation cleanup.

### Q25. What if the source changes while embeddings are being generated?

Encode outside a short database transaction, then lock/check the authoritative revision when publishing. Reject the old job if its revision or generation is obsolete. Our test advances the source to revision 2, hides old chunks and rejects a late revision 1 publisher. Include content/configuration guards when revision alone is insufficient.

### Q26. How do you delete a document reliably?

Make the canonical source ineligible, retain a tombstone/cleanup intent, remove every owned vector generation and invalidate dependent caches. Reject late ingestion jobs. A remote search result can lag canonical deletion, so validate IDs/revisions before using text. Include source objects and retention/backup policy in the wider deletion design.

### Q27. How would you migrate to another embedding model?

Create a separate compatible space/layout, backfill current sources, synchronize changes, evaluate relevance and approximation separately, shadow queries and switch routing deliberately. Keep an appropriate rollback window. Do not mix raw scores from unrelated models or claim old vectors become compatible merely because the new model has the same dimensions.

### Q28. How do you choose Pinecone versus pgvector?

State workload, consistency, filtering, recovery, cost and operational needs. pgvector can place relational and vector changes in one database transaction; a separate search service needs publication/reconciliation across services. Prototype representative queries and tenant filters. Our local pgvector fixture is not evidence that either product wins a hosted production benchmark.

### Q29. How would you prove retrieval improved?

Use labeled questions/passages with paraphrases, exact terms, distractors and unanswerable cases. Compare lexical, exact vector, ANN and combined retrieval using matching snapshots/scopes. Record relevance coverage, ranking, no-result behavior and latency under realistic load. ANN recall measures approximation loss; it cannot independently establish that users receive better evidence.

### Q30. What architecture would you describe for a notes assistant?

Authenticated API, canonical source/revision database, ingestion jobs, compatible encoder configuration, scoped vector plus lexical candidates, canonical ACL/revision acceptance, reranking/context budgeting and cited answer generation. Explain crash recovery after remote writes and deletion during ingestion. Be explicit: this module verifies database mechanics and request bodies, not a deployed model-backed assistant.

---

## 20. Practice tasks

1. Calculate cosine, dot and L2 for three vector pairs by hand, then compare Python and SQL with a float tolerance. Explain why unnormalized rankings differ.
2. Add a model/preprocessing generation to the fixture and demonstrate rejection of a same-dimensional incompatible query. Keep the original space queryable.
3. Extend the publisher with a content-hash guard. Create two jobs for the same document revision with different expected hashes and prove the stale one cannot overwrite the accepted generation.
4. Add a second application connection and a small pool. Alternate alpha/beta queries and inject a failed transaction; verify that tenant scope never leaks after reuse.
5. Run a parameter sweep for HNSW search effort. Save exact ground truth first, record recall/counts and timing, and identify which claims the tiny corpus cannot support.
6. Vary category selectivity and compare exact filtered search, iterative HNSW and a suitable partial index. Show plans for each rather than assuming an index was used.
7. Compare IVFFlat list/probe settings after loading representative data. Record build/query work and recall, then add a shifted data distribution and reevaluate.
8. Design a Pinecone adapter around the verified body builder. Use a test peer for transport errors and bounded retries; label those results separately from any later authorized hosted integration test.
9. Write an outbox/reconciliation state machine for a crash after remote upsert but before canonical publication. Include deletion during the retry window and cleanup of abandoned generations.
10. Build a labeled question set over your actual notes, including paraphrases, exact code terms, unanswerable questions and tenant distractors. Compare lexical, vector and combined retrieval before adding generation.

---

## 21. Revision checklist

- [ ] I can explain what an embedding represents and what its coordinates do not guarantee.
- [ ] I can distinguish vector dimensions from embedding-space compatibility.
- [ ] I can calculate cosine, dot product and L2 and explain normalization.
- [ ] I can distinguish distance, similarity and calibrated confidence.
- [ ] I can explain exact search, ANN recall, top-k and a relevance threshold.
- [ ] I can write an index-compatible pgvector nearest-neighbor query.
- [ ] I can explain the different roles of HNSW construction and query effort.
- [ ] I can explain IVFFlat lists/probes and the role of representative build data.
- [ ] I can diagnose ANN underfill with selective metadata predicates.
- [ ] I can derive tenant scope safely and explain the limits of the RLS fixture.
- [ ] I can design revision checks, deletion and a separate-service publication workflow.
- [ ] I can defend Pinecone versus pgvector using measured workload requirements.

---

## 22. Primary sources and verification artifacts

Version-sensitive sources were checked on **15 October 2026**. Recheck current provider behavior and installed extension limits before implementation.

| Topic | Primary reference |
| --- | --- |
| Encoder output/configuration | [OpenAI embeddings guide](https://developers.openai.com/api/docs/guides/embeddings), [creation reference](https://developers.openai.com/api/reference/python/resources/embeddings/methods/create) |
| Vector types/operators/indexes | [pgvector upstream](https://github.com/pgvector/pgvector), tagged v0.8.7 source identified by upstream release tags |
| Graph-search design | [Original HNSW paper](https://arxiv.org/abs/1603.09320) |
| PostgreSQL plans | [EXPLAIN](https://www.postgresql.org/docs/18/sql-explain.html), [reading plans](https://www.postgresql.org/docs/18/using-explain.html) |
| PostgreSQL access and scope | [Row security](https://www.postgresql.org/docs/18/ddl-rowsecurity.html), [SET LOCAL](https://www.postgresql.org/docs/18/sql-set.html) |
| Portable package provenance | [conda-forge recipe](https://github.com/conda-forge/pgvector-feedstock/blob/main/recipe/meta.yaml), pinned package metadata and hashes in the example |
| Pinecone concepts/tenancy | [Key terms](https://docs.pinecone.io/guides/core-concepts/key-terms), [multitenancy](https://docs.pinecone.io/guides/index-data/implement-multitenancy) |
| Pinecone record lifecycle | [Upsert](https://docs.pinecone.io/guides/index-data/upsert-data), [delete](https://docs.pinecone.io/guides/manage-data/delete-data), [freshness](https://docs.pinecone.io/guides/index-data/check-data-freshness) |
| Pinecone retrieval | [Metadata filters](https://docs.pinecone.io/guides/search/filter-by-metadata), [semantic search](https://docs.pinecone.io/guides/search/semantic-search) |

Local artifacts are under `examples/resume-skills/module-24-vectors/`: the exact sources embedded above, `verify.py`, owned-cluster/runtime helpers, dependency lock/check, `runtime-provenance.json`, `verification-results.json`, `cleanup-results.json`, and content/site validation reports. The verification report names every actual assertion and records both engine versions and the complete observed ANN results.

**Next: [M25: LangChain, LangGraph and LlamaIndex](/docs/resume-skills/langchain-langgraph-llamaindex).** That chapter will use these retrieval and lifecycle contracts to reason about framework abstractions and orchestration.
