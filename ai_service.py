import os
import re
import json
import logging
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import dotenv

import models
import schemas

dotenv.load_dotenv()

logger = logging.getLogger("ai_assistant")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"
FALLBACK_MODEL = "google/gemini-2.0-flash-001"


def build_catalog_context(db: Session) -> str:
    """Extracts live product catalog, pricing, ingredients, nutrition, and coupons from SQLite."""
    products = db.query(models.Product).all()
    coupons = db.query(models.Coupon).filter(models.Coupon.is_active == True).all()

    catalog_lines = ["=== LIVE PRODUCT CATALOG & PRICING (INR ₹) ==="]
    for p in products:
        mrp = p.original_price if p.original_price else round(p.price * 1.25)
        discount_pct = round(((mrp - p.price) / mrp) * 100) if mrp > p.price else 0
        catalog_lines.append(
            f"• Product ID: {p.id} | Name: {p.name} | Category: {p.category}\n"
            f"  Current Price: ₹{p.price:.0f} | MRP: ₹{mrp:.0f} ({discount_pct}% OFF) | Stock: {p.stock} bottles\n"
            f"  Origin: {p.origin or 'India'} | Shelf-Life: {p.shelf_life or '7 Days Refrigerated (0-4°C)'}\n"
            f"  Ingredients: {p.ingredients or '100% Pure Cold-Pressed'}\n"
            f"  Nutrition Facts: {p.nutrition_info or 'N/A'}\n"
            f"  Rating: {p.rating}★ ({p.review_count} reviews) | Tag: {p.ribbon_badge or 'Fresh'}\n"
            f"  Description: {p.description}\n"
        )

    catalog_lines.append("\n=== ACTIVE DISCOUNT PROMO COUPONS ===")
    for c in coupons:
        catalog_lines.append(
            f"• Code '{c.code}': {c.discount_percent}% OFF (Max Discount: ₹{c.max_discount:.0f})"
        )

    catalog_lines.append("\n=== PAYMENT METHODS SUPPORTED ===")
    catalog_lines.append("• UPI & QR (Google Pay, PhonePe, Paytm, BHIM, Cred)")
    catalog_lines.append("• RuPay Platinum Debit / Credit Cards (Instant 3D secure)")
    catalog_lines.append(
        "• NetBanking (SBI, HDFC Bank, ICICI Bank, Axis Bank, Kotak, PNB)"
    )
    catalog_lines.append("• Cash on Delivery (COD) / Scan on delivery")

    return "\n".join(catalog_lines)


def get_system_prompt(catalog_text: str) -> str:
    return f"""You are 'RasAI', the expert AI Sommelier, Product Specialist, and Pricing Concierge for the OWASP Juice Shop Indian E-Commerce Platform.

{catalog_text}

YOUR MISSION & GUIDELINES:
1. Product Expertise: Help customers discover the perfect cold-pressed juices, smoothies, and traditional coolers based on taste preferences, health goals (immunity, digestion, workout recovery, detox, low sugar, glowing skin), and dietary needs.
2. Accurate Pricing & Discounts: Always quote exact Indian Rupee (₹) prices from the live catalog above. Highlight savings (e.g., "₹149 (MRP ₹199 - 25% OFF)"). Recommend active promo coupons (e.g. `DESI10`, `NAMASTE20`, `INDIA50`, `FREESHIP`) when customers ask about discounts.
3. Ingredients & Origins: Share authentic ingredients, botanical highlights (e.g., Amla, Holy Tulsi, Wayanad Nendran Banana, Ratnagiri Alphonso Mango, Kashmiri Apples), and farm origins.
4. Formatting: Use concise, structured Markdown with bullet points, emojis, bold pricing in ₹ INR, and enthusiastic, warm hospitality (using polite Indian greetings like 'Namaste!').
5. Interactive Recommendations: Whenever you recommend specific products, mention their name clearly.

Keep answers concise, helpful, informative, and engaging. Never invent fake products not listed in the catalog above.
"""


def extract_recommended_products(
    reply_text: str, all_products: List[models.Product]
) -> List[Dict[str, Any]]:
    """Identifies products mentioned in AI response to render interactive cards."""
    recommended = []
    reply_lower = reply_text.lower()

    for p in all_products:
        name_lower = p.name.lower()
        # Check if product name or key phrase appears in reply
        simple_name = name_lower.split("(")[0].strip()
        if (
            simple_name in reply_lower
            or f"id: {p.id}" in reply_lower
            or p.name.lower() in reply_lower
        ):
            mrp = p.original_price if p.original_price else round(p.price * 1.25)
            recommended.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "price": p.price,
                    "original_price": mrp,
                    "category": p.category,
                    "image_url": p.image_url,
                    "rating": p.rating,
                    "origin": p.origin,
                    "stock": p.stock,
                }
            )
            if len(recommended) >= 3:
                break
    return recommended


