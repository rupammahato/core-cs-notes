from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path
from threading import Barrier
import json
import os
import platform
import socket
import subprocess
import sys
import time
import tiktoken
from openai import APIStatusError, APITimeoutError
from accounting import BudgetLedger, estimated_cost
from client import local_client, card_request, router_request
from contracts import InvalidOutput, completed_text, validate_card
from evaluation import score_fixture_cases
from fixture_server import CARD, fixture_server
from reliability import retry_delay, retry_read_only
from streaming import collect_stream
from tools import NoteTools, run_tool_loop

BASE = Path(__file__).resolve().parent
os.environ['TIKTOKEN_CACHE_DIR'] = str(BASE / '.token-cache')
checks = []
observations = {}


def check(group, name, condition):
    assert condition, name
    checks.append({'group': group, 'name': name, 'passed': True})
    print('PASS ' + group + ': ' + name, flush=True)


def rejects(group, name, operation, error_type):
    try:
        operation()
    except error_type:
        check(group, name, True)
    else:
        raise AssertionError(name + ': expected rejection')


encoding = tiktoken.get_encoding('cl100k_base')
samples = ['Hello, world!', 'caf\u00e9 \U0001f680', 'Node.js runs JavaScript outside the browser.']
observations['tokens'] = [{'text': sample, 'characters': len(sample), 'tokens': len(encoding.encode(sample))} for sample in samples]
check('tokens', 'actual_bpe_encoding_round_trips_unicode', all(encoding.decode(encoding.encode(sample)) == sample for sample in samples))
check('tokens', 'token_count_is_not_character_count', any(row['tokens'] != row['characters'] for row in observations['tokens']))
input_count = len(encoding.encode(samples[2]))
fits = lambda count, output, overhead, context: count + output + overhead <= context
check('tokens', 'application_budget_reserves_output_and_overhead', fits(input_count, 200, 128, 512))
check('tokens', 'application_budget_rejects_overflow_before_request', not fits(500, 200, 128, 512))
check('tokens', 'encoded_output_can_exceed_word_count', len(encoding.encode(samples[1])) > len(samples[1].split()))

card_text = json.dumps(CARD)
check('contract', 'valid_card_passes_local_runtime_contract', validate_card(card_text, {'note-a'}) == CARD)
for name, value in [
    ('wrong_enum', {**CARD, 'topic': 'sql'}), ('extra_field', {**CARD, 'role': 'admin'}),
    ('blank_summary', {**CARD, 'summary': ' '}), ('long_summary', {**CARD, 'summary': 'x' * 301}),
    ('unapproved_source', {**CARD, 'source_ids': ['note-b']}), ('duplicate_source', {**CARD, 'source_ids': ['note-a', 'note-a']}),
    ('wrong_source_type', {**CARD, 'source_ids': 'note-a'}), ('missing_field', {'topic': 'nodejs', 'summary': 'x'}),
]:
    rejects('contract', 'reject_' + name, lambda value=value: validate_card(json.dumps(value), {'note-a'}), InvalidOutput)
rejects('contract', 'reject_malformed_json', lambda: validate_card('{', {'note-a'}), InvalidOutput)

