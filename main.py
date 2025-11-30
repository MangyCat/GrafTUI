import csv
import datetime
import os

from textual.app import App, ComposeResult, on
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import (Button, ContentSwitcher, DataTable, Footer,
                             Header, Input, RichLog, Select)
from textual_plotext import PlotextPlot

import config_manager
import exporter
import fin_controller
import sim_controller
import tools_views
import views
import workspace_manager
from file_manager import FileScreen

SHOW_LOGS = True # toggle to show logs at default, l for hide/show
#minimum size
MIN_WIDTH = 100
MIN_HEIGHT = 30

class GrafTUI(App):
    CSS_PATH = "app_styles.tcss"
    BINDINGS = [
        Binding("s", "open_settings", "Settings"),
        Binding("b", "toggle_sidebar", "Toggle Sidebar"),
        Binding("l", "toggle_logs", "Toggle Logs"),
        Binding("q", "quit_and_save", "Quit"),
    ]

    gen_data_state = {
        "columns": ["Label", "Series 1", "Series 2"],
        "rows": [["A", 10, 5], ["B", 25, 15], ["C", 15, 30]]
    }

    sidebar_hidden = False
    active_series_index = 0

    def __init__(self):
        super().__init__()
        self.app_prefs = {}
        self.last_mode = None
        self.last_data = None
        self.last_gen_data = None
        self.last_gen_mode = "line"
        self._pending_export_path = None

    # startup
    def on_mount(self) -> None:
        prefs = config_manager.load_prefs() # load saved changes
        self.theme = prefs.get("app_theme", "textual-dark")
        self.app_prefs = prefs # load prefs then push intro
        self.push_screen(views.IntroScreen()) # optimize the intro? good enough.
        # restore. explained in function.
        self._restore_workspace()

        self.call_after_refresh(self.init_plots)
        self.check_screen_size()
        self.log_msg(f"Done! Theme: {self.theme}")

    def _restore_workspace(self):
        ws = workspace_manager.load_workspace()
        if not ws: return

        # 1. bring back spreadsheet
        if "data_view" in ws and ws["data_view"].get("rows"):
            self.gen_data_state = ws["data_view"]
            self.log_msg("restored spreadsheet")

        # 2. restore financial inputs, if any...
        if "financial" in ws:
            fin = ws["financial"]
            try:
                if fin.get("symbol"):
                    self.query_one("#fin_symbol", Input).value = fin["symbol"]
                self.query_one("#fin_period", Select).value = fin.get("period", "1mo")
                self.query_one("#fin_interval", Select).value = fin.get("interval", "1d")
            except Exception:  # pragma: no cover
                pass

        # 3. electronic sim saved changes
        if "electronics" in ws:
            elec = ws["electronics"]
            try:
                if "active_circuit" in elec:
                    self.query_one("#circuit_select", Select).value = elec["active_circuit"]
                # rc
                self.query_one("#rc_mode", Select).value = elec.get("rc_mode", "step")
                self.query_one("#rc_voltage", Input).value = elec.get("rc_voltage", "5.0")
                self.query_one("#rc_freq", Input).value = elec.get("rc_freq", "1000")
                self.query_one("#rc_res", Input).value = elec.get("rc_res", "1000, 4700")
                self.query_one("#rc_cap", Input).value = elec.get("rc_cap", "100")
                #555
                self.query_one("#timer_r1", Input).value = elec.get("timer_r1", "1000")
                self.query_one("#timer_r2", Input).value = elec.get("timer_r2", "10000")
                self.query_one("#timer_c", Input).value = elec.get("timer_c", "10")
                #monostable 555
                self.query_one("#mono_r", Input).value = elec.get("mono_r", "10000")
                self.query_one("#mono_c", Input).value = elec.get("mono_c", "100")
                self.query_one("#sim_duration", Input).value = elec.get("sim_duration", "0")
            except Exception as e:
                self.log_msg(f"Store Error, electronics: {e}")

        # 4. current tab the user was in, for example markets
        if "active_tab" in ws:
            tab = ws["active_tab"]
            try:
                self.query_one("#switcher", ContentSwitcher).current = tab
                self.query(".nav-btn").remove_class("active-tab")
                btn_map = {
                    "view_elec": "nav_elec",
                    "view_general": "nav_gen",
                    "view_fin": "nav_fin"
                }
                for view_id, btn_id in btn_map.items():
                    if tab == view_id:
                        self.query_one(f"#{btn_id}").add_class("active-tab")
            except Exception:  # pragma: no cover
                pass

    def action_quit_and_save(self):
        state = {}
        try:
            state["active_tab"] = self.query_one("#switcher").current
        except Exception:  # pragma: no cover
            state["active_tab"] = "view_elec"

        try:
            state["financial"] = {
                "symbol": self.query_one("#fin_symbol").value,
                "period": self.query_one("#fin_period").value,
                "interval": self.query_one("#fin_interval").value
            }
        except Exception:  # pragma: no cover
            pass

        try:
            state["electronics"] = {
                "active_circuit": self.query_one("#circuit_select").value,

                "rc_mode": self.query_one("#rc_mode").value,
                "rc_voltage": self.query_one("#rc_voltage").value,
                "rc_freq": self.query_one("#rc_freq").value,
                "rc_res": self.query_one("#rc_res").value,
                "rc_cap": self.query_one("#rc_cap").value,

                "timer_r1": self.query_one("#timer_r1").value,
                "timer_r2": self.query_one("#timer_r2").value,
                "timer_c": self.query_one("#timer_c").value,

                "mono_r": self.query_one("#mono_r").value,
                "mono_c": self.query_one("#mono_c").value,

                "sim_duration": self.query_one("#sim_duration").value
            }
        except Exception:  # pragma: no cover
            pass

        state["data_view"] = self.gen_data_state # data state
        workspace_manager.save_workspace(state)
        self.exit() # quit

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(classes="nav-bar"): # top ribbon
            yield Button("ELECTRONICS", id="nav_elec", classes="nav-btn active-tab")
            yield Button("DATA VIEW", id="nav_gen", classes="nav-btn")
            yield Button("MARKETS", id="nav_fin", classes="nav-btn")
            yield Button("VIEW", id="btn_toggle_side", classes="nav-btn right-dock")

        with ContentSwitcher(initial="view_elec", id="switcher"): # area
            yield views.ElectronicsView(id="view_elec")
            yield views.GeneralPlotterView(id="view_general")
            yield views.FinancialView(id="view_fin")

        yield Footer()

    def on_resize(self, event) -> None:
        self.check_screen_size() # alarm, must not be smaller than constants defined at top

    # --- UI ACTIONS ---
    def check_screen_size(self): # check if screen is too small
        is_small = self.size.width < MIN_WIDTH or self.size.height < MIN_HEIGHT
        if is_small and not isinstance(self.screen, views.TooSmallScreen):
            self.push_screen(views.TooSmallScreen()) # push warning menu
        elif not is_small and isinstance(self.screen, views.TooSmallScreen):
            self.pop_screen() # pop screen

    def action_toggle_sidebar(self) -> None: # toggle sidebar
        self.sidebar_hidden = not self.sidebar_hidden
        for sidebar in self.query(".sidebar"):
            sidebar.set_class(not self.sidebar_hidden, "visible")
            sidebar.set_class(self.sidebar_hidden, "hidden")

    def action_toggle_logs(self) -> None:
        try:
            log = self.query_one("#log_container")
            if log.has_class("hidden"):
                log.remove_class("hidden")
            else:
                log.add_class("hidden")
        except Exception:  # pragma: no cover
            pass

    def action_open_settings(self) -> None:
        def apply_settings(new_prefs: dict | None) -> None:
            if new_prefs:
                config_manager.save_prefs(new_prefs)
                self.app_prefs = new_prefs
                if "app_theme" in new_prefs:
                    self.theme = new_prefs["app_theme"] # theme change
                    self.init_plots() # initialize plots, to take effect
        self.push_screen(views.SettingsScreen(self.app_prefs), apply_settings)

    @on(Button.Pressed, "#btn_toggle_side")
    def manual_toggle_side(self):
        self.action_toggle_sidebar()

    def log_msg(self, msg: str) -> None:
        if not SHOW_LOGS:
            return
        try:
            log = self.query_one("#system_log", RichLog)
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            log.write(f"[{ts}] {msg}")
        except Exception:  # pragma: no cover
            try:
                log = self.query_one("#fin_log", RichLog)
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                log.write(f"[{ts}] {msg}")
            except Exception:  # pragma: no cover
                pass

    def init_plots(self) -> None:
        try:
            for pid in ["#main_plot", "#gen_plot", "#fin_plot"]:
                try:
                    self.query_one(pid, PlotextPlot).refresh()
                except Exception:  # pragma: no cover
                    pass
        except Exception:  # pragma: no cover
            pass

    @on(Button.Pressed)
    def handle_nav(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_open_editor":
            self.push_screen(views.DataEditorScreen(self.gen_data_state))
            return

        if bid in ["nav_elec", "nav_gen", "nav_fin"]:
            targets = {
                "nav_elec": "view_elec",
                "nav_gen": "view_general",
                "nav_fin": "view_fin"
            }
            self.query_one("#switcher", ContentSwitcher).current = targets[bid]
            self.query(".nav-btn").remove_class("active-tab")
            event.button.add_class("active-tab")

    # stonks
    @on(Button.Pressed, "#btn_fin_fetch")
    def run_financial_fetch(self):
        fin_controller.FinancialController.update_market_view(self)

    @on(Button.Pressed, "#btn_fin_export")
    def export_financial(self):
        fin_controller.FinancialController.handle_export(self)

    @on(Button.Pressed, "#btn_fin_search")
    def open_ticker_search(self):
        def on_select(symbol: str | None) -> None:
            if symbol:
                try:
                    self.query_one("#fin_symbol", Input).value = symbol
                    self.notify(f"Selected: {symbol}")
                except Exception as e:
                    self.notify(f"interface error: {e}", severity="error")
        self.push_screen(views.TickerSearchScreen(), on_select)

    # series control, pie specific
    @on(Select.Changed, "#gen_type")
    def on_chart_type_changed(self, event: Select.Changed):
        try:
            btn_cycle = self.query_one("#btn_cycle_series")
            btn_export_all = self.query_one("#btn_export_all")
            series_count = max(1, len(self.gen_data_state.get("columns", [])) - 1)
            is_multi = series_count > 1
            is_pie = event.value == "pie"
            if is_pie and is_multi:
                btn_cycle.remove_class("hidden")
                btn_export_all.remove_class("hidden")
            else:
                btn_cycle.add_class("hidden")
                btn_export_all.add_class("hidden")
        except Exception:  # pragma: no cover
            pass

    @on(Button.Pressed, "#btn_cycle_series") #cycles,
    def on_cycle_series(self): # ONLY FOR 3.14159 CHART!!!!
        cols = self.gen_data_state.get("columns", [])
        series_count = max(1, len(cols) - 1)
        self.active_series_index = (self.active_series_index + 1) % series_count
        self.render_gen()

    # data editing
    def _update_table(self, op="add_row", col_name=None):
        try:
            table = self.screen.query_one("#editor_table", DataTable)
            ts = datetime.datetime.now().timestamp()

            if op == "add_row":
                key = f"r_{table.row_count}_{ts}"
                vals = ["New"] + ["0.0"] * (len(table.columns)-1)
                table.add_row(*vals, key=key)
            elif op == "add_col" and col_name: #e
                key = f"c_{col_name}_{ts}"
                table.add_column(col_name, key=key, width=15) #a
                for rk in table.rows:
                    table.update_cell(rk, key, "0.0")#c
            elif op == "clear":
                table.clear() #d
        except Exception as e:
            self.log_msg(f"editor error {e}")

    @on(Button.Pressed, "#btn_edit_add_row")
    def edit_add_row(self):
        self._update_table("add_row")

    @on(Button.Pressed, "#btn_edit_add_col")
    def edit_add_col(self):
        self.push_screen(views.InputScreen("Series name", "New series name"),
                         lambda n: self._update_table("add_col", n) if n else None)

    @on(Button.Pressed, "#btn_edit_clear")
    def edit_clear(self):
        self._update_table("clear")

    @on(Button.Pressed, "#btn_edit_import")
    def edit_import_csv(self):
        """Import CSV with format detection."""
        def on_path(path):
            if not path or not os.path.exists(path):
                if path:
                    self.log_msg(f"file not found: {path}")
                return
            try:
                with open(path, 'r', encoding='utf-8-sig') as f:
                    sample = f.read(1024)
                    f.seek(0)
                    try:
                        dialect = csv.Sniffer().sniff(sample)
                    except (csv.Error, Exception):
                        dialect = csv.excel
                    if dialect.delimiter not in [',', ';', '\t']:
                        dialect.delimiter = ','
                    reader = csv.reader(f, dialect)
                    raw_rows = list(reader)

                if not raw_rows: return

                looks_transposed = False
                if len(raw_rows) > 0 and len(raw_rows[0]) > 1:
                    try:
                        float(raw_rows[0][1])
                        looks_transposed = True
                    except (ValueError, IndexError):
                        looks_transposed = False

                def load_data(do_transpose): # transpose logic, rows become columns, columns become rows, easier said than done.
                    table = self.screen.query_one("#editor_table", DataTable)
                    table.clear(columns=True)
                    ts = int(datetime.datetime.now().timestamp() * 1000)

                    if do_transpose:
                        self.log_msg("tranposing!")
                        series_names = [r[0] for r in raw_rows]
                        max_len = max(len(r) for r in raw_rows)
                        data_matrix = []
                        for r in raw_rows:
                            row_data = r[1:] + ['0'] * (max_len - len(r))
                            data_matrix.append(row_data)

                        transposed = list(zip(*data_matrix))
                        headers = ["Index"] + series_names
                        for i, h in enumerate(headers):
                            table.add_column(str(h), key=f"col_{i}_{ts}")
                        for i, r in enumerate(transposed):
                            full_row = [str(i+1)] + list(r)
                            table.add_row(*full_row, key=f"row_{i}_{ts}")
                    else:
                        self.log_msg("loading standard csv")
                        headers = raw_rows[0]
                        for i, h in enumerate(headers):
                            table.add_column(str(h), key=f"col_{i}_{ts}")
                        for i, r in enumerate(raw_rows[1:]):
                            table.add_row(*r, key=f"row_{i}_{ts}")

                    self.log_msg(f"imported {path}")

                if looks_transposed:
                    self.push_screen(views.TransposePromptScreen(), load_data)
                else:
                    load_data(False)

            except (IOError, OSError, csv.Error) as e:
                self.log_msg(f"csv error: {e}")

        self.push_screen(FileScreen(title="Import CSV file"), on_path)

    @on(Button.Pressed, "#btn_edit_export")
    def edit_export_csv(self):
        def on_path(path):
            if not path:
                return
            if not path.lower().endswith('.csv'):
                path += ".csv"
            try:
                table = self.screen.query_one("#editor_table", DataTable)
                cols = list(table.columns.values())
                headers = [c.label.plain for c in cols]
                rows = [[table.get_cell(rk, c.key) for c in cols]
                        for rk in table.rows]

                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(rows)

                self.log_msg(f"Exported CSV: {path}")
                self.notify(f"Saved to {path}")
            except Exception as e:
                self.log_msg(f"Export Failed: {e}")

        self.push_screen(FileScreen(title="Export CSV As"), on_path)

    @on(Button.Pressed, "#btn_edit_done")
    def edit_done(self):
        try:
            table = self.screen.query_one("#editor_table", DataTable)
            cols = list(table.columns.values())
            rows = [[table.get_cell(rk, c.key) for c in cols]
                    for rk in table.rows]
            self.gen_data_state = {"columns": [c.label.plain for c in cols],
                                   "rows": rows}
            self.pop_screen()
            self.log_msg(f"Data Saved: {len(rows)} rows.")
        except Exception as e:
            self.log_msg(f"[red]Save Error: {e}[/red]")
    # tools 'n utilities
    @on(Button.Pressed, "#btn_tool_resistor")
    def open_resistor_tool(self):
        self.push_screen(tools_views.ResistorScreen())
    @on(Button.Pressed, "#btn_tool_ohm")
    def open_ohms_law(self):
        self.push_screen(tools_views.OhmsLawScreen())
    @on(DataTable.CellSelected, "#editor_table")
    def edit_table_cell(self, event: DataTable.CellSelected):
        def on_input(val):
            if val is not None:
                try:
                    self.screen.query_one("#editor_table", DataTable).update_cell_at(
                        event.coordinate, val)
                except (AttributeError, NameError):
                    pass
        self.push_screen(views.InputScreen(str(event.value), "Edit Cell"), on_input)

    # simulating
    @on(Select.Changed, "#circuit_select")
    def handle_circuit_change(self, event: Select.Changed):
        switcher = self.query_one("#sidebar_switcher", ContentSwitcher)
        lookup = {
            "circuit_rc": "controls_rc",
            "circuit_555": "controls_555",
            "circuit_555_mono": "controls_555_mono"
        }
        if event.value in lookup:
            switcher.current = lookup[event.value]

    @on(Button.Pressed, "#btn_sim_run")
    def run_simulation(self):
        active = self.query_one("#circuit_select", Select).value
        msg = ""
        if active == "circuit_rc":
            msg = sim_controller.SimulationController.run_rc_filter(self)
        elif active == "circuit_555":
            msg = sim_controller.SimulationController.run_555_astable(self)
        elif active == "circuit_555_mono":
            msg = (sim_controller.SimulationController
                   .run_555_monostable(self))
        self.query_one("#main_plot", PlotextPlot).refresh()
        if msg:
            self.log_msg(msg)

    @on(Button.Pressed, "#btn_gen_render")
    def render_gen(self):
        msg = sim_controller.SimulationController.run_general_plot(self)
        self.query_one("#gen_plot", PlotextPlot).refresh()
        if msg:
            self.log_msg(msg)

    # handle exporting
    def _prompt_export(self, title, export_callback):
        """Export dialog handler."""
        def on_path(path):
            if not path:
                return
            if not path.lower().endswith('.png'):
                path += ".png"
            try:
                result = export_callback(path)
                if "Error" in result:
                    self.log_msg(result)
                else:
                    self.log_msg(f"Exported: {result}")
                    self.notify(f"Saved to {result}")
            except (OSError, IOError) as e:
                self.log_msg(f"export error: {e}")
        self.push_screen(FileScreen(title=title), on_path)

    @on(Button.Pressed, "#btn_export")
    def export_data(self):
        if not hasattr(self, "last_data"):
            return self.log_msg("No simulation data.")

        def do_export(path):
            if self.last_mode == "rc_square":
                return exporter.export_square_wave(self.last_data, path)
            if self.last_mode == "rc_step":
                return exporter.export_rc_transient(self.last_data, path)
            if self.last_mode == "555_astable":
                return exporter.export_555_astable(self.last_data, path)
            if self.last_mode == "555_mono":
                return exporter.export_555_monostable(self.last_data, path)
            return "Mode not supported for export."

        self._prompt_export("Save electronics plot", do_export)

    @on(Button.Pressed, "#btn_gen_export")
    def export_gen(self):
        if not hasattr(self, "last_gen_data"):
            return self.log_msg("no data plot.")

        def export_callback(path):
            return exporter.export_generic_plot(
                self.last_gen_data,
                mode=getattr(self, "last_gen_mode", "line"),
                filename=path,
                active_index=self.active_series_index
            )

        self._prompt_export("Save data plot", export_callback)

    @on(Button.Pressed, "#btn_export_all")
    def on_export_all_click(self):
        def on_mode_selected(mode):
            if not mode:
                return
            path = getattr(self, "_pending_export_path", None)
            if not path:
                return

            if not hasattr(self, "last_gen_data"):
                self.log_msg("No data to export.")
                return

            base_path = os.path.splitext(path)[0]
            outcome = exporter.export_multi_series(self.last_gen_data, base_path, mode)
            if "Error" in outcome:
                self.log_msg(outcome)
            else:
                self.log_msg(f"Export successful: {outcome}")
                self.notify(f"Exported: {outcome}")

        def on_file_selected(path):
            if not path:
                return
            self._pending_export_path = path
            self.push_screen(views.ExportModeScreen(), on_mode_selected)

        self.push_screen(FileScreen(title="Choose base filename"), on_file_selected)

if __name__ == "__main__":
    GrafTUI().run()
