import sys
sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
import models
import rag_service
import ai_service
import asyncio

def test_chroma_indexing():
    db = SessionLocal()
    try:
        res = rag_service.index_catalog_to_chroma(db)
        print("Indexing Result:", res)
        assert res["status"] == "success"
        assert res["total_documents"] >= 10
    finally:
        db.close()

def test_chroma_semantic_query():
    # 1. Test query for gut health / probiotics
    res1 = rag_service.query_knowledge_base("Which juice is best for gut health and probiotics?", n_results=3)
    docs1 = res1.get("documents", [])
    print("\n--- Semantic Search 1: Gut Health / Probiotics ---")
    for d in docs1:
        print(d[:100] + "...")
    assert len(docs1) > 0
    assert any(
        "pitaya" in d.lower()
        or "dragon" in d.lower()
        or "curd" in d.lower()
        or "probiotic" in d.lower()
        or "gut" in d.lower()
        or "prebiotic" in d.lower()
        for d in docs1
    )


    # 2. Test query for immunity / vitamin C
    res2 = rag_service.query_knowledge_base("Immunity boosting cold pressed juice with Vitamin C", n_results=3)
    docs2 = res2.get("documents", [])
    print("\n--- Semantic Search 2: Immunity / Vitamin C ---")
    for d in docs2:
        print(d[:100] + "...")
    assert len(docs2) > 0
    assert any("tulsi" in d.lower() or "orange" in d.lower() or "vitamin c" in d.lower() or "apple" in d.lower() for d in docs2)

    # 3. Test query for active promo coupons
    res3 = rag_service.query_knowledge_base("What discount coupons can I use at checkout?", n_results=2)
    docs3 = res3.get("documents", [])
    print("\n--- Semantic Search 3: Promo Coupons ---")
    for d in docs3:
        print(d[:100] + "...")
    assert len(docs3) > 0
    assert any("desi10" in d.lower() or "coupon" in d.lower() for d in docs3)

def test_rag_ai_chat():
    db = SessionLocal()
    try:
        messages = [
            {"role": "user", "content": "What is the origin and ingredients of your Kashmiri Apple Juice, and what is its price?"}
        ]
        res = asyncio.run(ai_service.ask_ai_assistant(messages, db))
        print("\n--- RAG AI Chat Response ---")
        print(res.get("reply"))
        reply_lower = res.get("reply", "").lower()
        assert "149" in reply_lower or "kashmir" in reply_lower or "srinagar" in reply_lower
        assert len(res.get("suggested_products", [])) > 0 or "apple" in reply_lower
    finally:
        db.close()

if __name__ == "__main__":
    print("Testing ChromaDB Indexing...")
    test_chroma_indexing()
    print("\nTesting ChromaDB Semantic Vector Queries...")
    test_chroma_semantic_query()
    print("\nTesting Full RAG AI Chat...")
    test_rag_ai_chat()
    print("\n=== ALL CHROMADB RAG TESTS PASSED WITH 100% SUCCESS! ===")
