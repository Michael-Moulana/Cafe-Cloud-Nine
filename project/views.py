from flask import Blueprint, render_template, redirect, session, request, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .forms import LoginForm, RegisterForm
from .models import get_user_by_email, create_user

main = Blueprint("main", __name__)

@main.route('/')
def home():
    return render_template('index.html')  # assuming you have templates/index.html

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