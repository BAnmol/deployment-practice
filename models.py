import datetime
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default='customer') # 'customer' or 'admin'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    basket_items = relationship('BasketItem', back_populates='user', cascade='all, delete-orphan')
    orders = relationship('Order', back_populates='user')

class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    image_url = Column(String(500), nullable=False)
    category = Column(String(100), default='Juice')
    ingredients = Column(Text, nullable=True) # Comma-separated or detailed ingredients
    nutrition_info = Column(Text, nullable=True) # JSON or key:value nutritional data
    origin = Column(String(255), nullable=True) # Farm / Region of origin
    shelf_life = Column(String(100), default='7 Days Refrigerated (0-4°C)')
    stock = Column(Integer, default=50)
    ribbon_badge = Column(String(100), nullable=True) # e.g. 'Only 1 left', 'Sale', 'Popular'
    rating = Column(Float, default=4.5)
    review_count = Column(Integer, default=1)
    is_featured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


    reviews = relationship('Review', back_populates='product', cascade='all, delete-orphan')
    basket_items = relationship('BasketItem', back_populates='product')

class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    author_email = Column(String(255), nullable=False)
    author_name = Column(String(255), default='Verified Customer')
    city = Column(String(100), default='India')
    helpful_count = Column(Integer, default=3)
    rating = Column(Integer, default=5)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    product = relationship('Product', back_populates='reviews')


class BasketItem(Base):
    __tablename__ = 'basket_items'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    session_id = Column(String(100), index=True, nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='basket_items')
    product = relationship('Product', back_populates='basket_items')

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user_email = Column(String(255), nullable=False)
    customer_name = Column(String(255), nullable=False)
    delivery_address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    zip_code = Column(String(50), nullable=False)
    country = Column(String(100), default='India')

    delivery_method = Column(String(100), default='Standard Delivery')
    delivery_fee = Column(Float, default=0.0)
    subtotal = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    payment_method = Column(String(100), nullable=False) # 'Credit Card', 'UPI / QR', 'Net Banking', 'Cash on Delivery'
    payment_status = Column(String(50), default='Completed')
    payment_reference = Column(String(100), nullable=True)
    status = Column(String(50), default='Order Placed') # 'Order Placed', 'Preparing', 'Out for Delivery', 'Delivered'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')

class OrderItem(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    image_url = Column(String(500), nullable=False)

    order = relationship('Order', back_populates='items')

class Coupon(Base):
    __tablename__ = 'coupons'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    discount_percent = Column(Float, default=10.0)
    max_discount = Column(Float, default=50.0)
    is_active = Column(Boolean, default=True)
