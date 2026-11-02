#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""五粮液 2025 年半年度营业收入 / 营业总收入 计算底稿（可复算）。

数据来源：《宜宾五粮液股份有限公司 2025 年半年度报告全文》
（巨潮资讯网，2025-08-28 披露，PDF，126 页）：
  - PDF 第 6 页“四、主要会计数据和财务指标”：营业收入 52,770,984,383.52 / 50,648,026,578.65
  - PDF 第 12 页“2、营业收入构成”：营业收入合计 52,770,984,383.52 / 50,648,026,578.65
  - PDF 第 36 页“3、合并利润表”：一、营业总收入 与 其中：营业收入 均为上述金额
  - PDF 第 16 页：2025 年上半年实现营业总收入 527.71 亿元，同比增长 4.19%

用法：
    python3 calc.py            # 输出计算表并校验
    python3 calc.py --json     # 以 JSON 输出供程序比对

脚本只用标准库，原始金额以十进制字符串保存，避免二进制浮点误差。
"""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP, getcontext

getcontext().prec = 50

YI = Decimal("100000000")

# 原始金额（元），来自报告正文，字符串形式保留报告中列示的全部精度。
REVENUE = {
    "name": "营业收入",
    "current": Decimal("52770984383.52"),   # 2025 年半年度，PDF 第 6、12、36 页
    "prior": Decimal("50648026578.65"),     # 2024 年半年度，PDF 第 6、12、36 页
    "pages": "PDF 第 6、12、36 页",
}

TOTAL_OPERATING_REVENUE = {
    "name": "营业总收入",
    "current": Decimal("52770984383.52"),   # 2025 年半年度，PDF 第 36 页
    "prior": Decimal("50648026578.65"),     # 2024 年半年度，PDF 第 36 页
    "pages": "PDF 第 16、36 页",
}

# 报告自列的同比，用于校验重算结果（PDF 第 6、12、16 页均为 4.19%）。
REPORT_STATED_YOY = Decimal("4.19")

# 2024 年半年度报告（PDF 第 6 页）自列的 2024 年上半年营业收入及其同比，
# 用于核对 2025 年报告“上年同期”列是否经过重述（第 7 页：无需追溯调整或重述）。
PRIOR_REPORT_2024H1 = {
    "revenue": Decimal("50648026578.65"),
    "yoy": Decimal("11.30"),
    "url": "https://static.cninfo.com.cn/finalpage/2024-08-29/1221032897.PDF",
}


def to_yi(amount: Decimal) -> Decimal:
    """元 -> 亿元，四舍五入保留两位小数。"""
    return (amount / YI).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def yoy_percent(current: Decimal, prior: Decimal) -> Decimal:
    """同比 =（本期 - 上年同期）/ 上年同期 × 100%，全精度计算后四舍五入到两位小数。"""
    return ((current - prior) / prior * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt(amount: Decimal) -> str:
    """千分位显示，保留两位小数，与报告列示格式一致。"""
    return f"{amount:,.2f}"


def build_row(item):
    current, prior = item["current"], item["prior"]
    return {
        "name": item["name"],
        "pages": item["pages"],
        "current_raw": str(current),
        "current_wan": str(current / Decimal("10000")),
        "current_yi_full": str(current / YI),
        "current_yi": str(to_yi(current)),
        "prior_raw": str(prior),
        "prior_wan": str(prior / Decimal("10000")),
        "prior_yi_full": str(prior / YI),
        "prior_yi": str(to_yi(prior)),
        "change_raw": str(current - prior),
        "change_yi": str(to_yi(current - prior)),
        "yoy_percent": str(yoy_percent(current, prior)),
    }


def main() -> int:
    rows = [build_row(REVENUE), build_row(TOTAL_OPERATING_REVENUE)]

    # --- 校验 1：报告列示的金额在“主要会计数据”“营业收入构成”“合并利润表”三处一致 ---
    assert REVENUE["current"] == TOTAL_OPERATING_REVENUE["current"]
    assert REVENUE["prior"] == TOTAL_OPERATING_REVENUE["prior"]

    # --- 校验 2：重算同比与报告自列值一致 ---
    for row in rows:
        assert Decimal(row["yoy_percent"]) == REPORT_STATED_YOY, row

    # --- 校验 3：亿元显示值 ---
    assert rows[0]["current_yi"] == "527.71"
    assert rows[0]["prior_yi"] == "506.48"

    # --- 校验 4：上年同期数与 2024 年半年度报告原文一致，未重述 ---
    assert REVENUE["prior"] == PRIOR_REPORT_2024H1["revenue"]
    assert yoy_percent(
        PRIOR_REPORT_2024H1["revenue"], Decimal("45506384818.37")
    ) == PRIOR_REPORT_2024H1["yoy"]

    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    header = (
        "| 项目 | 2025H1 原始金额（元） | 2025H1（亿元） | "
        "2024H1 原始金额（元） | 2024H1（亿元） | 变动额（元） | 同比 | PDF 页序 |"
    )
    print(header)
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for row in rows:
        print(
            f"| {row['name']} | {fmt(Decimal(row['current_raw']))} | {row['current_yi']} | "
            f"{fmt(Decimal(row['prior_raw']))} | {row['prior_yi']} | "
            f"{fmt(Decimal(row['change_raw']))} | {row['yoy_percent']}% | {row['pages']} |"
        )
    print()
    print("逐项代入：")
    for row in rows:
        print(
            f"  {row['name']}同比 = ({fmt(Decimal(row['current_raw']))} - "
            f"{fmt(Decimal(row['prior_raw']))}) / {fmt(Decimal(row['prior_raw']))} "
            f"× 100% = {row['yoy_percent']}%"
        )
    print()
    print("亿元换算：")
    for row in rows:
        print(
            f"  {row['name']}：{fmt(Decimal(row['current_raw']))} 元 / 100,000,000 = "
            f"{row['current_yi_full']} 亿元 → {row['current_yi']} 亿元；"
            f"{fmt(Decimal(row['prior_raw']))} 元 / 100,000,000 = {row['prior_yi_full']} 亿元 "
            f"→ {row['prior_yi']} 亿元"
        )
    print()
    print("校验通过：")
    print("  - 营业收入与营业总收入在 PDF 第 6、12、36 页金额一致；")
    print(f"  - 重算同比 {REPORT_STATED_YOY}% 与报告自列值一致；")
    print("  - 上年同期数与 2024 年半年度报告第 6 页一致，未重述。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
