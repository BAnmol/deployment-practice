import os
import uuid
import datetime
from typing import List, Optional
import dotenv
dotenv.load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc

from database import engine, get_db, Base
import models
import schemas
import ai_service
import rag_service
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user_optional,
    get_current_user,
    get_session_id
)
from seed_data import seed_database


# Initialize database tables and seed initial data
Base.metadata.create_all(bind=engine)
seed_database()

# Automatically index catalog to ChromaDB vector database
try:
    with Session(engine) as init_db:
        rag_service.index_catalog_to_chroma(init_db)
except Exception as e:
    print(f"ChromaDB startup indexing note: {e}")

app = FastAPI(
    title="OWASP Juice Shop API",
    description="Full-featured e-commerce API for Juice Shop with Dummy Payment Portal and Auth",
    version="1.0.0"
)


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure static directory exists
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Helper function to get or generate guest session ID
def resolve_cart_identity(request: Request, response: Response, current_user: Optional[models.User]):
    user_id = current_user.id if current_user else None
    session_id = request.cookies.get("juice_session_id")
    if not session_id and not user_id:
        session_id = f"guest_{uuid.uuid4().hex[:12]}"
        response.set_cookie(key="juice_session_id", value=session_id, max_age=30*86400, httponly=False)
    return user_id, session_id

def calculate_cart_summary(cart_items: List[models.BasketItem], discount_pct: float = 0.0, delivery_fee: float = 0.0):
    items_out = []
    subtotal = 0.0
    item_count = 0
    for item in cart_items:
        prod = item.product
        line_total = round(prod.price * item.quantity, 2)
        subtotal += line_total
        item_count += item.quantity
        items_out.append({
            "id": item.id,
            "product_id": prod.id,
            "product": prod,
            "quantity": item.quantity,
            "total_price": line_total
        })

    subtotal = round(subtotal, 2)
    discount_amount = round(subtotal * (discount_pct / 100.0), 2)
    total = round(max(0.0, subtotal - discount_amount + delivery_fee), 2)
    return {
        "items": items_out,
        "item_count": item_count,
        "subtotal": subtotal,
        "discount": discount_amount,
        "delivery_fee": delivery_fee,
        "total": total
    }

# ==========================================
# AUTHENTICATION ENDPOINTS
# ==========================================

def migrate_guest_basket(db: Session, session_id: Optional[str], user_id: int):
    if not session_id or not user_id:
        return
    guest_items = db.query(models.BasketItem).filter(models.BasketItem.session_id == session_id).all()
    for g_item in guest_items:
        existing_user_item = db.query(models.BasketItem).filter(
            models.BasketItem.user_id == user_id,
            models.BasketItem.product_id == g_item.product_id
        ).first()
        if existing_user_item:
            existing_user_item.quantity += g_item.quantity
            db.delete(g_item)
        else:
            g_item.user_id = user_id
            g_item.session_id = None
    db.commit()

