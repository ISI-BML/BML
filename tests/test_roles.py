from myapp.extensions import db
from myapp.models.user import User


def _register_and_login(
    client, username: str, email: str, password: str = "password123"
):
    client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": password},
    )
    client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )


def test_user_and_admin_roles_permissions(client, app):
    # 1. Usuario común crea pregunta y respuesta
    _register_and_login(client, "user_uno", "user1@gmail.com")

    q_res = client.post(
        "/api/questions",
        json={
            "title": "Consulta sobre índices en SQL",
            "body": "¿Cuándo conviene crear un índice compuesto?",
        },
    )
    assert q_res.status_code == 201
    q_id = q_res.json["id"]

    a_res = client.post(
        f"/api/questions/{q_id}/answers",
        json={"body": "Aporto un ejemplo adicional de mi consulta."},
    )
    assert a_res.status_code == 201
    a_id = a_res.json["id"]

    # 2. Otro usuario común NO puede eliminar preguntas ni respuestas ajenas
    _register_and_login(client, "user_dos", "user2@gmail.com")

    del_other_ans = client.delete(f"/api/questions/{q_id}/answers/{a_id}")
    assert del_other_ans.status_code == 403

    del_other_q = client.delete(f"/api/questions/{q_id}")
    assert del_other_q.status_code == 403

    # 3. Administrador puede crear preguntas/respuestas y eliminar las de otros usuarios
    _register_and_login(client, "admin_foro", "admin@gmail.com")
    with app.app_context():
        user_uno = db.session.scalar(db.select(User).where(User.username == "user_uno"))
        admin_user = db.session.scalar(
            db.select(User).where(User.username == "admin_foro")
        )
        assert user_uno.role == "user"
        assert user_uno.is_admin is False
        admin_user.role = "admin"
        db.session.commit()
        assert admin_user.role == "admin"
        assert admin_user.is_admin is True

    # El admin puede hacer preguntas y respuestas igual que un usuario
    admin_q = client.post(
        "/api/questions",
        json={
            "title": "Reglas del foro",
            "body": "Bienvenidos al espacio de consultas.",
        },
    )
    assert admin_q.status_code == 201

    admin_a = client.post(
        f"/api/questions/{q_id}/answers",
        json={"body": "Respuesta oficial del administrador."},
    )
    assert admin_a.status_code == 201

    # El admin elimina la respuesta y la pregunta del otro usuario
    del_ans_ok = client.delete(f"/api/questions/{q_id}/answers/{a_id}")
    assert del_ans_ok.status_code == 200

    del_q_ok = client.delete(f"/api/questions/{q_id}")
    assert del_q_ok.status_code == 200

    assert client.get(f"/api/questions/{q_id}").status_code == 404
