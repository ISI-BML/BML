from datetime import UTC, datetime

from sqlalchemy.ext.hybrid import hybrid_property
from werkzeug.security import check_password_hash, generate_password_hash

from myapp.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    _email = db.Column("email", db.String(255), nullable=False, unique=True, index=True)
    _password_hash = db.Column("password_hash", db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # "user" | "admin"
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    questions = db.relationship("Question", back_populates="author", lazy=True)
    answers = db.relationship("Answer", back_populates="author", lazy=True)

    def __init__(
        self,
        email: str,
        contraseña: str | None = None,
        username: str = "",
        role: str = "user",
    ) -> None:
        self.username = username
        self.email = email
        self.role = role
        if contraseña is not None:
            self.contraseña = contraseña

    @hybrid_property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        self._email = value.strip().lower()

    @property
    def contraseña(self) -> str:
        return self._password_hash

    @contraseña.setter
    def contraseña(self, raw_password: str) -> None:
        self._password_hash = generate_password_hash(raw_password)

    def set_password(self, raw_password: str) -> None:
        self.contraseña = raw_password

    def check_password(self, raw_password: str) -> bool:
        if not self._password_hash:
            return False
        return check_password_hash(self._password_hash, raw_password)

    def login(self, email: str, contraseña: str) -> bool:
        if not email or not contraseña:
            return False
        return self.email == email.strip().lower() and self.check_password(contraseña)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


# Alias para compatibilidad directa con el Diagrama de Clases
Usuario = User
