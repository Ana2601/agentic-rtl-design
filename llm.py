"""NVIDIA NIM LLM client (OpenAI-compatible)."""
import os

from openai import OpenAI

BASE_URL = "https://integrate.api.nvidia.com/v1"

DEFAULT_MODEL = "nvidia/llama-3.1-nemotron-nano-8b-v1"
DEFAULT_CRITIC = "openai/gpt-oss-20b"


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        critic_model: str | None = None,
        temperature: float = 0.2,
    ):
        api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError(
                "NVIDIA_API_KEY not set. Run: export NVIDIA_API_KEY=nvapi-..."
            )
        self.client = OpenAI(base_url=BASE_URL, api_key=api_key)
        self.model = model or os.environ.get("LLM_MODEL", DEFAULT_MODEL)
        self.critic_model = critic_model or os.environ.get(
            "LLM_MODEL_CRITIC", DEFAULT_CRITIC
        )
        self.temperature = temperature

    def chat(self, system: str, user: str, model: str | None = None) -> str:
        """Single chat completion, returns assistant text."""
        resp = self.client.chat.completions.create(
            model=model or self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    def critique(self, system: str, user: str) -> str:
        """Run the reviewer pass with the critic model."""
        return self.chat(system, user, model=self.critic_model)
