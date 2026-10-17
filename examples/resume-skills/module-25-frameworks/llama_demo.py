"""Actual LlamaIndex pipeline/index/query engine with a handwritten feature encoder."""
import re
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from domain import NOTES


class FeatureEmbedding(BaseEmbedding):
    """Three word-count features; not a trained semantic embedding model."""
    model_name: str = 'handwritten-session-index-deployment-v1'

    def _encode(self, text):
        words = re.findall(r'[a-z]+', text.lower())
        return [float(words.count(term)) + 0.01 for term in ('session', 'index', 'deployment')]

    def _get_query_embedding(self, query):
        return self._encode(query)

    async def _aget_query_embedding(self, query):
        return self._encode(query)

    def _get_text_embedding(self, text):
        return self._encode(text)


def splitter():
    # Words are the fixture's counting units; no BPE/NLTK/provider tokenizer.
    return SentenceSplitter(chunk_size=64, chunk_overlap=8, tokenizer=str.split,
                            chunking_tokenizer_fn=lambda text: [text],
                            id_func=lambda ordinal, doc: f'{doc.doc_id}:c{ordinal}')


def build_index():
    Settings.tokenizer = str.split
    encoder = FeatureEmbedding()
    documents = [Document(id_=note['id'], text=note['text'],
                          metadata={'tenant': note['tenant'], 'revision': note['revision']},
                          excluded_embed_metadata_keys=['tenant', 'revision'],
                          excluded_llm_metadata_keys=['tenant', 'revision']) for note in NOTES]
    pipeline = IngestionPipeline(transformations=[splitter(), encoder])
    nodes = pipeline.run(documents=documents, show_progress=False)
    index = VectorStoreIndex(nodes, embed_model=encoder, show_progress=False)
    return documents, nodes, index, encoder


def retriever_for(index, principal, top_k=2):
    if not principal.can_read or principal.tenant not in ('alpha', 'beta'):
        raise PermissionError('Read permission denied')
    return index.as_retriever(similarity_top_k=top_k, filters=MetadataFilters(filters=[
        MetadataFilter(key='tenant', value=principal.tenant), MetadataFilter(key='revision', value=1),
    ]))


def query_engine(index, principal):
    return RetrieverQueryEngine.from_args(retriever_for(index, principal), llm=MockLLM(max_tokens=3),
        response_mode='simple_summarize', node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.8)])


def restore_index(folder, encoder):
    return load_index_from_storage(StorageContext.from_defaults(persist_dir=str(folder)), embed_model=encoder)
