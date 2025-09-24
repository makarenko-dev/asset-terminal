from typing import List, Dict
import httpx
import asyncio
import yfinance as yf
from data_types import AssetStat, AssetType
from data_source import CachedDataProvider

# https://api.kraken.com/0/public/Ticker?pair=XBTUSD,ETHUSD,SOLUSD


async def get_crypto_prices(assets: List[str]) -> Dict[str, float]:
    result = {}
    assets_keys = [a.lower() for a in assets]
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1"
    async with httpx.AsyncClient() as client:
        r = await client.get(url)
        r_json = r.json()
        for coin in r_json:
            # print(coin["symbol"])
            if coin["symbol"] in assets_keys:
                result[coin["symbol"].upper()] = float(coin["current_price"])
    return result


async def get_stocks_prices(stocks: List[str]) -> Dict[str, float]:
    prices = await asyncio.gather(*(_stock_price(s) for s in stocks))
    return dict(prices)


async def _stock_price(stock: str):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, lambda: (stock, yf.Ticker(stock).info["bid"])
    )


async def get_test_data():
    lst = [
        AssetStat(AssetType.CRYPTO, "BTC", 1, 87000, 112000, 300, 1000),
        AssetStat(AssetType.CRYPTO, "ETH", 3, 1900, 4300, 500, 1000),
        AssetStat(AssetType.STOCK, "MSFT", 2, 396, 500, 100, -123),
    ]
    return lst


async def get_data():
    crypto = ["BTC", "ETH"]
    stocks = ["MSFT", "AAPL"]
    stocks_response = await get_stocks_prices(stocks)
    crypto_response = await get_crypto_prices(crypto)
    return crypto_response.update(stocks_response)


async def main():
    crypto = ["BTC", "ETH"]
    stocks = ["MSFT", "AAPL"]
    stocks_response = await get_stocks_prices(stocks)
    crypto_response = await get_crypto_prices(crypto)
    print(f"Crypto - {crypto_response} \n Stocks - {stocks_response}")


if __name__ == "__main__":
    p = CachedDataProvider()
    asyncio.run(p.total_stat())
