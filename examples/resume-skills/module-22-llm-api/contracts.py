import json

CARD_SCHEMA = {
    'type': 'object',
    'properties': {
        'topic': {'type': 'string', 'enum': ['nodejs', 'react']},
        'summary': {'type': 'string'},
        'source_ids': {'type': 'array', 'items': {'type': 'string'}},
    },
    'required': ['topic', 'summary', 'source_ids'],
    'additionalProperties': False,
}


class InvalidOutput(ValueError):
    pass


def validate_card(text, allowed_sources):
    try:
        value = json.loads(text)
    except (ValueError, TypeError) as error:
        raise InvalidOutput('Invalid JSON') from error
    if not isinstance(value, dict) or set(value) != {'topic', 'summary', 'source_ids'}:
        raise InvalidOutput('Invalid fields')
    if value['topic'] not in ('nodejs', 'react'):
        raise InvalidOutput('Unknown topic')
    if not isinstance(value['summary'], str) or not 1 <= len(value['summary'].strip()) <= 300:
        raise InvalidOutput('Invalid summary')
    sources = value['source_ids']
    if not isinstance(sources, list) or not 1 <= len(sources) <= 3:
        raise InvalidOutput('Invalid source list')
    if any(not isinstance(source, str) or source not in allowed_sources for source in sources):
        raise InvalidOutput('Unapproved source')
    if len(set(sources)) != len(sources):
        raise InvalidOutput('Duplicate source')
    return value


def completed_text(response):
    if response.status != 'completed':
        raise InvalidOutput('Response did not complete')
    parts = []
    for item in response.output:
        if item.type != 'message':
            continue
        for content in item.content:
            if content.type == 'refusal':
                return {'kind': 'refusal', 'text': content.refusal}
            if content.type == 'output_text':
                parts.append(content.text)
    if not parts:
        raise InvalidOutput('No completed text')
    return {'kind': 'text', 'text': ''.join(parts)}
