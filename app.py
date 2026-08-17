"""Simple toy API for Kubernetes exercise.

A minimal FastAPI application with health checks, basic CRUD operations,
Prometheus metrics, and PostgreSQL database.
"""

import asyncpg
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    database_url: str = "postgresql://postgres:postgres@localhost:5432/toyapi"
    model_config = SettingsConfigDict(env_prefix="")


settings = Settings()

# Global database connection pool
db_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    global db_pool
    # Startup: create database pool and initialize schema
    db_pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
    await init_db()
    yield
    # Shutdown: close database pool
    if db_pool:
        await db_pool.close()


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


app = FastAPI(title="K8s Toy API", root_path="/api/v1", lifespan=lifespan)

# Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Custom metrics
item_operations = Counter(
    "item_operations_total", "Item operations by type", ["operation"]
)


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
        return {"status": "degraded", "database": f"error: {e}"}


@app.get("/items")
async def list_items() -> list[Item]:
    """List all items."""
    item_operations.labels(operation="list").inc()
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, value FROM items ORDER BY id")
        return [Item(id=row["id"], name=row["name"], value=row["value"]) for row in rows]


@app.get("/items/{item_id}")
async def get_item(item_id: str) -> Item:
    """Get a specific item by ID."""
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, value FROM items WHERE id = $1", item_id)

        if not row:
            item_operations.labels(operation="get_not_found").inc()
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

        item_operations.labels(operation="get").inc()
        return Item(id=row["id"], name=row["name"], value=row["value"])


@app.post("/items")
async def create_item(item: Item) -> Item:
    """Create a new item."""
    async with db_pool.acquire() as conn:
        # Check if item already exists
        exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)", item.id)
        if exists:
            item_operations.labels(operation="create_conflict").inc()
            raise HTTPException(status_code=409, detail=f"Item already exists: {item.id}")

        # Insert new item
        await conn.execute(
            "INSERT INTO items (id, name, value) VALUES ($1, $2, $3)",
            item.id,
            item.name,
            item.value,
        )
        item_operations.labels(operation="create").inc()
        return item


@app.put("/items/{item_id}")
async def update_item(item_id: str, item: Item) -> Item:
    """Update an existing item."""
    if item.id != item_id:
        raise HTTPException(status_code=400, detail="ID mismatch")

    async with db_pool.acquire() as conn:
        # Check if item exists
        exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM items WHERE id = $1)", item_id)
        if not exists:
            item_operations.labels(operation="update_not_found").inc()
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

        # Update item
        await conn.execute(
            "UPDATE items SET name = $1, value = $2 WHERE id = $3",
            item.name,
            item.value,
            item_id,
        )
        item_operations.labels(operation="update").inc()
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
            raise HTTPException(status_code=404, detail=f"Item not found: {item_id}")

        item_operations.labels(operation="delete").inc()
        return {"status": "deleted", "id": item_id}
