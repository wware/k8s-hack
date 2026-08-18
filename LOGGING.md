# Logging & Observability Guide

This document covers logging, log aggregation, and observability for the K8s Toy API, with patterns applicable to production Kubernetes deployments.

## Current State

The application implements **structured JSON logging** with request correlation:
- All logs output as JSON to stdout (captured by Kubernetes)
- Request IDs automatically generated and included in all logs
- Request IDs returned in `X-Request-ID` response headers for client correlation
- Pod name automatically included from `HOSTNAME` environment variable
- Logs include context (item_id, operation type, error details, etc.)

Check `app.py` for the full implementation:
- `JSONFormatter` - Custom logging formatter
- `RequestIDMiddleware` - Request ID injection
- All endpoints instrumented with structured logging

## The Three Pillars of Observability

Modern observability requires three complementary data types:

### 1. Logs - Discrete Events
Individual events with context (requests, errors, state changes).

**Format:** Structured JSON logs (not plain text)
```json
{"timestamp": "2026-08-18T10:15:30Z", "level": "error", "message": "database timeout", "request_id": "abc-123"}
```

**Storage & Query Tools:**
- **EFK Stack**: Elasticsearch (storage) + Fluentd (collection) + Kibana (UI)
- **Loki + Grafana**: Lighter alternative, better for Kubernetes (recommended)
- **Managed**: CloudWatch, Datadog, Splunk, New Relic

### 2. Metrics - Aggregated Measurements
Time-series data showing trends (request rate, latency percentiles, error rate).

**Format:** Numeric measurements with labels
```
http_requests_total{method="GET", status="200"} 1234
http_request_duration_seconds{quantile="0.99"} 0.045
```

**Tools:**
- **Prometheus**: Industry standard for Kubernetes (already integrated in this project)
- **Grafana**: Visualization dashboards
- **Managed**: CloudWatch, Datadog, New Relic

### 3. Traces - Request Flow
Follow a single request through multiple services, showing the full call graph.

**Format:** Spans forming a trace tree
```
Trace abc-123: API → Database → Cache → External API (250ms total)
```

**Tools:**
- **OpenTelemetry**: Instrumentation standard (vendor-neutral)
- **Jaeger**: Open-source trace storage and UI
- **Tempo**: Grafana's tracing backend (works with Loki)
- **Managed**: AWS X-Ray, Google Cloud Trace, Datadog APM

**The Power of Integration:**
- Logs have `trace_id` → click to see full trace
- Traces link to logs → see detailed errors
- Metrics trigger alerts → investigate with logs and traces

This guide focuses on logs but shows integration points with metrics (Prometheus) and traces (OpenTelemetry).

## Logging Fundamentals

### Structured Logging (JSON)

**Why:** Machine-parseable, searchable, correlatable across services.

**This application already implements structured JSON logging.** Here's what it looks like:

```json
{
  "timestamp": "2026-08-18T10:15:30.123Z",
  "level": "info",
  "message": "request completed",
  "request_id": "abc-123",
  "method": "GET",
  "path": "/api/v1/items",
  "status": 200,
  "service": "toy-api",
  "pod": "toy-api-868959d7cb-9hxsh",
  "item_id": "item1"
}
```

Compare this to traditional plain-text logging (what many apps still use):
```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
```

The JSON format provides:
- Automatic parsing by log aggregation systems
- Easy filtering and search (e.g., find all logs with `request_id="abc-123"`)
- Correlation across services
- Rich context without string parsing

**Implementation Details:**

```python
# app.py additions
import logging
import json
import uuid
from contextvars import ContextVar
from datetime import datetime

# Context variable for request ID (thread-safe for async)
request_id_ctx: ContextVar[str] = ContextVar('request_id', default=None)

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "logger": record.name,
            "service": "toy-api",
        }

        # Add request ID if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)

# Configure logging
def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)

    # Reduce noise from uvicorn access logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# Call during startup
setup_logging()

# Middleware to add request IDs
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(request_id)

        # Add to response headers for client correlation
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

app.add_middleware(RequestIDMiddleware)

# Usage in endpoints
logger = logging.getLogger(__name__)

@app.get("/items/{item_id}")
async def get_item(item_id: str) -> Item:
    logger.info("fetching item", extra={
        'extra_fields': {'item_id': item_id}
    })
    # ... rest of endpoint
```

### Log Levels

Use appropriately:

