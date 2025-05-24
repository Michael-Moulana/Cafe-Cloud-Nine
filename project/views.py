
from flask import Blueprint, render_template, redirect, session, request, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegisterForm
from .models import get_user_by_email, create_user, update_user_details, get_all_items, get_carousels, search_items, get_item_by_id, get_user_details_by_id, get_user_addresses, create_order, add_order_items, get_user_orders, get_user_profile, update_item_in_db, add_item_to_db, remove_item_from_db, get_all_user_orders, get_order_items, update_order_status
from .db import mysql
from datetime import datetime

import os
from .decorators import admin_required


main = Blueprint("main", __name__)



@main.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing = get_user_by_email(form.email.data)
        if existing:
            flash("Email already registered.", "danger")
            return redirect(url_for("main.register"))

        hashed = generate_password_hash(form.password.data)
        create_user(form.name.data, form.email.data, hashed)
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("main.login"))
    return render_template("register.html", form=form)

@main.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user and check_password_hash(user['password'], form.password.data):
            session.permanent = True
            session['user_id'] = user['userID']
            session['user_name'] = user['name']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for("main.admin"))
            else:
                return redirect(url_for("main.index"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html", form=form)

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))

@main.route('/')
def index():
    items = get_all_items()
    carousels = get_carousels()

    query = request.args.get('query', '').strip()
    category = request.args.get('category', '').strip()
    
    items = search_items(query, category)
    
    return render_template("index.html", items=items, carousels=carousels, query=query, category=category)

@main.route('/item/<int:item_id>')
def item_detail_page(item_id):
    item_data = get_item_by_id(item_id)
    
    cart_items = session.get('cart', {})
    cart_item_count = sum(item['quantity'] for item in cart_items.values())

    if not item_data:
        flash("Item not found.")
        return redirect(url_for('main.index'))
        
    return render_template('item.html', item=item_data, cart_item_count=cart_item_count)



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
    item=get_item_by_id(item_id)

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
    else:
        flash("Item not found.", "error")

    next_url = request.referrer
    if next_url:
        return redirect(next_url)
    else:
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
@main.route('/update_quantity/<int:item_id>', methods = ['POST'])
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


@main.route('/checkout', methods = ['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    if not cart:
        flash("Your cart is empty. Please add items before proceeding to checkout.")
        return redirect(url_for('main.cart'))
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
    delivery_option = 'standard-delivery'
    delivery_fee = 5
    payment_method = 'card'

    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to place an order.", "warning")
        return redirect(url_for('main.login'))
        
    
    user_details = get_user_details_by_id(user_id)

    addresses = get_user_addresses(user_id)


    if user_details:
        name, email, phone, addressID  = user_details        

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address_id = request.form.get('address')
        print(f"Address ID: { address_id}")
        delivery_option = request.form.get('deliveryOption')
        payment_method = request.form.get('payment-method')

        # Update delivery fee
        if delivery_option == 'standard-delivery':
            delivery_fee = 5
        elif delivery_option == 'express-delivery':
            delivery_fee = 10
        elif delivery_option == 'eco-delivery':
            delivery_fee = 3

        total = subtotal + delivery_fee

        if not all([name, email, phone, address_id, delivery_option, payment_method]):
            flash("All fields are required. Please complete the form.", "danger")
            return render_template(
        'checkout.html',
        cart=cart,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        delivery_option=delivery_option,
        payment_method=payment_method,
        user_details=user_details,
        addresses=addresses
    )

        order_id = create_order(user_id,
            datetime.now(),
            address_id,
            'pending',
            total,
            payment_method,
            
            delivery_option)

        add_order_items(
                order_id, list(cart.values())
            )


        session['cart'] = {}
        flash("Your order has been placed successfully!", "success")
        return redirect(url_for('main.order_success'))
    
        

    else:
        if delivery_option == 'standard-delivery':
            delivery_fee = 5
        elif delivery_option == 'express-delivery':
            delivery_fee = 10
        elif delivery_option == 'eco-delivery':
            delivery_fee = 3
        

    total = subtotal + delivery_fee

    return render_template(
        'checkout.html',
        cart=cart,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        delivery_option=delivery_option,
        payment_method=payment_method,
        user_details=user_details,
        addresses=addresses
    )



@main.route('/order-success')
def order_success():
    return render_template('order_success.html')


@main.route('/profile', methods=['GET', 'POST'])
def profile():
    user_id = session['user_id']

    user = get_user_profile(user_id)

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        street_name = request.form['address']
        city = request.form['city']
        postcode = request.form['postcode']
        territory = request.form['territory']

        update_user_details(user_id, name, email, phone, street_name, city, postcode, territory)
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('main.profile'))

    raw_orders = get_user_orders(user_id)

    from collections import defaultdict
    orders = defaultdict(lambda: {"items": [], "order_date": None, "total": 0, "status": ""})

    for row in raw_orders:
        oid = row['orderID']
        orders[oid]["order_date"] = row['order_date']
        orders[oid]["total"] = row['total_amount']
        orders[oid]["status"] = row['status']
        orders[oid]["items"].append({
            "name": row['item_name'],
            "quantity": row['quantity'],
            "unit_price": row['unit_price'],
            "total_price": row['total_price']
        })

    return render_template("profile.html", user=user, orders=orders)

@main.route('/update_profile', methods=['POST'])
def update_profile():

    user_id = session['user_id']
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    street_name = request.form['address']
    city = request.form['city']
    postcode = request.form['postcode']
    territory = request.form['territory']

    update_user_details(user_id, name, email, phone, street_name, city, postcode, territory)
    
    flash("Profile updated successfully!", "success")
    return redirect(url_for('main.profile'))


# admin routes
@main.route('/admin')
@admin_required
def admin():
    items = get_all_items()
    orders = get_all_user_orders()
    print(orders)

    # List image files from static/img
    image_dir = os.path.join(os.path.dirname(__file__), 'static', 'img')
    image_list = os.listdir(image_dir) if os.path.exists(image_dir) else []

    return render_template('admin.html', items=items, image_list=image_list, orders=orders)

@main.route("/admin/update/<int:item_id>", methods=["POST"])
@admin_required
def update_item(item_id):
    name = request.form["name"]
    price = request.form["price"]
    description = request.form["description"]
    category = request.form["category"]
    image = request.form["image"]

    update_item_in_db(item_id, name, price, description, category, image) 
    flash("Item updated successfully.")
    return redirect(url_for("main.admin"))

@main.route('/admin/add_item', methods=['POST'])
@admin_required
def add_item():
    name = request.form['name']
    price = request.form['price']
    description = request.form['description']
    category = request.form['category']
    image = 'img/' + request.form['image']

    add_item_to_db(name, price, description, category, image) 
    flash("New item added successfully.")
    return redirect(url_for('main.admin'))

@main.route('/admin/delete_item/<int:item_id>', methods=['POST'])
@admin_required
def delete_item(item_id):
    remove_item_from_db(item_id)
    flash("Item deleted successfully.")
    return redirect(url_for('main.admin'))


@main.route('/admin/order/<int:order_id>', methods=['POST'])
@admin_required
def update_order_status_route(order_id):
    new_status = request.form.get('status')
    update_order_status(order_id, new_status)
    flash(f"Order {order_id} status updated to '{new_status}'.")
    return redirect(url_for('main.admin'))

# test error routes
# @main.route('/error/400')
# def trigger_400():
#     abort(400)

# @main.route('/error/401')
# def trigger_401():
#     abort(401)

# @main.route('/error/403')
# def trigger_403():
#     abort(403)

# @main.route('/error/404')
# def trigger_404():
#     abort(404)
