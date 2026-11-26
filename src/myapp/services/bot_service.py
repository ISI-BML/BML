import json
import logging
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta

from flask import current_app

from myapp.extensions import db
from myapp.models.forum import Answer, Question

logger = logging.getLogger(__name__)


class BotService:
    @staticmethod
    def normalize_mode(mode: str | None) -> str:
        if mode in ("detallada", "desarrollada"):
            return "desarrollada"
        return "breve"

    @classmethod
    def build_prompt(cls, question: Question) -> str:
        if cls.normalize_mode(question.bot_response_mode) == "desarrollada":
            style_instruction = (
                "Proporciona una respuesta DESARROLLADA y detallada, estructurada paso a paso, "
                "explicando el porqué de la solución y dando un ejemplo claro."
            )
        else:
            style_instruction = (
                "Proporciona una respuesta BREVE, directa y concisa (máximo 3 oraciones) "
                "que resuelva la duda puntual sin rodeos."
            )

        return (
            f"Eres el asistente técnico oficial de un foro de preguntas y respuestas.\n"
            f"Instrucción de formato: {style_instruction}\n\n"
            f"Título de la pregunta: {question.title}\n"
            f"Detalle de la pregunta: {question.body}\n\n"
            f"Responde en español de forma precisa y acorde a lo consultado:"
        )

    @classmethod
    def generate_answer_text(cls, question: Question) -> str:
        prompt = cls.build_prompt(question)
        api_key = current_app.config.get("LLM_API_KEY", "")
        model = current_app.config.get("LLM_MODEL", "gemini-2.5-flash")

        if not api_key:
            return cls._fallback_response(question)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode(
            "utf-8"
        )
        req = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except (
            urllib.error.URLError,
            json.JSONDecodeError,
            KeyError,
            IndexError,
            TypeError,
            TimeoutError,
            OSError,
        ) as exc:
            logger.error("Error invocando IA para question_id=%s: %s", question.id, exc)
            return cls._fallback_response(question)

    @classmethod
    def _fallback_response(cls, question: Question) -> str:
        if cls.normalize_mode(question.bot_response_mode) == "desarrollada":
            return (
                f"Respuesta desarrollada automática sobre «{question.title}»:\n"
                f"1. Contexto: Analizando tu consulta («{question.body[:120]}...»), el problema requiere revisar los parámetros involucrados.\n"
                f"2. Pasos recomendados: Verifica la estructura de entrada, valida los estados intermedios y comprueba la ejecución.\n"
                f"3. Conclusión: Siguiendo esta secuencia resolverás el caso planteado."
            )
        return (
            f"Respuesta breve sobre «{question.title}»: Revisa la configuración asociada a "
            f"«{question.body[:80]}» y valida los datos de entrada para resolverlo directamente."
        )

    @classmethod
    def answer_question_on_demand(
        cls, question: Question, mode: str | None = None
    ) -> Answer:
        if not question.can_request_bot:
            raise ValueError(
                "La consulta al bot solo está disponible tras 24 horas sin respuestas."
            )

        if mode is not None:
            question.bot_response_mode = cls.normalize_mode(mode)

        reply_text = cls.generate_answer_text(question)
        bot_answer = Answer(
            body=reply_text,
            question_id=question.id,
            author_id=None,
            is_bot=True,
            bot_style=cls.normalize_mode(question.bot_response_mode),
        )
        db.session.add(bot_answer)
        db.session.commit()
        return bot_answer

    @classmethod
    def process_unanswered_questions(cls, delay_minutes: int | None = None) -> int:
        if delay_minutes is None:
            delay_minutes = current_app.config.get(
                "BOT_RESPONSE_DELAY_MINUTES", 24 * 60
            )

        cutoff_time = datetime.now(UTC) - timedelta(minutes=delay_minutes)

        unanswered_questions = db.session.scalars(
            db.select(Question)
            .where(~Question.answers.any())
            .where(Question.created_at <= cutoff_time)
        ).all()

        answered_count = 0
        for question in unanswered_questions:
            reply_text = cls.generate_answer_text(question)
            bot_answer = Answer(
                body=reply_text,
                question_id=question.id,
                author_id=None,
                is_bot=True,
                bot_style=cls.normalize_mode(question.bot_response_mode),
            )
            db.session.add(bot_answer)
            answered_count += 1

        if answered_count > 0:
            db.session.commit()

        return answered_count
