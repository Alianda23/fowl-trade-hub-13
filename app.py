from flask import Flask, request, jsonify, session
from flask_cors import CORS
from models import db, User, SellerProfile, AdminProfile, Product, Message, Order, OrderItem
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import uuid
from app_auth import check_admin_auth, check_seller_auth
from routes.mpesa import mpesa_routes

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/kukuhub'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change this to a secure key in production

# Configure upload folder for product images
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

CORS(app, supports_credentials=True)
db.init_app(app)

# Register blueprints
app.register_blueprint(mpesa_routes, url_prefix='/api/mpesa')

# User registration and authentication routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already registered'})
    
    try:
        # Create new buyer user
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            phone_number=data.get('phone_number')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User registered successfully'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error during registration: {str(e)}")
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    # Find user (buyer) by email
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    # Set session data for the user
    session['user_id'] = user.user_id
    
    return jsonify({
        'success': True, 
        'message': 'Login successful',
        'user_id': user.user_id,
        'username': user.username,
        'email': user.email
    })

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if user:
            return jsonify({
                'isAuthenticated': True,
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email
            })
    
    return jsonify({'isAuthenticated': False})

@app.route('/api/logout', methods=['POST'])
def logout():
    # Clear the session
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

# Seller routes
@app.route('/api/seller/register', methods=['POST'])
def seller_register():
    data = request.json
    
    # Check if seller already exists
    existing_seller = SellerProfile.query.filter_by(email=data['email']).first()
    if existing_seller:
        return jsonify({'success': False, 'message': 'Email already registered'})
    
    try:
        # Create new seller directly in SellerProfile
        hashed_password = generate_password_hash(data['password'])
        new_seller = SellerProfile(
            username=data['username'],
            email=data['email'],
            password_hash=hashed_password,
            business_name=data['business_name'],
            business_description=data.get('business_description'),
            phone_number=data.get('phone_number'),
            approval_status='pending'  # Default status
        )
        
        db.session.add(new_seller)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Seller registered successfully'})
    
    except Exception as e:
        db.session.rollback()
        print(f"Error during seller registration: {str(e)}")
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'})

@app.route('/api/seller/login', methods=['POST'])
def seller_login():
    data = request.json
    
    # Find seller by email
    seller = SellerProfile.query.filter_by(email=data['email']).first()
    
    if not seller or not check_password_hash(seller.password_hash, data['password']):
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    # Set session data for the seller
    session['seller_id'] = seller.seller_id
    
    return jsonify({
        'success': True, 
        'message': 'Login successful',
        'seller_id': seller.seller_id,
        'username': seller.username,
        'email': seller.email,
        'business_name': seller.business_name,
        'approval_status': seller.approval_status
    })

@app.route('/api/seller/check-auth', methods=['GET'])
def seller_auth_check():
    return check_seller_auth()

@app.route('/api/seller/update-profile', methods=['PUT'])
def update_seller_profile():
    """Update seller profile information"""
    # First check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        seller = SellerProfile.query.get(seller_id)
        
        if not seller:
            return jsonify({'success': False, 'message': 'Seller not found'})
        
        data = request.json
        
        # Update fields
        if 'username' in data:
            seller.username = data['username']
        if 'business_name' in data:
            seller.business_name = data['business_name']
        if 'business_description' in data:
            seller.business_description = data['business_description']
        if 'phone_number' in data:
            seller.phone_number = data['phone_number']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating seller profile: {str(e)}")
        return jsonify({'success': False, 'message': f'Update failed: {str(e)}'})

# Admin routes
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    
    # Find admin by email
    admin = AdminProfile.query.filter_by(email=data['email']).first()
    
    if not admin or not check_password_hash(admin.password_hash, data['password']):
        return jsonify({'success': False, 'message': 'Invalid admin credentials'})
    
    # Set session data for the admin
    session['admin_id'] = admin.admin_id
    
    return jsonify({
        'success': True, 
        'message': 'Admin login successful',
        'admin_id': admin.admin_id,
        'username': admin.username,
        'email': admin.email,
        'role': admin.role,
        'department': admin.department
    })

@app.route('/api/admin/check-auth', methods=['GET'])
def admin_auth_check():
    return check_admin_auth()

@app.route('/api/admin/update-profile', methods=['PUT'])
def update_admin_profile():
    """Update admin profile information"""
    # First check if admin is authenticated
    auth_check = check_admin_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Admin not authenticated'})
    
    try:
        admin_id = auth_data.get('admin_id')
        admin = AdminProfile.query.get(admin_id)
        
        if not admin:
            return jsonify({'success': False, 'message': 'Admin not found'})
        
        data = request.json
        
        # Update fields
        if 'username' in data:
            admin.username = data['username']
        if 'department' in data:
            admin.department = data['department']
        if 'phone_number' in data:
            admin.phone_number = data['phone_number']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating admin profile: {str(e)}")
        return jsonify({'success': False, 'message': f'Update failed: {str(e)}'})

