#!/usr/bin/env python3
"""Recompute and assert the Moutai morning-card figures from data.json."""
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

D = json.loads((Path(__file__).with_name("data.json")).read_text(encoding="utf-8"))
TWO = Decimal("0.01")
THREE = Decimal("0.001")


def dec(x):
    return Decimal(str(x))


def r2(x):
    return dec(x).quantize(TWO, rounding=ROUND_HALF_UP)


def r3(x):
    return dec(x).quantize(THREE, rounding=ROUND_HALF_UP)


def yi(raw):
    return dec(raw) / Decimal("100000000")


def yoy(a, b):
    return (dec(a) - dec(b)) / abs(dec(b)) * Decimal("100")


checks = []


def check(name, got, want, note=""):
    ok = got == want
    checks.append(ok)
    print(f"{'OK ' if ok else 'FAIL'} {name}: {got} (expected {want}) {note}".rstrip())


fin = D["financials"]
rev = fin["revenue"]
np = fin["net_profit_attributable"]
tor = fin["total_operating_revenue"]
ttm = fin["ttm_net_profit_attributable"]
quote = D["quote"]

print("== 营业收入 ==")
print("raw", rev["raw_cny"], "prior", rev["prior_raw_cny"])
check("营业收入同比", r2(yoy(rev["raw_cny"], rev["prior_raw_cny"])), dec(rev["yoy_display_pct"]))
check("营业收入亿元", r2(yi(rev["raw_cny"])), dec(rev["display_yi"]))
check("上年同期营业收入亿元", r2(yi(rev["prior_raw_cny"])), dec(rev["prior_display_yi"]))

print("\n== 归母净利润 ==")
print("raw", np["raw_cny"], "prior", np["prior_raw_cny"])
check("归母净利润同比", r2(yoy(np["raw_cny"], np["prior_raw_cny"])), dec(np["yoy_display_pct"]))
check("归母净利润亿元", r2(yi(np["raw_cny"])), dec(np["display_yi"]))
check("上年同期归母净利润亿元", r2(yi(np["prior_raw_cny"])), dec(np["prior_display_yi"]))

print("\n== 营业总收入（参考口径） ==")
check("营业总收入同比", r2(yoy(tor["raw_cny"], tor["prior_raw_cny"])), dec(tor["yoy_display_pct"]))
check("营业总收入亿元", r2(yi(tor["raw_cny"])), dec(tor["display_yi"]))
diff = dec(tor["raw_cny"]) - dec(rev["raw_cny"])
print("营业总收入-营业收入 =", diff, "元 =", r2(yi(diff)), "亿元")
check("两口径差额", r2(yi(diff)), Decimal("23.13"))

print("\n== 2026Q3 单季（补充口径） ==")
sq = fin["single_quarter_2026q3"]
sq_rev = sq["revenue"]
sq_np = sq["net_profit_attributable"]
check("单季营业收入亿元", r2(yi(sq_rev["raw_cny"])), dec(sq_rev["display_yi"]))
check("单季营业收入同比", r2(yoy(sq_rev["raw_cny"], str(dec(sq_rev["prior_display_yi"]) * Decimal("100000000")))), dec(sq_rev["yoy_display_pct"]))
check("单季上年同期营业收入亿元", r2(dec(sq_rev["prior_display_yi"])), Decimal("390.64"))
check("单季归母净利润亿元", r2(yi(sq_np["raw_cny"])), dec(sq_np["display_yi"]))
check("单季归母净利润同比", r2(yoy(sq_np["raw_cny"], sq_np["prior_raw_cny"])), dec(sq_np["yoy_display_pct"]))
check("单季上年同期归母净利润亿元", r2(yi(sq_np["prior_raw_cny"])), dec(sq_np["prior_display_yi"]))

print("\n== TTM 归母净利润与市盈率 ==")
comp = ttm["components"]
ttm_calc = dec(comp["fy2025_raw_cny"]) - dec(comp["cumulative_2025_9m_raw_cny"]) + dec(comp["cumulative_2026_9m_raw_cny"])
check("TTM归母净利润(元)", ttm_calc, dec(ttm["raw_cny"]))
check("TTM归母净利润(亿元)", r2(yi(ttm_calc)), dec(ttm["display_yi"]))
pe_calc = dec(quote["total_market_cap_cny"]) / ttm_calc
check("PE(TTM)复算(6位)", pe_calc.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP), Decimal("22.178401"))
check("PE(TTM)显示", r2(pe_calc), dec(quote["pe_ttm_display"]))
check("PE(TTM)接口值一致", pe_calc.quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP), Decimal("22.1784006"))

print("\n== 行情快照 ==")
prev = dec(quote["latest_price_cny"]) / (1 + dec(quote["change_pct"]) / 100)
check("前收盘价(元)", r2(prev), dec(quote["prev_close_cny"]))
shares = dec(quote["total_market_cap_cny"]) / dec(quote["latest_price_cny"])
check("总股本(股)", shares.quantize(Decimal("1"), rounding=ROUND_HALF_UP), Decimal(D["verification"]["total_shares_recalc"]))
prev_pe = (prev * shares) / ttm_calc
check("前收盘PE(TTM,3位)", r3(prev_pe), dec(D["verification"]["daily_pe_crosscheck"]))
check("最新价显示", dec(quote["latest_price_cny"]), dec(quote["latest_price_display_cny"]))
check("涨跌幅显示", r2(quote["change_pct"]), dec(quote["change_display_pct"]))
check("总市值亿元", r2(yi(quote["total_market_cap_cny"])), dec(quote["total_market_cap_display_yi"]))

print("\n== 报告期 ==")
check("报告期末", fin["report"]["period_end"], "2026-09-30")
check("披露日期", fin["report"]["disclosure_date"], "2026-10-31")
check("审计状态", fin["report"]["audited"], False)
print("累计区间", fin["report"]["cumulative_start"], "至", fin["report"]["period_end"])
print("上年同期", fin["report"]["comparative_start"], "至", fin["report"]["period_end"].replace("2026", "2025"))

print("\n== 汇总 ==")
if all(checks):
    print(f"ALL {len(checks)} CHECKS PASSED")
else:
    print(f"{sum(checks)}/{len(checks)} CHECKS PASSED")
    raise SystemExit(1)
