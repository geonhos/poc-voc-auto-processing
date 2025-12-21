"""
LLM Service - Provider abstraction layer
"""

from typing import Optional, Dict, Any
from langchain_community.llms import Ollama
from langchain.schema import BaseMessage, HumanMessage, SystemMessage
from app.config import settings


class LLMService:
    """LLM service abstraction layer"""

    def __init__(self):
        """Initialize LLM service with Ollama"""
        self.llm = Ollama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.1,  # Low temperature for consistent outputs
        )

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate text using LLM

        Args:
            system_prompt: System instruction
            user_prompt: User input
            temperature: Override default temperature

        Returns:
            Generated text
        """
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # Override temperature if provided
        if temperature is not None:
            self.llm.temperature = temperature

        # Generate
        response = await self.llm.ainvoke(full_prompt)

        return response

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate JSON output using LLM

        Args:
            system_prompt: System instruction (should specify JSON format)
            user_prompt: User input
            temperature: Override default temperature

        Returns:
            Generated JSON string (needs parsing)
        """
        response = await self.generate(system_prompt, user_prompt, temperature)
        return response


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get singleton LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
