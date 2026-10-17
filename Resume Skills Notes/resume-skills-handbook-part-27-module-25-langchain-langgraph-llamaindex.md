# Resume Skills Placement Handbook — Part 27
# Module 25: LangChain, LangGraph and LlamaIndex

**Estimated time: 5–6 hours | Tier: 2 | Requires: M22 model/tool APIs, M23 RAG/ingestion, M24 embeddings/vector stores; M8 authorization and M15 jobs help**

---

## Why this module exists

An interviewer who sees these three framework names can ask what they contributed beyond an API call. You should be able to trace a question through retrieval, prompt construction, model output, tool execution and acceptance; explain what survives a restart; and identify which business rules remain ordinary application code.

This chapter extends the placement-note assistant from M23–M24. It runs the actual libraries with explicit local fixtures, then uses those observations to reason about more capable applications. The questions are selected resume-linked fundamentals and design follow-ups, not a measured ranking of interview frequency.

**Organizing principle: frameworks organize execution; the application still owns authority, evidence, budgets and durable business results.**

---

## 1. What these frameworks are and why use them

LangChain, LangGraph and LlamaIndex are application libraries, not language models. They do not gain factual knowledge merely because you import them. An encoder or language model still supplies learned behavior, a database retains source data, and your backend decides who can access or change it.

| Library | Main role in this chapter | Useful reason to adopt it |
| --- | --- | --- |
| LangChain | Model/message/tool interfaces and composable execution; an agent harness | Reuse integration contracts instead of rebuilding every adapter |
| LangGraph | Explicit state, nodes, routing, checkpoints and interruption/resumption | Make a multistep workflow inspectable and resumable |
| LlamaIndex | Documents/nodes, ingestion, retrieval and query-engine composition | Structure a data-backed question-answering pipeline |