@app.post("/api/auth/register", response_model=schemas.TokenResponse)
def register_user(user_in: schemas.UserRegister, request: Request, response: Response, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    new_user = models.User(
        email=user_in.email.lower(),
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name or user_in.email.split("@")[0].capitalize(),
        role="customer"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    session_id = request.cookies.get("juice_session_id")
    migrate_guest_basket(db, session_id, new_user.id)

    token = create_access_token({"sub": new_user.email, "id": new_user.id, "role": new_user.role})
    response.set_cookie(key="access_token", value=token, max_age=7*86400, httponly=False)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user
    }

@app.post("/api/auth/login", response_model=schemas.TokenResponse)
def login_user(credentials: schemas.UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email.lower()).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    session_id = request.cookies.get("juice_session_id")
    migrate_guest_basket(db, session_id, user.id)

    token = create_access_token({"sub": user.email, "id": user.id, "role": user.role})
    response.set_cookie(key="access_token", value=token, max_age=7*86400, httponly=False)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@app.post("/api/auth/logout")
def logout_user(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me", response_model=schemas.UserOut)
def get_current_user_profile(user: models.User = Depends(get_current_user)):
    return user

# ==========================================
# PRODUCTS & CATALOG ENDPOINTS
# ==========================================

@app.get("/api/products", response_model=List[schemas.ProductOut])
def get_products(
    q: Optional[str] = Query(None, description="Search term for product name or description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    sort: Optional[str] = Query(None, description="Sort order: price-asc, price-desc, rating, name"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Product)

    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.Product.name.ilike(search_pattern),
                models.Product.description.ilike(search_pattern),
                models.Product.category.ilike(search_pattern)
            )
        )

    if category and category.lower() != "all":
        query = query.filter(models.Product.category.ilike(category.strip()))

    if sort == "price-asc":
        query = query.order_by(asc(models.Product.price))
    elif sort == "price-desc":
        query = query.order_by(desc(models.Product.price))
    elif sort == "rating":
        query = query.order_by(desc(models.Product.rating))
    elif sort == "name":
        query = query.order_by(asc(models.Product.name))
    else:
        query = query.order_by(asc(models.Product.id))

    return query.all()

@app.get("/api/products/{product_id}", response_model=schemas.ProductDetail)
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product

@app.post("/api/products/{product_id}/reviews", response_model=schemas.ReviewOut)
def add_product_review(
    product_id: int,
    review_in: schemas.ReviewCreate,
    request: Request,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    author_email = current_user.email if current_user else "anonymous@juice-sh.op"
    author_name = review_in.author_name or (current_user.full_name if current_user else "Verified Customer")
    city = review_in.city or "India"

    review = models.Review(
        product_id=product_id,
        author_email=author_email,
        author_name=author_name,
        city=city,
        helpful_count=0,
        rating=review_in.rating,
        comment=review_in.comment.strip()
    )
    db.add(review)

    # Recalculate average rating
    all_reviews = db.query(models.Review).filter(models.Review.product_id == product_id).all()
    total_ratings = sum(r.rating for r in all_reviews) + review_in.rating
    count = len(all_reviews) + 1
    product.rating = round(total_ratings / count, 1)
    product.review_count = count

    db.commit()
    db.refresh(review)
    return review

@app.post("/api/reviews/{review_id}/helpful")
def upvote_review_helpful(review_id: int, db: Session = Depends(get_db)):
    review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found.")
    review.helpful_count = (review.helpful_count or 0) + 1
    db.commit()
    db.refresh(review)
    return {"id": review.id, "helpful_count": review.helpful_count}


@app.get("/api/categories")
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(models.Product.category).distinct().all()
    return ["All"] + [c[0] for c in categories if c[0]]

# ==========================================
# BASKET / CART ENDPOINTS
# ==========================================

@app.get("/api/basket", response_model=schemas.BasketResponse)
def get_basket(
    request: Request,
    response: Response,
    coupon: Optional[str] = Query(None),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    user_id, session_id = resolve_cart_identity(request, response, current_user)

    if user_id:
        items = db.query(models.BasketItem).filter(models.BasketItem.user_id == user_id).all()
    else:
        items = db.query(models.BasketItem).filter(models.BasketItem.session_id == session_id).all()

    discount_pct = 0.0
    if coupon:
        c = db.query(models.Coupon).filter(models.Coupon.code == coupon.upper().strip(), models.Coupon.is_active == True).first()
        if c:
            discount_pct = c.discount_percent

    return calculate_cart_summary(items, discount_pct=discount_pct)

@app.post("/api/basket/add", response_model=schemas.BasketResponse)
def add_to_basket(
    item_in: schemas.BasketItemCreate,
    request: Request,
    response: Response,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.id == item_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")

    user_id, session_id = resolve_cart_identity(request, response, current_user)

    # Check if item exists in cart
    if user_id:
        existing = db.query(models.BasketItem).filter(
            models.BasketItem.user_id == user_id,
            models.BasketItem.product_id == item_in.product_id
        ).first()
    else:
        existing = db.query(models.BasketItem).filter(
            models.BasketItem.session_id == session_id,
            models.BasketItem.product_id == item_in.product_id
        ).first()

    if existing:
        existing.quantity += item_in.quantity
    else:
        new_item = models.BasketItem(
            user_id=user_id,
            session_id=session_id if not user_id else None,
            product_id=item_in.product_id,
            quantity=item_in.quantity
        )
        db.add(new_item)

    db.commit()

    # Return updated basket
    if user_id:
        items = db.query(models.BasketItem).filter(models.BasketItem.user_id == user_id).all()
    else:
        items = db.query(models.BasketItem).filter(models.BasketItem.session_id == session_id).all()

    return calculate_cart_summary(items)

@app.put("/api/basket/item/{item_id}", response_model=schemas.BasketResponse)
def update_basket_item_quantity(
    item_id: int,
    item_in: schemas.BasketItemUpdate,
    request: Request,
    response: Response,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    user_id, session_id = resolve_cart_identity(request, response, current_user)

    if user_id:
        item = db.query(models.BasketItem).filter(models.BasketItem.id == item_id, models.BasketItem.user_id == user_id).first()
    else:
        item = db.query(models.BasketItem).filter(models.BasketItem.id == item_id, models.BasketItem.session_id == session_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found.")

    if item_in.quantity <= 0:
        db.delete(item)
    else:
        item.quantity = item_in.quantity

    db.commit()

    if user_id:
        items = db.query(models.BasketItem).filter(models.BasketItem.user_id == user_id).all()
    else:
        items = db.query(models.BasketItem).filter(models.BasketItem.session_id == session_id).all()

    return calculate_cart_summary(items)

@app.delete("/api/basket/item/{item_id}", response_model=schemas.BasketResponse)
def delete_basket_item(
    item_id: int,
    request: Request,
    response: Response,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    user_id, session_id = resolve_cart_identity(request, response, current_user)

    if user_id:
        item = db.query(models.BasketItem).filter(models.BasketItem.id == item_id, models.BasketItem.user_id == user_id).first()
    else:
        item = db.query(models.BasketItem).filter(models.BasketItem.id == item_id, models.BasketItem.session_id == session_id).first()

    if item:
        db.delete(item)
        db.commit()

    if user_id:
        items = db.query(models.BasketItem).filter(models.BasketItem.user_id == user_id).all()
    else:
        items = db.query(models.BasketItem).filter(models.BasketItem.session_id == session_id).all()

    return calculate_cart_summary(items)

@app.delete("/api/basket/clear")
def clear_basket(
    request: Request,
    response: Response,
    current_user: Optional[models.User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    user_id, session_id = resolve_cart_identity(request, response, current_user)

    if user_id:
        db.query(models.BasketItem).filter(models.BasketItem.user_id == user_id).delete()
    else:
        db.query(models.BasketItem).filter(models.BasketItem.session_id == session_id).delete()

    db.commit()
    return {"message": "Basket cleared successfully", "items": [], "item_count": 0, "total": 0.0}

@app.post("/api/basket/coupon", response_model=schemas.CouponResponse)
def apply_coupon(req: schemas.CouponApplyRequest, db: Session = Depends(get_db)):
    code = req.code.strip().upper()
    coupon = db.query(models.Coupon).filter(models.Coupon.code == code, models.Coupon.is_active == True).first()
    if not coupon:
        return {
            "code": code,
            "discount_percent": 0.0,
            "valid": False,
            "message": "Invalid or expired promo code."
        }
    return {
        "code": coupon.code,
        "discount_percent": coupon.discount_percent,
        "valid": True,
        "message": f"Coupon applied! You got {coupon.discount_percent}% off your juices."
    }

# ==========================================
# DUMMY PAYMENT & CHECKOUT ENDPOINTS
# ==========================================

@app.post("/api/checkout/process", response_model=schemas.OrderOut)
def process_checkout(
    checkout_data: schemas.CheckoutRequest,
    request: Request,
    response: Response,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.id

    # 1. Fetch current cart items for authenticated user
    cart_items = db.query(models.BasketItem).filter(models.BasketItem.user_id == user_id).all()

    if not cart_items:
        raise HTTPException(status_code=400, detail="Your basket is empty. Please add items before checking out.")

    # 2. Check coupon if provided
    discount_pct = 0.0
    if checkout_data.coupon_code:
        coupon = db.query(models.Coupon).filter(
            models.Coupon.code == checkout_data.coupon_code.strip().upper(),
            models.Coupon.is_active == True
        ).first()
        if coupon:
            discount_pct = coupon.discount_percent

    delivery_fee = checkout_data.delivery_fee or 0.0
    cart_summary = calculate_cart_summary(cart_items, discount_pct=discount_pct, delivery_fee=delivery_fee)

    # 3. Simulate Indian Payment Gateway Reference
    order_num = f"JUICE-IN-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    method_prefix = "UPI"
    if "RuPay" in checkout_data.payment_method or "Card" in checkout_data.payment_method:
        method_prefix = "RUPAY"
    elif "Net Banking" in checkout_data.payment_method:
        method_prefix = "NETBANK"
    elif "Cash" in checkout_data.payment_method:
        method_prefix = "COD"

    payment_ref = f"{method_prefix}-IN-{uuid.uuid4().hex[:8].upper()}"

    # 4. Create Order Record
    new_order = models.Order(
        order_number=order_num,
        user_id=user_id,
        user_email=checkout_data.email.lower(),
        customer_name=checkout_data.customer_name,
        delivery_address=checkout_data.address,
        city=checkout_data.city,
        zip_code=checkout_data.zip_code,
        country=checkout_data.country or "India",
        delivery_method=checkout_data.delivery_method or "Standard Fresh Delivery",
        delivery_fee=delivery_fee,
        subtotal=cart_summary["subtotal"],
        discount=cart_summary["discount"],
        total=cart_summary["total"],
        payment_method=checkout_data.payment_method,
        payment_status="Paid (Simulated via NPCI / Indian Gateway)" if "Cash" not in checkout_data.payment_method else "Pending (Pay on Delivery)",
        payment_reference=payment_ref,
        status="Order Confirmed & Preparing Fresh Juices"
    )
    db.add(new_order)
    db.flush()


    # 5. Create Order Items & Update Stock
    for item in cart_items:
        prod = item.product
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=prod.id,
            product_name=prod.name,
            price=prod.price,
            quantity=item.quantity,
            image_url=prod.image_url
        )
        db.add(order_item)

        # Decrement stock safely
        if prod.stock is not None and prod.stock > 0:
            prod.stock = max(0, prod.stock - item.quantity)

    # 6. Clear Basket
    if user_id:
        db.query(models.BasketItem).filter(models.BasketItem.user_id == user_id).delete()
    else:
        db.query(models.BasketItem).filter(models.BasketItem.session_id == session_id).delete()

    db.commit()
    db.refresh(new_order)
    return new_order

@app.get("/api/orders", response_model=List[schemas.OrderOut])
def get_user_orders(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(models.Order).filter(models.Order.user_id == current_user.id).order_by(desc(models.Order.created_at)).all()
    return orders

@app.get("/api/orders/{order_number}", response_model=schemas.OrderOut)
def get_order_by_number(order_number: str, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.order_number == order_number.strip()).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    return order

# ==========================================
# AI Assistant (RasAI) Routes (Powered by OpenRouter)
# ==========================================

@app.post("/api/ai/chat", response_model=schemas.AIChatResponse)
async def ai_chat_endpoint(
    request: schemas.AIChatRequest,
    db: Session = Depends(get_db)
):
    """Answers customer queries on juice products, pricing, discounts, health benefits, and recommendations."""
    messages_payload = [{"role": m.role, "content": m.content} for m in request.messages]
    result = await ai_service.ask_ai_assistant(
        messages=messages_payload,
        db=db,
        current_product_id=request.current_product_id
    )
    return result

@app.get("/api/ai/suggestions", response_model=schemas.AISuggestionsResponse)
def get_ai_suggestions():
    """Provides prompt starters for the AI Concierge."""
    return {
        "suggestions": [
            "🍹 What are your cheapest juices under ₹150?",
            "🛡️ Which cold-pressed juices boost immunity?",
            "🏷️ What active discount coupons can I use?",
            "🍏 Tell me about Kashmiri Apple Juice ingredients & pricing",
            "⚡ How do I pay via Google Pay UPI or RuPay?"
        ]
    }

@app.post("/api/ai/reindex")
def reindex_chroma_knowledge_base(db: Session = Depends(get_db)):
    """Re-indexes all products, reviews, and coupons into the ChromaDB vector database."""
    res = rag_service.index_catalog_to_chroma(db)
    return res

# ==========================================
# HTML PAGE ROUTES
# ==========================================

@app.get("/")
def serve_index_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/login")
def serve_login_page():
    return FileResponse(os.path.join(STATIC_DIR, "login.html"))

@app.get("/orders")
def serve_orders_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    import socket

    def find_free_port(preferred_port=8000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', preferred_port))
                return preferred_port
            except OSError:
                return None

    desired_port = int(os.environ.get("PORT", 8000))
    active_port = find_free_port(desired_port)

    if not active_port:
        print(f"\n⚠️  Port {desired_port} is already in use by another running server instance.")
        # Try alternate port 8001, 8080
        for fallback in [8001, 8080, 5000]:
            if find_free_port(fallback):
                active_port = fallback
                print(f"🔄 Automatically switching to available fallback port: http://127.0.0.1:{active_port}\n")
                break
        if not active_port:
            active_port = desired_port

    print(f"\n🚀 Starting OWASP Juice Shop Indian E-Commerce on http://127.0.0.1:{active_port} ...\n")
    uvicorn.run("main:app", host="127.0.0.1", port=active_port, reload=True)

