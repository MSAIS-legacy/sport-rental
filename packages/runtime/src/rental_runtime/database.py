"""Технические адаптеры SQLAlchemy; доменных моделей сервисов здесь нет."""

import json
import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Column, Integer, MetaData, String, Table, Text, create_engine, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

metadata = MetaData()
aggregates = Table(
    "aggregates",
    metadata,
    Column("kind", String(80), primary_key=True),
    Column("id", String(100), primary_key=True),
    Column("payload", Text, nullable=False),
)
versions = Table(
    "cache_versions",
    metadata,
    Column("kind", String(80), primary_key=True),
    Column("revision", Integer, nullable=False),
)


outbox = Table(
    "outbox",
    metadata,
    Column("id", String(100), primary_key=True),
    Column("envelope", Text, nullable=False),
    Column("published", Integer, nullable=False, default=0),
    Column("created_at", String(50), nullable=False),
)
inbox = Table(
    "inbox",
    metadata,
    Column("id", String(100), primary_key=True),
    Column("processed_at", String(50), nullable=False),
)


class Database:
    def __init__(self, url):
        if "://" not in url:
            Path(url).parent.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{url}"
        self.engine = create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {},
        )
        self.initialized = False
        self.lock = threading.Lock()

    def initialize(self):
        with self.lock:
            if not self.initialized:
                # Защита от одновременного CREATE TABLE в API и worker одного сервиса.
                with self.engine.begin() as connection:
                    if self.engine.dialect.name == "postgresql":
                        connection.execute(text("SELECT pg_advisory_xact_lock(927401)"))
                    metadata.create_all(connection)
                self.initialized = True

    def close(self):
        self.engine.dispose()


class SQLRepository:
    def __init__(self, connection, not_found, cache=None):
        self.connection, self.not_found, self.cache = connection, not_found, cache

    def cache_key(self, kind, suffix):
        revision = (
            self.connection.execute(select(versions.c.revision).where(versions.c.kind == kind)).scalar() or 0
        )
        return f"{kind}:{revision}:{suffix}"

    def get(self, kind, identifier, entity_type):
        key = self.cache_key(kind, identifier) if self.cache else None
        payload = self.cache.get(key) if self.cache else None
        if payload is None:
            payload = self.connection.execute(
                select(aggregates.c.payload).where(aggregates.c.kind == kind, aggregates.c.id == identifier)
            ).scalar()
            if payload is None:
                raise self.not_found(f"{kind}: {identifier} не найден")
            if self.cache:
                self.cache.set(key, payload)
        return entity_type(**json.loads(payload))

    def list(self, kind, entity_type):
        key = self.cache_key(kind, "all") if self.cache else None
        cached = self.cache.get(key) if self.cache else None
        if cached is None:
            rows = (
                self.connection.execute(
                    select(aggregates.c.payload).where(aggregates.c.kind == kind).order_by(aggregates.c.id)
                )
                .scalars()
                .all()
            )
            cached = json.dumps(list(rows))
            if self.cache:
                self.cache.set(key, cached)
        return [entity_type(**json.loads(value)) for value in json.loads(cached)]

    def save(self, kind, entity):
        insert = pg_insert if self.connection.dialect.name == "postgresql" else sqlite_insert
        stmt = insert(aggregates).values(kind=kind, id=entity.id, payload=json.dumps(asdict(entity)))
        self.connection.execute(
            stmt.on_conflict_do_update(index_elements=["kind", "id"], set_={"payload": stmt.excluded.payload})
        )
        stmt = insert(versions).values(kind=kind, revision=1)
        self.connection.execute(
            stmt.on_conflict_do_update(index_elements=["kind"], set_={"revision": versions.c.revision + 1})
        )
        # Не кэшируем неподтверждённые записи текущей транзакции.
        self.cache = None


class SQLUnitOfWork:
    def __init__(self, database, not_found, cache=None):
        self.database, self.not_found, self.cache = database, not_found, cache

    def __enter__(self):
        self.database.initialize()
        self.connection = self.database.engine.connect()
        try:
            if self.connection.dialect.name == "sqlite":
                self.connection.exec_driver_sql("BEGIN IMMEDIATE")
            else:
                self.connection.begin()
                # Учебный сервис сериализует read-check-write в своей БД.
                self.connection.execute(text("SELECT pg_advisory_xact_lock(927402)"))
            self.repository = SQLRepository(self.connection, self.not_found, self.cache)
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

    def enqueue(self, target, event_type, payload):
        identifier = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()
        envelope = {
            "id": identifier,
            "type": event_type,
            "target": target,
            "payload": payload,
            "created_at": now,
            "version": 1,
        }
        self.connection.execute(
            outbox.insert().values(id=identifier, envelope=json.dumps(envelope), published=0, created_at=now)
        )
        return identifier

    def seen(self, identifier):
        return (
            self.connection.execute(select(inbox.c.id).where(inbox.c.id == identifier)).scalar() is not None
        )

    def remember(self, identifier):
        self.connection.execute(
            inbox.insert().values(id=identifier, processed_at=datetime.now(timezone.utc).isoformat())
        )

    def pending_events(self, limit=50):
        rows = self.connection.execute(
            select(outbox.c.envelope)
            .where(outbox.c.published == 0)
            .order_by(outbox.c.created_at, outbox.c.id)
            .limit(limit)
        ).scalars()
        return [json.loads(row) for row in rows]

    def mark_published(self, identifier):
        self.connection.execute(outbox.update().where(outbox.c.id == identifier).values(published=1))
