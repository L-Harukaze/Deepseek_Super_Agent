#!/usr/bin/env python3
"""贵州茅台 2026 年三季报财务速览：复算脚本（仅依赖 Python 3 标准库）。

用法：
    python3 research/ifind-moutai-2026q3-feishu/calc.py

金额单位：元；亿元显示值 = 原始金额 / 1e8，四舍五入两位；
同比 =（本期 - 上年同期）/ |上年同期| * 100%，按原始金额全精度计算后再舍入。
原始金额取自 iFinD 公告检索片段（2026 年三季报及 2025 年三季报），
行业值取自 iFinD 行业财务数据 CSV（851231.SL）。
"""

from __future__ import annotations

import csv
import pathlib
from decimal import Decimal, ROUND_HALF_UP

D = Decimal
Q4 = D("0.0001")
Q2 = D("0.01")

# --- 2026 年前三季度（2026-01-01 至 2026-09-30，合并报表，未经审计） ---
REV_TOTAL_26 = D("133283652508.95")  # 营业总收入
REV_26 = D("130970743649.04")        # 营业收入
NP_26 = D("64467425981.95")          # 归母净利润
COST_26 = D("13645718932.90")        # 营业成本
Q3_REV_26 = D("40267482684.56")      # 2026Q3 单季营业收入
Q3_NP_26 = D("19950545560.09")       # 2026Q3 单季归母净利润
ROE_26 = D("24.47")                  # 加权平均 ROE，累计
ROE_Q3_26 = D("7.64")                # 加权平均 ROE，单季

# --- 2025 年前三季度（上年同期） ---
REV_TOTAL_25 = D("130903889634.88")  # 营业总收入
REV_25 = D("128453707655.86")        # 营业收入
NP_25 = D("64626746712.18")          # 归母净利润（2026 年三季报比较利润表）
COST_25 = D("11183972073.77")        # 营业成本
Q3_REV_25 = D("39064353239.02")      # 2025Q3 单季营业收入（2025 年三季报）
Q3_NP_25 = D("19223784414.08")       # 2025Q3 单季归母净利润（2025 年三季报）
ROE_25 = D("24.64")                  # 加权平均 ROE，累计
ROE_Q3_25 = D("7.75")                # 加权平均 ROE，单季

# --- 申万三级行业（2014 版）白酒 851231.SL，iFinD 行业财务数据（整体法） ---
IND_ROE_26 = D("15.6372")
IND_ROE_25 = D("17.5707")
IND_GM_26 = D("81.8105")
IND_GM_25 = D("82.0570")

INDUSTRY_CSV = (
    pathlib.Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "ifind"
    / "profit_20260930.csv"
)
INDUSTRY_SUMMARY_CSV = (
    pathlib.Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "ifind"
    / "summary_20260930.csv"
)


def yi(amount: Decimal) -> Decimal:
    return (amount / D(1e8)).quantize(Q2, rounding=ROUND_HALF_UP)


def yoy(current: Decimal, prior: Decimal) -> Decimal:
    return ((current - prior) / abs(prior) * D(100)).quantize(
        Q4, rounding=ROUND_HALF_UP
    )


def gm(revenue: Decimal, cost: Decimal) -> Decimal:
    return ((revenue - cost) / revenue * D(100)).quantize(
        Q4, rounding=ROUND_HALF_UP
    )


def pct(value: Decimal) -> str:
    return f"{value:+.2f}%"


def ppt(value: Decimal) -> str:
    return f"{value:+.2f}pct"


