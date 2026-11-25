import hmac
import re

from flask import current_app

from myapp.extensions import db
from myapp.models.user import User

GMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", re.IGNORECASE)


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_user(
    username: str,
    email: str,
    password: str,
    role: str = "user",
    company_key: str | None = None,
) -> User:
    username = username.strip()
    email = email.strip().lower()

    if not username or len(username) < 3:
        raise AuthError("El nombre de usuario debe tener al menos 3 caracteres.", 400)

    if not GMAIL_REGEX.match(email):
        raise AuthError(
            "Debe ingresar una dirección de Gmail válida (@gmail.com).", 400
        )

    if not password or len(password) < 6:
        raise AuthError("La contraseña debe tener al menos 6 caracteres.", 400)

    if role not in ("user", "admin"):
        raise AuthError("Rol inválido.", 400)

    if role == "admin":
        expected_key = current_app.config.get("ADMIN_REGISTRATION_KEY", "")
        if (
            not expected_key
            or not company_key
            or not hmac.compare_digest(company_key, expected_key)
        ):
            raise AuthError(
                "Clave de empresa inválida para registro de administrador.", 403
            )

    if db.session.scalar(db.select(User).filter_by(username=username)):
        raise AuthError("El nombre de usuario ya está en uso.", 409)

    if db.session.scalar(db.select(User).filter_by(email=email)):
        raise AuthError("El Gmail ya se encuentra registrado.", 409)

    user = User(username=username, email=email, role=role)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return user


def authenticate_user(username: str, password: str) -> User:
    clean_id = username.strip()
    user = db.session.scalar(
        db.select(User).where(
            (User.username == clean_id) | (User.email == clean_id.lower())
        )
    )
    if not user or not user.login(user.email, password):
        raise AuthError("Credenciales incorrectas.", 401)
    return user
