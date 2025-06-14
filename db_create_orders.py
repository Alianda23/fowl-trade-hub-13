
from flask import Flask
from models import db, Order, OrderItem
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/kukuhub'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        # Create the new order tables
        db.create_all()
        print("Order tables created successfully!")
        print("Tables created:")
        print("- orders")
        print("- order_items")
        
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
