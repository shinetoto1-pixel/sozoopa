import pandas as pd

src = r"C:\Users\user\Desktop\클로드코드\sozoopa\종목테마_정리.xlsx"
out = r"C:\Users\user\Desktop\클로드코드\sozoopa\테마목록.md"

df = pd.read_excel(src, sheet_name="종목테마")

total = 0
lines = []
lines.append("# 테마 목록 (카테고리별)")
lines.append("")
lines.append("사용자가 직접 정리한 기존 테마 목록. Phase 2에서 뉴스로 테마 후보를 도출할 때, 여기 있는")
lines.append("테마명과 일치/유사한 것이 있으면 우선적으로 그 이름을 사용한다 (alphasquare 등에서 실제로")
lines.append("종목 매핑이 가능한 이름일 확률이 높음). 여기 없는 새 테마를 발견하면 이 목록에 추가한다.")
lines.append("")
lines.append(f"(2026-07-27 최초 작성, `종목테마_정리.xlsx` 기반, 총 {{TOTAL}}개 테마)")
lines.append("")

for col in df.columns:
    vals = [str(v).strip() for v in df[col].tolist() if pd.notna(v) and str(v).strip() and str(v).strip().lower() != 'nan']
    if not vals:
        continue
    total += len(vals)
    lines.append(f"## {col} ({len(vals)}개)")
    lines.append(", ".join(vals))
    lines.append("")

text = "\n".join(lines).replace("{TOTAL}", str(total))

with open(out, "w", encoding="utf-8") as f:
    f.write(text)

print(f"총 {total}개 테마, {out} 에 저장 완료")
