"""
Сервис для генерации сайтов по описанию с использованием LLM
"""

import re
from typing import Dict, List, Optional
from openai import OpenAI


class GenerationService:
    """Сервис для генерации сайтов по описанию через OpenRouter API"""
    
    def __init__(self, api_key: str, model: str = "openai/gpt-4-turbo-preview", base_url: str = "https://openrouter.ai/api/v1"):
        """
        Инициализация сервиса генерации
        
        Args:
            api_key: API ключ OpenRouter
            model: Модель для использования
            base_url: Базовый URL OpenRouter API
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.api_key = api_key
    
    def generate_site_from_description(
        self,
        description: str,
        site_style: Optional[str] = None,
        num_pages: int = 1
    ) -> Dict:
        """
        Генерирует сайт на основе описания
        
        Args:
            description: Описание сайта от пользователя
            site_style: Стиль сайта (опционально)
            num_pages: Количество страниц для генерации
            
        Returns:
            Словарь с HTML кодом страниц
        """
        prompt = self._build_generation_prompt(description, site_style, num_pages)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Ты эксперт по веб-разработке и Astro. Ты создаешь современные, красивые веб-сайты на основе описания пользователя.

Требования к HTML коду:
1. Используй современный HTML5 с семантическими тегами
2. Все блоки контента должны иметь класс 'block' и position: absolute
3. Используй viewport единицы (vw, vh) для адаптивности
4. Добавь красивые стили: градиенты, тени, скругления
5. Используй современную цветовую палитру
6. Создай структурированный контент с заголовками, параграфами, изображениями
7. Каждая страница должна быть в отдельном HTML файле
8. Используй встроенные стили в <style> теге

Формат ответа:
- Если одна страница: верни один HTML блок
- Если несколько страниц: верни JSON с ключами page_1, page_2, etc., где значения - HTML код"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=8000
            )
            
            generated_content = response.choices[0].message.content
            
            # Парсим результат
            pages = self._parse_generated_content(generated_content, num_pages)
            
            return {
                "status": "success",
                "pages": pages,
                "total_pages": len(pages)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "pages": []
            }
    
    def _build_generation_prompt(
        self,
        description: str,
        site_style: Optional[str],
        num_pages: int
    ) -> str:
        """Формирует промпт для генерации сайта"""
        
        style_part = f"\nСтиль сайта: {site_style}" if site_style else ""
        
        prompt = f"""Создай веб-сайт на основе следующего описания:

{description}{style_part}

Требования:
- Количество страниц: {num_pages}
- Все блоки контента должны иметь класс 'block' и position: absolute
- Используй viewport единицы (vw, vh) для размеров и позиций
- Создай красивый современный дизайн
- Добавь разнообразный контент: заголовки, текст, изображения (используй placeholder изображения)
- Используй градиенты, тени, скругления для визуальной привлекательности

{"Если страниц несколько, верни JSON объект с ключами page_1, page_2, etc. и значениями - HTML кодом страниц." if num_pages > 1 else "Верни готовый HTML код страницы."}"""
        
        return prompt
    
    def _parse_generated_content(self, content: str, num_pages: int) -> List[Dict[str, str]]:
        """Парсит сгенерированный контент и извлекает HTML страниц"""
        pages = []
        
        if num_pages == 1:
            # Одна страница - просто HTML код
            html_code = self._extract_html(content)
            if html_code:
                pages.append({
                    "page_id": "page_1",
                    "html": html_code
                })
        else:
            # Несколько страниц - пытаемся найти JSON или отдельные HTML блоки
            # Сначала пробуем найти JSON
            json_match = re.search(r'\{[^{}]*"page_\d+"[^{}]*\}', content, re.DOTALL)
            if json_match:
                try:
                    import json
                    pages_dict = json.loads(json_match.group())
                    for key, html in pages_dict.items():
                        if key.startswith("page_"):
                            pages.append({
                                "page_id": key,
                                "html": html
                            })
                except:
                    pass
            
            # Если JSON не найден, ищем отдельные HTML блоки
            if not pages:
                html_blocks = re.findall(r'<html[^>]*>.*?</html>', content, re.DOTALL | re.IGNORECASE)
                for i, html in enumerate(html_blocks[:num_pages], 1):
                    pages.append({
                        "page_id": f"page_{i}",
                        "html": html
                    })
        
        # Если ничего не найдено, создаем базовую страницу
        if not pages:
            pages.append({
                "page_id": "page_1",
                "html": self._create_default_html(content)
            })
        
        return pages
    
    def _extract_html(self, content: str) -> str:
        """Извлекает HTML код из текста"""
        # Ищем HTML теги
        html_match = re.search(r'<html[^>]*>.*?</html>', content, re.DOTALL | re.IGNORECASE)
        if html_match:
            return html_match.group()
        
        # Если нет полного HTML, ищем body
        body_match = re.search(r'<body[^>]*>.*?</body>', content, re.DOTALL | re.IGNORECASE)
        if body_match:
            return f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Generated Site</title></head>{body_match.group()}</html>"
        
        # Если ничего не найдено, возвращаем весь контент как HTML
        return content
    
    def _create_default_html(self, description: str) -> str:
        """Создает базовую HTML страницу если генерация не удалась"""
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generated Site</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            position: relative;
        }}
        .block {{
            position: absolute;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 2vw;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }}
    </style>
</head>
<body>
    <div class="block" style="left: 10vw; top: 10vh; width: 80vw; height: auto; padding: 3vw;">
        <h1 style="font-size: 4vw; margin-bottom: 2vh; color: #333;">Сгенерированный сайт</h1>
        <p style="font-size: 2vw; line-height: 1.6; color: #666;">{description[:200]}</p>
    </div>
</body>
</html>"""

