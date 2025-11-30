# GrafTUI - Electronic analyzer and data plotter

A TUI application I built with textual for TerminalCraft for making graphs from CSV spreadsheets, and rendering stock graphs, aswell as electronic graphs (555, RC)

![Python 3.14](https://img.shields.io/badge/python-3.14-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)


## Features

### Simple electronics simulation
- **RC filter analysis**: Calculate transient response for Resistor-capacitor circuits
- **555 timer circuits**:
  - Astable mode (oscillating) frequency calculations
  - Monostable mode (one shot) pulse width calculations
- **Resistor color code calculator**: Convert between resistance values and color bands. (don't worry about the gap in the middle)
- **Ohm's law calculator**: Solves for voltage, current, resistance or power.

### Financial market analysis
- **Real market data 🤯**: Retrieves OHLC data (thanks to Yahoo Finance)
- **Stock charts**: Candlestick for render, area for preview.
- **Technical indicators**: Basic statistics and market indicators
- **Ticker search**: Search for stocks by ticker symbol or company name (Tesla, Nvidia, NVDA)

### Data Visualization
- **Multi-format plotting**:
  - Line, bar, area, scatter, and pie charts 
  - Support for single and multi-series exports (pie charts only)
- **Interactive plot rendering**: Real-time visualization with Textual's plotext
- **Export to PNG**: Save charts in PNG format (1500x900)

### Workspace
- **Persistence**: Autosaves data and position when quitting (spreadsheet data, electronic resistor values, etc)
- **Custom themes**: Is compatible with any textual theme


## Installation

### Requirements
- Python 3.14+ (older may work)
- pip (Python package manager, obviously)

### Setup

1. **git clone or download the repository:**
   ```bash
   cd GrafTUI
   ```

2. **install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **run the python file:**
   ```bash
   python main.py
   ```


## Usage

### Main Navigation
Use the navigation bar at the top to switch between modules:
- **MARKETS**: Stock market analysis and charting
- **ELECTRONICS**: Circuit simulators and calculators
- **DATA VIEW**: Custom data import and plotting

### Financial Module
1. Enter a stock ticker (e.g., `AAPL`, `GOOGL`)
2. Select time period and interval (auto-adjusted for accuracy)
3. View candlestick chart with OHLC data
4. Export chart as PNG or view market statistics

### Electronics Module
1. **RC Filter**: Enter resistance and capacitance values
2. **555 Timer**: Calculate frequency or pulse width based on resistor/capacitor values
3. **Resistor Color**: Input resistance value or click on color bands
4. **Ohm's Law**: Enter ANY two electrical values to solve for the rest

### General Module
1. **Import CSV**: Load data from CSV files with transpose detection
2. **Plot Data**: Choose from line, bar, area, scatter, or pie chart types
3. **Multi-Series**: Plot multiple data series with combined or separate exports
4. **Export**: Save visualizations as high-resolution PNG files

### Keyboard Shortcuts
- `Tab`: Navigate between elements
- `Enter`: Confirm/Execute action
- `Esc`: Close modals and dialogs
- Arrow keys: Navigate lists and selections



## Project Structure

```
GrafTUI/
├── main.py                    # Main app.
├── views.py                   # UI components
├── fin_controller.py          # Financial data fetching and logic
├── sim_controller.py          # Electronic calculations
├── tools_views.py             # Resistor calc and Ohm's law calc UI
├── exporter.py                # Chart exporting, using matplotlib
├── financial_manager.py       # Yahoo finance api integrating
├── fin_indicators.py          # Basic analysis indicators
├── config_manager.py          # User preferences manager
├── workspace_manager.py       # Persistence manager
├── file_manager.py            # File picker/saver
├── statistics_engine.py       # Data calculations
├── app_styles.tcss            # Textual CSS styling
├── requirements.txt           # Python dependencies
└── README.md                  # What you're currently looking at
```

## App structure

The application follows a [Model-view-controller](https://en.wikipedia.org/wiki/Model–view–controller) architecture

- **Models**: `financial_manager.py`, `fin_indicators.py`, `sim_controller.py`
- **Views**: `views.py`, `tools_views.py`, `file_manager.py`
- **Controllers**: `fin_controller.py`, `sim_controller.py` (hybrid)
- **Managers**: Config, workspace, and file management utilities

### Lazy Imports
Performance heavy libraries like matplotlib or yfinance are only imported when needed to minimize startup latency.

### Threading
Data fetching was threaded to keep the UI responsive (UI would lock up, if not threaded.)

---

## Dependencies

### Core
- **textual** - Main TUI framework
- **textual-plotext** - Plotext integration for textual


### Data and utilties
- **matplotlib** - Chart generating and exporting
- **numpy** - Numerical calculations
- **yfinance** - Yahoo Finance data fetching and processing
- **pandas** - Data manipulation (implied by yfinance)

- **requests** - HTTP client for ticker search and fetching

---

## License

This project is licensed under the MIT License - see LICENSE file for details.


## End

**Developed for TerminalCraft YSWS using Textual & Python ❤️**


