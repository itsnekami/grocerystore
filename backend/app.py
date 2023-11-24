from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from models.models import db, User, Category, Product, Cart, CartItem, Order, OrderItem

app = Flask(__name__, template_folder= "../frontend/templates")
app.config['SECRET_KEY'] = 'hellosafwaan'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.sqlite3'
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/registration', methods=['GET', 'POST'])
def user_registration():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if password != confirm_password:
            return "Passwords do not match."
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already exists."
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return "User created successfully! Go Back to homepage to login"
    return render_template('user_registration.html')

@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('store'))
        else:
            return "Invalid username or password."
    return render_template('user_login.html')

@app.route('/store')
def store():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        user_name = user.username if user else "Guest"
    categories = Category.query.all()
    return render_template('store.html', categories=categories, user_name=user_name)

@app.route('/load_products/<int:category_id>')
def load_products(category_id):
    category = Category.query.get(category_id)
    if category:
        products = category.products[3:8]  # Adjust the range as needed
        return render_template('load_products.html', products=products)
    else:
        return jsonify({'error': 'Category not found'}), 404
    
@app.route('/category/<int:category_id>')
def category_page(category_id):
    category = Category.query.get(category_id)
    if category:
        products = category.products
        return render_template('category_page.html', category=category, products=products)
    else:
        return "Category not found."

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    products = Product.query.filter(Product.name.ilike(f'%{query}%')).all()
    return render_template('store.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

        product_id = request.form.get('product_id')
        product = Product.query.get(product_id)

        if not user or not product:
            return jsonify({'message': 'User or product not found'}), 400

        cart = Cart.query.filter_by(user_id=user_id, is_completed=False).first()
        if not cart:
            cart = Cart(user_id=user_id)
            db.session.add(cart)
            db.session.commit()  

        cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product.id).first()
        if cart_item:
            cart_item.quantity += 1
        else:
            cart_item = CartItem(cart_id=cart.id, product_id=product.id, quantity=1, total_price=product.price)
            db.session.add(cart_item)

        cart.update_total_amount() 
        cart_item.update_total_amount()  
        db.session.commit()

        return jsonify({'message': 'Product added to cart successfully'}), 200

    return jsonify({'message': 'User not logged in'}), 401




@app.route('/view_cart')
def view_cart():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 400
        cart = Cart.query.filter_by(user_id=user_id, is_completed=False).first()
        if not cart:
            return jsonify({'message': 'No active cart for this user'}), 200
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        return render_template('view_cart.html', user=user, cart=cart, cart_items=cart_items)

    return jsonify({'message': 'User not logged in'}), 401

@app.route('/update_quantity/<int:cart_item_id>', methods=['POST'])
def update_quantity(cart_item_id):
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 400

        cart_item = CartItem.query.get(cart_item_id)
        if not cart_item:
            return jsonify({'message': 'Cart item not found'}), 400

        if cart_item.cart.user_id != user_id:
            return jsonify({'message': 'Unauthorized'}), 401

        action = request.form['action']
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
        else:
            return jsonify({'message': 'Invalid action'}), 400

        cart_item.total_price = cart_item.calculate_total_price()
        cart_item.cart.update_total_amount()

        db.session.commit()

        return redirect(url_for('view_cart'))
    return jsonify({'message': 'User not logged in'}), 401


@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)

        if not user:
            return jsonify({'message': 'User not found'}), 400

        cart = Cart.query.filter_by(user_id=user_id, is_completed=False).first()
        if not cart or cart.total_amount == 0:
            return jsonify({'message': 'No items in the cart to checkout'}), 400

        cart.is_completed = True
        order = Order(user_id=user_id, total_amount=cart.total_amount)
        db.session.add(order)
        db.session.commit()

        return jsonify({'message': 'Checkout successful'}), 200

    return jsonify({'message': 'User not logged in'}), 401

@app.route('/orders', methods = ['GET'])
def view_orders():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            orders = Order.query.filter_by(user_id=user_id).all()
            return render_template('orders.html', user=user, orders=orders)
    return redirect(url_for('index')) 

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = User.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            if admin.is_admin:
                session['admin_id'] = admin.id
                return redirect(url_for('admin_dashboard'))
            else:
                return "You are not authorized as an admin."
        else:
            return "Invalid username or password."
    return render_template('admin_login.html')

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_id' in session:
        user = User.query.get(session['admin_id'])
        user_name = user.username if user else "Admin"
        categories = Category.query.all()
        return render_template('/categories/admin_dashboard.html', user_name=user_name, categories=categories)
    else:   
        return "You are not authorized to access this page."

