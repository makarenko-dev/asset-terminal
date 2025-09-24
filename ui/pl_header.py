from textual.widget import Widget
from textual.reactive import reactive
from textual.app import ComposeResult
from textual.widgets import Label
from textual.containers import Center
from rich.text import Text
from . import helper
import logging


class PLHeader(Widget):
    DEFAULT_CSS = """
    PLHeader {
        width: 100%;
        background: $panel;
        color: $foreground;
        height: 1;
    }
    """
    value: reactive[float] = reactive(0.0)
    today_pl: reactive[float] = reactive(0.0)
    total_pl: reactive[float] = reactive(0.0)

    def _create_header_text(self, value: float, total: float, today: float) -> Text:
        text = Text(f"Value {value} ; Total P&L ")
        pl_total = Text(f"{round(total, 2)}", style=helper.color_for_pl(total))
        text.append(pl_total)
        text.append(Text(" ; Today P&L "))
        pl_today = Text(f"{round(today)}", style=helper.color_for_pl(today))
        text.append(pl_today)
        return text

    def compose(self) -> ComposeResult:
        with Center():
            yield Label("Value ??? Total P&L ??? Today P&L ???")

    def watch_today_pl(self, v: float):
        text = self._create_header_text(self.value, self.total_pl, v)
        label = self.query_one(Label)
        label.update(text)

    def watch_total_pl(self, v: float):
        text = self._create_header_text(self.value, v, self.today_pl)
        label = self.query_one(Label)
        label.update(text)

    def watch_value(self, v: float):
        text = self._create_header_text(v, self.total_pl, self.today_pl)
        label = self.query_one(Label)
        label.update(text)
