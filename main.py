from services.provider import DataProvider
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
    provider = DataProvider()
    app = AssetsTui(provider)
    app.run()
