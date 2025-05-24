from functools import wraps
from flask import session, abort

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'admin':
             abort(403)
    return decorated_function
