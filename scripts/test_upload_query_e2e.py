"""End-to-end proof: upload a PDF -> get a document_set_id -> query only that set.

Run from the repo root:
    set PYTHONPATH=backend && python scripts/test_upload_query_e2e.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

import psycopg2
from fastapi.testclient import TestClient

from app.main import app
from app.retrieval.search import DB_CONFIG


def drop_sets(set_ids: list[str]):
    """Remove only the sets this test created, so repeat runs don't accumulate rows."""
    set_ids = [s for s in set_ids if s]
    if not set_ids:
        return
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM chunks WHERE document_set_id = ANY(%s);", (set_ids,))
                chunks_deleted = cur.rowcount
                # The document_sets row drives the sidebar; leaving it behind
                # would show a workspace with no content after every test run.
                cur.execute(
                    "DELETE FROM document_sets WHERE document_set_id = ANY(%s);",
                    (set_ids,),
                )
                print(
                    f"[test] cleaned up {chunks_deleted} chunks and "
                    f"{cur.rowcount} set record(s) from {len(set_ids)} test set(s)"
                )
    finally:
        conn.close()

SAMPLE_TEXT = [
    "Northwind Robotics — Fiscal Year 2024 Annual Summary",
    "",
    "Northwind Robotics designs autonomous warehouse sorting arms.",
    "Total revenue for fiscal year 2024 was 87.4 million dollars.",
    "Research and development expense for fiscal year 2024 was 19.2 million dollars.",
    "The company employed 412 people at the end of the fiscal year.",
    "Headquarters are located in Tampere, Finland.",
    "The flagship product is the NW-9 sorting arm, which shipped 1,340 units in 2024.",
    "Gross margin for the year was 61 percent.",
    "The board approved a share buyback program of 5 million dollars in November 2024.",
]

DECOY_TEXT = [
    "Southgate Bakery — Fiscal Year 2024 Annual Summary",
    "",
    "Southgate Bakery operates twelve retail bakery locations.",
    "Total revenue for fiscal year 2024 was 3.1 million dollars.",
    "The company employed 58 people at the end of the fiscal year.",
    "Headquarters are located in Leeds, United Kingdom.",
]


def make_pdf(path: str, lines: list[str]) -> str:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER
    y = height - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 20
    c.showPage()
    c.save()
    print(f"[test] built sample PDF: {path}")
    return path


def banner(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    created_sets = []
    try:
        run_checks(created_sets)
    finally:
        drop_sets(created_sets)


def run_checks(created_sets: list[str]):
    client = TestClient(app)
    tmp_dir = tempfile.mkdtemp(prefix="rag_e2e_")
    failures = []

    main_pdf = make_pdf(os.path.join(tmp_dir, "northwind_robotics_2024.pdf"), SAMPLE_TEXT)
    decoy_pdf = make_pdf(os.path.join(tmp_dir, "southgate_bakery_2024.pdf"), DECOY_TEXT)

    # ---- 1. Upload -------------------------------------------------------
    banner("STEP 1 — POST /upload")
    with open(main_pdf, "rb") as f:
        resp = client.post(
            "/upload",
            files={"file": ("northwind_robotics_2024.pdf", f, "application/pdf")},
        )
    if resp.status_code != 201:
        print(f"[FAIL] upload returned {resp.status_code}: {resp.text}")
        sys.exit(1)

    upload = resp.json()
    document_set_id = upload["document_set_id"]
    created_sets.append(document_set_id)
    print(f"  document_set_id: {document_set_id}")
    print(f"  filename:        {upload['filename']}")
    print(f"  chunks_created:  {upload['chunks_created']}")
    if upload["chunks_created"] < 1:
        failures.append("upload created zero chunks")

    # ---- 2. Query that set ----------------------------------------------
    banner("STEP 2 — POST /query (same set)")
    question = "What was total revenue and R&D expense in fiscal year 2024?"
    resp = client.post("/query", json={"document_set_id": document_set_id, "question": question})
    if resp.status_code != 200:
        print(f"[FAIL] query returned {resp.status_code}: {resp.text}")
        sys.exit(1)

    result = resp.json()
    print(f"  QUESTION: {result['question']}\n")
    print(f"  ANSWER:\n{result['answer']}\n")
    print("  EVIDENCE:")
    for e in result["evidence"]:
        location = " · ".join(filter(None, [e.get("section"), e.get("page_label")]))
        print(f"    [{e['n']}] {e['document']} — {location or 'no section'}")

    if "87.4" not in result["answer"]:
        failures.append("answer did not contain the revenue figure 87.4")
    if "19.2" not in result["answer"]:
        failures.append("answer did not contain the R&D figure 19.2")
    if not result["evidence"]:
        failures.append("answer returned no evidence")
    # Evidence must be citable: a page reference on every passage.
    if not all(e.get("page_label") for e in result["evidence"]):
        failures.append("some evidence had no page reference")

    # ---- 3. Isolation ----------------------------------------------------
    banner("STEP 3 — isolation: a second set must not see the first")
    with open(decoy_pdf, "rb") as f:
        resp = client.post(
            "/upload",
            files={"file": ("southgate_bakery_2024.pdf", f, "application/pdf")},
        )
    other_set_id = resp.json()["document_set_id"]
    created_sets.append(other_set_id)
    print(f"  second document_set_id: {other_set_id}")

    resp = client.post(
        "/query",
        json={"document_set_id": other_set_id, "question": "What was Northwind Robotics' revenue in 2024?"},
    )
    other_answer = resp.json()["answer"]
    print(f"\n  ANSWER FROM OTHER SET:\n{other_answer}\n")
    leaked = [
        c["chunk_id"]
        for c in resp.json()["evidence"]
        if not c["chunk_id"].startswith(other_set_id)
    ]
    if leaked:
        failures.append(f"chunks leaked across sets: {leaked}")
    if "87.4" in other_answer:
        failures.append("other set's answer leaked the 87.4 revenue figure")

    # ---- 4. Unknown set is rejected -------------------------------------
    banner("STEP 4 — unknown document_set_id is rejected")
    resp = client.post("/query", json={"document_set_id": "does-not-exist", "question": "anything?"})
    print(f"  status: {resp.status_code}")
    print(f"  detail: {resp.json().get('detail')}")
    if resp.status_code != 404:
        failures.append(f"expected 404 for unknown set, got {resp.status_code}")

    # ---- Result ----------------------------------------------------------
    banner("RESULT")
    if failures:
        for f_ in failures:
            print(f"  [FAIL] {f_}")
        sys.exit(1)
    print("  All checks passed — upload -> query loop works and sets are isolated.")


if __name__ == "__main__":
    main()
