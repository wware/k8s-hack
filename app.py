"""Simple toy API for Kubernetes exercise.

A minimal FastAPI application with health checks, basic CRUD operations,
Prometheus metrics, PostgreSQL database, and structured JSON logging.
"""

import asyncpg
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for request ID (thread-safe for async)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default=None)


class Settings(BaseSettings):
    """Application settings from environment variables."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/toyapi"
    log_level: str = "INFO"
    model_config = SettingsConfigDict(env_prefix="")


settings = Settings()


# JSON Logging Setup
class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "logger": record.name,
            "service": "toy-api",
            "pod": os.getenv("HOSTNAME", "local"),  # Kubernetes sets this to pod name
        }

        # Add request ID if available
        request_id = request_id_ctx.get()
        if request_id:
            log_data["request_id"] = request_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            log_data["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None

        # Add any extra fields passed via extra parameter
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging():
    """Configure structured JSON logging."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Reduce noise from uvicorn access logs (handled by Prometheus metrics)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)


# Request ID Middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request IDs to all requests and responses for correlation."""

    async def dispatch(self, request: Request, call_next):
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_ctx.set(request_id)

        # Log the incoming request
        logger.info(
            "request started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            },
        )

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log the completed request
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
            },
        )

        return response


# Global database connection pool
db_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global db_pool
    logger.info("application starting", extra={"database_url": settings.database_url.split("@")[-1]})

    try:
        # Startup: create database pool and initialize schema
        db_pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
        logger.info("database pool created", extra={"min_size": 2, "max_size": 10})
        await init_db()
        logger.info("application startup complete")
    except Exception as e:
        logger.error("application startup failed", exc_info=True)
        raise

    yield

    # Shutdown: close database pool
    logger.info("application shutting down")
    if db_pool:
        await db_pool.close()
        logger.info("database pool closed")


async def init_db():
    """Initialize database schema if not exists."""
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                value INTEGER NOT NULL
            )
            """
        )
        logger.info("database schema initialized")

        # Insert initial data if table is empty
        count = await conn.fetchval("SELECT COUNT(*) FROM items")
        if count == 0:
            await conn.execute(
                """
                INSERT INTO items (id, name, value) VALUES
                    ('item1', 'First Item', 100),
                    ('item2', 'Second Item', 200)
                """
            )
            logger.info("initial data inserted", extra={"item_count": 2})
        else:
            logger.info("existing data found", extra={"item_count": count})


app = FastAPI(title="K8s Toy API", root_path="/api/v1", lifespan=lifespan)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Custom metrics
item_operations = Counter(
    "item_operations_total", "Item operations by type", ["operation"]
)

logger.info("fastapi application initialized")


class Item(BaseModel):
    model_config = SettingsConfigDict(frozen=True)

    id: str
    name: str
    value: int


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    """Health check endpoint - also checks database connectivity."""
    try:
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error("health check failed", exc_info=True, extra={"component": "database"})
        return {"status": "degraded", "database": f"error: {e}"}


@app.get("/items")
async def list_items() -> list[Item]:
    """List all items."""
    item_operations.labels(operation="list").inc()
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, value FROM items ORDER BY id")
        items = [Item(id=row["id"], name=row["name"], value=row["value"]) for row in rows]
        logger.info("items listed", extra={"count": len(items)})
        return items


@app.get("/items/{item_id}")
async def get_item(item_id: str) -> Item:
    """Get a specific item by ID."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, value FROM items WHERE id = $1", item_id)

        if not row:
            item_operations.labels(operation="get_not_found").inc()
            logger.warning("item not found", extra={"item_id": item_id})
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

        item_operations.labels(operation="get").inc()
        logger.info("item retrieved", extra={"item_id": item_id})
        return Item(id=row["id"], name=row["name"], value=row["value"])


@app.post("/items")
async def create_item(item: Item) -> Item:
    """Create a new item."""
    async with db_pool.acquire() as conn:
        # Check if item already exists
        exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)", item.id)
        if exists:
            item_operations.labels(operation="create_conflict").inc()
            logger.warning("item creation conflict", extra={"item_id": item.id})
            raise HTTPException(status_code=409, detail=f"Item already exists: {item.id}")

        # Insert new item
        await conn.execute(
            "INSERT INTO items (id, name, value) VALUES ($1, $2, $3)",
            item.id,
            item.name,
            item.value,
        )
        item_operations.labels(operation="create").inc()
        logger.info("item created", extra={"item_id": item.id, "name": item.name, "value": item.value})
        return item


@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item) -> Item:
    """Update an existing item."""
    if item.id != item_id:
        logger.warning("item update ID mismatch", extra={"path_id": item_id, "body_id": item.id})
        raise HTTPException(status_code=400, detail="ID mismatch")

    async with db_pool.acquire() as conn:
        # Check if item exists
        exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)", item_id)
        if not exists:
            item_operations.labels(operation="update_not_found").inc()
            logger.warning("item update failed - not found", extra={"item_id": item_id})
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

        # Update item
        await conn.execute(
            "UPDATE items SET name = $1, value = $2 WHERE id = $3",
            item.name,
            item.value,
            item_id,
        )
        item_operations.labels(operation="update").inc()
        logger.info("item updated", extra={"item_id": item_id, "name": item.name, "value": item.value})
        return item


@app.delete("/items/{item_id}")
async def delete_item(item_id: str) -> dict[str, str]:
    """Delete an item."""
    async with db_pool.acquire() as conn:
        # Check if item exists and delete
        result = await conn.execute("DELETE FROM items WHERE id = $1", item_id)

        # result is like "DELETE 1" or "DELETE 0"
        deleted_count = int(result.split()[-1])
        if deleted_count == 0:
            item_operations.labels(operation="delete_not_found").inc()
            logger.warning("item deletion failed - not found", extra={"item_id": item_id})
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

        item_operations.labels(operation="delete").inc()
        logger.info("item deleted", extra={"item_id": item_id})
        return {"status": "deleted", "id": item_id}
