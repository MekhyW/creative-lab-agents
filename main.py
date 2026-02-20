import asyncio
import os
from typing import Dict, Any
from services.llm import LLMService, ModelConfig
from services.memory_service import MemoryService
from services.trend_service import TrendService
from graph.build_graph import build_graph


# -----------------------------
# CONFIGURATION
# -----------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_PATH = "./chroma_db"

MODEL_MAP = {
    "brainstorm": ModelConfig(
        name="gpt-4o-mini",
        temperature=0.9,
        max_tokens=1200,
    ),
    "critic": ModelConfig(
        name="gpt-4o",
        temperature=0.2,
        max_tokens=1000,
    ),
    "script": ModelConfig(
        name="gpt-4o",
        temperature=0.7,
        max_tokens=2000,
    ),
    "utility": ModelConfig(
        name="gpt-4o-mini",
        temperature=0.3,
        max_tokens=800,
    ),
}


# -----------------------------
# HUMAN INPUT HELPERS
# -----------------------------

def ask_theme() -> str:
    print("\n=== NEW CREATIVE SESSION ===")
    return input("Theme (or blank for exploration mode): ").strip()


def ask_constraints() -> list:
    print("\nEnter constraints (empty line to finish):")
    constraints = []
    while True:
        c = input("> ").strip()
        if not c:
            break
        constraints.append(c)
    return constraints


def summarize_identity(memory_service: MemoryService) -> str:
    """
    Pull representative samples from memory
    to generate creator identity summary.
    """
    samples = memory_service.retrieve_context(
        query="creator identity style personality themes",
        k=5,
    )
    summary = "\n\n".join([s["content"][:500] for s in samples])
    return summary


# -----------------------------
# INITIAL STATE BUILDER
# -----------------------------

def build_initial_state(theme: str, constraints: list) -> Dict[str, Any]:
    return {
        "theme": theme if theme else None,
        "constraints": constraints,
        "memory_context": [],
        "trend_signals": [],
        "idea_pool": [],
        "ranked_ideas": [],
        "selected_idea": None,
        "script_variants": [],
        "scored_variants": [],
        "selected_script": None,
        "critique_log": [],
        "iteration_count": 0,
        "human_feedback": None,
        "approval_stage": None,
        "final_package": None,
    }


# -----------------------------
# MAIN RUNNER
# -----------------------------

async def run_session():
    llm_service = LLMService(api_key=OPENAI_API_KEY, model_map=MODEL_MAP)
    memory_service = MemoryService(persist_directory=CHROMA_PATH, embedding_api_key=OPENAI_API_KEY)
    trend_service = TrendService(llm_service)
    app = build_graph(llm_service=llm_service, memory_service=memory_service, trend_service=trend_service)
    theme = ask_theme()
    constraints = ask_constraints()
    identity_summary = summarize_identity(memory_service)
    state = build_initial_state(theme, constraints)
    state["identity_summary"] = identity_summary
    print("\nRunning creative graph...\n")
    async for event in app.astream_events(state, version="v1"):
        if event["event"] == "on_node_end":
            node_name = event["name"]
            print(f"\n[Node Complete] {node_name}")
        if event["event"] == "on_chain_end":
            updated_state = event["data"]["output"]
            if updated_state.get("approval_stage") == "idea_selected":
                print("\nIdea locked in.\n")
            if updated_state.get("selected_script"):
                print("\nScript candidate ready.\n")
                print(updated_state["selected_script"])
                decision = input("\nApprove script? (y/n): ")
                if decision.lower() != "y":
                    feedback = input("Provide feedback: ")
                    updated_state["human_feedback"] = feedback
                    updated_state["iteration_count"] += 1
                    print("\nRe-entering refinement loop...\n")
                    await app.ainvoke(updated_state)
                    return
            state = updated_state
    print("\n=== FINAL CREATIVE PACKAGE ===\n")
    print(state["final_package"])
    print("\nSession complete.\n")


# -----------------------------
# ENTRYPOINT
# -----------------------------

if __name__ == "__main__":
    asyncio.run(run_session())