def main() -> None:
    print("== 公司：贵州茅台（600519.SH），2026 年三季报，合并报表，人民币 ==")

    checks = [
        ("营业总收入", REV_TOTAL_26, REV_TOTAL_25, D("1.8179")),
        ("营业收入", REV_26, REV_25, D("1.9595")),
        ("归母净利润", NP_26, NP_25, D("-0.2465")),
    ]
    for name, cur, prior, stated in checks:
        calc = yoy(cur, prior)
        print(
            f"{name}: {yi(cur):,.2f} 亿元 vs {yi(prior):,.2f} 亿元, "
            f"同比 {pct(calc)}（iFinD 列示 {stated:+.4f}%）"
        )
        assert calc == stated, (name, calc, stated)

    q3_checks = [
        ("营业收入", Q3_REV_26, Q3_REV_25, D("3.0799")),
        ("归母净利润", Q3_NP_26, Q3_NP_25, D("3.7805")),
    ]
    for name, cur, prior, stated in q3_checks:
        calc = yoy(cur, prior)
        print(
            f"Q3 单季{name}: {yi(cur):,.2f} 亿元 vs {yi(prior):,.2f} 亿元, "
            f"同比 {pct(calc)}（iFinD 列示 {stated:+.4f}%）"
        )
        assert calc == stated, (name, calc, stated)

    gm_26 = gm(REV_26, COST_26)
    gm_25 = gm(REV_25, COST_25)
    print(
        f"销售毛利率: {gm_26:.4f}% vs {gm_25:.4f}%, "
        f"变化 {gm_26 - gm_25:+.4f}pct（iFinD 列示 89.5811% / 91.2934%）"
    )
    assert gm_26 == D("89.5811")
    assert gm_25 == D("91.2934")
    assert gm_26 - gm_25 == D("-1.7123")

    cost_yoy = yoy(COST_26, COST_25)
    print(f"营业成本同比: {pct(cost_yoy)}（iFinD 列示 +22.0114%）")
    assert cost_yoy == D("22.0114")

    print(
        f"加权平均 ROE: {ROE_26:.2f}% vs {ROE_25:.2f}%, "
        f"变化 {ROE_26 - ROE_25:+.2f}pct"
    )
    print(
        f"Q3 单季加权平均 ROE: {ROE_Q3_26:.2f}% vs {ROE_Q3_25:.2f}%, "
        f"变化 {ROE_Q3_26 - ROE_Q3_25:+.2f}pct"
    )

    print("\n== 申万白酒行业（851231.SL，2014 版三级，整体法）==")
    print(
        f"ROE: {IND_ROE_26:.4f}% vs {IND_ROE_25:.4f}%, "
        f"变化 {IND_ROE_26 - IND_ROE_25:+.4f}pct"
    )
    print(
        f"销售毛利率: {IND_GM_26:.4f}% vs {IND_GM_25:.4f}%, "
        f"变化 {IND_GM_26 - IND_GM_25:+.4f}pct"
    )
    assert IND_ROE_26 - IND_ROE_25 == D("-1.9335")
    assert IND_GM_26 - IND_GM_25 == D("-0.2465")

    print("\n== 公司与行业对比（2026 年前三季度） ==")
    print(f"ROE 差值: {ROE_26 - IND_ROE_26:+.2f}pct")
    print(f"销售毛利率差值: {gm_26 - IND_GM_26:+.2f}pct")

    if INDUSTRY_CSV.exists():
        with INDUSTRY_CSV.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("代码") == "851231.SL":
                    assert D(row["ROE(%)_本期"]) == IND_ROE_26
                    assert D(row["ROE(%)_上年同期"]) == IND_ROE_25
                    assert D(row["销售毛利率(%)_本期"]) == IND_GM_26
                    assert D(row["销售毛利率(%)_上年同期"]) == IND_GM_25
                    print(f"\n已核对行业原始 CSV：{INDUSTRY_CSV}")
                    break
            else:
                raise AssertionError("行业 CSV 中未找到 851231.SL")
    else:
        print(
            f"\n[提示] 行业原始 CSV 不在本地（{INDUSTRY_CSV}），跳过文件核对；"
            "接口返回值仍已断言。"
        )

    if INDUSTRY_SUMMARY_CSV.exists():
        with INDUSTRY_SUMMARY_CSV.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("代码") == "851231.SL":
                    rev = D(row["营业收入(亿元)_本期"])
                    net = D(row["净利润(亿元)_本期"])
                    eq_now = D(row["归属母公司股东的权益(亿元)_本期"])
                    eq_prev = D(row["归属母公司股东的权益(亿元)_上年同期(调整后)"])
                    net_margin = (net / rev * D(100)).quantize(
                        Q4, rounding=ROUND_HALF_UP
                    )
                    avg_equity = (eq_now + eq_prev) / D(2)
                    roe_deducted = (
                        D(row["扣除非经常损益后的净利润(亿元)_本期"])
                        / avg_equity
                        * D(100)
                    ).quantize(Q4, rounding=ROUND_HALF_UP)
                    print(
                        f"行业财务摘要：营业收入 {rev:.4f} 亿元、净利润 {net:.4f} 亿元，"
                        f"销售净利率 {net_margin}%；ROE(扣非) {roe_deducted}%"
                    )
                    assert net_margin == D("37.7792")
                    assert roe_deducted == D("15.5441")
                    break
            else:
                raise AssertionError("行业财务摘要 CSV 中未找到 851231.SL")
    else:
        print(
            f"\n[提示] 行业财务摘要 CSV 不在本地（{INDUSTRY_SUMMARY_CSV}），"
            "跳过整体法交叉核对。"
        )

    print("\n全部断言通过。")


if __name__ == "__main__":
    main()
