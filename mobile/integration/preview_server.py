"""Disposable local shared backend for browser/device QA. No production credentials/data.

Run with backend/.venv/bin/python mobile/integration/preview_server.py.
The account and DB are synthetic; AI response is explicitly stubbed for transport QA.
"""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
RUN_DIR = Path(tempfile.mkdtemp(prefix='vspomin-mobile-qa-'))
os.environ.update(DATABASE_URL=f'sqlite:///{RUN_DIR}/test.db', DEBUG='false', USE_S3='false',
                  OPENAI_API_KEY='', FISH_AUDIO_API_KEY='', ELEVENLABS_API_KEY='',
                  INVESTOR_DEMO_MODE='false', SMTP_HOST='', RESEND_API_KEY='',
                  CORS_ORIGINS='http://localhost:8081,http://127.0.0.1:8081,http://localhost:5188,http://127.0.0.1:5188',
                  PUBLIC_FRONTEND_URL='http://localhost:5188', FRONTEND_URL='http://localhost:5188')
sys.path.insert(0, str(ROOT / 'backend'))
from app.main import app
from app.db import SessionLocal
from app.models import User, Memorial, MemorialAccess, UserRole
from app.auth import hash_password
from app.schemas import AvatarChatResponse
import app.api.auth as auth
import app.api.memorials as memorials
import app.api.ai as ai
app.state.limiter.enabled = False
auth.send_verification_email = lambda *args, **kwargs: None
memorials.UPLOAD_DIR = RUN_DIR
memorials.THUMBNAILS_DIR = RUN_DIR
sys.modules['app.workers.worker'] = SimpleNamespace(create_memory_embedding_task=SimpleNamespace(delay=lambda **kw: None))
async def synthetic_chat(request, db, current_user, invite_token):
    # Deliberately preserve normal access checks even though the paid provider is stubbed.
    from app.auth import require_memorial_access
    require_memorial_access(request.memorial_id, current_user, db, allow_public=True)
    return AvatarChatResponse(answer='Тест связи: мобильный чат получил ответ от общего сервера. Это вымышленная проверка без внешнего AI.', sources=[])
ai._avatar_chat_response = synthetic_chat
with SessionLocal() as db:
    user = User(email='mobile-qa@example.com', username='mobileqa', full_name='Тестовая семья',
                hashed_password=hash_password('MobileTest123!'), email_verified=True, is_active=True, is_demo=True)
    db.add(user); db.flush()
    page = Memorial(name='Анна Соколова · тест', description='Вымышленная страница для проверки мобильного приложения.', owner_id=user.id, is_public=False)
    db.add(page); db.flush()
    db.add(MemorialAccess(memorial_id=page.id,user_id=user.id,role=UserRole.OWNER))
    db.commit()

if __name__ == '__main__':
    import uvicorn
    print('Synthetic QA API http://localhost:8000; temporary DB:', RUN_DIR)
    uvicorn.run(app,host='127.0.0.1',port=8000)
