"""Bounded, tenant-scoped graph traversal over hand-authored relations."""
from collections import deque


def reports(tenant, manager_id, people, links, max_nodes=100):
    if max_nodes < 1:
        raise ValueError('Invalid traversal bound')
    if people.get(manager_id) != tenant:
        raise PermissionError('Manager outside tenant')
    adjacency = {}
    for parent, child, kind in links:
        if kind not in ('line', 'escalation'):
            raise ValueError('Unknown relationship type')
        adjacency.setdefault(parent, []).append(child)
    seen, queue, result = {manager_id}, deque([manager_id]), []
    while queue:
        parent = queue.popleft()
        for child in sorted(adjacency.get(parent, [])):
            if people.get(child) != tenant:
                raise PermissionError('Invalid tenant edge')
            if child in seen:
                continue
            if len(seen) >= max_nodes:
                raise ValueError('Traversal bound exceeded; no partial authorization set')
            seen.add(child)
            result.append(child)
            queue.append(child)
    return result
