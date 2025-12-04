# 🔑 Руководство по API ключам

## 📋 Список необходимых API ключей

### ✅ Обязательные для MVP:

1. **OpenAI API Key** - для LLM и embeddings
2. **Pinecone API Key** - для векторной базы данных
3. **HeyGen API Key** (или D-ID) - для анимации фото
4. **ElevenLabs API Key** - для текста в речь (опционально)

### ⚙️ Опциональные:

5. **AWS S3** - для хранения медиа в облаке (можно использовать локальное хранилище)
6. **Redis** - для очередей задач (можно использовать локальный Redis)

---

## 🔧 Формат и где получить

### 1. **OpenAI API Key**

**Формат:** `sk-...` (строка, начинается с `sk-`)

**Где получить:**
1. Перейдите на https://platform.openai.com/api-keys
2. Войдите в аккаунт (или создайте)
3. Нажмите "Create new secret key"
4. Скопируйте ключ (показывается только один раз!)

**В .env:**
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

---

### 2. **Qdrant** (Рекомендуется - бесплатно) ⭐

**Формат:** 
- `QDRANT_URL`: URL вида `http://localhost:6333` или `https://xxxxx.cloud.qdrant.io:6333`
- `QDRANT_API_KEY`: Строка (опционально, только для Qdrant Cloud)

**Где получить (Qdrant Cloud):**
1. Перейдите на https://cloud.qdrant.io/
2. Зарегистрируйтесь (можно через GitHub)
3. Создайте бесплатный кластер
4. Скопируйте URL и API Key

**В .env:**
```env
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=https://xxxxx-xxxxx.us-east-1-0.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
QDRANT_COLLECTION_NAME=memorial-memories
```

**Локально (без регистрации):**
```env
VECTOR_DB_PROVIDER=qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # Оставить пустым
QDRANT_COLLECTION_NAME=memorial-memories
```

Запуск локального Qdrant:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Важно:** Коллекция создается автоматически при первом использовании.

---

### 2.1. **Pinecone** (Альтернатива, если нужен Pinecone)

**Формат:** Обычно строка вида `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

**Где получить:**
1. Перейдите на https://www.pinecone.io/
2. Зарегистрируйтесь (бесплатный план доступен)
3. Создайте проект
4. Перейдите в API Keys
5. Скопируйте API Key

**В .env:**
```env
VECTOR_DB_PROVIDER=pinecone
PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=memorial-memories
```

**Важно:** После получения ключа нужно создать индекс в Pinecone:
- Dimension: `1536` (для text-embedding-3-small)
- Metric: `cosine`
- Name: `memorial-memories` (или как указано в PINECONE_INDEX_NAME)

---

### 3. **HeyGen API Key**

**Формат:** Строка вида `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Где получить:**
1. Перейдите на https://www.heygen.com/
2. Зарегистрируйтесь
3. Перейдите в Settings → API Keys
4. Создайте новый API Key
5. Скопируйте ключ

**В .env:**
```env
HEYGEN_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HEYGEN_API_URL=https://api.heygen.com/v2
USE_HEYGEN=true
```

**Альтернатива - D-ID:**
```env
DID_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DID_API_URL=https://api.d-id.com
USE_HEYGEN=false
```

---

### 4. **ElevenLabs API Key** (опционально)

