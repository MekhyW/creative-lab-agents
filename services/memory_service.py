import os
from typing import List, Dict, Any
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

    def retrieve_context(self, query: str, k: int = 8) -> List[Dict[str, Any]]:
        results = self.vectorstore.similarity_search_with_score(query, k=k * 4) # Increase initial search space for diversification
        diversified = []
        seen_sources = set()
        for doc, score in results:
            metadata = doc.metadata or {}
            source = metadata.get("source", "unknown") # Use source file for diversification
            if source in seen_sources:
                continue
            seen_sources.add(source)
            diversified.append({
                "content": doc.page_content,
                "score": float(score),
                "metadata": metadata,
                "source": os.path.basename(source) if source != "unknown" else "Unknown"
            })
            if len(diversified) >= k:
                break
        return diversified