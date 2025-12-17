# Используем Ubuntu 20.04 как базовый образ
FROM ubuntu:20.04

# Установка Python 3.8 и необходимых инструментов (стандартный для Ubuntu 20.04)
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    python3 \
    python3-dev \
    python3-pip \
    python3-distutils \
    && python3 -m pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

# Установка системных зависимостей (совпадает с cpu-version)
RUN apt-get update && apt-get install -y \
    git \
    wget \
    ninja-build \
    build-essential \
    cmake \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libgl1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование requirements.txt и установка зависимостей
COPY requirements.txt .

# Установка torch и torchvision сначала (требуется для detectron2)
# Используем те же версии что в cpu-version (без жестких ограничений для совместимости)
RUN python3 -m pip install torch torchvision

# Установка базовых зависимостей для detectron2 (как в cpu-version)
RUN python3 -m pip install opencv-python-headless pillow numpy

# Установка fvcore (требуется для detectron2, как в cpu-version)
RUN python3 -m pip install 'git+https://github.com/facebookresearch/fvcore'

# Установка остальных зависимостей API
RUN python3 -m pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 pydantic-settings==2.1.0 python-multipart==0.0.6 openai==1.3.5 aiofiles==23.2.1 python-dotenv==1.0.0 beautifulsoup4==4.12.2 lxml==4.9.3 playwright==1.40.0

# Установка Detectron2 (после установки torch и fvcore)
RUN python3 -m pip install 'git+https://github.com/facebookresearch/detectron2.git'

# Установка браузеров Playwright
RUN python3 -m playwright install chromium
# Установка зависимостей Playwright (в Ubuntu 20.04 все пакеты доступны)
RUN python3 -m playwright install-deps chromium 

# Копирование кода приложения
COPY app/ ./app/
COPY config/ ./config/

# Создание директорий для моделей и данных
RUN mkdir -p /app/models /app/data/images /app/data/pages /app/data/sites

# Установка переменных окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
