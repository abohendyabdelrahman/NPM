# -*- coding: utf-8 -*-
"""online_trainer.rules — the A..L decision cascade (algorithm spec section 1-2).

A parameter dict holds the 21 fitted thresholds (letters A..Y/NX/NY as in the
v2 mapping table). evaluate() applies the cases in exact order; first match wins.
"""
from __future__ import annotations

# Names follow the spec mapping table. Missing params -> a KeyError tells you
# which file is wrong.
REQUIRED_PARAMS = [
    "E", "T", "L", "N", "D",            # z thresholds (sigma)
    "V", "S", "O",                       # percentile thresholds (%)
    "R",                                  # LDD_E (%)
    "J", "I",                             # LDD_F, L2DD_F (%)
    "X",                                  # LDD_G (%)
    "Z",                                  # LDD_H (%)
    "M", "K",                             # LDD_I, L2DD_I (%)
    "Y",                                  # NSDD_G (count)
    "A",                                  # NS2DD_I (count)
    "B", "C",                             # LDD_J, L2DD_J (%)
    "NY", "NX",                           # case A thresholds
]


def check_params(p):
    miss = [k for k in REQUIRED_PARAMS if k not in p]
    if miss:
        raise KeyError(f"missing parameters: {miss}")


def evaluate(feat, p):
    """feat: feature dict (z_deg, P_deg, LDD, L2DD, NSDD, NS2DD, analysable);
    p: parameter dict. Returns (verdict, case, detail_str)."""
    check_params(p)
    if not feat["analysable"]:
        return "Normal", "NO_ANALYSIS", "fewer than 10 clean points"

    z = feat["z_deg"]
    pct = feat["P_deg"]
    ldd = feat["LDD"]
    l2dd = feat["L2DD"]
    nsdd = feat["NSDD"]
    ns2dd = feat["NS2DD"]

    # Case A (new): LDV better-than-mean, but last-day degradation is large and rare
    if z <= 0 and ldd >= p["NY"] and nsdd <= p["NX"]:
        return "Problematic", "A", f"z={z:.2f}<=0, LDD={ldd:.1f}>={p['NY']}, NSDD={nsdd}<={p['NX']}"
    if z <= 0:
        return "Normal", "B", f"z={z:.2f}<=0"
    if z >= p["E"]:
        return "Problematic", "C", f"z={z:.2f}>={p['E']}"
    if pct >= p["V"]:
        return "Problematic", "D", f"P_deg={pct:.1f}>={p['V']}"
    if pct >= p["S"] and z >= p["T"]:
        return "Problematic", "E", f"P_deg={pct:.1f}>={p['S']}, z={z:.2f}>={p['T']}"
    if ldd <= p["R"]:
        return "Normal", "F", f"LDD={ldd:.1f}<={p['R']}"
    if ldd >= p["J"] and l2dd <= p["I"] and z <= p["L"]:
        return "Normal", "G", f"LDD={ldd:.1f}>={p['J']}, L2DD={l2dd:.1f}<={p['I']}, z={z:.2f}<={p['L']}"
    if ldd >= p["X"] and nsdd <= p["Y"]:
        return "Problematic", "H", f"LDD={ldd:.1f}>={p['X']}, NSDD={nsdd}<={p['Y']}"
    if ldd >= p["Z"] and (z >= p["N"] or pct >= p["O"]):
        return "Problematic", "I", f"LDD={ldd:.1f}>={p['Z']}, (z={z:.2f}>={p['N']} or P_deg={pct:.1f}>={p['O']})"
    if ldd <= p["M"] and l2dd >= p["K"] and ns2dd <= p["A"]:
        return "Problematic", "J", f"LDD={ldd:.1f}<={p['M']}, L2DD={l2dd:.1f}>={p['K']}, NS2DD={ns2dd}<={p['A']}"
    if ldd <= p["B"] and l2dd >= p["C"] and z >= p["D"]:
        return "Problematic", "K", f"LDD={ldd:.1f}<={p['B']}, L2DD={l2dd:.1f}>={p['C']}, z={z:.2f}>={p['D']}"
    return "Normal", "L", "otherwise"


def verdict_binary(verdict):
    return 1 if verdict == "Problematic" else 0
