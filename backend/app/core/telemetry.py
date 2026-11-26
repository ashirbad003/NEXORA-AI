import time
from collections import defaultdict
from typing import Dict, Any, List
from contextvars import ContextVar

# ContextVar for propagating correlation request ID across async tasks
request_id_ctx: ContextVar[str] = ContextVar("request_id_ctx", default="")

class MetricsCollector:
    """
    Privacy-preserving in-memory operational metrics collector.
    Aggregates request counts, latency metrics, error distributions, and auth telemetry.
    Never stores IP addresses, usernames, passwords, or personal data.
    """
    def __init__(self):
        self.request_count = 0
        self.total_process_time_ms = 0.0
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.route_counts: Dict[str, int] = defaultdict(int)
        self.auth_failures = 0
        self.rate_limit_hits = 0
        self.sync_operations = 0
        self.sandbox_executions = 0

    def record_request(self, method: str, path: str, status_code: int, process_time_ms: float):
        self.request_count += 1
        self.total_process_time_ms += process_time_ms
        self.status_codes[status_code] += 1
        # Normalize parameterized routes (e.g. /api/v1/auth/login)
        route_prefix = "/".join(path.split("/")[:4])
        route_key = f"{method} {route_prefix}"
        if len(self.route_counts) < 500 or route_key in self.route_counts:
            self.route_counts[route_key] += 1
        else:
            self.route_counts["OTHER_ROUTES"] += 1

        if status_code == 401 or status_code == 403:
            self.auth_failures += 1
        elif status_code == 429:
            self.rate_limit_hits += 1

    def record_sync(self, count: int = 1):
        self.sync_operations += count

    def record_sandbox_execution(self):
        self.sandbox_executions += 1

    def get_summary(self) -> Dict[str, Any]:
        avg_latency = (
            round(self.total_process_time_ms / self.request_count, 2)
            if self.request_count > 0
            else 0.0
        )
        return {
            "total_requests": self.request_count,
            "average_latency_ms": avg_latency,
            "status_distribution": dict(self.status_codes),
            "route_distribution": dict(self.route_counts),
            "auth_failures": self.auth_failures,
            "rate_limit_exceeded_count": self.rate_limit_hits,
            "sync_operations_total": self.sync_operations,
            "sandbox_executions_total": self.sandbox_executions
        }

metrics = MetricsCollector()