@app.route('/api/admin/products/<product_id>', methods=['DELETE'])
def admin_delete_product(product_id):
    """Admin delete a product"""
    # First check if admin is authenticated
    auth_check = check_admin_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Admin not authenticated'})
    
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully by admin'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting product: {str(e)}'})

# Product routes
@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products for public viewing"""
    try:
        products = Product.query.all()
        product_list = []
        
        for product in products:
            # Get seller info
            seller = SellerProfile.query.get(product.seller_id)
            seller_name = seller.business_name if seller else "Unknown Seller"
            
            product_list.append({
                'id': str(product.product_id),
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock,
                'category': product.category,
                'image': product.image_url,
                'sellerId': str(product.seller_id),
                'sellerName': seller_name,
                'createdAt': product.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'products': product_list
        })
    
    except Exception as e:
        print(f"Error fetching products: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching products: {str(e)}'})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Get seller info
        seller = SellerProfile.query.get(product.seller_id)
        seller_name = seller.business_name if seller else "Unknown Seller"
        
        product_data = {
            'id': str(product.product_id),
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'stock': product.stock,
            'category': product.category,
            'image': product.image_url,
            'sellerId': str(product.seller_id),
            'sellerName': seller_name,
            'sellerEmail': seller.email if seller else None,
            'createdAt': product.created_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'product': product_data
        })
    
    except Exception as e:
        print(f"Error fetching product: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching product: {str(e)}'})

@app.route('/api/seller/products', methods=['GET'])
def get_seller_products():
    """Get products for the authenticated seller"""
    # First check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        products = Product.query.filter_by(seller_id=seller_id).all()
        product_list = []
        
        for product in products:
            product_list.append({
                'id': str(product.product_id),
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'stock': product.stock,
                'category': product.category,
                'image': product.image_url,
                'sellerId': str(product.seller_id),
                'sellerName': auth_data.get('business_name'),
                'createdAt': product.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'products': product_list
        })
    
    except Exception as e:
        print(f"Error fetching seller products: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching products: {str(e)}'})

@app.route('/api/products/create', methods=['POST'])
def add_product():
    """Add a new product (seller only)"""
    # First check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        # Check if we have form data (multipart/form-data) or JSON
        if request.form:
            name = request.form.get('name')
            description = request.form.get('description')
            price = float(request.form.get('price', 0))
            stock = int(request.form.get('stock', 0))
            category = request.form.get('category')
            seller_id = auth_data.get('seller_id')
            
            # Handle image upload
            image_url = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '':
                    # Generate unique filename
                    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Save file
                    file.save(file_path)
                    
                    # Generate URL
                    image_url = f"/static/uploads/{filename}"
            
            # Create new product
            new_product = Product(
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                image_url=image_url,
                seller_id=seller_id
            )
        else:
            # Handle JSON data
            data = request.json
            seller_id = auth_data.get('seller_id')
            
            # Create new product
            new_product = Product(
                name=data['name'],
                description=data['description'],
                price=float(data['price']),
                stock=int(data['stock']),
                category=data['category'],
                image_url=data.get('image'),  # Frontend should upload image first and send URL
                seller_id=seller_id
            )
        
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product added successfully',
            'productId': new_product.product_id
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error adding product: {str(e)}")
        return jsonify({'success': False, 'message': f'Error adding product: {str(e)}'})

@app.route('/api/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update product details (seller only)"""
    # First check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Verify product belongs to the seller
        if product.seller_id != int(seller_id):
            return jsonify({'success': False, 'message': 'You do not own this product'})
        
        data = request.json
        
        # Update fields
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data['description']
        if 'price' in data:
            product.price = float(data['price'])
        if 'stock' in data:
            product.stock = int(data['stock'])
        if 'category' in data:
            product.category = data['category']
        if 'image' in data and data['image']:
            product.image_url = data['image']
            
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product updated successfully',
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating product: {str(e)}")
        return jsonify({'success': False, 'message': f'Error updating product: {str(e)}'})

