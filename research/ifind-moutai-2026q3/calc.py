#!/usr/bin/env python3
"""贵州茅台 2026 年三季报财务速览：复算脚本（仅依赖 Python 3 标准库）。

用法：
    python3 research/ifind-moutai-2026q3/calc.py

原始金额单位：元；亿元显示值 = 原始金额 / 1e8，四舍五入两位；
同比 =（本期 - 上年同期）/ |上年同期| * 100%，按原始金额全精度计算后再舍入。
2025 年同期金额中，部分取自 iFinD 接口的“亿元”显示值（4 位小数），
已在对应变量上注明；这些数值的复算结果与 iFinD 自列同比一致。
"""

from __future__ import annotations

import csv
import pathlib

# --- 2026 年前三季度（2026-01-01 至 2026-09-30，合并报表，未经审计） ---
# 来源：iFinD search_notice《贵州茅台 2026 年第三季度报告》，2026-10-31，
# 与 get_security_indicators 返回的元金额一致。
REV_TOTAL_2026 = 133_283_652_508.95  # 营业总收入
REV_2026 = 130_970_743_649.04        # 营业收入
NP_2026 = 64_467_425_981.95          # 归母净利润
COST_2026 = 13_645_720_000.00        # 营业成本，iFinD 显示 136.4572 亿元

# --- 2025 年前三季度（上年同期） ---
REV_TOTAL_2025 = 130_903_889_634.88  # 营业总收入
REV_2025 = 128_453_707_655.86        # 营业收入
NP_2025 = 64_626_750_000.00          # 归母净利润，iFinD 显示 646.2675 亿元
COST_2025 = 11_183_970_000.00        # 营业成本，iFinD 显示 111.8397 亿元

# 净利润（含少数股东损益），用于销售净利率
NET_PROFIT_2026 = 66_717_143_218.04  # iFinD 显示 667.1714 亿元
NET_PROFIT_2025 = 66_898_800_000.00  # iFinD 显示 668.988 亿元

# --- 2026 年第三季度单季（7-9 月） ---
Q3_REV_TOTAL_2026 = 41_005_580_000.00  # 营业总收入，iFinD 显示 410.0558 亿元
Q3_REV_TOTAL_2025 = 39_810_130_000.00  # 营业总收入，iFinD 显示 398.1013 亿元
Q3_REV_2026 = 40_267_482_684.56        # 营业收入
Q3_REV_2025 = 39_064_350_000.00        # 营业收入，iFinD 显示 390.6435 亿元
Q3_NP_2026 = 19_950_545_560.09         # 归母净利润
Q3_NP_2025 = 19_223_780_000.00         # 归母净利润，iFinD 显示 192.2378 亿元

# --- 公司披露的加权平均 ROE（%） ---
ROE_2026 = 24.47
ROE_2025 = 24.64
ROE_Q3_2026 = 7.64
ROE_Q3_2025 = 7.75

# --- 申万三级行业（2014 版）白酒 851231.SL，iFinD 行业财务数据（整体法） ---
IND_ROE_2026 = 15.6372
IND_ROE_2025 = 17.5707
IND_GM_2026 = 81.8105
IND_GM_2025 = 82.0570

INDUSTRY_CSV = (
    pathlib.Path(__file__).resolve().parents[2]
    / "data"
    / "raw"
    / "ifind"
    / "profit_20260930.csv"
)


def yi(amount: float) -> float:
    return round(amount / 1e8, 2)


def yoy(current: float, prior: float) -> float:
    return (current - prior) / abs(prior) * 100


def pct(value: float) -> str:
    return f"{value:+.2f}%"


def ppt(value: float) -> str:
    return f"{value:+.2f}pct"


