# Настройка OpenRouter API

## Что такое OpenRouter?

OpenRouter - это унифицированный API для доступа к различным LLM моделям (GPT-4, Claude, Llama и др.) через единый интерфейс. Это позволяет легко переключаться между различными моделями без изменения кода.

## Преимущества использования OpenRouter

1. **Доступ к множеству моделей** - GPT-4, Claude, Llama, Mistral и другие
2. **Единый API** - один интерфейс для всех моделей
3. **Гибкость** - легко переключаться между моделями
4. **Прозрачное ценообразование** - видно стоимость каждого запроса

## Получение API ключа

1. Перейдите на https://openrouter.ai/
2. Зарегистрируйтесь или войдите в аккаунт
3. Перейдите в раздел "Keys" в настройках
4. Создайте новый API ключ
5. Скопируйте ключ (начинается с `sk-or-...`)

## Настройка в проекте

### 1. Обновите `.env` файл

```env
OPENROUTER_API_KEY=sk-or-your-actual-key-here
OPENROUTER_MODEL=openai/gpt-4-turbo-preview
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

### 2. Выбор модели

OpenRouter поддерживает множество моделей. Формат: `provider/model-name`

**Популярные модели:**

- `openai/gpt-4-turbo-preview` - GPT-4 Turbo (рекомендуется)
- `openai/gpt-4` - GPT-4
- `openai/gpt-3.5-turbo` - GPT-3.5 Turbo (более дешевая)
- `anthropic/claude-3-opus` - Claude 3 Opus
- `anthropic/claude-3-sonnet` - Claude 3 Sonnet
- `meta-llama/llama-3-70b-instruct` - Llama 3 70B
- `google/gemini-pro` - Google Gemini Pro

**Список всех доступных моделей:**
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### 3. Проверка работы

После настройки проверьте health endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "openai_configured": true,
  "version": "1.0.0"
}
```

## Использование различных моделей

### Переключение модели

Просто измените `OPENROUTER_MODEL` в `.env`:

```env
# Использовать GPT-4
OPENROUTER_MODEL=openai/gpt-4-turbo-preview

# Или Claude
OPENROUTER_MODEL=anthropic/claude-3-sonnet

# Или Llama
OPENROUTER_MODEL=meta-llama/llama-3-70b-instruct
```

После изменения перезапустите контейнер:
```bash
docker-compose restart api
```

### Рекомендации по выбору модели

- **Для точности:** `openai/gpt-4-turbo-preview` или `anthropic/claude-3-opus`
- **Для экономии:** `openai/gpt-3.5-turbo` или `meta-llama/llama-3-8b-instruct`
- **Для скорости:** `openai/gpt-3.5-turbo` или `anthropic/claude-3-haiku`

## Мониторинг использования

OpenRouter предоставляет дашборд для мониторинга:
- Количество запросов
- Потраченные средства
- Использование по моделям

Доступен на https://openrouter.ai/activity

## Troubleshooting

### Ошибка "Invalid API key"

1. Проверьте, что ключ скопирован полностью (начинается с `sk-or-`)
2. Убедитесь, что ключ активен в настройках OpenRouter
3. Проверьте, что в `.env` нет лишних пробелов

### Ошибка "Model not found"

1. Проверьте правильность формата: `provider/model-name`
2. Убедитесь, что модель доступна в вашем плане OpenRouter
3. Проверьте список доступных моделей через API

### Ошибка "Rate limit exceeded"

1. Проверьте лимиты в настройках OpenRouter
2. Рассмотрите переход на более дешевую модель
3. Добавьте задержки между запросами

## Стоимость

Стоимость зависит от выбранной модели. OpenRouter показывает стоимость каждого запроса в ответе API.

Примерные цены (на момент написания):
- GPT-4 Turbo: ~$0.01-0.03 за запрос
- GPT-3.5 Turbo: ~$0.001-0.002 за запрос
- Claude 3 Sonnet: ~$0.003-0.015 за запрос

Актуальные цены: https://openrouter.ai/models

## Дополнительная информация

- Документация OpenRouter: https://openrouter.ai/docs
- Список моделей: https://openrouter.ai/models
- Примеры использования: https://openrouter.ai/docs/quick-start
