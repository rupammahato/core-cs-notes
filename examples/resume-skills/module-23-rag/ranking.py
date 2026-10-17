import re


def reciprocal_rank_fusion(rankings, rank_constant=60):
    if rank_constant <= 0:
        raise ValueError('Positive rank constant required')
    scores = {}
    for ranking in rankings:
        seen = set()
        for rank, identifier in enumerate(ranking, 1):
            if identifier in seen:
                continue
            seen.add(identifier)
            scores[identifier] = scores.get(identifier, 0) + 1 / (rank_constant + rank)
    return [{'id': identifier, 'score': score} for identifier, score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]


def lexical_rerank(query, candidates):
    """A transparent phrase/coverage heuristic, not a learned semantic reranker."""
    terms = set(re.findall(r'\w+', query.lower()))
    def key(item):
        text = item['text'].lower()
        coverage = len(terms & set(re.findall(r'\w+', text)))
        return (-int(query.lower() in text), -coverage, item['score'], item['chunk_id'])
    return sorted(candidates, key=key)
