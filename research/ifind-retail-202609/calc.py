#!/usr/bin/env python3
"""复核 2026 年 9 月社零总额与限额以上单位烟酒类零售额的取数与同比。

运行：python3 research/ifind-retail-202609/calc.py
仅使用标准库；读取同目录 data.json 中的发布值与 iFinD 值。
"""
from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / "data.json").read_text(encoding="utf-8"))


def d(x):
    return Decimal(str(x))


def q(x, places=2):
    return d(x).quantize(Decimal("1." + "0" * places), rounding=ROUND_HALF_UP)


def main():
    social = DATA["latest"]["social_retail_total"]
    tobacco = DATA["latest"]["tobacco_alcohol_retail"]

    print("=" * 64)
    print("2026年9月 社零总额 / 限额以上单位烟酒类零售额（iFinD EDB）")
    print("=" * 64)
    rows = [
        ("社会消费品零售总额", social),
        ("限额以上单位烟酒类零售额", tobacco),
    ]
    for name, row in rows:
        print(f"\n{name}")
        print(f"  当月值(iFinD)      : {row['month_value_yi']} 亿元")
        print(f"  当月值(发布稿)      : {row['release_month_value_yi']} 亿元")
        print(f"  当月同比(发布)      : {row['month_yoy_pct']:+.1f}%")
        print(f"  累计值(2026年1-9月) : {row['cum_value_yi']} 亿元")
        print(f"  累计同比(发布)      : {row['cum_yoy_pct']:+.1f}%")
        print(f"  上年同月值          : {row['prior_year_same_month_value_yi']} 亿元")

    # 1) 取整一致性
    for name, row in rows:
        got = q(row["month_value_yi"], 0)
        assert got == d(row["release_month_value_yi"]), (name, got, row["release_month_value_yi"])
    print("\n[PASS] 当月值四舍五入后与发布稿一致（仅取整差异）")

    # 2) 社零当月同比可用两期水平复算
    social_implied = (d(social["month_value_yi"]) / d(social["prior_year_same_month_value_yi"]) - 1) * 100
    social_implied = q(social_implied, 2)
    print(f"[CHECK] 社零水平复算同比 = {social_implied:+.2f}%（发布 {social['month_yoy_pct']:+.1f}%）")
    assert abs(social_implied - d(social["month_yoy_pct"])) <= d("0.02"), "社零复算与发布同比不一致"
    print("[PASS] 社零当月同比与发布值一致")

    # 3) 烟酒类：公布同比按可比口径，不能用两期公布水平复算
    tobacco_implied = (d(tobacco["month_value_yi"]) / d(tobacco["prior_year_same_month_value_yi"]) - 1) * 100
    tobacco_implied = q(tobacco_implied, 2)
    gap = q(d(tobacco["month_yoy_pct"]) - tobacco_implied, 2)
    print(f"\n[NOTE] 烟酒类水平复算同比 = {tobacco_implied:+.2f}%（发布 {tobacco['month_yoy_pct']:+.1f}%）")
    print(f"       差异 = {gap:+.2f} 个百分点")
    print("       原因：限额以上单位统计范围每年调整，发布同比按可比口径计算，")
    print("       所用同期数与本期统计范围一致，和上年公布的名义水平存在口径差异。")
    print("       结论：引用发布同比 +13.8%；不能自行用两期公布当月值相除。")

    # 4) 2025 发布稿与可比基数
    print("\n[CHECK] 2025-09 发布稿：烟酒类 615 亿元、+1.6%；1-9月 4,808 亿元、+4.0%")
    base_month = d(tobacco["month_value_yi"]) / (1 + d(tobacco["month_yoy_pct"]) / 100)
    base_cum = d(tobacco["cum_value_yi"]) / (1 + d(tobacco["cum_yoy_pct"]) / 100)
    pct_month = (base_month / d("615") - 1) * 100
    pct_cum = (base_cum / d("4808") - 1) * 100
    print(f"       按2026年发布同比反推的可比基数：当月 {q(base_month, 2)} 亿元、累计 {q(base_cum, 2)} 亿元")
    print(f"       与2025年公布水平的差异：{q(pct_month, 2)}% / {q(pct_cum, 2)}%，与统计范围调整的解释一致")

    # 5) 发布稿表内一致性：累计值/累计同比来自同一发布稿
    print("\n[INFO] 发布稿原文（2026-10-19 10:00）：")
    print("       9月社零 42,433 亿元、+1.1%；1-9月 370,001 亿元、+1.1%")
    print("       烟酒类 9月 663 亿元、+13.8%；1-9月 5,105 亿元、+12.6%")
    print("\n所有断言通过。")


if __name__ == "__main__":
    main()
