from typing import List, Dict, Any


class TrendService:
    """
    WIP Trend ingestion layer that simulates real-world research.
    """

    def __init__(self, llm_service):
        self.llm = llm_service

    async def fetch_raw_trends(self, theme: str = None) -> List[Dict[str, Any]]:
        """
        Simulates fetching trending topics.
        """
        # Simulation of trending topics
        topics = [
            {"topic": "AI-powered storytelling", "relevance": 92},
            {"topic": "Retro tech nostalgia", "relevance": 88},
            {"topic": "Minimalist workspace setups", "relevance": 85},
            {"topic": "Nostalgic tech restorations", "relevance": 95}
        ]
        return topics

    async def analyze_trends(self, creator_identity_summary: str, trend_data: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        raw = trend_data or await self.fetch_raw_trends()
        system_prompt = """
        You are a trend analyst.
        Score trends for:
        - Alignment with creator identity
        - Novelty potential
        - Saturation risk
        Return structured JSON list of objects with 'topic', 'score', and 'rationale'.
        """
        user_prompt = f"""
        Creator identity:
        {creator_identity_summary}

        Trends:
        {raw}
        """
        analysis = await self.llm.generate_json(role="utility", system_prompt=system_prompt, user_prompt=user_prompt)
        return analysis