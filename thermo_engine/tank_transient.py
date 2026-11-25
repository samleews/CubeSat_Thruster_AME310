import numpy as np
from scipy.integrate import solve_ivp
from .fluid_props import IdealGas
from .nozzle_sssf import solve_sssf_thruster

def simulate_hohmann_mission(
    gas: IdealGas,
    V_tank: float, # Tank volume [m^3]
    P_init: float, # Initial tank pressure [Pa]
    T_init: float, # Initial tank temperature [K]
    m_dry: float, # Spacecraft dry mass [kg]
    A_throat: float, # Nozzle throat area [m^2]
    area_ratio: float, # Nozzle Ae/A* [-]
    dv1_target: float, # Burn 1 target delta-v [m/s]
    dv2_target: float, # Burn 2 target delta-v [m/s]
    t_coast: float, # Coast duration [s]
    eta_nozzle: float = 0.92,
    Q_heater: float = 0.0, # Resistojet heater power during burns [W]
    Q_tank_wall: float = 0.0, # Ambient/electronics heat into tank [W]
    regulated: bool = False,
    P_reg_set: float = 5.0e5,
    m_min_frac: float = 0.02, # Stop burn if mass drops below 2% of initial
    max_burn_time: float = 3600.0,
    rtol: float = 1e-7,
    atol: float = 1e-9,
) -> dict:
    """
    Simulate the coupled transient tank + SSSF thruster across:
    Phase 1 (Burn 1) -> Phase 2 (Coast) -> Phase 3 (Burn 2).
    """
    m_init = (P_init * V_tank) / (gas.R * T_init)
    m_min = m_min_frac * m_init

    def make_burn_ode(dv_goal):
        def ode(t, y):
            m, T, dv, E_out, Q_in = y
            P = (m * gas.R * T) / V_tank
            sssf = solve_sssf_thruster(
                P, T, gas, A_throat, area_ratio, eta_nozzle, Q_heater, regulated, P_reg_set
            )
            m_dot = sssf["m_dot_kg_s"]
            F = sssf["thrust_N"]

            dm_dt = -m_dot
            dT_dt = (Q_tank_wall / (m * gas.cv)) - (gas.gamma - 1.0) * (T / m) * m_dot
            ddv_dt = F / (m_dry + m)
            dE_out_dt = m_dot * gas.cp * T  # Enthalpy leaving tank control volume
            dQ_in_dt = Q_tank_wall
            return [dm_dt, dT_dt, ddv_dt, dE_out_dt, dQ_in_dt]

        def event_dv_reached(t, y):
            return y[2] - dv_goal
        event_dv_reached.terminal = True
        event_dv_reached.direction = 1

        def event_tank_empty(t, y):
            return y[0] - m_min
        event_tank_empty.terminal = True
        event_tank_empty.direction = -1

        return ode, [event_dv_reached, event_tank_empty]

    def coast_ode(t, y):
        m, T, dv, E_out, Q_in = y
        dT_dt = Q_tank_wall / (m * gas.cv)
        return [0.0, dT_dt, 0.0, 0.0, Q_tank_wall]

    # --- Phase 1: Burn 1 ---
    y0 = [m_init, T_init, 0.0, 0.0, 0.0]
    ode1, events1 = make_burn_ode(dv1_target)
    sol1 = solve_ivp(ode1, (0.0, max_burn_time), y0, events=events1, rtol=rtol, atol=atol, max_step=1.0)

    # --- Phase 2: Coast ---
    t1_end = sol1.t[-1]
    y1_end = sol1.y[:, -1]
    sol2 = solve_ivp(
        coast_ode, (t1_end, t1_end + t_coast), y1_end, rtol=rtol, atol=atol, max_step=30.0
    )

    # --- Phase 3: Burn 2 ---
    t2_end = sol2.t[-1]
    y2_end = sol2.y[:, -1]
    ode3, events3 = make_burn_ode(dv1_target + dv2_target)
    sol3 = solve_ivp(
        ode3, (t2_end, t2_end + max_burn_time), y2_end, events=events3, rtol=rtol, atol=atol, max_step=1.0
    )

    # Stitch trajectories and compute derived SSSF histories
    t_all = np.concatenate([sol1.t, sol2.t[1:], sol3.t[1:]])
    y_all = np.hstack([sol1.y, sol2.y[:, 1:], sol3.y[:, 1:]])
    phases = (
        ["Burn 1"] * len(sol1.t)
        + ["Coast"] * (len(sol2.t) - 1)
        + ["Burn 2"] * (len(sol3.t) - 1)
    )

    m_arr, T_arr, dv_arr, E_out_arr, Q_in_arr = y_all
    P_arr = (m_arr * gas.R * T_arr) / V_tank

    F_arr = np.zeros_like(t_all)
    mdot_arr = np.zeros_like(t_all)
    isp_arr = np.zeros_like(t_all)

    for i, phase in enumerate(phases):
        if phase != "Coast":
            sssf = solve_sssf_thruster(
                P_arr[i], T_arr[i], gas, A_throat, area_ratio, eta_nozzle, Q_heater, regulated, P_reg_set
            )
            F_arr[i] = sssf["thrust_N"]
            mdot_arr[i] = sssf["m_dot_kg_s"]
            isp_arr[i] = sssf["isp_s"]

    return {
        "t": t_all,
        "phase": phases,
        "m": m_arr,
        "T": T_arr,
        "P": P_arr,
        "dv": dv_arr,
        "F": F_arr,
        "mdot": mdot_arr,
        "isp": isp_arr,
        "E_out": E_out_arr,
        "Q_in": Q_in_arr,
        "m_init": m_init,
        "t_burn1_end": t1_end,
        "t_coast_end": t2_end,
        "t_burn2_end": sol3.t[-1],
    }

