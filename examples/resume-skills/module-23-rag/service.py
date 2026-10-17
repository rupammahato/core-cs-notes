from copy import deepcopy
from context import pack_context, extractive_reply, validate_reply
from ranking import lexical_rerank


class SearchService:
    def __init__(self, store, encoding):
        self.store = store
        self.encoding = encoding
        self.cache = {}

    def search(self, principal, query, limit=5):
        self.store.query_expression(query)
        if type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError('Limit must be 1..10')
        # One global corpus epoch simplifies invalidation; scope remains part of every key.
        key = (principal.tenant, principal.user, self.store.epoch(), query, limit)
        if key in self.cache:
            return deepcopy(self.cache[key]), True
        epoch, candidates = self.store.search(principal, query, limit)
        ranked = lexical_rerank(query, candidates)
        key = (principal.tenant, principal.user, epoch, query, limit)
        self.cache[key] = deepcopy(ranked)
        # Keep the teaching cache bounded; this is not a distributed result cache.
        if len(self.cache) > 32:
            self.cache.pop(next(iter(self.cache)))
        return ranked, False

    def answer(self, principal, query):
        candidates, hit = self.search(principal, query)
        packed = pack_context(self.store, principal, query, candidates, self.encoding)
        reply = validate_reply(self.store, principal, packed, extractive_reply(packed))
        return {'reply': reply, 'context': packed, 'cache_hit': hit}
