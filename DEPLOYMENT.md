# Руководство по развертыванию

## Развертывание на сервере со статическим IP

### Предварительные требования

1. **Сервер с Ubuntu/Debian** (рекомендуется Ubuntu 22.04 LTS)
2. **Статический IP адрес**
3. **Docker и Docker Compose** установлены
4. **Обученная модель Detectron2** (model_final.pth)
5. **OpenRouter API ключ** (для доступа к LLM моделям)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose-plugin -y

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker
```

### Шаг 2: Клонирование и настройка проекта

```bash
# Клонирование проекта (или загрузка файлов)
cd /opt
sudo mkdir -p astro-correction-api
sudo chown $USER:$USER astro-correction-api
cd astro-correction-api

# Копирование файлов проекта
# (скопируйте все файлы из astro-correction-api/)
```

### Шаг 3: Настройка переменных окружения

```bash
# Создание .env файла
cp .env.example .env
nano .env
```

Заполните следующие переменные:

```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=sk-or-your-actual-api-key-here
OPENROUTER_MODEL=openai/gpt-4-turbo-preview
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Model Configuration
MODEL_PATH=/app/models/model_final.pth
CONFIG_PATH=/app/config/config.yaml
NUM_CLASSES=1
THING_CLASSES=frame
CONFIDENCE_THRESHOLD=0.5

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Server Configuration
ALLOWED_ORIGINS=*
```

### Шаг 4: Размещение модели и конфигурации

```bash
# Копирование модели
sudo mkdir -p models
sudo cp /path/to/model_final.pth models/

# Копирование конфигурации (уже должно быть в config/)
# Убедитесь, что config/config.yaml существует
```

### Шаг 5: Запуск через Docker Compose

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка логов
docker-compose logs -f api

# Проверка статуса
docker-compose ps
```

### Шаг 6: Настройка firewall

```bash
# Разрешение порта 8000
sudo ufw allow 8000/tcp
sudo ufw enable
```

### Шаг 7: Настройка Nginx (опционально, для HTTPS)

```bash
# Установка Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Создание конфигурации
sudo nano /etc/nginx/sites-available/astro-correction-api
```

Конфигурация Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # или ваш IP адрес

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/astro-correction-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Настройка SSL (если есть домен)
sudo certbot --nginx -d your-domain.com
```

### Шаг 8: Проверка работы

```bash
# Проверка health endpoint
curl http://localhost:8000/api/v1/health

# Или через браузер
# http://your-server-ip:8000/api/v1/health
```

### Шаг 9: Автозапуск при перезагрузке

Docker Compose уже настроен на автозапуск через `restart: unless-stopped` в docker-compose.yml.

Для дополнительной надежности можно создать systemd service:

```bash
sudo nano /etc/systemd/system/astro-correction-api.service
```

```ini
[Unit]
Description=Astro Correction API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/astro-correction-api
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable astro-correction-api
sudo systemctl start astro-correction-api
```

## Мониторинг и обслуживание

### Просмотр логов

```bash
# Логи контейнера
docker-compose logs -f api

# Последние 100 строк
docker-compose logs --tail=100 api
```

### Перезапуск сервиса

```bash
docker-compose restart api
```

### Обновление кода

```bash
# Остановка
docker-compose down

# Обновление кода
git pull  # или копирование новых файлов

# Пересборка и запуск
docker-compose up -d --build
```

### Резервное копирование

```bash
# Бэкап модели и конфигурации
tar -czf backup-$(date +%Y%m%d).tar.gz models/ config/ .env

# Восстановление
tar -xzf backup-YYYYMMDD.tar.gz
```

## Устранение неполадок

### Контейнер не запускается

```bash
# Проверка логов
docker-compose logs api

# Проверка конфигурации
docker-compose config
```

### Модель не найдена

```bash
# Проверка наличия файла
ls -lh models/model_final.pth

# Проверка прав доступа
sudo chmod 644 models/model_final.pth
```

### Проблемы с OpenRouter API

```bash
# Проверка переменной окружения
docker-compose exec api env | grep OPENROUTER

# Тест API ключа
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

## Безопасность

1. **Никогда не коммитьте .env файл** в git
2. **Используйте HTTPS** для продакшена
3. **Ограничьте доступ** через firewall только необходимым IP
4. **Регулярно обновляйте** зависимости и систему
5. **Мониторьте логи** на подозрительную активность

## Масштабирование

Для увеличения производительности можно:

1. **Использовать GPU** (если доступно):
   - Установить nvidia-docker
   - Добавить `runtime: nvidia` в docker-compose.yml

2. **Добавить балансировщик нагрузки** для нескольких инстансов

3. **Использовать Redis** для кеширования результатов
