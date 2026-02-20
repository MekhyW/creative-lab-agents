from typing import List, Dict, Any


class TrendService:
    """
    Abstract trend ingestion layer.
    Replace stub fetchers with real API integrations later.
    """

    def __init__(self, llm_service):
        self.llm = llm_service

    async def fetch_raw_trends(self) -> List[Dict[str, Any]]:
        """
        Stub: replace with real sources
        - TikTok Creative Center scraping
        - YouTube trending API
        - Twitter/X trends
        """

        # Placeholder
        return [
            {"topic": "AI in everyday tools", "engagement": 92},
            {"topic": "Retro tech nostalgia", "engagement": 88},
            {"topic": "Behind the scenes builds", "engagement": 95},
        ]

    async def analyze_trends(self, creator_identity_summary: str) -> List[Dict[str, Any]]:
        raw = await self.fetch_raw_trends()
        system_prompt = """
        You are a trend analyst.
        Score trends for:
        - Alignment with creator identity
        - Novelty potential
        - Saturation risk
        Return structured JSON.
        """
        user_prompt = f"""
        Creator identity:
        {creator_identity_summary}

        Trends:
        {raw}
        """
        analysis = await self.llm.generate_json(role="utility", system_prompt=system_prompt, user_prompt=user_prompt)
        return analysis