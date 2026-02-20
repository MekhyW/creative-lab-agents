def memory_pull_node(state: CreativeState):
    query = state["theme"] or "creative video idea"
    results = vector_store.similarity_search(query, k=8)
    return {"memory_context": [r.page_content for r in results]}