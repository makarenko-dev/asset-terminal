import logging
import asyncio
import httpx
from typing import List, Tuple, Set, Optional, Dict
import time
import yfinance as yf

import db
from data_types import AssetType, ChartPeriod

MAX_DIFF = 1000 * 60 * 60 * 24


class ChartService:
    def __init__(self, symbol_to_name: Dict[str, str]):
        self.symbol_to_name = symbol_to_name
        self._queue: asyncio.Queue[Tuple[str, AssetType]] = asyncio.Queue()
        self._enqueued: Set[Tuple[str, AssetType]] = set()

    async def chart_data_for(
        self, asset: str, asset_type: AssetType, period: ChartPeriod = ChartPeriod.MONTH
    ) -> Optional[List[Tuple[int, float]]]:
        normalized_name = asset.lower()
        result = await db.get_last_updated_price(normalized_name)
        current_time = time.time() * 1000
        if not result or (current_time - result) > MAX_DIFF:
            logging.info(f"No data for {asset} chart. Adding to queue")
            self._add_to_fetch_queue(normalized_name, asset_type)
            return None
        chart = await db.prices_chart_for(normalized_name, period)
        return chart

    def _add_to_fetch_queue(self, asset: str, asset_type: AssetType):
        data = (asset, asset_type)
        if data not in self._enqueued:
            self._enqueued.add(data)
            self._queue.put_nowait(data)

    def run(self):
        asyncio.create_task(self._worker())

    async def _worker(self):
        while True:
            try:
                data = await self._queue.get()
                asset, asset_type = data
                if asset_type == AssetType.CRYPTO:
                    rows = await self.fetch_crypto_chart_data(asset)
                else:
                    rows = await self.fetch_stock_chart_data(asset)
                if rows:
                    await db.update_prices_data(asset, rows)
                self._enqueued.remove(data)
                self._queue.task_done()
            except Exception as e:
                logging.error(f"Error {e}")
            await asyncio.sleep(60)

    async def fetch_crypto_chart_data(
        self, asset_symbol: str
    ) -> List[Tuple[int, float]]:
        name = self.symbol_to_name[asset_symbol]
        logging.info(f"Called fetch_chart_data for {asset_symbol}, name {name}")
        url = f"https://api.coingecko.com/api/v3/coins/{name}/market_chart?vs_currency=usd&days=365&interval=daily"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            data = r.json()
        prices = [(int(ts), float(price)) for ts, price in data.get("prices")]
        return prices

    async def fetch_stock_chart_data(
        self, asset_symbol: str
    ) -> List[Tuple[int, float]]:
        loop = asyncio.get_running_loop()

        def _get() -> List[Tuple[int, float]]:
            df = yf.Ticker(asset_symbol).history(period="1y", interval="1d")
            if df.empty:
                return []
            rows = []
            for ts, close in df["Close"].items():
                rows.append((int(ts.value // 1_000_000), float(close)))
            return rows

        data = await loop.run_in_executor(None, _get)
        return data
