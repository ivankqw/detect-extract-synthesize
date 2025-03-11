from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser, HierarchicalNodeParser
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings, VectorStoreIndex, Document
from llama_index.core.schema import NodeWithScore
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

LLM = "gpt-4-1106-preview"
EMBED_MODEL = "text-embedding-3-large"
EMBED_MODEL = "text-embedding-3-small"
EMBED_SIZE = 3072 # size of the embedding vector


class VectorDB:
    def __init__(self, url: str, api_key: str = None , port: int = None, collection_name: str = "documents"):
        self.collection_name = collection_name
        self.url = url
        self.api_key = api_key
        self.port = port
        if self.port and self.api_key:
            raise ValueError(
                "Only one of two parameters can be set: api_key or port."
            )
        self.local = self.url and self.port and not self.api_key

    def _create_collection_if_not_exists(self):
        if not self.local:
            client = QdrantClient(url=self.url, api_key=self.api_key)
        else:
            # local qdrant
            client = QdrantClient(url=self.url, port=self.port)
        if not client.collection_exists(self.collection_name):
            client.create_collection(collection_name=self.collection_name,
                                     vectors_config=VectorParams(
                                         size=EMBED_SIZE, distance=Distance.COSINE)
                                     )

    def _setup(self):
        self._create_collection_if_not_exists()
        # Set up global llama index settings
        Settings.llm = OpenAI(model=LLM)
        Settings.embed_model = OpenAIEmbedding(model=EMBED_MODEL)

        Settings.node_parser = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=Settings.embed_model
        )
        
        Settings.num_output = 512  
        Settings.context_window = 3900
        if self.local:
            self.index = VectorStoreIndex.from_vector_store(
                QdrantVectorStore(
                    client=QdrantClient(url=self.url, port=self.port), # try this first 
                    collection_name=self.collection_name)
            )
        else:
            self.index = VectorStoreIndex.from_vector_store(
                QdrantVectorStore(
                    url=self.url,
                    api_key=self.api_key,
                    collection_name=self.collection_name)
            )

    def ingest_document(self, id: str, text_from_doc: str, path_to_document: str, page_number: int) -> None:
        document = Document(
            doc_id=id,
            text=text_from_doc,
            metadata={
                "path": path_to_document,
                "doc_id": id,
                "page_number": page_number
            }
        )
        self.index.insert(document)

    # 1 page is 1 document, and add metadata about page number
    def ingest_pitchdeck(self, doc_id: str, page_contents: List[str], path_to_document: str) -> None:
        for i, content in enumerate(page_contents):
            self.ingest_document(doc_id, content, path_to_document, i)


    def retrieve_with_constaints(self, query, doc_id):
        retriever = self.index.as_retriever(
            similarity_top_k=5,
            filters=MetadataFilters(
                filters=[
                    ExactMatchFilter(
                        key="doc_id",
                        value=doc_id,
                    )
                ]
            )
        )
        return retriever.retrieve(query)
        

    def get_relevant_docs(self, query):
        search_results: List[NodeWithScore] = self.retrieve(query)
        metadatas: Dict[str, Any] = [
            result.metadata for result in search_results]
        doc_ids = [metadata["doc_id"] for metadata in metadatas]
        return list(set(doc_ids))

    def get_relevant_texts(self, doc_id, query):

        search_results: List[NodeWithScore] = self.retrieve_with_constaints(
            query, doc_id)
        relevant_context = ""

        # process the context
        for result in search_results:
            page_number = result.metadata.get("page_number")
            text = result.text
            relevant_context += f"""
            OBTAINED FROM PAGE NUMBER {page_number}: 
            {text}
            """
        return relevant_context
