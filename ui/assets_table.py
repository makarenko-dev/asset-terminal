from textual.widget import Widget
from textual.widgets import DataTable
from textual.reactive import reactive
from textual.binding import Binding
from textual_plotext import PlotextPlot
from rich.text import Text

from typing import Tuple, Any, Dict, Callable, Optional, List
import logging
from datetime import datetime

from ui.pl_header import PLHeader
from ui.edit_screen import EditAmountScreen
from ui import helper


from services.provider import DataProvider
from data_types import AssetStat, TotalStat, AssetType, ChartPeriod, Asset


class AssetsTable(Widget):
    BINDINGS = [
        Binding("t", "sort_by_type", "sort by type", show=False),
        Binding("n", "sort_by_name", "sort by name", show=False),
        Binding("p", "sort_by_pl_total", "sort by p&l total", show=False),
        Binding("c", "show_chart", "show chart"),
        Binding("a", "add_asset", "add asset"),
        Binding("e", "edit_asset", "edit asset"),
        Binding("1", "chart_range_1m", "1M"),
        Binding("2", "chart_range_6m", "6M"),
        Binding("3", "chart_range_1y", "1Y"),
    ]
    stat: reactive[TotalStat] = reactive(None)
    current_sort: Dict[str, bool] = {}
    current_sort_key: Optional[Callable] = None

    def __init__(self, provider: DataProvider, *args, **kwargs):
        self.provider = provider
        super().__init__(*args, **kwargs)

    async def action_add_asset(self):
        self.run_worker(self._add_asset_flow(), exclusive=True)

    async def action_edit_asset(self):
        self.run_worker(self._edit_asset_flow(), exclusive=True)

    async def _edit_asset_flow(self):
        asset_name, _, amount = self.asset_under_cursor()
        result = await self.app.push_screen_wait(EditAmountScreen(asset_name, amount))

    async def _add_asset_flow(self):
        result = await self.app.push_screen_wait(EditAmountScreen("", 0.0, 0.0))
        if result:
            asset_type, name, amount, price = result
            a = Asset(asset_type, name.upper(), amount, price)
            await self.provider.add_asset(a)
            self.stat = await self.provider.total_stat()

    def compose(self):
        yield PlotextPlot()
        yield PLHeader()
        yield DataTable()

    def _plain_key(self, value):
        return value

    def _float_from_text(self, value):
        return float(value.plain)

    def asset_under_cursor(self) -> Tuple[str, AssetType, float]:
        table = self.query_one(DataTable)
        coordinate = table.cursor_coordinate
        row_key = table.coordinate_to_cell_key(coordinate).row_key
        row_values = table.get_row(row_key)
        asset_name = row_values[1].lower()
        asset_type = AssetType(row_values[0])
        amount = row_values[2]
        return asset_name, asset_type, amount

    def draw_chart(self, data: List[Tuple[int, float]], title: str):
        plot_text = self.query_one(PlotextPlot)
        plt = plot_text.plt
        plt.clear_figure()
        if data:
            y = [d[1] for d in data]
            x = [datetime.fromtimestamp(d[0] / 1000).strftime("%d/%m/%Y") for d in data]
            plt.plot(x, y)
        else:
            plt.plot([], [])
        plt.title(title)
        display = plot_text.display
        if display:
            plot_text.refresh()
        else:
            plot_text.display = True

    async def on_mount(self):
        self.query_one(PlotextPlot).display = False
        table = self.query_one(DataTable)
        table.show_cursor = True
        table.cursor_type = "row"
        for header, key in helper.COLUMNS:
            table.add_column(header, key=key)
        await self.provider.init()
        self.call_later(self.refresh_data)
        self.set_interval(helper.UPDATE_INTERVAL, self.refresh_data)

    def on_data_table_row_highlighted(self, _):
        pass
        # self.query_one(PlotextPlot).display = False

    async def action_chart_range_1m(self):
        asset_name, asset_type, _ = self.asset_under_cursor()
        data = await self.provider.chart_data_for(
            asset_name, asset_type, ChartPeriod.MONTH
        )
        self.draw_chart(data, f"{asset_name} price for 1M")

    async def action_chart_range_6m(self):
        asset_name, asset_type, _ = self.asset_under_cursor()
        data = await self.provider.chart_data_for(
            asset_name, asset_type, ChartPeriod.HALF_YEAR
        )
        self.draw_chart(data, f"{asset_name} price for 6M")

    async def action_chart_range_1y(self):
        asset_name, asset_type, _ = self.asset_under_cursor()
        data = await self.provider.chart_data_for(
            asset_name, asset_type, ChartPeriod.YEAR
        )
        self.draw_chart(data, f"{asset_name} price for 1Y")

    async def action_show_chart(self):
        plot_text = self.query_one(PlotextPlot)
        display = plot_text.display
        if display:
            plot_text.display = False
            return
        await self.action_chart_range_1m()

    async def refresh_data(self):
        new_stat = await self.provider.total_stat()
        self.stat = new_stat

    def create_table_row(self, stat: AssetStat) -> Tuple[Any]:
        pl_today = Text(
            f"{stat.pl_today:+.2f}", style=helper.color_for_pl(stat.pl_today)
        )
        pl_total = Text(
            f"{stat.pl_total:+.2f}", style=helper.color_for_pl(stat.pl_total)
        )
        return (
            stat.asset.asset_type.value,
            stat.asset.name,
            f"{stat.asset.amount:.4f}",
            f"{stat.asset.avg_price:.2f}",
            f"{stat.price:.2f}",
            stat.value,
            pl_today,
            pl_total,
        )

    def sort_reverse(self, sort_type: str):
        already_applied = sort_type in self.current_sort
        if already_applied:
            reverse = not self.current_sort[sort_type]
            self.current_sort[sort_type] = reverse
            return reverse
        self.current_sort.clear()
        self.current_sort[sort_type] = False
        return False

    def action_sort_by_type(self):
        table = self.query_one(DataTable)
        table.sort("type", reverse=self.sort_reverse("type"))
        self.current_sort_key = self._plain_key

    def action_sort_by_name(self):
        table = self.query_one(DataTable)
        table.sort("name", reverse=self.sort_reverse("name"))
        self.current_sort_key = self._plain_key

    def action_sort_by_pl_total(self):
        table = self.query_one(DataTable)
        table.sort(
            "pl_total",
            key=self._float_from_text,
            reverse=self.sort_reverse("pl_total"),
        )
        self.current_sort_key = self._float_from_text

    def watch_stat(self, stat: TotalStat) -> None:
        if not stat:
            return
        header = self.query_one(PLHeader)
        header.value = round(stat.total_value, 2)
        header.today_pl = stat.pl_today
        header.total_pl = stat.pl_total
        table = self.query_one(DataTable)
        cursor = table.cursor_coordinate
        table.clear()
        for r in stat.asset_stats:
            table.add_row(*self.create_table_row(r), key=r.asset.name.lower())
        if self.current_sort:
            col, reverse = next(iter(self.current_sort.items()))
            table.sort(col, reverse=reverse, key=self.current_sort_key)
        table.cursor_coordinate = cursor
