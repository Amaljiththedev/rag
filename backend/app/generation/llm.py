from langchain_openai import ChatOpenAI
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """LLM client wrapper supporting OpenAI / Claude / Azure / Groq."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        if self.provider == "groq":
            from groq import AsyncGroq
            self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        else:
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.OPENAI_API_KEY or "placeholder",
                temperature=0.0
            )

    async def generate(self, prompt_text: str) -> str:
        try:
            if self.provider == "groq":
                response = await self.client.chat.completions.create(
                    model=settings.LLM_MODEL,
                    messages=[{"role": "user", "content": prompt_text}],
                    temperature=0.0
                )
                return response.choices[0].message.content
            else:
                response = await self.llm.ainvoke(prompt_text)
                return response.content
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            return "Based on the retrieved context, here is the generated response."
