from textual.app import App
from textual.binding import Binding
from textual.widgets import Footer, Button
from textual_plotext import PlotextPlot

import logging
from typing import List, Tuple, Any
from datetime import datetime

from ui.assets_table import AssetsTable
from ui.assets_widget import AssetsWidget
from services.provider import DataProvider


class AssetsTui(App):
    CSS_PATH = "assets.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]
    ENABLE_COMMAND_PALETTE = False

    def __init__(self, provider: DataProvider, *args, **kwargs):
        self.provider = provider
        super().__init__(*args, **kwargs)

    def compose(self):
        yield AssetsTable(self.provider, id="assets-table")
        yield Footer()

    def on_mount(self):
        pass
