import numpy as np
from scipy.optimize import brentq
from .fluid_props import IdealGas

G0 = 9.80665 # Standard gravity [m/s^2]

def solve_supersonic_mach(area_ratio: float, gamma: float) -> float:
    """Solve the isentropic area-Mach relation for supersonic exit Mach number Me > 1."""
    if area_ratio <= 1.0:
        return 1.0

    def residual(M):
        term = (2.0 / (gamma + 1.0)) * (1.0 + 0.5 * (gamma - 1.0) * M**2)
        return (1.0 / M) * (term ** ((gamma + 1.0) / (2.0 * (gamma - 1.0)))) - area_ratio

    return brentq(residual, 1.0001, 50.0)

def solve_sssf_thruster(
    P_tank: float,
    T_tank: float,
    gas: IdealGas,
    A_throat: float,
    area_ratio: float,
    eta_nozzle: float = 0.92,
    Q_heater: float = 0.0,
    regulated: bool = False,
    P_reg_set: float = 5.0e5,
) -> dict:
    """
    Evaluate instantaneous Steady-State Steady-Flow (SSSF) thruster performance
    expanding into vacuum (Pa = 0).
    """
    # 1. Pressure Regulator (isenthalpic throttling for ideal gas -> T_reg = T_tank)
    P0 = min(P_tank, P_reg_set) if regulated else P_tank
    T_reg = T_tank

    # Choked flow constant: m_dot = C_choke / sqrt(T0)
    g = gas.gamma
    choke_factor = np.sqrt(g / gas.R) * ((2.0 / (g + 1.0)) ** ((g + 1.0) / (2.0 * (g - 1.0))))
    C_choke = P0 * A_throat * choke_factor

    # 2. Resistojet Heater (exact closed-form solution for coupled m_dot and T0)
    # Q_heater = (C_choke / sqrt(T0)) * cp * (T0 - T_reg)
    if Q_heater > 0.0 and C_choke > 0.0:
        a = C_choke * gas.cp
        b = -Q_heater
        c = -C_choke * gas.cp * T_reg
        sqrt_T0 = (-b + np.sqrt(b**2 - 4.0 * a * c)) / (2.0 * a)
        T0 = sqrt_T0**2
    else:
        T0 = T_reg

    m_dot = C_choke / np.sqrt(T0) if T0 > 0 else 0.0

    # 3. Vacuum Converging-Diverging Nozzle
    Me = solve_supersonic_mach(area_ratio, g)
    temp_ratio = 1.0 + 0.5 * (g - 1.0) * Me**2
    T_es = T0 / temp_ratio
    P_e = P0 / (temp_ratio ** (g / (g - 1.0)))

    # Actual exit velocity & temperature with nozzle efficiency
    V_e = np.sqrt(max(0.0, 2.0 * eta_nozzle * gas.cp * (T0 - T_es)))
    T_e = T0 - (V_e**2) / (2.0 * gas.cp)

    A_exit = A_throat * area_ratio
    thrust = m_dot * V_e + P_e * A_exit
    isp = thrust / (m_dot * G0) if m_dot > 0 else 0.0

    # Entropy generation in nozzle (adiabatic)
    ds_nozzle = gas.cp * np.log(T_e / T0) - gas.R * np.log(P_e / P0)
    S_gen_nozzle = m_dot * ds_nozzle

    return {
        "P0_Pa": P0,
        "T0_K": T0,
        "m_dot_kg_s": m_dot,
        "Me": Me,
        "P_e_Pa": P_e,
        "T_e_K": T_e,
        "V_e_m_s": V_e,
        "thrust_N": thrust,
        "isp_s": isp,
        "S_gen_nozzle_W_K": S_gen_nozzle,
    }