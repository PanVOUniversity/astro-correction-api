"""
Утилиты для парсинга и обработки HTML кода
"""

import re
from typing import List, Dict, Tuple, Optional
from bs4 import BeautifulSoup


def extract_blocks(html: str) -> List[Dict[str, any]]:
    """
    Извлекает блоки из HTML кода
    
    Args:
        html: HTML код страницы
        
    Returns:
        Список словарей с информацией о блоках
    """
    soup = BeautifulSoup(html, 'html.parser')
    blocks = []
    
    # Ищем все элементы с классом 'block'
    block_elements = soup.find_all(class_=re.compile(r'\bblock\b'))
    
    for idx, block in enumerate(block_elements):
        style = block.get('style', '')
        style_dict = parse_style(style)
        
        blocks.append({
            'id': idx,
            'element': str(block),
            'style': style,
            'position': {
                'top': style_dict.get('top', '0vh'),
                'left': style_dict.get('left', '0vw'),
                'width': style_dict.get('width', '0vw'),
                'height': style_dict.get('height', '0vh'),
            },
            'z_index': style_dict.get('z-index', '0'),
        })
    
    return blocks


def parse_style(style_str: str) -> Dict[str, str]:
    """
    Парсит строку стиля в словарь
    
    Args:
        style_str: Строка стиля CSS
        
    Returns:
        Словарь с парами ключ-значение
    """
    style_dict = {}
    if not style_str:
        return style_dict
    
    # Разбиваем по точкам с запятой
    styles = style_str.split(';')
    for style in styles:
        style = style.strip()
        if ':' in style:
            key, value = style.split(':', 1)
            key = key.strip()
            value = value.strip()
            style_dict[key] = value
    
    return style_dict


def update_block_coordinates(
    html: str,
    block_updates: List[Dict[str, any]]
) -> str:
    """
    Обновляет координаты блоков в HTML
    
    Args:
        html: Исходный HTML код
        block_updates: Список обновлений для блоков
        
    Returns:
        Обновленный HTML код
    """
    soup = BeautifulSoup(html, 'html.parser')
    block_elements = soup.find_all(class_=re.compile(r'\bblock\b'))
    
    for idx, block in enumerate(block_elements):
        if idx < len(block_updates):
            update = block_updates[idx]
            style_dict = parse_style(block.get('style', ''))
            
            # Обновляем координаты
            if 'top' in update:
                style_dict['top'] = update['top']
            if 'left' in update:
                style_dict['left'] = update['left']
            if 'width' in update:
                style_dict['width'] = update['width']
            if 'height' in update:
                style_dict['height'] = update['height']
            
            # Формируем новую строку стиля
            style_parts = []
            for key, value in style_dict.items():
                style_parts.append(f"{key}:{value}")
            
            block['style'] = ';'.join(style_parts)
    
    return str(soup)


def convert_pixels_to_viewport(
    x: float,
    y: float,
    width: float,
    height: float,
    img_width: int,
    img_height: int
) -> Dict[str, str]:
    """
    Конвертирует координаты из пикселей в viewport единицы (vw/vh)
    
    Args:
        x: X координата в пикселях
        y: Y координата в пикселях
        width: Ширина в пикселях
        height: Высота в пикселях
        img_width: Ширина изображения в пикселях
        img_height: Высота изображения в пикселях
        
    Returns:
        Словарь с координатами в vw/vh
    """
    left_vw = (x / img_width) * 100
    top_vh = (y / img_height) * 100
    width_vw = (width / img_width) * 100
    height_vh = (height / img_height) * 100
    
    return {
        'left': f"{left_vw:.1f}vw",
        'top': f"{top_vh:.1f}vh",
        'width': f"{width_vw:.1f}vw",
        'height': f"{height_vh:.1f}vh",
    }
