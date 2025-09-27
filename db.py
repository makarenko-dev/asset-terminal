import aiosqlite
from typing import List, Tuple
import time
import logging
from datetime import datetime, timezone, timedelta
from data_types import ChartPeriod, Asset, AssetType

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
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            amount     REAL NOT NULL,
            price     REAL NOT NULL,
            asset_type TEXT NOT NULL
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


def _since_ms_for(period: ChartPeriod) -> int:
    now = datetime.now(timezone.utc)
    if period == ChartPeriod.MONTH:
        delta = timedelta(days=30)
    if period == ChartPeriod.HALF_YEAR:
        delta = timedelta(days=182)
    if period == ChartPeriod.YEAR:
        delta = timedelta(days=365)
    return int((now - delta).timestamp() * 1000)


async def prices_chart_for(asset: str, period: ChartPeriod) -> List[Tuple[int, float]]:
    async with aiosqlite.connect(DB_PATH) as db:
        asset_id = await _asset_id(db, asset)
        since_ms = _since_ms_for(period)
        curr = await db.execute(
            "SELECT ts_ms, price FROM prices WHERE asset_id = ? AND ts_ms >= ?",
            (asset_id, since_ms),
        )
        rows = await curr.fetchall()
        return [(int(ts), float(p)) for ts, p in rows]


async def _asset_id(db: aiosqlite.Connection, asset: str):
    curr_time = 0
    curr = await db.execute("SELECT id FROM assets WHERE symbol = ?", (asset,))
    row = await curr.fetchone()
    if row:
        return row[0]
    result = await db.execute(
        "INSERT INTO assets (symbol, last_called_ms) VALUES (?, ?)", (asset, curr_time)
    )
    await db.commit()
    return result.lastrowid


async def add_asset_to_wallet(asset: Asset):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO wallet (name, amount, price, asset_type) VALUES (?, ?, ?, ?)",
            (asset.name, asset.amount, asset.avg_price, asset.asset_type.value),
        )
        await db.commit()


async def update_asset_in_wallet(asset: Asset):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE wallet SET amount=?, price=? WHERE name=?",
            (asset.amount, asset.avg_price, asset.name),
        )
        await db.commit()


async def delete_asset_from_wallet(asset: Asset):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM wallet WHERE name=?",
            (asset.name,),
        )
        await db.commit()


async def wallet_assets() -> List[Asset]:
    async with aiosqlite.connect(DB_PATH) as db:
        curr = await db.execute(
            "SELECT name, amount, price, asset_type FROM wallet",
        )
        rows = await curr.fetchall()
        result = [
            Asset(AssetType(asset_type), name, amount, price)
            for name, amount, price, asset_type in rows
        ]
        return result


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
