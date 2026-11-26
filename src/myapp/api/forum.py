from flask import Blueprint, g, jsonify, request

from myapp.extensions import db
from myapp.models.forum import Answer, Question

api_forum_bp = Blueprint("api_forum", __name__, url_prefix="/api/questions")


@api_forum_bp.post("")
def create_question():
    if g.user is None:
        return jsonify({"error": "Autenticación requerida."}), 401

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    bot_mode = data.get("bot_response_mode", "breve")

    if not title or not body:
        return jsonify({"error": "Título y contenido son obligatorios."}), 400

    if bot_mode not in ("breve", "detallada"):
        return jsonify(
            {"error": "El modo del bot debe ser 'breve' o 'detallada'."}
        ), 400

    question = Question(
        title=title,
        body=body,
        author_id=g.user.id,
        bot_response_mode=bot_mode,
    )
    db.session.add(question)
    db.session.commit()

    return jsonify(
        {
            "id": question.id,
            "title": question.title,
            "bot_response_mode": question.bot_response_mode,
        }
    ), 201


@api_forum_bp.patch("/<int:question_id>")
def update_bot_preference(question_id: int):
    if g.user is None:
        return jsonify({"error": "Autenticación requerida."}), 401

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    if question.author_id != g.user.id and not g.user.is_admin:
        return jsonify({"error": "No autorizado para modificar esta pregunta."}), 403

    data = request.get_json(silent=True) or {}
    if "bot_response_mode" in data:
        if data["bot_response_mode"] not in ("breve", "detallada"):
            return jsonify({"error": "Modo inválido."}), 400
        question.bot_response_mode = data["bot_response_mode"]

    db.session.commit()
    return jsonify(
        {
            "id": question.id,
            "bot_response_mode": question.bot_response_mode,
        }
    ), 200


@api_forum_bp.post("/<int:question_id>/answers")
def create_answer(question_id: int):
    if g.user is None:
        return jsonify({"error": "Autenticación requerida."}), 401

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    if not body:
        return jsonify({"error": "La respuesta no puede estar vacía."}), 400

    answer = Answer(
        body=body,
        question_id=question.id,
        author_id=g.user.id,
        is_bot=False,
    )
    db.session.add(answer)
    db.session.commit()

    return jsonify({"id": answer.id, "is_bot": False, "body": answer.body}), 201
