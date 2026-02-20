def human_select_idea_node(state: CreativeState):
    print("\nTop Ideas:\n")
    for i, idea in enumerate(state["ranked_ideas"][:5]):
        print(i, idea["title"], idea["score"])
    selected = input("Select idea index: ")
    return {
        "selected_idea": state["ranked_ideas"][int(selected)],
        "approval_stage": "idea_selected"
    }


def human_script_approval_node(state: CreativeState):
    print("\nTop Script:\n")
    print(state["scored_variants"][0]["content"])
    decision = input("Approve? (y/n): ")
    if decision == "y":
        return {"selected_script": state["scored_variants"][0]}
    else:
        feedback = input("Provide feedback: ")
        return {"human_feedback": feedback}