These are emphasis areas, not exclusive product boundaries. LlamaIndex also has agent/workflow abstractions, and LangChain has retrieval integrations. LangChain's current `create_agent` harness uses LangGraph underneath. You can use LangGraph without a model or without LangChain's agent builder. [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview), [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview), [LlamaIndex concepts](https://developers.llamaindex.ai/python/framework/getting_started/concepts/)

### Where they fit in a backend

```text
Browser -> authenticated API -> application contracts
                                    |
                 +------------------+-------------------+
                 |                  |                   |
          model/tool adapters   stateful workflow   ingestion/retrieval
             LangChain            LangGraph           LlamaIndex
                 |                  |                   |
            model provider     checkpoint storage    source/vector store
                                    |
                            canonical business database
```

The same application may use one, two, all three, or none. Do not install every framework just because it appears on a resume. First explain the flow in plain functions; add a library where it solves a concrete integration, control-flow or data-management problem.

---

## 2. What was actually verified

Recorded **15 October 2026** on Windows:

| Runtime/package | Recorded version |
| --- | --- |
| Python | 3.12.10 |
| SQLite | 3.49.1 |
| langchain | 1.4.6 |
| langchain-core | 1.6.10 |
| langgraph | 1.2.15 |
| langgraph-checkpoint | 4.3.0 |
| langgraph-checkpoint-sqlite | 3.1.2 |
| llama-index-core | 0.14.25 |
| pydantic | 2.14.1 |

**89 actual local checks passed.** They execute LangChain composition/parsing/batch/async/stream/retry behavior and a real `create_agent` tool loop; LangGraph state/reducer/checkpoint/interrupt behavior; and LlamaIndex ingestion, filtered vector retrieval, synthesis, persistence/reload and deletion.

The graph is invoked by **21 short-lived worker processes** across the scenario suite. A new process resumes a file-backed checkpoint, and another recovers after an injected exception between canonical result commitment and graph completion. This is a process-restart mechanism check, not a power-loss, distributed-scheduler or production durability benchmark.

The model responses are **fake/scripted local responses**. The graph draft copies retrieved text. LlamaIndex uses a handwritten three-feature word-count encoder and an explicit `MockLLM` that returns `text text text`. **No learned model inference, provider API, hosted tracing, remote vector store or production quality benchmark was run.**

### Reproduce

From the repository root in PowerShell:

```powershell
python -m venv examples/resume-skills/module-25-frameworks/.venv
& examples/resume-skills/module-25-frameworks/.venv/Scripts/python.exe -m pip install -r examples/resume-skills/module-25-frameworks/requirements-lock.txt
& examples/resume-skills/module-25-frameworks/.venv/Scripts/python.exe -X utf8 examples/resume-skills/module-25-frameworks/verify.py
```

Installation needs network access. Execution disables hosted tracing and installs an external-socket audit guard in the parent and graph workers. The tested paths made zero external socket attempts. No credentials are read or required. Async internals may use local runtime mechanisms; the example starts no persistent HTTP/database listener.

Direct dependencies are pinned in `requirements.txt`; the complete environment is recorded in `requirements-lock.txt`. `pip check` found no dependency conflicts, which is not a vulnerability audit. The examples target the versions above. Old tutorials using other constructors/import paths are historical context, not the executed API contract.

Temporary application/checkpoint databases and persisted LlamaIndex files are placed in one owned temporary directory and removed in `finally`. Worker processes exit and database handles close. Docker and port 3000 remain stopped; the final site validation uses and closes its own ephemeral preview.

| Check group | Passing checks |
| --- | --- |
| langchain | 14 |
| retry_budget | 4 |
| agent | 10 |
| graph_state | 7 |
| persistence | 11 |
| approval | 8 |
| recovery | 7 |
| freshness | 5 |
| llamaindex | 18 |
| offline | 3 |
| cleanup | 2 |

---

## 3. Chain, workflow and agent: distinguish the control flow

A chain composes a sequence of operations: prepare input, format messages, call a model, parse its response. The developer determines the sequence. A workflow exposes control flow, branching, state and possibly pauses across multiple operations. An agent lets model output influence which available operation should run next, within an application-controlled loop.

```text
Chain:    retrieve -> prompt -> model -> parse
Workflow: retrieve -> evidence? -> draft -> review -> approved? -> commit
Agent:    model -> requested tools? -> authorized tool execution -> model -> ... -> stop
```

An agent is not necessarily more useful than a fixed workflow. If the product always searches notes and summarizes the results, a deterministic retrieval path may be easier to evaluate, bound and debug. Model-directed tool selection becomes useful when the next step genuinely depends on interpreting the task or intermediate evidence.

The official workflow/agent guide uses predetermined versus dynamic control flow as a useful distinction. Our graph deliberately uses deterministic routing and an extractive draft so the state mechanics are visible without model variability. [Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)

### Three different graphs

| Graph | What nodes/edges mean | Example |
| --- | --- | --- |
| LangGraph workflow | Execution steps and transitions | Review before committing a result |
| Knowledge/graph database | Entities and domain relationships | Person works at organization |
| HNSW index | Vector proximity/navigation links | Approximate nearest-neighbor search from M24 |

Using LangGraph does not create a Neo4j knowledge graph, and an HNSW graph does not represent an application approval workflow. M26 covers graph-backed data separately.

---

## 4. LangChain fundamentals: models, messages, prompts and runnables

A chat-model interface receives messages and returns a model message. Messages retain roles and may carry tool calls or metadata beyond plain text. A prompt template formats application inputs into the messages sent to that interface. A runnable is an executable component that can be composed with other components.

The common runnable operations used here are `invoke`, `batch`, `ainvoke`, `abatch` and `stream`. `invoke` handles one input; `batch` handles a collection; async methods integrate with asynchronous application code; streaming exposes incremental output. A common interface reduces adapter work but does not make all providers' capabilities, parameters or errors identical. [LangChain model interfaces](https://docs.langchain.com/oss/python/langchain/models)

### LCEL composition

The pipe operator in a runnable expression sends one stage's output to the next stage. It is function composition, not a shell pipe and not a model instruction:

```text
RunnableLambda(authorized preparation)
    | ChatPromptTemplate
    | FakeListChatModel
    | PydanticOutputParser
```

The stages must agree on shapes. Our preparation returns `question` and serialized `context`; the template creates messages; the fake model returns an AI message containing JSON; the parser produces an `Answer` object. A missing field or wrong response shape is an integration error to diagnose at the relevant stage.

Prompt templates also do not authorize access. Retrieved passages remain untrusted data even if a system instruction says to use only evidence. A passage containing “ignore your instructions” is not a grant of tool privileges. Keep security decisions in trusted code.

---

## 5. Executed application contracts and LangChain pipeline

The shared contracts make tenant scope, output shape and approval identity explicit. `Principal` is constructed by the fixture; in a real API it must come from verified authentication and current membership, not from an arbitrary client JSON object.

### `domain.py`

```python
"""Small application contracts shared by the actual framework examples."""
from dataclasses import dataclass
import hashlib
import json
from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class Principal:
    tenant: str
    user: str
    can_read: bool = True


NOTES = [
    {'id': 'alpha-session', 'tenant': 'alpha', 'revision': 1,
     'text': 'Session records keep login state on the server. A cookie carries a session identifier.'},
    {'id': 'alpha-index', 'tenant': 'alpha', 'revision': 1,
     'text': 'An index helps locate rows. Index maintenance adds work to writes.'},
    {'id': 'beta-session', 'tenant': 'beta', 'revision': 1,
     'text': 'Session records for beta contain private deployment procedures.'},
]


def retrieve(principal, topic, limit=2):
    if not principal.can_read or principal.tenant not in ('alpha', 'beta'):
        raise PermissionError('Read permission denied')
    if not isinstance(topic, str) or not topic.strip() or len(topic) > 100:
        raise ValueError('Bad topic')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 3:
        raise ValueError('Bad result limit')
    terms = set(topic.lower().split())
    return [dict(note) for note in NOTES if note['tenant'] == principal.tenant
            and terms.intersection(note['text'].lower().split())][:limit]


class Answer(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    answer: str = Field(min_length=1)
    citations: list[str] = Field(min_length=1)


class Decision(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    approved: bool
    draft_hash: str = Field(pattern=r'^[0-9a-f]{64}$')


def draft_hash(job_id, draft, evidence):
    payload = {'job': job_id, 'draft': draft,
               'sources': [(row['id'], row['revision']) for row in evidence]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def accept_citations(answer, evidence):
    allowed = {note['id'] for note in evidence}
    if not set(answer.citations).issubset(allowed):
        raise ValueError('Citation outside supplied evidence')
    return answer
```

The baseline retriever is a transparent lexical filter over three synthetic notes. `Answer` uses strict validation and rejects extra fields. Its citation check verifies that the cited IDs belong to supplied evidence. It does **not** prove that the answer is entailed by the passage; a schema-valid invented statement can still cite a real ID.

`draft_hash` binds the job, draft text and evidence revisions. It is an integrity comparison, not a signature or authorization token. A caller must already be allowed to review the job. The hash assumes source revisions identify the underlying content; the commit path also compares current text.

### `langchain_demo.py`

```python
"""Actual LCEL and create_agent; fake/scripted responses, no provider inference."""
import json
from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from domain import Answer, Principal, accept_citations, retrieve


class LocalTrace(BaseCallbackHandler):
    def __init__(self):
        self.events = []

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.events.append({'event': 'model_start', 'message_count': len(messages[0])})

    def on_llm_end(self, response, **kwargs):
        self.events.append({'event': 'model_end'})


def make_chain(principal, response):
    def prepare(inputs):
        evidence = retrieve(principal, inputs['question'])
        if not evidence:
            raise LookupError('No eligible evidence')
        return {'question': inputs['question'], 'context': json.dumps(evidence)}

    parser = PydanticOutputParser(pydantic_object=Answer)
    prompt = ChatPromptTemplate.from_messages([
        ('system', 'Use only the supplied evidence. Return answer and citations as JSON.'),
        ('human', 'Question: {question}\nEvidence: {context}'),
    ])
    return (RunnableLambda(prepare).with_config(run_name='authorized_retrieval')
            | prompt | FakeListChatModel(responses=[response]) | parser)


def checked_chain_answer(chain, principal, question, config=None):
    answer = chain.invoke({'question': question}, config=config)
    return accept_citations(answer, retrieve(principal, question))


def stream_fixture():
    return (FakeListChatModel(responses=['local-stream']) | StrOutputParser())


@tool
def read_note(topic: str, runtime: ToolRuntime[Principal], limit: int = 2) -> str:
    """Read current notes matching a topic for the authenticated user."""
    return json.dumps(retrieve(runtime.context, topic, limit))


class ScriptedToolModel(BaseChatModel):
    """Return predetermined tool calls; bind_tools does not contact a provider."""
    mode: str = 'normal'

    @property
    def _llm_type(self):
        return 'placement-scripted-tool-model'

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if self.mode == 'loop' or not any(isinstance(m, ToolMessage) for m in messages):
            args = {'topic': 'session', 'limit': 2}
            name = 'read_note'
            if self.mode == 'bad_limit':
                args['limit'] = 99
            if self.mode == 'unknown':
                name = 'not_registered'
            message = AIMessage(content='', tool_calls=[{
                'name': name, 'args': args, 'id': 'call-' + str(len(messages)), 'type': 'tool_call',
            }])
        else:
            message = AIMessage(content='Scripted final reply: ' + messages[-1].content)
        return ChatResult(generations=[ChatGeneration(message=message)])


def make_agent(mode='normal'):
    return create_agent(model=ScriptedToolModel(mode=mode), tools=[read_note], context_schema=Principal,
                        system_prompt='Use the read-only note tool; this is a scripted local fixture.')
```

`make_chain` closes over trusted principal context instead of accepting a tenant chosen by the model. If no eligible evidence exists, the preparation stage raises before the fake model runs. The verifier checks both the exception and the absence of model callback events.

The script also includes the agent's explicitly handwritten model implementation. Its `bind_tools` method returns itself; it does not serialize a real provider request or exercise learned tool selection. This adapter lets the actual framework loop consume a predetermined `AIMessage`, run a real tool and deliver its result back to a second model turn.

### Actual composition output

```json
{
  "answer": {
    "answer": "Session records keep login state on the server.",
    "citations": [
      "alpha-session"
    ]
  },
  "callbacks": [
    {
      "event": "model_start",
      "message_count": 2
    },
    {
      "event": "model_end"
    }
  ],
  "batch_outputs": 2,
  "async_outputs": 2,
  "stream_joined": "local-stream",
  "transient_attempts": 2,
  "denied_attempts": 1
}
```

Callbacks recorded two formatted messages, then model completion. Batch and async execution returned typed answers. The stream joined to the fixture string. These observations verify library plumbing, not factual answer quality or provider latency.

---

## 6. Structured output, parsing and acceptance

Structured output helps an application consume a predictable shape. There are different mechanisms: a provider can constrain an output format, a tool schema can structure a call, and a local parser can validate the completed response. Current LangChain agents expose structured-output strategies; our executed chain uses **local Pydantic parsing** of fake model text. [LangChain structured output](https://docs.langchain.com/oss/python/langchain/structured-output)

Do not say the provider enforced the schema in this example. The parser rejects malformed JSON and an extra `admin` field after generation. The application separately rejects a schema-valid citation to beta's passage when alpha supplied the evidence.

```text
Bytes/text -> parseable JSON -> declared schema -> authorized references -> task correctness
```

Each arrow adds a different check. A JSON parser does not establish permission. A schema does not establish truth. A valid citation ID does not establish that the cited passage supports the answer. Answer acceptance can include source freshness, semantic/claim evaluation and domain rules after structural parsing.

### What to do on invalid output

Return a typed application error or use a deliberately bounded repair attempt. Record why validation failed and which stage produced the invalid value. Do not silently coerce a string `"yes"` into an approval boolean when that field controls an effect. Our `Decision` model requires an actual boolean and binds it to a draft hash.

A repair prompt is another model call with latency/cost and its own failure possibilities. Re-running a whole chain may also repeat earlier retrieval or side effects. Keep the retry scope small and preserve the original trusted context.

---

## 7. Tools and the actual agent loop

A tool is an application function exposed with a name, description and input contract. A model can propose a tool name and arguments. The application/framework executes an allowed implementation and returns an observation correlated with the tool-call ID.

In our tool, the model-visible inputs are `topic` and `limit`. `ToolRuntime` provides invocation context without exposing it as a model-controlled argument. The tool's implementation still checks permission and result bounds; hiding a parameter is not authorization by itself. [LangChain tools and runtime context](https://docs.langchain.com/oss/python/langchain/tools)

### Executed sequence

1. The user message enters `create_agent`.
2. `ScriptedToolModel` requests `read_note(topic="session", limit=2)`.
3. The framework injects the trusted `Principal` into the tool runtime.
4. `retrieve` checks access and selects only that tenant's synthetic notes.
5. A `ToolMessage` carries the result and matching call ID.
6. The scripted second turn returns a final response without another tool call.

### Actual agent observations

```json
{
  "tool_schema_properties": [
    "limit",
    "topic"
  ],
  "message_types": [
    "human",
    "ai",
    "tool",
    "ai"
  ],
  "tool_calls": 1,
  "tool_result": [
    {
      "id": "alpha-session",
      "tenant": "alpha",
      "revision": 1,
      "text": "Session records keep login state on the server. A cookie carries a session identifier."
    }
  ],
  "final_reply": "Scripted final reply: [{\"id\": \"alpha-session\", \"tenant\": \"alpha\", \"revision\": 1, \"text\": \"Session records keep login state on the server. A cookie carries a session identifier.\"}]",
  "loop_limit_error": "GraphRecursionError"
}
```

The same tool returns beta evidence only when invoked with beta's trusted context. A missing read permission and an oversized limit raise errors. A request for an unregistered tool becomes an error observation in the tested harness. Error-handling defaults can differ across versions/configuration, so verify the intended policy instead of assuming every exception is automatically retried or shown to the model.

### Choosing tool scope

Expose a narrow read operation such as `read_note(topic, limit)`, not arbitrary SQL or unrestricted filesystem access. The backend chooses the tenant, permitted source set and enforced result cap. For a tool that changes data, bind the effect to authenticated authority, validated arguments and a stable operation ID. Model intent is not enough to commit a payment, deletion or invitation.

Our agent is read-only. The workflow's only effect is a local result row in a temporary database. No message, payment, account change or external publication occurs in this module.

---

## 8. LangGraph fundamentals: state, nodes, edges and compilation

State is the data carried through the workflow. A node reads state, performs an operation and returns updates. Edges determine which node runs next. Conditional edges choose a route from the current result. Compilation creates an executable graph from the declared structure.

The executed graph has four nodes: retrieve, draft, review and commit. No evidence ends the run; a negative review ends the run; a positive review proceeds to commitment after current source/ownership checks.

```text
START -> retrieve -- no evidence ------------------------------> END
             |
             +-- evidence -> draft -> review -- rejected ------> END
                                        |
                                        +-- approved -> commit -> END
```

Keep business state explicit. Useful fields include job ID, source IDs/revisions, draft, draft hash, status and accepted result ID. A database connection, API client or authentication secret belongs in runtime dependencies, not in a persisted state dictionary. Our `RunContext` carries the current principal and repository handle separately from checkpointed `State`.

A `TypedDict` describes state shape for code/tools; it is not automatically a complete runtime validation boundary. Validate public input, tool arguments and approval payloads explicitly, as the fixture does with `Decision` and repository authorization.

---

## 9. Reducers, parallel updates and message identity

A reducer controls how a field's existing value and a node's update combine. Without a custom reducer, an ordinary field uses replacement behavior. An additive list reducer appends/combines updates; returning an empty list therefore does not clear accumulated values. These mechanics are described in the Graph API and executed by the fixture. [LangGraph state and reducers](https://docs.langchain.com/oss/python/langgraph/graph-api)

Two parallel nodes updating the same ordinary scalar can produce an invalid concurrent update. Adding a reducer makes the conflict rule explicit, but the reducer must match the business meaning. Summing counts, merging unique IDs and replacing a status are different operations.

The tests run a small fan-out/fan-in graph. Parallel event contributions are combined with `operator.add`, and a final empty event update preserves them. We sort the event list for the observation instead of claiming a meaningful order between independent parallel branches.

Messages need identity-aware behavior too. The tested `add_messages` reducer replaces a message with a matching ID rather than appending another copy. Blind list concatenation would duplicate an edited message. Decide whether an event is an append-only fact, a replaceable message or a canonical business record.

### Actual state observations

```json
{
  "parallel_events": [
    "a",
    "b"
  ],
  "final_status": "done",
  "empty_update_cleared_events": false,
  "message_replacement_count": 1,
  "fresh_memory_snapshot": {}
}
```

An in-memory saver can inspect state while that saver exists. A newly constructed in-memory saver has no previous snapshots. This distinguishes same-object continuity from restart durability.

---

## 10. Checkpoints, threads, stores and canonical records

A checkpointer retains execution-state snapshots associated with a thread. A cross-thread store retains application-defined data such as preferences. These are different persistence roles. An in-memory saver loses state when its process/object lifetime ends; the fixture uses file-backed `SqliteSaver` for restart continuity. [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)

| Data | Authority and purpose | Fixture location |
| --- | --- | --- |
| Graph checkpoint | Where execution can continue; state needed by pending nodes | `checkpoints.sqlite` |
| Canonical job/source data | Who owns the job; current source content/revision and revocation | `application.sqlite` |
| Committed result | Accepted local application result with an idempotency key | `application.sqlite` |
| Runtime context | Current principal and open repository handle | Fresh worker memory |

Do not treat a checkpoint's old permission field as current authority. A user can lose access while a graph is paused. Our worker authorizes against the canonical job table **before it reads the saved graph**, then supplies fresh context to resumed execution.

`thread_id` is a lookup/routing identifier, not an authentication credential. Namespacing it by tenant helps organize data, but anyone allowed to read arbitrary threads could still expose private state. A deployed API needs ownership checks for start, inspect, stream, resume, cancel and delete operations.

Checkpoints can contain private passages and prompts. Apply access controls, retention and appropriate storage protection. Keeping every checkpoint forever can duplicate deleted source material even after a vector-store cleanup. Application deletion must address both source-derived data and retained workflow history.

---

## 11. Executed workflow and process-restart boundary

The repository below is deliberately separate from graph persistence. It supplies canonical source/ownership checks and one idempotent local result operation.

### `repository.py`

```python
"""Canonical ownership and an idempotent local result table, separate from checkpoints."""
import sqlite3
from domain import NOTES


class Repository:
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    def setup(self):
        self.conn.executescript('''
            CREATE TABLE jobs(job_id TEXT PRIMARY KEY, tenant TEXT NOT NULL, user TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE sources(id TEXT PRIMARY KEY, tenant TEXT NOT NULL, revision INTEGER NOT NULL, text TEXT NOT NULL, deleted INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE attempts(job_id TEXT NOT NULL, node TEXT NOT NULL);
            CREATE TABLE results(job_id TEXT PRIMARY KEY, draft_hash TEXT NOT NULL, answer TEXT NOT NULL);
        ''')
        self.conn.executemany('INSERT INTO sources(id,tenant,revision,text) VALUES (:id,:tenant,:revision,:text)', NOTES)
        self.conn.commit()

    def create_job(self, job_id, principal):
        with self.conn:
            self.conn.execute('INSERT INTO jobs(job_id,tenant,user) VALUES (?,?,?)', (job_id, principal.tenant, principal.user))

    def authorize(self, job_id, principal):
        row = self.conn.execute('SELECT * FROM jobs WHERE job_id=?', (job_id,)).fetchone()
        if not row or row['revoked'] or not principal.can_read or (row['tenant'], row['user']) != (principal.tenant, principal.user):
            raise PermissionError('Job unavailable')
        return principal.tenant + ':' + job_id

    def retrieve(self, job_id, principal, question):
        self.authorize(job_id, principal)
        terms = set(question.lower().split())
        rows = self.conn.execute('SELECT id,tenant,revision,text FROM sources WHERE tenant=? AND deleted=0 ORDER BY id', (principal.tenant,))
        return [dict(row) for row in rows if terms.intersection(row['text'].lower().split())][:2]

    def attempt(self, job_id, node):
        with self.conn:
            self.conn.execute('INSERT INTO attempts VALUES (?,?)', (job_id, node))

    def current(self, principal, evidence):
        for note in evidence:
            row = self.conn.execute('SELECT tenant,revision,text,deleted FROM sources WHERE id=?', (note['id'],)).fetchone()
            if not row or row['deleted'] or row['tenant'] != principal.tenant or row['revision'] != note['revision'] or row['text'] != note['text']:
                return False
        return bool(evidence)

    def commit_result(self, job_id, principal, evidence, expected_hash, answer):
        # Validate source state and insert under one SQLite write transaction.
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            self.authorize(job_id, principal)
            if not self.current(principal, evidence):
                self.conn.rollback()
                return False
            self.conn.execute('INSERT INTO results VALUES (?,?,?) ON CONFLICT(job_id) DO NOTHING', (job_id, expected_hash, answer))
            row = self.conn.execute('SELECT draft_hash,answer FROM results WHERE job_id=?', (job_id,)).fetchone()
            if tuple(row) != (expected_hash, answer):
                raise ValueError('Idempotency key reused for a different result')
            self.conn.commit()
            return True
        except BaseException:
            self.conn.rollback()
            raise
```

`commit_result` rechecks job ownership and source revisions/text within one SQLite write transaction. A stable job ID prevents duplicate local result rows, while a conflicting hash/answer under the same key is rejected. This proves a narrow local invariant; it does not establish exactly-once execution against a remote service.

### `graph_demo.py`

```python
"""Actual checkpointed graph with review, revalidation, and a replay-safe local write."""
from dataclasses import dataclass
from operator import add
from typing import Annotated, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langgraph.types import interrupt
from domain import Decision, Principal, draft_hash
from repository import Repository


class State(TypedDict, total=False):
    job_id: str
    question: str
    evidence: list[dict]
    draft: str
    draft_hash: str
    approved: bool
    status: str
    events: Annotated[list[str], add]


@dataclass
class RunContext:
    principal: Principal
    repo: Repository
    fail_after_commit: bool = False


def build_graph(checkpointer):
    def retrieve_node(state: State, runtime: Runtime[RunContext]):
        ctx = runtime.context
        evidence = ctx.repo.retrieve(state['job_id'], ctx.principal, state['question'])
        return {'evidence': evidence, 'status': 'retrieved' if evidence else 'no_evidence', 'events': ['retrieve']}

    def draft_node(state: State):
        # Extractive, deterministic draft; no language model is called.
        draft = state['evidence'][0]['text']
        return {'draft': draft, 'draft_hash': draft_hash(state['job_id'], draft, state['evidence']),
                'status': 'awaiting_review', 'events': ['draft']}

    def review_node(state: State, runtime: Runtime[RunContext]):
        ctx = runtime.context
        ctx.repo.authorize(state['job_id'], ctx.principal)
        # Instrumentation deliberately before interrupt: this runs again on resume.
        ctx.repo.attempt(state['job_id'], 'review')
        value = interrupt({'job_id': state['job_id'], 'draft': state['draft'], 'draft_hash': state['draft_hash']})
        decision = Decision.model_validate(value)
        if decision.draft_hash != state['draft_hash']:
            raise ValueError('Approval belongs to another draft')
        return {'approved': decision.approved, 'status': 'approved' if decision.approved else 'rejected', 'events': ['review']}

    def commit_node(state: State, runtime: Runtime[RunContext]):
        ctx = runtime.context
        ctx.repo.attempt(state['job_id'], 'commit')
        accepted = ctx.repo.commit_result(state['job_id'], ctx.principal, state['evidence'], state['draft_hash'], state['draft'])
        if accepted and ctx.fail_after_commit:
            raise RuntimeError('Injected failure after canonical commit, before graph checkpoint')
        return {'status': 'committed' if accepted else 'stale_source', 'events': ['commit']}

    builder = StateGraph(State, context_schema=RunContext)
    builder.add_node('retrieve', retrieve_node)
    builder.add_node('draft', draft_node)
    builder.add_node('review', review_node)
    builder.add_node('commit', commit_node)
    builder.add_edge(START, 'retrieve')
    builder.add_conditional_edges('retrieve', lambda state: 'draft' if state['evidence'] else END)
    builder.add_edge('draft', 'review')
    builder.add_conditional_edges('review', lambda state: 'commit' if state['approved'] else END)
    builder.add_edge('commit', END)
    return builder.compile(checkpointer=checkpointer)
```

The draft is extractive, not generated. The pre-interrupt attempt entry is deliberate instrumentation to expose replay; it would be a poor place for an irreversible business effect. The canonical write itself is designed to tolerate a node retry.

### `graph_worker.py`

```python
"""A new OS process per action proves file checkpoint continuity across restarts."""
import json
import os
from pathlib import Path
import sys
from offline import guard_external_connections
network_attempts = guard_external_connections()
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from domain import Principal
from graph_demo import RunContext, build_graph
from repository import Repository


def run(request):
    folder = Path(request['folder']).resolve()
    repo = Repository(folder / 'application.sqlite')
    principal = Principal(**request['principal'])
    try:
        # Authenticate/authorize before reading a saved graph snapshot.
        thread = repo.authorize(request['job_id'], principal)
        config = {'configurable': {'thread_id': thread}, 'recursion_limit': 12}
        with SqliteSaver.from_conn_string(str(folder / 'checkpoints.sqlite')) as saver:
            graph = build_graph(saver)
            snapshot = graph.get_state(config)
            mode = request['mode']
            if mode == 'start':
                if snapshot.values:
                    raise ValueError('Job already started')
                value = {'job_id': request['job_id'], 'question': request['question'], 'events': []}
            elif mode == 'resume':
                if not any(task.interrupts for task in snapshot.tasks):
                    raise ValueError('No pending review')
                value = Command(resume=request['decision'])
            elif mode == 'recover':
                if 'commit' not in snapshot.next:
                    raise ValueError('No pending commit recovery')
                value = None
            else:
                raise ValueError('Unknown action')
            graph.invoke(value, config, context=RunContext(principal, repo, request.get('fail_after_commit', False)))
            snapshot = graph.get_state(config)
            interrupts = [item.value for task in snapshot.tasks for item in task.interrupts]
            return {'ok': True, 'pid': os.getpid(), 'state': snapshot.values, 'next': list(snapshot.next),
                    'interrupts': interrupts, 'checkpoint_id': snapshot.config['configurable'].get('checkpoint_id')}
    finally:
        repo.close()


if __name__ == '__main__':
    try:
        result = run(json.load(sys.stdin))
    except Exception as exc:
        result = {'ok': False, 'pid': os.getpid(), 'error': type(exc).__name__, 'detail': str(exc)}
    result['external_network_attempts'] = len(network_attempts)
    print(json.dumps(result))
```

Each verifier action launches a fresh Python process with a synthetic trusted principal. The CLI is a test harness, not an authenticated web service. A deployed API must derive that principal from verified credentials and must not expose failure-injection flags to clients.

Start refuses an already-started job. Resume requires a pending interrupt. Recovery requires a pending commit node. These entry checks help prevent an old approval payload from being treated as a new start or a completed run being resumed again.

### Actual restart observations

```json
{
  "start_status": "awaiting_review",
  "start_next": [
    "review"
  ],
  "start_events": [
    "retrieve",
    "draft"
  ],
  "resume_status": "committed",
  "resume_events": [
    "retrieve",
    "draft",
    "review",
    "commit"
  ],
  "different_processes": true,
  "review_attempts": 2,
  "result_rows": 1,
  "checkpoint_changed": true
}
```

The review node was entered twice across pause/resume, but its completed update appears once in graph event state. The new process's checkpoint ID changed, it reached `END`, and one canonical result row was present.

---

## 12. Interrupts, approval binding and freshness on resume

An interrupt pauses execution and exposes a payload for a later resume value. In a graph with a checkpointer, resumption uses the same authorized thread and a `Command(resume=...)`. The interrupted node is re-entered, so code preceding the interrupt can execute again. Our attempt counter observes exactly that behavior. [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)

Keep interrupt payloads serializable and stable. Do not place a payment, email or destructive operation before an interrupt while assuming it runs only once. Do not casually reorder a sequence of interrupts inside a node whose persisted resumes still exist. Prefer small nodes with clear contracts and a versioned migration policy for long-running jobs.

### What approval means in this fixture

The canonical owner is allowed to review its own synthetic job. The decision must contain a strict boolean and the hash of the pending draft/evidence identity. A negative decision ends the workflow without commitment. A different hash is rejected. Production approval may require a separate reviewer role and a policy around changed drafts or multiple approvers.

The hash is not secret and does not replace authorization. A cross-tenant caller and another user in alpha are denied before checkpoint access. A revoked job is denied on resume. An old completed-job approval is rejected at the worker entry boundary.

### Actual approval and freshness observations

```json
{
  "cross_tenant_error": "PermissionError",
  "wrong_user_error": "PermissionError",
  "negative_decision_status": "rejected",
  "wrong_hash_error": "ValueError",
  "wrong_boolean_error": "ValidationError",
  "revoked_error": "PermissionError",
  "stale_revision_status": "stale_source",
  "deleted_source_status": "stale_source"
}
```

A positive review is necessary for this workflow, but it is not sufficient. If the source changes or is deleted while the job waits, the commit transaction returns `stale_source` and stores no result. The application can ask for a new draft/review under a new generation; it should not quietly publish an obsolete approved answer.

These checks establish the local acceptance boundary. They do not promise instantaneous revocation of content already viewed by a reviewer or streamed before a later change. Define the product's revocation/freshness promise explicitly.

---

## 13. Durable effects, retries and the checkpoint gap

Consider a node that writes an application result and then finishes. The write can succeed before the graph records successful node completion. If a failure occurs in that gap, recovery can execute the node again.

```text
Node starts -> canonical result committed -> injected exception
                                         X graph completion not recorded
Fresh worker -> pending node retried -> same operation ID -> existing result accepted
```

The verifier injects a `RuntimeError` after the SQLite result transaction commits. A later process invokes the pending node with `None` as continuation input and fresh runtime context. The commit attempt count becomes two, while the result table contains one matching row.

### Actual recovery observations

```json
{
  "first_resume_error": "RuntimeError",
  "result_survived_before_checkpoint": true,
  "recovered_status": "committed",
  "commit_attempts": 2,
  "canonical_result_rows": 1,
  "completed_commit_updates": 1,
  "external_service_claim": false
}
```

Checkpointing did not make the node execute once. The canonical operation made its local effect replay-safe. A different payload under the same job key raises an error instead of overwriting a committed answer.

### Remote effects require another contract

For a payment, notification or external mutation, use the destination's supported idempotency mechanism and retain a stable operation ID, intent and reconciliation state. An outbox can atomically record the intent with canonical database changes, while a worker dispatches it separately. If the remote service accepts the operation but its response is lost, reconcile the original operation rather than inventing a new one.

Our local SQLite transaction is not evidence of a distributed atomic commit, remote deduplication or exactly-once external delivery. The system-design reasoning extends M9/M15; hosted behavior needs its own authorized integration checks.

---

## 14. LlamaIndex: documents, nodes, indexes and query engines

A `Document` represents an ingested source with text and metadata. Parsing creates `Node` objects used as retrieval units, with relationships back to their source. An index organizes the retrieval representation; a retriever returns candidate nodes; a query engine combines retrieval, optional postprocessing and response synthesis. [LlamaIndex documents](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_documents/), [query stages](https://developers.llamaindex.ai/python/framework/understanding/rag/querying/)

```text
Documents -> transformations -> Nodes -> embeddings/index
Question -> retriever -> filtered/reranked nodes -> synthesis -> response + source nodes
```

The application still decides source identity, tenant ownership, content revision, chunking policy and embedding-space compatibility from M23/M24. Importing a loader does not validate whether an uploaded file is current, safe or permitted for this user.

### IngestionPipeline

The pipeline applies declared transformations and provides reusable ingestion structure; its documented cache/storage capabilities can help avoid repeated work. A cache hit is not evidence of current permission or correct source publication. Separate deterministic transformation caching from the canonical revision checks that decide whether a generation may become visible. [LlamaIndex ingestion pipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/)

The executed pipeline uses a real `SentenceSplitter` followed by a custom `BaseEmbedding`. It does not run the M23 PDF parser again or publish a hosted ingestion job. Its synthetic source IDs and ordinals produce stable node IDs useful for the small persistence/deletion tests.

### VectorStoreIndex

The index uses LlamaIndex's local vector-store machinery and cosine retrieval over supplied embeddings. It is not Pinecone or pgvector. Metadata filtering in this local store is verified directly; a remote integration may support different filter operators or consistency behavior. [Using VectorStoreIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/)

The index is derived search state. Keep canonical source content/manifests so it can be rebuilt and current access can be checked independently.

---

## 15. Executed LlamaIndex ingestion, retrieval and synthesis

### `llama_demo.py`

```python
"""Actual LlamaIndex pipeline/index/query engine with a handwritten feature encoder."""
import re
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from domain import NOTES


class FeatureEmbedding(BaseEmbedding):
    """Three word-count features; not a trained semantic embedding model."""
    model_name: str = 'handwritten-session-index-deployment-v1'

    def _encode(self, text):
        words = re.findall(r'[a-z]+', text.lower())
        return [float(words.count(term)) + 0.01 for term in ('session', 'index', 'deployment')]

    def _get_query_embedding(self, query):
        return self._encode(query)

    async def _aget_query_embedding(self, query):
        return self._encode(query)

    def _get_text_embedding(self, text):
        return self._encode(text)


def splitter():
    # Words are the fixture's counting units; no BPE/NLTK/provider tokenizer.
    return SentenceSplitter(chunk_size=64, chunk_overlap=8, tokenizer=str.split,
                            chunking_tokenizer_fn=lambda text: [text],
                            id_func=lambda ordinal, doc: f'{doc.doc_id}:c{ordinal}')


def build_index():
    Settings.tokenizer = str.split
    encoder = FeatureEmbedding()
    documents = [Document(id_=note['id'], text=note['text'],
                          metadata={'tenant': note['tenant'], 'revision': note['revision']},
                          excluded_embed_metadata_keys=['tenant', 'revision'],
                          excluded_llm_metadata_keys=['tenant', 'revision']) for note in NOTES]
    pipeline = IngestionPipeline(transformations=[splitter(), encoder])
    nodes = pipeline.run(documents=documents, show_progress=False)
    index = VectorStoreIndex(nodes, embed_model=encoder, show_progress=False)
    return documents, nodes, index, encoder


def retriever_for(index, principal, top_k=2):
    if not principal.can_read or principal.tenant not in ('alpha', 'beta'):
        raise PermissionError('Read permission denied')
    return index.as_retriever(similarity_top_k=top_k, filters=MetadataFilters(filters=[
        MetadataFilter(key='tenant', value=principal.tenant), MetadataFilter(key='revision', value=1),
    ]))


def query_engine(index, principal):
    return RetrieverQueryEngine.from_args(retriever_for(index, principal), llm=MockLLM(max_tokens=3),
        response_mode='simple_summarize', node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.8)])


def restore_index(folder, encoder):
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=str(folder)), embed_model=encoder)
```

`FeatureEmbedding` counts the words `session`, `index` and `deployment`, adding a small constant so vectors are nonzero. That is an intentionally transparent encoder, not a trained semantic model. It can make “session” rank above “index,” but it does not understand a paraphrase such as “remember my login.”

The splitter uses whitespace-separated **word counts** and an explicit splitting callback. Its `chunk_size=64` is therefore a fixture word budget, not 64 BPE tokens for a real model. Supplying those callbacks also avoids an implicit tokenizer vocabulary/NLTK download during verification.

Tenant/revision metadata remains available for filtering but is excluded from embedding and LLM text. That exclusion controls representation/prompt content; it does not remove metadata from storage or turn it into confidential data hidden from the backend.

`Settings.tokenizer` is a process-wide setting used here only to make the isolated fixture's word counting explicit. Production applications should prefer component-scoped configuration where available and avoid mutating global model/tenant configuration per request.

### Actual LlamaIndex output

```json
{
  "node_ids": [
    "alpha-session:c0",
    "alpha-index:c0",
    "beta-session:c0"
  ],
  "feature_vectors": [
    [
      2.01,
      0.01,
      0.01
    ],
    [
      0.01,
      2.01,
      0.01
    ],
    [
      1.01,
      0.01,
      1.01
    ]
  ],
  "alpha_results": [
    {
      "id": "alpha-session:c0",
      "score": 0.999976
    },
    {
      "id": "alpha-index:c0",
      "score": 0.014924
    }
  ],
  "beta_results": [
    "beta-session:c0"
  ],
  "mock_answer": "text text text",
  "query_source_ids": [
    "alpha-session"
  ],
  "restored_result_ids": [
    "alpha-session:c0",
    "alpha-index:c0"
  ],
  "after_delete_ids": [
    "alpha-index:c0"
  ],
  "long_chunk_word_counts": [
    64,
    64,
    38
  ],
  "embedding_scope": "Handwritten three-feature word counts; no learned model"
}
```

The query engine's similarity postprocessor keeps only the matching alpha source. The explicit `MockLLM(max_tokens=3)` returns three repeated words. The presence of `source_nodes` demonstrates response provenance plumbing; it does not establish that this mock reply is a useful answer.

### Persistence and deletion

The example persists storage files, reloads the index with the same explicit encoder, verifies IDs/scores, and deletes the alpha session source using `delete_ref_doc`. Beta remains queryable. These are local storage semantics, not a remote-store backup, distributed publication or deletion-retention guarantee. [LlamaIndex persistence](https://developers.llamaindex.ai/python/framework/module_guides/storing/save_load/)

The long synthetic source produces chunks of 64, 64 and 38 words. Their total includes overlap, illustrating why repeated boundary text needs deduplication/context budgeting. Stable IDs help target deletion, but real citation fidelity also needs the source revision and page/character provenance from M23.

---

## 16. Budgets, streaming, retries and observability

An agent loop needs more than a prompt saying “stop soon.” Bound model/tool calls, elapsed time, per-tool work, output tokens, concurrency and spend. The verifier's nonterminating scripted agent hits `GraphRecursionError` under a small graph recursion limit. That limit bounds graph progression, not the same quantity as tokens, dollars or a wall-clock deadline.

Current LangChain exposes middleware for common agent policies, but the exact APIs are version-sensitive. Use explicit application budgets and inspect the installed version's configuration rather than copying an old tutorial. This module tests recursion limiting and a bounded runnable retry; it does not test every middleware policy. [LangChain middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)

### Retry only the intended failure

The runnable retry test raises a synthetic timeout once, then succeeds on attempt two. A permission failure is outside that retry classification and executes once. A malformed output might justify a separate bounded repair attempt; a rejected authorization decision does not become a transient error merely because the framework can retry it.

Avoid multiplying retries at the SDK, runnable, graph-node and job layers without a shared budget. Three layers each attempting three times can create many downstream attempts. Give attempts a stable operation identity where effects are possible and propagate deadlines across stages.

### Streaming is a transport/execution feature

The fixture streams a fake model string through `StrOutputParser`. Those chunks are characters generated by the fake adapter, not measured learned-model tokens. A framework's incremental output does not automatically provide an HTTP/SSE endpoint, browser cancellation handling or final answer acceptance. M22 covers those transport concerns.

Distinguish progress updates from candidate answer text and committed results. If an answer must be reviewed before release, stream “retrieval complete” and “awaiting review” events rather than exposing an unapproved private draft to unauthorized viewers. The current docs describe additional agent streaming interfaces; this chapter executes the basic runnable stream path only. [LangChain streaming](https://docs.langchain.com/oss/python/langchain/streaming)

### Trace the stages you need to debug

Record job/request IDs, node/runnable names, attempts, state transitions, source IDs/revisions, result counts, validation failures and stage latency. Do not dump full private prompts, passages or credentials into logs by default. Hosted tracing is optional infrastructure with its own data policy; installing a tracing dependency is not consent to upload content.

The local callback here records message counts and completion events only. Hosted tracing is disabled. It proves callback plumbing, not a distributed tracing deployment or automatic root-cause analysis.

---

## 17. Architectural understanding: build a resumable notes assistant

Start with a deterministic answer workflow. Add model-directed tools only if the product needs flexible task decomposition. Keep ingestion from M23/M24 separate from request-time orchestration so an uploaded source does not become ready merely because an agent run started.

```text
Upload -> canonical source revision -> ingestion job -> retrieval index/manifest

Authenticated question -> owned job -> retrieval -> current permitted evidence
                                            |
                                       draft + hash
                                            |
                                 checkpoint / optional review
                                            |
                               current authority/source check
                                            |
                                idempotent canonical result
                                            |
                                 authorized answer/citations
```

### Suggested API boundary

| Interface | Essential contract |
| --- | --- |
| Start answer job | Authenticated owner, question limits, immutable server job ID |
| Read job/status/events | Authorize before reading checkpoint content |
| Review pending draft | Current reviewer authority, expected draft hash/generation, strict decision schema |
| Resume/recover | Server-controlled action for a known pending state |
| Cancel/delete job | Canonical eligibility change, worker coordination and checkpoint retention |
| Resolve source citation | Current ACL and the intended source revision/location |

The browser should not submit arbitrary graph state, choose a tenant runtime context or select another user's `thread_id`. Treat framework checkpoint APIs as backend implementation capabilities behind your application's authorization layer.

### Separate four stores of state

Canonical source/job state defines current authority. The vector/lexical index is rebuildable retrieval state. Graph checkpoints retain continuation state. Answer/result storage holds accepted product output. Their deletion, consistency and recovery policies differ, even if a small application places some in the same physical database.

The fixture uses two SQLite files to make one important separation visible. It does not include a queue, HTTP API, model provider, multi-worker lease or deployment. A production worker needs concurrency control so two resumes cannot race the same pending review. Use an authoritative state/version transition or lease plus idempotent effects; a thread name alone is not a distributed mutex.

### Failure handling

| Failure | Desired behavior |
| --- | --- |
| Retrieval finds no permitted evidence | Stop or use a deliberately evaluated no-answer branch |
| Parser rejects model text | Bounded repair or explicit validation failure |
| Tool requests another tenant's source | Trusted runtime scope and application authorization deny it |
| User loses access while graph waits | Reauthorize before reading/resuming private checkpoint data |
| Source changes after draft review | Reject stale commitment and create a new review generation |
| Node effect succeeds before completion checkpoint | Retry/reconcile with the same idempotency key |
| Agent keeps requesting tools | Enforce call/step/time/spend limits and report bounded failure |
| Worker code changes while old jobs are paused | Maintain compatible workflow versions or migrate/restart deliberately |

---

## 18. Choosing a framework and common wrong answers

| Situation | A reasonable starting point |
| --- | --- |
| One model request with a small fixed prompt | Plain SDK/application functions |
| Several reusable model/tool adapters and typed stages | LangChain composition |
| Explicit branching, long waits and recoverable state | LangGraph workflow |
| Data loading, chunk/node metadata and retrieval query composition | LlamaIndex |
| A combination of these requirements | Compose behind narrow application interfaces after a prototype |

A framework introduces dependency/version, configuration and debugging costs. Measure the work it saves against those costs. Hide library-specific objects at service boundaries where practical: an application `Evidence` contract or `AnswerResult` is easier to preserve across migrations than returning a framework's entire internal state to the browser.

### Common misconceptions

| Incorrect claim | Better explanation |
| --- | --- |
| LangChain is a model | It is an application framework using model interfaces |
| Every RAG app needs an agent | Fixed authorized retrieval can be a deterministic workflow |
| LangGraph is a graph database | It represents execution state and transitions |
| TypedDict makes all graph input safe | Explicit runtime validation and authorization still apply |
| A checkpoint guarantees each effect happens once | Nodes can replay; effects need idempotency/reconciliation |
| A thread ID is a security boundary | Authorize access before inspecting or resuming a thread |
| A valid JSON answer must be correct | Structure, evidence identity and factual support are distinct |
| ToolRuntime automatically grants correct permissions | It injects context; trusted application code enforces policy |
| LlamaIndex source nodes prove a faithful citation | They expose provenance candidates; claims still need support checks |
| Framework mocks prove production model behavior | They isolate integration mechanics from learned behavior |

### Resume connection

If you used these libraries in a RAG project, explain the actual boundaries: which component loaded/chunked documents, where vectors lived, what selected authorized sources, how the prompt was built, whether a model selected tools, what was persisted and how failures were recovered.

Do not add this fixture's checkpointing, approval mechanism or replay guarantees to an earlier project's claims unless its code actually implemented them. These notes provide a learning and design path, not evidence that every listed project already had these features.

For debugging, first identify the failed stage and inspect its contract: loader output, chunk metadata, retrieval scope, prompt shape, model/tool message, parser, reducer, checkpoint or canonical commit. A framework stack trace should become a concrete input/state transition you can reproduce.

---

## 19. Interview questions and answers

### Q1. What is LangChain?

It is an application framework with model, message, tool and composition interfaces, including an agent harness. It is not an LLM. Explain which integration or execution contract it provides in your application and which database, model and business rules remain outside it. Our example runs actual composition with explicitly fake model responses.

### Q2. What is LangGraph?

It is a framework for stateful execution through nodes and transitions, with facilities such as checkpoints and interrupts. Our graph performs retrieval, drafting, review and commitment without calling a learned model. It represents control flow, not stored domain relationships like a graph database or vector proximity links like HNSW.

### Q3. What is LlamaIndex?

It provides data-backed application abstractions such as documents, nodes, ingestion transformations, indexes, retrievers and query engines. Our example uses those actual components with a handwritten feature encoder and MockLLM. The application still defines source ownership, revisions, embedding compatibility and answer acceptance.

### Q4. How do these three libraries relate?

Their features overlap, but LangChain emphasizes model/tool integration and composition, LangGraph explicit workflow state/control, and LlamaIndex data ingestion/retrieval composition. Current LangChain agents use LangGraph underneath. Choose components for requirements; using all three is not a prerequisite for RAG or evidence that the architecture is more advanced.

### Q5. What is the difference between a chain, workflow and agent?

A chain composes operations; a workflow declares stateful steps and routing; an agent lets model output influence which available operation happens next. Fixed search-and-answer can be deterministic. Our scripted agent exercises the actual tool loop but does not prove learned decision quality. Explain why dynamic tool selection is needed before introducing it.

### Q6. What is LCEL and what does the pipe operator do?

It composes runnable stages by passing one stage's output into the next. In the fixture, authorized preparation returns prompt variables, the template produces messages, a fake chat model returns JSON text and a parser produces Answer. The operator is composition, not parallel execution by itself or a security boundary.

### Q7. How do invoke, batch, ainvoke and stream differ?

They handle one input, multiple inputs, asynchronous invocation and incremental output respectively. Their availability does not mean each underlying operation becomes nonblocking or gains unlimited throughput. Our tests execute synchronous/async/batch paths and a fake-model stream; provider latency, tokenization and HTTP transport are separate concerns.

### Q8. Does an output schema make an answer correct?

No. Parsing checks format and declared types; application checks enforce allowed references and domain constraints; factual support needs another evaluation. The fixture rejects malformed JSON, extra fields and a beta citation in alpha evidence. It can still accept an unsupported statement that cites a permitted source, so do not call that an entailment check.

### Q9. How does an agent call a tool?

The model returns a requested tool name, arguments and call ID. The harness executes an available implementation under application policy and returns a correlated tool observation before another model turn. Our real loop produces human, AI, tool and AI messages. The model proposes the action; trusted code decides whether it is allowed.

### Q10. What is ToolRuntime used for?

It gives the tool access to invocation state/context and other runtime facilities without making that context a model-visible argument. Our schema exposes topic and limit, while the tool receives Principal through runtime.context. Hiding identity does not enforce policy by itself; the implementation checks read permission and tenant scope.

### Q11. How do you secure an agent tool?

Expose a narrow operation, validate arguments, derive identity from trusted context, authorize current resource access and bound work. For effects, use stable operation IDs and any required approval policy. Do not expose unrestricted SQL or let the model choose a tenant. Test allowed and denied paths through the actual tool harness, not only the underlying helper.

### Q12. How do you stop an agent from looping forever?

Define termination and bound graph progression, model/tool calls, elapsed time, concurrency and spend. Our scripted loop reaches GraphRecursionError under a small recursion limit. That is not a token or dollar budget. A prompt instruction to stop is useful behavior guidance, but application limits must still enforce the resource contract.

### Q13. What are state, nodes and edges in LangGraph?

State carries execution data; a node reads it and returns updates; edges select subsequent execution. Conditional routing can end early when no evidence exists or review is negative. Keep state compact and serializable, and put current clients/credentials/principal dependencies in trusted runtime context rather than checkpointing them as authority.

### Q14. Does TypedDict validate graph inputs at runtime?

It describes shape for code/tooling, but is not a complete public-input validator or authorization layer. Validate request payloads, review decisions and resource access explicitly. Our review uses a strict Pydantic Decision; the worker checks canonical ownership before inspecting saved state. Neither step is replaced by state type annotations.

### Q15. What is a reducer?

It defines how an existing state field combines with a returned update. Replacement, addition and identity-aware message merging express different semantics. Our parallel graph combines event lists, while a scalar update replaces status. An empty additive update does not clear the list; test the intended business behavior instead of picking a reducer just to suppress an error.

### Q16. What happens when parallel nodes update the same field?

Without an appropriate reducer, conflicting concurrent updates can raise InvalidUpdateError. With a reducer, the merge rule becomes explicit but still must match the data meaning. The fixture checks this failure and a successful fan-out/fan-in graph. Independent parallel contributions should not be interpreted as an ordered business history without an ordering contract.

### Q17. Why use add_messages instead of ordinary list concatenation?

Messages have IDs and can be replaced/edited. The tested reducer replaces a matching-ID message rather than appending a duplicate. Concatenation is suitable for some append-only event lists but would treat an edit as another message. Preserve the distinction between editable conversation messages, execution events and canonical business records.

### Q18. What does a checkpointer persist?

It retains graph execution-state snapshots used for thread continuity and recovery. Our file saver carries a pending review into a fresh process. Canonical ownership, source freshness and committed product results are stored separately. A checkpoint can contain private passages, so thread access and retention need the same attention as other sensitive backend state.

### Q19. Is InMemorySaver durable across a restart?

No. A fresh in-memory saver has no previous snapshots, which our test demonstrates. A file-backed saver provides the local restart mechanism tested here. Production durability also depends on the storage system, deployment, backups and failure model; a successful local resume does not prove resilience to disk loss or distributed worker races.

### Q20. Is thread_id enough to isolate users?

No. It is an identifier for saved execution state, not a credential. Derive/select the thread through an authenticated ownership check and protect inspection, streaming, resume and deletion. Our worker rejects another tenant and another alpha user before reading the checkpoint. Namespacing IDs helps organization but does not independently enforce access.

### Q21. What happens when an interrupted node resumes?

The node is re-entered and receives the resume value at the interrupt, so code before it can execute again. Our pre-interrupt attempt counter becomes two while the completed review update appears once in graph state. Keep irreversible effects out of that pre-interrupt region and maintain compatible interrupt ordering for persisted runs.

### Q22. How should approval be tied to an action?

Authorize the reviewer against current canonical state and bind the decision to the intended job, draft and source generation. Our strict boolean and draft hash prevent a different draft's decision from being accepted. The hash is not authentication. Recheck freshness before commitment, and define whether production policy requires a separate reviewer or multiple approvers.

### Q23. Does checkpointing guarantee exactly-once tool effects?

No. An effect can commit before the node's successful completion checkpoint. Recovery may rerun the node. Our injected failure produces two commit attempts but one matching local result through a unique operation key and transaction. Remote services require their own idempotency/reconciliation contract; local deduplication does not prove distributed exactly-once delivery.

### Q24. What if a source changes while a graph waits for review?

An old checkpoint can retain old text even after the canonical source changes. Recheck current revision/content and permissions before commitment. The fixture returns stale_source after a revision change or deletion and stores no result. A product can create a new draft/review generation rather than silently using the old approval.

### Q25. How do Document and Node differ in LlamaIndex?

A Document represents the source; Nodes are retrieval units produced by parsing/transformations. Preserve source relationships, metadata and stable identity. Our nodes retain ref_doc_id and tenant/revision metadata. Actual citations also need the intended source revision and location; a node ID alone does not establish page-level provenance or support for a claim.

### Q26. What does a LlamaIndex query engine do?

It composes retrieval, optional node postprocessing and response synthesis. Our query engine retrieves alpha candidates, applies a similarity cutoff and calls explicit MockLLM. Its response includes source nodes. The mock's repeated text and feature vectors establish framework mechanics, not a useful semantic answer or a validated citation policy.

### Q27. Do metadata filters make the entire RAG system secure?

They scope a retrieval operation when correctly supplied and supported by the store. Identity selection, canonical ACL/freshness checks, checkpoint access and output handling still matter. Our local vector store's alpha/beta filters are tested. Do not assume a remote adapter supports identical expressions or that old cached/checkpointed passages become authorized automatically.

### Q28. How would you persist and update a LlamaIndex index?

Persist the configured storage components or use the selected store's persistence, then reload with compatible encoder/configuration. Track source IDs, revisions and chunk manifests for replacement/deletion. Our local persist/reload retains IDs/scores and delete_ref_doc removes alpha's source while leaving beta. Hosted publication, backups and retention require additional verification.

### Q29. How do you debug or evaluate framework-based AI applications?

Trace stage contracts: source/chunks, retrieval scope, prompt shape, model/tool messages, parser, graph updates, checkpoint and canonical effect. Use deterministic fixtures for mechanisms, then labeled tasks and representative failure/latency cases for actual models. Keep logs scoped and redact sensitive content. Hosted tracing is optional and was disabled in this module.

### Q30. When would you avoid these frameworks?

When a few explicit functions or a direct SDK request meet the requirements more clearly with less dependency/configuration overhead. Adopt a framework for a concrete reusable integration, retrieval or state-control benefit. Explain the application's invariants first, then the library chosen to implement them. A stack with more framework names is not automatically more reliable.

---

## 20. Practice tasks

1. Implement the same small authorized retrieval/answer flow with plain functions and with LCEL. Compare the inputs, outputs and errors at each stage without claiming a model-quality difference.
2. Return malformed JSON, an extra schema field, a wrong citation ID and a schema-valid unsupported statement. Identify which validation layer detects each and which remains undetected.
3. Extend the read-only tool with a narrowly scoped document lookup. Attempt cross-tenant IDs and oversized arguments; verify that runtime identity comes from trusted application context.
4. Add separate model-call, tool-call and elapsed-time budgets to the scripted agent. Show that graph recursion limit is not a substitute for all three.
5. Create a parallel graph with a deliberately conflicting state update. Add a reducer matching the intended business meaning and explain why appending lists is different from replacing a message by ID.
6. Extend the file-checkpoint scenario to pause at two separate review nodes. Resume in new processes and document what must remain compatible when workflow code changes.
7. Add a canonical job version or lease that prevents competing review resumes. Run two workers and verify the allowed transition and idempotent result behavior.
8. Replace the fixture's word-count encoder with an explicitly configured learned encoder only after defining a labeled evaluation set. Report integration, ANN loss and relevance separately; preserve tenant/revision constraints.
9. Build a deletion checklist for sources, vectors, query caches, committed answers and checkpoint history. Demonstrate a late worker and revoked reviewer cannot expose or republish the deleted source.
10. Design an outbox around a hypothetical external effect after review. Inject failures before dispatch, after remote acceptance and before local acknowledgment; explain which guarantees require actual destination support.

---

## 21. Revision checklist

- [ ] I can distinguish a framework, model, vector store and canonical database.
- [ ] I can compare a chain, deterministic workflow and model-directed agent.
- [ ] I can trace messages and shapes through an LCEL expression.
- [ ] I can distinguish schema parsing from citation authority and factual support.
- [ ] I can explain tool-call IDs, injected context and application authorization.
- [ ] I can describe LangGraph state, nodes, routing and reducers.
- [ ] I can explain conflicting parallel updates and identity-aware message reduction.
- [ ] I can distinguish in-memory continuity, file checkpoints and canonical results.
- [ ] I can explain why interrupt resumption reruns pre-interrupt code.
- [ ] I can bind review to a draft and recheck permissions/source freshness.
- [ ] I can explain LlamaIndex documents, nodes, retrieval, synthesis and persistence.
- [ ] I can justify framework choice, execution budgets and replay-safe effects.

---

## 22. Primary sources and verification artifacts

Version-sensitive sources were checked on **15 October 2026**. The installed packages and actual checks above define the executed behavior; provider/model features need separate verification.

| Topic | Primary reference |
| --- | --- |
| LangChain role and agent harness | [Overview](https://docs.langchain.com/oss/python/langchain/overview), [agents](https://docs.langchain.com/oss/python/langchain/agents) |
| Model/message interface | [Models](https://docs.langchain.com/oss/python/langchain/models), installed `langchain_core` source |
| Tools and context | [Tools](https://docs.langchain.com/oss/python/langchain/tools) |
| Output/limits/streaming | [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output), [middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in), [streaming](https://docs.langchain.com/oss/python/langchain/streaming) |
| Workflow foundations | [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview), [workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents) |
| State/routing/reducers | [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api) |
| Pause and persistence | [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts), [persistence](https://docs.langchain.com/oss/python/langgraph/persistence), [memory](https://docs.langchain.com/oss/python/langgraph/add-memory) |
| LlamaIndex data model | [Concepts](https://developers.llamaindex.ai/python/framework/getting_started/concepts/), [documents/nodes](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_documents/) |
| Ingestion and vector indexing | [IngestionPipeline](https://developers.llamaindex.ai/python/framework/module_guides/loading/ingestion_pipeline/), [VectorStoreIndex](https://developers.llamaindex.ai/python/framework/module_guides/indexing/vector_store_index/) |
| Query and storage | [Query stages](https://developers.llamaindex.ai/python/framework/understanding/rag/querying/), [query engines](https://developers.llamaindex.ai/python/framework/module_guides/deploying/query_engine/), [persist/load](https://developers.llamaindex.ai/python/framework/module_guides/storing/save_load/) |

Artifacts are under `examples/resume-skills/module-25-frameworks/`: the six sources embedded verbatim above, the external-network guard, `verify.py`, dependency lock/check, `verification-results.json`, `cleanup-results.json` and content/site validation evidence. The report names all actual assertions and records the observations without treating scripted responses as learned-model results.

**Next: [M26: Neo4j and graph-backed applications](/docs/resume-skills/neo4j-graph-backed-applications).** That chapter separates domain graph data and traversals from the workflow graphs and vector-index graphs discussed here.
