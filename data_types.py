from dataclasses import dataclass, asdict
from enum import Enum
from typing import Tuple, List, Any


class AssetType(Enum):
    CRYPTO = "crypto"
    STOCK = "stock"


@dataclass
class Asset:
    asset_type: AssetType
    name: str
    amount: float
    avg_price: float

    def to_json(self) -> dict:
        d = asdict(self)
        d["asset_type"] = self.asset_type.value
        return d

    @staticmethod
    def from_json(d: dict) -> "Asset":
        return Asset(
            asset_type=AssetType(d["asset_type"]),
            name=d["name"],
            amount=float(d["amount"]),
            avg_price=float(d["avg_price"]),
        )


@dataclass
class AssetStat:
    asset: Asset
    price: float
    value: float
    pl_today: float
    pl_total: float


@dataclass
class TotalStat:
    total_value: float
    pl_total: float
    pl_today: float
    asset_stats: List[AssetStat]
