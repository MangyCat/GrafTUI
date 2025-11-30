from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import ModalScreen, Screen
from textual.widgets import (Button, ContentSwitcher, DataTable, Footer,
                             Header, Input, Label, RadioButton, RadioSet,
                             RichLog, Select, Static)
from textual_plotext import PlotextPlot
title_art = r"""  ________              ____________________ ___.___ 
 /  _____/___________ _/ ____\__    ___/    |   \   |
/   \  __\_  __ \__  \\   __\  |    |  |    |   /   |
\    \_\  \  | \// __ \|  |    |    |  |    |  /|   |
 \______  /__|  (____  /__|    |____|  |______/ |___|
        \/           \/                              
"""
class IntroScreen(Screen):

    def compose(self) -> ComposeResult:
        # Using raw string for the art to avoid warnings, moved to top for effortless changing

        with Container(id="intro_container"):
            yield Label(title_art, id="intro_title")
            yield Label("Loading", id="intro_status")

    def on_mount(self) -> None:
        self.step = 0
        self.messages = [ # silly messages
            "Loading.",
            "More loading..",
            "Just a bit more loading...",
            "Done!"
            #"Almost done....",
            #"Just kidding, still loading.....",
            #"Preparing awesomeness......",
            #"Finalizing........",
            #uncomment for maximum inpatience :3
        ]
        self.update_timer = self.set_interval(0.6, self.update_status)

    def update_status(self) -> None:
        if self.step < len(self.messages):
            self.query_one("#intro_status").update(self.messages[self.step])
            self.step += 1
        else:
            self.update_timer.stop()
            self.app.pop_screen()

class TooSmallScreen(Screen):
    def compose(self) -> ComposeResult:
        with Container(id="warning-box"):
            yield Label("Terminal too small!", classes="warning-title")
            yield Label("Please resize to atleast 100x30 columns 🥺", classes="warning-text")

class SettingsScreen(ModalScreen):
    def __init__(self, current_prefs: dict = None):
        super().__init__()
        self.current_prefs = current_prefs or {}

    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Label("Application settings", classes="group-title")

            with Container(classes="setting-row"):
                yield Label("App theme", classes="setting-label")
                yield Select([], id="pref_app_theme", classes="setting-input")

            with Container(classes="setting-row"):
                yield Label("Default line color", classes="setting-label")
                colors = [("Yellow", "yellow"), ("Cyan", "cyan"),
                          ("Red", "red"), ("Green", "green")]
                yield Select(colors, id="pref_line_color",
                             classes="setting-input", value="yellow")

            with Horizontal(classes="modal-btn-row"):
                yield Button("DONE", id="btn_save", classes="btn-primary")

    def on_mount(self) -> None:
        try:
            available_themes = list(self.app.available_themes.keys())
            available_themes.sort()
            theme_options = [(t.replace("-", " ").title(), t)
                             for t in available_themes]

            theme_select = self.query_one("#pref_app_theme", Select)
            theme_select.set_options(theme_options)

            current_theme = self.current_prefs.get("app_theme", "textual-dark")
            theme_select.value = (current_theme if current_theme in available_themes
                                   else "textual-dark")
        except Exception:  # pragma: no cover
            pass

        if self.current_prefs:
            try:
                line = self.current_prefs.get("graph_line_color", "yellow")
                self.query_one("#pref_line_color", Select).value = line
            except Exception:  # pragma: no cover
                pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            line_color = self.query_one("#pref_line_color", Select).value
            theme = self.query_one("#pref_app_theme", Select).value
            new_prefs = {"graph_line_color": line_color, "app_theme": theme}
            self.dismiss(new_prefs)



class InputScreen(ModalScreen):
    def __init__(self, initial_value: str = "", title: str = "Edit value") -> None:
        super().__init__()
        self.initial_value = initial_value
        self.title = title

    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Label(self.title, classes="group-title")
            yield Input(id="edit_input", value=self.initial_value)
            yield Button("OK", variant="primary", id="btn_ok")

    def on_mount(self) -> None:
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(self.query_one(Input).value)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_ok":
            self.dismiss(self.query_one(Input).value)

class TransposePromptScreen(ModalScreen): # ask for transposing, known to happen to improper csvs
    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Label("IMPORT OPTIONS", classes="group-title")
            yield Label("This file looks like it has series in rows instead of columns.")
            yield Label("Would you like to transpose (swap rows/cols)?")

            with Horizontal(classes="modal-btn-row"):
                yield Button("NO (Keep as is)", id="btn_no", classes="btn-secondary")
                yield Button("YES (Transpose)", id="btn_yes", classes="btn-primary")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_yes": self.dismiss(True)
        else: self.dismiss(False)

class DataEditorScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Close")]
    def __init__(self, data_state: dict): super().__init__(); self.data_state = data_state

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="editor-container"): # horizontal, tools 
            with Horizontal(classes="editor-toolbar"):
                yield Button("Add row", id="btn_edit_add_row", classes="btn-secondary")
                yield Button("Add series", id="btn_edit_add_col", classes="btn-secondary")
                yield Button("Import CSV", id="btn_edit_import", classes="btn-secondary")
                yield Button("Export CSV", id="btn_edit_export", classes="btn-secondary")
                yield Button("Clear", id="btn_edit_clear", classes="btn-secondary")
                yield Button("Save & Return", id="btn_edit_done", classes="btn-primary")
            yield DataTable(id="editor_table")
        yield Footer()

    def on_mount(self):
        table = self.query_one(DataTable)
        table.cursor_type = "cell"
        table.clear(columns=True)
        for col in self.data_state.get("columns", ["Label", "Value"]):
            table.add_column(col, key=f"col_{col}")
        for i, row in enumerate(self.data_state.get("rows", [])):
            table.add_row(*row, key=f"row_{i}")

class ExportModeScreen(ModalScreen): # exporting for pie chart
    BINDINGS = [Binding("escape", "cancel", "Cancel")] # keybinds as is
    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Label("EXPORT FORMAT", classes="group-title")
            with RadioSet(id="export_mode"):
                yield RadioButton("Combined (one image)", value=True, id="mode_combined")
                yield RadioButton("Separate files (_1, _2...)", id="mode_separate")
            with Horizontal(classes="modal-btn-row"):
                yield Button("CONFIRM", id="btn_confirm", classes="btn-primary")

    def action_cancel(self): self.dismiss(None)
    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_confirm":
            is_combined = self.query_one("#mode_combined").value
            mode = "combined" if is_combined else "separate"
            self.dismiss(mode)

class TickerSearchScreen(ModalScreen): # method for searching tickers. works fairly well.
    BINDINGS = [("escape", "app.pop_screen", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container(id="settings_dialog"):
            yield Label("TICKER LOOKUP", classes="group-title")
            yield Label("Company name or ticker")

            # Use explicit horizontal box but manual styling on widgets
            with Horizontal(classes="setting-row"):
                inp = Input(placeholder="e.g. Intel, Nvidia", id="search_query")
                inp.styles.width = "1fr"
                inp.styles.margin_right = 1
                yield inp

                btn = Button("SEARCH", id="btn_do_search", classes="btn-primary", variant="primary")
                btn.styles.width = "auto"
                yield btn

            yield Label("Results", classes="group-title")
            yield DataTable(id="search_results", cursor_type="row")

            with Horizontal(classes="modal-btn-row"):
                yield Button("CANCEL", id="btn_cancel", variant="error")

    def on_mount(self):
        table = self.query_one(DataTable)
        table.add_columns("Symbol", "Name", "Type", "Exchange")
        self.query_one("#search_query").focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn_cancel":
            self.dismiss(None)
        elif event.button.id == "btn_do_search":
            self._do_search()

    def on_input_submitted(self, event: Input.Submitted):
        self._do_search()

    def _do_search(self):
        query = self.query_one("#search_query").value
        if not query: return

        import financial_manager
        results = financial_manager.FinancialManager.search_tickers(query) # search tickers function in financial_manager.py

        table = self.query_one(DataTable)
        table.clear()
        if results:
            for r in results:
                table.add_row(*r)
        else:
            table.add_row("N/A", "No results found", "", "") # likely misspelled or very niche ticker

    def on_data_table_row_selected(self, event: DataTable.RowSelected):
        try:
            row = self.query_one(DataTable).get_row(event.row_key)
            symbol = row[0]
            if symbol not in ("Error", "N/A"):
                self.dismiss(symbol)
        except Exception:  # pragma: no cover
            self.dismiss(None)

# view classes

class ElectronicsView(Container):
    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="sidebar"):
            yield Label("ELECTRONICS", classes="sidebar-header")

            # utils 29/11/25
            with Container(classes="control-group"):
                yield Label("UTILITIES", classes="group-title")
                yield Button("RESISTOR CALCULATOR", id="btn_tool_resistor", classes="btn-secondary")
                yield Button("OHM'S LAW CALC", id="btn_tool_ohm", classes="btn-secondary")
            with Container(classes="control-group"):
                yield Label("ACTIVE CIRCUIT", classes="group-title")
                circuits = [("RC Filter / circuit", "circuit_rc"),
                            ("555 Timer (astable)", "circuit_555"),
                            ("555 Timer (monostable)", "circuit_555_mono")]
                yield Select(circuits, value="circuit_rc",
                             id="circuit_select")

            with ContentSwitcher(initial="controls_rc", id="sidebar_switcher"):
                with Container(id="controls_rc"):
                    with Container(classes="control-group"):
                        yield Label("SOURCE CONFIG", classes="group-title")
                        yield Label("Waveform type")
                        waveforms = [("Step (DC)", "step"),
                                     ("Square (AC)", "square")]
                        yield Select(waveforms, value="step",
                                     id="rc_mode")
                        yield Label("Voltage (V)")
                        yield Input(value="5.0", id="rc_voltage", type="number")
                        yield Label("Freq (Hz) [AC Mode]")
                        yield Input(value="1000", id="rc_freq", type="number")

                    with Container(classes="control-group"):
                        yield Label("COMPONENTS", classes="group-title")
                        yield Label("Resistors (Ω)")
                        yield Input(value="1000, 4700", id="rc_res", type="text")
                        yield Label("Capacitor (µF)")
                        yield Input(value="100", id="rc_cap", type="number")

                with Container(id="controls_555"):
                    with Container(classes="control-group"):
                        yield Label("ASTABLE CONFIG", classes="group-title")
                        yield Label("R1 (Ω)")
                        yield Input(value="1000", id="timer_r1", type="number")
                        yield Label("R2 (Ω)")
                        yield Input(value="10000", id="timer_r2", type="number")
                        yield Label("C (µF)")
                        yield Input(value="10", id="timer_c", type="number")

                with Container(id="controls_555_mono"):
                    with Container(classes="control-group"):
                        yield Label("MONOSTABLE CONFIG", classes="group-title")
                        yield Label("R (Ω)")
                        yield Input(value="10000", id="mono_r", type="number")
                        yield Label("C (µF)")
                        yield Input(value="100", id="mono_c", type="number")

            with Container(classes="control-group"):
                yield Label("SIM STATS", classes="group-title")
                yield Static("Run simulation...", id="stats_display_elec")

            with Container(classes="control-group"):
                yield Label("SIMULATION", classes="group-title")
                yield Label("Duration limit (s)")
                yield Input(value="0", id="sim_duration", type="number")
                yield Button("RUN SIMULATION", classes="btn-primary", id="btn_sim_run")
                yield Button("EXPORT DATA", classes="btn-secondary", id="btn_export")

        with Container(classes="display-area"):
            with Container(classes="graph-frame"):
                yield PlotextPlot(id="main_plot")
            with Container(classes="log-frame", id="log_container"):
                yield Label("SYSTEM LOG", classes="panel-label")
                yield RichLog(id="system_log", highlight=True, markup=True)


class GeneralPlotterView(Container): # plotter view, for data. 
    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="sidebar"):
            yield Label("DATA PLOTTER", classes="sidebar-header")

            with Container(classes="control-group"):
                yield Label("CONFIG", classes="group-title")
                yield Label("Chart Type")
                chart_types = [("Line", "line"), ("Bar", "bar"),
                               ("Scatter", "scatter"), ("Area", "area"),
                               ("Pie", "pie")]
                yield Select(chart_types, value="line",
                             id="gen_type")

            with Container(classes="control-group"):
                yield Label("DATA SOURCE", classes="group-title")
                yield Button("OPEN EDITOR", id="btn_open_editor", classes="btn-primary")
                yield Button("CYCLE SERIES >",
                             id="btn_cycle_series",
                             classes="btn-secondary hidden")

            with Container(classes="control-group"):
                yield Label("STATISTICS", classes="group-title")
                yield Static("No data loaded", id="stats_display")

            with Container(classes="control-group"):
                yield Label("ACTIONS", classes="group-title")
                yield Button("RENDER VIEW", classes="btn-primary", id="btn_gen_render")
                yield Button("EXPORT PLOT", classes="btn-secondary",
                             id="btn_gen_export")
                yield Button("EXPORT ALL SERIES", # pi only
                             classes="btn-secondary hidden",
                             id="btn_export_all")

        with Container(classes="display-area"):
            with Container(classes="graph-frame"):
                yield PlotextPlot(id="gen_plot")


