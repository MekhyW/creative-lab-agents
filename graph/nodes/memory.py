from graph.state import CreativeState

def memory_pull_node(memory_service):
    def node(state: CreativeState):
        query = state["theme"] or "creative video idea"
        results = memory_service.retrieve_context(query, k=8)
        return {"memory_context": results}
    return node