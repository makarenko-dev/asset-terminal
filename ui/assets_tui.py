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

    def __init__(self, provider: DataProvider, *args, **kwargs):
        self.provider = provider
        super().__init__(*args, **kwargs)

    def compose(self):
        # yield PlotextPlot()
        yield AssetsTable(self.provider, id="assets-table")
        # yield AssetsWidget(self.provider)
        yield Footer()

    def on_mount(self):
        pass
        # self.query_one(PlotextPlot).display = False
        # self.set_interval(15, self.refresh_chart)

    async def refresh_chart(self):
        logging.info("Started to wait")
        new_data = await self.provider.chart_data_for("btc")
        y = [d[1] for d in new_data]
        x = [datetime.fromtimestamp(d[0] / 1000).strftime("%d/%m/%Y") for d in new_data]
        logging.info("Finished to wait")
        plt = self.query_one(PlotextPlot).plt
        plt.plot(x, y)
        self.query_one(PlotextPlot).display = True

    def on_button_pressed(self, event: Button.Pressed):
        logging.info(f"Button pressed {event.button.id}")
        # self.query_one(ContentSwitcher).current = event.button.id
