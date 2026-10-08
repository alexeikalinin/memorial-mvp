from app.models import User
from app.config import settings


def test_only_service_owner_can_delegate_admin(auth_client, db_session, monkeypatch):
    current = db_session.query(User).first()
    current.email_verified = True
    db_session.commit()
    current.is_admin = True
    db_session.commit()
    monkeypatch.setattr(settings, 'SERVICE_OWNER_EMAIL', 'different-owner@example.com')
    assert auth_client.get('/api/v1/memorials/administration/site-admins').status_code == 403
    assert auth_client.patch('/api/v1/memorials/administration/site-admins', json={'email': current.email, 'is_admin': True}).status_code == 403
    monkeypatch.setattr(settings, 'SERVICE_OWNER_EMAIL', current.email)
    target = User(email='relative@example.com', username='relative', is_active=True, email_verified=True, is_admin=False)
    db_session.add(target); db_session.commit()
    response = auth_client.patch('/api/v1/memorials/administration/site-admins', json={'email': target.email, 'is_admin': True})
    assert response.status_code == 200, response.text
    db_session.refresh(target)
    assert target.is_admin
    assert auth_client.patch('/api/v1/memorials/administration/site-admins', json={'email': current.email, 'is_admin': False}).status_code == 400
    assert auth_client.patch('/api/v1/memorials/administration/site-admins', json={'email': target.email, 'is_admin': False}).status_code == 200
    db_session.refresh(target)
    assert not target.is_admin


def test_unverified_recipient_cannot_become_admin(auth_client, db_session, monkeypatch):
    current = db_session.query(User).first()
    current.email_verified = True
    db_session.commit()
    monkeypatch.setattr(settings, 'SERVICE_OWNER_EMAIL', current.email)
    target = User(email='unverified@example.com', username='unverified', is_active=True, email_verified=False)
    db_session.add(target); db_session.commit()
    response = auth_client.patch('/api/v1/memorials/administration/site-admins', json={'email': target.email, 'is_admin': True})
    assert response.status_code == 400
    db_session.refresh(target)
    assert not target.is_admin
