"""
Сервис для деплоя готовых сайтов
"""

import hashlib
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import json


class DeployService:
    """Сервис для деплоя готовых сайтов"""
    
    def __init__(self, sites_dir: str = "/app/data/sites"):
        """
        Инициализация сервиса деплоя
        
        Args:
            sites_dir: Директория для хранения деплоенных сайтов
        """
        self.sites_dir = Path(sites_dir)
        self.sites_dir.mkdir(parents=True, exist_ok=True)
    
    def deploy_site(
        self,
        pages: List[Dict[str, str]],
        site_metadata: Optional[Dict] = None
    ) -> str:
        """
        Деплоит сайт из списка страниц
        
        Args:
            pages: Список словарей с ключами page_id и html
            site_metadata: Метаданные сайта (опционально)
            
        Returns:
            Хеш сайта (используется в URL)
        """
        # Генерируем уникальный хеш на основе содержимого страниц
        content_hash = self._generate_site_hash(pages)
        site_path = self.sites_dir / content_hash
        
        # Создаем директорию для сайта
        site_path.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем каждую страницу
        for page in pages:
            page_id = page.get("page_id", "page_1")
            html_content = page.get("html", "")
            
            # Сохраняем HTML файл
            page_file = site_path / f"{page_id}.html"
            page_file.write_text(html_content, encoding='utf-8')
        
        # Создаем index.html (первая страница или главная)
        index_html = pages[0].get("html", "") if pages else ""
        index_file = site_path / "index.html"
        index_file.write_text(index_html, encoding='utf-8')
        
        # Сохраняем метаданные
        if site_metadata:
            metadata_file = site_path / "metadata.json"
            metadata_file.write_text(
                json.dumps(site_metadata, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
        
        # Сохраняем список страниц
        pages_info = [{"page_id": p.get("page_id"), "file": f"{p.get('page_id')}.html"} for p in pages]
        pages_file = site_path / "pages.json"
        pages_file.write_text(
            json.dumps(pages_info, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        return content_hash
    
    def get_site_path(self, site_hash: str) -> Optional[Path]:
        """
        Получает путь к деплоенному сайту
        
        Args:
            site_hash: Хеш сайта
            
        Returns:
            Path к директории сайта или None если не найден
        """
        site_path = self.sites_dir / site_hash
        if site_path.exists() and site_path.is_dir():
            return site_path
        return None
    
    def get_site_page(self, site_hash: str, page_id: str = "index") -> Optional[str]:
        """
        Получает HTML код страницы сайта
        
        Args:
            site_hash: Хеш сайта
            page_id: ID страницы или "index" для главной
            
        Returns:
            HTML код страницы или None если не найдена
        """
        site_path = self.get_site_path(site_hash)
        if not site_path:
            return None
        
        if page_id == "index":
            page_file = site_path / "index.html"
        else:
            page_file = site_path / f"{page_id}.html"
        
        if page_file.exists():
            return page_file.read_text(encoding='utf-8')
        
        return None
    
    def list_sites(self) -> List[Dict]:
        """
        Возвращает список всех деплоенных сайтов
        
        Returns:
            Список словарей с информацией о сайтах
        """
        sites = []
        for site_dir in self.sites_dir.iterdir():
            if site_dir.is_dir():
                metadata_file = site_dir / "metadata.json"
                metadata = {}
                if metadata_file.exists():
                    try:
                        metadata = json.loads(metadata_file.read_text(encoding='utf-8'))
                    except:
                        pass
                
                sites.append({
                    "site_hash": site_dir.name,
                    "metadata": metadata,
                    "path": str(site_dir)
                })
        
        return sites
    
    def delete_site(self, site_hash: str) -> bool:
        """
        Удаляет деплоенный сайт
        
        Args:
            site_hash: Хеш сайта
            
        Returns:
            True если удален успешно, False если не найден
        """
        site_path = self.get_site_path(site_hash)
        if site_path:
            shutil.rmtree(site_path)
            return True
        return False
    
    def _generate_site_hash(self, pages: List[Dict[str, str]]) -> str:
        """
        Генерирует уникальный хеш для сайта на основе содержимого страниц
        
        Args:
            pages: Список страниц
            
        Returns:
            SHA256 хеш (первые 16 символов)
        """
        # Создаем строку из содержимого всех страниц
        content = ""
        for page in sorted(pages, key=lambda x: x.get("page_id", "")):
            content += page.get("html", "")
        
        # Генерируем хеш
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return hash_obj.hexdigest()[:16]

