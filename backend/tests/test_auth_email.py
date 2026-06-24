"""
Тесты email-верификации и сброса пароля.

Покрывает:
  POST /auth/verify-email
  POST /auth/resend-verification
  POST /auth/password-reset
  POST /auth/password-reset/confirm
"""
import secrets
from datetime import datetime, timedelta, timezone

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _mock_email(monkeypatch):
    """Заглушка email-сервиса — не отправляем реальные письма в тестах."""
    import app.api.auth as auth_module
    monkeypatch.setattr(auth_module, "send_verification_email", lambda *a, **kw: None)
    monkeypatch.setattr(auth_module, "send_password_reset_email", lambda *a, **kw: None)


def _get_user_from_db(db_session, email: str):
    from app.models import User
    db_session.expire_all()  # сброс stale-кэша после commit в endpoint
    return db_session.query(User).filter(User.email == email).first()


# ── register: email_verified starts False ────────────────────────────────────

class TestRegisterEmailVerifiedState:
    def test_register_sets_email_verified_false(self, client):
        resp = client.post("/api/v1/auth/register", json={
            "email": "check@example.com",
            "username": "checkuser",
            "full_name": "Check User",
            "password": "password123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email_verified"] is False

    def test_register_creates_verification_token(self, client, db_session):
        client.post("/api/v1/auth/register", json={
            "email": "tokencheck@example.com",
            "username": "tokencheck",
            "password": "password123",
        })
        user = _get_user_from_db(db_session, "tokencheck@example.com")
        assert user is not None
        assert user.verification_token is not None
        assert len(user.verification_token) > 10
        assert user.verification_token_expires is not None


# ── POST /auth/verify-email ───────────────────────────────────────────────────

class TestVerifyEmail:
    def test_verify_valid_token(self, client, db_session):
        """Валидный токен — верифицирует, очищает токен."""
        client.post("/api/v1/auth/register", json={
            "email": "verify@example.com",
            "username": "verifyuser",
            "password": "password123",
        })
        user = _get_user_from_db(db_session, "verify@example.com")
        token = user.verification_token

        resp = client.post(f"/api/v1/auth/verify-email?token={token}", json={}, headers={"X-Lang": "en"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "Email verified successfully"

        fresh = _get_user_from_db(db_session, "verify@example.com")
        assert fresh.email_verified is True
        assert fresh.verification_token is None
        assert fresh.verification_token_expires is None

    def test_verify_invalid_token(self, client):
        """Несуществующий токен → 400."""
        resp = client.post("/api/v1/auth/verify-email?token=nonexistenttoken123", headers={"X-Lang": "en"})
        assert resp.status_code == 400
        assert "Invalid" in resp.json()["detail"]

    def test_verify_already_verified(self, client, db_session):
        """Повторная верификация → 200 с сообщением 'already verified'."""
        client.post("/api/v1/auth/register", json={
            "email": "already@example.com",
            "username": "alreadyverified",
            "password": "password123",
        })
        user = _get_user_from_db(db_session, "already@example.com")
        token = user.verification_token

        # Первый раз
        client.post(f"/api/v1/auth/verify-email?token={token}")
        # Создадим новый токен вручную для уже-верифицированного юзера
        new_token = secrets.token_urlsafe(32)
        user.email_verified = True
        user.verification_token = new_token
        db_session.commit()

        resp = client.post(f"/api/v1/auth/verify-email?token={new_token}", json={}, headers={"X-Lang": "en"})
        assert resp.status_code == 200
        assert "already verified" in resp.json()["message"]

    def test_verify_expired_token(self, client, db_session):
        """Просроченный токен → 400 с упоминанием expired."""
        client.post("/api/v1/auth/register", json={
            "email": "expired@example.com",
            "username": "expireduser",
            "password": "password123",
        })
        user = _get_user_from_db(db_session, "expired@example.com")
        # Делаем токен просроченным
        user.verification_token_expires = datetime.now(timezone.utc) - timedelta(hours=1)
        db_session.commit()

        resp = client.post(f"/api/v1/auth/verify-email?token={user.verification_token}", json={}, headers={"X-Lang": "en"})
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()


# ── POST /auth/resend-verification ────────────────────────────────────────────

class TestResendVerification:
    def test_resend_for_unverified_user(self, client, db_session, auth_headers):
        """Неверифицированный пользователь — получает новый токен."""
        # registered_user уже создан через auth_headers (email_verified=False)
        resp = client.post("/api/v1/auth/resend-verification", headers={**auth_headers, "X-Lang": "en"})
        assert resp.status_code == 200
        assert "sent" in resp.json()["message"].lower()

        user = _get_user_from_db(db_session, "test@example.com")
        assert user.verification_token is not None

    def test_resend_for_verified_user(self, client, db_session, auth_headers):
        """Уже верифицированный — возвращает 'already verified'."""
        user = _get_user_from_db(db_session, "test@example.com")
        user.email_verified = True
        db_session.commit()

        resp = client.post("/api/v1/auth/resend-verification", headers={**auth_headers, "X-Lang": "en"})
        assert resp.status_code == 200
        assert "already verified" in resp.json()["message"]

    def test_resend_requires_auth(self, client):
        """Без токена — 401."""
        resp = client.post("/api/v1/auth/resend-verification")
        assert resp.status_code == 401

    def test_resend_updates_token(self, client, db_session, auth_headers):
        """Повторный resend создаёт новый токен (не старый)."""
        user = _get_user_from_db(db_session, "test@example.com")
        old_token = user.verification_token

        client.post("/api/v1/auth/resend-verification", headers=auth_headers)
        fresh = _get_user_from_db(db_session, "test@example.com")
        assert fresh.verification_token != old_token


# ── POST /auth/password-reset ─────────────────────────────────────────────────

class TestPasswordReset:
    def test_reset_known_email(self, client, db_session, registered_user):
        """Существующий email — создаёт токен, возвращает 200."""
        resp = client.post("/api/v1/auth/password-reset",
                           json={"email": "test@example.com"}, headers={"X-Lang": "en"})
        assert resp.status_code == 200
        assert "receive" in resp.json()["message"].lower()

        user = _get_user_from_db(db_session, "test@example.com")
        assert user.password_reset_token is not None
        assert user.password_reset_token_expires is not None

    def test_reset_unknown_email_still_200(self, client):
        """Несуществующий email — тоже 200 (защита от перебора)."""
        resp = client.post("/api/v1/auth/password-reset",
                           json={"email": "nobody@example.com"})
        assert resp.status_code == 200

    def test_reset_token_expires_in_1h(self, client, db_session, registered_user):
        """Токен сброса пароля действителен ~1 час."""
        client.post("/api/v1/auth/password-reset",
                    json={"email": "test@example.com"})
        db_session.expire_all()
        user = _get_user_from_db(db_session, "test@example.com")
        expires = user.password_reset_token_expires
        # SQLite returns naive datetimes — normalize before comparing
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = expires - now
        # Должно быть примерно 1 час (±5 минут)
        assert timedelta(minutes=55) < delta < timedelta(hours=1, minutes=5)


# ── POST /auth/password-reset/confirm ─────────────────────────────────────────

class TestPasswordResetConfirm:
    def _get_reset_token(self, client, db_session, email="test@example.com"):
        client.post("/api/v1/auth/password-reset", json={"email": email})
        db_session.expire_all()
        user = _get_user_from_db(db_session, email)
        return user.password_reset_token

    def test_confirm_valid_token(self, client, db_session, registered_user):
        """Валидный токен — меняет пароль, очищает токен."""
        token = self._get_reset_token(client, db_session)
        resp = client.post("/api/v1/auth/password-reset/confirm",
                           json={"token": token, "new_password": "newpassword456"}, headers={"X-Lang": "en"})
        assert resp.status_code == 200
        assert "updated" in resp.json()["message"].lower()

        # Токен очищен
        fresh = _get_user_from_db(db_session, "test@example.com")
        assert fresh.password_reset_token is None
        assert fresh.password_reset_token_expires is None

    def test_confirm_new_password_works(self, client, db_session, registered_user):
        """После сброса можно войти с новым паролем."""
        token = self._get_reset_token(client, db_session)
        client.post("/api/v1/auth/password-reset/confirm",
                    json={"token": token, "new_password": "brandnewpass789"})

        resp = client.post("/api/v1/auth/login",
                           json={"email": "test@example.com", "password": "brandnewpass789"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_confirm_old_password_rejected(self, client, db_session, registered_user):
        """Старый пароль после сброса не работает."""
        token = self._get_reset_token(client, db_session)
        client.post("/api/v1/auth/password-reset/confirm",
                    json={"token": token, "new_password": "brandnewpass789"})

        resp = client.post("/api/v1/auth/login",
                           json={"email": "test@example.com", "password": "testpassword123"})
        assert resp.status_code == 401

    def test_confirm_invalid_token(self, client, registered_user):
        """Несуществующий токен → 400."""
        resp = client.post("/api/v1/auth/password-reset/confirm",
                           json={"token": "fakeresettoken999", "new_password": "newpassword456"}, headers={"X-Lang": "en"})
        assert resp.status_code == 400
        assert "Invalid" in resp.json()["detail"]

    def test_confirm_expired_token(self, client, db_session, registered_user):
        """Просроченный токен → 400."""
        token = self._get_reset_token(client, db_session)
        user = _get_user_from_db(db_session, "test@example.com")
        user.password_reset_token_expires = datetime.now(timezone.utc) - timedelta(hours=2)
        db_session.commit()

        resp = client.post("/api/v1/auth/password-reset/confirm",
                           json={"token": token, "new_password": "newpassword456"}, headers={"X-Lang": "en"})
        assert resp.status_code == 400
        assert "expired" in resp.json()["detail"].lower()

    def test_confirm_token_one_time_use(self, client, db_session, registered_user):
        """Токен одноразовый — повторное использование → 400."""
        token = self._get_reset_token(client, db_session)
        client.post("/api/v1/auth/password-reset/confirm",
                    json={"token": token, "new_password": "firstnewpass123"})

        resp = client.post("/api/v1/auth/password-reset/confirm",
                           json={"token": token, "new_password": "secondnewpass456"})
        assert resp.status_code == 400

    def test_confirm_short_password_rejected(self, client, db_session, registered_user):
        """Слишком короткий новый пароль → 422 (Pydantic validation)."""
        token = self._get_reset_token(client, db_session)
        resp = client.post("/api/v1/auth/password-reset/confirm",
                           json={"token": token, "new_password": "short"})
        assert resp.status_code == 422


# ── Full flow: register → verify → reset password ────────────────────────────

class TestFullAuthFlow:
    def test_full_email_verification_flow(self, client, db_session):
        """Полный сценарий: регистрация → верификация через токен → /me показывает verified=True."""
        # 1. Регистрация
        resp = client.post("/api/v1/auth/register", json={
            "email": "flow@example.com",
            "username": "flowuser",
            "full_name": "Flow User",
            "password": "flowpass123",
        })
        assert resp.status_code == 201
        assert resp.json()["email_verified"] is False

        # 2. Токен из БД
        user = _get_user_from_db(db_session, "flow@example.com")
        token = user.verification_token

        # 3. Верификация
        resp = client.post(f"/api/v1/auth/verify-email?token={token}", json={})
        assert resp.status_code == 200

        # 4. Логин + /me → email_verified=True
        login = client.post("/api/v1/auth/login",
                            json={"email": "flow@example.com", "password": "flowpass123"})
        jwt = login.json()["access_token"]
        me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {jwt}"})
        assert me.status_code == 200
        assert me.json()["email_verified"] is True

    def test_full_password_reset_flow(self, client, db_session):
        """Полный сценарий: регистрация → запрос сброса → смена пароля → вход с новым."""
        client.post("/api/v1/auth/register", json={
            "email": "resetflow@example.com",
            "username": "resetflowuser",
            "password": "oldpass123",
        })

        # Запрос сброса
        client.post("/api/v1/auth/password-reset",
                    json={"email": "resetflow@example.com"})
        user = _get_user_from_db(db_session, "resetflow@example.com")
        token = user.password_reset_token

        # Подтверждение
        resp = client.post("/api/v1/auth/password-reset/confirm",
                           json={"token": token, "new_password": "newpass789"})
        assert resp.status_code == 200

        # Вход с новым паролем
        login = client.post("/api/v1/auth/login",
                            json={"email": "resetflow@example.com", "password": "newpass789"})
        assert login.status_code == 200
        assert "access_token" in login.json()
