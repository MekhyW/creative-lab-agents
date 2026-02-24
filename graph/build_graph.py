from langgraph.graph import StateGraph, END
from graph.state import CreativeState
from graph.nodes.memory import memory_pull_node
from graph.nodes.idea import idea_divergence_node, idea_ranking_node
from graph.nodes.human import human_select_idea_node, human_script_approval_node
from graph.nodes.script import script_split_node
from graph.nodes.critic import critic_node, critic_router
from graph.nodes.final import final_package_node

def build_graph(llm_service, memory_service, trend_service):
    builder = StateGraph(CreativeState)

    # Add nodes
    builder.add_node("memory_pull", memory_pull_node(memory_service))
    builder.add_node("idea_rank", idea_ranking_node(llm_service))
    builder.add_node("critic", critic_node(llm_service))
    builder.add_node("human_idea", human_select_idea_node)
    builder.add_node("human_script", human_script_approval_node)
    builder.add_node("final_package", final_package_node)

    # Parallel idea nodes
    for style in ["cinematic", "chaotic", "technical", "meta"]:
        node_id = f"idea_{style}"
        builder.add_node(node_id, idea_divergence_node(style, llm_service))
        builder.add_edge("memory_pull", node_id)
        builder.add_edge(node_id, "idea_rank")

    builder.add_edge("idea_rank", "human_idea")

    # Script branches
    for style in ["dramatic", "meme", "documentary"]:
        node_id = f"script_{style}"
        builder.add_node(node_id, script_split_node(style, llm_service))
        builder.add_edge("human_idea", node_id)
        builder.add_edge(node_id, "critic")

    # Routing
    builder.add_conditional_edges(
        "critic",
        critic_router,
        {
            "rewrite": "human_idea", # Loop back to re-select or refine? 
            # Or to a specific script node. For simplicity, let's say it loops to human_idea to pivot or rethink.
            "approve": "human_script"
        }
    )

    builder.add_edge("human_script", "final_package")
    builder.add_edge("final_package", END)
    builder.set_entry_point("memory_pull")
    return builder.compile()