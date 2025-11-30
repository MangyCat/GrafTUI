import statistics

class FinancialIndicators: # simple indicators


    @staticmethod
    def analyze_market_data(data: dict) -> str:
        "ierirrurrr grrr"
        if not data or "error" in data: return "No Market Data"
        
        try:
            closes = data["close"]
            if not closes: return "Empty Data"

            current_price = closes[-1]
            start_price = closes[0]
            
            # 1. Basic Price Stats
            delta = current_price - start_price
            pct_change = (delta / start_price) * 100
            
            try: vol = statistics.stdev(closes)
            except: vol = 0.0

            highs = data["high"]
            lows = data["low"]
            avg_spread = statistics.mean([h - l for h, l in zip(highs, lows)])
            
            symbol = data.get("symbol", "STOCK")

            # 2. Technical Indicators (New)
            sma_20 = FinancialIndicators.calculate_sma(closes, 5) # Short window for demo, maybe?
            trend = "BULL" if current_price > sma_20[-1] else "BEAR"

            return (
                f"Ticker: {symbol}\n"
                f"Price: ${current_price:.2f}\n"
                f"Change: {pct_change:+.2f}%\n"
                f"Volat.: {vol:.2f}\n"
                f"Spread: ${avg_spread:.2f}\n"
                f"Trend:  {trend} (SMA5)"
            )

        except Exception as e:
            return f"Fin Stats Error: {e}"

    @staticmethod
    def calculate_sma(data: list, window: int) -> list:
        """Calculates Simple Moving Average."""
        if len(data) < window: return data
        return [statistics.mean(data[i-window:i]) if i >= window else data[i] for i in range(len(data))]
#Charlie, what is jesus doing? 67. 
# Yeah, I guess he is.