def simulate_freeplay_blowdown(
    gas: IdealGas,
    V_tank: float,
    P_init: float,
    T_init: float,
    m_dry: float,
    A_throat: float,
    area_ratio: float,
    burn_duration: float = 120.0,
    eta_nozzle: float = 0.92,
    use_heater: bool = False,
    Q_heater: float = 0.0,
    Q_tank_wall: float = 0.0,
    use_regulator: bool = False,
    P_reg_set: float = 3.0e6,
    m_min_frac: float = 0.02,
    n_frames: int = 120,
    rtol: float = 1e-7,
    atol: float = 1e-9,
) -> dict:
    """
    Simulate a single continuous blowdown for Free-Play Mode, resampled onto
    a uniform time grid for smooth real-time / slowed-time playback.
    """
    m_init = (P_init * V_tank) / (gas.R * T_init)
    m_min = m_min_frac * m_init
    q_h = Q_heater if use_heater else 0.0

    def ode(t, y):
        m, T, dv, E_out, Q_in = y
        P = (m * gas.R * T) / V_tank
        sssf = solve_sssf_thruster(
            P, T, gas, A_throat, area_ratio, eta_nozzle, q_h, use_regulator, P_reg_set
        )
        m_dot = sssf["m_dot_kg_s"]
        F = sssf["thrust_N"]

        dm_dt = -m_dot
        dT_dt = (Q_tank_wall / (m * gas.cv)) - (gas.gamma - 1.0) * (T / m) * m_dot
        ddv_dt = F / (m_dry + m)
        dE_out_dt = m_dot * gas.cp * T
        return [dm_dt, dT_dt, ddv_dt, dE_out_dt, Q_tank_wall]

    def event_empty(t, y):
        return y[0] - m_min
    event_empty.terminal = True
    event_empty.direction = -1

    y0 = [m_init, T_init, 0.0, 0.0, 0.0]
    sol = solve_ivp(
        ode, (0.0, burn_duration), y0, events=[event_empty], rtol=rtol, atol=atol, max_step=0.5
    )

    # Resample onto a uniform time grid for smooth playback
    t_end = sol.t[-1]
    t_grid = np.linspace(0.0, t_end, n_frames)
    m_arr = np.interp(t_grid, sol.t, sol.y[0])
    T_arr = np.interp(t_grid, sol.t, sol.y[1])
    dv_arr = np.interp(t_grid, sol.t, sol.y[2])
    E_out_arr = np.interp(t_grid, sol.t, sol.y[3])
    Q_in_arr = np.interp(t_grid, sol.t, sol.y[4])
    P_arr = (m_arr * gas.R * T_arr) / V_tank

    F_arr = np.zeros(n_frames)
    mdot_arr = np.zeros(n_frames)
    isp_arr = np.zeros(n_frames)
    for i in range(n_frames):
        sssf = solve_sssf_thruster(
            P_arr[i], T_arr[i], gas, A_throat, area_ratio, eta_nozzle, q_h, use_regulator, P_reg_set
        )
        F_arr[i] = sssf["thrust_N"]
        mdot_arr[i] = sssf["m_dot_kg_s"]
        isp_arr[i] = sssf["isp_s"]

    return {
        "t": t_grid,
        "phase": ["Burn"] * n_frames,
        "m": m_arr,
        "T": T_arr,
        "P": P_arr,
        "dv": dv_arr,
        "F": F_arr,
        "mdot": mdot_arr,
        "isp": isp_arr,
        "E_out": E_out_arr,
        "Q_in": Q_in_arr,
        "m_init": m_init,
    }