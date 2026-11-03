#!/usr/bin/env python3
"""复算并校验白酒晨会简报的数据、口径与字数。

数据来自本目录 data.json（由前序已交付底稿汇总）；本脚本不重新取数，
只验证：亿元显示值、同比复算、行情交叉核对、板块成交额/涨跌家数、
宏观水平复算差异、以及 brief.md 的字数与关键数值是否一致。
"""
from decimal import Decimal, ROUND_HALF_UP
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
checks = []


def check(name, condition, detail=""):
    checks.append((name, bool(condition), detail))
    print(("PASS" if condition else "FAIL"), "-", name, ("| " + detail) if detail else "")


def q2(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def q0(value):
    return Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def yi(raw):
    return q2(Decimal(raw) / Decimal(100_000_000))


def yoy(raw, prior):
    return q2((Decimal(raw) - Decimal(prior)) / Decimal(prior) * Decimal(100))


data = json.loads((BASE / "data.json").read_text())
brief = (BASE / "brief.md").read_text()

# ---------- 1. 三家公司：亿元显示值、累计同比、价格/PE 舍入 ----------
for company in data["companies"]:
    name = company["name"]
    fin = company["financials"]
    for metric in ("revenue", "net_profit"):
        item = fin[metric]
        check(f"{name} {metric} 亿元显示值", yi(item["raw_cny"]) == q2(item["yi"]),
              f"{item['raw_cny']} -> {yi(item['raw_cny'])}")
        check(f"{name} {metric} 累计同比复算", yoy(item["raw_cny"], item["prior_raw_cny"]) == q2(item["yoy_pct"]),
              f"{yoy(item['raw_cny'], item['prior_raw_cny'])}%")
    if "total_operating_revenue" in fin:
        item = fin["total_operating_revenue"]
        check(f"{name} 营业总收入亿元显示值", yi(item["raw_cny"]) == q2(item["yi"]), f"{yi(item['raw_cny'])}")
    for metric in ("revenue", "net_profit"):
        item = fin["q3"][metric]
        check(f"{name} Q3 {metric} 亿元显示值", yi(item["raw_cny"]) == q2(item["yi"]), f"{yi(item['raw_cny'])}")
        if item.get("prior_raw_cny"):
            check(f"{name} Q3 {metric} 同比复算（基数精度见注）",
                  yoy(item["raw_cny"], item["prior_raw_cny"]) == q2(item["yoy_pct"]),
                  f"{yoy(item['raw_cny'], item['prior_raw_cny'])}%")
    quote = company["quote"]
    check(f"{name} PE TTM 舍入", q2(quote["pe_ttm_raw"]) == q2(quote["pe_ttm"]), f"{quote['pe_ttm_raw']} -> {q2(quote['pe_ttm_raw'])}")
    check(f"{name} 涨跌幅舍入", q2(quote["change_pct_raw"]) == q2(quote["change_pct"]), f"{q2(quote['change_pct_raw'])}%")

# ---------- 2. 板块：成交额合计、涨跌家数、领涨/领跌 ----------
sector = data["sector"]
consts = sector["constituents"]
amount_sum = sum(Decimal(c["amount_cny"]) for c in consts)
sector_amount = Decimal(sector["amount_cny"])
check("板块成交额合计与指数快照一致（差额 < 13 元）", abs(amount_sum - sector_amount) < Decimal("13"),
      f"sum={amount_sum} index={sector_amount} diff={abs(amount_sum - sector_amount)}")
up = sum(1 for c in consts if Decimal(str(c["change_pct"])) > 0)
down = sum(1 for c in consts if Decimal(str(c["change_pct"])) < 0)
check("成分股 17 涨 2 跌", up == 17 and down == 2 and len(consts) == 19, f"{up} up / {down} down / {len(consts)} total")
check("板块涨跌幅舍入", q2(sector["change_pct_raw"]) == q2(sector["change_pct"]), f"{sector['change_pct_raw']} -> {sector['change_pct']}")
check("板块成交额亿元显示值", q2(sector_amount / Decimal(100_000_000)) == q2(sector["amount_yi"]), f"{q2(sector_amount / Decimal(100_000_000))} 亿元")
gainer = max(consts, key=lambda c: Decimal(str(c["change_pct"])))
loser = min(consts, key=lambda c: Decimal(str(c["change_pct"])))
check("领涨为皇台酒业且 +10.00%", gainer["name"] == "皇台酒业" and q2(gainer["change_pct"]) == Decimal("10.00"), f"{gainer['name']} {q2(gainer['change_pct'])}")
check("领跌为迎驾贡酒且 -5.03%", loser["name"] == "迎驾贡酒" and q2(loser["change_pct"]) == Decimal("-5.03"), f"{loser['name']} {q2(loser['change_pct'])}")

# ---------- 3. 板块成分股与三家公司行情交叉核对 ----------
by_code = {c["code"]: c for c in consts}
for company in data["companies"]:
    code = company["code"]
    quote = company["quote"]
    check(f"{company['name']} 行情与板块成分股表一致",
          code in by_code
          and Decimal(str(by_code[code]["price"])) == Decimal(str(quote["price_cny"]))
          and q2(by_code[code]["change_pct"]) == q2(quote["change_pct"]),
          f"{code} {by_code.get(code, {}).get('price')} {q2(by_code[code]['change_pct']) if code in by_code else 'missing'}%")

# ---------- 4. 宏观：水平复算与可比口径差异 ----------
macro = data["macro"]
sr = macro["social_retail_total"]
check("社零当月同比水平复算", q2(Decimal(str(sr["month_value_yi"])) / Decimal(str(sr["prior_year_same_month_value_yi"])) * 100 - 100) == Decimal("1.10"),
      f"{q2(Decimal(str(sr['month_value_yi'])) / Decimal(str(sr['prior_year_same_month_value_yi'])) * 100 - 100)}%")
check("社零发布稿取整", q0(Decimal(str(sr["month_value_yi"]))) == Decimal(str(sr["release_month_value_yi"])), f"{sr['month_value_yi']} -> {q0(Decimal(str(sr['month_value_yi'])))}")
ta = macro["tobacco_alcohol_retail"]
level_yoy = q2(Decimal(str(ta["month_value_yi"])) / Decimal(str(ta["prior_year_same_month_value_yi"])) * 100 - 100)
check("烟酒类水平复算 = +7.77%（非发布同比）", level_yoy == Decimal("7.77"), f"{level_yoy}%")
check("烟酒类发布同比与水平复算差 = 6.03pct", q2(Decimal(str(ta["month_yoy_pct"])) - level_yoy) == Decimal("6.03"),
      f"{q2(Decimal(str(ta['month_yoy_pct'])) - level_yoy)}pct")
check("烟酒类发布稿取整", q0(Decimal(str(ta["month_value_yi"]))) == Decimal(str(ta["release_month_value_yi"])), f"{ta['month_value_yi']} -> {q0(Decimal(str(ta['month_value_yi'])))}")

# ---------- 5. 简报字数与关键数值 ----------
non_table = [line for line in brief.splitlines() if line.strip() and not line.lstrip().startswith("|")]
prose = []
for line in non_table:
    if line.startswith("**表"):
        break
    prose.append(line)
prose_chars = sum(len(re.sub(r"\s", "", line)) for line in prose)
nontable_chars = sum(len(re.sub(r"\s", "", line)) for line in non_table)
check("简报正文 ≤ 500 字", prose_chars <= 500, f"{prose_chars} 字（非空白字符）")
check("简报正文与 meta 记录一致", prose_chars == data["meta"]["brief_prose_char_count"], f"{prose_chars}")
check("简报含表格外全部文字 ≤ 500 字", nontable_chars <= 500, f"{nontable_chars} 字（含表题）")
check("简报含表格外文字与 meta 记录一致", nontable_chars == data["meta"]["brief_nontable_char_count"], f"{nontable_chars}")

expected_strings = [
    "1.11%", "126.87", "17 涨 2 跌", "皇台酒业 +10.00%", "迎驾贡酒 -5.03%",
    "13.32 亿元", "-57.03%", "42,432.5", "+1.1%", "662.6", "+13.8%", "+7.77%", "6.03pct",
    "1,457.66", "+1.29%", "22.18", "1,309.71", "+1.96%", "644.67", "-0.25%",
    "75.17", "+1.24%", "23.94", "328.58", "+7.25%", "97.11", "+49.98%",
    "80.51", "+0.93%", "20.65", "146.68", "-36.58%", "56.71", "-47.31%",
    "402.67", "+3.08%", "199.51", "+3.78%", "44.42", "-37.68%", "9.58", "-48.25%",
    "41.95", "-37.14%", "39,779.84", "1,332.84", "+1.82%",
]
missing = [s for s in expected_strings if s not in brief]
check("简报包含全部关键数值", not missing, f"missing={missing}" if missing else f"{len(expected_strings)} strings")

# ---------- 6. 结构完整性 ----------
check("三家公司齐全", [c["name"] for c in data["companies"]] == ["贵州茅台", "五粮液", "泸州老窖"])
check("板块 19 只成分股", len(consts) == 19)
check("新闻 3 条", len(data["news"]) == 3)
check("已核实/待核实/缺口清单非空", bool(data["status"]["verified"]) and bool(data["status"]["pending"]) and bool(data["status"]["gaps"]))
check("无占位数字", not re.search(r"(待补|N/A|TODO|TBD)", brief))

failed = [c for c in checks if not c[1]]
print()
if failed:
    print(f"{len(failed)} CHECK(S) FAILED")
    sys.exit(1)
print(f"ALL {len(checks)} CHECKS PASSED")