- **DEBUG** - Detailed diagnostic info (disabled in production)
- **INFO** - Normal operations (requests, state changes)
- **WARNING** - Unexpected but handled (deprecated API usage, slow queries)
- **ERROR** - Errors that were handled (failed validations, caught exceptions)
- **CRITICAL** - Service-level failures (can't connect to database)

## Kubernetes Logging Patterns

### Pattern 1: Node-level logging (Current approach)

**How it works:**
- Apps write to stdout/stderr
- Container runtime captures output
- Logs stored at `/var/log/containers/` on the node
- `kubectl logs` reads from there

**Viewing logs:**
```bash
# Single pod
kubectl logs toy-api-868959d7cb-9hxsh

# All pods in deployment
kubectl logs -l app=toy-api

# Follow logs
kubectl logs -f toy-api-868959d7cb-9hxsh

# Previous container (after crash)
kubectl logs toy-api-868959d7cb-9hxsh --previous

# Tail last 50 lines
kubectl logs toy-api-868959d7cb-9hxsh --tail=50

# Since timestamp
kubectl logs toy-api-868959d7cb-9hxsh --since=1h

# Multiple containers in a pod
kubectl logs toy-api-868959d7cb-9hxsh -c api
```

**Limitations:**
- Logs lost when pod is deleted
- Hard to correlate across services
- No long-term retention
- Manual searching across multiple pods

### Pattern 2: Cluster-level logging (Production approach)

Ship logs to a central aggregation system.

**Popular stacks:**

#### EFK Stack (Elasticsearch, Fluentd, Kibana)

```
Application → stdout → Fluentd (DaemonSet) → Elasticsearch → Kibana (UI)
```

**Fluentd DaemonSet** runs on every node and:
1. Reads `/var/log/containers/*.log`
2. Parses JSON logs
3. Adds Kubernetes metadata (pod, namespace, labels)
4. Ships to Elasticsearch

**Deployment:**
```bash
# Using helm
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluent-bit fluent/fluent-bit \
  --set backend.type=es \
  --set backend.es.host=elasticsearch \
  --set backend.es.port=9200
```

**Query in Kibana:**
```
service:"toy-api" AND request_id:"abc-123" AND level:"error"
```

#### Loki Stack (Grafana Loki + Promtail)

**Lighter alternative to EFK** - doesn't index log contents, only metadata.

```
Application → stdout → Promtail (DaemonSet) → Loki → Grafana (UI)
```

**Deployment:**
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --set grafana.enabled=true \
  --set promtail.enabled=true
```

**Query in Grafana:**
```
{app="toy-api"} |= "error" | json | request_id="abc-123"
```

**Advantages over EFK:**
- Lower resource usage
- Simpler to operate
- Better Prometheus integration
- Cost-effective for large volumes

#### Managed Solutions

Cloud providers offer managed logging:

- **AWS CloudWatch Logs** + Fluent Bit
- **GCP Cloud Logging** (formerly Stackdriver)
- **Azure Monitor**
- **Datadog**, **New Relic**, **Splunk**

### Pattern 3: Sidecar logging

For apps that can't log to stdout or need special processing:

```yaml
# deployment.yaml
spec:
  containers:
    - name: api
      image: k8s-toy-api:local
      volumeMounts:
        - name: logs
          mountPath: /var/log/app

    - name: log-shipper
      image: fluent/fluent-bit:latest
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true

  volumes:
    - name: logs
      emptyDir: {}
```

## Correlation: Tracing Requests Across Services

### Request IDs

Every request gets a unique ID that flows through all services.

**Client sends:**
```
GET /api/v1/items
X-Request-ID: abc-123-def-456
```

**Service A logs:**
```json
{"request_id": "abc-123-def-456", "service": "toy-api", "message": "processing request"}
```

**Service A calls Service B:**
```
GET http://item-enrichment/enrich
X-Request-ID: abc-123-def-456
```

**Service B logs:**
```json
{"request_id": "abc-123-def-456", "service": "enrichment", "message": "enriching item"}
```

**Now you can query:** `request_id:"abc-123-def-456"` and see the full journey.

### Distributed Tracing (Advanced)

For complex microservices, use **OpenTelemetry** (successor to OpenTracing).

**How it works:**
- Traces have a trace ID (whole request path)
- Each service creates spans (individual operations)
- Spans reference parent spans
- Creates a tree of operations

**Popular backends:**
- **Jaeger** (open source, CNCF project)
- **Tempo** (Grafana, works with Loki)
- **AWS X-Ray**
- **Google Cloud Trace**

**Example with OpenTelemetry:**

```python
# Install: pip install opentelemetry-api opentelemetry-sdk \
#          opentelemetry-instrumentation-fastapi \
#          opentelemetry-exporter-jaeger

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Manual spans for custom operations
tracer = trace.get_tracer(__name__)

@app.get("/items/{item_id}")
async def get_item(item_id: str) -> Item:
    with tracer.start_as_current_span("database.query") as span:
        span.set_attribute("item.id", item_id)
        # database query here
        item = await fetch_from_db(item_id)

    with tracer.start_as_current_span("external.enrich"):
        # call enrichment service
        enriched = await enrich_item(item)

    return enriched
```

**Jaeger UI shows:**
```
Trace: abc-123 (250ms)
├─ GET /items/item1 (250ms) [toy-api]
   ├─ database.query (45ms) [toy-api]
   └─ external.enrich (200ms) [toy-api]
      └─ GET /enrich (180ms) [enrichment-service]
         └─ ml.predict (150ms) [enrichment-service]
```

## Correlation Fields

Always log these for correlation:

```python
{
    # Identify the request
    "request_id": "abc-123",          # Unique per request
    "trace_id": "def-456",            # For distributed tracing
    "span_id": "ghi-789",

    # Identify the service
    "service": "toy-api",
    "version": "1.2.3",
    "pod": "toy-api-868959d7cb-9hxsh",
    "node": "node-1",
    "namespace": "production",

    # Request context
    "method": "GET",
    "path": "/api/v1/items/item1",
    "user_id": "user-42",             # If authenticated
    "tenant_id": "tenant-5",          # For multi-tenant

    # Operation details
    "operation": "fetch_item",
    "item_id": "item1",
    "duration_ms": 45.2,

    # Error context (if error)
    "error_code": "ITEM_NOT_FOUND",
    "error_category": "client_error"
}
```

## Log Retention & Cost Management

**Strategies:**

1. **Hot/Warm/Cold storage**
   - Hot (last 7 days): Full-text search, fast queries
   - Warm (8-90 days): Compressed, slower queries
   - Cold (90+ days): Archive to S3, query via Athena

2. **Log levels by environment**
   ```python
   LOG_LEVEL = {
       "production": "INFO",
       "staging": "DEBUG",
       "development": "DEBUG"
   }[env]
   ```

3. **Sampling for high-volume services**
   ```python
   # Only log 10% of successful requests
   if response.status == 200 and random.random() > 0.1:
       return  # Skip logging

   # Always log errors
   if response.status >= 400:
       logger.error(...)
   ```

4. **Drop noisy logs at collection**
   ```yaml
   # Fluentd config
   <filter kubernetes.**>
     @type grep
     <exclude>
       key log
       pattern /healthz/
     </exclude>
   </filter>
   ```

## Alerts from Logs

Combine logs with metrics for alerting:

**Example: Alert on error rate**

```yaml
# Prometheus rule
- alert: HighErrorRate
  expr: |
    sum(rate(log_messages_total{level="error"}[5m])) by (service)
    /
    sum(rate(log_messages_total[5m])) by (service)
    > 0.05
  for: 5m
  annotations:
    summary: "{{ $labels.service }} error rate > 5%"
```

**Example: Alert on specific errors**

```yaml
- alert: DatabaseConnectionFailed
  expr: |
    increase(log_messages_total{
      level="error",
      message=~".*database connection failed.*"
    }[5m]) > 0
  annotations:
    summary: "Database connection errors detected"
```

## Implementation Checklist

For production logging:

- [ ] Switch to structured (JSON) logging
- [ ] Add request ID middleware
- [ ] Include correlation fields (service, pod, namespace)
- [ ] Set appropriate log levels per environment
- [ ] Deploy log aggregation (EFK or Loki stack)
- [ ] Configure log retention policies
- [ ] Set up dashboards in Kibana/Grafana
- [ ] Create alerts for critical errors
- [ ] Add distributed tracing (OpenTelemetry + Jaeger/Tempo)
- [ ] Document log query patterns for common issues
- [ ] Test log correlation across service boundaries
- [ ] Implement log sampling for high-traffic endpoints
- [ ] Set up log cost monitoring and budgets

## Quick Start: Adding Loki to This Project

```bash
# Install Loki stack
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --set grafana.enabled=true \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=10Gi

# Get Grafana password
kubectl get secret loki-grafana -o jsonpath="{.data.admin-password}" | base64 -d

# Port forward Grafana
kubectl port-forward svc/loki-grafana 3000:80

# Open http://localhost:3000 (admin / <password>)
# Add Loki data source: http://loki:3100
# Query: {app="toy-api"} | json
```

## Further Reading

- [Kubernetes Logging Architecture](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
- [12-Factor App: Logs](https://12factor.net/logs)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Elasticsearch Guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Structured Logging Best Practices](https://www.loggly.com/ultimate-guide/python-logging-basics/)
