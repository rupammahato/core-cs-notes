def retrieval_metrics(retrieved, relevant, k):
    # Document-level evaluation: overlapping chunks from one document count once.
    unique = list(dict.fromkeys(retrieved))[:k]
    relevant = set(relevant)
    if not relevant:
        return {'recall': None, 'reciprocal_rank': None, 'empty_result': not unique}
    hits = len(set(unique) & relevant)
    first = next((rank for rank, identifier in enumerate(unique, 1) if identifier in relevant), None)
    return {'recall': hits / len(relevant), 'reciprocal_rank': 1 / first if first else 0.0, 'empty_result': not unique}
