from flask import Blueprint, render_template, redirect, session, request, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegisterForm
from .models import get_user_by_email, create_user
from .db import mysql

main = Blueprint("main", __name__)

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
            return redirect(url_for("main.index"))
        else:
            flash("Invalid credentials.")
    return render_template("login.html", form=form)

@main.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("main.login"))

@main.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM item")
    items = cur.fetchall()
    cur.execute("SELECT * FROM carousel")
    carousels = cur.fetchall()

    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip()
    sql = "SELECT * FROM item"
    filters = []
    params = []

    if query:
        filters.append("name LIKE %s")
        params.append(f"%{query}%")
    if category:
        filters.append("category = %s")
        params.append(category)
    if filters:
        sql += " WHERE " + " AND ".join(filters)

    cur.execute(sql, params)
    items = cur.fetchall()
    cur.close()
    
    return render_template("index.html", items=items, carousels=carousels, query=query, category=category)

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/menu')
def menu():
    return render_template('menu.html')

@main.route('/contact')
def contact():
    return render_template('contact.html')

@main.route('/cart')
def cart():
    cart = session.get('cart', {})
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, total=total)

@main.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT itemID, name, price FROM item WHERE itemID = %s", (item_id,))
    item = cur.fetchone()
    cur.close()

    if item:
        cart = session.get('cart', {})
        if str(item_id) in cart:
            cart[str(item_id)]['quantity'] += 1
        else:
            cart[str(item_id)] = {
                'itemID': item['itemID'],
                'name': item['name'],
                'price': float(item['price']),
                'quantity': 1
            }

        session['cart'] = cart
        flash(f"Added {item['name']} to cart!")

    return redirect(url_for('main.index'))

#This code allows the user to remove items
@main.route('/remove_from_cart/<int:item_id>', methods = ['POST'])
def remove_from_cart(item_id):
    cart = session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        remove_item = cart.pop(item_id_str)
        session['cart'] = cart
        flash(f"Removed {remove_item['name']}from cart.")
    
    else:
        flash("item not found.")
    
    return redirect(url_for('main.cart'))

#This code updates the quantity of items
@main.route('/update_quanitiy/<int:item_id>', methods = ['POST'])
def update_quantity(item_id):
    cart = session.get('cart', {})
    item_id_str = str(item_id)

    if item_id_str in cart:
        try:
            quantity = int(request.form.get('quantity', 1))
            if quantity > 0:
                cart[item_id_str]['quantity'] = quantity
                flash(f"Updated quantity for {cart[item_id_str]['name']}.")
            
            else:
                cart.pop(item_id_str)
                flash("Item removed from cart (quantity set to 0).")
        
        except ValueError:
            flash("Invalid quantity.")
    
    else:
        flash("Item not found.")

    session['cart'] = cart
    return redirect(url_for('main.cart'))

#This code allows the user to empty the cart
@main.route('/clear_cart', methods = ['POST'])
def clear_cart():
    session['cart'] = {}
    flash("The cart is now empty")
    return redirect(url_for('main.cart'))


@main.route('/checkout')
def checkout():
    return render_template('checkout.html')

