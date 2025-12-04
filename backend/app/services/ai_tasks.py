"""
Сервисы для работы с AI-задачами: D-ID/HeyGen, OpenAI, ElevenLabs, Qdrant/Pinecone.
"""
import httpx
from typing import Optional, List, Dict, Tuple
from app.config import settings


# ========== D-ID (Photo Animation) ==========

async def animate_photo_did(
    image_url: str,
    script: Optional[str] = None,
    voice_id: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> Dict:
    """
    Оживить фото через D-ID API.
    
    Args:
        image_url: URL изображения
        script: Текст для озвучки (опционально)
        voice_id: ID голоса (опционально)
        webhook_url: URL для webhook'а при завершении (опционально)
    
    Returns:
        Dict с task_id и статусом
    """
    if not settings.DID_API_KEY:
        raise ValueError("DID_API_KEY not configured")
    
    url = f"{settings.DID_API_URL}/talks"
    headers = {
        "Authorization": f"Basic {settings.DID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "source_url": image_url,
        "script": {
            "type": "text",
            "input": script or "Hello, I'm here to share memories with you."
        }
    }
    
    if voice_id:
        payload["config"] = {
            "voice": voice_id
        }
    
    # Добавляем webhook если указан
    if webhook_url:
        payload["webhook"] = webhook_url
    elif settings.DID_WEBHOOK_URL:
        payload["webhook"] = settings.DID_WEBHOOK_URL
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        raise ValueError(f"D-ID API error: {e.response.status_code} - {error_detail}")
    except httpx.RequestError as e:
        raise ValueError(f"D-ID API request failed: {str(e)}")


async def get_did_talk_status(talk_id: str) -> Dict:
    """
    Проверить статус задачи анимации в D-ID.
    
    Returns:
        Dict с полями: id, status, result_url (если готово), error (если ошибка)
    """
    if not settings.DID_API_KEY:
        raise ValueError("DID_API_KEY not configured")
    
    url = f"{settings.DID_API_URL}/talks/{talk_id}"
    headers = {
        "Authorization": f"Basic {settings.DID_API_KEY}"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        raise ValueError(f"D-ID API error: {e.response.status_code} - {error_detail}")
    except httpx.RequestError as e:
        raise ValueError(f"D-ID API request failed: {str(e)}")


# ========== HeyGen (Photo Animation - Alternative) ==========

async def upload_photo_to_heygen(image_url: str) -> Optional[str]:
    """
    Загрузить фото в HeyGen и получить talking_photo_id.
    
    Returns:
        talking_photo_id или None если не удалось
    """
    if not settings.HEYGEN_API_KEY:
        return None
    
    try:
        # Сначала скачиваем изображение
        async with httpx.AsyncClient() as client:
            image_response = await client.get(image_url, timeout=30.0)
            image_response.raise_for_status()
            image_data = image_response.content
            
            # Загружаем в HeyGen
            upload_url = f"{settings.HEYGEN_API_URL}/talking_photo/upload"
            headers = {
                "X-Api-Key": settings.HEYGEN_API_KEY,
            }
            files = {
                "photo": ("photo.jpg", image_data, "image/jpeg")
            }
            
            upload_response = await client.post(upload_url, headers=headers, files=files, timeout=30.0)
            if upload_response.status_code == 200:
                result = upload_response.json()
                talking_photo_id = result.get("data", {}).get("talking_photo_id") or result.get("talking_photo_id")
                if talking_photo_id:
                    print(f"Successfully uploaded photo to HeyGen, got talking_photo_id: {talking_photo_id}")
                    return talking_photo_id
    except Exception as e:
        print(f"Warning: Failed to upload photo to HeyGen: {e}")
        # Продолжаем без talking_photo_id, попробуем использовать photo_url
    
    return None


async def animate_photo_heygen(
    image_url: str,
    script: Optional[str] = None,
    voice_id: Optional[str] = None
) -> Dict:
    """
    Оживить фото через HeyGen API (альтернатива D-ID).
    
    Args:
        image_url: URL изображения
        script: Текст для озвучки (опционально)
        voice_id: ID голоса (опционально)
    
    Returns:
        Dict с task_id и статусом
    """
    if not settings.HEYGEN_API_KEY:
        raise ValueError("HEYGEN_API_KEY not configured")
    
    url = f"{settings.HEYGEN_API_URL}/video/generate"
    headers = {
        "X-Api-Key": settings.HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }
    
    # Пытаемся сначала загрузить фото и получить talking_photo_id
    talking_photo_id = await upload_photo_to_heygen(image_url)
    
    # Формируем payload для HeyGen API
    if talking_photo_id:
        # Используем talking_photo_id если получили
        character_payload = {
            "type": "talking_photo",
            "talking_photo": {
                "talking_photo_id": talking_photo_id
            }
        }
    else:
        # Fallback на photo_url
        character_payload = {
            "type": "talking_photo",
            "talking_photo": {
                "photo_url": image_url
            }
        }
    
    payload = {
        "video_inputs": [
            {
                "character": character_payload,
                "voice": {
                    "type": "text",
                    "input_text": script or "Hello, I'm here to share memories with you.",
                    "voice_id": voice_id or settings.ELEVENLABS_VOICE_ID or "default"
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=30.0)
            response.raise_for_status()
            result = response.json()
            # Логируем ответ для отладки
            print(f"HeyGen create video response: {result}")
            return result
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        raise ValueError(f"HeyGen API error: {e.response.status_code} - {error_detail}")
    except httpx.RequestError as e:
        raise ValueError(f"HeyGen API request failed: {str(e)}")


async def get_heygen_video_status(video_id: str) -> Dict:
    """
    Проверить статус видео в HeyGen.
    
    Returns:
        Dict с полями: status, video_url (если готово), error (если ошибка)
    """
    if not settings.HEYGEN_API_KEY:
        raise ValueError("HEYGEN_API_KEY not configured")
    
    # HeyGen API v2 использует endpoint /v2/video/{video_id} для проверки статуса
    url = f"{settings.HEYGEN_API_URL}/video/{video_id}"
    headers = {
        "X-Api-Key": settings.HEYGEN_API_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
            
            # Логируем для отладки
            print(f"HeyGen status check - URL: {url}, Status: {response.status_code}")
            
            # Если 404, возможно видео еще не создано или ID неверный
            if response.status_code == 404:
                print(f"HeyGen 404 - video_id: {video_id}")
                return {
                    "data": {
                        "status": "not_found",
                        "video_url": None
                    },
                    "error": "Video not found. It may still be processing or the ID is incorrect."
                }
            
            response.raise_for_status()
            result = response.json()
            print(f"HeyGen status response: {result}")
            return result
    except httpx.HTTPStatusError as e:
        # Для 404 возвращаем структурированный ответ вместо исключения
        if e.response.status_code == 404:
            return {
                "data": {
                    "status": "not_found",
                    "video_url": None
                },
                "error": "Video not found"
            }
        error_detail = e.response.text if e.response else str(e)
        raise ValueError(f"HeyGen API error: {e.response.status_code} - {error_detail}")
    except httpx.RequestError as e:
        raise ValueError(f"HeyGen API request failed: {str(e)}")


# ========== Unified Animation Interface ==========

async def animate_photo(
    image_url: str,
    script: Optional[str] = None,
    voice_id: Optional[str] = None,
    webhook_url: Optional[str] = None
) -> Dict:
    """
    Унифицированный интерфейс для анимации фото.
    Использует HeyGen если USE_HEYGEN=true, иначе D-ID.
    
    Returns:
        Dict с полями: provider, task_id, status
    """
    if settings.USE_HEYGEN:
        result = await animate_photo_heygen(image_url, script, voice_id)
        # HeyGen может вернуть video_id в разных местах
        # Проверяем все возможные варианты структуры ответа
        video_id = (
            result.get("data", {}).get("video_id") or 
            result.get("data", {}).get("id") or
            result.get("video_id") or 
            result.get("id") or
            result.get("data", {}).get("video", {}).get("id")
        )
        
        if not video_id:
            # Логируем полный ответ для отладки
            print(f"ERROR: Could not extract video_id from HeyGen response: {result}")
            raise ValueError(f"HeyGen API did not return video_id. Response: {result}")
        
        print(f"HeyGen video_id extracted: {video_id}")
        return {
            "provider": "heygen",
            "task_id": video_id,
            "status": "processing"
        }
    else:
        result = await animate_photo_did(image_url, script, voice_id, webhook_url)
        return {
            "provider": "d-id",
            "task_id": result.get("id"),
            "status": result.get("status", "processing")
        }


async def get_animation_status(provider: str, task_id: str) -> Dict:
    """
    Унифицированный интерфейс для проверки статуса анимации.
    
    Args:
        provider: "d-id" или "heygen"
        task_id: ID задачи
    
    Returns:
        Dict с полями: status, video_url (если готово), error (если ошибка)
    """
    if provider == "heygen":
        try:
            result = await get_heygen_video_status(task_id)
            # Обрабатываем разные форматы ответа HeyGen
            if "data" in result:
                data = result.get("data", {})
                status = data.get("status", "unknown")
                # Если статус not_found, возвращаем processing (возможно еще обрабатывается)
                if status == "not_found":
                    status = "processing"
                return {
                    "status": status,
                    "video_url": data.get("video_url") or data.get("url"),
                    "error": result.get("error")
                }
            else:
                # Прямой формат ответа
                return {
                    "status": result.get("status", "unknown"),
                    "video_url": result.get("video_url") or result.get("url"),
                    "error": result.get("error")
                }
        except ValueError as e:
            # Если ошибка 404, возвращаем processing вместо ошибки
            if "404" in str(e) or "not found" in str(e).lower():
                return {
                    "status": "processing",
                    "video_url": None,
                    "error": None
                }
            raise
    else:  # d-id
        result = await get_did_talk_status(task_id)
        return {
            "status": result.get("status", "unknown"),
            "video_url": result.get("result_url"),
            "error": result.get("error")
        }


# ========== OpenAI (LLM + Embeddings) ==========

async def get_embedding(text: str, max_length: int = 8000) -> List[float]:
    """
    Получить embedding текста через OpenAI.
    
    Args:
        text: Текст для получения embedding
        max_length: Максимальная длина текста (обрезается если больше)
    
    Returns:
        Список чисел (вектор embedding)
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Обрезаем текст если слишком длинный
    if len(text) > max_length:
        text = text[:max_length]
    
    try:
        response = await client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text
        )
        
        return response.data[0].embedding
    except Exception as e:
        raise ValueError(f"OpenAI embedding error: {str(e)}")


async def generate_rag_response(
    question: str,
    context_chunks: List[Dict],
    memorial_name: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> Tuple[str, List[str]]:
    """
    Сгенерировать ответ через OpenAI с использованием RAG.
    
    Args:
        question: Вопрос пользователя
        context_chunks: Список словарей с полями: text, memory_id, score
        memorial_name: Имя человека из мемориала (для персонализации)
        system_prompt: Системный промпт (по умолчанию используется этичный)
    
    Returns:
        Tuple[answer_text, sources] - ответ и список источников (memory_id)
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")
    
    from openai import AsyncOpenAI
    
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    # Улучшенный этичный системный промпт
    default_system_prompt = f"""Ты - ИИ-аватар, созданный для сохранения памяти о человеке{f" по имени {memorial_name}" if memorial_name else ""}. 
Твоя задача - отвечать на вопросы на основе предоставленных воспоминаний и фактов.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА:
1. Отвечай на основе предоставленных фрагментов воспоминаний - используй всю релевантную информацию
2. НЕ придумывай факты, которые не упомянуты в контексте
3. НЕ используй общие знания или предположения, которых нет в воспоминаниях
4. Если в воспоминаниях есть релевантная информация (даже частично), используй её для ответа
5. Только если в воспоминаниях НЕТ НИКАКОЙ релевантной информации, скажи: "У меня нет информации на эту тему."
6. Будь уважительным, тактичным и эмпатичным
7. Используй естественный, разговорный стиль, как будто ты сам человек, о котором идет речь
8. Если в воспоминаниях есть противоречия, упомяни об этом
9. Если вопрос можно интерпретировать по-разному, используй информацию из воспоминаний для уточнения

Формат ответа:
- Будь конкретным и детальным, используя информацию из воспоминаний
- Объединяй информацию из разных воспоминаний, если это уместно
- Если вопрос касается эмоций или чувств, используй тон, соответствующий контексту
- Отвечай так, как будто ты вспоминаешь эти события"""
    
    system_prompt = system_prompt or default_system_prompt
    
    # Формирование контекста с источниками
    context_parts = []
    sources = []
    
    for i, chunk in enumerate(context_chunks, 1):
        text = chunk.get("text", "")
        memory_id = chunk.get("memory_id")
        score = chunk.get("score", 0)
        
        if text:
            context_parts.append(f"[Воспоминание #{memory_id if memory_id else i}, релевантность: {score:.2f}]\n{text}")
            if memory_id:
                sources.append(f"memory_{memory_id}")
    
    context_text = "\n\n---\n\n".join(context_parts)
    
    # Формирование промпта пользователя
    user_prompt = f"""Контекст (воспоминания о человеке):
{context_text}

Вопрос пользователя: {question}

Пожалуйста, ответь на вопрос, используя информацию из предоставленных воспоминаний. 
Используй всю релевантную информацию из воспоминаний, даже если она частично отвечает на вопрос.
Объединяй информацию из разных воспоминаний, если это помогает дать полный ответ.
Только если в воспоминаниях НЕТ НИКАКОЙ релевантной информации, скажи об этом."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=800,  # Увеличено для более детальных ответов
            top_p=0.9
        )
        
        answer = response.choices[0].message.content
        return answer, sources
    
    except Exception as e:
        raise ValueError(f"OpenAI API error: {str(e)}")


# ========== ElevenLabs (TTS) ==========

async def create_custom_voice_elevenlabs(
    audio_file_path: str,
    voice_name: str,
    description: Optional[str] = None
) -> str:
    """
    Создать кастомный голос в ElevenLabs на основе загруженного аудио.
    
    Args:
        audio_file_path: Путь к аудио файлу
        voice_name: Имя для голоса
        description: Описание голоса (опционально)
    
    Returns:
        voice_id созданного голоса
    """
    if not settings.ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not configured")
    
    url = "https://api.elevenlabs.io/v1/voices/add"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY
    }
    
    # Читаем аудио файл в байты
    audio_path = Path(audio_file_path)
    mime_type = "audio/mpeg"
    if audio_path.suffix.lower() in [".wav"]:
        mime_type = "audio/wav"
    elif audio_path.suffix.lower() in [".m4a"]:
        mime_type = "audio/m4a"
    
    # Читаем файл в байты (httpx требует байты, а не файловый объект)
    with open(audio_file_path, "rb") as audio_file:
        audio_bytes = audio_file.read()
    
    files = {
        "files": (audio_path.name, audio_bytes, mime_type)
    }
    data = {
        "name": voice_name,
    }
    if description:
        data["description"] = description
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, files=files, data=data, timeout=120.0)
            
            if response.status_code != 200:
                error_detail = response.text if response.text else "No error details"
                print(f"ElevenLabs create voice error: {response.status_code} - {error_detail}")
                raise ValueError(f"ElevenLabs API error {response.status_code}: {error_detail}")
            
            result = response.json()
            voice_id = result.get("voice_id")
            
            if not voice_id:
                raise ValueError(f"ElevenLabs did not return voice_id. Response: {result}")
            
            print(f"Successfully created custom voice: {voice_name} (ID: {voice_id})")
            return voice_id
    
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        raise ValueError(f"ElevenLabs API HTTP error: {e.response.status_code} - {error_detail}")
    except httpx.RequestError as e:
        raise ValueError(f"ElevenLabs API request failed: {str(e)}")


async def generate_speech_elevenlabs(text: str, voice_id: Optional[str] = None) -> bytes:
    """
    Сгенерировать аудио из текста через ElevenLabs.
    
    Returns:
        Байты аудио-файла (MP3)
    """
    if not settings.ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not configured")
    
    voice_id = voice_id or settings.ELEVENLABS_VOICE_ID
    if not voice_id:
        raise ValueError("ELEVENLABS_VOICE_ID not configured")
    
    # Ограничиваем длину текста (ElevenLabs имеет лимиты)
    # Максимальная длина для большинства моделей - около 5000 символов
    max_text_length = 4000
    if len(text) > max_text_length:
        text = text[:max_text_length] + "..."
        print(f"Warning: Text truncated to {max_text_length} characters for ElevenLabs")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": settings.ELEVENLABS_API_KEY
    }
    
    # Payload для ElevenLabs API
    # Пробуем сначала с model_id, если не работает - без него
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",  # Мультиязычная модель
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            
            # Детальная обработка ошибок
            if response.status_code != 200:
                error_detail = response.text if response.text else "No error details"
                print(f"ElevenLabs API error: {response.status_code} - {error_detail}")
                print(f"Request URL: {url}")
                print(f"Voice ID: {voice_id}")
                print(f"Text length: {len(text)}")
                
                # Если 400, возможно проблема с voice_id или форматом
                if response.status_code == 400:
                    # Проверяем, не достигнут ли лимит голосов
                    import json
                    try:
                        error_json = json.loads(error_detail)
                        if error_json.get("detail", {}).get("status") == "voice_limit_reached":
                            # Используем стандартный голос вместо кастомного
                            print(f"Warning: Voice limit reached. Trying with default voice.")
                            # Пробуем использовать один из стандартных голосов
                            default_voices = [
                                "21m00Tcm4TlvDq8ikWAM",  # Rachel (английский)
                                "AZnzlk1XvdvUeBnXmlld",  # Domi (английский)
                                "EXAVITQu4vr4xnSDxMaL",  # Bella (английский)
                                "ErXwobaYiN019PkySvjV",  # Antoni (английский)
                                "MF3mGyEYCl7XYWbV9V6O",  # Elli (английский)
                                "TxGEqnHWrfWFTfGW9XjX",  # Josh (английский)
                                "VR6AewLTigWG4xSOukaG",  # Arnold (английский)
                                "pNInz6obpgDQGcFmaJgB",  # Adam (английский)
                                "yoZ06aMxZJJ28mfd3POQ",  # Sam (английский)
                            ]
                            # Пробуем первый доступный стандартный голос
                            for default_voice in default_voices:
                                try:
                                    default_url = f"https://api.elevenlabs.io/v1/text-to-speech/{default_voice}"
                                    default_response = await client.post(
                                        default_url, json=payload, headers=headers, timeout=60.0
                                    )
                                    if default_response.status_code == 200:
                                        print(f"Successfully used default voice: {default_voice}")
                                        return default_response.content
                                except:
                                    continue
                            
                            # Если не удалось использовать стандартные голоса
                            raise ValueError(
                                f"ElevenLabs: Достигнут лимит кастомных голосов (3/3). "
                                f"Используйте стандартные голоса или обновите подписку. "
                                f"Ошибка: {error_detail}"
                            )
                    except:
                        pass
                    
                    raise ValueError(
                        f"ElevenLabs API error 400: {error_detail}. "
                        f"Проверьте правильность voice_id ({voice_id}) и формат запроса."
                    )
                elif response.status_code == 401:
                    raise ValueError(
                        f"ElevenLabs API error 401: Неверный API ключ. "
                        f"Проверьте ELEVENLABS_API_KEY в настройках."
                    )
                elif response.status_code == 404:
                    raise ValueError(
                        f"ElevenLabs API error 404: Voice ID не найден ({voice_id}). "
                        f"Проверьте правильность ELEVENLABS_VOICE_ID."
                    )
                else:
                    response.raise_for_status()
            
            return response.content
    
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        raise ValueError(f"ElevenLabs API HTTP error: {e.response.status_code} - {error_detail}")
    except httpx.RequestError as e:
        raise ValueError(f"ElevenLabs API request failed: {str(e)}")


# ========== Vector Database (Pinecone / Qdrant) ==========

def get_vector_db_client():
    """
    Получить клиент векторной БД (Pinecone или Qdrant).
    """
    if settings.VECTOR_DB_PROVIDER == "qdrant":
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        # Инициализация Qdrant клиента
        if settings.QDRANT_API_KEY:
            # Qdrant Cloud
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            # Локальный Qdrant
            client = QdrantClient(url=settings.QDRANT_URL)
        
        # Создание коллекции, если не существует
        try:
            collections = client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if settings.QDRANT_COLLECTION_NAME not in collection_names:
                client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=1536,  # Размерность для text-embedding-3-small
                        distance=Distance.COSINE
                    )
                )
        except Exception as e:
            print(f"Warning: Could not create Qdrant collection: {e}")
        
        return client
    
    else:  # Pinecone
        if not settings.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY not configured")
        
        from pinecone import Pinecone
        return Pinecone(api_key=settings.PINECONE_API_KEY)


def get_pinecone_client():
    """
    Получить клиент Pinecone (deprecated, используйте get_vector_db_client).
    """
    return get_vector_db_client()


async def upsert_memory_embedding(
    memory_id: int,
    memorial_id: int,
    text: str,
    embedding: List[float],
    title: Optional[str] = None
) -> str:
    """
    Сохранить embedding воспоминания в векторную БД (Qdrant или Pinecone).
    
    Returns:
        ID вектора
    """
    # Qdrant требует числовой ID (uint64) или UUID
    # Используем UUID для уникальности и совместимости
    import uuid
    id_string = f"memory_{memorial_id}_{memory_id}"
    # Создаем детерминированный UUID из строки
    vector_id_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, id_string)
    vector_id = str(vector_id_uuid)
    
    if settings.VECTOR_DB_PROVIDER == "qdrant":
        try:
            from qdrant_client.models import PointStruct
        except ImportError:
            raise ValueError("qdrant-client not installed. Run: pip install qdrant-client")
        
        client = get_vector_db_client()
        
        client.upsert(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            points=[
                PointStruct(
                    id=vector_id,  # Используем строку UUID (Qdrant принимает строку)
                    vector=embedding,
                    payload={
                        "memory_id": memory_id,
                        "memorial_id": memorial_id,
                        "text": text[:1000],  # Первые 1000 символов для метаданных
                        "title": title or ""
                    }
                )
            ]
        )
        
        return vector_id
    
    else:  # Pinecone
        pc = get_vector_db_client()
        index = pc.Index(settings.PINECONE_INDEX_NAME)
        
        index.upsert(vectors=[{
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "memory_id": memory_id,
                "memorial_id": memorial_id,
                "text": text[:500],
                "title": title or ""
            }
        }])
        
        return vector_id


async def search_similar_memories(
    memorial_id: int,
    query_embedding: List[float],
    top_k: int = 5,
    min_score: float = 0.5
) -> List[Dict]:
    """
    Найти похожие воспоминания в векторной БД (Qdrant или Pinecone).
    
    Args:
        memorial_id: ID мемориала
        query_embedding: Embedding запроса
        top_k: Количество результатов
        min_score: Минимальный score для включения в результаты
    
    Returns:
        Список словарей с полями: id, score, text, memory_id, title
    """
    try:
        if settings.VECTOR_DB_PROVIDER == "qdrant":
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
            except ImportError:
                raise ValueError("qdrant-client not installed. Run: pip install qdrant-client")
            
            client = get_vector_db_client()
            
            # Запрашиваем без фильтра (Qdrant Cloud требует индекс для фильтрации)
            # Фильтруем по memorial_id в коде
            results = client.search(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query_vector=query_embedding,
                limit=top_k * 10,  # Запрашиваем больше для фильтрации по memorial_id
                score_threshold=min_score
            )
            
            # Фильтруем результаты по memorial_id и score в коде
            filtered_results = []
            for result in results:
                if (result.payload.get("memorial_id") == memorial_id and 
                    result.score >= min_score):
                    filtered_results.append({
                        "id": str(result.id),
                        "score": result.score,
                        "text": result.payload.get("text", ""),
                        "memory_id": result.payload.get("memory_id"),
                        "title": result.payload.get("title", "")
                    })
                    if len(filtered_results) >= top_k:
                        break
            
            return filtered_results
        
        else:  # Pinecone
            pc = get_vector_db_client()
            index = pc.Index(settings.PINECONE_INDEX_NAME)
            
            results = index.query(
                vector=query_embedding,
                top_k=top_k * 2,
                include_metadata=True,
                filter={"memorial_id": memorial_id}
            )
            
            filtered_results = [
                {
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "memory_id": match.metadata.get("memory_id"),
                    "title": match.metadata.get("title", "")
                }
                for match in results.matches
                if match.score >= min_score
            ][:top_k]
            
            return filtered_results
    
    except Exception as e:
        print(f"Error searching vector DB: {e}")
        return []


async def delete_memory_embedding(memory_id: int, memorial_id: int) -> bool:
    """
    Удалить embedding воспоминания из векторной БД (Qdrant или Pinecone).
    
    Returns:
        True если успешно
    """
    try:
        # Используем тот же алгоритм для генерации ID
        import uuid
        id_string = f"memory_{memorial_id}_{memory_id}"
        vector_id_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, id_string)
        vector_id = str(vector_id_uuid)
        
        if settings.VECTOR_DB_PROVIDER == "qdrant":
            client = get_vector_db_client()
            client.delete(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                points_selector=[vector_id]  # Используем строку UUID
            )
            return True
        
        else:  # Pinecone
            pc = get_vector_db_client()
            index = pc.Index(settings.PINECONE_INDEX_NAME)
            index.delete(ids=[vector_id])
            return True
    
    except Exception as e:
        print(f"Error deleting embedding: {e}")
        return False

