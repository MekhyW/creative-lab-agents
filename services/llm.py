import json
import yaml
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from openai import AsyncOpenAI
import google.genai as genai
from google.genai import types as genai_types


def _is_gemini(model_name: str) -> bool:
    return model_name.startswith("gemini")


@dataclass
class ModelConfig:
    name: str
    temperature: float
    max_tokens: int
    provider: str = field(init=False)
    def __post_init__(self):
        self.provider = "google" if _is_gemini(self.name) else "openai"


class LLMService:
    """
    Centralized LLM router.
    Routes different creative roles to different models + configs.
    Supports OpenAI (GPT) and Google (Gemini) providers, determined
    automatically from the model name in models.yaml.
    """

    @staticmethod
    def load_config_from_yaml(file_path: str) -> Dict[str, ModelConfig]:
        with open(file_path, "r") as f:
            raw_config = yaml.safe_load(f)
        return {
            role: ModelConfig(name=cfg["name"], temperature=cfg["temperature"], max_tokens=cfg["max_tokens"])
            for role, cfg in raw_config.items()
        }

    def __init__(self, api_key: str, model_map: Dict[str, ModelConfig], google_api_key: str = ""):
        self.openai_client = AsyncOpenAI(api_key=api_key)
        self.google_api_key = google_api_key
        self.model_map = model_map
        if google_api_key:
            self._google_client = genai.Client(api_key=google_api_key)
        else:
            self._google_client = None

    async def _chat_openai(self, config: ModelConfig, system_prompt: str, user_prompt: str, response_format: Optional[Dict[str, Any]] = None) -> str:
        response = await self.openai_client.chat.completions.create(
            model=config.name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            response_format=response_format,
        )
        usage = response.usage
        print(f"[LLM/OpenAI] model={config.name} tokens={usage.total_tokens}")
        return response.choices[0].message.content

    async def _chat_google(self, config: ModelConfig, system_prompt: str, user_prompt: str, want_json: bool = False) -> str:
        if self._google_client is None:
            raise RuntimeError("Google API key not configured. Set GOOGLE_API_KEY in .env")
        gen_config = genai_types.GenerateContentConfig(temperature=config.temperature, max_output_tokens=config.max_tokens, system_instruction=system_prompt, response_mime_type="application/json" if want_json else "text/plain")
        response = await self._google_client.aio.models.generate_content(model=config.name, contents=user_prompt, config=gen_config)
        text = response.text
        print(f"[LLM/Google] model={config.name} chars={len(text)}")
        return text

    async def _chat(role: str, system_prompt: str, user_prompt: str, response_format: Optional[Dict[str, Any]] = None, want_json: bool = False) -> Any:
        config = self.model_map[role]
        try:
            if config.provider == "google":
                return await self._chat_google(config, system_prompt, user_prompt, want_json=want_json)
            else:
                return await self._chat_openai(config, system_prompt, user_prompt, response_format=response_format)
        except Exception as e:
            print(f"[LLM ERROR] role={role} provider={config.provider}: {e}")
            raise

    async def generate_text(self, role: str, system_prompt: str, user_prompt: str) -> str:
        return await self._chat(role, system_prompt, user_prompt)

    async def generate_json(self, role: str, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        raw = await self._chat(role, system_prompt, user_prompt, response_format={"type": "json_object"}, want_json=True)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            print("[LLM WARNING] JSON parsing failed, retrying once...")
            retry = await self._chat(
                role,
                system_prompt,
                user_prompt + "\n\nReturn valid JSON only.",
                response_format={"type": "json_object"},
                want_json=True,
            )
            return json.loads(retry)