with fixture_server() as (origin, state):
    port = int(origin.rsplit(':', 1)[1])
    with local_client(origin) as client:
        response = card_request(client, 'note-a: Node.js runs JavaScript outside the browser.')
        outcome = completed_text(response)
        check('sdk_http', 'responses_sdk_reads_real_local_http', response.status == 'completed' and outcome['kind'] == 'text')
        check('sdk_http', 'structured_card_validates_after_sdk_parsing', validate_card(outcome['text'], {'note-a'}) == CARD)
        request = state['requests'][-1]
        check('sdk_http', 'responses_request_has_schema_and_explicit_storage_policy', request['body']['text']['format']['strict'] is True and request['body']['store'] is False)
        check('sdk_http', 'instructions_and_untrusted_input_are_separate_fields', 'instructions' in request['body'] and request['body']['input'][0]['role'] == 'user')
        check('sdk_http', 'fixed_test_key_is_used_without_environment_credentials', request['fixture_authorized'])
        check('sdk_http', 'sdk_captures_request_id', response._request_id == 'fixture-request-id')
        check('sdk_http', 'usage_has_cached_and_reasoning_subsets', response.usage.input_tokens_details.cached_tokens == 200 and response.usage.output_tokens_details.reasoning_tokens == 40)
        refusal = completed_text(card_request(client, 'fixture refusal', 'refusal'))
        check('sdk_http', 'refusal_is_distinct_from_structured_success', refusal['kind'] == 'refusal')
        rejects('sdk_http', 'incomplete_is_not_published_as_success', lambda: completed_text(card_request(client, 'x', 'incomplete')), InvalidOutput)
        rejects('sdk_http', 'empty_completed_output_is_rejected', lambda: completed_text(card_request(client, 'x', 'empty')), InvalidOutput)
        rejects('sdk_http', 'unstructured_peer_output_fails_contract', lambda: validate_card(completed_text(card_request(client, 'x', 'bad-json'))['text'], {'note-a'}), InvalidOutput)
        observations['responses'] = {'status': response.status, 'card': CARD, 'usage': response.usage.model_dump(), 'request_id': response._request_id, 'refusal_kind': refusal['kind']}
        chat = router_request(client)
        router_body = state['requests'][-1]['body']
        check('router_shape', 'chat_compatible_sdk_uses_chat_completions_path', state['requests'][-1]['path'] == '/v1/chat/completions')
        check('router_shape', 'chat_response_uses_choices_message_content', chat.choices[0].message.content == 'Node.js is a JavaScript runtime.')
        check('router_shape', 'router_preferences_survive_extra_body_serialization', router_body['provider'] == {'require_parameters': True, 'allow_fallbacks': False})
        check('router_shape', 'chat_request_does_not_reuse_responses_input_shape', 'messages' in router_body and 'input' not in router_body)
        observations['router_request'] = router_body
        preview = []
        streamed = collect_stream(client, on_delta=preview.append)
        check('stream', 'semantic_deltas_survive_fragmented_utf8_http', streamed['text'] == 'Node.js caf\u00e9 \U0001f680')
        check('stream', 'preview_deltas_match_terminal_completed_text', preview == streamed['deltas'] and ''.join(preview) == streamed['text'])
        check('stream', 'final_stream_event_supplies_usage', streamed['usage']['total_tokens'] == 1100)
        rejects('stream', 'eof_without_completion_is_failure', lambda: collect_stream(client, 'stream-truncated'), InvalidOutput)
        rejects('stream', 'midstream_failure_is_not_complete_answer', lambda: collect_stream(client, 'stream-error'), InvalidOutput)
        observations['stream'] = streamed
        tools = NoteTools('alice')
        result, trace = run_tool_loop(client, tools)
        check('tool_http', 'two_round_tool_exchange_returns_final_text', result['kind'] == 'text' and len(trace) == 1 and state['counts']['tool'] == 2)
        sent = state['requests'][-1]['body']['input']
        output = next(item for item in sent if item.get('type') == 'function_call_output')
        check('tool_http', 'tool_output_links_call_id_and_preserves_prior_item', output['call_id'] == trace[0]['call_id'] and any(item.get('type') == 'function_call' for item in sent))
        check('tool_http', 'principal_is_not_taken_from_model_arguments', trace[0]['result']['note_id'] == 'note-a' and tools.principal == 'alice')
        rejects('tool_http', 'unknown_tool_from_peer_is_blocked', lambda: run_tool_loop(client, NoteTools('alice'), 'bad-tool'), InvalidOutput)
        rejects('tool_http', 'repeated_tool_loop_stops_at_round_budget', lambda: run_tool_loop(client, NoteTools('alice'), 'loop', 3), InvalidOutput)
        check('tool_http', 'round_budget_bounds_actual_http_calls', state['counts']['loop'] == 3)
        observations['tool_exchange'] = {'final': result, 'trace': trace, 'provider_rounds': state['counts']['tool']}
        attempt = lambda scenario: lambda remaining: client.with_options(timeout=remaining).responses.create(
            model='fixture-model', input='Read-only fixture', extra_headers={'x-fixture-scenario': scenario})
        recovered = retry_read_only(attempt('retry'))
        check('retry_http', 'transient_429_recovers_in_two_attempts', recovered.output_text == 'Recovered' and state['counts']['retry'] == 2)
        for scenario in ('http-400', 'http-401', 'quota'):
            rejects('retry_http', scenario + '_is_not_retried', lambda scenario=scenario: retry_read_only(attempt(scenario)), APIStatusError)
            check('retry_http', scenario + '_has_one_network_attempt', state['counts'][scenario] == 1)
        rejects('retry_http', 'persistent_503_exhausts_attempt_budget', lambda: retry_read_only(attempt('http-503')), APIStatusError)
        check('retry_http', 'sdk_retry_disabled_prevents_nested_attempts', state['counts']['http-503'] == 3)
        rejects('retry_http', 'huge_retry_hint_is_not_shortened', lambda: retry_read_only(attempt('huge-hint'), budget_seconds=0.5), TimeoutError)
        rejects('retry_http', 'actual_http_read_timeout_surfaces', lambda: client.with_options(timeout=0.03).responses.create(model='fixture-model', input='x', extra_headers={'x-fixture-scenario': 'slow'}), APITimeoutError)
        check('retry_http', 'ambiguous_timeout_is_not_automatically_replayed', state['counts']['slow'] == 1)
        observations['retry_attempts'] = {name: state['counts'][name] for name in ('retry', 'http-400', 'http-401', 'quota', 'http-503', 'huge-hint', 'slow')}
    check('cleanup', 'sdk_http_client_closed', client.is_closed())
    time.sleep(0.2)  # Let the one controlled timeout handler finish before server closure.
    observations['local_requests'] = len(state['requests'])

