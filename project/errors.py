from flask import render_template

def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("error.html", error_code=403, error_message="Forbidden"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("error.html", error_code=404, error_message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("error.html", error_code=500, error_message="Internal Server Error"), 500

    @app.errorhandler(400)
    def bad_request_error(error):
        return render_template("error.html", error_code=400, error_message="Bad Request"), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        return render_template("error.html", error_code=401, error_message="Unauthorized"), 401