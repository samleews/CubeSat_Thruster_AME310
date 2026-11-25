import numpy as np
from .fluid_props import IdealGas
from .nozzle_sssf import solve_sssf_thruster
from .tank_transient import simulate_hohmann_mission

def _trapz(y, x):
    """NumPy 1.x / 2.x compatible trapezoidal integration."""
    return np.trapezoid(y, x) if hasattr(np, "trapezoid") else np.trapz(y, x)

def audit_conservation(res: dict, gas: IdealGas) -> dict:
    """
    Verify First Law energy conservation and mass conservation
    for the transient propellant tank control volume.
    """
    m_init = res["m"][0]
    m_final = res["m"][-1]
    T_init = res["T"][0]
    T_final = res["T"][-1]

    # 1. Energy Balance: dU_tank = Q_in - E_out
    U_init = m_init * gas.cv * T_init
    U_final = m_final * gas.cv * T_final
    dU_actual = U_final - U_init
    dU_expected = res["Q_in"][-1] - res["E_out"][-1]

    energy_residual_J = abs(dU_actual - dU_expected)
    energy_rel_err = energy_residual_J / U_init if U_init > 0 else 0.0

    # 2. Mass Balance: (m_init - m_final) vs integral(m_dot dt)
    dm_tank = m_init - m_final
    m_expelled_trapz = _trapz(res["m_dot"], res["t"])
    mass_residual_kg = abs(dm_tank - m_expelled_trapz)
    mass_rel_err = mass_residual_kg / m_init if m_init > 0 else 0.0

    # 3. Physical Consistency
    physically_valid = bool(
        np.all(res["m"] > 0) and np.all(res["T"] > 0) and np.all(res["P"] > 0)
    )

    return {
        "U_init_kJ": U_init / 1000.0,
        "U_final_kJ": U_final / 1000.0,
        "Q_in_kJ": res["Q_in"][-1] / 1000.0,
        "E_out_kJ": res["E_out"][-1] / 1000.0,
        "energy_residual_J": energy_residual_J,
        "energy_rel_err": energy_rel_err,
        "mass_residual_kg": mass_residual_kg,
        "mass_rel_err": mass_rel_err,
        "physically_valid": physically_valid,
        "passed": (energy_rel_err < 1e-5) and physically_valid,
    }

def audit_second_law(
    res: dict,
    gas: IdealGas,
    A_throat: float,
    area_ratio: float,
    eta_nozzle: float = 0.92,
    Q_heater: float = 0.0,
    regulated: bool = False,
    P_reg_set: float = 5.0e5,
) -> dict:
    """Verify Second Law compliance (S_gen >= 0) across all active burn states."""
    s_gen_vals = []
    for i, phase in enumerate(res["phase"]):
        if phase != "Coast":
            sssf = solve_sssf_thruster(
                res["P"][i], res["T"][i], gas, A_throat, area_ratio,
                eta_nozzle, Q_heater, regulated, P_reg_set
            )
            s_gen_vals.append(sssf["S_gen_nozzle_W_K"])

    min_s_gen = float(np.min(s_gen_vals)) if s_gen_vals else 0.0
    max_s_gen = float(np.max(s_gen_vals)) if s_gen_vals else 0.0

    return {
        "min_S_gen_W_K": min_s_gen,
        "max_S_gen_W_K": max_s_gen,
        "passed": min_s_gen >= -1e-12,
    }

def benchmark_analytical_blowdown(
    gas: IdealGas,
    V_tank: float,
    P_init: float,
    T_init: float,
    m_dry: float,
    A_throat: float,
    area_ratio: float,
) -> dict:
    """
    Compare the transient ODE solver (with Q_tank_wall = 0) against the exact
    analytical isentropic blowdown relation: T/T0 = (P/P0)^((gamma-1)/gamma).
    """
    res = simulate_hohmann_mission(
        gas=gas, V_tank=V_tank, P_init=P_init, T_init=T_init, m_dry=m_dry,
        A_throat=A_throat, area_ratio=area_ratio,
        dv1_target=15.0, dv2_target=0.0, t_coast=0.0,
        Q_heater=0.0, Q_tank_wall=0.0, regulated=False,
    )
    exponent = (gas.gamma - 1.0) / gas.gamma
    T_analytical = T_init * (res["P"] / P_init) ** exponent
    max_abs_err_K = float(np.max(np.abs(res["T"] - T_analytical)))
    max_rel_err = float(np.max(np.abs(res["T"] - T_analytical) / T_analytical))

    return {
        "max_abs_err_K": max_abs_err_K,
        "max_rel_err": max_rel_err,
        "passed": max_rel_err < 1e-5,
    }

def check_solver_stability(sim_kwargs: dict) -> dict:
    """
    Verify numerical convergence by running the mission at coarse, baseline,
    and fine ODE solver tolerances.
    """
    settings = [
        ("Coarse (1e-5)", 1e-5, 1e-7),
        ("Baseline (1e-7)", 1e-7, 1e-9),
        ("Fine (1e-9)", 1e-9, 1e-11),
    ]
    runs = {}
    for label, rtol, atol in settings:
        kw = dict(sim_kwargs, rtol=rtol, atol=atol)
        r = simulate_hohmann_mission(**kw)
        runs[label] = {
            "dv_final": float(r["dv"][-1]),
            "m_final": float(r["m"][-1]),
            "T_min": float(r["T"].min()),
        }

    base = runs["Baseline (1e-7)"]
    fine = runs["Fine (1e-9)"]
    dv_diff = abs(base["dv_final"] - fine["dv_final"]) / max(1e-9, fine["dv_final"])
    m_diff = abs(base["m_final"] - fine["m_final"]) / max(1e-9, fine["m_final"])
    T_diff = abs(base["T_min"] - fine["T_min"]) / max(1e-9, fine["T_min"])

    return {
        "runs": runs,
        "dv_rel_diff": dv_diff,
        "m_rel_diff": m_diff,
        "T_rel_diff": T_diff,
        "passed": max(dv_diff, m_diff, T_diff) < 1e-4,
    }