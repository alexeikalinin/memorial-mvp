# Check API Quotas — memorial-mvp

Проверь текущие лимиты и остатки по всем API сервисам проекта.
Предупреди если что-то заканчивается.

## Порядок проверки

Выполни следующий Python скрипт в `backend/`:

```python
import httpx, asyncio, datetime
import sys, os
sys.path.insert(0, '.')
os.chdir('/Users/alexei.kalinin/Documents/VibeCoding/memorial-mvp/backend')

from app.config import settings

async def check_all():
    results = {}
    warnings = []

    async with httpx.AsyncClient() as client:

        # --- ElevenLabs ---
        try:
            r = await client.get(
                "https://api.elevenlabs.io/v1/user/subscription",
                headers={"xi-api-key": settings.ELEVENLABS_API_KEY.strip()},
                timeout=10
            )
            data = r.json()
            used = data.get('character_count', 0)
            limit = data.get('character_limit', 0)
            tier = data.get('tier', 'unknown')
            reset_unix = data.get('next_character_count_reset_unix', 0)
            reset_dt = datetime.datetime.fromtimestamp(reset_unix).strftime('%Y-%m-%d') if reset_unix else 'unknown'
            pct = 100 * used / limit if limit else 0
            results['elevenlabs'] = f"Tier: {tier} | {used:,}/{limit:,} chars ({pct:.0f}%) | reset: {reset_dt}"
            if pct >= 80:
                warnings.append(f"⚠️  ElevenLabs: {pct:.0f}% использовано ({limit-used:,} осталось, сброс {reset_dt})")
            if pct >= 95:
                warnings.append(f"🚨 ElevenLabs КРИТИЧНО: почти закончилось! Осталось {limit-used:,} символов")
        except Exception as e:
            results['elevenlabs'] = f"ОШИБКА: {e}"

        # --- OpenAI ---
        try:
            r = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                timeout=10
            )
            if r.status_code == 200:
                results['openai'] = "Ключ валиден ✅ (баланс проверяется только через браузер: platform.openai.com/usage)"
            elif r.status_code == 401:
                results['openai'] = "❌ Ключ недействителен или исчерпан"
                warnings.append("🚨 OpenAI: ключ недействителен!")
            elif r.status_code == 429:
                results['openai'] = "⚠️  Rate limit или квота исчерпана"
                warnings.append("🚨 OpenAI: квота исчерпана (429)!")
            else:
                results['openai'] = f"Статус {r.status_code}"
        except Exception as e:
            results['openai'] = f"ОШИБКА: {e}"

        # --- Qdrant ---
        try:
            r = await client.get(
                f"{settings.QDRANT_URL}/collections/{settings.QDRANT_COLLECTION_NAME}",
                headers={"api-key": settings.QDRANT_API_KEY},
                timeout=10
            )
            data = r.json()
            points = data.get("result", {}).get("points_count", 0)
            results['qdrant'] = f"OK ✅ | Collection: {settings.QDRANT_COLLECTION_NAME} | Points: {points:,} | Free: 1GB RAM, 4GB disk"
            if points > 500000:
                warnings.append("⚠️  Qdrant: много векторов, следи за лимитом free tier")
        except Exception as e:
            results['qdrant'] = f"ОШИБКА: {e}"
            warnings.append(f"🚨 Qdrant недоступен: {e}")

    # Вывод
    print("\n=== API Quotas — Memorial MVP ===\n")
    print(f"📊 OpenAI:     {results.get('openai', 'N/A')}")
    print(f"🎙️  ElevenLabs: {results.get('elevenlabs', 'N/A')}")
    print(f"🔍 Qdrant:     {results.get('qdrant', 'N/A')}")

    if warnings:
        print("\n--- ПРЕДУПРЕЖДЕНИЯ ---")
        for w in warnings:
            print(w)
        print("\n👉 Действия при исчерпании:")
        print("   ElevenLabs: новый аккаунт ($0) или Starter $5/мес")
        print("   OpenAI: пополнить баланс на platform.openai.com/billing")
        print("   Qdrant: free tier 4GB диска, при переполнении — удалить старые точки")
    else:
        print("\n✅ Всё в норме")

asyncio.run(check_all())
```

Запусти скрипт и выведи результат.

## Пороги предупреждений

| Сервис | Предупреждение | Критично |
|--------|---------------|---------|
| ElevenLabs | > 80% символов | > 95% |
| OpenAI | ключ 401/429 | ключ 401 |
| Qdrant | > 500k векторов | недоступен |

## Что делать при исчерпании

**ElevenLabs free (10k/мес):**
- Сброс 15 числа каждого месяца
- Новый аккаунт на другой email
- Или Starter $5/мес = 30k символов

**OpenAI:**
- platform.openai.com → Billing → Add credits
- Текущий ключ: sk-proj-Zt7eMs3K... (хранится в backend/.env)

**Qdrant Free:**
- 1 кластер, 1GB RAM, 4GB диск
- При 168 векторах — запас огромный (тысячи мемориалов)
- При переполнении: удалить старые embeddings или перейти на Qdrant Cloud $25/мес
