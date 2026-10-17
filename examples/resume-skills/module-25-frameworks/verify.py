"""Exercise actual framework runtimes offline, including restart and replay failures."""
import os
os.environ['LANGSMITH_TRACING'] = 'false'
os.environ['LANGCHAIN_TRACING_V2'] = 'false'
os.environ['OTEL_SDK_DISABLED'] = 'true'
from offline import guard_external_connections
network_attempts = guard_external_connections()
import asyncio
from collections import Counter
from dataclasses import asdict
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError, InvalidUpdateError
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import ValidationError
from typing import Annotated, TypedDict
from domain import Answer, Decision, Principal, accept_citations, retrieve
from langchain_demo import LocalTrace, checked_chain_answer, make_agent, make_chain, read_note, stream_fixture
from llama_demo import build_index, query_engine, restore_index, retriever_for, splitter
from llama_index.core import Document
from llama_index.core.schema import MetadataMode
from repository import Repository

BASE = Path(__file__).resolve().parent
checks = []
observations = {}
workers = []


def check(group, name, condition):
    checks.append({'group': group, 'name': name, 'passed': bool(condition)})
    if not condition:
        raise AssertionError(name)


def rejects(group, name, fn, error=ValueError):
    try:
        fn()
    except error:
        check(group, name, True)
    else:
        check(group, name, False)


def scalar(repo, statement, params=()):
    return repo.conn.execute(statement, params).fetchone()[0]


