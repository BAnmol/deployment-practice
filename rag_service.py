import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import dotenv

dotenv.load_dotenv()

logger = logging.getLogger("rag_service")

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8002"))
COLLECTION_NAME = "juice_shop_knowledge"

_chroma_client = None
_collection = None


def get_chroma_client():
    """Initializes ChromaDB client. Tries Docker container first, falls back to persistent store."""
    global _chroma_client
    if _chroma_client is not None:
        return _chroma_client

    import chromadb
    from chromadb.config import Settings

    import time
    # 1. Attempt connection to Dockerized ChromaDB instance with retries
    for attempt in range(1, 6):
        try:
            logger.info(f"Connecting to ChromaDB on {CHROMA_HOST}:{CHROMA_PORT} (attempt {attempt}/5)...")
            client = chromadb.HttpClient(
                host=CHROMA_HOST,
                port=CHROMA_PORT,
                settings=Settings(anonymized_telemetry=False)
            )
            client.heartbeat()
            logger.info(f"Successfully connected to ChromaDB server at {CHROMA_HOST}:{CHROMA_PORT}!")
            _chroma_client = client
            return _chroma_client
        except Exception as e:
            if attempt < 5:
                time.sleep(1)
            else:
                logger.warning(
                    f"Could not connect to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT} after 5 attempts ({e}). "
                    f"Using local persistent ChromaDB storage as fallback."
                )

    # 2. Fallback to Local Persistent Storage
    try:
        persist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_db_store")
        os.makedirs(persist_dir, exist_ok=True)
        client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        logger.info(f"Initialized local persistent ChromaDB at {persist_dir}")
        _chroma_client = client
        return _chroma_client
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB persistent client: {e}", exc_info=True)
        return None


def get_or_create_collection():
    """Retrieves or creates the vector collection in ChromaDB."""
    global _collection
    client = get_chroma_client()
    if client is None:
        return None

    try:
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "OWASP Juice Shop Product & Pricing Knowledge Base"}
        )
        return _collection
    except Exception as e:
        logger.error(f"Error accessing Chroma collection '{COLLECTION_NAME}': {e}")
        return None


def index_catalog_to_chroma(db: Session) -> Dict[str, Any]:
    """Extracts all products, ingredients, nutrition, reviews, and coupons from SQLite and upserts embeddings into ChromaDB."""
    import models

    collection = get_or_create_collection()
    if collection is None:
        return {"status": "error", "message": "ChromaDB client unavailable"}

    products = db.query(models.Product).all()
    coupons = db.query(models.Coupon).filter(models.Coupon.is_active == True).all()
    reviews = db.query(models.Review).all()

    documents = []
    metadatas = []
    ids = []

    # 1. Index All Products
    for p in products:
        mrp = p.original_price if p.original_price else round(p.price * 1.25)
        discount_pct = round(((mrp - p.price) / mrp) * 100) if mrp > p.price else 0

        doc_text = (
            f"Product: {p.name}\n"
            f"Category: {p.category}\n"
            f"Current Price: ₹{p.price:.0f} INR\n"
            f"Original MRP: ₹{mrp:.0f} ({discount_pct}% OFF discount)\n"
            f"Farm Origin: {p.origin or 'India'}\n"
            f"Botanical Ingredients: {p.ingredients or '100% Pure Cold Pressed'}\n"
            f"Nutrition Facts: {p.nutrition_info or 'N/A'}\n"
            f"Shelf-Life: {p.shelf_life or '7 Days Refrigerated (0-4°C)'}\n"
            f"Stock Status: {p.stock} bottles in stock\n"
            f"Customer Rating: {p.rating}★ ({p.review_count} verified reviews)\n"
            f"Tag: {p.ribbon_badge or 'Fresh'}\n"
            f"Description: {p.description}\n"
        )

        doc_id = f"prod_{p.id}"
        documents.append(doc_text)
        metadatas.append({
            "doc_type": "product",
            "product_id": p.id,
            "name": p.name,
            "category": p.category,
            "price": float(p.price),
            "rating": float(p.rating),
            "origin": p.origin or "India"
        })
        ids.append(doc_id)

    # 2. Index Verified Customer Reviews
    for r in reviews:
        doc_text = (
            f"Customer Review for Product #{r.product_id}:\n"
            f"Reviewer: {r.author_name} ({r.city or 'India'})\n"
            f"Rating: {r.rating} / 5 Stars\n"
            f"Helpful Votes: {r.helpful_count or 0}\n"
            f"Feedback: {r.comment}\n"
        )
        doc_id = f"rev_{r.id}"
        documents.append(doc_text)
        metadatas.append({
            "doc_type": "review",
            "product_id": r.product_id,
            "rating": r.rating,
            "city": r.city or "India"
        })
        ids.append(doc_id)

    # 3. Index Active Promo Coupons & Payment Policies
    coupon_texts = [f"• Code '{c.code}': {c.discount_percent}% OFF (Max Discount: ₹{c.max_discount:.0f})" for c in coupons]
    policy_doc = (
        f"Active Discount Promo Coupons:\n" + "\n".join(coupon_texts) + "\n\n"
        f"Supported Payment Methods:\n"
        f"• UPI & QR (Google Pay, PhonePe, Paytm, BHIM, Cred)\n"
        f"• RuPay Platinum Debit / Credit Cards\n"
        f"• NetBanking (SBI, HDFC Bank, ICICI Bank, Axis Bank, Kotak, PNB)\n"
        f"• Cash on Delivery (COD)\n"
        f"Hyperlocal 4°C cold delivery in 30-45 minutes across Indian metro cities."
    )
    documents.append(policy_doc)
    metadatas.append({
        "doc_type": "policy",
        "category": "promos_and_payments",
        "product_id": 0,
        "name": "Promos and Payments",
        "price": 0.0,
        "rating": 5.0,
        "origin": "India"
    })
    ids.append("policy_promos_payments")

    # Upsert all into ChromaDB collection
    try:
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        total_indexed = collection.count()
        logger.info(f"Successfully indexed {len(ids)} knowledge chunks into ChromaDB. Total documents: {total_indexed}")
        return {
            "status": "success",
            "chunks_indexed": len(ids),
            "total_documents": total_indexed
        }
    except Exception as e:
        logger.error(f"Error upserting vectors to ChromaDB: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


def query_knowledge_base(
    query_text: str,
    n_results: int = 4,
    doc_type: Optional[str] = None
) -> Dict[str, Any]:
    """Performs semantic vector similarity search against ChromaDB."""
    collection = get_or_create_collection()
    if collection is None or collection.count() == 0:
        return {"documents": [], "metadatas": [], "matched_product_ids": []}

    try:
        where_filter = {"doc_type": doc_type} if doc_type else None
        
        results = collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection.count()),
            where=where_filter
        )

        retrieved_docs = results.get("documents", [[]])[0]
        retrieved_metadatas = results.get("metadatas", [[]])[0]

        matched_product_ids = []
        for meta in retrieved_metadatas:
            pid = meta.get("product_id")
            if pid and pid > 0 and pid not in matched_product_ids:
                matched_product_ids.append(pid)

        return {
            "documents": retrieved_docs,
            "metadatas": retrieved_metadatas,
            "matched_product_ids": matched_product_ids
        }
    except Exception as e:
        logger.error(f"Vector search failed in ChromaDB: {e}", exc_info=True)
        return {"documents": [], "metadatas": [], "matched_product_ids": []}
