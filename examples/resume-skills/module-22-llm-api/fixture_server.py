"""A narrow handwritten API peer, not an LLM or a provider emulator."""
from collections import Counter
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import json
import time

CARD = {'topic': 'nodejs', 'summary': 'Node.js runs JavaScript outside the browser.', 'source_ids': ['note-a']}
USAGE = {'input_tokens': 1000, 'input_tokens_details': {'cached_tokens': 200}, 'output_tokens': 100,
         'output_tokens_details': {'reasoning_tokens': 40}, 'total_tokens': 1100}


def response_body(text=None, status='completed', output=None):
    if output is None:
        output = [{'id': 'msg_fixture', 'type': 'message', 'role': 'assistant', 'status': 'completed',
                   'content': [{'type': 'output_text', 'text': text or '', 'annotations': []}]}]
    return {'id': 'resp_fixture', 'object': 'response', 'created_at': 0, 'model': 'fixture-model',
            'status': status, 'output': output, 'usage': USAGE, 'parallel_tool_calls': False,
            'tools': [], 'tool_choice': 'auto', 'error': None, 'incomplete_details': None}


@contextmanager
def fixture_server():
    state = {'requests': [], 'counts': Counter(), 'disconnected': 0}

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *_args):
            pass

        def send_json(self, status, body, headers=None):
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Connection', 'close')
            self.close_connection = True
            self.send_header('x-request-id', 'fixture-request-id')
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            value = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            scenario = self.headers.get('x-fixture-scenario', 'card')
            state['counts'][scenario] += 1
            # Record shape and test-only authorization status; never log header/key values.
            state['requests'].append({'path': self.path, 'scenario': scenario, 'body': value,
                                      'fixture_authorized': self.headers.get('Authorization') == 'Bearer fixture-key-not-a-secret'})
            try:
                self.respond(scenario, value)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                state['disconnected'] += 1

        def respond(self, scenario, value):
            if self.path == '/v1/chat/completions':
                return self.send_json(200, {'id': 'chat_fixture', 'object': 'chat.completion', 'created': 0,
                    'model': 'fixture/provider-model', 'choices': [{'index': 0, 'finish_reason': 'stop',
                    'message': {'role': 'assistant', 'content': 'Node.js is a JavaScript runtime.'}}],
                    'usage': {'prompt_tokens': 10, 'completion_tokens': 8, 'total_tokens': 18}})
            if self.path != '/v1/responses':
                return self.send_json(404, {'error': {'message': 'Not found', 'type': 'invalid_request_error'}})
            if scenario.startswith('http-') or scenario in ('retry', 'quota', 'huge-hint'):
                status = int(scenario.split('-')[1]) if scenario.startswith('http-') else 429
                if scenario == 'retry' and state['counts'][scenario] > 1:
                    return self.send_json(200, response_body('Recovered'))
                code = 'insufficient_quota' if scenario == 'quota' else 'rate_limit_exceeded' if status == 429 else 'fixture_error'
                return self.send_json(status, {'error': {'message': 'Fixture HTTP failure', 'type': 'api_error', 'code': code}},
                                      {'Retry-After': '60' if scenario == 'huge-hint' else '0'})
            if scenario == 'slow':
                time.sleep(0.15)
                return self.send_json(200, response_body('Late'))
            if scenario.startswith('stream'):
                return self.send_stream(scenario)
            if scenario in ('tool', 'loop', 'bad-tool'):
                results = [item for item in value['input'] if item.get('type') == 'function_call_output']
                if results and scenario == 'tool':
                    return self.send_json(200, response_body('Your note describes the Node.js runtime.'))
                call = {'id': 'fc_fixture', 'type': 'function_call', 'status': 'completed', 'call_id': 'call_read_a',
                        'name': 'delete_note' if scenario == 'bad-tool' else 'read_note',
                        'arguments': json.dumps({'note_id': 'note-a'})}
                return self.send_json(200, response_body(output=[call]))
            if scenario == 'refusal':
                message = {'id': 'msg_refusal', 'type': 'message', 'role': 'assistant', 'status': 'completed',
                           'content': [{'type': 'refusal', 'refusal': 'Cannot provide that answer.'}]}
                return self.send_json(200, response_body(output=[message]))
            if scenario == 'incomplete':
                body = response_body('{"topic":', status='incomplete')
                body['incomplete_details'] = {'reason': 'max_output_tokens'}
                return self.send_json(200, body)
            if scenario == 'empty':
                return self.send_json(200, response_body(output=[]))
            text = json.dumps(CARD) if scenario == 'card' else 'not valid json' if scenario == 'bad-json' else 'Fixture answer'
            return self.send_json(200, response_body(text))

        def send_stream(self, scenario):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            self.wfile.write(b': fixture keepalive\r\n\r\n')
            deltas = ['Node.js ', 'caf\u00e9 \U0001f680']
            events = [{'type': 'response.output_text.delta', 'delta': delta, 'sequence_number': index,
                       'item_id': 'msg_fixture', 'output_index': 0, 'content_index': 0} for index, delta in enumerate(deltas)]
            if scenario == 'stream-error':
                events.append({'type': 'response.failed', 'sequence_number': 2,
                               'response': response_body(status='failed', output=[])})
            elif scenario != 'stream-truncated':
                events.append({'type': 'response.completed', 'sequence_number': 2,
                               'response': response_body(''.join(deltas))})
            for event in events:
                encoded = ('event: ' + event['type'] + '\r\ndata: ' + json.dumps(event, ensure_ascii=False) + '\r\n\r\n').encode('utf-8')
                # Split UTF-8 bytes and event boundaries across actual HTTP writes.
                for start in range(0, len(encoded), 3):
                    self.wfile.write(encoded[start:start + 3])
                self.wfile.flush()

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = Thread(target=server.serve_forever, name='m22-owned-fixture')
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        assert not thread.is_alive()
