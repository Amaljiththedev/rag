import os
from dotenv import load_dotenv
from groq import Groq
from backend.app.retrieval.search import hybrid_search

load_dotenv()
client = Groq()

MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

PROMPT_TEMPLATE = """You are a helpful assistant answering questions about SEC filings.

Use ONLY the numbered context chunks below to answer the question.
- Cite the chunk number(s) you used, like [1] or [2], after each fact.
- If the answer is not in the context, say exactly: "I could not find this in the provided documents."
- Do not use any outside knowledge.

Context:
{context}

Question: {question}

Answer:"""


def generate_answer(question: str, top_k: int = 5) -> dict:
    # Step 1: retrieve
    chunks = hybrid_search(question, top_k=top_k)

    # Step 2: build the numbered context block
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(f"[{i}] (Section: {chunk['section']})\n{chunk['content']}")
    context = "\n\n".join(context_parts)

    # Step 3: build the full prompt
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)

    # Step 4: call the LLM (non-streaming for easy testing)
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,  # 0 = deterministic, factual — important for RAG
    )
    answer = completion.choices[0].message.content

    # Step 5: return answer + the sources it was given
    return {
        "question": question,
        "answer": answer,
        "sources": [{"n": i, "chunk_id": c["chunk_id"], "section": c["section"]}
                    for i, c in enumerate(chunks, start=1)]
    }


if __name__ == "__main__":
    import sys
    result = generate_answer("What was Apple's revenue from its coffee shop division in 2013?")
    
    def safe_print(text: str):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii', 'ignore').decode('ascii'))

    safe_print(f"QUESTION: {result['question']}")
    safe_print(f"\nANSWER:\n{result['answer']}")
    safe_print("\nSOURCES:")
    for s in result["sources"]:
        safe_print(f"  [{s['n']}] {s['section']} ({s['chunk_id']})")
