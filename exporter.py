import datetime
import math

import numpy as np

# lazy loaded matplotlib

def get_default_filename(prefix: str) -> str: #should not be used much
    return f"{prefix}_{datetime.datetime.now().strftime('%H%M%S')}.png"

def _setup_and_save(filename: str, title: str, plot_logic):
    try:
        import matplotlib.pyplot as plt # lazy load

        plt.figure(figsize=(10, 6))
        plt.title(title)

        plt.style.use('default')
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3

        plot_logic(plt)

        plt.tight_layout()
        plt.savefig(filename, dpi=150)
        plt.close()

        return filename
    except (OSError, IOError, RuntimeError) as e:
        try:
            import matplotlib.pyplot as plt
            plt.close()
        except (ImportError, RuntimeError):
            pass
        return f"Error: {str(e)}"

def export_rc_transient(data: dict, filename: str = None) -> str:
    if not filename:
        filename = get_default_filename("rc_step")

    def plot(plt):
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (V)")
        for c in data["curves"]:
            plt.plot(data["time"], c["voltage"], label=f"R={c['R']}Ω")
        plt.legend()

    return _setup_and_save(filename, "RC step response", plot)

def export_square_wave(data: dict, filename: str = None) -> str:
    if not filename:
        filename = get_default_filename("rc_square")

    def plot(plt):
        plt.title(f"RC response ({data['freq']}Hz)")
        plt.plot(data["time"], data["input_wave"], label="Input", color="green", alpha=0.7)
        plt.plot(data["time"], data["output_wave"], label="Output", color="orange")
        plt.legend()

    return _setup_and_save(filename, "RC square wave", plot)

def export_555_astable(data: dict, filename: str = None) -> str:
    if not filename:
        filename = get_default_filename("555_astable")

    def plot(plt):
        plt.title(f"555 Astable output (Freq={data['freq']:.1f}Hz)")
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (V)")
        plt.plot(data["time"], data["voltage"], label="Output Pin 3", color="tab:blue")
        plt.ylim(-0.5, 6)
        plt.legend()

    return _setup_and_save(filename, "555 Astable", plot)

def export_555_monostable(data: dict, filename: str = None) -> str:
    if not filename:
        filename = get_default_filename("555_mono")

    def plot(plt): #plotting
        plt.title(f"555 Monostable pulse ({data['pulse_width']:.4f}s)")
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (V)")
        plt.plot(data["time"], data["trigger"], label="Trigger", color="green",
                 linestyle="--")
        plt.plot(data["time"], data["output"], label="Output", color="orange")
        plt.plot(data["time"], data["cap_voltage"], label="Capacitor",
                 color="blue", alpha=0.6)
        plt.legend()

    return _setup_and_save(filename, "555 Monostable", plot)

# exporting, white background, ink saving.

def export_generic_plot(data: dict, title: str = "Data Export", mode: str = "line",
                         filename: str = None, active_index: int = 0) -> str:
    if not filename:
        filename = get_default_filename("export_data")

    def plot(plt):
        labels = data.get("labels", [])
        series = data.get("series", [])
        names = data.get("names", [])

        safe_colors = ["tab:red", "tab:green", "tab:orange", "tab:blue", "tab:purple", "tab:cyan", "black"]

        if not series and "values" in data:
            series = [data["values"]]; names = ["Data"]

        if mode == "pie": # plot
            if series:
                idx = active_index if 0 <= active_index < len(series) else 0
                vals = [abs(x) for x in series[idx]]
                s_name = names[idx] if idx < len(names) else f"Series {idx+1}"
                plt.title(f"{s_name} (Distribution)")

                if sum(vals) > 0:
                    plt.pie(vals, labels=labels, autopct='%1.1f%%', startangle=90, colors=safe_colors)
                    plt.axis('equal')
                else: plt.text(0.5, 0.5, "Sum is zero, fix.", ha='center') 
        else:
            x = np.arange(len(labels))
            for i, s_data in enumerate(series):
                label = names[i] if i < len(names) else f"Series {i+1}"
                col = safe_colors[i % len(safe_colors)]

                if mode == "bar":
                    width = 0.8 / len(series)
                    offset = (i - len(series)/2 + 0.5) * width
                    plt.bar(x + offset, s_data, width, label=label, color=col)
                elif mode == "scatter": plt.scatter(x, s_data, label=label, color=col)
                elif mode == "area":
                    plt.plot(x, s_data, label=label, color=col)
                    plt.fill_between(x, s_data, alpha=0.3, color=col)
                else: plt.plot(s_data, marker='o', label=label, color=col)

            plt.xticks(x, labels); plt.legend()

    return _setup_and_save(filename, title, plot)