**Формат:** Строка вида `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Где получить:**
1. Перейдите на https://elevenlabs.io/
2. Зарегистрируйтесь
3. Перейдите в Profile → API Keys
4. Создайте новый API Key
5. Скопируйте ключ

**В .env:**
```env
ELEVENLABS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM  # ID голоса (можно оставить пустым)
```

**Настройки в ElevenLabs:**
- В разделе API Keys выберите "Create API Key"
- Скопируйте ключ
- Voice ID можно найти в разделе Voice Library (опционально)

---

### 5. **AWS S3** (опционально, для облачного хранилища)

**Формат:** 
- `AWS_ACCESS_KEY_ID`: строка вида `AKIA...`
- `AWS_SECRET_ACCESS_KEY`: длинная строка

**Где получить:**
1. Перейдите на https://aws.amazon.com/
2. Создайте аккаунт
3. Перейдите в IAM → Users → Create User
4. Создайте пользователя с правами S3
5. Создайте Access Key
6. Скопируйте Access Key ID и Secret Access Key

**В .env:**
```env
S3_BUCKET_NAME=memorial-mvp-media
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
USE_S3=true
```

**Альтернатива - Cloudflare R2:**
- Используйте те же переменные, но измените `S3_REGION` на регион R2
- Endpoint настраивается отдельно в коде

---

### 6. **Redis** (опционально, для очередей задач)

**Формат:** URL вида `redis://localhost:6379/0`

**Локально:**
```env
REDIS_URL=redis://localhost:6379/0
```

**Облако (Redis Cloud, Upstash и т.д.):**
```env
REDIS_URL=redis://:password@host:port/0
```

---

## 📝 Пример полного .env файла

```env
# Database
DATABASE_URL=sqlite:///./memorial.db

# Security
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# HeyGen (для анимации фото)
HEYGEN_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
HEYGEN_API_URL=https://api.heygen.com/v2
USE_HEYGEN=true

# D-ID (альтернатива HeyGen)
# DID_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# DID_API_URL=https://api.d-id.com
# DID_WEBHOOK_URL=

# ElevenLabs (для TTS)
ELEVENLABS_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Vector Database (Qdrant - рекомендуется, или Pinecone)
VECTOR_DB_PROVIDER=qdrant  # "qdrant" или "pinecone"

# Qdrant (рекомендуется - бесплатно)
QDRANT_URL=http://localhost:6333  # Локальный или Qdrant Cloud URL
QDRANT_API_KEY=  # Опционально, для Qdrant Cloud
QDRANT_COLLECTION_NAME=memorial-memories

# Pinecone (альтернатива, если VECTOR_DB_PROVIDER="pinecone")
PINECONE_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=memorial-memories

# AWS S3 (опционально)
# S3_BUCKET_NAME=memorial-mvp-media
# S3_REGION=us-east-1
# AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxxxxxx
# AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# USE_S3=false

# Redis (опционально)
REDIS_URL=redis://localhost:6379/0

# Application
DEBUG=true
API_V1_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# File Upload
MAX_UPLOAD_SIZE=104857600
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,mp4,mov,mp3,wav,pdf,txt
```

---

## ✅ Минимальная конфигурация для запуска

Для базового функционала достаточно:

```env
# OpenAI (обязательно)
OPENAI_API_KEY=sk-...

# Pinecone (обязательно)
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=memorial-memories

# HeyGen (обязательно для анимации)
HEYGEN_API_KEY=...
USE_HEYGEN=true

# Остальное можно оставить по умолчанию
```

---

## 🔒 Безопасность

⚠️ **ВАЖНО:**
- Никогда не коммитьте `.env` файл в Git
- Используйте `.env.example` как шаблон
- В production используйте переменные окружения сервера
- Регулярно ротируйте API ключи
- Используйте разные ключи для dev/prod

---

## 🧪 Проверка ключей

После добавления ключей проверьте:

```bash
# Проверка OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Проверка Qdrant (локально)
curl http://localhost:6333/collections

# Проверка Qdrant (через Python)
python -c "from qdrant_client import QdrantClient; client = QdrantClient(url='http://localhost:6333'); print(client.get_collections())"

# Проверка HeyGen
curl -X GET "https://api.heygen.com/v2/avatars" \
  -H "X-Api-Key: $HEYGEN_API_KEY"
```

---

## 📞 Поддержка

Если возникли проблемы с получением ключей:
- OpenAI: https://help.openai.com/
- Pinecone: https://docs.pinecone.io/
- HeyGen: https://docs.heygen.com/
- ElevenLabs: https://docs.elevenlabs.io/

