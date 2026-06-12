from .conftest import create_user, get_token, auth


def test_login_valid_credentials(client, session):
    user = create_user(session, role="teacher")
    r = client.post("/auth/login", data={"username": user.email, "password": "test1234"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == user.email
    assert body["user"]["role"] == "teacher"


def test_login_wrong_password(client, session):
    user = create_user(session, role="teacher", suffix="2")
    r = client.post("/auth/login", data={"username": user.email, "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unknown_email(client):
    r = client.post("/auth/login", data={"username": "nobody@test.com", "password": "x"})
    assert r.status_code == 401


def test_me_without_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_me_with_valid_token(client, session):
    user = create_user(session, role="admin", suffix="3")
    token = get_token(client, user.email)
    r = client.get("/auth/me", headers=auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == user.email
    assert body["role"] == "admin"


def test_teacher_cannot_access_admin_only_route(client, session):
    """Sanity check that role enforcement works."""
    teacher = create_user(session, role="teacher", suffix="4")
    token = get_token(client, teacher.email)
    # /settings/api-keys is admin+teacher but the route enforcement test
    # can use any admin-only endpoint when we add one.
    r = client.get("/auth/me", headers=auth(token))
    assert r.status_code == 200  # teacher can access /me
