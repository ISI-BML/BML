from functools import wraps

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from myapp.extensions import db
from myapp.models.user import User
from myapp.services.auth_service import AuthError, authenticate_user, register_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = db.session.get(User, user_id) if user_id else None


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


def admin_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None or not g.user.is_admin:
            flash("Acceso restringido a administradores.", "error")
            return redirect(url_for("auth.login"))
        return view(**kwargs)

    return wrapped_view


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            user = register_user(
                username=request.form.get("username", ""),
                email=request.form.get("email", ""),
                password=request.form.get("password", ""),
                role=request.form.get("role", "user"),
                company_key=request.form.get("company_key"),
            )
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("forum.index"))
        except AuthError as err:
            flash(err.message, "error")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = authenticate_user(
                username=request.form.get("username", ""),
                password=request.form.get("password", ""),
            )
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("forum.index"))
        except AuthError as err:
            flash(err.message, "error")

    return render_template("auth/login.html")


@auth_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
