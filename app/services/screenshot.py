"""
Сервис для создания скриншотов HTML страниц с использованием Playwright
"""

import asyncio
import base64
from pathlib import Path
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Browser, Page


class ScreenshotService:
    """Сервис для создания скриншотов HTML страниц"""
    
    def __init__(self, headless: bool = True):
        """
        Инициализация сервиса скриншотов
        
        Args:
            headless: Запускать браузер в headless режиме
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def initialize(self):
        """Инициализация Playwright браузера"""
        if self.browser is None:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
    
    async def close(self):
        """Закрытие браузера"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.playwright = None
    
    async def create_screenshot_from_html(
        self,
        html_content: str,
        width: int = 390,
        height: int = 844,
        output_path: Optional[str] = None,
        wait_time: int = 1000
    ) -> Tuple[str, Tuple[int, int]]:
        """
        Создает скриншот из HTML контента
        
        Args:
            html_content: HTML код страницы
            width: Ширина viewport
            height: Высота viewport
            output_path: Путь для сохранения скриншота (опционально)
            wait_time: Время ожидания перед скриншотом (мс)
            
        Returns:
            Tuple (путь к файлу или base64, размеры изображения)
        """
        if self.browser is None:
            await self.initialize()
        
        page = await self.browser.new_page()
        
        try:
            # Установка размера viewport
            await page.set_viewport_size({"width": width, "height": height})
            
            # Загрузка HTML контента
            await page.set_content(html_content, wait_until="networkidle")
            
            # Ожидание для загрузки всех ресурсов
            await page.wait_for_timeout(wait_time)
            
            # Получение реальных размеров контента
            content_size = await page.evaluate("""() => {
                return {
                    width: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth),
                    height: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight)
                };
            }""")
            
            # Установка размера viewport под контент
            actual_width = max(width, content_size["width"])
            actual_height = max(height, content_size["height"])
            await page.set_viewport_size({"width": actual_width, "height": actual_height})
            
            # Создание скриншота
            if output_path:
                await page.screenshot(path=output_path, full_page=True)
                result = output_path
            else:
                screenshot_bytes = await page.screenshot(full_page=True)
                result = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return result, (actual_width, actual_height)
            
        finally:
            await page.close()
    
    async def create_screenshot_from_file(
        self,
        html_file_path: str,
        width: int = 390,
        height: int = 844,
        output_path: Optional[str] = None
    ) -> Tuple[str, Tuple[int, int]]:
        """
        Создает скриншот из HTML файла
        
        Args:
            html_file_path: Путь к HTML файлу
            width: Ширина viewport
            height: Высота viewport
            output_path: Путь для сохранения скриншота
            
        Returns:
            Tuple (путь к файлу, размеры изображения)
        """
        html_path = Path(html_file_path)
        if not html_path.exists():
            raise FileNotFoundError(f"HTML file not found: {html_file_path}")
        
        html_content = html_path.read_text(encoding='utf-8')
        return await self.create_screenshot_from_html(
            html_content, width, height, output_path
        )
    
    async def create_screenshot_sync(
        self,
        html_content: str,
        width: int = 390,
        height: int = 844,
        output_path: Optional[str] = None
    ) -> Tuple[str, Tuple[int, int]]:
        """
        Синхронная обертка для создания скриншота (используется как async)
        
        Args:
            html_content: HTML код страницы
            width: Ширина viewport
            height: Высота viewport
            output_path: Путь для сохранения скриншота
            
        Returns:
            Tuple (путь к файлу или base64, размеры изображения)
        """
        return await self.create_screenshot_from_html(html_content, width, height, output_path)

