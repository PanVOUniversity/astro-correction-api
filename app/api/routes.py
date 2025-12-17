"""
API маршруты для коррекции Astro кода
"""

import os
import tempfile
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi import Request

from app.models.schemas import (
    CorrectionRequest,
    CorrectionResponse,
    HealthResponse,
    DetectionInfo,
    GenerateRequest,
    GenerateResponse,
    PageInfo
)
from app.services.inference import InferenceService
from app.services.chatgpt import ChatGPTService
from app.services.generation import GenerationService
from app.services.screenshot import ScreenshotService
from app.services.deploy import DeployService
from app import __version__


router = APIRouter()

# Глобальные сервисы (инициализируются в main.py)
inference_service: Optional[InferenceService] = None
chatgpt_service: Optional[ChatGPTService] = None
generation_service: Optional[GenerationService] = None
screenshot_service: Optional[ScreenshotService] = None
deploy_service: Optional[DeployService] = None


def set_services(
    inference: InferenceService,
    chatgpt: ChatGPTService,
    generation: GenerationService,
    screenshot: ScreenshotService,
    deploy: DeployService
):
    """Устанавливает сервисы для использования в роутерах"""
    global inference_service, chatgpt_service, generation_service, screenshot_service, deploy_service
    inference_service = inference
    chatgpt_service = chatgpt
    generation_service = generation
    screenshot_service = screenshot
    deploy_service = deploy


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Проверка работоспособности API"""
    model_loaded = inference_service is not None
    openrouter_configured = chatgpt_service is not None
    
    return HealthResponse(
        status="healthy" if (model_loaded and openrouter_configured) else "degraded",
        model_loaded=model_loaded,
        openai_configured=openrouter_configured,  # Сохраняем имя поля для обратной совместимости
        version=__version__
    )


@router.post("/correct", response_model=CorrectionResponse)
async def correct_code(request: CorrectionRequest):
    """
    Исправляет Astro код на основе детекции объектов
    
    Принимает код страницы, выполняет детекцию и возвращает исправленный код
    """
    if not inference_service or not chatgpt_service:
        raise HTTPException(
            status_code=503,
            detail="Services not initialized"
        )
    
    try:
        # Создаем временный файл для HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
            html_file.write(request.astro_code)
            html_path = html_file.name
        
        # Для детекции нужен скриншот страницы
        # В реальной системе здесь бы использовался headless браузер (Playwright/Selenium)
        # Для демонстрации используем существующее изображение если есть
        # Или создаем заглушку
        
        # TODO: Интеграция с headless браузером для генерации скриншота
        # Пока используем существующее изображение из cpu-version если доступно
        image_path = None
        default_image = Path("/app/data/images/page_1.png")
        
        if default_image.exists():
            image_path = str(default_image)
        else:
            # Если изображения нет, возвращаем ошибку
            raise HTTPException(
                status_code=400,
                detail="Image file required for detection. Please provide screenshot of the page."
            )
        
        # Выполняем детекцию
        detections = inference_service.detect_objects(image_path)
        
        # Исправляем код с помощью ChatGPT
        options = request.options or {}
        preserve_blocks = options.preserve_blocks if options.preserve_blocks is not None else True
        
        correction_result = chatgpt_service.correct_code(
            astro_code=request.astro_code,
            detections=detections,
            page_id=request.page_id,
            preserve_blocks=preserve_blocks
        )
        
        # Формируем ответ
        detection_info = DetectionInfo(
            total_objects=detections.get("total_objects", 0),
            overlaps=detections.get("overlaps", 0),
            objects=detections.get("objects", [])
        )
        
        # Удаляем временный файл
        try:
            os.unlink(html_path)
        except:
            pass
        
        return CorrectionResponse(
            status=correction_result.get("status", "success"),
            corrected_code=correction_result.get("corrected_code", request.astro_code),
            detections=detection_info,
            corrections_applied=correction_result.get("corrections_applied", []),
            error=correction_result.get("error")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/detect")
async def detect_objects_only(image: UploadFile = File(...)):
    """
    Выполняет только детекцию объектов на изображении
    (без коррекции кода)
    """
    if not inference_service:
        raise HTTPException(
            status_code=503,
            detail="Inference service not initialized"
        )
    
    try:
        # Сохраняем загруженное изображение во временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            content = await image.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Выполняем детекцию
        detections = inference_service.detect_objects(tmp_path)
        
        # Удаляем временный файл
        try:
            os.unlink(tmp_path)
        except:
            pass
        
        return JSONResponse(content=detections)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Detection error: {str(e)}"
        )


@router.post("/generate", response_model=GenerateResponse)
async def generate_site(request: GenerateRequest, http_request: Request):
    """
    Генерирует сайт по описанию с итеративной коррекцией наложений
    
    Процесс:
    1. Генерирует сайт по описанию через LLM
    2. Создает скриншоты для каждой страницы
    3. Итеративно исправляет наложения на каждой странице
    4. Деплоит готовый сайт
    5. Возвращает ссылку на сайт
    """
    if not all([generation_service, screenshot_service, inference_service, chatgpt_service, deploy_service]):
        raise HTTPException(
            status_code=503,
            detail="Services not initialized"
        )
    
    try:
        # 1. Генерация сайта по описанию
        generation_result = generation_service.generate_site_from_description(
            description=request.description,
            site_style=request.site_style,
            num_pages=request.num_pages
        )
        
        if generation_result.get("status") != "success":
            return GenerateResponse(
                status="error",
                site_hash="",
                site_url="",
                total_pages=0,
                error=generation_result.get("error", "Generation failed")
            )
        
        pages = generation_result.get("pages", [])
        if not pages:
            return GenerateResponse(
                status="error",
                site_hash="",
                site_url="",
                total_pages=0,
                error="No pages generated"
            )
        
        # Инициализация браузера для скриншотов
        await screenshot_service.initialize()
        
        corrected_pages = []
        pages_info = []
        
        # 2. Обработка каждой страницы
        for page in pages:
            page_id = page.get("page_id", "page_1")
            html_content = page.get("html", "")
            corrections_count = 0
            
            # Итеративная коррекция
            final_overlaps = 0
            for iteration in range(request.max_correction_iterations):
                # Создание скриншота
                screenshot_path = None
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    screenshot_path = tmp_file.name
                
                try:
                    screenshot_result, (img_width, img_height) = await screenshot_service.create_screenshot_from_html(
                        html_content=html_content,
                        width=request.viewport_width,
                        height=request.viewport_height,
                        output_path=screenshot_path
                    )
                    
                    # Детекция объектов
                    detections = inference_service.detect_objects(screenshot_path)
                    final_overlaps = detections.get("overlaps", 0)
                    
                    # Если нет наложений, можно выходить
                    if final_overlaps == 0:
                        break
                    
                    # Коррекция кода
                    correction_result = chatgpt_service.correct_code(
                        astro_code=html_content,
                        detections=detections,
                        page_id=page_id,
                        preserve_blocks=True
                    )
                    
                    if correction_result.get("status") == "success":
                        html_content = correction_result.get("corrected_code", html_content)
                        corrections_count += 1
                    else:
                        # Если коррекция не удалась, прекращаем итерации
                        break
                    
                finally:
                    # Удаляем временный скриншот
                    if screenshot_path and os.path.exists(screenshot_path):
                        try:
                            os.unlink(screenshot_path)
                        except:
                            pass
            
            corrected_pages.append({
                "page_id": page_id,
                "html": html_content
            })
            
            pages_info.append(PageInfo(
                page_id=page_id,
                corrections_applied=corrections_count,
                final_overlaps=final_overlaps
            ))
        
        # Закрываем браузер
        await screenshot_service.close()
        
        # 3. Деплой сайта
        base_url = str(http_request.base_url).rstrip('/')
        site_hash = deploy_service.deploy_site(
            pages=corrected_pages,
            site_metadata={
                "description": request.description,
                "site_style": request.site_style,
                "num_pages": len(corrected_pages)
            }
        )
        
        site_url = f"{base_url}/site/{site_hash}"
        
        return GenerateResponse(
            status="success",
            site_hash=site_hash,
            site_url=site_url,
            total_pages=len(corrected_pages),
            pages=pages_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Убеждаемся, что браузер закрыт при ошибке
        try:
            await screenshot_service.close()
        except:
            pass
        
        return GenerateResponse(
            status="error",
            site_hash="",
            site_url="",
            total_pages=0,
            error=str(e)
        )


@router.get("/site/{site_hash}")
async def get_site(site_hash: str):
    """
    Возвращает главную страницу деплоенного сайта
    """
    if not deploy_service:
        raise HTTPException(
            status_code=503,
            detail="Deploy service not initialized"
        )
    
    html_content = deploy_service.get_site_page(site_hash, "index")
    
    if html_content is None:
        raise HTTPException(
            status_code=404,
            detail=f"Site {site_hash} not found"
        )
    
    return HTMLResponse(content=html_content)


@router.get("/site/{site_hash}/{page_id}")
async def get_site_page(site_hash: str, page_id: str):
    """
    Возвращает конкретную страницу деплоенного сайта
    """
    if not deploy_service:
        raise HTTPException(
            status_code=503,
            detail="Deploy service not initialized"
        )
    
    html_content = deploy_service.get_site_page(site_hash, page_id)
    
    if html_content is None:
        raise HTTPException(
            status_code=404,
            detail=f"Page {page_id} not found in site {site_hash}"
        )
    
    return HTMLResponse(content=html_content)
