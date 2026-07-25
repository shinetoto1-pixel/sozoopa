import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


def fetch(ticker):
    df = yf.download(ticker, period="5d", progress=False)
    last = df["Close"].iloc[-1].item()
    prev = df["Close"].iloc[-2].item()
    chg = (last - prev) / prev * 100
    return last, chg


def draw_grid(cells, ncols, out_path, title, fmt="{:,.2f}"):
    nrows = -(-len(cells) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 1.6 * nrows))
    fig.suptitle(title, fontsize=16, fontweight="bold", y=1.02)
    axes = axes.flatten() if nrows * ncols > 1 else [axes]

    for ax in axes:
        ax.axis("off")

    for ax, (name, last, chg, valfmt) in zip(axes, cells):
        color = "red" if chg >= 0 else "blue"
        sign = "▲" if chg >= 0 else "▼"
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                                    facecolor="#f5f5f5", edgecolor="#cccccc"))
        ax.text(0.06, 0.72, name, fontsize=13, fontweight="bold", transform=ax.transAxes, va="center")
        ax.text(0.06, 0.32, valfmt.format(last), fontsize=15, color=color, transform=ax.transAxes, va="center")
        ax.text(0.62, 0.32, f"{sign}{abs(chg):.2f}%", fontsize=12, color=color, transform=ax.transAxes, va="center")

    for ax in axes[len(cells):]:
        ax.set_visible(False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print("saved:", out_path)


# 세계 주요 증시
idx_tickers = [
    ("다우산업", "^DJI", "{:,.2f}"),
    ("나스닥종합", "^IXIC", "{:,.2f}"),
    ("S&P500", "^GSPC", "{:,.2f}"),
    ("니케이225", "^N225", "{:,.2f}"),
    ("상해종합", "000001.SS", "{:,.2f}"),
    ("항셍", "^HSI", "{:,.2f}"),
    ("영국(FTSE)", "^FTSE", "{:,.2f}"),
    ("프랑스(CAC40)", "^FCHI", "{:,.2f}"),
    ("독일(DAX)", "^GDAXI", "{:,.2f}"),
]
idx_cells = []
for name, t, fmt in idx_tickers:
    last, chg = fetch(t)
    idx_cells.append((name, last, chg, fmt))
draw_grid(idx_cells, 3, "charts/world_indices.png", "세계 주요 증시 현황")

# 환율 / 유가 / 금시세
usdkrw, usdkrw_chg = fetch("KRW=X")
usdjpy, usdjpy_chg = fetch("JPY=X")
eurusd, eurusd_chg = fetch("EURUSD=X")
gbpusd, gbpusd_chg = fetch("GBPUSD=X")
cnyusd, cnyusd_chg = fetch("CNY=X")
dxy, dxy_chg = fetch("DX-Y.NYB")
wti, wti_chg = fetch("CL=F")
gold, gold_chg = fetch("GC=F")

jpykrw = usdkrw / usdjpy * 100
eurkrw = usdkrw * eurusd
cnykrw = usdkrw / cnyusd

fx_cells = [
    ("미국 USD/KRW", usdkrw, usdkrw_chg, "{:,.2f}원"),
    ("일본 JPY(100엔)", jpykrw, usdkrw_chg - usdjpy_chg, "{:,.2f}원"),
    ("유럽연합 EUR/KRW", eurkrw, usdkrw_chg + eurusd_chg, "{:,.2f}원"),
    ("중국 CNY/KRW", cnykrw, usdkrw_chg - cnyusd_chg, "{:,.2f}원"),
    ("유로/달러", eurusd, eurusd_chg, "{:,.4f}"),
    ("파운드/달러", gbpusd, gbpusd_chg, "{:,.4f}"),
    ("달러인덱스", dxy, dxy_chg, "{:,.2f}"),
    ("WTI유가", wti, wti_chg, "${:,.2f}"),
    ("국제금", gold, gold_chg, "${:,.2f}"),
]
draw_grid(fx_cells, 3, "charts/fx_commodity.png", "환율 · 유가 · 금시세 (국내 휘발유·국내금 제외)")
