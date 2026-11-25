from myapp.models.user import Usuario


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_register_user_and_duplicate_username(client):
    res1 = client.post(
        "/api/auth/register",
        json={
            "username": "mateo",
            "email": "mateo@gmail.com",
            "password": "password123",
            "role": "user",
        },
    )
    assert res1.status_code == 201

    res_dup = client.post(
        "/api/auth/register",
        json={
            "username": "mateo",
            "email": "otro@gmail.com",
            "password": "password123",
            "role": "user",
        },
    )
    assert res_dup.status_code == 409


def test_register_admin_requires_valid_company_key(client, app):
    app.config["ADMIN_REGISTRATION_KEY"] = "secret-corp-key"

    res_fail = client.post(
        "/api/auth/register",
        json={
            "username": "admin_falso",
            "email": "falso@gmail.com",
            "password": "password123",
            "role": "admin",
            "company_key": "clave-erronea",
        },
    )
    assert res_fail.status_code == 403

    res_ok = client.post(
        "/api/auth/register",
        json={
            "username": "admin_real",
            "email": "admin@gmail.com",
            "password": "password123",
            "role": "admin",
            "company_key": "secret-corp-key",
        },
    )
    assert res_ok.status_code == 201


def test_unified_login_for_user_and_admin(client, app):
    app.config["ADMIN_REGISTRATION_KEY"] = "secret-corp-key"

    client.post(
        "/api/auth/register",
        json={
            "username": "admin_real",
            "email": "admin@gmail.com",
            "password": "password123",
            "role": "admin",
            "company_key": "secret-corp-key",
        },
    )

    login_res = client.post(
        "/api/auth/login",
        json={
            "username": "admin_real",
            "password": "password123",
        },
    )
    assert login_res.status_code == 200
    assert login_res.json["role"] == "admin"


def test_usuario_dc_encapsulation_and_login():
    usuario = Usuario(email="Mateo@Gmail.com", contraseña="mi_password_123")

    # Verifica getter/setter de email normalizado y contraseña hasheada
    assert usuario.email == "mateo@gmail.com"
    assert usuario.contraseña != "mi_password_123"

    # Verifica criterios de aceptación de login()
    assert usuario.login("mateo@gmail.com", "mi_password_123") is True
    assert usuario.login("mateo@gmail.com", "incorrecta") is False
    assert usuario.login("otro@gmail.com", "mi_password_123") is False
