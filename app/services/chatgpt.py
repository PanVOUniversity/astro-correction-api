"""
Сервис для коррекции кода с помощью OpenRouter API
"""

import json
from typing import Dict, List, Optional
from openai import OpenAI


class ChatGPTService:
    """Сервис для работы с OpenRouter API (поддерживает различные LLM модели)"""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4-turbo-preview", base_url: str = "https://openrouter.ai/api/v1"):
        """
        Инициализация сервиса через OpenRouter
        
        Args:
            api_key: API ключ OpenRouter
            model: Модель для использования (формат: provider/model-name)
            base_url: Базовый URL OpenRouter API
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.api_key = api_key
    
    def correct_code(
        self,
        astro_code: str,
        detections: Dict,
        page_id: str,
        preserve_blocks: bool = True
    ) -> Dict[str, any]:
        """
        Исправляет Astro код на основе результатов детекции
        
        Args:
            astro_code: Исходный код страницы на Astro
            detections: Результаты детекции объектов
            page_id: Идентификатор страницы
            preserve_blocks: Сохранять существующие блоки
            
        Returns:
            Словарь с исправленным кодом и информацией об исправлениях
        """
        # Формируем промпт для ChatGPT
        prompt = self._build_prompt(astro_code, detections, page_id, preserve_blocks)
        
        try:
            # OpenRouter поддерживает стандартный OpenAI API формат
            # Дополнительные заголовки можно добавить через default_headers при инициализации клиента
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по веб-разработке и Astro. Ты помогаешь исправлять HTML код страниц на основе данных детекции объектов. Ты обновляешь координаты блоков (position: absolute) используя данные из детекции, конвертируя пиксели в vw/vh единицы. Важно: не удаляй существующие блоки, только обновляй их координаты и добавляй новые при необходимости."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            corrected_code = response.choices[0].message.content
            
            # Извлекаем исправления из ответа
            corrections_applied = self._extract_corrections(corrected_code)
            
            return {
                "corrected_code": corrected_code,
                "corrections_applied": corrections_applied,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "corrected_code": astro_code,
                "corrections_applied": [],
                "status": "error",
                "error": str(e)
            }
    
    def _build_prompt(
        self,
        astro_code: str,
        detections: Dict,
        page_id: str,
        preserve_blocks: bool
    ) -> str:
        """Формирует промпт для LLM через OpenRouter"""
        
        objects_info = []
        for obj in detections.get("objects", []):
            objects_info.append(
                f"Объект {obj['id']}: "
                f"BBox=[{obj['bbox'][0]:.1f}, {obj['bbox'][1]:.1f}, {obj['bbox'][2]:.1f}, {obj['bbox'][3]:.1f}], "
                f"Размер={obj['bbox_size'][0]:.1f}x{obj['bbox_size'][1]:.1f}px, "
                f"Score={obj['score']:.3f}"
            )
        
        image_size = detections.get("image_size", [390, 2532])
        img_width, img_height = image_size[0], image_size[1]
        
        prompt = f"""Исправь HTML код страницы на основе данных детекции объектов.

Исходный код:
```html
{astro_code}
```

Данные детекции:
- Всего объектов: {detections.get('total_objects', 0)}
- Перекрытий: {detections.get('overlaps', 0)}
- Размер изображения: {img_width}x{img_height} пикселей

Объекты:
{chr(10).join(objects_info)}

Инструкции:
1. Обнови координаты всех блоков с классом 'block' на основе данных детекции
2. Конвертируй координаты из пикселей в vw/vh единицы:
   - left = (x1 / {img_width}) * 100 vw
   - top = (y1 / {img_height}) * 100 vh
   - width = ((x2 - x1) / {img_width}) * 100 vw
   - height = ((y2 - y1) / {img_height}) * 100 vh
3. {"Сохрани все существующие блоки, только обнови их координаты" if preserve_blocks else "Добавь новые блоки для всех обнаруженных объектов"}
4. Если обнаружено больше объектов, чем блоков в HTML, добавь новые блоки
5. Сохрани все остальные атрибуты блоков (z-index, border-radius, background, box-shadow и т.д.)
6. Верни только исправленный HTML код без дополнительных объяснений

Верни исправленный HTML код:"""
        
        return prompt
    
    def _extract_corrections(self, corrected_code: str) -> List[str]:
        """Извлекает список примененных исправлений"""
        corrections = []
        
        # Простая эвристика для определения исправлений
        if "position:absolute" in corrected_code:
            corrections.append("Updated block coordinates")
        if "vw" in corrected_code and "vh" in corrected_code:
            corrections.append("Converted pixels to viewport units")
        
        return corrections