class FinancialView(Container):
    def compose(self) -> ComposeResult:
        with VerticalScroll(classes="sidebar"):
            yield Label("MARKET TERMINAL", classes="sidebar-header")

            with Container(classes="control-group"):
                yield Label("SEARCH", classes="group-title")
                yield Label("Ticker symbol")

                # UPDATED: Removed Horizontal() wrapper to remove gap
                yield Input(placeholder="e.g. NVDA", id="fin_symbol")
                yield Button("LOOKUP SYMBOL", id="btn_fin_search", classes="btn-secondary")

                yield Label("Time period")
                periods = [("1 Day", "1d"), ("5 Days", "5d"),
                           ("1-Month", "1mo"), ("3-Month", "3mo"),
                           ("1-Year", "1y"), ("Maximum", "max")]
                yield Select(periods, value="1mo",
                             id="fin_period")

                yield Label("Interval")
                intervals = [("1 Minute", "1m"), ("15 Minutes", "15m"),
                             ("1 Hour", "1h"), ("1 Day", "1d")]
                yield Select(intervals, value="1d",
                             id="fin_interval")

                yield Button("FETCH DATA", id="btn_fin_fetch", classes="btn-primary")

            with Container(classes="control-group"):
                yield Label("MARKET STATS", classes="group-title")
                yield Static("Enter ticker...", id="stats_display_fin")
                yield Button("EXPORT CHART", id="btn_fin_export", classes="btn-secondary")

        with Container(classes="display-area"):
            with Container(classes="graph-frame"):
                yield PlotextPlot(id="fin_plot")
