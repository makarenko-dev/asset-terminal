from decimal import Decimal, InvalidOperation
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Footer, Select
from textual.containers import Vertical

from data_types import AssetType

from typing import Tuple


class EditAmountScreen(ModalScreen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(
        self,
        asset: str,
        initial_amount: float,
        price: float,
    ):
        super().__init__()
        self.asset = asset
        self.initial_amount = initial_amount
        self.price = price

    def compose(self):
        with Vertical(id="edit-modal"):
            yield Label(id="error_label")
            yield Select(
                id="asset-type",
                options=[
                    ("Crypto", AssetType.CRYPTO.value),
                    ("Stock", AssetType.STOCK.value),
                ],
                value=AssetType.CRYPTO.value,
                allow_blank=False,
            )
            yield Label(f"Ticker")
            yield Input(
                value=str(self.asset), placeholder="Asset ticker", id="asset_name"
            )
            yield Label(f"Amount")
            yield Input(
                value=str(self.initial_amount), placeholder="Amount", id="amount"
            )
            yield Label(f"Price")
            yield Input(value=str(self.price), placeholder="Price", id="price")
        yield Footer()

    def on_mount(self):
        self.query_one("#error_label", Label).visible = False

    def action_cancel(self):
        self.dismiss(None)

    def action_save(self):
        self._save()

    def show_error_message(self, message: str):
        self.query_one("#amount", Input).value = ""
        error_label = self.query_one("#error_label", Label)
        error_label.update("Non negative float amount expected")
        error_label.visible = True

    def validate_float(self, raw: str) -> Tuple[bool, str]:
        try:
            value = float(raw.strip())
        except ValueError:
            return False, "Non negative float {name} expected", 0
        if value <= 0:
            return False, "Non negative float {name} expected", 0
        return True, "", value

    def validate_ticker(self, raw: str) -> Tuple[bool, str]:
        text = raw.strip()
        if not text:
            return False, "Non empty ticker expected"
        return True, "", text

    def _save(self):
        amount_input = self.query_one("#amount", Input)
        amount_validate, amount_error, amount = self.validate_float(amount_input.value)
        if not amount_validate:
            amount_input.value = ""
            self.show_error_message(amount_error.format(name="amount"))
            return
        price_input = self.query_one("#price", Input)
        price_validate, price_error, price = self.validate_float(price_input.value)
        if not price_validate:
            price_input.value = ""
            self.show_error_message(price_error.format(name="price"))
            return
        name_input = self.query_one("#asset_name", Input)
        name_validate, name_error, name = self.validate_ticker(name_input.value)
        if not name_validate:
            name_input.value = ""
            self.show_error_message(name_error)
            return
        asset_type_input = self.query_one("#asset-type", Select)
        asset_type = AssetType(asset_type_input.value)
        self.dismiss((asset_type, name, amount, price))
