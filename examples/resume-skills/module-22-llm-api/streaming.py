from contracts import InvalidOutput, completed_text


def collect_stream(client, scenario='stream', on_delta=lambda delta: None):
    chunks = []
    terminal = None
    with client.responses.create(
        model='fixture-model', input='Explain the fixture topic.', stream=True,
        store=False, max_output_tokens=200, extra_headers={'x-fixture-scenario': scenario},
    ) as stream:
        for event in stream:
            if event.type == 'response.output_text.delta':
                chunks.append(event.delta)
                on_delta(event.delta)  # Preview only; not committed as a complete answer.
            elif event.type in ('error', 'response.failed', 'response.incomplete'):
                raise InvalidOutput('Stream failed')
            elif event.type == 'response.completed':
                terminal = event.response
    if terminal is None:
        raise InvalidOutput('Stream ended before completion')
    result = completed_text(terminal)
    if result['kind'] != 'text' or result['text'] != ''.join(chunks):
        raise InvalidOutput('Preview does not match completed text')
    return {'text': result['text'], 'usage': terminal.usage.model_dump(), 'deltas': chunks}
