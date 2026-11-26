from flask import Blueprint, g, jsonify, request

from myapp.extensions import db
from myapp.models.forum import Answer, Question
from myapp.services.bot_service import BotService

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

    if bot_mode not in ("breve", "detallada", "desarrollada"):
        return jsonify(
            {"error": "El modo del bot debe ser 'breve' o 'desarrollada'."}
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


@api_forum_bp.get("/<int:question_id>")
def get_question(question_id: int):
    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    return jsonify(
        {
            "id": question.id,
            "title": question.title,
            "body": question.body,
            "bot_response_mode": question.bot_response_mode,
            "can_request_bot": question.can_request_bot,
            "answers": [
                {
                    "id": ans.id,
                    "body": ans.body,
                    "is_bot": ans.is_bot,
                    "bot_style": ans.bot_style,
                }
                for ans in question.answers
            ],
        }
    ), 200


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
        if data["bot_response_mode"] not in ("breve", "detallada", "desarrollada"):
            return jsonify({"error": "Modo inválido."}), 400
        question.bot_response_mode = data["bot_response_mode"]

    db.session.commit()
    return jsonify(
        {
            "id": question.id,
            "bot_response_mode": question.bot_response_mode,
        }
    ), 200


@api_forum_bp.delete("/<int:question_id>")
def delete_question(question_id: int):
    if g.user is None:
        return jsonify({"error": "Autenticación requerida."}), 401

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    if question.author_id != g.user.id and not g.user.is_admin:
        return jsonify({"error": "No autorizado para eliminar esta pregunta."}), 403

    db.session.delete(question)
    db.session.commit()
    return jsonify({"message": "Pregunta eliminada correctamente."}), 200


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


@api_forum_bp.delete("/<int:question_id>/answers/<int:answer_id>")
def delete_answer(question_id: int, answer_id: int):
    if g.user is None:
        return jsonify({"error": "Autenticación requerida."}), 401

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    answer = db.session.get(Answer, answer_id)
    if not answer or answer.question_id != question.id:
        return jsonify({"error": "Respuesta no encontrada."}), 404

    if answer.author_id != g.user.id and not g.user.is_admin:
        return jsonify({"error": "No autorizado para eliminar esta respuesta."}), 403

    db.session.delete(answer)
    db.session.commit()
    return jsonify({"message": "Respuesta eliminada correctamente."}), 200


@api_forum_bp.post("/<int:question_id>/bot-answer")
def request_bot_answer(question_id: int):
    if g.user is None:
        return jsonify({"error": "Autenticación requerida."}), 401

    question = db.session.get(Question, question_id)
    if not question:
        return jsonify({"error": "Pregunta no encontrada."}), 404

    if question.author_id != g.user.id and not g.user.is_admin:
        return jsonify(
            {"error": "Solo el autor de la pregunta puede consultar al bot."}
        ), 403

    data = request.get_json(silent=True) or {}
    mode = data.get("bot_response_mode")
    if mode is not None and mode not in ("breve", "detallada", "desarrollada"):
        return jsonify({"error": "El modo debe ser 'breve' o 'desarrollada'."}), 400

    try:
        bot_answer = BotService.answer_question_on_demand(question, mode=mode)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(
        {
            "id": bot_answer.id,
            "is_bot": True,
            "bot_style": bot_answer.bot_style,
            "body": bot_answer.body,
        }
    ), 201
