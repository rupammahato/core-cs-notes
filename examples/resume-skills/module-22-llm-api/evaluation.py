def score_fixture_cases(cases):
    """Deterministic grader mechanics; cases contain handcrafted outputs, not model predictions."""
    results = []
    for case in cases:
        prediction = case['prediction']
        format_ok = isinstance(prediction, dict) and set(prediction) == {'label', 'source_id'}
        label_ok = format_ok and prediction['label'] == case['expected_label']
        source_ok = format_ok and prediction['source_id'] in case['allowed_sources']
        results.append({'id': case['id'], 'format_ok': format_ok, 'label_ok': label_ok,
                        'source_scope_ok': source_ok, 'passed': bool(label_ok and source_ok)})
    return {'total': len(results), 'passed': sum(result['passed'] for result in results), 'cases': results}
