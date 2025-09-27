from typing import List, Dict, Any
import httpx
import asyncio
import logging
import yfinance as yf

from data_types import TotalStat, AssetStat, Asset, AssetType
from wallet import Wallet
import db


class PortfolioService:

    async def init(self):
        assets = await db.wallet_assets()
        self.wallet = Wallet.from_asset_list(assets)

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

    async def add_asset(self, asset: Asset):
        await db.add_asset_to_wallet(asset)
        if asset.asset_type == AssetType.CRYPTO:
            self.wallet.crypto[asset.name] = asset
        else:
            self.wallet.stocks[asset.name] = asset

    async def update_asset(self, asset: Asset):
        pass
