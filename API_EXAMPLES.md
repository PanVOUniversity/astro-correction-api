# Примеры использования API

## Базовые примеры

### 1. Проверка работоспособности

```bash
curl http://localhost:8000/api/v1/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "openai_configured": true,
  "version": "1.0.0"
}
```

### 2. Коррекция Astro кода

**Запрос:**
```bash
curl -X POST http://localhost:8000/api/v1/correct \
  -H "Content-Type: application/json" \
  -d '{
    "astro_code": "<html><body><div class=\"block\" style=\"position:absolute; top:10vh; left:20vw;\">Content</div></body></html>",
    "page_id": "page_1",
    "options": {
      "confidence_threshold": 0.5,
      "preserve_blocks": true
    }
  }'
```

**Ответ:**
```json
{
  "status": "success",
  "corrected_code": "<html>...</html>",
  "detections": {
    "total_objects": 22,
    "overlaps": 0,
    "objects": [
      {
        "id": 0,
        "score": 0.999,
        "bbox": [194.0, 1779.0, 388.0, 1889.0],
        "bbox_center": [291.0, 1834.0],
        "bbox_size": [194.0, 110.0],
        "mask_area": 20858
      }
    ]
  },
  "corrections_applied": [
    "Updated block coordinates",
    "Converted pixels to viewport units"
  ],
  "error": null
}
```

### 3. Только детекция объектов (без коррекции)

```bash
curl -X POST http://localhost:8000/api/v1/detect \
  -F "image=@/path/to/screenshot.png"
```

**Ответ:**
```json
{
  "total_objects": 22,
  "overlaps": 0,
  "objects": [...],
  "image_size": [390, 2532]
}
```

## Примеры на Python

### Базовый пример

```python
import requests
import json

API_URL = "http://localhost:8000/api/v1"

# Проверка здоровья
response = requests.get(f"{API_URL}/health")
print(response.json())

# Коррекция кода
astro_code = """
<html>
<body>
  <div class="block" style="position:absolute; top:10vh; left:20vw;">
    Content
  </div>
</body>
</html>
"""

payload = {
    "astro_code": astro_code,
    "page_id": "page_1",
    "options": {
        "confidence_threshold": 0.5,
        "preserve_blocks": True
    }
}

response = requests.post(
    f"{API_URL}/correct",
    json=payload,
    headers={"Content-Type": "application/json"}
)

result = response.json()
print(f"Status: {result['status']}")
print(f"Corrections: {result['corrections_applied']}")
print(f"Corrected code:\n{result['corrected_code']}")
```

### Пример с обработкой ошибок

```python
import requests
from requests.exceptions import RequestException

def correct_astro_code(astro_code: str, page_id: str) -> dict:
    """Корректирует Astro код через API"""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/correct",
            json={
                "astro_code": astro_code,
                "page_id": page_id,
                "options": {
                    "confidence_threshold": 0.5,
                    "preserve_blocks": True
                }
            },
            timeout=60  # 60 секунд таймаут
        )
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Ошибка запроса: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return {"status": "error", "error": str(e)}

# Использование
result = correct_astro_code("<html>...</html>", "page_1")
if result.get("status") == "success":
    print("Код успешно исправлен!")
    print(result["corrected_code"])
else:
    print(f"Ошибка: {result.get('error')}")
```

## Примеры на JavaScript/Node.js

### Базовый пример

```javascript
const axios = require('axios');

const API_URL = 'http://localhost:8000/api/v1';

// Проверка здоровья
async function checkHealth() {
  try {
    const response = await axios.get(`${API_URL}/health`);
    console.log(response.data);
  } catch (error) {
    console.error('Ошибка:', error.message);
  }
}

// Коррекция кода
async function correctCode(astroCode, pageId) {
  try {
    const response = await axios.post(`${API_URL}/correct`, {
      astro_code: astroCode,
      page_id: pageId,
      options: {
        confidence_threshold: 0.5,
        preserve_blocks: true
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Ошибка коррекции:', error.response?.data || error.message);
    throw error;
  }
}

// Использование
const astroCode = `
<html>
<body>
  <div class="block" style="position:absolute; top:10vh; left:20vw;">
    Content
  </div>
</body>
</html>
`;

correctCode(astroCode, 'page_1')
  .then(result => {
    console.log('Статус:', result.status);
    console.log('Исправления:', result.corrections_applied);
    console.log('Исправленный код:', result.corrected_code);
  })
  .catch(error => {
    console.error('Ошибка:', error);
  });
```

## Примеры на cURL (продвинутые)

### С сохранением результата в файл

```bash
curl -X POST http://localhost:8000/api/v1/correct \
  -H "Content-Type: application/json" \
  -d @request.json \
  -o response.json
```

Где `request.json`:
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

### С таймаутом и повторными попытками

```bash
#!/bin/bash

API_URL="http://localhost:8000/api/v1"
MAX_RETRIES=3
RETRY_DELAY=5

for i in $(seq 1 $MAX_RETRIES); do
  response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/correct" \
    -H "Content-Type: application/json" \
    -d @request.json \
    --max-time 120)
  
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  if [ "$http_code" -eq 200 ]; then
    echo "$body" | jq .
    break
  else
    echo "Попытка $i/$MAX_RETRIES неудачна (HTTP $http_code)"
    if [ $i -lt $MAX_RETRIES ]; then
      sleep $RETRY_DELAY
    fi
  fi
done
```

## Интеграция в CI/CD

### GitHub Actions пример

```yaml
name: Correct Astro Code

on:
  push:
    branches: [ main ]

jobs:
  correct:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Correct Astro code
        run: |
          curl -X POST ${{ secrets.API_URL }}/api/v1/correct \
            -H "Content-Type: application/json" \
            -d '{
              "astro_code": "${{ github.event.head_commit.message }}",
              "page_id": "page_1"
            }' \
            -o corrected.html
      
      - name: Commit corrected code
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add corrected.html
          git commit -m "Auto-corrected code" || exit 0
          git push
```

## Мониторинг и метрики

### Проверка метрик (если добавлен endpoint)

```bash
curl http://localhost:8000/api/v1/metrics
```

### Логирование запросов

Все запросы логируются автоматически. Просмотр логов:

```bash
docker-compose logs -f api | grep "POST /api/v1/correct"
```
