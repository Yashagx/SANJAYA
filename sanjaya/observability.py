# Observability Module - Logging and Tracing Infrastructure
# Implements: Loki, Grafana, Kibana, Request Tracing, Async Job Monitoring

import logging
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pythonjsonlogger import jsonlogger
import os

# ────────────────────────────────────────────────────────────
# Request Tracing (Distributed Tracing)
# ────────────────────────────────────────────────────────────
class RequestTracer:
    """Traces requests across all microservices."""
    
    def __init__(self):
        self.trace_id = None
        self.span_id = None
    
    @staticmethod
    def generate_trace_id() -> str:
        """Generate unique trace ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_span_id() -> str:
        """Generate unique span ID."""
        return str(uuid.uuid4())[:12]
    
    def start_trace(self) -> Dict[str, str]:
        """Start a new trace."""
        self.trace_id = self.generate_trace_id()
        self.span_id = self.generate_span_id()
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }
    
    def get_trace_context(self) -> Dict[str, str]:
        """Get current trace context."""
        return {
            "trace_id": self.trace_id or self.generate_trace_id(),
            "span_id": self.span_id or self.generate_span_id(),
        }

# ────────────────────────────────────────────────────────────
# JSON Logging Configuration
# ────────────────────────────────────────────────────────────
def setup_json_logging(service_name: str, output_path: str = "logs"):
    """Configure JSON logging for Loki/ELK integration."""
    
    os.makedirs(output_path, exist_ok=True)
    
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)
    
    # File handler with JSON formatter
    file_handler = logging.FileHandler(f"{output_path}/{service_name}.json")
    json_formatter = jsonlogger.JsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s %(trace_id)s %(span_id)s"
    )
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    # Console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    return logger

# ────────────────────────────────────────────────────────────
# Structured Logging
# ────────────────────────────────────────────────────────────
class StructuredLogger:
    """Provides structured logging with context."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context = {}
    
    def add_context(self, **kwargs):
        """Add context fields to all logs."""
        self.context.update(kwargs)
    
    def log_event(self, event: str, level: str = "INFO", **fields):
        """Log structured event."""
        log_data = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            **self.context,
            **fields,
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_data))

# ────────────────────────────────────────────────────────────
# Async Job Monitoring
# ────────────────────────────────────────────────────────────
class AsyncJobMonitor:
    """Monitors async job execution across workers."""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.jobs = {}
    
    def start_job(self, job_id: str, job_type: str, **metadata):
        """Log job start."""
        self.jobs[job_id] = {
            "status": "started",
            "type": job_type,
            "start_time": datetime.utcnow(),
            "metadata": metadata,
        }
        self.logger.log_event(
            "async_job_started",
            job_id=job_id,
            job_type=job_type,
            **metadata,
        )
    
    def complete_job(self, job_id: str, result: Optional[Any] = None):
        """Log job completion."""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            duration = (datetime.utcnow() - job["start_time"]).total_seconds()
            self.logger.log_event(
                "async_job_completed",
                job_id=job_id,
                duration_seconds=duration,
                result=str(result)[:100],  # Truncate for logging
            )
    
    def fail_job(self, job_id: str, error: str):
        """Log job failure."""
        self.logger.log_event(
            "async_job_failed",
            level="ERROR",
            job_id=job_id,
            error=error,
        )

# ────────────────────────────────────────────────────────────
# Performance Metrics
# ────────────────────────────────────────────────────────────
class MetricsCollector:
    """Collects metrics for Prometheus/Grafana."""
    
    def __init__(self):
        self.metrics = {}
    
    def record_request_latency(self, endpoint: str, method: str, duration_ms: float):
        """Record request latency."""
        key = f"{method}_{endpoint}"
        if key not in self.metrics:
            self.metrics[key] = {"count": 0, "total_duration": 0, "max_duration": 0}
        
        self.metrics[key]["count"] += 1
        self.metrics[key]["total_duration"] += duration_ms
        self.metrics[key]["max_duration"] = max(self.metrics[key]["max_duration"], duration_ms)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return self.metrics

print("[OBSERVABILITY] Observability module initialized with JSON logging, request tracing, and metrics collection")
