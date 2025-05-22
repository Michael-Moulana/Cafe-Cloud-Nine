from functools import wraps
from flask import session, redirect, url_for, flash

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
            return redirect(url_for('main.error'))  # Ensure you have an 'error' route defined
        return f(*args, **kwargs)
    return decorated_function
