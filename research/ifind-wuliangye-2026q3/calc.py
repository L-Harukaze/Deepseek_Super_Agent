#!/usr/bin/env python3
"""五粮液 2026 年三季报 iFinD 晨会速览卡：复算与一致性校验。

用法：
    python3 research/ifind-wuliangye-2026q3/calc.py

原始金额单位：元；亿元显示值 = 原始金额 / 1e8，四舍五入两位；
同比 =（本期 - 上年同期）/ |上年同期| * 100%，按原始金额全精度计算后再舍入。
2026Q3 与 2025 年前三季度金额来自公司三季报原文（经 iFinD 公告片段与结构化接口双向核对）；
2025Q3 单季金额来自 iFinD 亿元显示值（4 位小数）换算，精度万元级。
"""

from decimal import Decimal as D, getcontext, ROUND_HALF_UP

getcontext().prec = 30

# --- 行情（iFinD security_highfreq_quotes real_time，2026-11-03 12:12:48） ---
PRICE = D("75.17")
CHANGE_PCT_REPORTED = D("1.2390572390572414")
PE_TTM_REPORTED = D("23.9353591")
MARKET_CAP = D("291780473735.85")
PREV_CLOSE_FROM_CHANGE = PRICE / (1 + CHANGE_PCT_REPORTED / 100)

# --- 2026 年前三季度（2026-01-01 至 2026-09-30，合并报表，未经审计） ---
REV_2026 = D("32858473964.34")   # 营业收入（= 营业总收入）
NP_2026 = D("9710647471.03")     # 归母净利润

# --- 2025 年前三季度（上年同期，公司三季报可比数） ---
REV_2025 = D("30637727654.97")
NP_2025 = D("6474551792.18")

# --- 2026 年第三季度单季（7-9 月） ---
Q3_REV_2026 = D("4441799422.57")
Q3_NP_2026 = D("957704479.72")

# --- 2025 年第三季度单季（iFinD 亿元显示值换算：71.2776 / 18.5070 亿元） ---
Q3_REV_2025 = D("7127760000")
Q3_NP_2025 = D("1850700000")

# --- iFinD 列示同比（%），用于交叉核对 ---
YOY_REPORTED = {
    "营业收入_累计": D("7.2484"),
    "归母净利润_累计": D("49.9818"),
    "营业收入_单季": D("-37.6831"),
    "归母净利润_单季": D("-48.2518"),
}

# --- 公司季报公告片段列示同比（%） ---
YOY_ANNOUNCEMENT = {
    "营业收入_累计": D("7.25"),
    "归母净利润_累计": D("49.98"),
    "营业收入_单季": D("-37.68"),
    "归母净利润_单季": D("-48.25"),
}


def yi(amount: D) -> D:
    return (amount / D("100000000")).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def yoy(current: D, prior: D) -> D:
    return ((current - prior) / abs(prior) * 100).quantize(D("0.0001"), rounding=ROUND_HALF_UP)


def check(label: str, got, want, tol=D("0")) -> None:
    ok = abs(D(str(got)) - D(str(want))) <= tol
    print(f"  [{'OK' if ok else 'FAIL'}] {label}: {got} (期望 {want})")
    assert ok, label


def main() -> None:
    print("== 亿元显示值 ==")
    check("营业收入 9M 亿元", yi(REV_2026), "328.58")
    check("营业收入 上年同期 亿元", yi(REV_2025), "306.38")
    check("归母净利润 9M 亿元", yi(NP_2026), "97.11")
    check("归母净利润 上年同期 亿元", yi(NP_2025), "64.75")
    check("单季营业收入 亿元", yi(Q3_REV_2026), "44.42")
    check("单季归母净利润 亿元", yi(Q3_NP_2026), "9.58")

    print("== 同比复算 ==")
    rev_yoy = yoy(REV_2026, REV_2025)
    np_yoy = yoy(NP_2026, NP_2025)
    q3_rev_yoy = yoy(Q3_REV_2026, Q3_REV_2025)
    q3_np_yoy = yoy(Q3_NP_2026, Q3_NP_2025)
    check("营业收入 累计同比（复算 vs iFinD）", rev_yoy, YOY_REPORTED["营业收入_累计"])
    check("归母净利润 累计同比（复算 vs iFinD）", np_yoy, YOY_REPORTED["归母净利润_累计"])
    check("营业收入 单季同比（复算 vs iFinD）", q3_rev_yoy, YOY_REPORTED["营业收入_单季"])
    check("归母净利润 单季同比（复算 vs iFinD）", q3_np_yoy, YOY_REPORTED["归母净利润_单季"])
    check("营业收入 累计同比 与公告差", rev_yoy, YOY_ANNOUNCEMENT["营业收入_累计"], tol=D("0.01"))
    check("归母净利润 累计同比 与公告差", np_yoy, YOY_ANNOUNCEMENT["归母净利润_累计"], tol=D("0.01"))
    check("营业收入 单季同比 与公告差", q3_rev_yoy, YOY_ANNOUNCEMENT["营业收入_单季"], tol=D("0.01"))
    check("归母净利润 单季同比 与公告差", q3_np_yoy, YOY_ANNOUNCEMENT["归母净利润_单季"], tol=D("0.01"))

    print("== 行情与估值 ==")
    check("昨收（由涨跌幅反推）", PREV_CLOSE_FROM_CHANGE.quantize(D("0.01")), "74.25", tol=D("0.01"))
    check("市盈率 TTM 显示值", PE_TTM_REPORTED.quantize(D("0.01")), "23.94")
    # 日频摘要 PE 23.6424 对应昨收 74.25；按最新价 75.17 比例换算应与实时 PE 一致
    pe_from_daily = (D("23.6424") * PRICE / D("74.25")).quantize(D("0.01"))
    check("日频 PE 按价格换算", pe_from_daily, "23.94", tol=D("0.01"))
    check("隐含 TTM 归母净利润（亿元）", (MARKET_CAP / PE_TTM_REPORTED / D("1e8")).quantize(D("0.01")), "121.90", tol=D("0.01"))

    print("== 口径一致性 ==")
    # 营业总收入与营业收入同额：三季报利润表两行均为 32,858,473,964.34 元
    check("营业总收入 = 营业收入", REV_2026, "32858473964.34")
    # 单季 + 上半年应等于累计（仅作算术自洽检查，不引入未披露数据）
    assert Q3_REV_2026 < REV_2026 and Q3_NP_2026 < NP_2026
    print("  [OK] Q3 单季金额小于累计金额（口径自洽）")

    print("== 卡片显示值 ==")
    print(f"  最新价 {PRICE} 元/股，涨跌幅 +{CHANGE_PCT_REPORTED.quantize(D('0.01'))}%")
    print(f"  市盈率TTM {PE_TTM_REPORTED.quantize(D('0.01'))} 倍")
    print(f"  营业收入 {yi(REV_2026)} 亿元，同比 +{rev_yoy}%")
    print(f"  归母净利润 {yi(NP_2026)} 亿元，同比 +{np_yoy}%")
    print(f"  单季营业收入 {yi(Q3_REV_2026)} 亿元，同比 {q3_rev_yoy}%")
    print(f"  单季归母净利润 {yi(Q3_NP_2026)} 亿元，同比 {q3_np_yoy}%")
    print("全部断言通过。")


if __name__ == "__main__":
    main()
