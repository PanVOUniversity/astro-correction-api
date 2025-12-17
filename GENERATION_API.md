# API генерации сайтов

## Обзор

API для генерации сайтов по описанию с автоматической коррекцией наложений. Система использует гибридную архитектуру со внутренними сервисами:

- **Generation Service** - генерация HTML кода по описанию через LLM
- **Screenshot Service** - создание скриншотов страниц через Playwright
- **Inference Service** - детекция объектов на скриншотах через Detectron2
- **Correction Service** - исправление наложений через LLM
- **Deploy Service** - деплой готовых сайтов

## Endpoints

### POST /api/v1/generate

Генерирует сайт по описанию с итеративной коррекцией наложений.

**Запрос:**
```json
{
  "description": "Создай сайт для портфолио фотографа с галереей работ",
  "site_style": "современный, минималистичный",
  "num_pages": 2,
  "max_correction_iterations": 3,
  "viewport_width": 390,
  "viewport_height": 844
}
```

**Параметры:**
- `description` (обязательный) - описание сайта от пользователя
- `site_style` (опционально) - стиль сайта
- `num_pages` (по умолчанию: 1) - количество страниц (1-10)
- `max_correction_iterations` (по умолчанию: 3) - максимальное количество итераций коррекции (1-10)
- `viewport_width` (по умолчанию: 390) - ширина viewport для скриншотов
- `viewport_height` (по умолчанию: 844) - высота viewport для скриншотов

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
    },
    {
      "page_id": "page_2",
      "corrections_applied": 1,
      "final_overlaps": 0
    }
  ]
}
```

**Процесс работы:**
1. Генерация HTML кода для всех страниц через LLM
2. Для каждой страницы:
   - Создание скриншота через Playwright
   - Детекция объектов через Detectron2
   - Если есть наложения - коррекция через LLM
   - Повтор до отсутствия наложений или достижения максимума итераций
3. Деплой готового сайта
4. Возврат ссылки на сайт

### GET /site/{site_hash}

Возвращает главную страницу деплоенного сайта.

**Пример:**
```
GET /site/a1b2c3d4e5f6g7h8
```

**Ответ:** HTML код главной страницы

### GET /site/{site_hash}/{page_id}

Возвращает конкретную страницу деплоенного сайта.

**Пример:**
```
GET /site/a1b2c3d4e5f6g7h8/page_2
```

**Ответ:** HTML код указанной страницы

## Пример использования

### Python

```python
import requests

# Генерация сайта
response = requests.post(
    "http://your-ip:8000/api/v1/generate",
    json={
        "description": "Создай сайт для кафе с меню и контактами",
        "num_pages": 1,
        "max_correction_iterations": 3
    }
)

result = response.json()
print(f"Site URL: {result['site_url']}")
print(f"Total pages: {result['total_pages']}")
print(f"Corrections applied: {sum(p['corrections_applied'] for p in result['pages'])}")

# Открыть сайт в браузере
import webbrowser
webbrowser.open(result['site_url'])
```

### cURL

```bash
# Генерация сайта
curl -X POST "http://your-ip:8000/api/v1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Создай сайт для портфолио дизайнера",
    "num_pages": 2,
    "max_correction_iterations": 3
  }'

# Получение сайта
curl "http://your-ip:8000/site/a1b2c3d4e5f6g7h8"
```

## Структура деплоенных сайтов

Деплоенные сайты сохраняются в `/app/data/sites/{site_hash}/`:

```
sites/
  └── a1b2c3d4e5f6g7h8/
      ├── index.html          # Главная страница
      ├── page_1.html         # Страница 1
      ├── page_2.html         # Страница 2
      ├── pages.json          # Список страниц
      └── metadata.json       # Метаданные сайта
```

## Обработка ошибок

API возвращает стандартные HTTP коды:

- `200` - успешная операция
- `400` - неверный запрос
- `404` - сайт или страница не найдены
- `500` - внутренняя ошибка сервера
- `503` - сервисы не инициализированы

При ошибке генерации:
```json
{
  "status": "error",
  "site_hash": "",
  "site_url": "",
  "total_pages": 0,
  "error": "Описание ошибки"
}
```

## Производительность

- Генерация одной страницы: ~10-30 секунд
- Генерация нескольких страниц: ~10-30 секунд на страницу
- Время зависит от сложности сайта и количества итераций коррекции

## Ограничения

- Максимум 10 страниц за один запрос
- Максимум 10 итераций коррекции на страницу
- Размер HTML кода ограничен токенами LLM (до 8000 токенов на страницу)

## Интеграция с существующими endpoints

Новые endpoints работают вместе с существующими:

- `POST /api/v1/correct` - ручная коррекция кода
- `POST /api/v1/detect` - только детекция объектов
- `GET /api/v1/health` - проверка работоспособности

