
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # User type is now always 'buyer' - removed user_type field

class SellerProfile(db.Model):
    __tablename__ = 'seller_profile'
    
    seller_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    business_name = db.Column(db.String(255), nullable=False)
    business_description = db.Column(db.Text, nullable=True)
    approval_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, approved, rejected
    phone_number = db.Column(db.String(20), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminProfile(db.Model):
    __tablename__ = 'admin_profile'
    
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='general', nullable=False)  # general, super, etc.
    department = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# New Models for Products and Messages
class Product(db.Model):
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    
    seller_id = db.Column(db.Integer, db.ForeignKey('seller_profile.seller_id'), nullable=False)
    seller = db.relationship('SellerProfile', backref=db.backref('products', lazy=True))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# New Order Models
class Order(db.Model):
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Customer info (can be null for guest orders)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    
    # Customer details (for guest orders or backup)
    customer_name = db.Column(db.String(100), nullable=True)
    customer_email = db.Column(db.String(100), nullable=True)
    customer_phone = db.Column(db.String(20), nullable=True)
    
    # Order details
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, confirmed, dispatched, delivered, cancelled
    payment_status = db.Column(db.String(20), default='pending', nullable=False)  # pending, completed, failed
    payment_method = db.Column(db.String(50), default='mpesa', nullable=False)
    
    # M-Pesa details
    mpesa_checkout_request_id = db.Column(db.String(100), nullable=True)
    mpesa_receipt_number = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    item_id = db.Column(db.Integer, primary_key=True)
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    order = db.relationship('Order', backref=db.backref('items', lazy=True, cascade='all, delete-orphan'))
    
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    product = db.relationship('Product', backref=db.backref('order_items', lazy=True))
    
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = 'messages'
    
    message_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # For non-authenticated sender info
    senderName = db.Column(db.String(100), nullable=True)
    senderEmail = db.Column(db.String(100), nullable=True)
    productName = db.Column(db.String(255), nullable=True)
    
    # For buyer (user) messages - now optional
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)
    user = db.relationship('User', backref=db.backref('sent_messages', lazy=True))
    
    # For recipient (seller)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller_profile.seller_id'), nullable=False)
    seller = db.relationship('SellerProfile', backref=db.backref('received_messages', lazy=True))
    
    # Product reference (optional, if message is about a specific product)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=True)
    product = db.relationship('Product', backref=db.backref('messages', lazy=True))
    
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
