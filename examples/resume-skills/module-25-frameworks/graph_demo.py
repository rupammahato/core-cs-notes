"""Actual checkpointed graph with review, revalidation, and a replay-safe local write."""
from dataclasses import dataclass
from operator import add
from typing import Annotated, TypedDict
from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from langgraph.types import interrupt
from domain import Decision, Principal, draft_hash
from repository import Repository


class State(TypedDict, total=False):
    job_id: str
    question: str
    evidence: list[dict]
    draft: str
    draft_hash: str
    approved: bool
    status: str
    events: Annotated[list[str], add]


@dataclass
class RunContext:
    principal: Principal
    repo: Repository
    fail_after_commit: bool = False


def build_graph(checkpointer):
    def retrieve_node(state: State, runtime: Runtime[RunContext]):
        ctx = runtime.context
        evidence = ctx.repo.retrieve(state['job_id'], ctx.principal, state['question'])
        return {'evidence': evidence, 'status': 'retrieved' if evidence else 'no_evidence', 'events': ['retrieve']}

    def draft_node(state: State):
        # Extractive, deterministic draft; no language model is called.
        draft = state['evidence'][0]['text']
        return {'draft': draft, 'draft_hash': draft_hash(state['job_id'], draft, state['evidence']),
                'status': 'awaiting_review', 'events': ['draft']}

    def review_node(state: State, runtime: Runtime[RunContext]):
        ctx = runtime.context
        ctx.repo.authorize(state['job_id'], ctx.principal)
        # Instrumentation deliberately before interrupt: this runs again on resume.
        ctx.repo.attempt(state['job_id'], 'review')
        value = interrupt({'job_id': state['job_id'], 'draft': state['draft'], 'draft_hash': state['draft_hash']})
        decision = Decision.model_validate(value)
        if decision.draft_hash != state['draft_hash']:
            raise ValueError('Approval belongs to another draft')
        return {'approved': decision.approved, 'status': 'approved' if decision.approved else 'rejected', 'events': ['review']}

    def commit_node(state: State, runtime: Runtime[RunContext]):
        ctx = runtime.context
        ctx.repo.attempt(state['job_id'], 'commit')
        accepted = ctx.repo.commit_result(state['job_id'], ctx.principal, state['evidence'], state['draft_hash'], state['draft'])
        if accepted and ctx.fail_after_commit:
            raise RuntimeError('Injected failure after canonical commit, before graph checkpoint')
        return {'status': 'committed' if accepted else 'stale_source', 'events': ['commit']}

    builder = StateGraph(State, context_schema=RunContext)
    builder.add_node('retrieve', retrieve_node)
    builder.add_node('draft', draft_node)
    builder.add_node('review', review_node)
    builder.add_node('commit', commit_node)
    builder.add_edge(START, 'retrieve')
    builder.add_conditional_edges('retrieve', lambda state: 'draft' if state['evidence'] else END)
    builder.add_edge('draft', 'review')
    builder.add_conditional_edges('review', lambda state: 'commit' if state['approved'] else END)
    builder.add_edge('commit', END)
    return builder.compile(checkpointer=checkpointer)
