from textual.widgets import Input, Select, Static
from textual_plotext import PlotextPlot
import financial_manager
import fin_indicators
import exporter

class FinancialController:

    @staticmethod
    def _get_smart_interval(period: str, user_interval: str) -> str:
        if period == "max":
            return "1mo"
        if period == "1y" and user_interval in ["1m", "15m", "1h"]:
            return "1d"
        return user_interval

    @staticmethod
    def update_market_view(app) -> None:
        try:
            symbol = app.query_one("#fin_symbol", Input).value
            period = app.query_one("#fin_period", Select).value
            raw_interval = app.query_one("#fin_interval", Select).value
            
            interval = FinancialController._get_smart_interval(period, raw_interval)
            if interval != raw_interval:
                app.notify(f"adjusted interval to {interval}", severity="information")

        except (ValueError, AttributeError, KeyError) as e:
            app.notify(f"interface error: {e}", severity="error")
            return

        app.notify(f"Fetching {symbol}...", title="Please wait")
        
        # threading, due to network, do not lag ui
        
        def fetch_and_update():
            # work
            data = financial_manager.FinancialManager.fetch_data(symbol, period, interval)

            # should work on most textual versions
            app.call_from_thread(FinancialController._render_success, app, data, symbol)

        # Launch the thread without fancy callbacks
        app.run_worker(fetch_and_update, thread=True)

    @staticmethod
    def _render_success(app, data, symbol):
        if not data or "error" in data:
            err = data.get("error", "Unknown") if data else "No data"
            app.notify(f"Error: {err}", severity="error")
            return

        app.last_fin_data = data
        stats_text = fin_indicators.FinancialIndicators.analyze_market_data(data)
        app.query_one("#stats_display_fin", Static).update(stats_text)

        try:
            widget = app.query_one("#fin_plot", PlotextPlot)
            plt = widget.plt
            plt.clear_figure()

            closes = [float(x) for x in data["close"]]
            dates_safe = list(range(len(closes)))
            count = len(closes)

            plt.title(f"{symbol} ({count} candles)")
            plt.plot(dates_safe, closes, label="Close price", color="green", fillx=True)

            step = max(1, count // 10)
            ticks = dates_safe[::step]
            labels = [str(i + 1) for i in ticks]
            plt.xticks(ticks, labels)
            plt.xlabel("Day / Candle Index")

            plt.theme("dark")
            plt.yaxes(True, True)
            plt.frame(True)

            widget.refresh()
            app.notify(f"Loaded {count} points.")

        except (ValueError, AttributeError, KeyError, TypeError) as e:
            app.notify(f"Plot Error: {e}", severity="error")

    @staticmethod
    def handle_export(app) -> None:
        if not hasattr(app, "last_fin_data"):
            return app.notify("No market data to export.", severity="warning")

        def do_export(path):
            return exporter.export_financial_chart(app.last_fin_data, path)

        app._prompt_export("Save market chart", do_export)

