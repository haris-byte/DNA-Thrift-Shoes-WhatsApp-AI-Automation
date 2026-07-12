import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.models.conversation_models import BotResponse, ConversationSession
from app.models.inventory_models import InventoryItem, StockStatus
from app.inventory.seed import SEED_INVENTORY


class SQLiteDatabase:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS inventory (
                    product_id TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    brand TEXT NOT NULL,
                    model TEXT NOT NULL,
                    size_us REAL NOT NULL,
                    condition_score INTEGER NOT NULL CHECK(condition_score BETWEEN 1 AND 10),
                    base_price INTEGER NOT NULL CHECK(base_price > 0),
                    stock_status TEXT NOT NULL,
                    description TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_inventory_lookup
                    ON inventory(brand, model, size_us);

                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    sender_id TEXT PRIMARY KEY,
                    session_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id TEXT PRIMARY KEY,
                    sender_id TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            current_count = connection.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
            if current_count == 0:
                connection.executemany(
                    """
                    INSERT INTO inventory (
                        product_id, product_name, brand, model, size_us,
                        condition_score, base_price, stock_status, description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            item.product_id,
                            item.product_name,
                            item.brand,
                            item.model,
                            item.size_us,
                            item.condition_score,
                            item.base_price,
                            item.stock_status.value,
                            item.description,
                        )
                        for item in SEED_INVENTORY
                    ],
                )

    def reset_for_tests(self) -> None:
        if self.path.exists():
            self.path.unlink()
        self.initialize()


class InventoryRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> InventoryItem:
        return InventoryItem(
            product_id=row["product_id"],
            product_name=row["product_name"],
            brand=row["brand"],
            model=row["model"],
            size_us=row["size_us"],
            condition_score=row["condition_score"],
            base_price=row["base_price"],
            stock_status=StockStatus(row["stock_status"]),
            description=row["description"],
        )

    def exact_matches(self, brand: str, model: str, size_us: float) -> list[InventoryItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM inventory
                WHERE lower(brand) = lower(?)
                  AND lower(model) = lower(?)
                  AND abs(size_us - ?) < 0.01
                ORDER BY
                  CASE stock_status WHEN 'in_stock' THEN 0 WHEN 'reserved' THEN 1 ELSE 2 END,
                  condition_score DESC
                """,
                (brand, model, size_us),
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def same_model(self, brand: str, model: str, requested_size: float) -> list[InventoryItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM inventory
                WHERE lower(brand) = lower(?)
                  AND lower(model) = lower(?)
                  AND stock_status = 'in_stock'
                ORDER BY abs(size_us - ?), condition_score DESC
                LIMIT 5
                """,
                (brand, model, requested_size),
            ).fetchall()
        return [self._row_to_item(row) for row in rows]

    def brand_alternatives(self, brand: str) -> list[InventoryItem]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM inventory
                WHERE lower(brand) = lower(?) AND stock_status = 'in_stock'
                ORDER BY condition_score DESC, product_name
                LIMIT 5
                """,
                (brand,),
            ).fetchall()
        return [self._row_to_item(row) for row in rows]


class SessionRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def get(self, sender_id: str) -> ConversationSession:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT session_json FROM conversation_sessions WHERE sender_id = ?",
                (sender_id,),
            ).fetchone()
        if row is None:
            return ConversationSession(sender_id=sender_id)
        return ConversationSession.model_validate_json(row["session_json"])

    def save(self, session: ConversationSession) -> ConversationSession:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_sessions(sender_id, session_json, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(sender_id) DO UPDATE SET
                    session_json = excluded.session_json,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (session.sender_id, session.model_dump_json()),
            )
        return session

    def reset(self, sender_id: str) -> ConversationSession:
        session = ConversationSession(sender_id=sender_id)
        return self.save(session)


class IdempotencyRepository:
    def __init__(self, database: SQLiteDatabase) -> None:
        self.database = database

    def get(self, message_id: str) -> BotResponse | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT response_json FROM processed_messages WHERE message_id = ?",
                (message_id,),
            ).fetchone()
        if row is None:
            return None
        return BotResponse.model_validate_json(row["response_json"])

    def save(self, response: BotResponse) -> None:
        with self.database.connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO processed_messages(message_id, sender_id, response_json)
                VALUES (?, ?, ?)
                """,
                (response.message_id, response.sender_id, response.model_dump_json()),
            )
