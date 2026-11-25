from datetime import UTC, datetime, timedelta

from myapp.extensions import db
from myapp.models.forum import Question
from myapp.services.bot_service import BotService


def test_bot_answers_unanswered_question_in_chosen_style(client, app):
    client.post(
        "/api/auth/register",
        json={
            "username": "alumno1",
            "email": "alumno1@gmail.com",
            "password": "password123",
        },
    )
    client.post(
        "/api/auth/login",
        json={
            "username": "alumno1",
            "password": "password123",
        },
    )

    q_res = client.post(
        "/api/questions",
        json={
            "title": "¿Cómo funciona git rebase?",
            "body": "No entiendo la diferencia entre merge y rebase en ramas.",
            "bot_response_mode": "detallada",
        },
    )
    assert q_res.status_code == 201
    q_id = q_res.json["id"]

    with app.app_context():
        q = db.session.get(Question, q_id)
        q.created_at = datetime.now(UTC) - timedelta(minutes=45)
        db.session.commit()

        count = BotService.process_unanswered_questions(delay_minutes=30)
        assert count == 1

        q_updated = db.session.get(Question, q_id)
        assert len(q_updated.answers) == 1
        assert q_updated.answers[0].is_bot is True
        assert q_updated.answers[0].bot_style == "detallada"
        assert "git rebase" in q_updated.answers[0].body


def test_bot_skips_questions_already_answered_by_human(client, app):
    client.post(
        "/api/auth/register",
        json={
            "username": "alumno2",
            "email": "alumno2@gmail.com",
            "password": "password123",
        },
    )
    client.post(
        "/api/auth/login",
        json={
            "username": "alumno2",
            "password": "password123",
        },
    )

    q_res = client.post(
        "/api/questions",
        json={
            "title": "¿Qué es WSGI?",
            "body": "Necesito un ejemplo simple.",
            "bot_response_mode": "breve",
        },
    )
    q_id = q_res.json["id"]

    ans_res = client.post(
        f"/api/questions/{q_id}/answers",
        json={"body": "Es la interfaz estándar entre servidores web y apps Python."},
    )
    assert ans_res.status_code == 201

    with app.app_context():
        q = db.session.get(Question, q_id)
        q.created_at = datetime.now(UTC) - timedelta(minutes=60)
        db.session.commit()

        count = BotService.process_unanswered_questions(delay_minutes=30)
        assert count == 0