def run_langchain():
    alpha = Principal('alpha', 'alice')
    response = json.dumps({'answer': 'Session records keep login state on the server.', 'citations': ['alpha-session']})
    chain = make_chain(alpha, response)
    trace = LocalTrace()
    answer = checked_chain_answer(chain, alpha, 'session', {'callbacks': [trace], 'tags': ['offline-fixture']})
    check('langchain', 'LCEL returns the declared Pydantic output', isinstance(answer, Answer))
    check('langchain', 'accepted citation belongs to retrieved evidence', answer.citations == ['alpha-session'])
    check('langchain', 'local model callbacks record start/end', [e['event'] for e in trace.events] == ['model_start', 'model_end'])
    check('langchain', 'prompt produces system and human messages', trace.events[0]['message_count'] == 2)
    rejects('langchain', 'malformed JSON rejected by real output parser', lambda: make_chain(alpha, 'not json').invoke({'question': 'session'}), OutputParserException)
    rejects('langchain', 'schema extra field rejected', lambda: make_chain(alpha, '{"answer":"x","citations":["alpha-session"],"admin":true}').invoke({'question': 'session'}), OutputParserException)
    rejects('langchain', 'schema-valid unknown citation rejected by application', lambda: checked_chain_answer(make_chain(alpha, '{"answer":"x","citations":["beta-session"]}'), alpha, 'session'))
    empty_trace = LocalTrace()
    rejects('langchain', 'no-evidence branch stops before fake model', lambda: chain.invoke({'question': 'unfindable'}, {'callbacks': [empty_trace]}), LookupError)
    check('langchain', 'no-evidence branch made zero model calls', empty_trace.events == [])
    rejects('langchain', 'read permission denied before model call', lambda: make_chain(Principal('alpha', 'alice', False), response).invoke({'question': 'session'}), PermissionError)
    batch = chain.batch([{'question': 'session'}, {'question': 'session'}], {'max_concurrency': 2})
    check('langchain', 'real batch returns ordered typed outputs', len(batch) == 2 and all(isinstance(a, Answer) for a in batch))
    async def asynchronous():
        single = await chain.ainvoke({'question': 'session'})
        many = await chain.abatch([{'question': 'session'}] * 2, {'max_concurrency': 2})
        return single, many
    single, many = asyncio.run(asynchronous())
    check('langchain', 'real ainvoke agrees with synchronous answer', single == answer)
    check('langchain', 'real abatch returns both answers', len(many) == 2 and all(a == answer for a in many))
    chunks = list(stream_fixture().stream('hello'))
    check('langchain', 'fake chat model streams through string parser', ''.join(chunks) == 'local-stream' and len(chunks) > 1)
    attempts = []
    def flaky(value):
        attempts.append(value)
        if len(attempts) == 1:
            raise TimeoutError('Synthetic transient read failure')
        return 'retried'
    retried = RunnableLambda(flaky).with_retry(retry_if_exception_type=(TimeoutError,), stop_after_attempt=2, wait_exponential_jitter=False).invoke('x')
    check('retry_budget', 'bounded runnable retry succeeds on second attempt', retried == 'retried' and len(attempts) == 2)
    denied_attempts = []
    def denied(value):
        denied_attempts.append(value)
        raise PermissionError('No access')
    rejects('retry_budget', 'authorization denial is not a transient retry', lambda: RunnableLambda(denied).with_retry(retry_if_exception_type=(TimeoutError,), stop_after_attempt=2, wait_exponential_jitter=False).invoke('x'), PermissionError)
    check('retry_budget', 'nonretryable call executed only once', len(denied_attempts) == 1)
    observations['langchain'] = {'answer': answer.model_dump(), 'callbacks': trace.events,
        'batch_outputs': len(batch), 'async_outputs': len(many), 'stream_joined': ''.join(chunks),
        'transient_attempts': len(attempts), 'denied_attempts': len(denied_attempts)}
    schema = read_note.tool_call_schema.model_json_schema()
    check('agent', 'tool schema exposes topic and limit', set(schema['properties']) == {'topic', 'limit'})
    check('agent', 'tool runtime identity is hidden from model schema', 'runtime' not in schema['properties'] and 'tenant' not in schema['properties'])
    result = make_agent().invoke({'messages': [{'role': 'user', 'content': 'session'}]}, {'recursion_limit': 8}, context=alpha)
    messages = result['messages']
    tools = [m for m in messages if isinstance(m, ToolMessage)]
    calls = [call for m in messages if isinstance(m, AIMessage) for call in m.tool_calls]
    check('agent', 'create_agent actually runs a tool call', len(tools) == len(calls) == 1)
    check('agent', 'tool response retains matching call ID', tools[0].tool_call_id == calls[0]['id'])
    check('agent', 'tool injects authenticated alpha context', 'alpha-session' in tools[0].content and 'beta-session' not in tools[0].content)
    check('agent', 'scripted second model turn produces final reply', messages[-1].content.startswith('Scripted final reply:'))
    beta = make_agent().invoke({'messages': [{'role': 'user', 'content': 'session'}]}, context=Principal('beta', 'bob'))
    check('agent', 'same agent tool routes beta to beta evidence', 'beta-session' in beta['messages'][-1].content and 'alpha-session' not in beta['messages'][-1].content)
    rejects('agent', 'tool implementation enforces runtime permission', lambda: make_agent().invoke({'messages': [{'role': 'user', 'content': 'session'}]}, context=Principal('alpha', 'alice', False)), PermissionError)
    rejects('agent', 'tool implementation rejects oversized limit', lambda: make_agent('bad_limit').invoke({'messages': [{'role': 'user', 'content': 'session'}]}, context=alpha))
    unknown = make_agent('unknown').invoke({'messages': [{'role': 'user', 'content': 'session'}]}, context=alpha)
    check('agent', 'unknown tool is represented as an error observation', any(isinstance(m, ToolMessage) and m.status == 'error' for m in unknown['messages']))
    rejects('retry_budget', 'nonterminating scripted agent hits graph recursion limit', lambda: make_agent('loop').invoke({'messages': [{'role': 'user', 'content': 'session'}]}, {'recursion_limit': 4}, context=alpha), GraphRecursionError)
    observations['agent'] = {'tool_schema_properties': sorted(schema['properties']), 'message_types': [m.type for m in messages],
        'tool_calls': len(calls), 'tool_result': json.loads(tools[0].content),
        'final_reply': messages[-1].content, 'loop_limit_error': 'GraphRecursionError'}