rejects('boundary', 'local_example_rejects_external_provider_url', lambda: local_client('https://api.openai.com'), ValueError)
rejects('boundary', 'local_example_rejects_url_credentials', lambda: local_client('http://alice:password@127.0.0.1:1234'), ValueError)
check('retry_policy', 'numeric_retry_after_is_respected', retry_delay('1.5', 1) == 1.5)
check('retry_policy', 'http_date_retry_after_is_supported', retry_delay('Thu, 15 Oct 2026 00:00:03 GMT', 1, now=datetime(2026, 10, 15, tzinfo=timezone.utc)) == 3)
check('retry_policy', 'invalid_hint_uses_bounded_jitter', retry_delay('NaN', 2, random_value=0.0) == 0.25)
check('retry_policy', 'fallback_backoff_is_capped', retry_delay(None, 10, random_value=1.0) == 4.0)

dispatcher = NoteTools('alice')
first = dispatcher.execute('c1', 'read_note', '{"note_id":"note-a"}')
check('tool_policy', 'same_call_replay_reuses_local_result', dispatcher.execute('c1', 'read_note', '{"note_id":"note-a"}') == first and dispatcher.reads == 1)
for name, operation, error in [
    ('unknown_tool', lambda: dispatcher.execute('c2', 'delete_note', '{}'), InvalidOutput),
    ('wrong_owner', lambda: dispatcher.execute('c2', 'read_note', '{"note_id":"note-b"}'), PermissionError),
    ('model_supplied_principal', lambda: dispatcher.execute('c2', 'read_note', '{"note_id":"note-a","principal":"bob"}'), InvalidOutput),
    ('malformed_arguments', lambda: dispatcher.execute('c2', 'read_note', '{'), InvalidOutput),
    ('conflicting_call_reuse', lambda: dispatcher.execute('c1', 'read_note', '{"note_id":"note-b"}'), InvalidOutput),
]:
    rejects('tool_policy', name + '_is_rejected', operation, error)

cost = estimated_cost(1000, 200, 100)
check('accounting', 'cached_input_subset_and_output_cost_equal_decimal_total', cost == Decimal('0.0025'))
rejects('accounting', 'cached_input_cannot_exceed_total_input', lambda: estimated_cost(10, 11, 1), ValueError)
rejects('accounting', 'negative_usage_is_rejected', lambda: estimated_cost(10, 0, -1), ValueError)
ledger = BudgetLedger('0.01')
ledger.reserve('r1', '0.004'); ledger.settle('r1', cost)
check('accounting', 'settlement_refunds_unused_reservation', ledger.available == Decimal('0.0075'))
ledger.settle('r1', cost)
check('accounting', 'same_settlement_is_idempotent_in_process', ledger.available == Decimal('0.0075'))
rejects('accounting', 'conflicting_settlement_is_rejected', lambda: ledger.settle('r1', '0.003'), ValueError)
ledger.reserve('unknown', '0.002')
check('accounting', 'ambiguous_timeout_keeps_reservation_for_reconciliation', ledger.available == Decimal('0.0055') and 'unknown' in ledger.reservations)
concurrent = BudgetLedger('0.005')
barrier = Barrier(2)
def reserve_concurrently(index):
    barrier.wait()
    try:
        concurrent.reserve(str(index), '0.004')
        return 'admitted'
    except PermissionError:
        return 'denied'
