import json
import yaml
from typing import Any, Dict, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI


@dataclass
class ModelConfig:
    name: str
    temperature: float
    max_tokens: int


class LLMService:
    """
    Centralized LLM router.
    Routes different creative roles to different models + configs.
    """

    @staticmethod
    def load_config_from_yaml(file_path: str) -> Dict[str, ModelConfig]:
        with open(file_path, "r") as f:
            raw_config = yaml.safe_load(f)
        return { role: ModelConfig(name=cfg["name"], temperature=cfg["temperature"], max_tokens=cfg["max_tokens"]) for role, cfg in raw_config.items() }

    def __init__(self, api_key: str, model_map: Dict[str, ModelConfig]):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_map = model_map

    async def _chat(self, role: str, system_prompt: str, user_prompt: str, response_format: Optional[Dict[str, Any]] = None) -> Any:
        config = self.model_map[role]
        try:
            response = await self.client.chat.completions.create(
                model=config.name,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=response_format,
            )
            content = response.choices[0].message.content
            usage = response.usage
            print(f"[LLM] role={role} tokens={usage.total_tokens}")
            return content
        except Exception as e:
            print(f"[LLM ERROR] {e}")
            raise

    async def generate_text(self, role: str, system_prompt: str, user_prompt: str) -> str:
        return await self._chat(role, system_prompt, user_prompt)

    async def generate_json(self, role: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        raw = await self._chat(role, system_prompt, user_prompt, response_format={"type": "json_object"})
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print("[LLM WARNING] JSON parsing failed, retrying once...")
            retry = await self._chat(role, system_prompt, user_prompt + "\n\nReturn valid JSON only.", response_format={"type": "json_object"})
            return json.loads(retry)