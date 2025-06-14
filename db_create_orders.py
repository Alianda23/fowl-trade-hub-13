
from flask import Flask
from models import db, Order, OrderItem
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/kukuhub'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        # Drop existing order tables if they exist (to recreate with correct schema)
        db.engine.execute("DROP TABLE IF EXISTS order_items")
        db.engine.execute("DROP TABLE IF EXISTS orders")
        
        # Create the new order tables with correct schema
        db.create_all()
        print("Order tables created successfully!")
        print("Tables created:")
        print("- orders (with order_number column)")
        print("- order_items")
        
        # Verify the tables were created correctly
        result = db.engine.execute("DESCRIBE orders")
        print("\nOrders table structure:")
        for row in result:
            print(f"  {row[0]} - {row[1]}")
            
    except Exception as e:
        print(f"Error creating tables: {str(e)}")
