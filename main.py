from data_source import CachedDataProvider
from wallet import Wallet
from pathlib import Path
from ui.assets_tui import AssetsTui
import logging


if __name__ == "__main__":
    log_path = Path("logs/app.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=str(log_path),
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    p = Path("wallet.json")
    wallet = Wallet.load(p)
    provider = CachedDataProvider(wallet)
    app = AssetsTui(provider)
    app.run()
