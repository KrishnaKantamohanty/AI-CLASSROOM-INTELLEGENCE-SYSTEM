"""Detection Service — YOLOv8 student detection with simulation fallback.

When USE_SIMULATION is True, generates realistic mock detection data.
When False, uses the real YOLO model for inference on camera frames.
"""
import random
import time
import math


class DetectionService:
    """Handles student detection in classroom frames."""

    def __init__(self, use_simulation=True, model_path=None, confidence=0.5):
        self.use_simulation = use_simulation
        self.confidence_threshold = confidence
        self.model = None
        self._last_count = 42
        self._base_time = time.time()
        self._simulated_detections = []
        self._last_sim_update = 0

        if not use_simulation and model_path:
            try:
                from ultralytics import YOLO
                self.model = YOLO(model_path)
            except ImportError:
                print('[DetectionService] ultralytics not installed. Falling back to simulation.')
                self.use_simulation = True

    def detect_students(self, frame=None):
        """Detect students in a frame. Returns detection results dict."""
        if self.use_simulation:
            return self._simulate_detection()
        return self._real_detection(frame)

    def _simulate_detection(self):
        """Generate realistic simulated detection data with stable drifting boxes."""
        now = time.time()
        # Update student count and base positions every 2 seconds
        if not self._simulated_detections or now - self._last_sim_update > 2.0:
            elapsed = now - self._base_time
            base = 42 + 8 * math.sin(elapsed / 120)  # oscillate between 34-50
            noise = random.gauss(0, 2)
            count = max(5, min(58, int(base + noise)))
            self._last_count = count

            detections = []
            for i in range(count):
                x = random.randint(20, 580)
                y = random.randint(20, 380)
                w = random.randint(30, 60)
                h = random.randint(40, 80)
                conf = round(random.uniform(0.75, 0.99), 3)
                detections.append({
                    'id': i,
                    'bbox': [x, y, x + w, y + h],
                    'confidence': conf,
                    'class': 'person'
                })
            self._simulated_detections = detections
            self._last_sim_update = now
        else:
            # Let the boxes drift slightly to simulate subtle movements
            for det in self._simulated_detections:
                x1, y1, x2, y2 = det['bbox']
                dx = random.randint(-1, 1)
                dy = random.randint(-1, 1)
                w = x2 - x1
                h = y2 - y1
                x1 = max(10, min(x1 + dx, 590))
                y1 = max(10, min(y1 + dy, 390))
                det['bbox'] = [x1, y1, x1 + w, y1 + h]
                det['confidence'] = max(0.5, min(0.99, round(det['confidence'] + random.uniform(-0.005, 0.005), 3)))

        avg_conf = sum(d['confidence'] for d in self._simulated_detections) / len(self._simulated_detections) if self._simulated_detections else 0

        return {
            'student_count': len(self._simulated_detections),
            'detections': self._simulated_detections,
            'average_confidence': round(avg_conf * 100, 1),
            'detection_time_ms': round(random.uniform(15, 30), 1),
            'timestamp': now,
            'mode': 'simulation'
        }

    def _real_detection(self, frame):
        """Run YOLO inference on a real camera frame."""
        if self.model is None or frame is None:
            return self._simulate_detection()

        results = self.model(frame, conf=self.confidence_threshold, classes=[0], verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                detections.append({
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': round(conf, 3),
                    'class': 'person'
                })

        count = len(detections)
        avg_conf = sum(d['confidence'] for d in detections) / count if count > 0 else 0

        return {
            'student_count': count,
            'detections': detections,
            'average_confidence': round(avg_conf * 100, 1),
            'detection_time_ms': 0,
            'timestamp': time.time(),
            'mode': 'yolov8'
        }

    def get_live_stats(self):
        """Get current detection statistics for the dashboard."""
        result = self.detect_students()
        peak = max(self._last_count, result['student_count']) + random.randint(0, 5)
        lowest = max(5, min(self._last_count, result['student_count']) - random.randint(0, 8))
        return {
            'current_count': result['student_count'],
            'peak_occupancy': min(60, peak),
            'lowest_occupancy': lowest,
            'average_confidence': result['average_confidence'],
            'detection_mode': result['mode']
        }


# Module-level singleton
_service_instance = None


def get_detection_service(app=None):
    """Get or create the detection service singleton."""
    global _service_instance
    if _service_instance is None:
        use_sim = True
        model_path = None
        confidence = 0.5
        if app:
            use_sim = app.config.get('USE_SIMULATION', True)
            model_path = app.config.get('YOLO_MODEL_PATH')
            confidence = app.config.get('DETECTION_CONFIDENCE', 0.5)
        _service_instance = DetectionService(use_sim, model_path, confidence)
    return _service_instance
