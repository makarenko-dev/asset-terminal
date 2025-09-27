import json
from typing import Optional, List, Tuple

from wallet import Wallet
from services.chart import ChartService
from services.portfolio import PortfolioService
from data_types import AssetType, TotalStat, ChartPeriod, Asset
import db


def _load_symbol_map():
    with open("crypto_mapping.json", "r", encoding="utf-8") as f:
        m = json.load(f)
    return {k.lower(): v for k, v in m.items()}


class DataProvider:
    def __init__(self):
        self.charts = ChartService(_load_symbol_map())
        self.portfolio = PortfolioService()

    async def init(self):
        await db.init_db()
        await self.portfolio.init()
        await self._pre_cache_wallet()
        self.charts.run()

    async def _pre_cache_wallet(self):
        for stock in self.portfolio.wallet.stocks.keys():
            await self.charts.chart_data_for(stock, AssetType.STOCK)
        for crypto in self.portfolio.wallet.crypto.keys():
            await self.charts.chart_data_for(crypto, AssetType.CRYPTO)

    async def total_stat(self) -> TotalStat:
        return await self.portfolio.total_stat()

    async def chart_data_for(
        self, asset: str, asset_type: AssetType, period: ChartPeriod = ChartPeriod.MONTH
    ) -> Optional[List[Tuple[int, float]]]:
        return await self.charts.chart_data_for(asset, asset_type, period)

    async def add_asset(self, asset: Asset):
        return await self.portfolio.add_asset(asset)

    async def update_asset(self, asset: Asset):
        return await self.portfolio.update_asset(asset)

    async def delete_asset(self, asset: Asset):
        return await self.portfolio.delete_asset(asset)
