from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import datetime

# User Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4)
    full_name: Optional[str] = 'Juice Lover'

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: UserOut

# Review Schemas
class ReviewCreate(BaseModel):
    rating: int = Field(5, ge=1, le=5)
    comment: str = Field(..., min_length=2)
    author_name: Optional[str] = None
    city: Optional[str] = 'India'

class ReviewOut(BaseModel):
    id: int
    product_id: int
    author_email: str
    author_name: Optional[str]
    city: Optional[str] = 'India'
    helpful_count: Optional[int] = 0
    rating: int
    comment: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Product Schemas
class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    original_price: Optional[float]
    image_url: str
    category: str
    ingredients: Optional[str] = None
    nutrition_info: Optional[str] = None
    origin: Optional[str] = None
    shelf_life: Optional[str] = None
    stock: int
    ribbon_badge: Optional[str]
    rating: float
    review_count: int
    is_featured: bool

    class Config:
        from_attributes = True

class ProductDetail(ProductOut):
    reviews: List[ReviewOut] = []


# Basket Schemas
class BasketItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1)

class BasketItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0)

class BasketItemOut(BaseModel):
    id: int
    product_id: int
    product: ProductOut
    quantity: int
    total_price: float

class BasketResponse(BaseModel):
    items: List[BasketItemOut]
    item_count: int
    subtotal: float
    discount: float
    delivery_fee: float
    total: float

# Checkout & Payment Schemas
class PaymentCardDetails(BaseModel):
    card_number: Optional[str] = None
    card_holder: Optional[str] = None
    expiry: Optional[str] = None
    cvv: Optional[str] = None

class CheckoutRequest(BaseModel):
    customer_name: str
    email: EmailStr
    address: str
    city: str
    zip_code: str
    country: Optional[str] = 'India'

    delivery_method: Optional[str] = 'Standard Delivery (Free)'
    delivery_fee: Optional[float] = 0.0
    coupon_code: Optional[str] = None
    payment_method: str # 'Credit Card', 'UPI / QR', 'Net Banking', 'Cash on Delivery'
    card_details: Optional[PaymentCardDetails] = None
    upi_id: Optional[str] = None
    bank_name: Optional[str] = None

class OrderItemOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    price: float
    quantity: int
    image_url: str

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    order_number: str
    user_email: str
    customer_name: str
    delivery_address: str
    city: str
    zip_code: str
    delivery_method: str
    delivery_fee: float
    subtotal: float
    discount: float
    total: float
    payment_method: str
    payment_status: str
    payment_reference: Optional[str]
    status: str
    created_at: datetime.datetime
    items: List[OrderItemOut]

    class Config:
        from_attributes = True

class CouponApplyRequest(BaseModel):
    code: str

class CouponResponse(BaseModel):
    code: str
    discount_percent: float
    valid: bool
    message: str


# ==========================================
# AI Assistant Schemas
# ==========================================
class ChatMessage(BaseModel):
    role: str # 'user', 'assistant', 'system'
    content: str

class AIChatRequest(BaseModel):
    messages: List[ChatMessage]
    current_product_id: Optional[int] = None

class AISuggestedProduct(BaseModel):
    id: int
    name: str
    price: float
    original_price: Optional[float] = None
    category: str
    image_url: str
    rating: float
    origin: Optional[str] = None
    stock: int

class AIChatResponse(BaseModel):
    reply: str
    suggested_products: List[AISuggestedProduct] = []
    quick_replies: List[str] = []

class AISuggestionsResponse(BaseModel):
    suggestions: List[str]

