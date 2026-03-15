"""
Сервисы для работы с AI-задачами: D-ID/HeyGen, OpenAI, ElevenLabs, Qdrant/Pinecone.
"""
import httpx
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from app.config import settings


# ========== D-ID (Photo Animation) ==========

async def animate_photo_did(
    image_url: str,
    script: Optional[str] = None,
    voice_id: Optional[str] = None,
    webhook_url: Optional[str] = None,
    audio_url: Optional[str] = None,
) -> Dict:
    """
    Оживить фото через D-ID API.

    Args:
        image_url: URL изображения
        script: Текст для озвучки (опционально)
        voice_id: ID голоса (опционально)
        webhook_url: URL для webhook'а при завершении (опционально)
        audio_url: URL готового аудио для lip-sync (если передан, используется вместо TTS)

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

    if audio_url:
        # Используем готовое аудио (ElevenLabs) для lip-sync
        script_payload = {
            "type": "audio",
            "audio_url": audio_url,
        }
    else:
        script_payload = {
            "type": "text",
            "input": script or "Привет, я здесь, чтобы поделиться воспоминаниями с тобой."
        }

    payload = {
        "source_url": image_url,
        "script": script_payload,
    }

    if voice_id and not audio_url:
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
    
    Согласно документации HeyGen, для Photo Avatars API нужно:
    1. Создать talking_photo через POST /v2/talking_photo с photo_url в JSON
    2. Или загрузить файл напрямую
    
    Returns:
        talking_photo_id или None если не удалось
    """
    if not settings.HEYGEN_API_KEY:
        print("Warning: HEYGEN_API_KEY not configured")
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "X-Api-Key": settings.HEYGEN_API_KEY,
                "Content-Type": "application/json"
            }
            
            # Пробуем разные варианты endpoints для создания talking_photo
            # Возможно, нужен другой путь или версия API
            possible_endpoints = [
                f"{settings.HEYGEN_API_URL}/talking_photo",  # v2
                f"{settings.HEYGEN_API_URL.replace('/v2', '/v1')}/talking_photo",  # v1
                f"https://api.heygen.com/v1/talking_photo",  # v1 напрямую
                f"{settings.HEYGEN_API_URL}/photo_avatars",  # альтернативный путь
                f"{settings.HEYGEN_API_URL}/avatars/photo",  # еще один вариант
            ]
            
            create_payload = {
                "photo_url": image_url
            }
            
            talking_photo_id = None
            
            for create_url in possible_endpoints:
                try:
                    print(f"📤 Trying to create talking_photo: {create_url}")
                    print(f"   Payload: {create_payload}")
                    
                    create_response = await client.post(
                        create_url, 
                        json=create_payload, 
                        headers=headers, 
                        timeout=60.0
                    )
            
                    print(f"📥 HeyGen create response status: {create_response.status_code}")
                    
                    if create_response.status_code in [200, 201]:
                        result = create_response.json()
                        print(f"✅ HeyGen create response: {result}")
                        
                        # Извлекаем talking_photo_id из разных возможных мест в ответе
                        talking_photo_id = (
                            result.get("data", {}).get("talking_photo_id") or 
                            result.get("data", {}).get("id") or
                            result.get("talking_photo_id") or 
                            result.get("id") or
                            result.get("data", {}).get("talking_photo", {}).get("id") if isinstance(result.get("data", {}).get("talking_photo"), dict) else None
                        )
                        
                        if talking_photo_id:
                            print(f"✅ Successfully created talking_photo via {create_url}, got ID: {talking_photo_id}")
                            return talking_photo_id
                        else:
                            print(f"⚠️  Warning: Response does not contain talking_photo_id: {result}")
                    elif create_response.status_code not in [404, 405]:
                        # Если не 404/405, логируем ошибку
                        error_text = create_response.text[:500]
                        print(f"⚠️  HeyGen create failed {create_response.status_code}: {error_text}")
                        # Продолжаем пробовать другие endpoints
                except Exception as e:
                    print(f"⚠️  Error trying {create_url}: {e}")
                    continue
            
            # Если ни один endpoint не сработал, пробуем загрузить файл
            if not talking_photo_id:
                print(f"⚠️  All JSON endpoints failed, trying file upload...")
                
                # Если JSON не сработал, пробуем загрузить файл напрямую
                print(f"🔄 Trying to upload file directly...")
                try:
                    # Скачиваем изображение
                    print(f"📥 Downloading image from: {image_url}")
                    image_response = await client.get(image_url, timeout=30.0, follow_redirects=True)
                    image_response.raise_for_status()
                    image_data = image_response.content
                    
                    if not image_data:
                        print("Warning: Downloaded image is empty")
                        return None
                    
                    print(f"✅ Downloaded image, size: {len(image_data)} bytes")
                    
                    # Пробуем загрузить через multipart/form-data
                    upload_headers = {
                        "X-Api-Key": settings.HEYGEN_API_KEY,
                    }
                    
                    content_type = "image/jpeg"
                    if image_url.lower().endswith('.png'):
                        content_type = "image/png"
                    
                    files = {
                        "photo": ("photo.jpg", image_data, content_type)
                    }
                    
                    upload_response = await client.post(
                        create_url, 
                        headers=upload_headers, 
                        files=files, 
                        timeout=60.0
                    )
                    
                    print(f"📥 HeyGen upload response status: {upload_response.status_code}")
                    
                    if upload_response.status_code in [200, 201]:
                        upload_result = upload_response.json()
                        print(f"✅ HeyGen upload response: {upload_result}")
                        talking_photo_id = (
                            upload_result.get("data", {}).get("talking_photo_id") or 
                            upload_result.get("talking_photo_id") or 
                            upload_result.get("data", {}).get("id") or 
                            upload_result.get("id")
                        )
                        if talking_photo_id:
                            print(f"✅ Successfully uploaded photo, got talking_photo_id: {talking_photo_id}")
                            return talking_photo_id
                except Exception as upload_error:
                    print(f"⚠️  Error uploading file: {upload_error}")
                    
    except Exception as e:
        print(f"⚠️  Error creating talking_photo in HeyGen: {e}")
        import traceback
        traceback.print_exc()
    
    # Если не удалось создать, возвращаем None
    print(f"⚠️  Could not create talking_photo in HeyGen")
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
    
    # Проверяем, является ли URL localhost - HeyGen не может получить к нему доступ
    if "localhost" in image_url or "127.0.0.1" in image_url:
        # Пытаемся использовать PUBLIC_API_URL если он настроен
        public_api_url = getattr(settings, 'PUBLIC_API_URL', None)
        if public_api_url:
            # Заменяем localhost на публичный URL
            public_image_url = image_url.replace("http://localhost:8000", public_api_url).replace("http://127.0.0.1:8000", public_api_url)
            print(f"Replacing localhost URL with public URL: {image_url} -> {public_image_url}")
            image_url = public_image_url
        else:
            raise ValueError(
                f"❌ HeyGen cannot access localhost URLs!\n\n"
                f"Решение:\n"
                f"1. Установите ngrok: brew install ngrok\n"
                f"2. Запустите: ngrok http 8000\n"
                f"3. Скопируйте HTTPS URL (например: https://abc123.ngrok-free.app)\n"
                f"4. Добавьте в backend/.env: PUBLIC_API_URL=https://abc123.ngrok-free.app\n\n"
                f"Или используйте S3 хранилище для медиа-файлов.\n\n"
                f"Текущий URL: {image_url}"
            )
    
    # Пытаемся загрузить фото и получить talking_photo_id
    # Сначала проверяем, есть ли готовый talking_photo_id в настройках
    talking_photo_id = None
    if hasattr(settings, 'HEYGEN_TALKING_PHOTO_ID') and settings.HEYGEN_TALKING_PHOTO_ID:
        print(f"✅ Using pre-configured talking_photo_id from settings: {settings.HEYGEN_TALKING_PHOTO_ID}")
        talking_photo_id = settings.HEYGEN_TALKING_PHOTO_ID
    else:
        # Пытаемся создать talking_photo через API
        talking_photo_id = await upload_photo_to_heygen(image_url)
    
    # Формируем character payload для HeyGen
    if talking_photo_id:
        # Используем talking_photo_id если получили (предпочтительный способ)
        print(f"✅ Using talking_photo_id: {talking_photo_id}")
        character_payload = {
            "type": "talking_photo",
            "talking_photo": {
                "talking_photo_id": talking_photo_id
            }
        }
    else:
        # Если не удалось создать talking_photo, пробуем использовать photo_url напрямую
        # Но HeyGen требует talking_photo_id, поэтому это может не сработать
        print(f"⚠️  Could not create talking_photo_id. HeyGen requires talking_photo_id for video generation.")
        print(f"📸 Attempting to use photo_url directly (may fail): {image_url}")
        
        # Пробуем разные форматы payload
        # Вариант 1: Стандартный формат с photo_url
        character_payload = {
            "type": "talking_photo",
            "talking_photo": {
                "photo_url": image_url
            }
        }
        
        # Если это не сработает, возможно нужно использовать другой тип character
        # или создать talking_photo через веб-интерфейс HeyGen заранее
    
    # Формируем payload для HeyGen API
    # Важно: voice должен быть правильного формата для HeyGen
    # HeyGen использует свои собственные voice_id, не ElevenLabs
    voice_payload = {
        "type": "text",
        "input_text": script or "Привет, я здесь, чтобы поделиться воспоминаниями с тобой."
    }
    
    # HeyGen voice_id (не ElevenLabs!)
    # Если указан voice_id, используем его, иначе используем дефолтный голос HeyGen
    if voice_id:
        voice_payload["voice_id"] = voice_id
    # Не используем ELEVENLABS_VOICE_ID для HeyGen, так как это разные сервисы
    
    # Формируем payload для HeyGen API v2
    # Важно: проверяем правильный формат согласно документации HeyGen
    payload = {
        "video_inputs": [
            {
                "character": character_payload,
                "voice": voice_payload
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        }
    }
    
    print(f"📦 HeyGen payload structure:")
    print(f"   character: {character_payload}")
    print(f"   voice: {voice_payload}")
    print(f"   Full payload keys: {list(payload.keys())}")
    
    try:
        async with httpx.AsyncClient() as client:
            print(f"🚀 Sending request to HeyGen: {url}")
            print(f"   Payload: {payload}")
            response = await client.post(url, json=payload, headers=headers, timeout=60.0)
            
            print(f"📥 HeyGen response status: {response.status_code}")
            
            if response.status_code != 200:
                error_text = response.text
                print(f"❌ HeyGen API error {response.status_code}: {error_text}")
                
                # Если ошибка связана с talking_photo_id, предлагаем решение
                if "talking_photo_id" in error_text.lower() or "field required" in error_text.lower():
                    print(f"\n⚠️  ВАЖНО: HeyGen требует talking_photo_id, но endpoint для его создания не работает.")
                    print(f"   Возможные решения:")
                    print(f"   1. Создайте talking_photo через веб-интерфейс HeyGen (https://app.heygen.com/)")
                    print(f"   2. Используйте D-ID вместо HeyGen (установите USE_HEYGEN=false в .env)")
                    print(f"   3. Обратитесь в поддержку HeyGen для получения правильного endpoint\n")
                
                raise ValueError(f"HeyGen API error: {response.status_code} - {error_text}")
            
            response.raise_for_status()
            result = response.json()
            # Логируем ответ для отладки
            print(f"✅ HeyGen create video response: {result}")
            return result
    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else str(e)
        print(f"❌ HTTP error creating video in HeyGen: {e.response.status_code} - {error_detail}")
        raise ValueError(f"HeyGen API error: {e.response.status_code} - {error_detail}")
    except httpx.RequestError as e:
        print(f"❌ Request error creating video in HeyGen: {e}")
        raise ValueError(f"HeyGen API request failed: {str(e)}")


async def get_heygen_video_status(video_id: str) -> Dict:
    """
    Проверить статус видео в HeyGen.
    
    Returns:
        Dict с полями: status, video_url (если готово), error (если ошибка)
    """
    if not settings.HEYGEN_API_KEY:
        print("Warning: HEYGEN_API_KEY not configured")
        return {
            "data": {
                "status": "error",
                "video_url": None
            },
            "error": "HEYGEN_API_KEY not configured"
        }
    
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
            # Это нормальная ситуация на ранних этапах обработки
            if response.status_code == 404:
                print(f"HeyGen 404 - video_id: {video_id} (video may still be processing)")
                return {
                    "data": {
                        "status": "processing",  # Возвращаем processing вместо not_found
                        "video_url": None
                    },
                    "error": None  # Не возвращаем ошибку, так как это нормально
                }
            
            response.raise_for_status()
            result = response.json()
            print(f"HeyGen status response: {result}")
            return result
    except httpx.HTTPStatusError as e:
        # Для 404 возвращаем структурированный ответ вместо исключения
        # 404 может означать, что видео еще обрабатывается
        if e.response.status_code == 404:
            print(f"HeyGen 404 exception - video_id: {video_id} (video may still be processing)")
            return {
                "data": {
                    "status": "processing",  # Возвращаем processing вместо not_found
                    "video_url": None
                },
                "error": None  # Не возвращаем ошибку, так как это нормально
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
    webhook_url: Optional[str] = None,
    audio_url: Optional[str] = None,
) -> Dict:
    """
    Унифицированный интерфейс для анимации фото.
    Использует HeyGen если USE_HEYGEN=true, иначе D-ID.

    Args:
        audio_url: Готовое аудио для lip-sync (ElevenLabs). Поддерживается только D-ID.

    Returns:
        Dict с полями: provider, task_id, status
    """
    if settings.USE_HEYGEN:
        result = await animate_photo_heygen(image_url, script, voice_id)
        # HeyGen может вернуть video_id в разных местах
        # Проверяем все возможные варианты структуры ответа
        # Пытаемся извлечь video_id из разных мест ответа
        video_id = (
            result.get("data", {}).get("video_id") or 
            result.get("data", {}).get("id") or
            result.get("video_id") or 
            result.get("id") or
            result.get("data", {}).get("video", {}).get("id") or
            result.get("data", {}).get("video_id") or
            result.get("video", {}).get("id") if isinstance(result.get("video"), dict) else None
        )
        
        if not video_id:
            # Логируем полный ответ для отладки
            print(f"❌ ERROR: Could not extract video_id from HeyGen response!")
            print(f"   Full response: {result}")
            print(f"   Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
            if isinstance(result, dict) and "data" in result:
                print(f"   Data keys: {list(result['data'].keys()) if isinstance(result['data'], dict) else 'Not a dict'}")
            raise ValueError(f"HeyGen API did not return video_id. Response: {result}")
        
        print(f"✅ HeyGen video_id extracted: {video_id}")
        return {
            "provider": "heygen",
            "task_id": video_id,
            "status": "processing"
        }
    else:
        result = await animate_photo_did(image_url, script, voice_id, webhook_url, audio_url)
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
            
            # Проверяем, что result - это словарь
            if not isinstance(result, dict):
                print(f"Warning: HeyGen returned non-dict result: {type(result)}")
                return {
                    "status": "processing",
                    "video_url": None,
                    "error": None
                }
            
            # Обрабатываем разные форматы ответа HeyGen
            if "data" in result:
                data = result.get("data", {})
                if not isinstance(data, dict):
                    data = {}
                status = data.get("status", "unknown")
                # Если статус not_found, возвращаем processing (возможно еще обрабатывается)
                if status == "not_found":
                    status = "processing"
                # Не возвращаем error, если статус processing (это нормально)
                error = result.get("error") if status not in ("processing", "pending") else None
                return {
                    "status": status,
                    "video_url": data.get("video_url") or data.get("url"),
                    "error": error
                }
            else:
                # Прямой формат ответа
                status = result.get("status", "unknown")
                # Не возвращаем error, если статус processing
                error = result.get("error") if status not in ("processing", "pending") else None
                return {
                    "status": status,
                    "video_url": result.get("video_url") or result.get("url"),
                    "error": error
                }
        except ValueError as e:
            # Если ошибка 404, возвращаем processing вместо ошибки
            error_str = str(e).lower()
            if "404" in error_str or "not found" in error_str:
                return {
                    "status": "processing",
                    "video_url": None,
                    "error": None
                }
            raise
        except Exception as e:
            # Обработка любых других исключений
            print(f"Error in get_animation_status for HeyGen: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "video_url": None,
                "error": f"Error checking animation status: {str(e)}"
            }
    else:  # d-id
        try:
            result = await get_did_talk_status(task_id)
            return {
                "status": result.get("status", "unknown"),
                "video_url": result.get("result_url"),
                "error": result.get("error")
            }
        except ValueError as e:
            # Если ошибка 404, возвращаем processing вместо ошибки
            error_str = str(e).lower()
            if "404" in error_str or "not found" in error_str:
                return {
                    "status": "processing",
                    "video_url": None,
                    "error": None
                }
            raise
        except Exception as e:
            # Обработка любых других исключений
            print(f"Error in get_animation_status for D-ID: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "video_url": None,
                "error": f"Error checking animation status: {str(e)}"
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
                elif response.status_code == 402:
                    # Бесплатный тариф: часть голосов по API недоступна — пробуем по очереди все голоса из .env
                    fallback_ids = [
                        settings.ELEVENLABS_VOICE_ID,
                        settings.ELEVENLABS_VOICE_ID_MALE,
                        settings.ELEVENLABS_VOICE_ID_FEMALE,
                    ]
                    for fid in fallback_ids:
                        if not fid or fid == voice_id:
                            continue
                        print(f"ElevenLabs 402. Пробуем голос: {fid}")
                        try:
                            fallback_url = f"https://api.elevenlabs.io/v1/text-to-speech/{fid}"
                            fallback_response = await client.post(
                                fallback_url, json=payload, headers=headers, timeout=60.0
                            )
                            if fallback_response.status_code == 200:
                                return fallback_response.content
                        except Exception:
                            continue
                    raise ValueError(
                        "На бесплатном тарифе ElevenLabs выбранный голос по API недоступен. "
                        "В .env укажите голоса из раздела Professional в вашем аккаунте (скрипт: python -m scripts.list_elevenlabs_voices) или оформите подписку."
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
        if settings.QDRANT_LOCAL_PATH:
            # Локальный файловый режим (без сервера, без Docker)
            client = QdrantClient(path=settings.QDRANT_LOCAL_PATH)
        elif settings.QDRANT_API_KEY:
            # Qdrant Cloud
            client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            # Локальный сервер Qdrant
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
    query_embedding: List[float],
    top_k: int = 5,
    min_score: float = 0.2,
    memorial_ids: Optional[List[int]] = None,
    memorial_id: Optional[int] = None,
) -> List[Dict]:
    """
    Найти похожие воспоминания в векторной БД (Qdrant или Pinecone).

    Args:
        query_embedding: Embedding запроса
        top_k: Количество результатов
        min_score: Минимальный score для включения в результаты
        memorial_ids: Список ID мемориалов для поиска (включает родственников)
        memorial_id: Deprecated — используй memorial_ids. Для обратной совместимости.

    Returns:
        Список словарей с полями: id, score, text, memory_id, title, source_memorial_id
    """
    # Совместимость: если передан memorial_id, оборачиваем в список
    if memorial_ids is None:
        if memorial_id is not None:
            memorial_ids = [memorial_id]
        else:
            raise ValueError("Either memorial_ids or memorial_id must be provided")

    try:
        if settings.VECTOR_DB_PROVIDER == "qdrant":
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchAny
            except ImportError:
                raise ValueError("qdrant-client not installed. Run: pip install qdrant-client")

            client = get_vector_db_client()

            # Нативный фильтр Qdrant по memorial_ids — исключает "призрачные" embeddings
            # от удалённых мемориалов и повышает точность поиска
            qdrant_filter = Filter(
                must=[
                    FieldCondition(
                        key="memorial_id",
                        match=MatchAny(any=memorial_ids),
                    )
                ]
            )

            # qdrant-client 1.7+: query_points заменил search()
            response = client.query_points(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                query=query_embedding,
                query_filter=qdrant_filter,
                limit=top_k * len(memorial_ids),
                score_threshold=min_score,
            )
            raw_results = response.points

            filtered_results = [
                {
                    "id": str(result.id),
                    "score": result.score,
                    "text": result.payload.get("text", ""),
                    "memory_id": result.payload.get("memory_id"),
                    "title": result.payload.get("title", ""),
                    "source_memorial_id": result.payload.get("memorial_id"),
                }
                for result in raw_results
            ]

            return filtered_results

        else:  # Pinecone
            pc = get_vector_db_client()
            index = pc.Index(settings.PINECONE_INDEX_NAME)

            results = index.query(
                vector=query_embedding,
                top_k=top_k * 2 * len(memorial_ids),
                include_metadata=True,
                filter={"memorial_id": {"$in": memorial_ids}}
            )

            filtered_results = [
                {
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "memory_id": match.metadata.get("memory_id"),
                    "title": match.metadata.get("title", ""),
                    "source_memorial_id": match.metadata.get("memorial_id"),
                }
                for match in results.matches
                if match.score >= min_score
            ][:top_k * len(memorial_ids)]

            return filtered_results

    except Exception as e:
        print(f"Error searching vector DB: {e}")
        return []


async def sync_family_memories(memorial_id: int, db, dry_run: bool = False) -> Dict:
    """
    Memory Sync Agent — находит упоминания родственников в воспоминаниях
    и создаёт "отражённые" воспоминания (source="family_sync") в мемориалах родственников.

    Args:
        memorial_id: ID мемориала-источника
        db: SQLAlchemy сессия
        dry_run: Если True — только анализирует, не создаёт записей

    Returns:
        {created, skipped, details}
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    from openai import AsyncOpenAI
    import json as _json

    from app.models import Memorial, Memory, FamilyRelationship

    # Загружаем источник
    source_memorial = db.query(Memorial).filter(Memorial.id == memorial_id).first()
    if not source_memorial:
        raise ValueError(f"Memorial {memorial_id} not found")

    memories = db.query(Memory).filter(Memory.memorial_id == memorial_id).all()
    if not memories:
        return {"created": 0, "skipped": 0, "details": []}

    # Загружаем родственников
    relationships = db.query(FamilyRelationship).filter(
        FamilyRelationship.memorial_id == memorial_id
    ).all()
    if not relationships:
        return {"created": 0, "skipped": 0, "details": [], "message": "No family relationships found"}

    relatives = []
    for rel in relationships:
        related = db.query(Memorial).filter(Memorial.id == rel.related_memorial_id).first()
        if related:
            relatives.append({
                "memorial_id": rel.related_memorial_id,
                "name": related.name,
                "relationship_type": rel.relationship_type.value,
            })

    if not relatives:
        return {"created": 0, "skipped": 0, "details": []}

    relative_list_str = ", ".join(
        f"{r['name']} ({r['relationship_type']})" for r in relatives
    )

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    created = 0
    skipped = 0
    details = []

    for memory in memories:
        prompt = (
            f"Анализируй воспоминание человека по имени {source_memorial.name}.\n"
            f"Родственники: {relative_list_str}.\n"
            f"Текст воспоминания: \"{memory.content}\"\n\n"
            "Найди явные или косвенные упоминания родственников из списка. "
            "Для каждого упоминания верни JSON-массив объектов вида:\n"
            '[{"related_name": "имя", "memorial_id": ID, "reflected_text": "переформулированный текст от лица родственника", "should_sync": true/false}]\n'
            "Если упоминаний нет — верни пустой массив [].\n"
            "Только JSON, никаких объяснений."
        )

        try:
            resp = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=1000,
            )
            raw = resp.choices[0].message.content.strip()
            # Убираем возможные markdown-блоки
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            matches = _json.loads(raw)
        except Exception as e:
            print(f"GPT analysis failed for memory {memory.id}: {e}")
            continue

        for match in matches:
            if not match.get("should_sync"):
                continue

            target_id = match.get("memorial_id")
            reflected_text = match.get("reflected_text", "").strip()
            related_name = match.get("related_name", "")

            if not target_id or not reflected_text:
                continue

            # Проверяем дубликат
            attribution = f"family_sync_from_{memorial_id}_mem_{memory.id}"
            existing = db.query(Memory).filter(
                Memory.memorial_id == target_id,
                Memory.source == "family_sync",
                Memory.embedding_id == attribution,
            ).first()

            detail = {
                "source_memory_id": memory.id,
                "target_memorial_id": target_id,
                "related_name": related_name,
                "reflected_text": reflected_text[:100],
            }

            if existing:
                skipped += 1
                detail["status"] = "skipped_duplicate"
                details.append(detail)
                continue

            if dry_run:
                skipped += 1
                detail["status"] = "dry_run"
                details.append(detail)
                continue

            # Создаём отражённое воспоминание
            new_memory = Memory(
                memorial_id=target_id,
                title=f"Общее воспоминание с {source_memorial.name}",
                content=reflected_text,
                source="family_sync",
                # Используем embedding_id как attribution-метку (до создания реального вектора)
                embedding_id=attribution,
            )
            db.add(new_memory)
            db.flush()  # получаем id

            # Создаём embedding
            try:
                embedding = await get_embedding(reflected_text)
                vector_id = await upsert_memory_embedding(
                    memory_id=new_memory.id,
                    memorial_id=target_id,
                    text=reflected_text,
                    embedding=embedding,
                    title=new_memory.title,
                )
                new_memory.embedding_id = vector_id
            except Exception as emb_err:
                print(f"Embedding failed for synced memory: {emb_err}")
                # Оставляем attribution как embedding_id

            created += 1
            detail["status"] = "created"
            details.append(detail)

    if not dry_run and created > 0:
        db.commit()

    return {"created": created, "skipped": skipped, "details": details}


# ========== AI Agents ==========

async def build_avatar_persona(
    memories: List[Dict],
    memorial_name: str
) -> str:
    """
    Smart Avatar Persona Agent — строит системный промпт-личность аватара из всех воспоминаний.

    Используется вместо стандартного промпта в generate_rag_response для более точного
    отыгрывания образа человека.

    Args:
        memories: Список словарей с полями title и content
        memorial_name: Имя человека

    Returns:
        Готовый system prompt для передачи в generate_rag_response
    """
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    memories_text = "\n\n".join(
        f"[{m.get('title', 'Воспоминание')}]\n{m.get('content', '')}"
        for m in memories
    )

    system_prompt = "Ты — помощник по созданию ИИ-аватаров для мемориального сервиса."
    user_prompt = (
        f"На основе следующих воспоминаний о человеке по имени {memorial_name}, "
        "составь системный промпт для ИИ-аватара. Промпт должен:\n"
        "1. Описывать личность, характер, привычки и ценности этого человека\n"
        "2. Указывать его профессию, увлечения, важные события жизни\n"
        "3. Задавать стиль общения (как он говорил, что любил повторять)\n"
        "4. Включать правила: не придумывать факты, отвечать от первого лица, быть эмпатичным\n\n"
        f"Воспоминания:\n{memories_text}\n\n"
        "Напиши только системный промпт, без пояснений."
    )

    try:
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        raise ValueError(f"OpenAI API error: {str(e)}")


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