def run_graph_semantics():
    class CounterState(TypedDict):
        value: int
    builder = StateGraph(CounterState)
    builder.add_node('left', lambda state: {'value': 1})
    builder.add_node('right', lambda state: {'value': 2})
    builder.add_edge(START, 'left')
    builder.add_edge(START, 'right')
    builder.add_edge('left', END)
    builder.add_edge('right', END)
    rejects('graph_state', 'parallel writes without reducer rejected', lambda: builder.compile().invoke({'value': 0}), InvalidUpdateError)
    from operator import add
    class ReducedState(TypedDict):
        events: Annotated[list[str], add]
        status: str
    b = StateGraph(ReducedState)
    b.add_node('a', lambda s: {'events': ['a']})
    b.add_node('b', lambda s: {'events': ['b']})
    b.add_node('finish', lambda s: {'status': 'done', 'events': []})
    b.add_edge(START, 'a')
    b.add_edge(START, 'b')
    b.add_edge(['a', 'b'], 'finish')
    b.add_edge('finish', END)
    state = b.compile().invoke({'events': [], 'status': 'new'})
    check('graph_state', 'reducer accumulates parallel updates', sorted(state['events']) == ['a', 'b'])
    check('graph_state', 'empty additive update does not erase accumulated values', len(state['events']) == 2)
    check('graph_state', 'default reducer replaces scalar value', state['status'] == 'done')
    messages = add_messages([AIMessage(content='old', id='same')], [AIMessage(content='replacement', id='same')])
    check('graph_state', 'message reducer replaces matching ID rather than appending duplicate', len(messages) == 1 and messages[0].content == 'replacement')
    saver = InMemorySaver()
    saved_graph = b.compile(checkpointer=saver)
    config = {'configurable': {'thread_id': 'local'}}
    saved_graph.invoke({'events': [], 'status': 'new'}, config)
    check('graph_state', 'same in-memory saver can inspect stored state', saved_graph.get_state(config).values['status'] == 'done')
    fresh = b.compile(checkpointer=InMemorySaver())
    check('graph_state', 'new in-memory saver has no previous state', fresh.get_state(config).values == {})
    observations['graph_state'] = {'parallel_events': sorted(state['events']), 'final_status': state['status'],
        'empty_update_cleared_events': False, 'message_replacement_count': len(messages), 'fresh_memory_snapshot': {}}


