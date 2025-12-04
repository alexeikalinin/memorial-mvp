#!/bin/bash

# Скрипт для запуска ngrok и настройки PUBLIC_API_URL

echo "🚀 Запуск ngrok туннеля для порта 8000..."
echo ""

# Запускаем ngrok в фоне
ngrok http 8000 > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

echo "⏳ Ожидание создания туннеля (5 секунд)..."
sleep 5

# Получаем публичный URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tunnels = [t for t in data.get('tunnels', []) if t.get('proto') == 'https']
    if tunnels:
        print(tunnels[0]['public_url'])
except:
    pass
" 2>/dev/null)

if [ -z "$PUBLIC_URL" ]; then
    echo "❌ Не удалось получить публичный URL"
    echo "Проверьте, что ngrok запущен и доступен на http://localhost:4040"
    echo ""
    echo "Попробуйте запустить вручную:"
    echo "  ngrok http 8000"
    echo ""
    echo "Затем скопируйте HTTPS URL и добавьте в backend/.env:"
    echo "  PUBLIC_API_URL=https://your-url.ngrok-free.app"
    kill $NGROK_PID 2>/dev/null
    exit 1
fi

echo "✅ Публичный URL получен: $PUBLIC_URL"
echo ""

# Проверяем, есть ли .env файл
ENV_FILE="backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Файл $ENV_FILE не найден, создаю..."
    touch "$ENV_FILE"
fi

# Обновляем или добавляем PUBLIC_API_URL
if grep -q "PUBLIC_API_URL" "$ENV_FILE"; then
    # Обновляем существующую строку
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|PUBLIC_API_URL=.*|PUBLIC_API_URL=$PUBLIC_URL|" "$ENV_FILE"
    else
        # Linux
        sed -i "s|PUBLIC_API_URL=.*|PUBLIC_API_URL=$PUBLIC_URL|" "$ENV_FILE"
    fi
    echo "✅ Обновлен PUBLIC_API_URL в $ENV_FILE"
else
    # Добавляем новую строку
    echo "" >> "$ENV_FILE"
    echo "PUBLIC_API_URL=$PUBLIC_URL" >> "$ENV_FILE"
    echo "✅ Добавлен PUBLIC_API_URL в $ENV_FILE"
fi

echo ""
echo "🎉 Настройка завершена!"
echo ""
echo "Ngrok запущен в фоне (PID: $NGROK_PID)"
echo "Публичный URL: $PUBLIC_URL"
echo ""
echo "Для остановки ngrok выполните:"
echo "  kill $NGROK_PID"
echo ""
echo "Или откройте веб-интерфейс ngrok:"
echo "  open http://localhost:4040"
echo ""
echo "Backend автоматически перезагрузится с новым URL (если запущен с --reload)"

