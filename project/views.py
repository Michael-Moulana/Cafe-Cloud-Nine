from flask import Blueprint, render_template, jsonify, redirect, session, request, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegisterForm
from .models import get_user_by_email, create_user
from . import mysql

main = Blueprint("main", __name__)

@main.route('/')
def home():
    return render_template('index.html')  # assuming you have templates/index.html

@main.route('/item1')
def item1_page():
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT itemID, name, price, description, image FROM item WHERE itemID = %s", (1,))
    item_data = cur.fetchone()
    cur.close()
    
    cart_items = session.get('cart', {})
    cart_item_count = sum(item['quantity'] for item in cart_items.values())

    if not item_data:
        flash("Item not found.")
        return redirect(url_for('main.home'))
        
    return render_template('item1.html', item=item_data, cart_item_count=cart_item_count)


@main.route('/about')
def about():
    cart_items = session.get('cart', {})
    cart_item_count = sum(item['quantity'] for item in cart_items.values())
    return render_template('about.html', cart_item_count=cart_item_count)

@main.route('/menu')
def menu():
    # You would fetch items from DB here
    cur = mysql.connection.cursor()
    cur.execute("SELECT itemID, name, price, description, image, category FROM item")
    all_items = cur.fetchall()
    cur.close()
    cart_items = session.get('cart', {})
    cart_item_count = sum(item['quantity'] for item in cart_items.values())
    return render_template('menu.html', items=all_items, cart_item_count=cart_item_count)

@main.route('/contact')
def contact():
    cart_items = session.get('cart', {})
    cart_item_count = sum(item['quantity'] for item in cart_items.values())
    return render_template('contact.html', cart_item_count=cart_item_count)

@main.route('/cart')
def view_cart():
    cart = session.get('cart', {})
    cart_item_count = sum(item['quantity'] for item in cart.values())
    total_price = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, total_price=total_price, cart_item_count=cart_item_count)

@main.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
   

    cur = mysql.connection.cursor()
    
    cur.execute("SELECT itemID, name, price FROM item WHERE itemID = %s", (item_id,))
    item_from_db = cur.fetchone() 
    cur.close()

    if item_from_db:
        cart = session.get('cart', {}) 

        item_id_str = str(item_id) 

        if item_id_str in cart:
            cart[item_id_str]['quantity'] += 1
        else:
            cart[item_id_str] = {
                'itemID': item_from_db['itemID'], 
                'name': item_from_db['name'],
                'price': float(item_from_db['price']),
                'quantity': 1
            }
        
        session['cart'] = cart # saves updated cart back to session
        session.modified = True # makes sure session is saved
        flash(f"Added {item_from_db['name']} to cart!")
    else:
        flash("Item not found.")

    # Redirect back to the page the user was on, or to home/cart page
    
    return redirect(url_for('main.item1_page'))

@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing = get_user_by_email(form.email.data)
        if existing:
            flash("Email already registered.")
            return redirect(url_for("main.register"))

        hashed = generate_password_hash(form.password.data)
        create_user(form.name.data, form.email.data, hashed)
        flash("Registration successful. Please log in.")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)

@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user and check_password_hash(user['password'], form.password.data):
            session['user_id'] = user['userID']
            session['user_name'] = user['name']
            session['role'] = user['role']
            return redirect(url_for("main.home"))
        else:
            flash("Invalid credentials.")
    return render_template("login.html", form=form)

@main.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("main.login"))

@main.route('/test_db')
def test_db_connection():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT VERSION()") # A simple query that should always work if connected
        db_version = cur.fetchone()
        cur.close()
        if db_version:
            return jsonify(message="Successfully connected to MySQL!", version=db_version)
        else:
            return jsonify(message="Connected, but no version info retrieved."), 500
    except Exception as e:
        # Print the full error to the Flask console for debugging
        print(f"Database connection error: {e}")
        return jsonify(error=str(e)), 500