with ThreadPoolExecutor(max_workers=2) as pool:
    admissions = list(pool.map(reserve_concurrently, range(2)))
check('accounting', 'concurrent_admission_does_not_overspend_available_balance', sorted(admissions) == ['admitted', 'denied'] and concurrent.available == Decimal('0.001'))
observations['cost'] = {'price_kind': 'hypothetical USD per million tokens', 'input_tokens': 1000, 'cached_input_tokens': 200,
                        'output_tokens_including_reasoning': 100, 'reasoning_subset': 40, 'estimated_usd': str(cost),
                        'balance_after_settlement': '0.0075', 'balance_with_unknown_reservation': str(ledger.available),
                        'concurrent_admissions': sorted(admissions)}

cases = [
    {'id': 'correct', 'prediction': {'label': 'runtime', 'source_id': 'note-a'}, 'expected_label': 'runtime', 'allowed_sources': ['note-a']},
    {'id': 'wrong-label', 'prediction': {'label': 'framework', 'source_id': 'note-a'}, 'expected_label': 'runtime', 'allowed_sources': ['note-a']},
    {'id': 'wrong-scope', 'prediction': {'label': 'runtime', 'source_id': 'note-b'}, 'expected_label': 'runtime', 'allowed_sources': ['note-a']},
    {'id': 'bad-format', 'prediction': 'runtime', 'expected_label': 'runtime', 'allowed_sources': ['note-a']},
]
evaluation = score_fixture_cases(cases)
check('evaluation', 'handwritten_correct_case_passes', evaluation['cases'][0]['passed'])
check('evaluation', 'format_success_does_not_hide_semantic_failure', evaluation['cases'][1]['format_ok'] and not evaluation['cases'][1]['passed'])
check('evaluation', 'correct_label_does_not_hide_source_scope_failure', evaluation['cases'][2]['label_ok'] and not evaluation['cases'][2]['passed'])
check('evaluation', 'aggregate_records_handcrafted_case_results', evaluation['passed'] == 1 and evaluation['total'] == 4)
observations['evaluation'] = evaluation

with socket.socket() as probe:
    closed = probe.connect_ex(('127.0.0.1', port)) != 0
check('cleanup', 'owned_loopback_listener_closed', closed)
dependency = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
dependency.check_returncode()
(BASE / 'dependency-check.txt').write_text(dependency.stdout, encoding='utf-8')
frozen = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
(BASE / 'requirements-lock.txt').write_text(frozen.stdout, encoding='utf-8')
counts = {group: sum(item['group'] == group for item in checks) for group in sorted({item['group'] for item in checks})}
proof = {'module': 22, 'verified_date': '2026-10-15', 'python': platform.python_version(), 'os': platform.platform(),
         'dependencies': {name: version(name) for name in ('openai', 'httpx', 'tiktoken')},
         'checks': checks, 'counts': counts, 'total': len(checks), 'observations': observations,
         'cleanup': {'sdk_closed': True, 'loopback_ports_closed': {str(port): closed}, 'docker_started': False},
         'scope': 'Actual OpenAI Python SDK serialization/parsing/SSE/errors over owned local HTTP; actual cl100k_base tokenizer; local tool/authorization, retry, Decimal budget/concurrency and deterministic grader mechanics. Handcrafted responses, no model inference/provider calls/keys/charges, no learned-model quality or production durability claim.'}
(BASE / 'verification-results.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(BASE / 'cleanup-results.json').write_text(json.dumps(proof['cleanup'], indent=2) + '\n', encoding='utf-8')
print(json.dumps({'counts': counts, 'total': len(checks), 'cleanup': proof['cleanup']}, indent=2))
