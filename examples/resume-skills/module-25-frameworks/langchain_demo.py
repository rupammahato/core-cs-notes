"""Actual LCEL and create_agent; fake/scripted responses, no provider inference."""
import json
from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from domain import Answer, Principal, accept_citations, retrieve


class LocalTrace(BaseCallbackHandler):
    def __init__(self):
        self.events = []

    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.events.append({'event': 'model_start', 'message_count': len(messages[0])})

    def on_llm_end(self, response, **kwargs):
        self.events.append({'event': 'model_end'})


def make_chain(principal, response):
    def prepare(inputs):
        evidence = retrieve(principal, inputs['question'])
        if not evidence:
            raise LookupError('No eligible evidence')
        return {'question': inputs['question'], 'context': json.dumps(evidence)}

    parser = PydanticOutputParser(pydantic_object=Answer)
    prompt = ChatPromptTemplate.from_messages([
        ('system', 'Use only the supplied evidence. Return answer and citations as JSON.'),
        ('human', 'Question: {question}\nEvidence: {context}'),
    ])
    return (RunnableLambda(prepare).with_config(run_name='authorized_retrieval')
            | prompt | FakeListChatModel(responses=[response]) | parser)


def checked_chain_answer(chain, principal, question, config=None):
    answer = chain.invoke({'question': question}, config=config)
    return accept_citations(answer, retrieve(principal, question))


def stream_fixture():
    return (FakeListChatModel(responses=['local-stream']) | StrOutputParser())


@tool
def read_note(topic: str, runtime: ToolRuntime[Principal], limit: int = 2) -> str:
    """Read current notes matching a topic for the authenticated user."""
    return json.dumps(retrieve(runtime.context, topic, limit))


class ScriptedToolModel(BaseChatModel):
    """Return predetermined tool calls; bind_tools does not contact a provider."""
    mode: str = 'normal'

    @property
    def _llm_type(self):
        return 'placement-scripted-tool-model'

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if self.mode == 'loop' or not any(isinstance(m, ToolMessage) for m in messages):
            args = {'topic': 'session', 'limit': 2}
            name = 'read_note'
            if self.mode == 'bad_limit':
                args['limit'] = 99
            if self.mode == 'unknown':
                name = 'not_registered'
            message = AIMessage(content='', tool_calls=[{
                'name': name, 'args': args, 'id': 'call-' + str(len(messages)), 'type': 'tool_call',
            }])
        else:
            message = AIMessage(content='Scripted final reply: ' + messages[-1].content)
        return ChatResult(generations=[ChatGeneration(message=message)])


def make_agent(mode='normal'):
    return create_agent(model=ScriptedToolModel(mode=mode), tools=[read_note], context_schema=Principal,
                        system_prompt='Use the read-only note tool; this is a scripted local fixture.')
