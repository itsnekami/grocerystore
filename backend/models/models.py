from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    carts = db.relationship("Cart", back_populates="user")
    orders = db.relationship("Order", back_populates="user")

    def __init__(self, username, password, is_admin=False):
        self.username = username
        self.password_hash = generate_password_hash(password, method='scrypt')
        self.is_admin = is_admin

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    products = db.relationship("Product", back_populates="category")

    def __init__(self, name):
        self.name = name

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity_available = db.Column(db.Integer, nullable=False)
    manufacture_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    # image_url = db.Column(db.String, default='default_image_url')
    category = db.relationship("Category", back_populates="products")

    def __init__(self, name, category_id, price, quantity_available, manufacture_date=None, expiry_date=None, image_url='default_image_url'):
        self.name = name
        self.category_id = category_id
        self.price = price
        self.quantity_available = quantity_available
        self.manufacture_date = manufacture_date
        self.expiry_date = expiry_date
        # self.image_url = image_url

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    cart_items = db.relationship("CartItem", back_populates="cart")
    user = db.relationship("User", back_populates="carts")

    def __init__(self, user_id):
        self.user_id = user_id

    def update_total_amount(self):
        total = sum(cart_item.total_price for cart_item in self.cart_items)
        self.total_amount = total

    def save(self):
        self.update_total_amount()
        db.session.add(self)
        db.session.commit()

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    cart = db.relationship("Cart", back_populates="cart_items")
    product = db.relationship("Product", backref="cart_items")

    def __init__(self, cart_id, product_id, quantity, total_price):
        self.cart_id = cart_id
        self.product_id = product_id
        self.quantity = quantity
        self.total_price = total_price

    def calculate_total_price(self):
        product = Product.query.get(self.product_id)
        if product:
            return product.price * self.quantity
        return 0

    def update_total_amount(self):
        self.cart.total_amount += self.calculate_total_price()

    def save(self):
        self.update_total_amount()
        db.session.add(self)
        db.session.commit()


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed = db.Column(db.Boolean, default=False)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    order_items = db.relationship("OrderItem", back_populates="order")
    user = db.relationship("User", back_populates="orders")



class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order = db.relationship("Order", back_populates="order_items")

    def calculate_total_price(self):
        return self.product.price * self.quantity
    
    def update_total_amount(self):
        self.order.total_amount += self.calculate_total_price()

    def save(self):
        self.update_total_amount()
        db.session.add(self)
        db.session.commit()
