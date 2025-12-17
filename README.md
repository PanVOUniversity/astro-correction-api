# Astro Correction API

Система автоматической коррекции сайтов на основе Astro с использованием нейросетевой детекции объектов и ChatGPT для исправления кода.

## Описание системы

Система автоматической генерации и коррекции сайтов на основе Astro. Поддерживает:

1. **Генерация сайтов по описанию** - создание HTML кода через LLM по текстовому описанию
2. **Автоматическая коррекция наложений** - итеративное исправление перекрывающихся элементов через детекцию объектов (Detectron2) и коррекцию кода (LLM)
3. **Деплой готовых сайтов** - автоматическое сохранение и доступ к готовым сайтам

Система использует гибридную архитектуру со внутренними сервисами для максимальной производительности.

## Архитектура

```
Client (JSON запрос) 
    ↓
FastAPI Server
    ↓
1. Сохранение HTML/скриншот
    ↓
2. Inference (Detectron2) - детекция объектов
    ↓
3. Анализ координат и структуры
    ↓
4. OpenRouter API (LLM) - коррекция кода
    ↓
5. Возврат исправленного Astro кода
```

## Компоненты

- **API Server** (FastAPI): REST API для приема запросов
- **Generation Service**: Генерация HTML кода по описанию через LLM
- **Screenshot Service**: Создание скриншотов страниц через Playwright
- **Inference Engine**: Модуль детекции объектов на основе Detectron2
- **Correction Service**: Автоматическая коррекция кода через OpenRouter API (поддерживает различные LLM модели)
- **Deploy Service**: Деплой и хранение готовых сайтов
- **Docker**: Контейнеризация для развертывания

## Установка и запуск

### Требования

- Docker и Docker Compose
- OpenRouter API ключ (для доступа к LLM моделям через OpenRouter)
- Обученная модель Detectron2 (model_final.pth)

### Быстрый старт

1. Клонируйте репозиторий и перейдите в директорию:
```bash
cd astro-correction-api
```

2. Создайте файл `.env`:
```bash
cp .env.example .env
```

3. Заполните переменные окружения в `.env`:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openai/gpt-4-turbo-preview
MODEL_PATH=/app/models/model_final.pth
CONFIG_PATH=/app/config/config.yaml
```

4. Запустите через Docker Compose:
```bash
docker-compose up -d
```

5. API будет доступно по адресу: `http://localhost:8000`

## Использование API

### Endpoint: POST `/api/v1/generate` (Новый!)

Генерирует сайт по описанию с автоматической коррекцией наложений.

**Запрос:**
```json
{
  "description": "Создай сайт для портфолио фотографа с галереей работ",
  "site_style": "современный, минималистичный",
  "num_pages": 2,
  "max_correction_iterations": 3
}
```

**Ответ:**
```json
{
  "status": "success",
  "site_hash": "a1b2c3d4e5f6g7h8",
  "site_url": "http://your-ip:8000/site/a1b2c3d4e5f6g7h8",
  "total_pages": 2,
  "pages": [
    {
      "page_id": "page_1",
      "corrections_applied": 2,
      "final_overlaps": 0
    }
  ]
}
```

Подробнее см. [GENERATION_API.md](GENERATION_API.md)

### Endpoint: POST `/api/v1/correct`

Принимает JSON с кодом Astro страницы и возвращает исправленный код.

**Запрос:**
```json
{
  "astro_code": "<html>...</html>",
  "page_id": "page_1",
  "options": {
    "confidence_threshold": 0.5,
    "preserve_blocks": true
  }
}
```

**Ответ:**
```json
{
  "status": "success",
  "corrected_code": "<html>...</html>",
  "detections": {
    "total_objects": 22,
    "overlaps": 0
  },
  "corrections_applied": [
    "Updated block coordinates",
    "Fixed positioning"
  ]
}
```

### Endpoint: GET `/api/v1/health`

Проверка работоспособности API.

**Ответ:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "openai_configured": true
}
```

### Endpoint: GET `/site/{site_hash}`

Возвращает главную страницу деплоенного сайта.

**Пример:**
```
GET /site/a1b2c3d4e5f6g7h8
```

### Endpoint: GET `/site/{site_hash}/{page_id}`

Возвращает конкретную страницу деплоенного сайта.

**Пример:**
```
GET /site/a1b2c3d4e5f6g7h8/page_2
```

## Структура проекта

```
astro-correction-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API маршруты
│   ├── services/
│   │   ├── __init__.py
│   │   ├── generation.py    # Генерация сайтов
│   │   ├── screenshot.py    # Создание скриншотов
│   │   ├── inference.py      # Детекция объектов
│   │   ├── chatgpt.py        # Интеграция с LLM
│   │   └── deploy.py         # Деплой сайтов
│   ├── models/
│   │   └── schemas.py        # Pydantic модели
│   └── utils/
│       ├── __init__.py
│       └── html_parser.py    # Парсинг HTML
├── config/
│   └── config.yaml          # Конфигурация Detectron2
├── models/
│   └── model_final.pth      # Обученная модель
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Переменные окружения

- `OPENROUTER_API_KEY` - API ключ OpenRouter
- `OPENROUTER_MODEL` - Модель для использования (формат: provider/model-name, например: openai/gpt-4-turbo-preview)
- `OPENROUTER_BASE_URL` - Базовый URL OpenRouter API (по умолчанию https://openrouter.ai/api/v1)
- `MODEL_PATH` - Путь к модели Detectron2
- `CONFIG_PATH` - Путь к конфигурации модели
- `SITES_DIR` - Директория для хранения деплоенных сайтов (по умолчанию /app/data/sites)
- `API_HOST` - Хост API (по умолчанию 0.0.0.0)
- `API_PORT` - Порт API (по умолчанию 8000)
- `LOG_LEVEL` - Уровень логирования (INFO, DEBUG, ERROR)

## Развертывание на сервере

1. Убедитесь, что у сервера есть статический IP
2. Скопируйте проект на сервер
3. Настройте `.env` файл
4. Запустите: `docker-compose up -d`
5. Настройте reverse proxy (nginx) для HTTPS (опционально)

## Мониторинг и логи

Логи доступны через:
```bash
docker-compose logs -f api
```

## Лицензия

MIT
#   a s t r o - c o r r e c t i o n - a p i 
 
 