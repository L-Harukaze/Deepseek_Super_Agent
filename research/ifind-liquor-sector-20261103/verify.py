#!/usr/bin/env python3
"""离线校验 data.json：成交额合计、涨跌家数、领涨/领跌与指数快照是否一致。

用法：python3 verify.py
退出码：0 = 全部通过；1 = 有校验失败。
"""
import json
import sys
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data.json"


def main() -> int:
    d = json.loads(DATA.read_text(encoding="utf-8"))
    sector = d["sector"]
    cons = d["constituents"]
    checks = []

    checks.append(("成分股数量为 19", len(cons) == 19, f"实际 {len(cons)}"))

    total = sum(Decimal(c["amount_cny_raw"]) for c in cons)
    idx_amt = Decimal(sector["amount_cny_raw"])
    diff = idx_amt - total
    checks.append((
        "成分股成交额合计与板块快照一致（差额 < 100 元）",
        abs(diff) < 100,
        f"合计 {total} 元；板块 {idx_amt} 元；差额 {diff} 元",
    ))

    up = sum(1 for c in cons if c["change_pct"] > 0)
    down = sum(1 for c in cons if c["change_pct"] < 0)
    flat = sum(1 for c in cons if c["change_pct"] == 0)
    checks.append((
        "涨跌家数与指数快照一致",
        up == sector["rise_count"] and down == sector["fall_count"] and flat == 0,
        f"自算 {up} 涨 / {down} 跌 / {flat} 平；快照 {sector['rise_count']} 涨 / {sector['fall_count']} 跌",
    ))

    ranked = sorted(cons, key=lambda c: c["change_pct"], reverse=True)
    top, bottom = ranked[0], ranked[-1]
    checks.append((
        "领涨股与 data.json 记录一致",
        top["code"] == d["leaders"]["top_gainer"]["code"],
        f"自算 {top['name']} {top['change_pct']:+.4f}%",
    ))
    checks.append((
        "领跌股与 data.json 记录一致",
        bottom["code"] == d["leaders"]["top_loser"]["code"],
        f"自算 {bottom['name']} {bottom['change_pct']:+.4f}%",
    ))

    checks.append((
        "指数点位与 11:30 高频末根记录一致",
        sector["last"] == "39779.84" and "39779.84" in sector["last_bar_1130"],
        f"快照 {sector['last']}；记录 {sector['last_bar_1130']}",
    ))

    ok = True
    for name, passed, detail in checks:
        print(("PASS" if passed else "FAIL"), "-", name)
        print("      ", detail)
        ok = ok and passed

    print()
    print("结论：", "全部校验通过" if ok else "存在校验失败")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
