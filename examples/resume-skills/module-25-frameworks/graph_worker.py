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
