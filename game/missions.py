from dataclasses import dataclass
from typing import Dict, Any
from thermo_engine.hohmann import compute_hohmann_targets


@dataclass(frozen=True)
class MissionSpec:
    id: str
    name: str
    difficulty: str
    brief: str
    alt_start_km: float
    alt_end_km: float
    # Locked CubeSat Bus Parameters
    V_tank_L: float
    P_init_MPa: float
    T_init_K: float
    m_dry_kg: float
    # Engineering Pass Criteria
    min_temp_K: float
    min_prop_left_pct: float
    max_peak_thrust_N: float  # Attitude-control structural/pointing limit


MISSIONS: Dict[str, MissionSpec] = {
    "Mission 1: LEO Orbit Raise (400 → 450 km)": MissionSpec(
        id="m1",
        name="Mission 1: LEO Orbit Raise (400 → 450 km)",
        difficulty="Standard",
        brief=(
            "Raise a 6U CubeSat from 400 km to 450 km circular orbit. "
            "Keep the propellant above the 230 K valve-freeze limit and retain at least 25% propellant reserve."
        ),
        alt_start_km=400.0,
        alt_end_km=450.0,
        V_tank_L=4.0,
        P_init_MPa=20.0,
        T_init_K=295.0,
        m_dry_kg=12.0,
        min_temp_K=230.0,
        min_prop_left_pct=25.0,
        max_peak_thrust_N=60.0,
    ),
    "Mission 2: Precision Attitude-Limited Transfer (400 → 475 km)": MissionSpec(
        id="m2",
        name="Mission 2: Precision Attitude-Limited Transfer (400 → 475 km)",
        difficulty="Hard",
        brief=(
            "Delicate optical payload limits peak thrust to 15.0 N. "
            "Use pressure regulation or throat sizing plus thermal management to reach 475 km without freezing the valve."
        ),
        alt_start_km=400.0,
        alt_end_km=475.0,
        V_tank_L=4.0,
        P_init_MPa=20.0,
        T_init_K=290.0,
        m_dry_kg=14.0,
        min_temp_K=230.0,
        min_prop_left_pct=15.0,
        max_peak_thrust_N=15.0,
    ),
    "Mission 3: Tight-Volume 3U MicroSat (380 → 460 km)": MissionSpec(
        id="m3",
        name="Mission 3: Tight-Volume 3U MicroSat (380 → 460 km)",
        difficulty="Expert",
        brief=(
            "A volume-starved 2.5 L tank must deliver a full 80 km orbit raise. "
            "Optimize propellant choice, resistojet heating, and coast-phase thermal recovery to survive Burn 2."
        ),
        alt_start_km=380.0,
        alt_end_km=460.0,
        V_tank_L=2.5,
        P_init_MPa=22.0,
        T_init_K=290.0,
        m_dry_kg=10.0,
        min_temp_K=230.0,
        min_prop_left_pct=10.0,
        max_peak_thrust_N=25.0,
    ),
}


def evaluate_mission(mission: MissionSpec, res: Dict[str, Any]) -> Dict[str, Any]:
    """Grade a completed Hohmann mission simulation against engineering criteria."""
    targets = compute_hohmann_targets(mission.alt_start_km, mission.alt_end_km)
    dv_target = targets["dv1_m_s"] + targets["dv2_m_s"]

    dv_achieved = float(res["dv"][-1])
    min_T = float(res["T"].min())
    prop_left_pct = 100.0 * float(res["m"][-1]) / float(res["m_init"])
    peak_F = float(res["F"].max())

    checks = [
        {
            "Criterion": "Target Orbit Δv Achieved",
            "Requirement": f"≥ {dv_target - 0.15:.2f} m/s",
            "Measured": f"{dv_achieved:.2f} m/s",
            "Passed": dv_achieved >= (dv_target - 0.15),
        },
        {
            "Criterion": "Valve Freeze Prevention",
            "Requirement": f"Min T ≥ {mission.min_temp_K:.0f} K",
            "Measured": f"{min_T:.1f} K",
            "Passed": min_T >= mission.min_temp_K,
        },
        {
            "Criterion": "Propellant Reserve Margin",
            "Requirement": f"≥ {mission.min_prop_left_pct:.0f}% remaining",
            "Measured": f"{prop_left_pct:.1f}%",
            "Passed": prop_left_pct >= mission.min_prop_left_pct,
        },
        {
            "Criterion": "Attitude-Control Thrust Cap",
            "Requirement": f"Peak F ≤ {mission.max_peak_thrust_N:.1f} N",
            "Measured": f"{peak_F:.2f} N",
            "Passed": peak_F <= mission.max_peak_thrust_N,
        },
    ]

    passed_all = all(c["Passed"] for c in checks)
    score = int(round(100.0 * sum(1 for c in checks if c["Passed"]) / len(checks)))

    return {
        "passed_all": passed_all,
        "score": score,
        "checks": checks,
        "dv_target": dv_target,
        "dv_achieved": dv_achieved,
        "min_T": min_T,
        "prop_left_pct": prop_left_pct,
        "peak_F": peak_F,
    }