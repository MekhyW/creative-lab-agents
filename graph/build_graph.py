from langgraph.graph import StateGraph, END

graph = StateGraph(CreativeState)

# Add nodes
graph.add_node("memory_pull", memory_pull_node)
graph.add_node("idea_rank", idea_ranking_node)
graph.add_node("critic", critic_node)
graph.add_node("human_idea", human_select_idea_node)
graph.add_node("human_script", human_script_approval_node)
graph.add_node("final_package", final_package_node)

# Parallel idea nodes
for style in ["cinematic", "chaotic", "technical", "meta"]:
    graph.add_node(f"idea_{style}", idea_divergence_node(style))
    graph.add_edge("memory_pull", f"idea_{style}")
    graph.add_edge(f"idea_{style}", "idea_rank")

# Script branches
for style in ["dramatic", "meme", "documentary"]:
    graph.add_node(f"script_{style}", script_split_node(style))
    graph.add_edge("human_idea", f"script_{style}")
    graph.add_edge(f"script_{style}", "critic")

# Routing
graph.add_conditional_edges(
    "critic",
    critic_router,
    {
        "rewrite": "script_dramatic",  # or route dynamically
        "approve": "human_script"
    }
)

graph.add_edge("human_script", "final_package")
graph.add_edge("final_package", END)

graph.set_entry_point("memory_pull")

app = graph.compile()