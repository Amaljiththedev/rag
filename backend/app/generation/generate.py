import os

from dotenv import load_dotenv
from groq import Groq

from app.retrieval.search import hybrid_search

load_dotenv()

MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

REFUSAL = "I could not find this in the provided documents."

PROMPT_TEMPLATE = """You are a helpful assistant answering questions about the user's uploaded documents.

Use ONLY the numbered context chunks below to answer the question.
- Cite the chunk number(s) you used, like [1] or [2], after each fact.
- If the answer is not in the context, say exactly: "{refusal}"
- Do not use any outside knowledge.

Context:
{context}

Question: {question}

Answer:"""

_client = None


def get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq()
    return _client


def _noop_progress(stage: str, message: str, **extra) -> None:
    print(f"[{stage}] {message}")


def generate_answer(
    question: str,
    document_set_id: str,
    top_k: int = 5,
    on_progress=None,
) -> dict:
    """Answer a question using only the chunks belonging to document_set_id."""
    if not document_set_id:
        raise ValueError("generate_answer requires a document_set_id.")

    progress = on_progress or _noop_progress

    chunks = hybrid_search(question, document_set_id, top_k=top_k)
    progress("retrieving", f"Found {len(chunks)} relevant passages", chunks=len(chunks))

    if not chunks:
        return {
            "question": question,
            "answer": REFUSAL,
            "refused": True,
            "sources": [],
        }

    context = "\n\n".join(
        f"[{i}] (Section: {chunk['section']})\n{chunk['content']}"
        for i, chunk in enumerate(chunks, start=1)
    )
    prompt = PROMPT_TEMPLATE.format(refusal=REFUSAL, context=context, question=question)

    progress("generating", "Writing the answer")
    completion = get_client().chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    answer = completion.choices[0].message.content

    # Chunks were retrieved but none answered the question. Citing them anyway
    # would imply the refusal came from them.
    refused = REFUSAL.rstrip(".") in (answer or "")

    return {
        "question": question,
        "answer": answer,
        "refused": refused,
        "sources": []
        if refused
        else [
            {"n": i, "chunk_id": c["chunk_id"], "section": c["section"]}
            for i, c in enumerate(chunks, start=1)
        ],
    }
