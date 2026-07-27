import yfinance as yf

stocks = [
    ("SK이터닉스", "475150.KS"),
    ("한국가스공사", "036460.KS"),
    ("S-Oil", "010950.KS"),
    ("GS건설", "006360.KS"),
    ("SK텔레콤", "017670.KS"),
    ("BGF리테일", "282330.KS"),
    ("GS리테일", "007070.KS"),
    ("한화오션", "042660.KS"),
    ("삼성전기", "009150.KS"),
    ("삼성전자", "005930.KS"),
    ("SK하이닉스", "000660.KS"),
]

for name, ticker in stocks:
    try:
        df = yf.download(ticker, period="5d", interval="1d", progress=False)
        if df is None or len(df) < 2:
            print(f"{name}({ticker}): 데이터 부족")
            continue
        df.columns = df.columns.get_level_values(0)
        last_close = df["Close"].iloc[-1]
        prev_close = df["Close"].iloc[-2]
        last_date = df.index[-1].strftime("%Y-%m-%d")
        chg = (last_close - prev_close) / prev_close * 100
        sign = "▲" if chg >= 0 else "▼"
        print(f"{name}({ticker}) [{last_date}]: {last_close:,.0f} {sign}{abs(chg):.2f}%")
    except Exception as e:
        print(f"{name}({ticker}): 에러 - {e}")
