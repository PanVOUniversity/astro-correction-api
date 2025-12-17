"""
Pydantic модели для API запросов и ответов
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CorrectionOptions(BaseModel):
    """Опции для коррекции кода"""
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Порог уверенности для детекции")
    preserve_blocks: bool = Field(default=True, description="Сохранять существующие блоки")
    max_corrections: Optional[int] = Field(default=None, description="Максимальное количество исправлений")


class CorrectionRequest(BaseModel):
    """Запрос на коррекцию Astro кода"""
    astro_code: str = Field(..., description="Код страницы на Astro (HTML)")
    page_id: str = Field(..., description="Идентификатор страницы")
    options: Optional[CorrectionOptions] = Field(default=None, description="Опции коррекции")


class DetectionInfo(BaseModel):
    """Информация о детекции объектов"""
    total_objects: int = Field(..., description="Общее количество обнаруженных объектов")
    overlaps: int = Field(..., description="Количество перекрытий")
    objects: List[Dict[str, Any]] = Field(default_factory=list, description="Детальная информация об объектах")


class CorrectionResponse(BaseModel):
    """Ответ с исправленным кодом"""
    status: str = Field(..., description="Статус операции")
    corrected_code: str = Field(..., description="Исправленный Astro код")
    detections: DetectionInfo = Field(..., description="Информация о детекции")
    corrections_applied: List[str] = Field(default_factory=list, description="Список примененных исправлений")
    error: Optional[str] = Field(default=None, description="Сообщение об ошибке, если есть")


class HealthResponse(BaseModel):
    """Ответ проверки здоровья API"""
    status: str = Field(..., description="Статус API")
    model_loaded: bool = Field(..., description="Модель загружена")
    openai_configured: bool = Field(..., description="OpenAI настроен")
    version: str = Field(..., description="Версия API")


class GenerateRequest(BaseModel):
    """Запрос на генерацию сайта по описанию"""
    description: str = Field(..., description="Описание сайта от пользователя")
    site_style: Optional[str] = Field(default=None, description="Стиль сайта (опционально)")
    num_pages: int = Field(default=1, ge=1, le=10, description="Количество страниц")
    max_correction_iterations: int = Field(default=3, ge=1, le=10, description="Максимальное количество итераций коррекции")
    viewport_width: int = Field(default=390, description="Ширина viewport для скриншотов")
    viewport_height: int = Field(default=844, description="Высота viewport для скриншотов")


class PageInfo(BaseModel):
    """Информация о странице"""
    page_id: str = Field(..., description="ID страницы")
    corrections_applied: int = Field(..., description="Количество примененных исправлений")
    final_overlaps: int = Field(..., description="Количество перекрытий после коррекции")


class GenerateResponse(BaseModel):
    """Ответ на запрос генерации сайта"""
    status: str = Field(..., description="Статус операции")
    site_hash: str = Field(..., description="Хеш сайта для доступа")
    site_url: str = Field(..., description="URL готового сайта")
    total_pages: int = Field(..., description="Общее количество страниц")
    pages: List[PageInfo] = Field(default_factory=list, description="Информация о страницах")
    error: Optional[str] = Field(default=None, description="Сообщение об ошибке, если есть")