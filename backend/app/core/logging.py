import logging
import sys
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        else:
            try:
                from backend.app.core.telemetry import request_id_ctx
                ctx_id = request_id_ctx.get()
                if ctx_id:
                    log_entry["request_id"] = ctx_id
            except Exception:
                pass
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def setup_logging(debug: bool = False):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    
    level = logging.DEBUG if debug else logging.INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Avoid duplicate handlers
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

logger = logging.getLogger("nexora.backend")