def main() -> None:
    print("== 公司：贵州茅台（600519.SH），2026 年三季报，合并报表 ==")
    rows = [
        ("营业总收入", REV_TOTAL_2026, REV_TOTAL_2025, 1.8179),
        ("营业收入", REV_2026, REV_2025, 1.9595),
        ("归母净利润", NP_2026, NP_2025, -0.2465),
    ]
    for name, cur, prior, stated in rows:
        calc = yoy(cur, prior)
        print(
            f"{name}: {yi(cur):,.2f} 亿元 vs {yi(prior):,.2f} 亿元, "
            f"同比 {pct(calc)}（iFinD 列示 {stated:+.4f}%）"
        )
        assert abs(calc - stated) < 0.001, (name, calc, stated)

    q3_rows = [
        ("营业总收入", Q3_REV_TOTAL_2026, Q3_REV_TOTAL_2025, 3.0029),
        ("营业收入", Q3_REV_2026, Q3_REV_2025, 3.0799),
        ("归母净利润", Q3_NP_2026, Q3_NP_2025, 3.7806),
    ]
    for name, cur, prior, stated in q3_rows:
        calc = yoy(cur, prior)
        print(
            f"Q3 单季{name}: {yi(cur):,.2f} 亿元 vs {yi(prior):,.2f} 亿元, "
            f"同比 {pct(calc)}（iFinD 列示 {stated:+.4f}%）"
        )
        assert abs(calc - stated) < 0.001, (name, calc, stated)

    gm_2026 = (REV_2026 - COST_2026) / REV_2026 * 100
    gm_2025 = (REV_2025 - COST_2025) / REV_2025 * 100
    print(
        f"销售毛利率: {gm_2026:.4f}% vs {gm_2025:.4f}%, "
        f"变化 {gm_2026 - gm_2025:+.4f}pct（iFinD 列示 89.5811% / 91.2934%）"
    )
    assert abs(gm_2026 - 89.5811) < 0.001
    assert abs(gm_2025 - 91.2934) < 0.001

    cost_yoy = yoy(COST_2026, COST_2025)
    print(f"营业成本同比: {pct(cost_yoy)}")
    assert abs(cost_yoy - 22.0114) < 0.001

    nm_2026 = NET_PROFIT_2026 / REV_2026 * 100
    nm_2025 = NET_PROFIT_2025 / REV_2025 * 100
    print(
        f"销售净利率: {nm_2026:.4f}% vs {nm_2025:.4f}%, "
        f"变化 {nm_2026 - nm_2025:+.4f}pct（iFinD 列示 50.9405% / 52.0801%）"
    )
    assert abs(nm_2026 - 50.9405) < 0.001
    assert abs(nm_2025 - 52.0801) < 0.001

    print(
        f"加权 ROE: {ROE_2026:.2f}% vs {ROE_2025:.2f}%, "
        f"变化 {ROE_2026 - ROE_2025:+.2f}pct"
    )
    print(
        f"Q3 单季加权 ROE: {ROE_Q3_2026:.2f}% vs {ROE_Q3_2025:.2f}%, "
        f"变化 {ROE_Q3_2026 - ROE_Q3_2025:+.2f}pct"
    )

    print("\n== 申万白酒行业（851231.SL，整体法）==")
    print(
        f"ROE: {IND_ROE_2026:.4f}% vs {IND_ROE_2025:.4f}%, "
        f"变化 {IND_ROE_2026 - IND_ROE_2025:+.4f}pct"
    )
    print(
        f"销售毛利率: {IND_GM_2026:.4f}% vs {IND_GM_2025:.4f}%, "
        f"变化 {IND_GM_2026 - IND_GM_2025:+.4f}pct"
    )

    print("\n== 公司与行业对比（2026 年前三季度） ==")
    print(f"ROE 差值: {ROE_2026 - IND_ROE_2026:+.2f}pct")
    print(f"销售毛利率差值: {gm_2026 - IND_GM_2026:+.2f}pct")

    if INDUSTRY_CSV.exists():
        with INDUSTRY_CSV.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("代码") == "851231.SL":
                    assert abs(float(row["ROE(%)_本期"]) - IND_ROE_2026) < 1e-9
                    assert abs(float(row["销售毛利率(%)_本期"]) - IND_GM_2026) < 1e-9
                    assert abs(float(row["ROE(%)_上年同期"]) - IND_ROE_2025) < 1e-9
                    assert abs(
                        float(row["销售毛利率(%)_上年同期"]) - IND_GM_2025
                    ) < 1e-9
                    print(f"\n已核对行业原始 CSV：{INDUSTRY_CSV}")
                    break
            else:
                raise AssertionError("行业 CSV 中未找到 851231.SL")
    else:
        print(f"\n[提示] 行业原始 CSV 不在本地（{INDUSTRY_CSV}），跳过文件核对")

    print("\n全部断言通过。")


if __name__ == "__main__":
    main()
