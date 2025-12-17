"""
Главный файл FastAPI приложения
"""

import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from app.api.routes import router, set_services
from app.services.inference import InferenceService
from app.services.chatgpt import ChatGPTService
from app.services.generation import GenerationService
from app.services.screenshot import ScreenshotService
from app.services.deploy import DeployService
from app import __version__


class Settings(BaseSettings):
    """Настройки приложения"""
    # OpenRouter
    openrouter_api_key: str
    openrouter_model: str = "openai/gpt-4-turbo-preview"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Model
    model_path: str = "/app/models/model_final.pth"
    config_path: str = "/app/config/config.yaml"
    num_classes: int = 1
    thing_classes: str = "frame"
    confidence_threshold: float = 0.5
    
    # Deploy
    sites_dir: str = "/app/data/sites"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    allowed_origins: str = "*"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Загрузка настроек
settings = Settings()

# Создание FastAPI приложения
app = FastAPI(
    title="Astro Correction API",
    description="Система автоматической коррекции сайтов на основе Astro",
    version=__version__
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(",") if settings.allowed_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация сервисов
inference_service = None
chatgpt_service = None
generation_service = None
screenshot_service = None
deploy_service = None


@app.on_event("startup")
async def startup_event():
    """Инициализация сервисов при запуске"""
    global inference_service, chatgpt_service, generation_service, screenshot_service, deploy_service
    
    try:
        # Проверка существования файлов модели и конфигурации
        model_path = Path(settings.model_path)
        config_path = Path(settings.config_path)
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        # Инициализация Inference Service
        thing_classes_list = settings.thing_classes.split(",")
        inference_service = InferenceService(
            model_path=str(model_path),
            config_path=str(config_path),
            num_classes=settings.num_classes,
            thing_classes=thing_classes_list,
            confidence_threshold=settings.confidence_threshold
        )
        
        # Инициализация ChatGPT Service через OpenRouter
        chatgpt_service = ChatGPTService(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url
        )
        
        # Инициализация Generation Service
        generation_service = GenerationService(
            api_key=settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url=settings.openrouter_base_url
        )
        
        # Инициализация Screenshot Service
        screenshot_service = ScreenshotService(headless=True)
        
        # Инициализация Deploy Service
        deploy_service = DeployService(sites_dir=settings.sites_dir)
        
        # Установка сервисов в роутер
        set_services(
            inference_service,
            chatgpt_service,
            generation_service,
            screenshot_service,
            deploy_service
        )
        
        print(f"✅ Services initialized successfully")
        print(f"   Model: {model_path}")
        print(f"   Config: {config_path}")
        print(f"   OpenRouter Model: {settings.openrouter_model}")
        print(f"   Sites directory: {settings.sites_dir}")
        
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при остановке"""
    global screenshot_service
    if screenshot_service:
        await screenshot_service.close()
    print("Shutting down...")


# Подключение роутеров
app.include_router(router, prefix="/api/v1", tags=["API"])


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "name": "Astro Correction API",
        "version": __version__,
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower()
    )
