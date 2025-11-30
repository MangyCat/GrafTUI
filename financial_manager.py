class FinancialManager:

    @staticmethod
    def fetch_data(symbol: str, period: str = "1mo", interval: str = "1d"): # fetches the data for a given symbol
        try:
            # lazy import! ignore pylint
            import yfinance as yf

            # clean up 
            ticker = symbol.strip().upper()
            if not ticker:
                return {"error": "No symbol provided"}

            # yahoofinance fetch
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df.empty:
                return {"error": f"No data found for {ticker}"}

            # drop nan rows
            df.dropna(inplace=True)

            # plottext formatting
            dates = [d.strftime("%Y-%m-%d") for d in df.index]
            opens = df['Open'].tolist()
            closes = df['Close'].tolist()
            highs = df['High'].tolist()
            lows = df['Low'].tolist()
            volumes = df['Volume'].tolist()

            return {
                "symbol": ticker,
                "dates": dates,
                "open": opens,
                "close": closes,
                "high": highs,
                "low": lows,
                "volume": volumes,
                "count": len(dates)
            }

        except (ImportError, ValueError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    @staticmethod
    def search_tickers(query: str):
        try:
            # LAZY IMPORT: Only load requests when user searches
            import requests

            url = "https://query2.finance.yahoo.com/v1/finance/search"
            params = {"q": query, "quotesCount": 15, "newsCount": 0}
            headers = {'User-Agent': 'Mozilla/5.0'} # totally.... shhhhh.

            res = requests.get(url, params=params, headers=headers, timeout=10)
            data = res.json()

            if "quotes" not in data:
                return []

            results = []
            for q in data["quotes"]:
                symbol = q.get("symbol", "")
                name = q.get("shortname") or q.get("longname", "Unknown")
                exch = q.get("exchange", "")
                type_ = q.get("quoteType", "")
                results.append((symbol, name, type_, exch))

            return results
        except (ImportError, requests.RequestException, ValueError, KeyError) as e:
            return [("Error", str(e), "", "")]
