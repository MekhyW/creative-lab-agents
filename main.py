import asyncio
import os
from typing import Dict, Any
from services.llm import LLMService
from services.memory_service import MemoryService
from services.trend_service import TrendService
from graph.build_graph import build_graph
from dotenv import load_dotenv

load_dotenv()

# -----------------------------
# CONFIGURATION
# -----------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
VAULT_PATH = os.getenv("VAULT_PATH", "./my_vault")
MODELS_CONFIG_PATH = os.path.join("config", "models.yaml")

# -----------------------------
# HUMAN INPUT HELPERS
# -----------------------------

def ask_theme() -> str:
    print("\n=== TREND SCOUTER SESSION ===")
    return input("Target Topic/Theme: ").strip()


def ask_constraints() -> list:
    print("\nEnter constraints (e.g. 'under 60s', 'no voiceover') - empty line to finish:")
    constraints = []
    while True:
        c = input("> ").strip()
        if not c:
            break
        constraints.append(c)
    return constraints


async def get_identity_summary(memory_service: MemoryService) -> str:
    """
    Summarize creator identity based on vault content.
    """
    samples = memory_service.retrieve_context(query="creator style personality brand themes", k=5)
    if not samples:
        return "A creative content creator looking for fresh angles."
    
    summary = "\n\n".join([s["content"][:400] for s in samples])
    return summary


# -----------------------------
# INITIAL STATE BUILDER
# -----------------------------

def build_initial_state(theme: str, constraints: list, trend_signals: list) -> Dict[str, Any]:
    return {
        "theme": theme,
        "constraints": constraints,
        "memory_context": [],
        "trend_signals": trend_signals,
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
    model_map = LLMService.load_config_from_yaml(MODELS_CONFIG_PATH)
    llm_service = LLMService(api_key=OPENAI_API_KEY, model_map=model_map, google_api_key=GOOGLE_API_KEY)
    memory_service = MemoryService(persist_directory=CHROMA_PATH, embedding_api_key=OPENAI_API_KEY)
    trend_service = TrendService(llm_service)
    app = build_graph(llm_service=llm_service, memory_service=memory_service, trend_service=trend_service)
    theme = ask_theme()
    constraints = ask_constraints()
    
    print("\n[1/3] Fetching and analyzing trends...")
    identity_summary = await get_identity_summary(memory_service)
    trends = await trend_service.analyze_trends(identity_summary)
    
    print("\nIdentified Trend Signals:")
    for i, t in enumerate(trends):
        print(f"{i}. {t['topic']} (Score: {t.get('score', 'N/A')})")
    
    state = build_initial_state(theme, constraints, trends)
    state["identity_summary"] = identity_summary
    
    print("\n[2/3] Running creative divergence...")
    
    async for event in app.astream_events(state, version="v1"):
        if event["event"] == "on_node_end":
            node_name = event["name"]
            print(f"   - Completed: {node_name}")
            
    # Note: Human input nodes will pause and wait for stdin if using input()
    # In a real app, this would be an API call or websocket.

    final_state = await app.ainvoke(state) # For terminal demo
    
    print("\n=== [3/3] FINAL CREATIVE PACKAGE ===")
    if final_state.get("final_package"):
        print(final_state["final_package"])
    else:
        print("No package generated.")

if __name__ == "__main__":
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in environment.")
    else:
        asyncio.run(run_session())