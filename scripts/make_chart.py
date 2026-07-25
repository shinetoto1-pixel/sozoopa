import sys
import time
import yfinance as yf
import mplfinance as mpf

# 기간별 기대 최소 봉 개수 (이것보다 적으면 데이터가 잘린 것으로 판단)
MIN_ROWS = {
    "1mo": 15, "3mo": 50, "6mo": 100, "1y": 200, "2y": 400,
}


def _fetch(ticker, period, interval, retries=3, wait=3):
    """데이터를 받아오되, 기대 봉 개수보다 적게 오면 재시도한다."""
    min_rows = MIN_ROWS.get(period, 5)
    last_df = None
    for attempt in range(retries):
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df is not None and len(df) >= min_rows:
            return df
        last_df = df
        if attempt < retries - 1:
            time.sleep(wait)
    return last_df  # 마지막 시도 결과라도 반환 (호출부에서 부족 여부 재확인)


def make_chart(code, name, period="6mo", interval="1d", mav=(5, 20, 60), out_path=None, _tried_alt=False):
    """
    code: 종목코드.KS(코스피) 또는 .KQ(코스닥), 예) 005930.KS / 지수는 ^KS11(코스피), ^KQ11(코스닥)
    name: 차트 제목에 쓸 이름, 예) 삼성전자
    데이터가 부족하게 오면(레이트리밋 등) 최대 2회 재시도하고, 그래도 안 되면 반대 거래소(.KS<->.KQ)로 전환해 재시도한다.
    """
    if code.startswith("^") or "." in code:
        ticker = code
    else:
        ticker = f"{code}.KS"

    df = _fetch(ticker, period, interval)
    min_rows = MIN_ROWS.get(period, 5)

    if (df is None or len(df) < min_rows) and not _tried_alt and not code.startswith("^"):
        # KS/KQ 반대쪽으로 한 번 더 시도
        base = ticker.split(".")[0]
        alt_suffix = ".KQ" if ticker.endswith(".KS") else ".KS"
        alt_ticker = base + alt_suffix
        alt_df = _fetch(alt_ticker, period, interval)
        if alt_df is not None and len(alt_df) >= min_rows:
            ticker = alt_ticker
            df = alt_df

    if df is None or len(df) < min_rows:
        raise RuntimeError(f"{ticker}: 데이터 부족 ({0 if df is None else len(df)}행, 최소 {min_rows}행 필요) - 재시도 후에도 실패")

    df.columns = df.columns.get_level_values(0)
    has_volume = bool(df["Volume"].sum() > 0)

    mc = mpf.make_marketcolors(up="red", down="blue", edge="inherit", wick="inherit", volume="inherit")
    style = mpf.make_mpf_style(
        base_mpf_style="yahoo",
        marketcolors=mc,
        rc={
            "font.family": "Malgun Gothic",
            "axes.unicode_minus": False,
            "axes.edgecolor": "black",
            "axes.linewidth": 1.2,
        },
    )

    if out_path is None:
        out_path = f"charts/{code.replace('.', '_').replace('^', '')}.png"

    title = f"{name} - {period} 일봉" if ticker.startswith("^") else f"{name} ({ticker}) - {period} 일봉"

    kwargs = dict(
        type="candle", style=style, volume=has_volume,
        mav=mav, title=title, savefig=out_path,
    )
    if has_volume:
        kwargs["panel_ratios"] = (3, 1)

    mpf.plot(df, **kwargs)
    return out_path


if __name__ == "__main__":
    # 사용 예: python make_chart.py 005930.KS 삼성전자
    code = sys.argv[1] if len(sys.argv) > 1 else "005930.KS"
    name = sys.argv[2] if len(sys.argv) > 2 else code
    path = make_chart(code, name)
    print(f"saved: {path}")
