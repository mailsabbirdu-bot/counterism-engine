import cv2
import numpy as np
from typing import List, Optional
try:
    from .schema import DetectedObject, BBox
except ImportError:
    from schema import DetectedObject, BBox

class BaseDetector:
    def detect(self, frame: np.ndarray) -> List[DetectedObject]:
        raise NotImplementedError

class YOLODetector(BaseDetector):
    def __init__(self, model_path: str = "yolov8n.pt"):
        try:
            from ultralytics import YOLO
            self.model = YOLO(model_path)
            self.available = True
        except ImportError:
            print("⚠️ ultralytics not installed. YOLODetector unavailable.")
            self.available = False
        except Exception as e:
            print(f"⚠️ Error loading YOLO model: {e}")
            self.available = False

    def detect(self, frame: np.ndarray) -> List[DetectedObject]:
        if not self.available:
            return []

        try:
            results = self.model(frame, verbose=False)
            detections = []
            for i, r in enumerate(results):
                boxes = r.boxes
                for box in boxes:
                    # Get box coordinates (x1, y1, x2, y2)
                    b = box.xyxy[0].cpu().numpy()
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    label = self.model.names[cls]

                    detections.append(DetectedObject(
                        id=f"{label}_{i}_{len(detections)}",
                        type=label,
                        confidence=conf,
                        bbox=BBox(
                            x=float(b[0]),
                            y=float(b[1]),
                            width=float(b[2] - b[0]),
                            height=float(b[3] - b[1])
                        )
                    ))
            return detections
        except Exception as e:
            print(f"⚠️ YOLO detection error: {e}")
            return []

class MockDetector(BaseDetector):
    def detect(self, frame: np.ndarray) -> List[DetectedObject]:
        # Legacy fallback or for testing
        return [
            DetectedObject(
                id="mock_001",
                type="building",
                confidence=0.95,
                bbox=BBox(x=100, y=100, width=200, height=300)
            )
        ]

# Global detector instance
_detector: Optional[BaseDetector] = None

def get_detector() -> BaseDetector:
    global _detector
    if _detector is None:
        yolo = YOLODetector()
        if yolo.available:
            _detector = yolo
        else:
            _detector = MockDetector()
    return _detector

def detect_objects(frame: np.ndarray) -> List[DetectedObject]:
    """
    Real object detection using YOLO (if available) or Mock fallback.
    """
    try:
        detector = get_detector()
        return detector.detect(frame)
    except Exception:
        return []

def classify_scene(frame: np.ndarray, objects: List[DetectedObject]) -> str:
    """
    Infers scene category from detected objects and visual context.
    COCO mapped categories for YOLOv8:
    - person, bicycle, car, motorcycle, airplane, bus, train, truck, boat, traffic light,
      fire hydrant, stop sign, parking meter, bench, bird, cat, dog, horse, sheep, cow,
      elephant, bear, zebra, giraffe, backpack, umbrella, handbag, tie, suitcase, frisbee,
      skis, snowboard, sports ball, kite, baseball bat, baseball glove, skateboard,
      surfboard, tennis racket, bottle, wine glass, cup, fork, knife, spoon, bowl,
      banana, apple, sandwich, orange, broccoli, carrot, hot dog, pizza, donut, cake,
      chair, couch, potted plant, bed, dining table, toilet, tv, laptop, mouse, remote,
      keyboard, cell phone, microwave, oven, toaster, sink, refrigerator, book, clock,
      vase, scissors, teddy bear, hair drier, toothbrush
    """
    try:
        counts = {}
        for obj in objects:
            counts[obj.type] = counts.get(obj.type, 0) + 1

        # Decision logic based on COCO object counts
        # Vehicle clusters often mean highways or cities
        vehicle_count = counts.get('car', 0) + counts.get('truck', 0) + counts.get('bus', 0)

        if vehicle_count > 5:
            return "highway"

        if counts.get('person', 0) > 3 and counts.get('chair', 0) > 0:
            return "interior" # Could be office or cafe

        if counts.get('potted plant', 0) > 2 and counts.get('dining table', 0) > 0:
            return "interior"

        if counts.get('boat', 0) > 0:
            return "river" # or coast

        if counts.get('airplane', 0) > 0:
            return "aerial_city" # often seen in aerial shots

        # Default fallback logic
        h, w = frame.shape[:2]
        roi = frame[0:h//3, :] # Top third for sky/context
        avg_color = np.mean(roi, axis=(0, 1))

        # Bright blue sky detection
        if avg_color[0] > 150 and avg_color[1] > 100:
             return "day_city"

        return "urban_city"
    except Exception:
        return "unknown"