def run_worker(folder, job_id, mode, principal=None, **extra):
    payload = {'folder': str(folder), 'job_id': job_id, 'mode': mode,
               'principal': asdict(principal or Principal('alpha', 'alice')), **extra}
    process = subprocess.run([sys.executable, '-X', 'utf8', str(BASE / 'graph_worker.py')],
        input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8', timeout=30,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    process.check_returncode()
    result = json.loads(process.stdout)
    workers.append({'pid': result['pid'], 'returncode': process.returncode,
                    'external_network_attempts': result['external_network_attempts']})
    return result


def run_persistence(folder):
    repo = Repository(folder / 'application.sqlite')
    repo.setup()
    principal = Principal('alpha', 'alice')
    for name in ('approved', 'rejected', 'stale', 'deleted', 'revoked', 'bad-hash', 'bad-type', 'recovery', 'empty'):
        repo.create_job(name, principal)
    try:
        start = run_worker(folder, 'approved', 'start', question='session')
        check('persistence', 'fresh worker pauses at actual interrupt', start['ok'] and len(start['interrupts']) == 1 and start['next'] == ['review'])
        check('persistence', 'draft checkpoint has expected deterministic node trace', start['state']['events'] == ['retrieve', 'draft'])
        check('persistence', 'review has not committed a result', scalar(repo, "SELECT count(*) FROM results WHERE job_id='approved'") == 0)
        check('persistence', 'file checkpointer created persistent tables', (folder / 'checkpoints.sqlite').is_file())
        decision = {'approved': True, 'draft_hash': start['state']['draft_hash']}
        done = run_worker(folder, 'approved', 'resume', decision=decision)
        check('persistence', 'fresh worker resumes saved state', done['ok'] and done['state']['status'] == 'committed')
        check('persistence', 'resume uses a different OS process', start['pid'] != done['pid'])
        check('persistence', 'checkpoint ID advances across resume', start['checkpoint_id'] != done['checkpoint_id'])
        check('persistence', 'successful graph reaches END', done['next'] == [] and done['interrupts'] == [])
        check('persistence', 'review pre-interrupt instrumentation reran', scalar(repo, "SELECT count(*) FROM attempts WHERE job_id='approved' AND node='review'") == 2)
        check('persistence', 'completed node updates appear once in graph event state', done['state']['events'] == ['retrieve', 'draft', 'review', 'commit'])
        check('persistence', 'canonical result is saved exactly once locally', scalar(repo, "SELECT count(*) FROM results WHERE job_id='approved'") == 1)
        duplicate = run_worker(folder, 'approved', 'resume', decision=decision)
        check('approval', 'completed job rejects another approval replay at entry boundary', not duplicate['ok'] and duplicate['error'] == 'ValueError')
        denied = run_worker(folder, 'approved', 'resume', Principal('beta', 'bob'), decision=decision)
        check('approval', 'cross-tenant resume denied before checkpoint read', not denied['ok'] and denied['error'] == 'PermissionError' and 'state' not in denied)
        wrong_user = run_worker(folder, 'approved', 'resume', Principal('alpha', 'mallory'), decision=decision)
        check('approval', 'same-tenant wrong owner denied', not wrong_user['ok'] and wrong_user['error'] == 'PermissionError')
        rejected = run_worker(folder, 'rejected', 'start', question='session')
        rejected = run_worker(folder, 'rejected', 'resume', decision={'approved': False, 'draft_hash': rejected['state']['draft_hash']})
        check('approval', 'negative review routes to END', rejected['ok'] and rejected['state']['status'] == 'rejected' and rejected['next'] == [])
        check('approval', 'negative review creates no canonical result', scalar(repo, "SELECT count(*) FROM results WHERE job_id='rejected'") == 0)
        bad = run_worker(folder, 'bad-hash', 'start', question='session')
        bad = run_worker(folder, 'bad-hash', 'resume', decision={'approved': True, 'draft_hash': '0' * 64})
        check('approval', 'approval bound to another draft is rejected', not bad['ok'] and bad['error'] == 'ValueError')
        bad_type = run_worker(folder, 'bad-type', 'start', question='session')
        bad_type = run_worker(folder, 'bad-type', 'resume', decision={'approved': 'yes', 'draft_hash': bad_type['state']['draft_hash']})
        check('approval', 'strict boolean review schema rejects string yes', not bad_type['ok'] and bad_type['error'] == 'ValidationError')
        revoked = run_worker(folder, 'revoked', 'start', question='session')
        with repo.conn:
            repo.conn.execute("UPDATE jobs SET revoked=1 WHERE job_id='revoked'")
        revoked = run_worker(folder, 'revoked', 'resume', decision={'approved': True, 'draft_hash': revoked['state']['draft_hash']})
        check('approval', 'permission revocation while paused denies resume', not revoked['ok'] and revoked['error'] == 'PermissionError')
        recovery_start = run_worker(folder, 'recovery', 'start', question='session')
        failed = run_worker(folder, 'recovery', 'resume', decision={'approved': True, 'draft_hash': recovery_start['state']['draft_hash']}, fail_after_commit=True)
        check('recovery', 'injected post-commit failure propagates', not failed['ok'] and failed['error'] == 'RuntimeError')
        check('recovery', 'canonical result survived missing graph completion checkpoint', scalar(repo, "SELECT count(*) FROM results WHERE job_id='recovery'") == 1)
        recovered = run_worker(folder, 'recovery', 'recover')
        check('recovery', 'new worker retries pending commit node', recovered['ok'] and recovered['state']['status'] == 'committed')
        check('recovery', 'commit node attempted twice', scalar(repo, "SELECT count(*) FROM attempts WHERE job_id='recovery' AND node='commit'") == 2)
        check('recovery', 'idempotent local result prevents duplicate row', scalar(repo, "SELECT count(*) FROM results WHERE job_id='recovery'") == 1)
        check('recovery', 'completed graph includes one committed node update', recovered['state']['events'].count('commit') == 1)
        rejects('recovery', 'idempotency-key reuse with a different answer is rejected', lambda: repo.commit_result('recovery', principal, recovery_start['state']['evidence'], '1' * 64, 'different'))
        stale = run_worker(folder, 'stale', 'start', question='session')
        with repo.conn:
            repo.conn.execute("UPDATE sources SET revision=2,text='Changed current session policy.' WHERE id='alpha-session'")
        stale = run_worker(folder, 'stale', 'resume', decision={'approved': True, 'draft_hash': stale['state']['draft_hash']})
        check('freshness', 'source revision change while paused blocks commitment', stale['ok'] and stale['state']['status'] == 'stale_source')
        check('freshness', 'stale source creates no result', scalar(repo, "SELECT count(*) FROM results WHERE job_id='stale'") == 0)
        deleted = run_worker(folder, 'deleted', 'start', question='session')
        with repo.conn:
            repo.conn.execute("UPDATE sources SET deleted=1 WHERE id='alpha-session'")
        deleted = run_worker(folder, 'deleted', 'resume', decision={'approved': True, 'draft_hash': deleted['state']['draft_hash']})
        check('freshness', 'source deletion while paused blocks commitment', deleted['ok'] and deleted['state']['status'] == 'stale_source')
        check('freshness', 'deleted source creates no result', scalar(repo, "SELECT count(*) FROM results WHERE job_id='deleted'") == 0)
        empty = run_worker(folder, 'empty', 'start', question='unfindable')
        check('freshness', 'no evidence routes directly to END without review', empty['ok'] and empty['state']['status'] == 'no_evidence' and empty['interrupts'] == [] and empty['next'] == [])
        observations['persistence'] = {'start_status': start['state']['status'], 'start_next': start['next'],
            'start_events': start['state']['events'], 'resume_status': done['state']['status'],
            'resume_events': done['state']['events'], 'different_processes': start['pid'] != done['pid'],
            'review_attempts': 2, 'result_rows': 1, 'checkpoint_changed': start['checkpoint_id'] != done['checkpoint_id']}
        observations['approval'] = {'cross_tenant_error': denied['error'], 'wrong_user_error': wrong_user['error'],
            'negative_decision_status': rejected['state']['status'], 'wrong_hash_error': bad['error'],
            'wrong_boolean_error': bad_type['error'], 'revoked_error': revoked['error'],
            'stale_revision_status': stale['state']['status'], 'deleted_source_status': deleted['state']['status']}
        observations['recovery'] = {'first_resume_error': failed['error'], 'result_survived_before_checkpoint': True,
            'recovered_status': recovered['state']['status'], 'commit_attempts': 2, 'canonical_result_rows': 1,
            'completed_commit_updates': recovered['state']['events'].count('commit'), 'external_service_claim': False}
    finally:
        repo.close()


def run_llama(folder):
    documents, nodes, index, encoder = build_index()
    alpha, beta = Principal('alpha', 'alice'), Principal('beta', 'bob')
    check('llamaindex', 'real ingestion pipeline produces one node per short source', len(documents) == len(nodes) == 3)
    check('llamaindex', 'node IDs deterministic by source and ordinal', {n.id_ for n in nodes} == {'alpha-session:c0', 'alpha-index:c0', 'beta-session:c0'})
    check('llamaindex', 'source document relationships preserved', {n.ref_doc_id for n in nodes} == {d.doc_id for d in documents})
    check('llamaindex', 'pipeline populates three feature coordinates', all(len(n.embedding) == 3 for n in nodes))
    check('llamaindex', 'tenant metadata retained for filtering', {n.metadata['tenant'] for n in nodes} == {'alpha', 'beta'})
    check('llamaindex', 'tenant metadata excluded from embedding text', all('tenant:' not in n.get_content(metadata_mode=MetadataMode.EMBED) for n in nodes))
    check('llamaindex', 'tenant metadata excluded from LLM text', all('tenant:' not in n.get_content(metadata_mode=MetadataMode.LLM) for n in nodes))
    results = retriever_for(index, alpha).retrieve('session')
    check('llamaindex', 'metadata-filtered vector retriever returns alpha only', len(results) == 2 and all(n.metadata['tenant'] == 'alpha' for n in results))
    check('llamaindex', 'feature cosine ranks session above index', results[0].node.ref_doc_id == 'alpha-session' and results[0].score > results[1].score)
    beta_results = retriever_for(index, beta).retrieve('session')
    check('llamaindex', 'beta retrieval excludes alpha nodes', len(beta_results) == 1 and beta_results[0].node.ref_doc_id == 'beta-session')
    rejects('llamaindex', 'retriever factory rejects missing read permission', lambda: retriever_for(index, Principal('alpha', 'alice', False)), PermissionError)
    response = query_engine(index, alpha).query('session')
    check('llamaindex', 'query engine executes explicit MockLLM synthesis', str(response) == 'text text text')
    check('llamaindex', 'similarity postprocessor keeps only matching source', len(response.source_nodes) == 1 and response.source_nodes[0].node.ref_doc_id == 'alpha-session')
    store = folder / 'llama-storage'
    index.storage_context.persist(persist_dir=str(store))
    restored = restore_index(store, encoder)
    restored_results = retriever_for(restored, alpha).retrieve('session')
    check('llamaindex', 'persist/reload preserves IDs and scores', [(n.node.id_, n.score) for n in restored_results] == [(n.node.id_, n.score) for n in results])
    restored.delete_ref_doc('alpha-session', delete_from_docstore=True)
    after_delete = retriever_for(restored, alpha).retrieve('session')
    check('llamaindex', 'delete_ref_doc removes source vectors', all(n.node.ref_doc_id != 'alpha-session' for n in after_delete))
    check('llamaindex', 'source deletion leaves another tenant intact', retriever_for(restored, beta).retrieve('session')[0].node.ref_doc_id == 'beta-session')
    long_doc = Document(id_='long', text=' '.join(['session'] * 150))
    split_nodes = splitter().get_nodes_from_documents([long_doc])
    check('llamaindex', 'real sentence splitter produces multiple bounded word chunks', len(split_nodes) > 1 and all(len(n.text.split()) <= 64 for n in split_nodes))
    check('llamaindex', 'long chunks retain source document relationship', all(n.ref_doc_id == 'long' for n in split_nodes))
    observations['llamaindex'] = {'node_ids': [n.id_ for n in nodes], 'feature_vectors': [n.embedding for n in nodes],
        'alpha_results': [{'id': n.node.id_, 'score': round(n.score, 6)} for n in results],
        'beta_results': [n.node.id_ for n in beta_results], 'mock_answer': str(response),
        'query_source_ids': [n.node.ref_doc_id for n in response.source_nodes],
        'restored_result_ids': [n.node.id_ for n in restored_results], 'after_delete_ids': [n.node.id_ for n in after_delete],
        'long_chunk_word_counts': [len(n.text.split()) for n in split_nodes],
        'embedding_scope': 'Handwritten three-feature word counts; no learned model'}


def main():
    tempbase = Path(tempfile.gettempdir()).resolve()
    folder = Path(tempfile.mkdtemp(prefix='placement-m25-', dir=tempbase)).resolve()
    cleanup = {'loopback_ports_closed': [], 'persistent_listener_started': False}
    try:
        run_langchain()
        run_graph_semantics()
        run_persistence(folder)
        run_llama(folder)
        check('offline', 'parent fixture made zero external socket attempts', not network_attempts)
        check('offline', 'all fresh graph workers made zero external socket attempts', all(w['external_network_attempts'] == 0 for w in workers))
        check('offline', 'all owned worker processes exited', all(w['returncode'] == 0 for w in workers))
    finally:
        if folder.parent != tempbase or not folder.name.startswith('placement-m25-'):
            raise RuntimeError('Unexpected cleanup target')
        shutil.rmtree(folder)
        cleanup['temporary_directory_removed'] = not folder.exists()
        cleanup['worker_processes_exited'] = len(workers)
    check('cleanup', 'temporary application/checkpoint/index data removed', cleanup['temporary_directory_removed'])
    check('cleanup', 'fixture starts no persistent listener', cleanup['persistent_listener_started'] is False)
    versions = {name: importlib.metadata.version(name) for name in (
        'langchain', 'langchain-core', 'langgraph', 'langgraph-checkpoint', 'langgraph-checkpoint-sqlite', 'llama-index-core', 'pydantic')}
    report = {'module': 25, 'verified_date': '2026-10-15', 'python': platform.python_version(), 'os': platform.platform(),
              'sqlite': sqlite3.sqlite_version, 'dependencies': versions, 'counts': dict(Counter(c['group'] for c in checks)),
              'total': len(checks), 'checks': checks, 'observations': observations, 'cleanup': cleanup,
              'scope': 'Actual LangChain/LangGraph/LlamaIndex offline runtimes. Fake/scripted chat, extractive graph draft and handwritten feature embeddings; no learned inference, provider/hosted tracing, HTTP service, Docker or production durability benchmark.'}
    (BASE / 'verification-results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    (BASE / 'cleanup-results.json').write_text(json.dumps(cleanup, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'total': report['total'], 'counts': report['counts'], 'observations': observations, 'cleanup': cleanup}, indent=2))


if __name__ == '__main__':
    main()