@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product (seller only)"""
    # First check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Verify this product belongs to the seller
        if product.seller_id != int(seller_id):
            return jsonify({'success': False, 'message': 'You do not own this product'})
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Product deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting product: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting product: {str(e)}'})

@app.route('/api/upload/product-image', methods=['POST'])
def upload_product_image():
    """Upload a product image and return the URL"""
    # Check authentication first
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image file provided'})
    
    try:
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No image selected'})
        
        # Generate unique filename
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(file_path)
        
        # Generate URL
        image_url = f"/static/uploads/{filename}"
        
        return jsonify({
            'success': True,
            'imageUrl': image_url
        })
    
    except Exception as e:
        print(f"Error uploading image: {str(e)}")
        return jsonify({'success': False, 'message': f'Error uploading image: {str(e)}'})

# Message Endpoints
@app.route('/api/messages/send', methods=['POST'])
def send_message():
    """Send a message to a seller"""
    data = request.json
    
    try:
        # Validate seller exists
        seller = SellerProfile.query.get(data['sellerId'])
        if not seller:
            return jsonify({'success': False, 'message': 'Seller not found'})
        
        # Create new message
        new_message = Message(
            content=data['content'],
            user_id=None,  # Anonymous message is okay
            seller_id=int(data['sellerId']),
            senderName=data.get('senderName', 'Anonymous'),
            senderEmail=data.get('senderEmail', 'no-email@example.com'),
            productName=data.get('productName', 'Unknown Product')
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message sent successfully',
            'messageId': new_message.message_id
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error sending message: {str(e)}")
        return jsonify({'success': False, 'message': f'Error sending message: {str(e)}'})

@app.route('/api/seller/messages', methods=['GET'])
def get_seller_messages():
    """Get messages for the authenticated seller"""
    # Check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        messages = Message.query.filter_by(seller_id=seller_id).order_by(Message.created_at.desc()).all()
        message_list = []
        
        for msg in messages:
            message_list.append({
                'id': str(msg.message_id),
                'senderName': msg.senderName,
                'senderEmail': msg.senderEmail,
                'message': msg.content,
                'productName': msg.productName,
                'isRead': msg.is_read,
                'createdAt': msg.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'messages': message_list
        })
    
    except Exception as e:
        print(f"Error fetching messages: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching messages: {str(e)}'})

@app.route('/api/seller/messages/mark-read/<message_id>', methods=['PUT'])
def mark_message_read(message_id):
    """Mark a message as read"""
    # Check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        message = Message.query.get(message_id)
        
        if not message:
            return jsonify({'success': False, 'message': 'Message not found'})
        
        # Verify this message belongs to the seller
        if message.seller_id != int(seller_id):
            return jsonify({'success': False, 'message': 'This message does not belong to you'})
        
        message.is_read = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Message marked as read'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error marking message as read: {str(e)}")
        return jsonify({'success': False, 'message': f'Error marking message as read: {str(e)}'})

@app.route('/api/seller/messages/count', methods=['GET'])
def get_seller_message_count():
    """Get count of unread messages for the authenticated seller"""
    # Check if seller is authenticated
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        unread_count = Message.query.filter_by(seller_id=seller_id, is_read=False).count()
        
        return jsonify({
            'success': True,
            'count': unread_count
        })
    
    except Exception as e:
        print(f"Error fetching message count: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching message count: {str(e)}'})

# Order Management APIs
@app.route('/api/orders/create', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        data = request.json
        
        # Generate unique order number
        order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:4].upper()}"
        
        # Get user info if authenticated
        user_id = session.get('user_id')
        
        # Create new order
        new_order = Order(
            order_number=order_number,
            user_id=user_id,
            customer_name=data.get('customerName'),
            customer_email=data.get('customerEmail'),
            customer_phone=data.get('customerPhone'),
            total_amount=float(data['totalAmount']),
            payment_method=data.get('paymentMethod', 'mpesa'),
            mpesa_checkout_request_id=data.get('checkoutRequestId')
        )
        
        db.session.add(new_order)
        db.session.flush()  # Get the order ID
        
        # Add order items
        for item in data['items']:
            order_item = OrderItem(
                order_id=new_order.order_id,
                product_id=int(item['productId']),
                quantity=int(item['quantity']),
                unit_price=float(item['unitPrice']),
                total_price=float(item['totalPrice'])
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order created successfully',
            'orderId': new_order.order_id,
            'orderNumber': order_number
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error creating order: {str(e)}")
        return jsonify({'success': False, 'message': f'Error creating order: {str(e)}'})

@app.route('/api/orders/update-payment', methods=['PUT'])
def update_order_payment():
    """Update order payment status"""
    try:
        data = request.json
        
        order = Order.query.filter_by(mpesa_checkout_request_id=data['checkoutRequestId']).first()
        
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        order.payment_status = data['paymentStatus']
        if data.get('receiptNumber'):
            order.mpesa_receipt_number = data['receiptNumber']
        
        # If payment is successful, update order status
        if data['paymentStatus'] == 'completed':
            order.status = 'confirmed'
        elif data['paymentStatus'] == 'failed':
            order.status = 'cancelled'
        
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order payment status updated'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating order payment: {str(e)}")
        return jsonify({'success': False, 'message': f'Error updating order payment: {str(e)}'})

@app.route('/api/orders/user', methods=['GET'])
def get_user_orders():
    """Get orders for the authenticated user"""
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'User not authenticated'})
        
        orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
        order_list = []
        
        for order in orders:
            # Get order items with product details
            items = []
            for item in order.items:
                product = item.product
                items.append({
                    'id': str(product.product_id),
                    'name': product.name,
                    'image': product.image_url,
                    'price': item.unit_price,
                    'quantity': item.quantity
                })
            
            order_list.append({
                'id': order.order_number,
                'products': items,
                'status': order.status,
                'date': order.created_at.strftime('%Y-%m-%d'),
                'total': order.total_amount
            })
        
        return jsonify({
            'success': True,
            'orders': order_list
        })
    
    except Exception as e:
        print(f"Error fetching user orders: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching orders: {str(e)}'})

@app.route('/api/orders/seller', methods=['GET'])
def get_seller_orders():
    """Get orders for the authenticated seller"""
    auth_check = check_seller_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Seller not authenticated'})
    
    try:
        seller_id = auth_data.get('seller_id')
        
        # Get orders that contain products from this seller
        orders = db.session.query(Order).join(OrderItem).join(Product).filter(
            Product.seller_id == seller_id
        ).distinct().order_by(Order.created_at.desc()).all()
        
        order_list = []
        
        for order in orders:
            # Get only items from this seller
            seller_items = []
            for item in order.items:
                if item.product.seller_id == int(seller_id):
                    seller_items.append({
                        'productName': item.product.name,
                        'quantity': item.quantity,
                        'unitPrice': item.unit_price,
                        'totalPrice': item.total_price
                    })
            
            if seller_items:  # Only include orders with items from this seller
                order_list.append({
                    'id': order.order_number,
                    'customerName': order.customer_name or 'Guest',
                    'items': seller_items,
                    'status': order.status,
                    'paymentStatus': order.payment_status,
                    'date': order.created_at.strftime('%Y-%m-%d'),
                    'total': sum(item['totalPrice'] for item in seller_items)
                })
        
        return jsonify({
            'success': True,
            'orders': order_list
        })
    
    except Exception as e:
        print(f"Error fetching seller orders: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching orders: {str(e)}'})

@app.route('/api/orders/admin', methods=['GET'])
def get_admin_orders():
    """Get all orders for admin"""
    auth_check = check_admin_auth()
    auth_data = auth_check.get_json()
    
    if not auth_data.get('isAuthenticated'):
        return jsonify({'success': False, 'message': 'Admin not authenticated'})
    
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        order_list = []
        
        for order in orders:
            order_list.append({
                'id': order.order_number,
                'customer': order.customer_name or 'Guest',
                'total': order.total_amount,
                'status': order.status,
                'paymentStatus': order.payment_status,
                'date': order.created_at.strftime('%Y-%m-%d')
            })
        
        return jsonify({
            'success': True,
            'orders': order_list
        })
    
    except Exception as e:
        print(f"Error fetching admin orders: {str(e)}")
        return jsonify({'success': False, 'message': f'Error fetching orders: {str(e)}'})

@app.route('/api/orders/<order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status (seller/admin only)"""
    try:
        # Check if user is seller or admin
        seller_auth = check_seller_auth()
        admin_auth = check_admin_auth()
        
        seller_data = seller_auth.get_json()
        admin_data = admin_auth.get_json()
        
        if not (seller_data.get('isAuthenticated') or admin_data.get('isAuthenticated')):
            return jsonify({'success': False, 'message': 'Authentication required'})
        
        data = request.json
        order = Order.query.filter_by(order_number=order_id).first()
        
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # If seller, verify they have products in this order
        if seller_data.get('isAuthenticated'):
            seller_id = seller_data.get('seller_id')
            has_products = db.session.query(OrderItem).join(Product).filter(
                OrderItem.order_id == order.order_id,
                Product.seller_id == seller_id
            ).first()
            
            if not has_products:
                return jsonify({'success': False, 'message': 'You do not have products in this order'})
        
        order.status = data['status']
        order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order status updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"Error updating order status: {str(e)}")
        return jsonify({'success': False, 'message': f'Error updating order status: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
