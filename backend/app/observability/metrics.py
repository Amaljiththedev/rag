import time
from typing import Dict, Any

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "total_queries": 0,
            "total_tokens_used": 0,
            "average_latency_ms": 0.0,
            "retrieval_hits": 0
        }

    def record_query(self, latency_ms: float, tokens: int, hit: bool):
        self.metrics["total_queries"] += 1
        self.metrics["total_tokens_used"] += tokens
        if hit:
            self.metrics["retrieval_hits"] += 1

metrics_collector = MetricsCollector()
