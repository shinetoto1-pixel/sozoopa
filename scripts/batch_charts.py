import time
from make_chart import make_chart

candidates = [
    # (code, name) - .KS/.KQ 자동 판별 + 실패시 재시도는 make_chart 내부에서 처리
]

results = []
for code, name in candidates:
    try:
        path = make_chart(code, name, period="6mo", out_path=f"charts/{code}_{name}.png")
        results.append((code, name, "OK", path))
    except RuntimeError as e:
        results.append((code, name, "FAIL", str(e)))
    time.sleep(1)  # 연속 요청 사이 텀

for r in results:
    print(r)
