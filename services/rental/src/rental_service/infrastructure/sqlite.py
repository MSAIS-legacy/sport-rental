"""SQLite-адаптер. Каждая команда выполняется одной транзакцией."""

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from ..domain.errors import NotFound


class SQLiteRepository:
    def __init__(self, connection):
        self.connection = connection

    def get(self, kind, identifier, entity_type):
        row = self.connection.execute(
            "SELECT payload FROM aggregates WHERE kind = ? AND id = ?",
            (kind, identifier),
        ).fetchone()
        if row is None:
            raise NotFound(f"{kind}: {identifier} не найден")
        return entity_type(**json.loads(row[0]))

    def list(self, kind, entity_type):
        rows = self.connection.execute(
            "SELECT payload FROM aggregates WHERE kind = ? ORDER BY rowid", (kind,)
        ).fetchall()
        return [entity_type(**json.loads(row[0])) for row in rows]

    def save(self, kind, entity):
        self.connection.execute(
            "INSERT INTO aggregates(kind, id, payload) VALUES (?, ?, ?) "
            "ON CONFLICT(kind, id) DO UPDATE SET payload = excluded.payload",
            (kind, entity.id, json.dumps(asdict(entity), ensure_ascii=False)),
        )


class SQLiteUnitOfWork:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def __enter__(self):
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path, timeout=15)
        try:
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS aggregates ("
                "kind TEXT NOT NULL, id TEXT NOT NULL, payload TEXT NOT NULL, "
                "PRIMARY KEY (kind, id))"
            )
            # Блокировка до чтения исключает гонки read-check-write,
            # в том числе двойное бронирование и двойной возврат денег.
            self.connection.execute("BEGIN IMMEDIATE")
            self.repository = SQLiteRepository(self.connection)
            return self
        except BaseException:
            self.connection.close()
            raise

    def __exit__(self, exc_type, exc, traceback):
        try:
            if exc_type is None:
                self.connection.commit()
            else:
                self.connection.rollback()
        finally:
            self.connection.close()
