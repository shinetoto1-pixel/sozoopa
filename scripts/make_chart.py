import sys
import time
from datetime import date, timedelta
import yfinance as yf
import mplfinance as mpf

# 기간별 기대 최소 봉 개수 (이것보다 적으면 데이터가 잘린 것으로 판단)
MIN_ROWS = {
    "1mo": 15, "3mo": 50, "6mo": 100, "1y": 200, "2y": 400,
}

# 2026-07-28 확인된 문제: 야후파이낸스에서 ^KS11(코스피)/^KQ11(코스닥) "지수" 티커는 개별 종목 대비
# 최근 영업일 데이터가 며칠씩 지연되는 경우가 있음(행 개수는 충분해서 위 MIN_ROWS 검증은 통과해버림).
# 지연이 감지되면 해당 지수를 추종하는 ETF로 대신 그린다(가격 스케일은 다르지만 등락 흐름은 사실상 동일).
INDEX_PROXY = {
    "^KS11": ("069500.KS", "코스피200 ETF"),
    "^KQ11": ("229200.KS", "코스닥150 ETF"),
}


def _expected_last_trading_day(today=None):
    """이 파이프라인은 항상 장 시작 전(07:30 이전)에 실행되므로, '오늘 이전 가장 최근 평일'을
    데이터가 있어야 할 마지막 날짜로 본다. 한국 공휴일은 반영하지 않은 근사치라, 공휴일 다음날엔
    실제로는 정상인데 지연으로 오탐될 수 있음 — 그 정도는 감수한다(경고만 찍고 차트는 정상 생성)."""
    d = (today or date.today()) - timedelta(days=1)
    while d.weekday() >= 5:  # 5=토, 6=일
        d -= timedelta(days=1)
    return d


def _staleness_days(df):
    """df의 마지막 날짜가 예상 마지막 영업일보다 며칠(영업일 기준) 뒤처져 있는지. 0이면 정상."""
    if df is None or len(df) == 0:
        return 999
    last_date = df.index[-1].date()
    expected = _expected_last_trading_day()
    if last_date >= expected:
        return 0
    gap, d = 0, last_date
    while d < expected:
        d += timedelta(days=1)
        if d.weekday() < 5:
            gap += 1
    return gap


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

    # --- 최신성 검증: 행 개수는 충분해도 "가장 최근 날짜"가 뒤처져 있을 수 있음 ---
    stale_gap = _staleness_days(df)
    if stale_gap > 0 and ticker in INDEX_PROXY:
        proxy_ticker, proxy_label = INDEX_PROXY[ticker]
        print(f"[경고] {ticker} 데이터가 {stale_gap}영업일 지연됨(최근 데이터: {df.index[-1].date()}). "
              f"{proxy_ticker}({proxy_label})로 대체 시도.")
        proxy_df = _fetch(proxy_ticker, period, interval)
        proxy_gap = _staleness_days(proxy_df)
        if proxy_df is not None and len(proxy_df) >= min_rows and proxy_gap < stale_gap:
            df, ticker, stale_gap = proxy_df, proxy_ticker, proxy_gap
            name = f"{name}({proxy_label} 대리)"
        else:
            print("[경고] 대리 티커도 데이터가 부족하거나 여전히 지연됨 — 원본 지수 데이터 그대로 사용.")

    if stale_gap > 0:
        print(f"[경고] {ticker} 최종 데이터가 예상보다 {stale_gap}영업일 지연됨 "
              f"(최근 데이터: {df.index[-1].date()}, 예상 최근 영업일: {_expected_last_trading_day()}). 차트 제목에 표기함.")

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
    if stale_gap > 0:
        title += f"\n[데이터 {df.index[-1].date()} 기준 · {stale_gap}영업일 지연]"

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