def export_multi_series(data: dict, filename_base: str, export_mode: str = "combined") -> str: # exports charts as either combo or in each file
    try:
        # lazy import
        import matplotlib.pyplot as plt

        series = data.get("series", [])
        labels = data.get("labels", [])
        names = data.get("names", [])

        if not series: return "No series data."

        safe_colors = ["tab:red", "tab:green", "tab:orange", "tab:blue", "tab:purple", "tab:cyan", "black"]
        plt.style.use('default')

        if export_mode == "combined":
            n = len(series)
            cols = math.ceil(math.sqrt(n))
            rows = math.ceil(n / cols)

            fig, axes = plt.subplots(rows, cols, figsize=(5 * cols, 5 * rows))
            fig.suptitle("Combined series export")

            if n == 1:
                ax_flat = [axes]
            else:
                ax_flat = axes.flatten()

            for i, ax in enumerate(ax_flat):
                if i < n:
                    vals = [abs(x) for x in series[i]]
                    s_name = names[i] if i < len(names) else f"Series {i+1}"
                    ax.set_title(s_name)
                    if sum(vals) > 0:
                        ax.pie(vals, labels=labels, autopct='%1.1f%%', startangle=90, colors=safe_colors)
                        ax.axis('equal')
                    else: ax.text(0.5, 0.5, "Zero sum, fix", ha='center')
                else: ax.axis('off')

            out_name = f"{filename_base}_combined.png"
            plt.tight_layout()
            plt.savefig(out_name, dpi=150)
            plt.close()
            return out_name

        saved_files = []
        for i, s_data in enumerate(series):
            plt.figure(figsize=(8, 6))
            s_name = names[i] if i < len(names) else f"Series {i+1}"
            plt.title(s_name)
            vals = [abs(x) for x in s_data]

            if sum(vals) > 0:
                plt.pie(vals, labels=labels, autopct='%1.1f%%', startangle=90, colors=safe_colors)
                plt.axis('equal')

            out_name = f"{filename_base}_{i+1}_{s_name}.png".replace(" ", "_")
            plt.tight_layout()
            plt.savefig(out_name, dpi=150)
            plt.close()
            saved_files.append(out_name)

        return f"Saved {len(saved_files)} files." # get number of saved files and return msg

    except (OSError, IOError, RuntimeError, ValueError, AttributeError, KeyError) as e:
        try:
            import matplotlib.pyplot as plt
            plt.close()
        except (ImportError, AttributeError):
            pass
        return f"Error: {e}"

#def export_financial_chart(data: dict, filename: str = None) -> str: OLD AREA GRAPH, Replaced by Candlesticks
  #  if not filename: filename = get_default_filename("market_chart")
   #
    #def plot(plt): #hmm hmm hmm hmm hmm hmm hm hmmm 📈📉📉📉📉📈📈📈📈📉📉📉📉
     #   symbol = data.get("symbol", "STOCK")
      #  plt.title(f"{symbol} Market Data")
       # plt.xlabel("Date"); plt.ylabel("Price ($)") #
        #
        #closes = data["close"]
        #dates = range(len(closes))
        #
        #plt.plot(dates, closes, label="Close Price", color="green")
        #plt.fill_between(dates, closes, alpha=0.3, color="green") #
        #plt.legend()

    #return _setup_and_save(filename, "Market Export", plot)

# mplfinance alternative
def export_financial_chart(data: dict, filename: str = None) -> str: # candles
    if not filename: filename = get_default_filename("market_chart")

    def plot(plt):
        try:
            dates = data.get("dates", [])
            opens = data["open"]
            highs = data["high"]
            lows = data["low"]
            closes = data["close"]

            n = len(closes)
            if n == 0: return

            plt.title(f"{data.get('symbol', 'STOCK')} Market Data ({n} candles)")
            plt.xlabel("Date / Index")
            plt.ylabel("Price ($)")

            # candle width
            width = 0.6
            width2 = width / 2.0

            # defined colours
            col_up = "green"
            col_down = "red"

            # draw candles manually
            for i in range(n):
                o, h, l, c = opens[i], highs[i], lows[i], closes[i]

                # determine the colour by comparing
                color = col_up if c >= o else col_down

                # wick
                plt.plot([i, i], [l, h], color="black", linewidth=1, zorder=1)

                # x: [i-w2, i+w2], y1: o, y2: c

                # Rect coords: (x, bottom), width, height
                lower = min(o, c)
                height = abs(o - c)

                # if open=close, min height so visible
                if height == 0: height = (h-l)*0.01 if h!=l else 0.01

                rect = plt.Rectangle((i - width2, lower), width, height,
                                     facecolor=color, edgecolor="black", linewidth=0.5, zorder=2)
                plt.gca().add_patch(rect)

            # auto scale view
            plt.autoscale()

            # x ticks, sparse
            step = max(1, n // 10)
            ticks = list(range(0, n, step))
            # try mapping date strings
            labels = [dates[t] if t < len(dates) else str(t) for t in ticks]

            plt.xticks(ticks, labels, rotation=30, ha='right', fontsize=8)
            plt.grid(True, alpha=0.3)

        except (ValueError, KeyError, AttributeError) as e:
            plt.text(0.5, 0.5, f"Error plotting candles: {e}", ha='center')

    return _setup_and_save(filename, "Market export", plot)
