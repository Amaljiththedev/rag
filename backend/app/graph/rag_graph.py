from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from app.retrieval.hybrid import HybridRetriever
from app.generation.llm import LLMClient
from app.generation.prompts import RAG_SYSTEM_PROMPT
from app.generation.guardrails import GuardrailsEngine

class RAGState(TypedDict):
    question: str
    chunks: List[Dict[str, Any]]
    answer: str
    confidence_score: float
    refused: bool

class RAGGraphPipeline:
    def __init__(self, db_session: AsyncSession):
        self.retriever = HybridRetriever(db_session)
        self.llm = LLMClient()
        self.guardrails = GuardrailsEngine()

    async def retrieve_step(self, state: RAGState) -> RAGState:
        chunks = await self.retriever.search(state["question"], top_k=5)
        passed, confidence = self.guardrails.evaluate_retrieval(chunks)
        state["chunks"] = chunks
        state["confidence_score"] = confidence
        state["refused"] = not passed
        return state

    async def generate_step(self, state: RAGState) -> RAGState:
        if state["refused"]:
            state["answer"] = "I cannot answer this question as no relevant context was found."
            return state

        context_str = "\n\n".join([f"[{c['filename']} p.{c['chunk_index']}]: {c['content']}" for c in state["chunks"]])
        prompt = RAG_SYSTEM_PROMPT.format(context=context_str, question=state["question"])
        state["answer"] = await self.llm.generate(prompt)
        return state

    def build_graph(self):
        workflow = StateGraph(RAGState)
        workflow.add_node("retrieve", self.retrieve_step)
        workflow.add_node("generate", self.generate_step)

        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile()
