from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from ..utils.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
metadata = MetaData()

events = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type", String),
    Column("severity", Integer),
    Column("timestamp", String),
)

metadata.create_all(engine)

def save_event(event: dict):
    with engine.connect() as conn:
        conn.execute(events.insert().values(**event))
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData
from src.utils.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
metadata = MetaData()

events = Table(
    "events",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("type", String),
    Column("severity", Integer),
    Column("timestamp", String),
)

metadata.create_all(engine)

def save_event(event: dict):
    with engine.connect() as conn:
        conn.execute(events.insert().values(**event))
