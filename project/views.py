
from flask import Blueprint, render_template, redirect, session, request, url_for, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegisterForm
from .models import get_user_by_email, create_user, update_user_details, get_all_items, get_carousels, search_items, get_item_by_id, get_user_details_by_id, get_user_addresses, create_order, add_order_items, get_user_orders, get_user_profile, update_item_in_db, add_item_to_db, remove_item_from_db, get_all_user_orders, update_order_status, get_category_enum_values, update_enum_categories, get_reviews, insert_inquiry, insert_review
from .db import mysql
from datetime import datetime
import re
import os
from .decorators import admin_required


main = Blueprint("main", __name__)

@main.app_context_processor
def inject_cart_total_items():
    def get_cart_total_items():
        cart = session.get('cart', {})
        return sum(item['quantity'] for item in cart.values())
    
    return dict(cart_total_items=get_cart_total_items())

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
    categories = get_category_enum_values()

    items = search_items(query, category)

    reviews = get_reviews()
    
    return render_template("index.html", items=items, carousels=carousels, query=query, category=category, reviews=reviews, categories=categories)


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
    item = get_item_by_id(item_id)

    if not item:
        flash("Invalid item.", "danger")
        return redirect(request.referrer or url_for('main.index'))

    try:
        quantity_str = request.form.get('quantity', '1') 
        quantity = int(quantity_str)
    except ValueError:
        flash("Invalid quantity. Please enter a number.", "danger")
        return redirect(url_for('main.item_detail_page', item_id=item_id)) 

    if quantity <= 0:
        flash("Quantity must be at least 1.", "danger")
        return redirect(url_for('main.item_detail_page', item_id=item_id))

    if item:
        cart = session.get('cart', {})
        if str(item_id) in cart:
            cart[str(item_id)]['quantity'] += quantity
        else:
            cart[str(item_id)] = {
                'itemID': item['itemID'],
                'name': item['name'],
                'price': float(item['price']),
                'quantity': quantity
            }

        session['cart'] = cart

        flash(f"Added {quantity} of {item['name']} to cart!")
    else:
        flash("Item not found.", "danger")
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


# updates the quantity of items
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

# allows the user to empty the cart
@main.route('/clear_cart', methods = ['POST'])
def clear_cart():
    session['cart'] = {}
    flash("The cart is now empty")
    return redirect(url_for('main.cart'))


@main.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = session.get('cart', {})
    subtotal = sum(item['price'] * item['quantity'] for item in cart.values())

    delivery_option = session.get('delivery_option', 'standard-delivery')

    # Calculate delivery fee based on stored option
    if delivery_option == 'standard-delivery':
        delivery_fee = 5
    elif delivery_option == 'express-delivery':
        delivery_fee = 10
    elif delivery_option == 'eco-delivery':
        delivery_fee = 3
    else:
        delivery_fee = 5

    total = subtotal + delivery_fee

    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to place an order.", "warning")
        return redirect(url_for('main.login'))

    user_details = get_user_details_by_id(user_id)
    addresses = get_user_addresses(user_id)

    if request.method == 'POST':
        # validate & process the main checkout form
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address_id = request.form.get('address')
        payment_method = request.form.get('payment-method')
        errors = {}

        if not name or not re.match(r'^[A-Za-z\s]+$', name):
            errors['name'] = "Name must contain only letters and spaces."
        if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors['email'] = "Invalid email address."
        if not phone or not re.match(r'^0[0-9]{9}$', phone):
            errors['phone'] = "Phone number must start with 0 and be 10 digits long."
        if errors:
            return render_template('checkout.html', errors=errors, cart=cart,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
                delivery_option=delivery_option,
                payment_method=payment_method,
                user_details=user_details,
                addresses=addresses)

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

        order_id = create_order(
            user_id,
            datetime.now(),
            address_id,
            'pending',
            total,
            payment_method,
            delivery_option)

        
        add_order_items(order_id, list(cart.values()))
        session['cart'] = {}
        flash("Your order has been placed successfully!", "success")
        return redirect(url_for('main.order_success'))

    return render_template(
        'checkout.html',
        cart=cart,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        delivery_option=delivery_option,
        payment_method='card',  # or fetch from session
        user_details=user_details,
        addresses=addresses
    )


@main.route('/select_delivery_option', methods=['POST'])
def select_delivery_option():
    delivery_option = request.form.get('deliveryOption')

    session['delivery_option'] = delivery_option
    flash("Delivery option updated.", "info")
    return redirect(url_for('main.checkout'))



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


@main.route('/contact', methods=['POST'])
def add_contact():
        if request.method == 'POST':
           name = request.form['name']
           email = request.form['email']
           subject = request.form['subject']
           message = request.form['message']

           insert_inquiry(name, email, subject, message)

           flash("Your Message has been sent successfully!", "success")
           return redirect(url_for('main.contact'))
        return render_template('contact.html')


@main.route('/add_review', methods=['POST'])
def add_review():
        user_id = session.get('user_id')
        if request.method == 'POST':
           review_text = request.form['review_text']

           insert_review(user_id, review_text)

           flash("Your review has been sent successfully!", "success")
           return redirect(url_for('main.index'))
        return render_template('index.html')

# admin routes
@main.route('/admin')
@admin_required
def admin():
    items = get_all_items()
    orders = get_all_user_orders()
    categories = get_category_enum_values()

    # List image files from static/img
    image_dir = os.path.join(os.path.dirname(__file__), 'static', 'img')
    image_list = os.listdir(image_dir) if os.path.exists(image_dir) else []

    return render_template('admin.html', items=items, image_list=image_list, orders=orders, categories=categories)

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


@main.route('/admin/categories/add', methods=['POST'])
@admin_required
def add_category():
    new_category = request.form.get('new_category').strip().lower()
    categories = get_category_enum_values()

    if new_category in categories:
        flash("Category already exists.", "warning")
        return redirect(url_for('main.admin'))

    categories.append(new_category)
    update_enum_categories(categories)
    flash("Category added successfully.", "success")
    return redirect(url_for('main.admin'))


@main.route('/admin/categories/update/<category>', methods=['POST'])
@admin_required
def update_category(category):

    flash("Category updated successfully.", "success")
    return redirect(url_for('main.admin'))


@main.route('/admin/categories/delete/<category>', methods=['GET', 'POST'])
@admin_required
def delete_category(category):
    categories = get_category_enum_values()

    if category not in categories:
        flash("Category not found.", "danger")
        return redirect(url_for('main.admin'))

    # Prevent deletion if items still use it
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) as count FROM item WHERE category = %s", (category,))
    count = cur.fetchone()['count']
    cur.close()

    if count > 0:
        flash("Cannot delete category in use by items.", "danger")
        return redirect(url_for('main.admin'))

    updated_categories = [c for c in categories if c != category]
    update_enum_categories(updated_categories)

    flash("Category deleted successfully.", "success")
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
