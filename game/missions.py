from thermo_engine.hohmann import compute_hohmann_targets

MISSIONS = {
    "Mission 1 — LEO Hohmann Orbit Raising": {
        "type": "hohmann",
        "alt1_km": 400.0,
        "alt2_km": 450.0,
        "m_dry": 12.0,
        "V_tank_L": 4.0,
        "P_init_MPa": 20.0,
        "T_init_K": 295.0,
        "eta_nozzle": 0.90,
        "briefing": (
            "Raise a **12 kg CubeSat** (locked 4.0 L tank at 20 MPa) from a **400 km** circular orbit to **450 km** "
            "using a two-burn Hohmann transfer (Burn 1 → 46.4 min Coast → Burn 2). Tune your propellant, nozzle, "
            "and thermal controls to complete both burns without freezing the thruster valve or exhausting your reserve."
        ),
        "constraints": {
            "min_T_K": 230.0,
            "min_prop_margin_pct": 10.0,
            "max_heater_W": 50.0,
        },
    },
    "Mission 2 — High-Altitude Hohmann (Power-Limited)": {
        "type": "hohmann",
        "alt1_km": 400.0,
        "alt2_km": 500.0,
        "m_dry": 10.0,
        "V_tank_L": 3.5,
        "P_init_MPa": 20.0,
        "T_init_K": 290.0,
        "eta_nozzle": 0.90,
        "briefing": (
            "Transfer a **10 kg CubeSat** (locked 3.5 L tank at 20 MPa) from **400 km** to **500 km** (higher $\\Delta v$ demand). "
            "Your solar array limits the Resistojet Heater to **≤ 35 W**. Use coast-phase thermal recovery "
            "and propellant selection wisely to avoid valve freezing."
        ),
        "constraints": {
            "min_T_K": 230.0,
            "min_prop_margin_pct": 5.0,
            "max_heater_W": 35.0,
        },
    },
    "Mission 3 — Rapid Burn Freeze Guard": {
        "type": "hohmann",
        "alt1_km": 400.0,
        "alt2_km": 435.0,
        "m_dry": 15.0,
        "V_tank_L": 3.0,
        "P_init_MPa": 22.0,
        "T_init_K": 290.0,
        "eta_nozzle": 0.90,
        "briefing": (
            "Execute a tight **400 km → 435 km** transfer for a heavy **15 kg CubeSat** (locked 3.0 L tank at 22 MPa) "
            "while keeping tank temperature strictly above **245 K** (strict seal margin) and finishing with **≥ 15%** propellant remaining."
        ),
        "constraints": {
            "min_T_K": 245.0,
            "min_prop_margin_pct": 15.0,
            "max_heater_W": 60.0,
        },
    },
}


def evaluate_mission(mission_key: str, res: dict, targets: dict, Q_heater: float, cons: dict) -> dict:
    """Evaluate mission pass/fail criteria and compute an engineering-based score."""
    c = MISSIONS[mission_key]["constraints"]
    dv_target = targets["dv_total_m_s"]
    dv_achieved = float(res["dv"][-1])
    dv_pct = 100.0 * dv_achieved / max(1e-6, dv_target)

    min_T = float(res["T"].min())
    prop_margin_pct = 100.0 * float(res["m"][-1]) / max(1e-9, float(res["m_init"]))

    checks = [
        ("Target Δv Achieved (≥ 99%)", dv_achieved >= 0.99 * dv_target, f"{dv_achieved:.2f} / {dv_target:.2f} m/s ({dv_pct:.1f}%)"),
        (f"Valve Freeze Guard (T ≥ {c['min_T_K']:.0f} K)", min_T >= c["min_T_K"], f"Min T = {min_T:.1f} K"),
        (f"Propellant Margin (≥ {c['min_prop_margin_pct']:.0f}%)", prop_margin_pct >= c["min_prop_margin_pct"], f"Remaining = {prop_margin_pct:.1f}%"),
        (f"Heater Power Budget (≤ {c['max_heater_W']:.0f} W)", Q_heater <= c["max_heater_W"], f"Heater = {Q_heater:.0f} W"),
        ("First Law Conservation (< 1e-5)", cons["passed"], f"Rel Err = {cons['energy_rel_err']:.2e}"),
    ]

    passed_all = all(item[1] for item in checks)
    # Engineering score: 70 pts for passing constraints + up to 30 pts for propellant & thermal efficiency
    base_pts = 70.0 * (sum(1 for item in checks if item[1]) / len(checks))
    eff_pts = min(15.0, prop_margin_pct * 0.5) + min(15.0, max(0.0, (min_T - c["min_T_K"]) * 0.3))
    score = round(base_pts + (eff_pts if passed_all else 0.0), 1)

    return {
        "passed_all": passed_all,
        "score": score,
        "checks": checks,
        "prop_margin_pct": prop_margin_pct,
        "min_T": min_T,
    }