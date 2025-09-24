from typing import List, Dict, Any, Optional, Tuple, Set
import asyncio
import yfinance as yf
import logging
import httpx
import time
import json

from data_types import AssetStat, TotalStat, AssetType
from wallet import Wallet
import db

MAX_DIFF = 1000 * 60 * 60 * 24


class CachedDataProvider:
    def __init__(self, wallet: Wallet):
        self.wallet = wallet
        self.symbol_to_name: Dict[str, str] = {}
        self._queue: asyncio.Queue[Tuple[str, AssetType]] = asyncio.Queue()
        self._enqueued: Set[Tuple[str, AssetType]] = set()

    async def chart_data_for(
        self, asset: str, asset_type: AssetType
    ) -> Optional[List[Tuple[int, float]]]:
        result = await db.get_last_updated_price(asset)
        current_time = time.time() * 1000
        if not result or (current_time - result) > MAX_DIFF:
            logging.info(f"No data for {asset} chart. Adding to queue")
            self._add_to_fetch_queue(asset, asset_type)
            return None
        chart = await db.prices_chart_for(asset)
        logging.info(f"Returning data for {asset} chart")
        return chart

    def _add_to_fetch_queue(self, asset: str, asset_type: AssetType):
        data = (asset, asset_type)
        if data not in self._enqueued:
            self._enqueued.add(data)
            self._queue.put_nowait(data)

    async def init_provider(self):
        await db.init_db()
        self.symbol_to_name = self._load_symbol_map()

    def _load_symbol_map(self):
        with open("crypto_mapping.json", "r", encoding="utf-8") as f:
            m = json.load(f)
        return {k.lower(): v for k, v in m.items()}

    def run(self):
        asyncio.create_task(self._job())

    async def _job(self):
        for crypto in self.wallet.crypto.keys():
            await self.chart_data_for(crypto.lower(), AssetType.CRYPTO)
        for stock in self.wallet.stocks.keys():
            await self.chart_data_for(stock.lower(), AssetType.STOCK)
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
        url = f"https://api.coingecko.com/api/v3/coins/{name}/market_chart?vs_currency=usd&days=30&interval=daily"
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
            df = yf.Ticker(asset_symbol).history(period="1mo", interval="1d")
            if df.empty:
                return []
            rows = []
            for ts, close in df["Close"].items():
                rows.append((int(ts.value // 1_000_000), float(close)))
            return rows

        data = await loop.run_in_executor(None, _get)
        return data

    async def total_stat(self) -> TotalStat:
        crypto = self.wallet.crypto.keys()
        stocks = self.wallet.stocks.keys()
        crypto_market, stok_market = await asyncio.gather(
            self.get_crypto_info(crypto), self.get_stocks_info(stocks)
        )
        stats: List[AssetStat] = []
        total_today = 0
        total_all = 0
        total_value = 0
        for coin in crypto:
            meta = crypto_market.get(coin)
            price = float(meta["current_price"])
            change_24h = float(meta["price_change_24h"])
            pl_today = self.wallet.crypto[coin].amount * change_24h
            pl_total = self.wallet.crypto[coin].amount * (
                price - self.wallet.crypto[coin].avg_price
            )
            value = self.wallet.crypto[coin].amount * price
            stats.append(
                AssetStat(self.wallet.crypto[coin], price, value, pl_today, pl_total)
            )
            total_today += pl_today
            total_all += pl_total
            total_value += value
        for stock in stocks:
            meta = stok_market.get(stock)
            try:
                price = float(meta["currentPrice"])
            except KeyError as e:
                logging.error(f"Stock {stock} doesn't have current price")
                price = float(meta["bid"])
            change_24h = float(meta["regularMarketChange"])
            pl_today = self.wallet.stocks[stock].amount * change_24h
            pl_total = self.wallet.stocks[stock].amount * (
                price - self.wallet.stocks[stock].avg_price
            )
            value = self.wallet.stocks[stock].amount * price
            stats.append(
                AssetStat(self.wallet.stocks[stock], price, value, pl_today, pl_total)
            )
            total_today += pl_today
            total_all += pl_total
            total_value += value
        logging.info(f"Total Value {total_value}")
        return TotalStat(total_value, total_all, total_today, stats)

    async def get_crypto_info(self, assets: List[str]) -> Dict[str, Dict[str, Any]]:
        result = {}
        assets_keys = [a.lower() for a in assets]
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            r_json = r.json()
            for coin in r_json:
                if coin["symbol"] in assets_keys:
                    result[coin["symbol"].upper()] = coin
        return result

    async def get_stocks_info(self, assets: List[str]) -> Dict[str, Dict[str, Any]]:
        prices = await asyncio.gather(*(self._stock_price(s) for s in assets))
        return dict(prices)

    async def _stock_price(self, stock: str):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: (stock, yf.Ticker(stock).info))
