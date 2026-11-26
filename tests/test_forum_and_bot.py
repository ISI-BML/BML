from datetime import UTC, datetime, timedelta

from myapp.extensions import db
from myapp.models.forum import Question
from myapp.services.bot_service import BotService


def test_bot_available_only_after_24_hours_and_answers_immediately(client, app):
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
            "bot_response_mode": "breve",
        },
    )
    assert q_res.status_code == 201
    q_id = q_res.json["id"]

    # Antes de las 24 horas no debe habilitarse ni responder
    detail_before = client.get(f"/api/questions/{q_id}")
    assert detail_before.json["can_request_bot"] is False
    early_bot = client.post(f"/api/questions/{q_id}/bot-answer")
    assert early_bot.status_code == 400

    # Pasadas 24 horas sin respuestas, se habilita y responde al instante
    with app.app_context():
        q = db.session.get(Question, q_id)
        q.created_at = datetime.now(UTC) - timedelta(hours=25)
        db.session.commit()

    detail_after = client.get(f"/api/questions/{q_id}")
    assert detail_after.json["can_request_bot"] is True

    bot_res = client.post(
        f"/api/questions/{q_id}/bot-answer",
        json={"bot_response_mode": "desarrollada"},
    )
    assert bot_res.status_code == 201
    assert bot_res.json["is_bot"] is True
    assert bot_res.json["bot_style"] == "desarrollada"
    assert "git rebase" in bot_res.json["body"]


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
        q.created_at = datetime.now(UTC) - timedelta(hours=30)
        db.session.commit()

        assert q.can_request_bot is False
        count = BotService.process_unanswered_questions()
        assert count == 0
