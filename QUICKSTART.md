# Быстрый старт

## Минимальная настройка за 5 минут

### 1. Подготовка файлов

```bash
# Убедитесь, что у вас есть:
# - model_final.pth (модель Detectron2)
# - config/config.yaml (конфигурация модели)
# - OpenAI API ключ
```

### 2. Настройка переменных окружения

Создайте файл `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env` и укажите:
```env
OPENROUTER_API_KEY=sk-or-your-key-here
OPENROUTER_MODEL=openai/gpt-4-turbo-preview
MODEL_PATH=/app/models/model_final.pth
CONFIG_PATH=/app/config/config.yaml
```

### 3. Размещение модели

```bash
# Скопируйте модель в директорию models/
cp /path/to/model_final.pth models/
```

### 4. Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d --build

# Проверка логов
docker-compose logs -f api
```

### 5. Проверка работы

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Должен вернуть:
# {"status":"healthy","model_loaded":true,"openai_configured":true,"version":"1.0.0"}
```

### 6. Тестовый запрос

```bash
curl -X POST http://localhost:8000/api/v1/correct \
  -H "Content-Type: application/json" \
  -d '{
    "astro_code": "<html><body><div class=\"block\" style=\"position:absolute; top:10vh; left:20vw;\">Test</div></body></html>",
    "page_id": "test_page"
  }'
```

## Структура проекта

```
astro-correction-api/
├── app/                    # Код приложения
│   ├── main.py            # Точка входа FastAPI
│   ├── api/               # API маршруты
│   ├── services/          # Бизнес-логика
│   ├── models/           # Pydantic модели
│   └── utils/             # Утилиты
├── config/                # Конфигурация модели
├── models/                # Модель Detectron2 (model_final.pth)
├── data/                  # Данные (изображения, страницы)
├── Dockerfile            # Docker образ
├── docker-compose.yml    # Docker Compose конфигурация
├── requirements.txt      # Python зависимости
└── .env                  # Переменные окружения (не в git)
```

## Основные команды

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f api

# Перезапуск
docker-compose restart api

# Пересборка после изменений кода
docker-compose up -d --build
```

## Troubleshooting

### Контейнер не запускается

```bash
# Проверьте логи
docker-compose logs api

# Проверьте наличие модели
ls -lh models/model_final.pth

# Проверьте .env файл
cat .env
```

### Ошибка "Model not found"

Убедитесь, что файл модели находится в `models/model_final.pth`:
```bash
cp /path/to/your/model_final.pth models/
```

### Ошибка OpenRouter API

Проверьте API ключ в `.env`:
```bash
echo $OPENROUTER_API_KEY  # или проверьте .env файл
```

Получить API ключ можно на https://openrouter.ai/

## Следующие шаги

1. Прочитайте `README.md` для полного описания
2. Изучите `API_EXAMPLES.md` для примеров использования
3. Следуйте `DEPLOYMENT.md` для развертывания на сервере
4. Прочитайте `SYSTEM_DESCRIPTION.md` для понимания архитектуры

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs api`
2. Проверьте health endpoint: `curl http://localhost:8000/api/v1/health`
3. Убедитесь, что все переменные окружения установлены правильно
