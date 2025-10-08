from textual.screen import ModalScreen
from textual.widgets import Label, Button, Checkbox, Footer
from textual.containers import Vertical, Horizontal


class ConfirmDeleteScreen(ModalScreen):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "save", "Save"),
    ]

    def __init__(self, asset_name: str):
        super().__init__()
        self.asset_name = asset_name

    def compose(self):
        with Vertical(id="confirm-del"):
            yield Label(f"Delete {self.asset_name.upper()} from your wallet?")
        yield Footer()

    def action_save(self):
        self.dismiss(True)

    def action_cancel(self):
        self.dismiss(None)
