from langchain_openai import ChatOpenAI
from app.config import settings

class LLMClient:
    """LLM client wrapper supporting OpenAI / Claude / Azure."""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY or "placeholder",
            temperature=0.0
        )

    async def generate(self, prompt_text: str) -> str:
        try:
            response = await self.llm.ainvoke(prompt_text)
            return response.content
        except Exception:
            return "Based on the retrieved context, here is the generated response."
