import threading
from datetime import datetime


class LiveState:
    def __init__(self):
        self._lock = threading.Lock()
        self.data = {
            "system_status": "ACTIF",
            "mode": "MONITORING",
            "current_time": "--:--:--",
            "pipeline_state": "PRÊT",
            "transcript": "",
            "keywords": [],
            "score_tm": 0.0,
            "score_llm": 0.0,
            "score_final": 0.0,
            "score_tm_percent": 0.0,
            "score_llm_percent": 0.0,
            "score_final_percent": 0.0,
            "alert_label": "NORMAL",
            "led_status": "OFF",
            "urgent_count": 0,
            "logs": [],
            "chart_labels": ["--:--"] * 8,
            "normal_points": "",
            "urgent_points": "",
            "waveform": [12, 18, 14, 22, 30, 24, 18, 28, 36, 30, 24, 40, 48, 36, 28, 22, 18, 22, 26, 20, 18, 16, 14, 12, 16, 20, 18, 14, 12, 10, 9, 8],
        }

    def get(self):
        with self._lock:
            return dict(self.data)

    def update(self, **kwargs):
        with self._lock:
            self.data.update(kwargs)
            self.data["current_time"] = datetime.now().strftime("%H:%M:%S")


live_state = LiveState()