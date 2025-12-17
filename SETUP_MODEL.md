# Инструкция по настройке модели

## Требования

Для работы системы необходима обученная модель Detectron2 в формате `.pth`.

## Шаги настройки

### 1. Получение модели

Модель должна быть обучена и сохранена как `model_final.pth`. Если у вас есть обученная модель из проекта `cpu-version`, скопируйте её:

```bash
# Из директории cpu-version
cp cpu-version/model_final.pth astro-correction-api/models/
```

### 2. Проверка модели

Убедитесь, что файл модели существует и имеет правильный размер:

```bash
ls -lh models/model_final.pth

# Должен показать что-то вроде:
# -rw-r--r-- 1 user user 50M Dec 16 10:00 models/model_final.pth
```

### 3. Проверка конфигурации

Убедитесь, что файл конфигурации существует:

```bash
ls -lh config/config.yaml

# Должен показать:
# -rw-r--r-- 1 user user 2.5K Dec 16 10:00 config/config.yaml
```

### 4. Настройка путей в .env

В файле `.env` убедитесь, что пути указаны правильно:

```env
MODEL_PATH=/app/models/model_final.pth
CONFIG_PATH=/app/config/config.yaml
```

**Важно:** Пути указаны относительно контейнера Docker (`/app/`), а не хост-системы.

### 5. Проверка через Docker

После запуска контейнера проверьте, что модель загружается:

```bash
docker-compose logs api | grep "Model"

# Должно показать:
# ✅ Services initialized successfully
#    Model: /app/models/model_final.pth
```

## Структура файлов

```
astro-correction-api/
├── models/
│   └── model_final.pth    # Модель Detectron2 (обязательно)
├── config/
│   └── config.yaml        # Конфигурация модели (обязательно)
└── .env                   # Переменные окружения
```

## Troubleshooting

### Ошибка "Model file not found"

1. Проверьте, что файл существует:
   ```bash
   ls -la models/model_final.pth
   ```

2. Проверьте права доступа:
   ```bash
   chmod 644 models/model_final.pth
   ```

3. Проверьте путь в `.env`:
   ```bash
   grep MODEL_PATH .env
   ```

### Ошибка "Config file not found"

1. Убедитесь, что `config/config.yaml` существует
2. Скопируйте из `cpu-version` если нужно:
   ```bash
   cp ../cpu-version/config/config.yaml config/
   ```

### Модель не загружается в Docker

1. Проверьте volume mapping в `docker-compose.yml`:
   ```yaml
   volumes:
     - ./models:/app/models:ro
     - ./config:/app/config:ro
   ```

2. Убедитесь, что файлы доступны из контейнера:
   ```bash
   docker-compose exec api ls -la /app/models/
   docker-compose exec api ls -la /app/config/
   ```

## Использование GPU (опционально)

Если у вас есть GPU и вы хотите использовать его для детекции:

1. Установите nvidia-docker2:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install nvidia-docker2
   ```

2. Обновите `docker-compose.yml`:
   ```yaml
   services:
     api:
       runtime: nvidia
       environment:
         - NVIDIA_VISIBLE_DEVICES=all
   ```

3. В `.env` установите:
   ```env
   # Detectron2 автоматически использует GPU если доступен
   ```

## Размер модели

Типичный размер модели Detectron2:
- **CPU версия:** ~50-100 MB
- **GPU версия:** ~100-200 MB

Убедитесь, что на сервере достаточно места:
```bash
df -h models/
```
