from typing import List, Dict, Any, Optional
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings


class MemoryService:
    """
    Retrieves contextual memory from vectorized Obsidian vault.
    Designed for creative diversification, not just similarity.
    """

    def __init__(self, persist_directory: str, embedding_api_key: str):
        self.embeddings = OpenAIEmbeddings(openai_api_key=embedding_api_key)
        self.vectorstore = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)

    def retrieve_context(self, query: str, k: int = 8, exclude_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        exclude_ids = exclude_ids or []
        results = self.vectorstore.similarity_search_with_score(query, k=k * 2)
        diversified = []
        seen_formats = set()
        for doc, score in results:
            metadata = doc.metadata or {}
            doc_id = metadata.get("id")
            if doc_id in exclude_ids:
                continue
            format_type = metadata.get("format_type")
            if format_type in seen_formats:
                continue
            seen_formats.add(format_type)
            diversified.append({"content": doc.page_content, "score": score, "metadata": metadata})
            if len(diversified) >= k:
                break
        return diversified