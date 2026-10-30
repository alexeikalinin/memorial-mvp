"""Rich disposable mobile QA fixture. All people, users and media are synthetic."""
import math
import struct
import wave
from datetime import datetime
from pathlib import Path
import importlib.util
import sys
import subprocess

# Reuse the isolated baseline: empty provider keys, temporary DB, stub chat.
spec = importlib.util.spec_from_file_location('mobile_qa_baseline', Path(__file__).with_name('preview_server.py'))
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
from app.models import Memorial, MemorialAccess, User, UserRole, Memory, Media, MediaType, FamilyRelationship
from app.api import media as media_api
from app.schemas import AvatarChatResponse
from PIL import Image, ImageDraw
media_api.UPLOAD_DIR = baseline.RUN_DIR
photo = baseline.RUN_DIR / 'synthetic-portrait.png'
image = Image.new('RGB', (600,800), '#e8d8bb')
draw = ImageDraw.Draw(image); draw.ellipse((130,100,470,440), fill='#af9273'); draw.rectangle((80,460,520,800), fill='#746859')
image.save(photo)
audio = baseline.RUN_DIR / 'synthetic-audio.wav'
with wave.open(str(audio),'wb') as stream:
    stream.setparams((1,2,16000,0,'NONE','not compressed'))
    stream.writeframes(b''.join(struct.pack('<h',int(1000*math.sin(i*2*math.pi*220/16000))) for i in range(32000)))
video = baseline.RUN_DIR / 'synthetic-video.mp4'
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','color=c=brown:s=320x240:d=1','-pix_fmt','yuv420p',str(video)],check=True)
with baseline.SessionLocal() as db:
    person=db.get(Memorial,1)
    person.name='Соколова Александра Константиновна'
    person.gender='female';person.maiden_name='Васильева'
    person.description='Вымышленная семья для проверки приложения. Здесь проверяются длинные имена, материалы, история и права доступа.'
    person.birth_date=datetime(1961,5,17);person.death_date=datetime(2019,10,21)
    for path,kind,mime in [(photo,MediaType.PHOTO,'image/png'),(audio,MediaType.AUDIO,'audio/wav'),(video,MediaType.VIDEO,'video/mp4')]:
        item=Media(memorial_id=1,file_name=path.name,file_path=str(path),file_size=path.stat().st_size,media_type=kind,mime_type=mime)
        db.add(item);db.flush()
        if kind==MediaType.PHOTO:person.cover_photo_id=item.id
    db.add(Memory(memorial_id=1,title='Большая семейная история',content=('Мы собирались всей семьёй за большим столом и рассказывали истории о путешествиях. '*7),event_date=datetime(1995,6,12),status='approved',contributor_name='Семья'))
    db.add(Memory(memorial_id=1,title='На рассмотрении',content='История от гостя на проверку владельцем.',status='pending',contributor_name='Гость'))
    owner=db.get(User,person.owner_id)
    relative=Memorial(name='Соколов Константин Александрович',gender='male',owner_id=owner.id,is_public=False)
    db.add(relative);db.flush();db.add(MemorialAccess(memorial_id=relative.id,user_id=owner.id,role=UserRole.OWNER))
    db.add(FamilyRelationship(memorial_id=1,related_memorial_id=relative.id,relationship_type='parent'))
    db.add(FamilyRelationship(memorial_id=relative.id,related_memorial_id=1,relationship_type='child'))
    for username,role in [('viewer',UserRole.VIEWER),('editor',UserRole.EDITOR)]:
        user=User(email=f'{username}-qa@example.com',username=username,full_name=username,hashed_password=baseline.hash_password('MobileTest123!'),email_verified=True,is_active=True,is_demo=True)
        db.add(user);db.flush();db.add(MemorialAccess(memorial_id=1,user_id=user.id,role=role))
    public=Memorial(name='Публичная тестовая страница',owner_id=owner.id,is_public=True)
    db.add(public);db.flush();db.add(MemorialAccess(memorial_id=public.id,user_id=owner.id,role=UserRole.OWNER))
    db.commit()

async def synthetic_chat(request, db, current_user, invite_token):
    from app.auth import require_memorial_access
    require_memorial_access(request.memorial_id,current_user,db,allow_public=True)
    return AvatarChatResponse(answer='Проверка: история найдена в тестовом семейном архиве.',sources=['Большая семейная история'],audio_url='/api/v1/media/2' if request.include_audio else None)
baseline.ai._avatar_chat_response=synthetic_chat

if __name__=='__main__':
    import uvicorn
    print('Synthetic readiness API; DB:',baseline.RUN_DIR,flush=True)
    uvicorn.run(baseline.app,host='127.0.0.1',port=8000)
