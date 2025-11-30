import math
import random

from textual.widgets import Input, Select, Static
from textual_plotext import PlotextPlot

import simulators
import statistics_engine
#tau = R * C
#0.693 = time to half voltage / (r times c)
class SimulationController: # handles logic
    @staticmethod
    def _get_graph_theme(app_theme_name: str) -> str:
        if app_theme_name == "matrix":
            return "matrix"
        return "pro"

    @staticmethod
    def _prepare_plot(app, title: str):
        widget = app.query_one("#main_plot", PlotextPlot)
        plt = widget.plt

        current_app_theme = getattr(app, "theme", "textual-dark")
        graph_theme = SimulationController._get_graph_theme(current_app_theme)

        prefs = getattr(app, "app_prefs", {})
        line_col = prefs.get("graph_line_color", "yellow")

        plt.clear_figure()
        plt.theme(graph_theme)
        plt.title(title)

        return plt, line_col

    @staticmethod
    def _update_elec_stats(app, data, mode):
        text = statistics_engine.StatsEngine.analyze_simulation(data, mode)
        try:
            app.query_one("#stats_display_elec", Static).update(text)
        except (AttributeError, NameError):
            pass

    @staticmethod
    def run_rc_filter(app):
        try:
            v_in = float(app.query_one("#rc_voltage", Input).value)
            c_uf = float(app.query_one("#rc_cap", Input).value)
            mode = app.query_one("#rc_mode", Select).value
            try:
                dur = float(app.query_one("#sim_duration", Input).value)
            except (ValueError, AttributeError):
                dur = 0.0

            if mode == "step":
                raw = app.query_one("#rc_res", Input).value
                res = [float(x) for x in raw.split(',') if x.strip()]
                if not res:
                    return "No resistors." # early exit
                data = simulators.calculate_rc_transient(v_in, c_uf, res, dur)
                plt, _ = SimulationController._prepare_plot(app, "RC Step Response")
                for c in data["curves"]:
                    plt.plot(data["time"], c["voltage"], label=f"R={c['R']}Ω")
                app.last_data = data
                app.last_mode = "rc_step"

                # Stats
                SimulationController._update_elec_stats(app, data, "rc_step")

                return f"RC Step: {len(res)} curves."
            elif mode == "square":
                freq = float(app.query_one("#rc_freq", Input).value)
                res = float(app.query_one("#rc_res", Input).value.split(',')[0])
                data = simulators.calculate_square_wave_response(v_in, c_uf, res, freq)
                plt, col = SimulationController._prepare_plot(app, f"RC Filter ({freq}Hz)")
                plt.plot(data["time"], data["input_wave"], label="In", color="green")
                plt.plot(data["time"], data["output_wave"], label="Out", color=col)
                app.last_data = data; app.last_mode = "rc_square"

                # Stats
                SimulationController._update_elec_stats(app, data, "rc_square")

                return f"RC Square: Tau={data['tau']:.4f}s"
        except Exception as e: return f"Error: {e}"

    @staticmethod
    def run_555_astable(app):
        try:
            r1 = float(app.query_one("#timer_r1", Input).value)
            r2 = float(app.query_one("#timer_r2", Input).value)
            c = float(app.query_one("#timer_c", Input).value)
            try:
                dur = float(app.query_one("#sim_duration", Input).value)
            except (ValueError, AttributeError):
                dur = 0.0
            data = simulators.calculate_555_astable(r1, r2, c, dur)
            plt, col = SimulationController._prepare_plot(
                app, f"555 Astable (Freq={data['freq']:.1f}Hz)")
            plt.plot(data["time"], data["voltage"], label="Output", color=col)
            app.last_data = data
            app.last_mode = "555_astable"

            SimulationController._update_elec_stats(app, data, "555_astable")

            return f"Freq={data['freq']:.2f}Hz"
        except (ValueError, KeyError, AttributeError) as e:
            return f"Error: {e}"

    @staticmethod
    def run_555_monostable(app):
        try:
            r = float(app.query_one("#mono_r", Input).value)
            c = float(app.query_one("#mono_c", Input).value)
            try:
                dur = float(app.query_one("#sim_duration", Input).value)
            except (ValueError, AttributeError):
                dur = 0.0
            data = simulators.calculate_555_monostable(r, c, dur)
            plt, col = SimulationController._prepare_plot(
                app, f"555 Monostable (R={r}Ω, C={c}µF)")
            plt.plot(data["time"], data["trigger"], label="Trigger", color="green")
            plt.plot(data["time"], data["output"], label="Output", color=col)
            plt.plot(data["time"], data["cap_voltage"], label="Capacitor",
                     color="blue")
            app.last_data = data
            app.last_mode = "555_mono"

            SimulationController._update_elec_stats(app, data, "555_mono")

            return f"Pulse: {data['pulse_width']:.4f}s"
        except (ValueError, KeyError, AttributeError) as e:
            return f"Error: {e}"

    @staticmethod
    def run_general_plot(app):
        try:
            data_state = getattr(app, "gen_data_state", {})
            cols = data_state.get("columns", [])
            rows = data_state.get("rows", [])

            if len(cols) < 2 or not rows: return "No data."

            labels = [str(r[0]) for r in rows]
            series_names = cols[1:]
            series_data = []
            for col_idx in range(1, len(cols)):
                col_vals = []
                for r in rows:
                    try:
                        val = float(r[col_idx])
                    except (ValueError, IndexError, TypeError):
                        val = 0.0
                    col_vals.append(val)
                series_data.append(col_vals)

            app.last_gen_data = {"labels": labels, "series": series_data, "names": series_names}
            app.last_gen_mode = app.query_one("#gen_type", Select).value
            mode = app.last_gen_mode

            # stats update
            try:
                active_idx = getattr(app, "active_series_index", 0)
                if active_idx >= len(series_data): active_idx = 0

                if series_data:
                    current_vals = series_data[active_idx]
                    s_name = series_names[active_idx]

                    # Use modular engine
                    stats_text = statistics_engine.StatsEngine.calculate_generic(current_vals, s_name)
                else:
                    stats_text = "No data"

                app.query_one("#stats_display", Static).update(stats_text)
            except (ValueError, KeyError, AttributeError):
                app.query_one("#stats_display", Static).update("stats error")
            # -------------------------

            widget = app.query_one("#gen_plot", PlotextPlot)
            plt = widget.plt

            current_app_theme = getattr(app, "theme", "textual-dark")
            graph_theme = SimulationController._get_graph_theme(current_app_theme)
            plt.clear_figure()
            plt.theme(graph_theme)
            plt.title("Data view")

            active_idx = getattr(app, "active_series_index", 0)
            if active_idx >= len(series_data): active_idx = 0

            colors = ["red", "green", "yellow", "blue", "magenta", "cyan", "white"]

            if mode == "pie": # plotting with dots. normal pie is hard-impossible in plotext
                if series_data:
                    vals = [abs(x) for x in series_data[active_idx]]
                    name = series_names[active_idx]

                    total = sum(vals)
                    if total > 0:
                        angles = []
                        current = 0
                        for v in vals:
                            share = (v / total) * 360
                            angles.append((current, current + share))
                            current += share

                        points_x = [[] for _ in vals]
                        points_y = [[] for _ in vals]

                        for _ in range(2000):
                            r = math.sqrt(random.random()) # EVERY PREVIEW will be different, due to added noise.
                            theta = random.random() * 360
                            slice_idx = 0
                            for i, (start, end) in enumerate(angles):
                                if start <= theta < end:
                                    slice_idx = i
                                    break
                            x = r * math.cos(math.radians(theta)) * 1.8
                            y = r * math.sin(math.radians(theta))
                            points_x[slice_idx].append(x)
                            points_y[slice_idx].append(y)

                        for i, _ in enumerate(vals): # finish up
                            label_txt = f"{labels[i]}" if i < len(labels) else ""
                            col = colors[i % len(colors)]
                            if points_x[i]:
                                plt.scatter(points_x[i], points_y[i], label=label_txt, color=col)

                        plt.title(f"{name} ({active_idx + 1}/{len(series_data)})")
                        plt.plotsize(None, None)
                        plt.xaxes(False, False)
                        plt.yaxes(False, False)
                        plt.frame(False)

            else: # other plot types (they take up less lines than the whole pie function)
                if mode == "bar":
                    try:
                        plt.multiple_bar(labels, series_data)
                    except (ValueError, AttributeError):
                        plt.multiple_bar(labels, series_data)
                elif mode == "area":
                    for i, s in enumerate(series_data):
                        col = colors[i % len(colors)]
                        try:
                            plt.plot(s, label=series_names[i], fillx=True, color=col)
                        except (ValueError, AttributeError):
                            plt.plot(s, label=series_names[i], color=col)
                    plt.xticks(range(len(labels)), labels)
                elif mode == "scatter":
                    for i, s in enumerate(series_data):
                        col = colors[i % len(colors)]
                        plt.scatter(s, label=series_names[i], color=col)
                    plt.xticks(range(len(labels)), labels)
                else:
                    for i, s in enumerate(series_data):
                        col = colors[i % len(colors)]
                        plt.plot(s, label=series_names[i], color=col)
                    plt.xticks(range(len(labels)), labels)

            widget.refresh()
            return f"Rendered {mode}."
        except (ValueError, KeyError, AttributeError, IndexError) as e:
            return f"Render error: {e}"

