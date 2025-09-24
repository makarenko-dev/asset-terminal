from dataclasses import dataclass
from typing import List, Dict, Any
from data_types import Asset
from pathlib import Path
import json


@dataclass
class Wallet:
    crypto: Dict[str, Asset]
    stocks: Dict[str, Asset]

    def to_json(self):
        return {
            "crypto": [val.to_json() for val in self.crypto.values()],
            "stocks": [val.to_json() for val in self.stocks.values()],
        }

    @staticmethod
    def _list_to_map(items: List[dict]) -> Dict[str, Asset]:
        out: Dict[str, Asset] = {}
        for x in items:
            a = Asset.from_json(x)
            key = a.name.upper()
            out[key] = a
        return out

    @staticmethod
    def from_json(d: dict) -> "Wallet":
        return Wallet(
            crypto=Wallet._list_to_map(d.get("crypto", [])),
            stocks=Wallet._list_to_map(d.get("stocks", [])),
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        print(self.to_json())
        path.write_text(json.dumps(self.to_json(), indent=2))

    @staticmethod
    def load(path: Path) -> "Wallet":
        if not path.exists():
            return Wallet({}, {})
        data = json.loads(path.read_text())
        return Wallet.from_json(data)
