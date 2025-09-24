RED = "#ff6960"
GREEN = "#00cc46"
COLUMNS = [
    ("[T]ype", "type"),
    ("[N]ame", "name"),
    ("Amount", "amount"),
    ("Avg price", "avg_price"),
    ("Price", "price"),
    ("Value", "value"),
    ("P&L today", "pl_today"),
    ("[P]&L total", "pl_total"),
]
UPDATE_INTERVAL = 60


def color_for_pl(value: float) -> str:
    if value < 0:
        return RED
    return GREEN
