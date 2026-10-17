import json
from contracts import InvalidOutput, completed_text

READ_NOTE_TOOL = {
    'type': 'function', 'name': 'read_note',
    'description': 'Read one note available to the signed-in user.',
    'strict': True,
    'parameters': {
        'type': 'object', 'properties': {'note_id': {'type': 'string'}},
        'required': ['note_id'], 'additionalProperties': False,
    },
}


class NoteTools:
    def __init__(self, principal):
        self.principal = principal  # Trusted caller supplies this, never model arguments.
        self.notes = {'note-a': ('alice', 'Node.js runs JavaScript outside the browser.'),
                      'note-b': ('bob', 'Private React draft.')}
        self.seen = {}
        self.reads = 0

    def execute(self, call_id, name, arguments):
        if not isinstance(call_id, str) or not 1 <= len(call_id) <= 80:
            raise InvalidOutput('Invalid call identifier')
        if name != 'read_note' or not isinstance(arguments, str) or len(arguments) > 256:
            raise InvalidOutput('Tool not allowed')
        try:
            args = json.loads(arguments)
        except ValueError as error:
            raise InvalidOutput('Invalid tool JSON') from error
        if not isinstance(args, dict) or set(args) != {'note_id'} or not isinstance(args['note_id'], str):
            raise InvalidOutput('Invalid tool arguments')
        fingerprint = (self.principal, name, json.dumps(args, sort_keys=True))
        if call_id in self.seen:
            previous, result = self.seen[call_id]
            if previous != fingerprint:
                raise InvalidOutput('Conflicting call reuse')
            return dict(result)
        note = self.notes.get(args['note_id'])
        if note is None or note[0] != self.principal:
            raise PermissionError('Note unavailable')
        self.reads += 1
        result = {'note_id': args['note_id'], 'text': note[1]}
        self.seen[call_id] = (fingerprint, result)
        return dict(result)


def run_tool_loop(client, tools, scenario='tool', max_rounds=3):
    conversation = [{'role': 'user', 'content': 'Read my note-a and explain it.'}]
    trace = []
    for _ in range(max_rounds):
        response = client.responses.create(
            model='fixture-model', store=False, input=conversation, tools=[READ_NOTE_TOOL],
            parallel_tool_calls=False, max_output_tokens=200,
            extra_headers={'x-fixture-scenario': scenario},
        )
        if response.status != 'completed':
            raise InvalidOutput('Tool round incomplete')
        calls = [item for item in response.output if item.type == 'function_call']
        if not calls:
            return completed_text(response), trace
        if len(calls) != 1:
            raise InvalidOutput('One tool call per round is required')
        # Preserve prior output items, including any provider reasoning items.
        conversation.extend(item.model_dump(exclude_none=True) for item in response.output)
        call = calls[0]
        result = tools.execute(call.call_id, call.name, call.arguments)
        conversation.append({'type': 'function_call_output', 'call_id': call.call_id, 'output': json.dumps(result)})
        trace.append({'call_id': call.call_id, 'name': call.name, 'result': result})
    raise InvalidOutput('Tool round budget exhausted')
