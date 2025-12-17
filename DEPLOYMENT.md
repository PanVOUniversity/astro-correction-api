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

```

### Шаг 2: Клонирование и настройка проекта

```bash
# Клонирование проекта (или загрузка файлов)
cd /opt
git clone https://github.com/PanVOUniversity/astro-correction-api

```

### Шаг 3: Настройка переменных окружения

```bash
# Создание .env файла
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
ALLOWED_ORIGINS=https://automatoria.ru,https://www.automatoria.ru
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
sudo apt install docker-compose
docker-compose up -d --build

# Проверка логов
docker-compose logs -f api

# Проверка статуса
docker-compose ps
```

### Шаг 6: Настройка firewall

```bash
# Разрешение портов
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8000/tcp    # API (только для локального доступа через Nginx)
sudo ufw enable

# Проверка статуса
sudo ufw status
```

**Важно:** Порт 8000 должен быть доступен только локально (через Nginx), не открывайте его напрямую в firewall для внешнего доступа.

### Шаг 7: Настройка Nginx для домена automatoria.ru

```bash
# Установка Nginx
sudo apt install nginx certbot python3-certbot-nginx -y

# Создание конфигурации
sudo nano /etc/nginx/sites-available/automatoria.ru
```

Конфигурация Nginx для automatoria.ru с API на пути /api:

```nginx
server {
    listen 80;
    server_name automatoria.ru www.automatoria.ru;

    # API на пути /api
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Увеличение таймаутов для долгих запросов
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Поддержка WebSocket (если понадобится)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Корневой путь (для основного сайта, если нужен)
    location / {
        # Здесь может быть ваш основной сайт или редирект
        # Например, статические файлы или другой сервис
        return 404;  # или proxy_pass на другой сервис
    }
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/automatoria.ru /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Настройка SSL для домена
sudo certbot --nginx -d automatoria.ru -d www.automatoria.ru
```

После настройки SSL, certbot автоматически обновит конфигурацию для HTTPS. Убедитесь, что DNS записи для automatoria.ru указывают на IP вашего сервера:

```bash
# Проверка DNS
dig automatoria.ru
nslookup automatoria.ru
```

**Важно:** После настройки SSL, API будет доступно по адресу:
- `https://automatoria.ru/api/v1/health`
- `https://automatoria.ru/api/v1/correct`
- `https://automatoria.ru/api/v1/generate`
- и т.д.

### Шаг 8: Проверка работы

```bash
# Проверка health endpoint локально
curl http://localhost:8000/api/v1/health

# Проверка через домен (после настройки Nginx)
curl https://automatoria.ru/api/v1/health

# Или через браузер
# https://automatoria.ru/api/v1/health
```

**Ожидаемый ответ:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "openai_configured": true,
  "version": "1.0.0"
}
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

## Настройка DNS для automatoria.ru

Перед настройкой Nginx убедитесь, что DNS записи настроены правильно:

### A-запись для домена

В панели управления DNS вашего регистратора домена добавьте:

```
Тип: A
Имя: @ (или automatoria.ru)
Значение: [IP адрес вашего сервера]
TTL: 3600
```

### A-запись для www поддомена (опционально)

```
Тип: A
Имя: www
Значение: [IP адрес вашего сервера]
TTL: 3600
```

Или используйте CNAME:

```
Тип: CNAME
Имя: www
Значение: automatoria.ru
TTL: 3600
```

### Проверка DNS

```bash
# Проверка A-записи
dig automatoria.ru +short
nslookup automatoria.ru

# Должен вернуть IP адрес вашего сервера
```

**Важно:** Изменения DNS могут распространяться до 48 часов, но обычно это занимает несколько минут.

## Доступ к API после развертывания

После успешной настройки, API будет доступно по следующим адресам:

- **Health check:** `https://automatoria.ru/api/v1/health`
- **Коррекция кода:** `POST https://automatoria.ru/api/v1/correct`
- **Генерация сайта:** `POST https://automatoria.ru/api/v1/generate`
- **Детекция объектов:** `POST https://automatoria.ru/api/v1/detect`
- **Деплоенные сайты:** `https://automatoria.ru/api/v1/site/{site_hash}`

### Пример использования через домен

```bash
# Проверка здоровья API
curl https://automatoria.ru/api/v1/health

# Коррекция кода
curl -X POST https://automatoria.ru/api/v1/correct \
  -H "Content-Type: application/json" \
  -d '{
    "astro_code": "<html>...</html>",
    "page_id": "page_1"
  }'
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

### Проблемы с Nginx и доменом

**Ошибка 502 Bad Gateway:**

```bash
# Проверка, что API контейнер запущен
docker-compose ps

# Проверка логов Nginx
sudo tail -f /var/log/nginx/error.log

# Проверка доступности API локально
curl http://localhost:8000/api/v1/health
```

**Ошибка 404 Not Found при обращении к /api:**

```bash
# Проверка конфигурации Nginx
sudo nginx -t

# Проверка, что конфигурация активна
ls -la /etc/nginx/sites-enabled/ | grep automatoria

# Перезагрузка Nginx
sudo systemctl reload nginx
```

**SSL сертификат не работает:**

```bash
# Проверка сертификата
sudo certbot certificates

# Обновление сертификата вручную
sudo certbot renew --dry-run

# Проверка автоматического обновления
sudo systemctl status certbot.timer
```

**DNS не резолвится:**

```bash
# Проверка с сервера
dig automatoria.ru
nslookup automatoria.ru

# Проверка с внешнего сервиса
# Используйте https://dnschecker.org/ или https://www.whatsmydns.net/
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
