"""
Сервис для выполнения детекции объектов с помощью Detectron2
"""

import warnings
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.data.detection_utils import read_image
from detectron2.engine import DefaultPredictor
from detectron2.utils.visualizer import Visualizer, ColorMode


class InferenceService:
    """Сервис для выполнения инференса на изображениях"""
    
    def __init__(
        self,
        model_path: str,
        config_path: str,
        num_classes: int = 1,
        thing_classes: List[str] = None,
        confidence_threshold: float = 0.5,
        device: Optional[str] = None
    ):
        """
        Инициализация сервиса инференса
        
        Args:
            model_path: Путь к обученной модели
            config_path: Путь к конфигурационному файлу
            num_classes: Количество классов
            thing_classes: Список имен классов
            confidence_threshold: Порог уверенности
            device: Устройство (cpu/cuda) или None для автоопределения
        """
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self.num_classes = num_classes
        self.thing_classes = thing_classes or ["frame"]
        self.confidence_threshold = confidence_threshold
        
        # Настройка конфигурации
        self.cfg = self._setup_cfg(device)
        
        # Создание предиктора
        self.predictor = DefaultPredictor(self.cfg)
        
    def _setup_cfg(self, device: Optional[str] = None):
        """Настройка конфигурации Detectron2"""
        cfg = get_cfg()
        cfg.merge_from_file(str(self.config_path))
        cfg.INPUT.MASK_FORMAT = "bitmask"
        
        cfg.MODEL.WEIGHTS = str(self.model_path)
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = self.num_classes
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = self.confidence_threshold
        
        # Установка устройства
        if device:
            cfg.MODEL.DEVICE = device
        else:
            import torch
            if torch.cuda.is_available():
                cfg.MODEL.DEVICE = "cuda"
            else:
                cfg.MODEL.DEVICE = "cpu"
        
        # Установка метаданных
        inference_dataset_name = "__inference__"
        cfg.DATASETS.TEST = (inference_dataset_name,)
        metadata = MetadataCatalog.get(inference_dataset_name)
        try:
            if not hasattr(metadata, 'thing_classes') or not metadata.thing_classes:
                metadata.thing_classes = self.thing_classes
        except (AttributeError, AssertionError):
            pass
        
        cfg.freeze()
        return cfg
    
    def detect_objects(self, image_path: str) -> Dict:
        """
        Выполняет детекцию объектов на изображении
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Словарь с результатами детекции
        """
        # Загрузка изображения
        image = read_image(image_path, format="BGR")
        
        # Выполнение предсказания
        predictions = self.predictor(image)
        instances = predictions["instances"].to("cpu")
        
        num_instances = len(instances)
        
        if num_instances == 0:
            return {
                "total_objects": 0,
                "overlaps": 0,
                "objects": [],
                "image_size": list(instances.image_size) if hasattr(instances, 'image_size') else None
            }
        
        # Извлечение информации об объектах
        boxes = instances.pred_boxes.tensor.numpy()
        scores = instances.scores.numpy()
        masks = instances.pred_masks.numpy()
        
        objects = []
        for i in range(num_instances):
            bbox = boxes[i]
            mask_area = int(masks[i].sum())
            
            objects.append({
                "id": i,
                "score": float(scores[i]),
                "bbox": [float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])],
                "bbox_center": [
                    float((bbox[0] + bbox[2]) / 2),
                    float((bbox[1] + bbox[3]) / 2)
                ],
                "bbox_size": [
                    float(bbox[2] - bbox[0]),
                    float(bbox[3] - bbox[1])
                ],
                "mask_area": mask_area
            })
        
        # Обнаружение перекрытий
        overlaps = self._detect_overlaps(instances)
        
        return {
            "total_objects": num_instances,
            "overlaps": overlaps["total_overlaps"],
            "objects": objects,
            "overlap_details": overlaps.get("overlaps", []),
            "image_size": list(instances.image_size) if hasattr(instances, 'image_size') else None
        }
    
    def _detect_overlaps(self, instances, iou_threshold: float = 0.1) -> Dict:
        """
        Обнаруживает перекрывающиеся объекты
        
        Args:
            instances: Экземпляры детекции
            iou_threshold: Порог IoU для определения перекрытия
            
        Returns:
            Словарь с информацией о перекрытиях
        """
        num_instances = len(instances)
        if num_instances < 2:
            return {
                "total_overlaps": 0,
                "overlaps": []
            }
        
        boxes = instances.pred_boxes.tensor.numpy()
        overlaps = []
        
        for i in range(num_instances):
            for j in range(i + 1, num_instances):
                iou_value = self._calculate_iou(boxes[i], boxes[j])
                if iou_value >= iou_threshold:
                    overlaps.append({
                        "instance1": int(i),
                        "instance2": int(j),
                        "iou": float(iou_value),
                        "score1": float(instances.scores[i]),
                        "score2": float(instances.scores[j])
                    })
        
        return {
            "total_overlaps": len(overlaps),
            "overlaps": overlaps
        }
    
    def _calculate_iou(self, box1: np.ndarray, box2: np.ndarray) -> float:
        """
        Вычисляет IoU для двух bounding boxes
        
        Args:
            box1: Первый bounding box [x1, y1, x2, y2]
            box2: Второй bounding box [x1, y1, x2, y2]
            
        Returns:
            Значение IoU
        """
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2
        
        # Вычисляем координаты пересечения
        inter_x_min = max(x1_min, x2_min)
        inter_y_min = max(y1_min, y2_min)
        inter_x_max = min(x1_max, x2_max)
        inter_y_max = min(y1_max, y2_max)
        
        # Если нет пересечения
        if inter_x_max <= inter_x_min or inter_y_max <= inter_y_min:
            return 0.0
        
        # Площадь пересечения
        inter_area = (inter_x_max - inter_x_min) * (inter_y_max - inter_y_min)
        
        # Площади каждого бокса
        box1_area = (x1_max - x1_min) * (y1_max - y1_min)
        box2_area = (x2_max - x2_min) * (y2_max - y2_min)
        
        # Площадь объединения
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