async def ask_ai_assistant(
    messages: List[Dict[str, str]],
    db: Session,
    current_product_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Interacts with OpenRouter API with dynamic SQLite catalog grounding."""
    catalog_text = build_catalog_context(db)
    system_prompt = get_system_prompt(catalog_text)

    all_products = db.query(models.Product).all()

    # If current_product_id is supplied, prepend context
    augmented_messages = [{"role": "system", "content": system_prompt}]

    if current_product_id:
        current_prod = (
            db.query(models.Product)
            .filter(models.Product.id == current_product_id)
            .first()
        )
        if current_prod:
            augmented_messages.append(
                {
                    "role": "system",
                    "content": f"Note: The customer is currently viewing Product #{current_prod.id}: '{current_prod.name}' priced at ₹{current_prod.price}.",
                }
            )

    for m in messages:
        if m.get("role") in ("user", "assistant", "system") and m.get("content"):
            augmented_messages.append({"role": m["role"], "content": m["content"]})

    # Prepare payload for OpenRouter
    api_key = os.getenv("OPENROUTER_API_KEY", OPENROUTER_API_KEY)

    if not api_key:
        return get_offline_fallback(messages, all_products)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Juice Shop AI Assistant",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEFAULT_MODEL,
        "messages": augmented_messages,
        "temperature": 0.7,
        "max_tokens": 800,
    }

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)

            if resp.status_code != 200:
                logger.warning(
                    f"OpenRouter returned {resp.status_code}: {resp.text}. Trying fallback model..."
                )
                payload["model"] = FALLBACK_MODEL
                resp = await client.post(OPENROUTER_URL, headers=headers, json=payload)

            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"]
                suggested_prods = extract_recommended_products(reply, all_products)

                # Contextual quick replies
                quick_replies = [
                    "What are your best deals under ₹150?",
                    "Which juices are best for immunity?",
                    "What promo coupons can I apply?",
                    "Tell me about Kashmiri Apple Juice",
                ]

                return {
                    "reply": reply,
                    "suggested_products": suggested_prods,
                    "quick_replies": quick_replies,
                }
            else:
                logger.error(f"OpenRouter Error: {resp.status_code} - {resp.text}")
                return get_offline_fallback(messages, all_products)

    except Exception as e:
        logger.error(f"AI Assistant Request Error: {e}", exc_info=True)
        return get_offline_fallback(messages, all_products)


def get_offline_fallback(
    messages: List[Dict[str, str]], all_products: List[models.Product]
) -> Dict[str, Any]:
    """Smart localized fallback in case of OpenRouter network timeout or key issue."""
    user_query = messages[-1]["content"].lower() if messages else ""

    if (
        "cheap" in user_query
        or "price" in user_query
        or "under" in user_query
        or "cost" in user_query
    ):
        sorted_prods = sorted(all_products, key=lambda x: x.price)
        reply = (
            "Here are our most budget-friendly authentic Indian juices under ₹150:\n\n"
        )
        for p in sorted_prods[:4]:
            reply += f"• {p.name} – ₹{p.price:.0f} (MRP ₹{p.original_price or round(p.price*1.25)}) • 📍 {p.origin}\n"
        reply += "\n💡 *Tip: Use coupon code `DESI10` for an extra 10% discount at checkout!*"
        suggested = extract_recommended_products(reply, all_products)
    elif (
        "coupon" in user_query
        or "discount" in user_query
        or "offer" in user_query
        or "promo" in user_query
    ):
        reply = "Here are our active discount coupons for your order:\n\n"
        reply += "• `DESI10` — 10% OFF on any juice order\n"
        reply += "• `NAMASTE20` — 20% OFF on orders above ₹500 (Max ₹250)\n"
        reply += "• `INDIA50` — 50% OFF mega discount (Max ₹500)\n"
        reply += "• `FREESHIP` — Free delivery discount across India\n\n"
        reply += "Apply any of these codes directly in your shopping basket before paying with UPI or RuPay!"
        suggested = []
    elif "immunity" in user_query or "health" in user_query or "tulsi" in user_query:
        reply = "For maximum natural immunity and wellness, I recommend:\n\n"
        reply += "1. Fresh Tulsi & Basil Herbal Smoothie (₹199) – Ayurvedic holy tulsi with fresh ginger extract.\n"
        reply += "2. Nagpur Fresh Orange Juice (₹149) – Packed with 82mg pure natural Vitamin C (136% RDA).\n"
        reply += "3. Desi Delhi Gajar Carrot Juice (₹169) – High in Beta-Carotene & Vitamin A.\n"
        suggested = extract_recommended_products(reply, all_products)
    else:
        reply = "Namaste! 🙏 I am RasAI, your smart Indian Juice Concierge.\n\n"
        reply += "I can help you with:\n"
        reply += "• Juice Pricing & Discounts (compare prices & find promo codes)\n"
        reply += (
            "• Ingredients & Nutrition (cold-pressed botanicals, calories, Vitamin C)\n"
        )
        reply += "• Tailored Recommendations (immunity boosters, workout recovery, sugar-free)\n\n"
        reply += "What kind of fresh juice are you looking for today?"
        suggested = []

    return {
        "reply": reply,
        "suggested_products": suggested,
        "quick_replies": [
            "What are your best deals under ₹150?",
            "Which juices are best for immunity?",
            "What promo coupons can I apply?",
            "Tell me about Kashmiri Apple Juice",
        ],
    }
