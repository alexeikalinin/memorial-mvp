"""
Тесты AI-эндпоинтов с мокированием внешних сервисов.
"""
from unittest.mock import AsyncMock, MagicMock, patch

from app.models import Media, MediaType


def test_avatar_chat_no_memories(client, memorial):
    """Чат без воспоминаний возвращает информативный ответ без вызова OpenAI."""
    response = client.post(
        "/api/v1/ai/avatar/chat",
        json={
            "memorial_id": memorial["id"],
            "question": "Расскажи о нём",
            "use_persona": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert data["sources"] == []


def test_avatar_chat_with_memories(client, memorial, db_session):
    """Чат с воспоминаниями — OpenAI замокирован, ответ возвращается корректно."""
    mid = memorial["id"]

    # Создаём воспоминание (без embedding — как будет в тестовой среде без OpenAI)
    mem_resp = client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Студенческие годы", "content": "Он учился в МГУ на физфаке."},
    )
    assert mem_resp.status_code == 201
    memory_id = mem_resp.json()["id"]

    with (
        patch("app.api.ai.get_embedding", new_callable=AsyncMock) as mock_embed,
        patch("app.services.ai_tasks.upsert_memory_embedding", new_callable=AsyncMock) as mock_upsert,
        patch("app.api.ai.search_similar_memories", new_callable=AsyncMock) as mock_search,
        patch("app.api.ai.generate_rag_response", new_callable=AsyncMock) as mock_generate,
    ):
        mock_embed.return_value = [0.0] * 1536
        mock_upsert.return_value = "test-vector-id"
        mock_search.return_value = [
            {
                "memory_id": memory_id,
                "score": 0.9,
                "text": "Он учился в МГУ на физфаке.",
                "title": "Студенческие годы",
            }
        ]
        mock_generate.return_value = ("Он учился в МГУ.", [memory_id])

        response = client.post(
            "/api/v1/ai/avatar/chat",
            json={
                "memorial_id": mid,
                "question": "Где он учился?",
                "use_persona": False,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Он учился в МГУ."
    assert len(data["sources"]) > 0


def test_animate_photo_no_redis(client, memorial, db_session):
    """Анимация фото: Redis недоступен → синхронный fallback с замоком D-ID."""
    mid = memorial["id"]

    # Вставляем запись медиа напрямую в БД (обходим реальную загрузку файла)
    media = Media(
        memorial_id=mid,
        file_path="uploads/test_photo.jpg",
        file_name="test_photo.jpg",
        media_type=MediaType.PHOTO,
        is_animated=False,
        file_size=1000,
        mime_type="image/jpeg",
    )
    db_session.add(media)
    db_session.commit()
    db_session.refresh(media)

    fake_task = MagicMock()
    fake_task.delay.side_effect = Exception("OperationalError: connection refused")

    with (
        patch("app.api.ai.animate_photo_task", fake_task),
        patch(
            "app.services.ai_tasks.animate_photo",
            new=AsyncMock(return_value={"provider": "d-id", "task_id": "did-task-abc123"}),
        ),
    ):
        response = client.post(
            "/api/v1/ai/photo/animate",
            json={"media_id": media.id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "did-task-abc123"
    assert data["status"] in ("processing", "pending", "done")


def test_avatar_chat_family_rag(auth_client, memorial, db_session):
    """5.6 Семейный RAG: include_family_memories=true включает воспоминания родственного мемориала."""
    mid = memorial["id"]

    # Создаём второй мемориал (родственный)
    resp2 = auth_client.post(
        "/api/v1/memorials/",
        json={"name": "Родственный мемориал", "is_public": False},
    )
    assert resp2.status_code == 201
    mid2 = resp2.json()["id"]

    # Связываем мемориалы
    rel_resp = auth_client.post(
        f"/api/v1/family/memorials/{mid}/relationships",
        json={"related_memorial_id": mid2, "relationship_type": "parent"},
    )
    assert rel_resp.status_code == 201

    # Добавляем воспоминание в основной мемориал (чтобы all_memories не был пуст)
    auth_client.post(
        f"/api/v1/memorials/{mid}/memories",
        json={"title": "Основное", "content": "Он жил в Москве."},
    )

    # Добавляем воспоминание в родственный мемориал
    mem_resp = auth_client.post(
        f"/api/v1/memorials/{mid2}/memories",
        json={"title": "Семейное", "content": "Его отец работал врачом."},
    )
    assert mem_resp.status_code == 201
    family_mem_id = mem_resp.json()["id"]

    with (
        patch("app.api.ai.get_embedding", new_callable=AsyncMock) as mock_embed,
        patch("app.api.ai.search_similar_memories", new_callable=AsyncMock) as mock_search,
        patch("app.api.ai.generate_rag_response", new_callable=AsyncMock) as mock_gen,
    ):
        mock_embed.return_value = [0.0] * 1536
        mock_search.return_value = [
            {
                "memory_id": family_mem_id,
                "score": 0.85,
                "text": "Его отец работал врачом.",
                "title": "Семейное",
            }
        ]
        mock_gen.return_value = ("Его отец был врачом.", [family_mem_id])

        response = auth_client.post(
            "/api/v1/ai/avatar/chat",
            json={
                "memorial_id": mid,
                "question": "Кем работал его отец?",
                "include_family_memories": True,
                "use_persona": False,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Его отец был врачом."
    assert len(data["sources"]) > 0


def test_animation_status(client):
    """Статус анимации возвращается корректно при замоке get_animation_status."""
    with patch(
        "app.api.ai.get_animation_status",
        new_callable=AsyncMock,
        return_value={"status": "done", "video_url": "https://example.com/video.mp4", "error": None},
    ):
        response = client.post(
            "/api/v1/ai/animation/status",
            json={"task_id": "test-task-xyz", "provider": "d-id"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test-task-xyz"
    assert data["status"] == "done"
    assert data["video_url"] == "https://example.com/video.mp4"
    assert data["provider"] == "d-id"
