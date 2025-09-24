import aiosqlite
from typing import List, Tuple
import time
import logging

DB_PATH = "cache.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS assets (
            id               INTEGER PRIMARY KEY,
            symbol           TEXT UNIQUE NOT NULL,
            last_called_ms   INTEGER
        )"""
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY,
            asset_id  INTEGER NOT NULL,
            ts_ms     INTEGER NOT NULL,
            price     REAL NOT NULL,
            FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE
        )"""
        )
        await db.commit()


async def get_last_updated_price(asset: str):
    async with aiosqlite.connect(DB_PATH) as db:
        asset_id = await _asset_id(db, asset)
        curr = await db.execute(
            "SELECT last_called_ms FROM assets WHERE id = ?", (asset_id,)
        )
        row = await curr.fetchone()
        if row:
            return row[0]
        return None


async def prices_chart_for(asset: str) -> List[Tuple[int, float]]:
    async with aiosqlite.connect(DB_PATH) as db:
        asset_id = await _asset_id(db, asset)
        curr = await db.execute(
            "SELECT ts_ms, price FROM prices WHERE asset_id = ?", (asset_id,)
        )
        rows = await curr.fetchall()
        return [(int(ts), float(p)) for ts, p in rows]


async def _asset_id(db: aiosqlite.Connection, asset: str):
    curr_time = 0
    curr = await db.execute("SELECT id FROM assets WHERE symbol = ?", (asset,))
    row = await curr.fetchone()
    if row:
        logging.info(f"Found asset returning id {row[0]}")
        return row[0]
    result = await db.execute(
        "INSERT INTO assets (symbol, last_called_ms) VALUES (?, ?)", (asset, curr_time)
    )
    await db.commit()
    return result.lastrowid


async def update_prices_data(asset: str, prices: List[Tuple[int, float]]):
    async with aiosqlite.connect(DB_PATH) as db:
        asset_id = await _asset_id(db, asset)
        await db.execute("DELETE FROM prices WHERE asset_id = ?", (asset_id,))
        await db.executemany(
            "INSERT INTO prices (asset_id, ts_ms, price) VALUES (?, ?, ?)",
            ((asset_id, ts, p) for ts, p in prices),
        )
        current_time = time.time() * 1000
        await db.execute(
            "UPDATE assets SET last_called_ms = ? WHERE id = ?",
            (current_time, asset_id),
        )
        await db.commit()