@app.route('/admin/add_category', methods=['GET', 'POST'])
def add_category():
    if 'admin_id' in session:
        if request.method == 'POST':
            category_name = request.form['category_name']
            new_category = Category(name=category_name)
            db.session.add(new_category)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        return render_template('/categories/add_category.html')
    else:
        return "You are not authorized to access this page."

@app.route('/admin/edit_category/<int:category_id>', methods=['GET', 'POST'])
def edit_category(category_id):
    if 'admin_id' in session:
        category = Category.query.get(category_id)
        if request.method == 'POST':
            category.name = request.form['new_category_name']
            db.session.commit()
            flash(f"Category '{category.name}' has been deleted successfully.", "success")
            return redirect(url_for('admin_dashboard'))
        return render_template('/categories/edit_category.html', category=category)
    else:
        return "You are not authorized to access this page."

@app.route('/admin/delete_category/<int:category_id>', methods=['GET', 'POST'])
def delete_category(category_id):
    if 'admin_id' in session:
        category = Category.query.get(category_id)
        if request.method == 'POST':
            db.session.delete(category)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
        return render_template('/categories/delete_category.html', category=category)
    else:
        return "You are not authorized to access this page."

@app.route('/admin/<int:category_id>/products', methods=['GET'])
def admin_products(category_id):
    if 'admin_id' in session:
        category = Category.query.get(category_id)
        if category:
            products = category.products
            return render_template('/products/admin_products.html', category=category, products=products)
        else:
            flash("Category not found", "error")
            return redirect(url_for('admin_dashboard'))
    else:
        return "You are not authorized to access this page."

@app.route('/admin/add_product/<int:category_id>', methods=['GET', 'POST'])
def add_product(category_id):
    if 'admin_id' in session:
        category = Category.query.get(category_id)
        if request.method == 'POST':
            product_name = request.form['product_name']
            price = float(request.form['price'])
            quantity_available = int(request.form.get('quantity_available', 0))
            manufacture_date_str = request.form['manufacture_date']
            manufacture_date = None if not manufacture_date_str else datetime.strptime(manufacture_date_str, '%Y-%m-%d').date()
            expiry_date_str = request.form['expiry_date']
            expiry_date = None if not expiry_date_str else datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            # image_url = request.form['image_url']
            
            new_product = Product(
                name=product_name, 
                category_id=category_id, 
                price=price, 
                quantity_available=quantity_available,
                manufacture_date=manufacture_date, 
                expiry_date=expiry_date, 
            )
            db.session.add(new_product)
            db.session.commit()
            return redirect(url_for('admin_products', category_id=category_id))
        return render_template('/products/add_product.html', category=category)
    else:
        return "You are not authorized to access this page."
    
@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'admin_id' in session:
        product = Product.query.get(product_id)
        category_id = product.category_id
        if request.method == 'POST':
            product.name = request.form['product_name']
            product.price = float(request.form['price'])
            product.quantity_available = int(request.form['quantity_available'])
            manufacture_date_str = request.form['manufacture_date']
            product.manufacture_date = None if not manufacture_date_str else datetime.strptime(manufacture_date_str, '%Y-%m-%d').date()
            expiry_date_str = request.form['expiry_date']
            product.expiry_date = None if not expiry_date_str else datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            # product.image_url = request.form['image_url']
            db.session.commit()
            return redirect(url_for('admin_products', category_id=category_id))
        return render_template('/products/edit_product.html', product=product)
    else:
        return "You are not authorized to access this page."

@app.route('/admin/delete_product/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    if 'admin_id' in session:
        product = Product.query.get(product_id)
        if request.method == 'POST':
            db.session.delete(product)
            db.session.commit()
            flash(f"Product '{product.name}' has been deleted successfully.", "success")
            return redirect(url_for('admin_products', category_id = product.category_id))
        return render_template('/products/delete_product.html', product=product)
    else:
        return "You are not authorized to access this page."
    
@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
