#!/bin/bash

# Скрипт для запуска всех компонентов приложения
# Использование: ./start_all.sh

echo "🚀 Запуск Memorial MVP..."
echo ""

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка Redis
echo -e "${BLUE}📦 Проверка Redis...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis не запущен. Запустите Redis:${NC}"
    echo "   brew services start redis"
    echo "   или"
    echo "   redis-server"
    exit 1
fi
echo -e "${GREEN}✅ Redis работает${NC}"
echo ""

# Проверка ngrok
echo -e "${BLUE}🌐 Проверка ngrok...${NC}"
if ! pgrep -f "ngrok http" > /dev/null; then
    echo -e "${YELLOW}⚠️  Ngrok не запущен. Запустите в отдельном терминале:${NC}"
    echo "   ngrok http 8000"
    echo ""
    echo -e "${YELLOW}Или запустите автоматически? (y/n)${NC}"
    read -r answer
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        nohup ngrok http 8000 > /tmp/ngrok.log 2>&1 &
        sleep 3
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
        if [ -n "$PUBLIC_URL" ]; then
            echo -e "${GREEN}✅ Ngrok запущен: $PUBLIC_URL${NC}"
            # Обновляем .env
            cd backend
            if grep -q "PUBLIC_API_URL" .env 2>/dev/null; then
                sed -i '' "s|PUBLIC_API_URL=.*|PUBLIC_API_URL=$PUBLIC_URL|" .env
            else
                echo "PUBLIC_API_URL=$PUBLIC_URL" >> .env
            fi
            cd ..
        fi
    fi
else
    echo -e "${GREEN}✅ Ngrok уже запущен${NC}"
fi
echo ""

# Запуск Backend
echo -e "${BLUE}🔧 Запуск Backend (uvicorn)...${NC}"
cd backend
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено. Создайте его:${NC}"
    echo "   python3 -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

source .venv/bin/activate
echo -e "${GREEN}✅ Виртуальное окружение активировано${NC}"
echo ""
echo -e "${YELLOW}📝 Backend будет запущен в этом терминале${NC}"
echo -e "${YELLOW}   Нажмите Ctrl+C для остановки${NC}"
echo ""
echo "Запуск uvicorn..."
uvicorn app.main:app --reload --port 8000

