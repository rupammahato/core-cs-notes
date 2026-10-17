"""Prepare output contracts and the canonical teaching-module catalogue."""
from pathlib import Path
import hashlib
import json
import re

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
drills = [
    ('D01', 'd01-async-prefix.mjs', 'Async function prefix', [1,2,4], ['before','inside','after',42], 'A JavaScript async function executes its synchronous prefix when called; returning a Promise does not offload CPU work.'),
    ('D02', 'd02-esm-microtasks.mjs', 'ES-module microtask context', [2,4], ['sync','promise','microtask','nextTick'], 'This is top-level ES-module execution on the recorded Node version. It is not a universal nextTick ordering rule for CommonJS or every callback context.'),
    ('D03', 'd03-promise-effects.mjs', 'Promise rejection and side effects', [2,9], {'error':'fail','effects':['first','third']}, 'Promise.all rejects on failure but does not roll back completed effects or automatically cancel other started work.'),
    ('D04', 'd04-async-map.mjs', 'Array of async results', [1,2], {'firstIsPromise':True,'resolved':[2,4]}, 'map preserves callback return values. An async callback returns a Promise; Promise.all collects resolved results in input order.'),
    ('D05', 'd05-shallow-copy.mjs', 'Nested alias after spread', [1,20,28], {'originalRole':'admin','sameNestedObject':True}, 'Object spread copies top-level properties, retaining the nested object reference. This is a memory-alias demonstration, not an authorization grant.'),
    ('D06', 'd06-json-boundary.mjs', 'Parsed JSON is still untrusted', [3,6,8], {'role':'admin','limitType':'string','limitPlusOne':'101'}, 'JSON parsing establishes syntax, not types, bounds or permission. The supplied role must not become authority; validate the limit before numeric use.'),
    ('D07', 'd07-mutable-default.py', 'Python shared default', [10], {'first':['a','b'],'second':['a','b'],'same':True}, 'The default list is created once for this function definition. Both calls return the same list; use a fresh per-call value when that is intended.'),
    ('D08', 'd08-offset.py', 'Timestamp meaning', [10,15,28], {'utc':'2026-10-16T04:30:00+00:00'}, 'The explicit source offset permits conversion to UTC. Attaching UTC to an unknown naive timestamp is a different operation and may change its intended meaning.'),
    ('D09', 'd09-decimal.py', 'Decimal-string arithmetic', [9,22,28], {'binary_float':'0.30000000000000004','decimal':'0.3'}, 'Binary floating-point cannot represent these decimal fractions exactly. Decimal-string input avoids that initial conversion; precision and rounding policy still matter.'),
    ('D10', 'd10-coroutine.py', 'Creating a Python coroutine', [10,11], [0,'ran'], 'Calling Python async def creates a coroutine without running its body. Awaiting it runs the body. Contrast this with the JavaScript async prefix in D01.'),
    ('D11', 'd11-sql-null-count.py', 'COUNT rows versus values', [13], {'rows':3,'nonnull':1,'sum':10}, 'COUNT(*) counts rows; COUNT(column) ignores null values. Do not mix these denominators in reporting.'),
    ('D12', 'd12-sql-null-unique.py', 'SQLite nullable uniqueness', [13,14,28], {'rows':3,'null_rows':2,'duplicate_rejected':True}, 'This SQLite UNIQUE column accepts multiple NULLs but rejects another nonnull x. Do not transfer this result to a MongoDB index or an explicit NULLS NOT DISTINCT policy.'),
    ('D13', 'd13-sql-rollback.py', 'Rollback after a dependent failure', [9,13,28], {'balance_cents':100,'events':1}, 'Both writes are inside one transaction. The duplicate event error rolls back the prior debit. This is local atomicity, not a full payment/external-provider workflow.'),
    ('D14', 'd14-async-filter.mjs', 'Async predicate in synchronous filter', [1,2,8], [1,2,3], 'filter tests each returned Promise object for truthiness; it does not await its boolean result. This pattern is especially unsafe for permission filtering.'),
]
manifest = [{'id':identity,'file':'drills/'+filename,'kind':'node-esm' if filename.endswith('.mjs') else 'sqlite' if 'sql-' in filename else 'python','title':title,'modules':modules,'expected':expected,'explanation':explanation} for identity,filename,title,modules,expected,explanation in drills]
(BASE / 'drills.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
mechanisms = [
    ('Trace browser, HTTP boundary, controller/service/data and response.', 'You cannot place a bug in the request path.'),
    ('Explain scope, values, references, closures and collection behavior.', 'Mutation, coercion or callback results surprise you.'),
    ('Trace Promises, awaiting, scheduling, rejection and bounded concurrency.', 'Async work is missing, leaked or falsely assumed rolled back.'),
    ('Separate static narrowing from runtime input validation.', 'A typed API trusts malformed external JSON.'),
    ('Explain Node execution, I/O, buffers/streams and process resources.', 'One CPU task or resource leak stalls unrelated traffic.'),
    ('Trace Express middleware order, service boundaries and error flow.', 'Validation/auth/error handling executes in the wrong order.'),
    ('Define method/status/representation, pagination and retry semantics.', 'A client and API disagree about success or replay safety.'),
    ('Trace credential transport, verification, expiry and revocation.', 'A login works but identity/session assumptions are unclear.'),
    ('Enforce resource/action/tenant policy at every relevant boundary.', 'Another tenant or a revoked user can access derived data.'),
    ('Protect payment/webhook effects with authentication and durable identity.', 'Duplicate or ambiguous events repeat business effects.'),
    ('Explain Python values, mutability, exceptions and coroutine execution.', 'Defaults, data types or async execution behave unexpectedly.'),
    ('Distinguish framework request handling from blocking dependency work.', 'An async endpoint blocks or loses request-lifetime work.'),
    ('Trace Django/DRF validation, ORM/query work and permissions.', 'Framework defaults are mistaken for complete application policy.'),
    ('Use access patterns, constraints, plans and transactions deliberately.', 'Queries, pool waits or read-modify-write operations fail under load.'),
    ('Choose document boundaries, indexes and atomic/transactional updates.', 'Partial updates, duplicate identity or multi-document rules fail.'),
    ('Explain source truth, cache freshness, job identity and publication.', 'A retry, stale worker or expiry creates incorrect derived state.'),
    ('Explain image/container, networks, volumes, configuration and readiness.', 'A container cannot reach dependencies or preserve data.'),
    ('Trace Linux process, reverse proxy, TLS, restart and drain behavior.', 'Deployment, trust or shutdown differs from local development.'),
    ('Separate IAM, service identity, networking, queue and storage boundaries.', 'A managed-service label hides an unresolved permission/failure rule.'),
    ('Link Git/CI gates, telemetry, performance evidence and rollback.', 'A test or benchmark claim lacks a reproducible boundary.'),
    ('Explain render snapshots, state, keys, effects and request races.', 'The UI shows stale results or loses identity/state.'),
    ('Separate Next.js runtime/render/cache boundaries and Tailwind styling.', 'Server/client code, hydration or cache scope leaks correctness.'),
    ('Bound model/tool work, usage, structured output and evaluation.', 'A model result is trusted as permission or an unbounded workflow.'),
    ('Trace source/chunk provenance, ingestion state and accepted evidence.', 'A citation or answer uses stale, missing or unauthorized content.'),
    ('Distinguish embedding/index configuration, scoped retrieval and recall.', 'A similarity score is mistaken for relevance or permission.'),
    ('Explain chain/workflow/agent state, checkpoints and replay.', 'A durable graph checkpoint repeats an external side effect.'),
    ('Anchor bounded graph queries and validate path/source scope.', 'Graph expansion crosses tenant or freshness boundaries.'),
    ('Defend placement, virtual nodes, health, overload and measured metrics.', 'Affinity, key balance and actual request load are conflated.'),
    ('Explain personal work and label reported, verified and proposed details.', 'A resume number or topology lacks original evidence.'),
]
catalogue = []
for path in (ROOT / 'Resume Skills Notes').glob('*.md'):
    match = re.search(r'part-\d+-module-(\d+)-(.+)\.md$', path.name)
    if not match or int(match[1]) > 28:
        continue
    module, slug = int(match[1]), match[2]
    text = path.read_text(encoding='utf-8')
    h1 = re.findall(r'^# (.+)$', text, re.M)
    mechanism, revisit = mechanisms[module]
    catalogue.append({'module':module,'file':path.name,'title':h1[1],'slug':slug,'route':'/docs/resume-skills/'+slug,'mechanism':mechanism,'revisit_when':revisit,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
catalogue.sort(key=lambda entry:entry['module'])
assert [entry['module'] for entry in catalogue] == list(range(29))
(BASE / 'module-catalogue.json').write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'drills':len(manifest),'teaching_modules':len(catalogue)}, indent=2))
