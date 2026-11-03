#!/usr/bin/env python3
"""泸州老窖 2026 年三季报晨会速览卡：复算脚本（仅依赖 Python 3 标准库）。

用法：
    python3 research/ifind-luzhou-2026q3/calc.py

原始金额单位：元；亿元显示值 = 原始金额 / 1e8，四舍五入两位；
同比 =（本期 - 上年同期）/ |上年同期| * 100%，按原始金额全精度计算后再舍入。
"""

from __future__ import annotations

import json
import pathlib
from decimal import Decimal, ROUND_HALF_UP

ROOT = pathlib.Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data.json").read_text(encoding="utf-8"))

REV_2026 = DATA["metrics"]["营业收入"]["raw_cny"]
REV_2025 = DATA["metrics"]["营业收入"]["prior_raw_cny"]
NP_2026 = DATA["metrics"]["归母净利润"]["raw_cny"]
NP_2025 = DATA["metrics"]["归母净利润"]["prior_raw_cny"]

Q3_REV_2026 = DATA["supplementary_single_quarter"]["营业收入"]["raw_cny"]
Q3_NP_2026 = DATA["supplementary_single_quarter"]["归母净利润"]["raw_cny"]


def yi(raw: str) -> Decimal:
    return (Decimal(raw) / Decimal("1e8")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def yoy(current: str, prior: str) -> Decimal:
    return ((Decimal(current) - Decimal(prior)) / Decimal(prior) * 100).quantize(
        Decimal("0.0001"), rounding=ROUND_HALF_UP
    )


def main() -> None:
    # 卡面显示值
    assert yi(REV_2026) == Decimal("146.68"), yi(REV_2026)
    assert yi(NP_2026) == Decimal("56.71"), yi(NP_2026)
    assert yi(REV_2025) == Decimal("231.27"), yi(REV_2025)
    assert yi(NP_2025) == Decimal("107.62"), yi(NP_2025)
    assert yi(Q3_REV_2026) == Decimal("41.95"), yi(Q3_REV_2026)
    assert yi(Q3_NP_2026) == Decimal("13.32"), yi(Q3_NP_2026)

    # 同比复算（保留四位），并与接口/公告列示的两位小数核对
    rev_yoy = yoy(REV_2026, REV_2025)
    np_yoy = yoy(NP_2026, NP_2025)
    assert rev_yoy == Decimal("-36.5792"), rev_yoy
    assert np_yoy == Decimal("-47.3067"), np_yoy
    assert rev_yoy.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("-36.58")
    assert np_yoy.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("-47.31")

    metric = DATA["metrics"]
    assert Decimal(str(metric["营业收入"]["stated_yoy_percent"])) == Decimal("-36.58")
    assert Decimal(str(metric["归母净利润"]["stated_yoy_percent"])) == Decimal("-47.31")
    assert metric["营业收入"]["raw_cny"] == "14667616562.73"
    assert metric["归母净利润"]["raw_cny"] == "5671059241.53"

    # 快照值
    quote = DATA["quote"]
    assert quote["latest_price"] == 80.51
    assert abs(quote["pe_ttm"] - 20.6473203) < 1e-9
    assert quote["snapshot_time"] == "2026-11-03 12:15:15"

    # 报告期与口径
    report = DATA["report"]
    assert report["period"] == "2026-09-30"
    assert report["cumulative"] is True
    assert report["scope"] == "合并报表"
    assert report["audited"] is False
    assert report["disclosure_date"] == "2026-10-30"

    print("OK")
    print(f"营业收入 2026 1-9月: {REV_2026} 元 = {yi(REV_2026)} 亿元, 同比 {rev_yoy}%")
    print(f"归母净利润 2026 1-9月: {NP_2026} 元 = {yi(NP_2026)} 亿元, 同比 {np_yoy}%")
    print(f"单季 Q3 营业收入: {Q3_REV_2026} 元 = {yi(Q3_REV_2026)} 亿元")
    print(f"单季 Q3 归母净利润: {Q3_NP_2026} 元 = {yi(Q3_NP_2026)} 亿元")
    print(f"最新价: {quote['latest_price']} 元, 市盈率TTM: {quote['pe_ttm']} 倍 @ {quote['snapshot_time']}")


if __name__ == "__main__":
    main()
