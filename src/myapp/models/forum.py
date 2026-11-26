from datetime import UTC, datetime, timedelta

from myapp.extensions import db


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bot_response_mode = db.Column(
        db.String(20), nullable=False, default="breve"
    )  # "breve" | "detallada"
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    author = db.relationship("User", back_populates="questions")
    answers = db.relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy=True,
    )

    @property
    def has_answers(self) -> bool:
        return len(self.answers) > 0

    @property
    def can_request_bot(self) -> bool:
        if self.has_answers:
            return False
        created = (
            self.created_at
            if self.created_at.tzinfo is not None
            else self.created_at.replace(tzinfo=UTC)
        )
        return datetime.now(UTC) - created >= timedelta(hours=24)


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    is_bot = db.Column(db.Boolean, nullable=False, default=False)
    bot_style = db.Column(db.String(20), nullable=True)  # "breve" | "detallada" | None
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    question = db.relationship("Question", back_populates="answers")
    author = db.relationship("User", back_populates="answers")
